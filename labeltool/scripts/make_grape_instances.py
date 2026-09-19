# -*- coding: utf-8 -*-
"""포도 CERTH 송이 인스턴스 → 우리 툴이 읽는 «번호 마스크» 로 변환 (사이클4 1차, 판정서 ③-3).

무엇을 하나
  CERTH 원본 배포에는 송이마다 번호가 매겨진 정답이 있다(2,502장 9,832송이 — 검출 팀 `grape_gt.py`).
  그런데 팀 표준 마스크와 CERTH 라벨맵은 **리샘플링이 달라 경계가 1~2화소 흔들린다**:
    - 팀 표준 마스크 : `prepare_certh_grape.py:209-211`  PIL NEAREST 로 줄인 뒤 `>127`
    - CERTH 라벨맵   : `grape_gt.py:113-116`             `(arange*scale).astype(int)` 격자 골라내기
  그래서 **전경의 기준은 우리(검수한) 마스크**로 두고 CERTH 에서는 **번호만** 빌린다:
    1) `lab[~mask] = 0`                              우리 마스크 밖의 번호를 버린다
    2) 전경인데 번호가 없는 화소는 EDT 로 **가장 가까운 번호**를 채운다
  결과는 «번호 마스크의 >0 == 우리 이진 마스크» 라는 블루베리와 같은 불변식을 만족한다.

⛔ 이 스크립트는 **살아 있는 툴을 바꾸지 않는다.** 산출물을 툴이 읽게 하려면
   `app/instances.py:24 SEED_DIRS` 에 포도 한 줄을 더해야 하고, 그것은 교수님 확인 8번의
   답을 받은 뒤다(판정서 ③-1). 지금은 만들고 검증만 한다.

읽기 전용: 원본 데이터셋 · `work/park_seongmoon/`.  쓰는 곳: `data/grape/instances_seed/` 뿐.

사용:
  PY=/home/kds0206/.conda/envs/kwak/bin/python
  $PY scripts/make_grape_instances.py --limit 12 --out /tmp/시험       # 맛보기
  $PY scripts/make_grape_instances.py                                   # 전수 2,502장
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "app"))
sys.path.insert(0, "/data/project/2026summer/platform/work/park_seongmoon/semantic-segmentation/tools")
from maskio import load_mask_bool                       # noqa: E402
from instances import write_u16_atomic                  # noqa: E402  번호를 잃지 않는 uint16 저장
import grape_gt                                         # noqa: E402  검출 팀 정답 (읽기만)

# 팀 표준 마스크를 전경 기준으로 쓴다. 검수판(`datasets_reviewed_260916`)의 포도 마스크 2,406장은
# 팀 표준과 **바이트까지 같다**(사이클4 1차 실측) — 검수판은 근접 중복 96장을 뺀 것일 뿐이므로
# 어느 쪽을 봐도 같은 배열이고, 전수 2,502장을 만들어 두면 두 폴더 어느 것을 보든 맞는다.
STD = "/data/project/2026summer/kds0206/datasets_resized_2mp/grape"
FAR_PX = 3          # 우리 전경인데 CERTH 번호에서 이만큼 넘게 떨어진 화소 → 사람이 봐야 함
MIN_PX = 4          # boxes.py boxes_of() 의 «4화소 미만은 상자에서 빠짐» 규칙


def convert(stem, out_dir):
    """한 장 변환. 반환: 통계 딕셔너리(오류면 'error' 키)."""
    mp_path = os.path.join(STD, "masks", stem + ".png")
    if not os.path.exists(mp_path):
        return {"stem": stem, "error": "우리 마스크 없음"}
    if not grape_gt.has(stem):
        return {"stem": stem, "error": "CERTH 정답 없음"}
    mask = load_mask_bool(mp_path)
    H, W = mask.shape
    lab, ids = grape_gt.label_map(stem, H, W)
    n_certh = int(len(ids))

    lab = lab.copy()
    lab[~mask] = 0                                    # ① 우리 마스크로 자른다
    need = mask & (lab == 0)
    n_need = int(need.sum())
    far = 0
    if n_need:
        dist, idx = ndimage.distance_transform_edt(lab == 0, return_indices=True)
        far = int((dist[need] > FAR_PX).sum())        # 검수자가 손으로 더 그린 자리일 수 있다
        lab[need] = lab[idx[0][need], idx[1][need]]   # ② 가장 가까운 번호로 채운다
    # 채울 번호가 아예 없었으면(자르고 나니 전부 0) 전경이 남아 있을 수 있다
    fg_ok = bool(((lab > 0) == mask).all())

    cnt = np.bincount(lab.ravel())
    present = np.nonzero(cnt)[0]
    present = present[present > 0]
    lost = sorted(int(v) for v in ids if v >= len(cnt) or cnt[v] == 0)
    small = sorted(int(v) for v in present if cnt[v] < MIN_PX)
    write_u16_atomic(os.path.join(out_dir, stem + ".png"), lab.astype(np.uint16))
    return {"stem": stem, "size": [int(H), int(W)],
            "certh": n_certh, "kept": int(present.size), "lost_ids": lost,
            "fg_pixels": int(mask.sum()), "filled_pixels": n_need, "far_pixels": far,
            "small_ids": small, "fg_match": fg_ok, "max_id": int(present.max()) if present.size else 0}


def _job(a):
    stem, out_dir = a
    try:
        return convert(stem, out_dir)
    except Exception as e:                            # 한 장이 깨져도 전수가 멈추지 않게
        return {"stem": stem, "error": "%s: %s" % (type(e).__name__, e)}


def main():
    ap = argparse.ArgumentParser(description="포도 CERTH 송이 인스턴스 → 번호 마스크")
    ap.add_argument("--out", default=os.path.join(BASE, "data", "grape", "instances_seed"))
    ap.add_argument("--limit", type=int, default=0, help="앞 N 장만 (맛보기)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--stats", default=None, help="통계 json 경로")
    a = ap.parse_args()

    stems = sorted(grape_gt._index().keys())
    if a.limit:
        stems = stems[:a.limit]
    os.makedirs(a.out, exist_ok=True)
    print("전경 기준(우리 마스크): %s/masks" % STD)
    print("번호 출처(읽기만)     : 검출 팀 grape_gt.py — CERTH %d장 %d송이" % grape_gt.totals())
    print("내보낼 곳             : %s  (%d장)" % (a.out, len(stems)))
    t0 = time.time()
    jobs = [(s, a.out) for s in stems]
    if a.workers > 1 and len(jobs) > 1:
        with mp.Pool(a.workers) as pool:
            rows = pool.map(_job, jobs, chunksize=4)
    else:
        rows = [_job(j) for j in jobs]
    dt = time.time() - t0

    err = [r for r in rows if r.get("error")]
    good = [r for r in rows if not r.get("error")]
    n_kept = sum(r["kept"] for r in good)
    n_certh = sum(r["certh"] for r in good)
    bad_fg = [r["stem"] for r in good if not r["fg_match"]]
    lost = {r["stem"]: r["lost_ids"] for r in good if r["lost_ids"]}
    small = {r["stem"]: r["small_ids"] for r in good if r["small_ids"]}
    far = sorted(((r["far_pixels"], r["stem"]) for r in good if r["far_pixels"]), reverse=True)

    print("\n%.1f초 (%d 프로세스)" % (dt, a.workers))
    print("  변환 %d장 · 오류 %d장" % (len(good), len(err)))
    print("  CERTH 송이 %d → 번호로 남은 것 %d (없어진 송이 %d장 %d개)"
          % (n_certh, n_kept, len(lost), sum(len(v) for v in lost.values())))
    print("  «번호>0 == 우리 마스크» 가 참인 장수 : %d / %d   (거짓 %d장)"
          % (len(good) - len(bad_fg), len(good), len(bad_fg)))
    print("  4화소 미만 번호가 있는 장수          : %d" % len(small))
    print("  CERTH 에서 %dpx 넘게 떨어진 전경이 있는 장수 : %d  (사람이 볼 것)" % (FAR_PX, len(far)))
    for n, s in far[:10]:
        print("      %-8s %d 화소" % (s, n))
    for r in err[:10]:
        print("      오류 %-8s %s" % (r["stem"], r["error"]))

    sp = a.stats or os.path.join(BASE, "cycles/260917_신기능/cycle_4/stage1/grape_instances_stats.json")
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    json.dump({"out": a.out, "fg_source": STD, "seconds": round(dt, 1),
               "n_images": len(good), "n_errors": len(err),
               "certh_objects": n_certh, "kept_objects": n_kept,
               "fg_match_images": len(good) - len(bad_fg), "fg_mismatch_stems": bad_fg,
               "lost_ids": lost, "small_ids": small,
               "far_stems": [{"stem": s, "px": n} for n, s in far],
               "errors": err, "rows": rows},
              open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("통계: " + sp)
    ok = not err and not bad_fg
    print("\n판정: " + ("통과" if ok else "확인 필요"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
