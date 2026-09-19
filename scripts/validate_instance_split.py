"""«과일 하나하나 쪼개기»가 얼마나 정확한지 사과 정답으로 실측한다.

사과(MinneApple) 마스크는 픽셀값이 **인스턴스 ID**(1,2,3,…)라 정답 개수를 알 수 있다.
그래서 사과만은 «정답 vs 알고리즘»을 직접 대조할 수 있다. 여기서 나온 오차율이
나머지 3과일(정답이 없음)에 대한 신뢰 근거가 된다.

비교 대상
  GT        정답 (인스턴스 ID 개수)
  CC        connected components — 붙은 열매가 하나로 합쳐짐 (2026-08-10 에 쓴 방법)
  WS        watershed 분리 — tools/instance_split.py

출력  output/instance_split_validation.json
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
from PIL import Image

from instance_split import MIN_AREA, label_cc, split_instances

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
OUT = ROOT / "semantic-segmentation/output/instance_split_validation.json"


def one(args):
    mpath, fracs = args
    a = np.array(Image.open(mpath))
    if a.ndim == 3:
        a = a[..., 0]

    ids, cnts = np.unique(a, return_counts=True)
    sel = (ids > 0) & (cnts >= MIN_AREA)
    gt = int(sel.sum())

    b = a > 0
    _, idx = label_cc(b)
    cc = int(len(idx))

    ws = []
    for f in fracs:
        _, i2 = split_instances(b, peak_frac=f)
        ws.append(int(len(i2)))
    return gt, cc, ws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fracs", type=float, nargs="+", default=[1.1])
    ap.add_argument("--limit", type=int, default=0, help="N장만 (시험용)")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    masks = sorted(p for p in (POOL / "apple" / "masks").iterdir() if p.is_file())
    if a.limit:
        step = max(1, len(masks) // a.limit)
        masks = masks[::step][:a.limit]
    print(f"사과 {len(masks)}장으로 검증 (fracs={a.fracs})", flush=True)

    with mp.Pool(a.workers) as pool:
        rows = pool.map(one, [(str(p), a.fracs) for p in masks], chunksize=4)

    gt = np.array([r[0] for r in rows], float)
    cc = np.array([r[1] for r in rows], float)
    ws = np.array([r[2] for r in rows], float)          # (N, len(fracs))

    def score(v):
        err = v - gt
        return {
            "per_image_mean": float(v.mean()),
            "total": int(v.sum()),
            "total_bias_pct": float(v.sum() / gt.sum() * 100 - 100),
            "abs_err_median": float(np.median(np.abs(err))),
            "rel_err_median_pct": float(np.median(np.abs(err) / np.maximum(gt, 1)) * 100),
            "within_20pct": float((np.abs(err) / np.maximum(gt, 1) <= 0.20).mean() * 100),
        }

    res = {
        "generated_by": "tools/validate_instance_split.py",
        "images": len(masks),
        "gt": {"per_image_mean": float(gt.mean()), "total": int(gt.sum())},
        "cc": score(cc),
        "watershed": {str(f): score(ws[:, i]) for i, f in enumerate(a.fracs)},
        "note": "GT = 사과 마스크의 인스턴스 ID. 나머지 3과일은 정답이 없어 이 오차율을 근거로 쓴다.",
    }
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))

    print(f"\n정답 장당 {gt.mean():.1f}개 (총 {int(gt.sum()):,})")
    print(f"  CC        장당 {cc.mean():6.1f}  총편향 {res['cc']['total_bias_pct']:+6.1f}%"
          f"  장별 상대오차중앙 {res['cc']['rel_err_median_pct']:5.1f}%"
          f"  ±20% 안 {res['cc']['within_20pct']:5.1f}%")
    for f in a.fracs:
        s = res["watershed"][str(f)]
        print(f"  WS f={f:<4} 장당 {s['per_image_mean']:6.1f}  총편향 {s['total_bias_pct']:+6.1f}%"
              f"  장별 상대오차중앙 {s['rel_err_median_pct']:5.1f}%"
              f"  ±20% 안 {s['within_20pct']:5.1f}%")
    print(f"\n저장: {a.out}")


if __name__ == "__main__":
    main()
