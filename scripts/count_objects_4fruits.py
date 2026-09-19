#!/usr/bin/env python
"""0810 랩미팅 지시 ④⑤ — 4과일의 «이미지 한 장당 개체 수» 통계를 낸다.

녹취 근거 (reports/0810 랩미팅.txt)
  04:02  "그것도 약간 좀 그 통계도 좀 한번 계산해 보세요. 랜덤 크롭을 했을 때
          몇 개 평균 몇 개 오브젝트가..."
  03:42  "센터에는 반드시 한 개는 한 개 이상 거의 들어가나요?"
  13:11  "정확하게 디텍션 알고리즘을 테스트할 건 아니기 때문에, 그냥 알고리즘 돌려서
          나온 결과를 기반으로 해가지고 저 플롯만 만들면 된다는 거죠.
          이거는 뭐 대략적인 약간 좀 틀려도 되는 거잖아요."
  14:20  "그니까 리사이즈 한 걸로. 이미지 한 장당 지금 개수 계산하면 돼요."
  14:56  "지워버리지 말고요. 아무튼 보관해 놓고 있으면, 크롭한 거에 대해서도
          필요하면 크롭한 거에 대해서도 또 계산하면 되거든요."

목적 (13:11) — "벤치마크 논문이 여러 개 있을 텐데 굳이 왜 이 데이터셋을 새로 해야 되느냐"에
대한 답. MinneApple 논문 3쪽 그림처럼 «한 장에 개체가 아주 많다»를 통계로 보여준다.

━━ 개체를 어떻게 «하나하나» 구별하는가 (2026-08-10 수정) ━━
교수님 요구의 핵심은 04:02 "오브젝트 디텍션이면 몇 개가 들어가는지 알 수 있는데 얘는 그게
없잖아요" → **과일이 한 알씩 구별돼야 한다**는 것이다.
  - 🍎 사과(MinneApple): 마스크 픽셀값이 **인스턴스 ID**(1..N) → 정답 개수를 정확히 앎
  - 나머지 3과일: 0/255 이진 → **거리변환 + watershed 로 붙은 열매를 알알이 분리**
    (`tools/instance_split.py`. 교수님 05:06 "그냥 알고리즘적으로 만들 수 있을 것 같다")

⛔ 첫 판(2026-08-10 오후, `object_stats_4fruits.json`)은 connected components(붙은 덩어리
= 1개)로 셌는데, 이것은 «하나하나 구별»이 아니어서 사과 정답 대비 **18.2% 과소 계수**였다.
같은 날 저녁에 분리 방식으로 고쳤다. 지금은 분리 후 센다.
정확도는 사과 정답으로 실측한다 → `tools/validate_instance_split.py`

입력  datasets_resized_2mp/<fruit>/{images,masks}
출력  output/object_stats_4fruits_split.json   (옛 CC 판은 object_stats_4fruits.json 로 보존)
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import grape_gt
import peach_gt
from instance_split import (MIN_AREA as SPLIT_MIN_AREA, PEAK_FRAC, PRIMARY, areas_of,
                            centroids_of, label_cc, label_gt, split_instances)

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
OUT = ROOT / "semantic-segmentation/output/object_stats_4fruits_split.json"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과", "peach": "복숭아", "grape": "포도"}
# 포도만 개체 = «송이». 나머지는 «열매 한 알».
UNIT = {"blueberry": "열매", "apple": "열매", "peach": "열매", "grape": "송이"}

# PRIMARY(과일별 개체 정의)는 tools/instance_split.py 로 옮겼다. 여기서는 가져다 쓴다.

CROP = 512
N_RANDOM_CROPS = 10          # 이미지당 랜덤 크롭 표본 수
MIN_AREA = 10                # 10픽셀 미만은 잡티로 보고 버림


def load_mask_raw(p: Path) -> np.ndarray:
    """마스크를 (H,W) 2차원으로. 3채널이면 첫 채널만 (0/255 복제본이므로 동일)."""
    a = np.array(Image.open(p))
    if a.ndim == 3:
        a = a[..., 0]
    return a


def crop_counts(centroids: np.ndarray, H: int, W: int, rng: np.random.Generator):
    """학습과 같은 규칙의 랜덤크롭 / 평가와 같은 센터크롭 안에 중심이 들어오는 개체 수.

    학습 RandomCrop: 512보다 작으면 오른쪽·아래 0패딩 후 좌상단 균등 무작위.
    평가 CenterCrop : 가운데 512x512.
    개체가 «들어갔다»의 정의 = **개체 중심(centroid)이 크롭 안**. (걸친 것을 이중으로
    세지 않기 위해. 개수 밀도를 재는 표준 방식)
    """
    Hp, Wp = max(H, CROP), max(W, CROP)      # 패딩 후 크기
    n_rand = []
    for _ in range(N_RANDOM_CROPS):
        top = int(rng.integers(0, Hp - CROP + 1))
        left = int(rng.integers(0, Wp - CROP + 1))
        if len(centroids) == 0:
            n_rand.append(0)
            continue
        inside = ((centroids[:, 0] >= top) & (centroids[:, 0] < top + CROP) &
                  (centroids[:, 1] >= left) & (centroids[:, 1] < left + CROP))
        n_rand.append(int(inside.sum()))

    ctop, cleft = (Hp - CROP) // 2, (Wp - CROP) // 2
    if len(centroids) == 0:
        n_center = 0
    else:
        inside = ((centroids[:, 0] >= ctop) & (centroids[:, 0] < ctop + CROP) &
                  (centroids[:, 1] >= cleft) & (centroids[:, 1] < cleft + CROP))
        n_center = int(inside.sum())
    return n_rand, n_center, (ctop, cleft)


def one_image(args):
    fruit, mpath, seed = args
    raw = load_mask_raw(Path(mpath))
    H, W = raw.shape
    binary = raw > 0
    fg_px = int(binary.sum())

    # ── 비교용으로 두 알고리즘을 항상 재둔다 ──────────────────────
    lab_ws, idx_ws = split_instances(binary)     # 거리변환+watershed (붙은 것을 쪼갬)
    lab_cc, idx_cc = label_cc(binary)            # 붙은 덩어리 = 1개

    # ── 주 지표 = 정답 어노테이션 (있는 과일은 전부 정답을 쓴다) ───
    stem = Path(mpath).stem
    n_exact = None
    if fruit == "apple":                          # 마스크 픽셀값 = 인스턴스 ID
        lab_g, idx_g = label_gt(raw)
        areas_obj, cent = areas_of(lab_g, idx_g), centroids_of(lab_g, idx_g)
        n_exact = int(len(idx_g))
    elif fruit == "peach" and peach_gt.has(stem):  # COCO 폴리곤
        areas_obj, cent = peach_gt.props(stem, H, W)
    elif fruit == "grape" and grape_gt.has(stem):  # CERTH RLE (송이 단위)
        areas_obj, cent = grape_gt.props(stem, H, W)
    else:                                          # 블루베리 — 정답이 없다
        areas_obj, cent = areas_of(lab_ws, idx_ws), centroids_of(lab_ws, idx_ws)

    if len(areas_obj):                             # 잡티 제거 기준은 알고리즘과 동일하게
        keep = areas_obj >= SPLIT_MIN_AREA
        areas_obj, cent = areas_obj[keep], cent[keep]
    if fruit in ("peach", "grape"):
        n_exact = int(len(areas_obj))

    rng = np.random.default_rng(seed)
    n_rand, n_center, (ctop, cleft) = crop_counts(cent, H, W, rng)

    # 평가(CenterCrop)가 실제로 채점하는 영역에 전경이 있는가 — 개체 «중심»이 아니라
    # 전경 «픽셀» 기준. 걸쳐 있기만 해도 채점 대상은 되므로 둘을 따로 재야 한다.
    if H < CROP or W < CROP:
        padded = np.zeros((max(H, CROP), max(W, CROP)), bool)
        padded[:H, :W] = binary
    else:
        padded = binary
    cwin = padded[ctop:ctop + CROP, cleft:cleft + CROP]
    center_fg_px = int(cwin.sum())

    return {
        "stem": stem,
        "H": H, "W": W,
        "n_obj": int(len(areas_obj)),    # 🔴 주 지표 (정답이 있으면 정답)
        "n_ws": int(len(idx_ws)),        # 쪼갠 개수
        "n_cc": int(len(idx_cc)),        # 덩어리 개수 (옛 방법)
        "n_exact": n_exact,
        "fg_ratio": fg_px / (H * W),
        "areas": np.asarray(areas_obj).astype(int).tolist(),
        "n_rand": n_rand,
        "n_center": n_center,
        "center_has_fg": bool(center_fg_px > 0),
        "center_fg_ratio": center_fg_px / (CROP * CROP),
    }


def summarize(recs: list[dict], fruit: str) -> dict:
    npi = np.array([r["n_obj"] for r in recs])
    allareas = np.concatenate([np.array(r["areas"]) for r in recs]) if recs else np.zeros(0)
    px = np.array([r["H"] * r["W"] for r in recs], float)
    rand = np.concatenate([np.array(r["n_rand"]) for r in recs]) if recs else np.zeros(0)
    cen = np.array([r["n_center"] for r in recs])

    # 화면 대비 크기 — 해상도가 달라도 공정하게 비교되는 유일한 축 (2026-07-23 교훈)
    rel = []
    for r in recs:
        if r["areas"]:
            rel.append(np.array(r["areas"]) / (r["H"] * r["W"]))
    rel = np.concatenate(rel) if rel else np.zeros(0)

    out = {
        "fruit": fruit, "kor": KOR[fruit], "unit": UNIT[fruit],
        "images": len(recs),
        "objects_total": int(npi.sum()),
        "per_image": {
            "mean": float(npi.mean()), "median": float(np.median(npi)),
            "min": int(npi.min()), "max": int(npi.max()), "std": float(npi.std()),
            "p90": float(np.percentile(npi, 90)),
            "ge50_pct": float((npi >= 50).mean() * 100),
            "ge100_pct": float((npi >= 100).mean() * 100),
        },
        "area_px": {
            "mean": float(allareas.mean()) if len(allareas) else 0.0,
            "median": float(np.median(allareas)) if len(allareas) else 0.0,
            "p10": float(np.percentile(allareas, 10)) if len(allareas) else 0.0,
            "p90": float(np.percentile(allareas, 90)) if len(allareas) else 0.0,
        },
        # 지름 환산 = 원이라 가정 (2*sqrt(A/pi)). 과일이 대체로 둥글어 타당
        "diameter_px_median": float(2 * np.sqrt(np.median(allareas) / np.pi)) if len(allareas) else 0.0,
        "area_rel_pct_median": float(np.median(rel) * 100) if len(rel) else 0.0,
        "fg_ratio_mean_pct": float(np.mean([r["fg_ratio"] for r in recs]) * 100),
        "image_pixels_mean": float(px.mean()),
        "random_crop_512": {
            "samples": int(len(rand)),
            "mean": float(rand.mean()) if len(rand) else 0.0,
            "median": float(np.median(rand)) if len(rand) else 0.0,
            "zero_pct": float((rand == 0).mean() * 100) if len(rand) else 0.0,
        },
        "center_crop_512": {
            "mean": float(cen.mean()),
            "median": float(np.median(cen)),
            # 🔴 교수님 03:42 "센터에는 반드시 한 개 이상 거의 들어가나요?" 에 대한 답.
            #   두 가지로 답해야 정확하다.
            #   ge1_pct     = 개체 «중심»이 들어온 비율 (= 온전한 열매가 1개 이상)
            #   any_fg_pct  = 전경 픽셀이 하나라도 있는 비율 (= 채점할 게 있는가)
            "ge1_pct": float((cen >= 1).mean() * 100),
            "zero_pct": float((cen == 0).mean() * 100),
            "any_fg_pct": float(np.mean([r["center_has_fg"] for r in recs]) * 100),
            "empty_pct": float(100 - np.mean([r["center_has_fg"] for r in recs]) * 100),
            "fg_ratio_mean_pct": float(np.mean([r["center_fg_ratio"] for r in recs]) * 100),
        },
    }

    # 두 방법의 차이 — 어느 쪽을 골랐는지, 다른 쪽은 얼마였는지 항상 남긴다
    cc = np.array([r["n_cc"] for r in recs])
    ws = np.array([r["n_ws"] for r in recs])
    out["methods"] = {
        "primary": PRIMARY[fruit],
        "cc_per_image_mean": float(cc.mean()),
        "watershed_per_image_mean": float(ws.mean()),
        "watershed_vs_cc_pct": float(ws.sum() / max(cc.sum(), 1) * 100 - 100),
    }

    if recs and recs[0]["n_exact"] is not None:
        ex = np.array([r["n_exact"] for r in recs])
        out["accuracy_vs_groundtruth"] = {
            "note": "정답 어노테이션과 두 알고리즘을 대조한 값",
            "exact_mean": float(ex.mean()),
            "watershed_mean": float(ws.mean()),
            "cc_mean": float(cc.mean()),
            "watershed_bias_pct": float(ws.sum() / ex.sum() * 100 - 100),
            "cc_bias_pct": float(cc.sum() / ex.sum() * 100 - 100),
            "watershed_abs_err_median": float(np.median(np.abs(ex - ws))),
            "cc_abs_err_median": float(np.median(np.abs(ex - cc))),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruits", nargs="+", default=FRUITS)
    ap.add_argument("--pool", default=str(POOL))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0, help="과일당 N장만 (시험용)")
    a = ap.parse_args()

    pool_root = Path(a.pool)
    result = {
        "generated_by": "tools/count_objects_4fruits.py",
        "source": str(pool_root),
        "method": {
            "binary": "mask > 0",
            "instances": f"거리변환 + watershed 분리 (tools/instance_split.py, PEAK_FRAC={PEAK_FRAC})",
            "components_legacy": "scipy.ndimage.label 8-이웃 (비교용으로만 병기)",
            "min_area_px": MIN_AREA,
            "apple_exact": "마스크 픽셀값 = 인스턴스 ID 이므로 정답 개수를 직접 셈",
            "crop_rule": "학습 RandomCrop(0패딩+균등무작위) / 평가 CenterCrop 과 동일",
            "in_crop_def": "개체 중심(centroid)이 크롭 안에 있으면 1개로 셈",
            "random_crops_per_image": N_RANDOM_CROPS,
            "limitation": "포도는 라벨 자체가 «송이» 단위라 알 단위로는 셀 수 없다. "
                          "정확도는 사과 정답으로 실측 → accuracy_vs_groundtruth",
        },
        "fruits": {},
    }

    for fruit in a.fruits:
        mdir = pool_root / fruit / "masks"
        masks = sorted(p for p in mdir.iterdir() if p.is_file())
        if a.limit:
            masks = masks[:a.limit]
        tasks = [(fruit, str(p), i) for i, p in enumerate(masks)]
        print(f"[{fruit}] {len(tasks)}장 처리 시작...", flush=True)
        with mp.Pool(a.workers) as pool:
            recs = pool.map(one_image, tasks, chunksize=8)
        s = summarize(recs, fruit)
        # 장별 기록은 그림 그릴 때 필요하므로 가벼운 형태로만 보관 (areas 는 제외)
        s["per_image_counts"] = [r["n_obj"] for r in recs]
        s["per_image_counts_cc"] = [r["n_cc"] for r in recs]
        s["per_image_center"] = [r["n_center"] for r in recs]
        s["area_hist"] = np.histogram(
            np.concatenate([np.array(r["areas"]) for r in recs]) if recs else np.zeros(0),
            bins=60, range=(0, 4000))[0].tolist()
        result["fruits"][fruit] = s
        pi = s["per_image"]
        print(f"  → 장당 평균 {pi['mean']:.1f}개 (중앙 {pi['median']:.0f}, 최대 {pi['max']}) "
              f"| 센터크롭 1개 이상 {s['center_crop_512']['ge1_pct']:.1f}% "
              f"| 랜덤크롭 평균 {s['random_crop_512']['mean']:.1f}개", flush=True)
        v = s["methods"]
        print(f"  → 방법: {v['primary']}  (덩어리 {v['cc_per_image_mean']:.1f}개 / "
              f"쪼갬 {v['watershed_per_image_mean']:.1f}개)", flush=True)
        if "accuracy_vs_groundtruth" in s:
            g = s["accuracy_vs_groundtruth"]
            print(f"  → [정확도] 정답 {g['exact_mean']:.1f} | 쪼갬 {g['watershed_mean']:.1f}"
                  f" ({g['watershed_bias_pct']:+.1f}%) | 덩어리 {g['cc_mean']:.1f}"
                  f" ({g['cc_bias_pct']:+.1f}%)", flush=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(f"\n저장: {a.out}")


if __name__ == "__main__":
    main()
