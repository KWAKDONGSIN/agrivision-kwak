#!/usr/bin/env python
"""
0806 교수님미팅 지시 ①: 4개 데이터셋의 해상도를 전수 조사한다.

교수님 말씀 요지
  - 블루베리는 해상도가 1440계열과 4K 두 종류로 섞여 있다 → 4K(과실 클로즈업)는 뺀다
  - 복숭아는 해상도가 6종이나 된다
  - 최종적으로 "총 화소 개수"를 1440x1440(=2,073,600)에 맞춰 비율 유지 리사이즈한다

이 스크립트는 추정하지 않는다. 모든 이미지 파일을 열어 (width, height)를 직접 읽는다.
PIL의 open()은 헤더만 읽으므로 픽셀을 디코딩하지 않아 4K여도 빠르다.

출력: output/dataset_resolution_survey.json  (+ 표준출력 요약표)
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None  # 4K 이상도 경고 없이 열기

ROOT = Path("/data/project/2026summer/kds0206")

# 조사 대상. (표시이름, 이미지가 들어있는 폴더들)
TARGETS: dict[str, list[Path]] = {
    "blueberry": [
        ROOT / "dataset_6fold/cv1/train/images",
        ROOT / "dataset_6fold/cv1/val/images",
        ROOT / "dataset_6fold/cv1/test/images",
    ],
    "peach": [
        ROOT / "연구실 블루베리/datasets_verified/peach_semseg/train/images",
        ROOT / "연구실 블루베리/datasets_verified/peach_semseg/val/images",
        ROOT / "연구실 블루베리/datasets_verified/peach_semseg/test/images",
    ],
    "apple_minneapple": [
        ROOT / "dataset_minneapple/train/images",
        ROOT / "dataset_minneapple/val/images",
        ROOT / "dataset_minneapple/test/images",
    ],
    "grape_certh_toy100": [
        ROOT / "dataset_certh_grape_toy100/images",
    ],
}

IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

TARGET_PIXELS = 1440 * 1440  # 2,073,600 — 교수님이 제시한 기준 화소 수


def exif_aware_size(path: Path) -> tuple[int, int]:
    """EXIF Orientation을 반영한 실제 표시 크기를 돌려준다.

    FruitSeg30 Guava에서 EXIF 90도 회전 때문에 이미지-마스크가 어긋난 전례가 있어
    (2026-07-25 작업기록) 여기서도 EXIF를 반영해 센다.
    """
    with Image.open(path) as im:
        w, h = im.size
        try:
            orientation = im.getexif().get(0x0112, 1)
        except Exception:
            orientation = 1
    if orientation in (5, 6, 7, 8):
        w, h = h, w
    return w, h


def scan_dir(d: Path) -> list[tuple[str, int, int]]:
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.iterdir()):
        if p.suffix.lower() not in IMG_EXT:
            continue
        try:
            w, h = exif_aware_size(p)
        except Exception as e:  # 깨진 파일은 건너뛰되 표시
            print(f"  [!] 열기 실패: {p} ({e})")
            continue
        out.append((p.name, w, h))
    return out


def aspect_label(w: int, h: int) -> str:
    from math import gcd

    g = gcd(w, h)
    return f"{w // g}:{h // g}"


def resize_to_target(w: int, h: int, target_px: int = TARGET_PIXELS,
                     multiple: int = 32) -> tuple[int, int]:
    """총 화소 수가 target_px에 가깝도록 비율을 유지해 줄인 크기.

    딥러닝 백본이 입력을 2배씩 5번 줄이므로(stride 32) 변의 길이를 32의 배수로
    맞춰 두면 패딩으로 인한 미세한 어긋남이 없다.
    """
    scale = (target_px / (w * h)) ** 0.5
    nw = max(multiple, int(round(w * scale / multiple)) * multiple)
    nh = max(multiple, int(round(h * scale / multiple)) * multiple)
    return nw, nh


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "semantic-segmentation/output/dataset_resolution_survey.json"))
    args = ap.parse_args()

    report: dict[str, dict] = {}

    for name, dirs in TARGETS.items():
        records: list[tuple[str, int, int]] = []
        per_split = {}
        for d in dirs:
            got = scan_dir(d)
            split = d.parent.name if d.parent.name in {"train", "val", "test"} else d.name
            per_split[split] = len(got)
            records.extend(got)

        if not records:
            print(f"[{name}] 이미지를 찾지 못했습니다: {[str(d) for d in dirs]}")
            continue

        sizes = Counter((w, h) for _, w, h in records)
        entries = []
        for (w, h), n in sizes.most_common():
            nw, nh = resize_to_target(w, h)
            entries.append({
                "width": w, "height": h, "count": n,
                "megapixels": round(w * h / 1e6, 3),
                "aspect": aspect_label(w, h),
                "ratio_to_target": round(w * h / TARGET_PIXELS, 3),
                "resized_to": [nw, nh],
                "resized_megapixels": round(nw * nh / 1e6, 3),
                "example": next(fn for fn, ww, hh in records if (ww, hh) == (w, h)),
            })

        report[name] = {
            "total_images": len(records),
            "per_split": per_split,
            "distinct_resolutions": len(sizes),
            "resolutions": entries,
        }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"target_pixels": TARGET_PIXELS, "datasets": report}, f, indent=2, ensure_ascii=False)

    # ---- 사람이 읽는 요약 ----
    print()
    print("=" * 96)
    print(f"해상도 전수 조사  (기준 화소 수 = 1440x1440 = {TARGET_PIXELS:,})")
    print("=" * 96)
    for name, info in report.items():
        print(f"\n■ {name}  —  총 {info['total_images']:,}장, 해상도 {info['distinct_resolutions']}종")
        print(f"   분할: {info['per_split']}")
        print(f"   {'해상도':>13} {'장수':>7} {'MP':>7} {'비율':>8} {'기준대비':>8}   → 리사이즈 후")
        print("   " + "-" * 88)
        for e in info["resolutions"]:
            print(f"   {e['width']:>5}x{e['height']:<7} {e['count']:>7,} {e['megapixels']:>7.2f} "
                  f"{e['aspect']:>8} {e['ratio_to_target']:>8.2f}배   → "
                  f"{e['resized_to'][0]}x{e['resized_to'][1]} ({e['resized_megapixels']:.2f}MP)")
    print()
    print(f"저장: {args.out}")


if __name__ == "__main__":
    main()
