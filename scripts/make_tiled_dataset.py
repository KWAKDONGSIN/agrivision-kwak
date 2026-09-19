#!/usr/bin/env python
"""
4과일 데이터셋을 «겉보기 크기 통일 + 512x512 격자 타일링» 으로 재구성합니다.

목적 (2026-08-09 곽동신 지시):
  "실험을 하려면 데이터셋이 동일해 보이는 게 좋다"
  → ① 열매가 화면에 비슷한 크기로 보이도록 과일별 배율을 맞추고
    ② 모든 표본을 512x512 라는 «완전히 같은 규격» 조각으로 자른다.

⛔ 원본은 한 장도 건드리지 않습니다.
   입력  : datasets_resized_2mp/            (팀 표준, 읽기 전용)
   출력  : datasets_tiled_512/              (새 폴더)

핵심 설계
  - 배율 s = TARGET_DIAM / (과일별 개체 지름 중앙값)
  - 잘라낼 창 window = round(512 / s)  →  창을 512 로 리사이즈 = 배율 s 적용과 동일
    (이미지를 통째로 늘렸다 자르는 것과 결과는 같고, 메모리를 훨씬 덜 씁니다)
  - window 가 이미지 짧은 변보다 크면 이미지 크기로 clamp (없는 화각은 만들 수 없음)
  - 격자는 «완전 덮기» — n = ceil(변길이/window), 남으면 겹치게 배치. 잘려나가는 영역 0
  - 빈 타일(열매 0)도 버리지 않고 저장 + index.csv 에 전경비를 기록해 나중에 고를 수 있게

사용:
    $PY tools/make_tiled_dataset.py --measure-only   # 배율만 계산해서 출력
    $PY tools/make_tiled_dataset.py                  # 타일 생성 + 폴드 링크
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None

SRC = Path("/data/project/2026summer/kds0206/datasets_resized_2mp")
DST = Path("/data/project/2026summer/kds0206/datasets_tiled_512")
FRUITS = ["blueberry", "apple", "peach", "grape"]
TILE = 512
# 목표: 열매 하나가 화면에서 지름 72px 로 보이게.
# 72 라는 숫자의 근거 — 포도는 1080px 짧은 변에 개체 지름 150px 이라 아무리 줄여도
# 512/1080 배가 한계(= 71.2px). 그보다 작은 목표를 잡으면 «찍히지도 않은 화각»이 필요해집니다.
# 즉 72px = 네 데이터셋 어디서도 없는 화면을 지어내지 않는 «가장 작은 목표 크기».
TARGET_DIAM = 72.0
COVER = 0.97            # 격자가 덮어야 할 최소 비율. 가장자리 3%까지는 버림
#                         (안 그러면 거의 똑같은 타일이 한 줄 더 생겨 중복이 됨)
MIN_BLOB = 30           # 이보다 작은 덩어리는 잡음으로 보고 크기 통계에서 제외
MEASURE_N = 400         # 과일당 크기 측정 표본 수 (전수가 이보다 적으면 전수)
SEED = 20260809


# ─────────────────────────────────────────────────────────── 1. 겉보기 크기 측정

def _diam_of(mask_path: Path) -> float | None:
    """마스크 한 장에서 개체 지름(등가원 지름)의 중앙값을 px 로 반환."""
    a = np.array(Image.open(mask_path).convert("L"))
    b = a > 0
    if not b.any():
        return None
    lab, n = ndimage.label(b)
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())[1:]
    sizes = sizes[sizes >= MIN_BLOB]
    if sizes.size == 0:
        return None
    return float(np.median(2.0 * np.sqrt(sizes / math.pi)))


def measure(fruit: str) -> dict:
    masks = sorted((SRC / fruit / "masks").glob("*.png"))
    rng = random.Random(SEED)
    sample = masks if len(masks) <= MEASURE_N else rng.sample(masks, MEASURE_N)
    with Pool(8) as pool:
        diams = [d for d in pool.map(_diam_of, sample) if d is not None]
    med = float(np.median(diams))
    return {
        "n_masks_total": len(masks),
        "n_measured": len(diams),
        "diam_median_px": round(med, 2),
        "diam_p25_px": round(float(np.percentile(diams, 25)), 2),
        "diam_p75_px": round(float(np.percentile(diams, 75)), 2),
        "scale": round(TARGET_DIAM / med, 4),
        "window_px": int(round(TILE / (TARGET_DIAM / med))),
    }


# ─────────────────────────────────────────────────────────── 2. 격자 좌표

def grid_starts(length: int, window: int) -> list[int]:
    """[0, length) 를 window 크기 창으로 덮는 시작좌표들.

    최소 COVER(97%) 를 덮는 «가장 적은 개수»를 쓰고, 남는 만큼은 창끼리 균등하게 겹칩니다.
    이렇게 하면 예를 들어 1080px 을 1067px 창으로 덮을 때 거의 똑같은 타일 두 장이
    생기는 낭비를 막습니다 (13px 가장자리 = 1.2% 만 포기).
    """
    if window >= length:
        return [0]
    n = max(1, math.ceil(length * COVER / window))
    if n == 1:
        return [(length - window) // 2]      # 한 장이면 가운데
    step = (length - window) / (n - 1)
    return [int(round(i * step)) for i in range(n)]


# ─────────────────────────────────────────────────────────── 3. 타일 생성

def tile_one(job: tuple) -> list[tuple]:
    fruit, stem, window_req = job
    img_p = SRC / fruit / "images" / f"{stem}.png"
    msk_p = SRC / fruit / "masks" / f"{stem}.png"

    img = Image.open(img_p).convert("RGB")
    msk = Image.open(msk_p).convert("L")
    if msk.size != img.size:
        msk = msk.resize(img.size, Image.NEAREST)
    W, H = img.size

    # 없는 화각은 만들 수 없으므로 창은 이미지 안쪽으로 제한
    window = min(window_req, W, H)

    out_img_dir = DST / fruit / "images"
    out_msk_dir = DST / fruit / "masks"

    rows = []
    for r, y in enumerate(grid_starts(H, window)):
        for c, x in enumerate(grid_starts(W, window)):
            box = (x, y, x + window, y + window)
            ti = img.crop(box).resize((TILE, TILE), Image.BILINEAR)
            tm = msk.crop(box).resize((TILE, TILE), Image.NEAREST)
            tm = Image.fromarray(((np.array(tm) > 0).astype(np.uint8) * 255), mode="L")

            name = f"{stem}__r{r}c{c}.png"
            ti.save(out_img_dir / name, optimize=False, compress_level=3)
            tm.save(out_msk_dir / name, optimize=False, compress_level=3)

            fg = float((np.array(tm) > 0).mean())
            rows.append((fruit, name, stem, r, c, window, round(fg * 100, 4)))
    return rows


# ─────────────────────────────────────────────────────────── 4. 폴드 링크

def link_splits(fruit: str, tiles_by_stem: dict[str, list[str]]) -> dict:
    """원본 splits/<fruit>/cv*/{train,val,test} 의 «장 단위» 배정을 타일에 그대로 물려줍니다.
    같은 사진에서 나온 타일은 반드시 같은 split 으로 갑니다 (누수 방지)."""
    src_splits = SRC / "splits" / fruit
    dst_splits = DST / "splits" / fruit
    report = {}
    if not src_splits.is_dir():
        return report

    for cv in sorted(p for p in src_splits.iterdir() if p.is_dir()):
        rep = {}
        for split in ("train", "val", "test"):
            src_dir = cv / split / "images"
            if not src_dir.is_dir():
                continue
            out_i = dst_splits / cv.name / split / "images"
            out_m = dst_splits / cv.name / split / "masks"
            out_i.mkdir(parents=True, exist_ok=True)
            out_m.mkdir(parents=True, exist_ok=True)

            n = 0
            for f in src_dir.iterdir():
                for tname in tiles_by_stem.get(f.stem, []):
                    for out_dir, kind in ((out_i, "images"), (out_m, "masks")):
                        link = out_dir / tname
                        if not link.is_symlink() and not link.exists():
                            os.symlink(f"../../../../../{fruit}/{kind}/{tname}", link)
                    n += 1
            rep[split] = n
        report[cv.name] = rep
    return report


# ─────────────────────────────────────────────────────────── main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure-only", action="store_true")
    ap.add_argument("--fruits", nargs="*", default=FRUITS)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    print(f"[+] 목표 개체 지름 = {TARGET_DIAM:.0f}px, 타일 = {TILE}x{TILE}")
    print(f"[+] 입력 {SRC}  (읽기 전용)")
    print(f"[+] 출력 {DST}\n")

    plan = {}
    for fruit in args.fruits:
        m = measure(fruit)
        plan[fruit] = m
        print(f"  {fruit:10s} 개체지름 {m['diam_median_px']:6.1f}px "
              f"→ 배율 {m['scale']:.3f}  잘라낼 창 {m['window_px']}px "
              f"(표본 {m['n_measured']}/{m['n_masks_total']}장)")

    if args.measure_only:
        print("\n[measure-only] 파일은 만들지 않았습니다.")
        return

    manifest = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generated_by": "tools/make_tiled_dataset.py",
        "purpose": "겉보기 크기 통일 + 512x512 격자 타일링 (실험용 후보 데이터셋)",
        "source": str(SRC),
        "source_untouched": True,
        "tile": TILE,
        "target_object_diameter_px": TARGET_DIAM,
        "min_blob_px": MIN_BLOB,
        "seed": SEED,
        "mask_format": "1채널 L, 0/255 이진 (4과일 전부 통일. 사과의 인스턴스 ID는 >0 으로 이진화)",
        "fruits": {},
    }

    for fruit in args.fruits:
        (DST / fruit / "images").mkdir(parents=True, exist_ok=True)
        (DST / fruit / "masks").mkdir(parents=True, exist_ok=True)

        stems = sorted(p.stem for p in (SRC / fruit / "images").glob("*.png"))
        window = plan[fruit]["window_px"]
        jobs = [(fruit, s, window) for s in stems]

        print(f"\n[+] {fruit}: 원본 {len(stems)}장 → 타일 생성 중 (창 {window}px)...")
        rows: list[tuple] = []
        with Pool(args.workers) as pool:
            for i, out in enumerate(pool.imap_unordered(tile_one, jobs, chunksize=8), 1):
                rows.extend(out)
                if i % 200 == 0:
                    print(f"    {i}/{len(stems)}장  (타일 {len(rows)}개)", flush=True)

        rows.sort(key=lambda r: r[1])
        idx = DST / fruit / "index.csv"
        with open(idx, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["fruit", "tile", "src_stem", "row", "col", "window_px", "fg_percent"])
            w.writerows(rows)

        fgs = np.array([r[6] for r in rows])
        tiles_by_stem: dict[str, list[str]] = {}
        for r in rows:
            tiles_by_stem.setdefault(r[2], []).append(r[1])

        print(f"    타일 {len(rows)}개 완료. 빈 타일 {int((fgs == 0).sum())}개 "
              f"({(fgs == 0).mean() * 100:.1f}%), 평균 전경 {fgs.mean():.2f}%")

        print(f"[+] {fruit}: 폴드 링크 생성 중...")
        split_report = link_splits(fruit, tiles_by_stem)

        manifest["fruits"][fruit] = {
            **plan[fruit],
            "src_images": len(stems),
            "tiles": len(rows),
            "tiles_per_image": round(len(rows) / max(1, len(stems)), 2),
            "empty_tiles": int((fgs == 0).sum()),
            "empty_tile_percent": round(float((fgs == 0).mean() * 100), 2),
            "fg_percent_mean": round(float(fgs.mean()), 3),
            "fg_percent_median": round(float(np.median(fgs)), 3),
            "splits": split_report,
        }
        with open(DST / "manifest.json", "w") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)

    tot = sum(v["tiles"] for v in manifest["fruits"].values())
    manifest["totals"] = {"tiles": tot,
                          "src_images": sum(v["src_images"] for v in manifest["fruits"].values())}
    with open(DST / "manifest.json", "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"\n[✓] 전체 완료 — 타일 {tot:,}개")
    print(f"    manifest: {DST / 'manifest.json'}")


if __name__ == "__main__":
    sys.exit(main())
