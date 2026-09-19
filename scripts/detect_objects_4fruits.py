#!/usr/bin/env python
"""0810 랩미팅 지시 ② — «디텍션 알고리즘»을 돌려 과실마다 바운딩 박스를 뽑는다.

━━ 왜 다시 만드는가 (connected components 로는 부족했던 이유) ━━
교수님 지적의 핵심은 «개수»가 아니라 «바운딩 박스»였다.

  04:02 "오브젝트 디텍션이면 이렇게 «바운딩 박스»가 있잖아요.
         그 1개가 «어디 있는지» 몇 개가 들어가는지 알 수가 있는데
         «얘는 그게 없잖아요». 지금 데이터 상에."
  05:06 "그냥 알고리즘적으로 만들 수 있을 것 같긴 하거든요.
         아무튼 «점 있는 데에 오브젝트를 넣으면» 되잖아요.
         아니면 우리 오브젝트 디텍션을 돌리던가 학습 시켜가지고"
  13:11 "정확하게 디텍션 알고리즘을 테스트할 건 아니기 때문에 그냥 알고리즘 돌려가지고
         나온 결과를 기반으로 저 «플롯만» 만들면 된다는 거죠. 대략적인 약간 좀 틀려도 되는 거잖아요.
         그래서 «알고리즘 디텍션 돌려서» 이렇게 해왔다, 뭐 이렇게 얘기하면 되는 거니까."
  14:56 "지워버리지 말고요. 아무튼 «보관»해 놓고 있으면"

앞서 쓴 connected components 는 붙어 있는 열매를 «한 덩어리»로 봐서 사과 기준 18.2% 적게
셌고, 무엇보다 «열매 하나하나의 위치(바운딩 박스)»를 만들지 못했다. 그래서 교체한다.

━━ 쓰는 알고리즘 ━━
거리변환(distance transform) + watershed = 붙어 있는 둥근 물체를 갈라내는 고전적인 방법.
  1) 마스크를 이진화
  2) 각 전경 화소가 «배경에서 얼마나 먼가»를 계산 (열매 중심일수록 값이 큼)
  3) 그 값의 «봉우리»를 열매 중심으로 잡음  ← 교수님 05:06 "점 있는 데에 오브젝트를 넣으면"
  4) 봉우리에서 물이 차오르듯 영역을 넓혀 경계에서 만나게 함 (watershed)
  5) 갈라진 덩어리마다 «바운딩 박스»를 뽑음
학습이 필요 없고, 봉우리 간 최소 거리(min_distance) 하나만 정하면 된다.

━━ 그 min_distance 를 «정답으로 보정»한다 ━━
사과(MinneApple)는 마스크 픽셀값이 인스턴스 ID 라 «정답 개수»를 안다.
그래서 사과에서 계수 f 를 훑어 정답에 가장 가까운 값을 고르고,
그 «같은 f» 를 4과일에 동일 적용한다.  min_distance = f x (그 과일 개체 지름 중앙값)
→ 과일마다 열매 크기가 다른 문제를 자동으로 흡수하면서, 사람이 눈대중으로 정하지 않는다.

입력  datasets_resized_2mp/<fruit>/masks + output/object_stats_4fruits.json (지름 중앙값)
출력  output/detect_stats_4fruits.json      과일별 통계 + 장별 개수
      output/detections/<fruit>_boxes.npz   바운딩 박스 전량 (보관용, 14:56)
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
CCSTATS = ROOT / "semantic-segmentation/output/object_stats_4fruits.json"
OUT = ROOT / "semantic-segmentation/output/detect_stats_4fruits.json"
BOXDIR = ROOT / "semantic-segmentation/output/detections"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과", "peach": "복숭아", "grape": "포도"}
UNIT = {"blueberry": "열매", "apple": "열매", "peach": "열매", "grape": "송이"}

CROP = 512
N_RANDOM_CROPS = 10
MIN_AREA = 10


def load_mask(p: Path) -> np.ndarray:
    a = np.array(Image.open(p))
    if a.ndim == 3:
        a = a[..., 0]
    return a


def detect(binary: np.ndarray, min_distance: int):
    """거리변환 + watershed 로 개체를 갈라내고 바운딩 박스를 돌려준다.

    반환: labels(H,W int), boxes(N,4 = x0,y0,x1,y1), centroids(N,2 = y,x), areas(N,)
    """
    if not binary.any():
        return (np.zeros(binary.shape, np.int32), np.zeros((0, 4), np.int32),
                np.zeros((0, 2)), np.zeros(0, np.int64))

    dist = ndimage.distance_transform_edt(binary)
    # 봉우리 = 열매 중심 후보. labels=binary 로 전경 안에서만 찾는다.
    coords = peak_local_max(dist, min_distance=max(1, int(min_distance)),
                            labels=binary, exclude_border=False)
    if len(coords) == 0:
        # 봉우리를 못 찾으면 덩어리 자체를 1개로 (아주 작은 개체)
        labels, _ = ndimage.label(binary, structure=np.ones((3, 3), int))
    else:
        markers = np.zeros(binary.shape, np.int32)
        markers[tuple(coords.T)] = np.arange(1, len(coords) + 1)
        markers, _ = ndimage.label(markers > 0, structure=np.ones((3, 3), int))
        labels = watershed(-dist, markers, mask=binary)

    n = int(labels.max())
    if n == 0:
        return (labels, np.zeros((0, 4), np.int32), np.zeros((0, 2)), np.zeros(0, np.int64))

    areas = np.bincount(labels.ravel(), minlength=n + 1)[1:]
    keep = np.nonzero(areas >= MIN_AREA)[0] + 1
    if len(keep) == 0:
        return (labels, np.zeros((0, 4), np.int32), np.zeros((0, 2)), np.zeros(0, np.int64))

    slices = ndimage.find_objects(labels)
    boxes, cents, ars = [], [], []
    for lab in keep:
        sl = slices[lab - 1]
        if sl is None:
            continue
        ys, xs = sl
        boxes.append((xs.start, ys.start, xs.stop, ys.stop))
        ars.append(int(areas[lab - 1]))
    cents = np.array(ndimage.center_of_mass(binary, labels, keep))
    return labels, np.array(boxes, np.int32), cents, np.array(ars, np.int64)


def crop_counts(cent: np.ndarray, H: int, W: int, seed: int):
    """학습 RandomCrop / 평가 CenterCrop 안에 «중심»이 들어오는 개체 수."""
    rng = np.random.default_rng(seed)
    Hp, Wp = max(H, CROP), max(W, CROP)
    n_rand = []
    for _ in range(N_RANDOM_CROPS):
        top = int(rng.integers(0, Hp - CROP + 1))
        left = int(rng.integers(0, Wp - CROP + 1))
        n_rand.append(0 if len(cent) == 0 else int((
            (cent[:, 0] >= top) & (cent[:, 0] < top + CROP) &
            (cent[:, 1] >= left) & (cent[:, 1] < left + CROP)).sum()))
    ct, cl = (Hp - CROP) // 2, (Wp - CROP) // 2
    n_cen = 0 if len(cent) == 0 else int((
        (cent[:, 0] >= ct) & (cent[:, 0] < ct + CROP) &
        (cent[:, 1] >= cl) & (cent[:, 1] < cl + CROP)).sum())
    return n_rand, n_cen


def one_image(args):
    fruit, mpath, min_distance, seed = args
    raw = load_mask(Path(mpath))
    H, W = raw.shape
    binary = raw > 0
    _, boxes, cent, areas = detect(binary, min_distance)

    n_exact = None
    if fruit == "apple":
        ids, cnts = np.unique(raw, return_counts=True)
        n_exact = int(((ids > 0) & (cnts >= MIN_AREA)).sum())

    n_rand, n_cen = crop_counts(cent, H, W, seed)
    return {
        "stem": Path(mpath).stem, "H": H, "W": W,
        "n_det": int(len(boxes)), "n_exact": n_exact,
        "fg_ratio": float(binary.sum()) / (H * W),
        "areas": areas.tolist(), "boxes": boxes.tolist(),
        "n_rand": n_rand, "n_center": n_cen,
    }


def run_fruit(fruit: str, masks: list[Path], md: int, workers: int):
    tasks = [(fruit, str(p), md, i) for i, p in enumerate(masks)]
    with mp.Pool(workers) as pool:
        return pool.map(one_image, tasks, chunksize=4)


def calibrate(median_diam: float, workers: int, n_img: int) -> tuple[float, list]:
    """사과 정답으로 계수 f 를 고른다. min_distance = f x 지름중앙값."""
    masks = sorted(p for p in (POOL / "apple" / "masks").iterdir() if p.is_file())[:n_img]
    rows = []
    print(f"[보정] 사과 {len(masks)}장으로 계수 f 를 훑습니다 "
          f"(지름 중앙값 {median_diam:.1f}px)", flush=True)
    for f in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60):
        md = max(1, int(round(f * median_diam)))
        recs = run_fruit("apple", masks, md, workers)
        det = np.array([r["n_det"] for r in recs], float)
        ex = np.array([r["n_exact"] for r in recs], float)
        ratio = det.sum() / ex.sum()
        mae = float(np.abs(det - ex).mean())
        rows.append({"f": f, "min_distance": md, "det_over_exact": float(ratio),
                     "abs_err_per_image": mae})
        print(f"   f={f:.2f} (min_dist={md:2d}) → 정답 대비 {ratio * 100:6.1f}% "
              f"| 장당 오차 {mae:5.1f}개", flush=True)
    best = min(rows, key=lambda r: abs(r["det_over_exact"] - 1.0))
    print(f"[보정] 선택 f = {best['f']} (정답 대비 {best['det_over_exact'] * 100:.1f}%)",
          flush=True)
    return best["f"], rows


def summarize(recs, fruit, md, f):
    n = np.array([r["n_det"] for r in recs])
    ar = np.concatenate([np.array(r["areas"]) for r in recs]) if recs else np.zeros(0)
    rand = np.concatenate([np.array(r["n_rand"]) for r in recs])
    cen = np.array([r["n_center"] for r in recs])
    out = {
        "fruit": fruit, "kor": KOR[fruit], "unit": UNIT[fruit],
        "images": len(recs), "objects_total": int(n.sum()),
        "min_distance": md, "f": f,
        "per_image": {"mean": float(n.mean()), "median": float(np.median(n)),
                      "min": int(n.min()), "max": int(n.max()),
                      "ge50_pct": float((n >= 50).mean() * 100),
                      "ge100_pct": float((n >= 100).mean() * 100)},
        "area_px": {"median": float(np.median(ar)) if len(ar) else 0.0},
        "diameter_px_median": float(2 * np.sqrt(np.median(ar) / np.pi)) if len(ar) else 0.0,
        "fg_ratio_mean_pct": float(np.mean([r["fg_ratio"] for r in recs]) * 100),
        "random_crop_512": {"mean": float(rand.mean()),
                            "zero_pct": float((rand == 0).mean() * 100)},
        "center_crop_512": {"mean": float(cen.mean()),
                            "ge1_pct": float((cen >= 1).mean() * 100)},
        "per_image_counts": n.tolist(),
        "per_image_center": cen.tolist(),
    }
    if fruit == "apple":
        ex = np.array([r["n_exact"] for r in recs], float)
        out["gt_validation"] = {
            "note": "마스크 인스턴스ID(정답) vs watershed 디텍션",
            "exact_mean": float(ex.mean()), "det_mean": float(n.mean()),
            "det_over_exact_pct": float(n.sum() / ex.sum() * 100),
            "abs_err_per_image": float(np.abs(n - ex).mean()),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruits", nargs="+", default=FRUITS)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--calib-images", type=int, default=120)
    ap.add_argument("--f", type=float, default=None, help="보정 건너뛰고 계수 직접 지정")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    cc = json.loads(CCSTATS.read_text())
    diam = {k: cc["fruits"][k]["diameter_px_median"] for k in FRUITS}

    if a.f is None:
        f, calib_rows = calibrate(diam["apple"], a.workers, a.calib_images)
    else:
        f, calib_rows = a.f, []

    result = {
        "generated_by": "tools/detect_objects_4fruits.py",
        "method": {
            "algorithm": "distance transform + watershed instance separation",
            "why": "세그멘테이션 마스크에는 바운딩 박스가 없어서(교수님 04:02) 알고리즘으로 만든다",
            "min_distance_rule": "f x (그 과일 개체 지름 중앙값)",
            "f": f, "calibrated_on": "apple instance-ID ground truth",
            "min_area_px": MIN_AREA,
            "outputs": "개체별 bounding box + centroid + area",
        },
        "calibration": calib_rows,
        "fruits": {},
    }

    BOXDIR.mkdir(parents=True, exist_ok=True)
    for fruit in a.fruits:
        md = max(1, int(round(f * diam[fruit])))
        masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
        if a.limit:
            masks = masks[:a.limit]
        print(f"[{fruit}] {len(masks)}장 · 지름중앙 {diam[fruit]:.1f}px → "
              f"min_distance {md}px", flush=True)
        recs = run_fruit(fruit, masks, md, a.workers)
        s = summarize(recs, fruit, md, f)
        result["fruits"][fruit] = s

        # 바운딩 박스 전량 보관 (교수님 14:56 "지워버리지 말고 보관")
        stems = np.array([r["stem"] for r in recs])
        counts = np.array([r["n_det"] for r in recs])
        allb = np.concatenate([np.array(r["boxes"], np.int32).reshape(-1, 4)
                               for r in recs]) if recs else np.zeros((0, 4), np.int32)
        np.savez_compressed(BOXDIR / f"{fruit}_boxes.npz",
                            stems=stems, counts=counts, boxes=allb, min_distance=md)
        p = s["per_image"]
        print(f"  → 장당 평균 {p['mean']:.1f}{UNIT[fruit]} "
              f"(중앙 {p['median']:.0f}, 최대 {p['max']}) | 박스 {len(allb):,}개 저장",
              flush=True)
        if "gt_validation" in s:
            v = s["gt_validation"]
            print(f"  → [정답 대조] 정답 {v['exact_mean']:.1f} vs 디텍션 {v['det_mean']:.1f} "
                  f"= {v['det_over_exact_pct']:.1f}%", flush=True)

    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(f"\n저장: {a.out}\n박스: {BOXDIR}/<fruit>_boxes.npz")


if __name__ == "__main__":
    main()
