#!/usr/bin/env python
"""datasets_resized_2mp/manifest.json 재생성 (읽기 전용 측정 → json 쓰기만).

2026-08-07 포도 교체 때 manifest.json이 포도 것만 남도록 덮어써졌습니다.
이 스크립트는 **이미지를 다시 만들지 않고**, 이미 만들어져 있는 리사이즈본과
원본 폴더의 크기를 실제로 재서 manifest 를 다시 씁니다.

- 리사이즈본 파일은 읽기만 합니다. 절대 수정/삭제하지 않습니다.
- 원본 폴더도 읽기만 합니다.

사용:
    python tools/rebuild_resized_manifest.py
    python tools/rebuild_resized_manifest.py --dry-run
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

BASE = Path("/data/project/2026summer/kds0206")
POOL_ROOT = BASE / "datasets_resized_2mp"
TARGET_PIXELS = 1440 * 1440
MULTIPLE_OF = 8
# EXIF Orientation 을 실제로 담는 형식만. PNG/BMP 에서 getexif() 를 부르면 매우 느립니다.
EXIF_FORMATS = {"JPEG", "MPO", "TIFF"}

# 과일별 원본 위치. 리스트 안의 폴더를 전부 뒤져 stem 으로 원본을 찾습니다.
SOURCES: dict[str, dict] = {
    "blueberry": {
        "dirs": [BASE / "dataset_6fold/cv1" / s / "images" for s in ("train", "val", "test")],
        "mask_note": "RGB 3채널, 값 0/255 (이진)",
        # 2026-08-08 곽동신 지시로 4K 128장도 1080x1920 으로 변환해 풀에 추가 → 제외분 0.
        # (0806 미팅 03:24 에는 제외하기로 했었음. tools/add_blueberry_4k_128.py 참조)
        "dropped_reason": None,
        "src_note": "2026-08-08 곽동신 지시로 4K(2160x3840) Camera 4 128장을 1080x1920 으로 "
                    "변환해 추가함(1,067 → 1,195). 0806 미팅에서는 제외하기로 했던 분량. "
                    "같은 날 팀 요청으로 분할도 1,195장 전량 7:1:2 로 다시 뜸 "
                    "(splits/blueberry/, 영상 단위 · tools/make_blueberry_folds_712.py). "
                    "옛 분할 두 벌은 splits/_old_blueberry_* 에 보관",
    },
    "apple": {
        "dirs": [BASE / "연구실 블루베리/dataset_minneapple" / s / "images" for s in ("train", "val", "test")],
        "mask_note": "인스턴스 ID (0=배경, 1..N=사과 개체번호). 학습 시 >0 으로 이진화됨",
        "dropped_reason": None,
    },
    "peach": {
        "dirs": [BASE / "연구실 블루베리/datasets_verified/peach_semseg" / s / "images" for s in ("train", "val", "test")],
        "mask_note": "1채널, 값 0/255 (이진)",
        "dropped_reason": None,
    },
    "grape": {
        "dirs": [BASE / "incoming/certh_grape_full_1920/images"],
        "mask_note": "1채널, 값 0/255 (이진). 성숙도 3클래스를 하나로 합친 것",
        "dropped_reason": "single-instance-one-class 100장 (한 장에 한 송이만) 제외",
        # ⚠️ 여기 적힌 src 는 '진짜 원본'이 아니라 중간 산출물입니다.
        # CERTH 진짜 원본은 2160x3840 (share_grape_certh/CERTH_images.zip) 이고,
        # prepare_certh_grape.py 가 zip 에서 직접 1080x1920 으로 뽑아 이 폴더를 만듭니다.
        # 그래서 아래 records 의 scale 이 1.0 으로 찍히지만 실제로는 2160x3840 → 1080x1920 (0.5배)입니다.
        "src_note": "src 는 중간 산출물(이미 1080x1920). 진짜 원본은 CERTH zip 의 2160x3840 → 0.5배 축소됨",
    },
}


def index_sources(dirs: list[Path]) -> dict[str, Path]:
    """stem -> 원본 경로. 앞 폴더가 우선."""
    idx: dict[str, Path] = {}
    for d in dirs:
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if p.is_file() and p.stem not in idx:
                idx[p.stem] = p
    return idx


def size_of(path: Path) -> tuple[int, int]:
    """EXIF 회전을 적용한 실제 표시 크기.

    ImageOps.exif_transpose() 는 이미지를 통째로 디코딩해서 매우 느립니다
    (4K BMP 수천 장이면 수십 분). 여기서는 **헤더만 읽고** Orientation 태그
    (0x0112)가 5~8(=90도 회전 계열)일 때만 가로세로를 맞바꿉니다.

    ⚠️ PNG 에서 getexif() 를 부르면 Pillow 가 파일 전체를 읽어 장당 90ms 가 걸립니다
    (실측). EXIF Orientation 을 실제로 갖는 JPEG/TIFF 에서만 호출합니다.
    """
    with Image.open(path) as im:
        w, h = im.size
        if im.format in EXIF_FORMATS:
            try:
                if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):
                    w, h = h, w
            except Exception:
                pass
        return w, h


def build_fruit(fruit: str, cfg: dict) -> dict:
    pool_img = POOL_ROOT / fruit / "images"
    pool_msk = POOL_ROOT / fruit / "masks"
    src_idx = index_sources(cfg["dirs"])

    records: dict[str, dict] = {}
    out_sizes: Counter = Counter()
    src_sizes: Counter = Counter()
    aspect_err: list[float] = []
    px_ratio: list[float] = []
    missing_src: list[str] = []
    mask_mismatch: list[str] = []

    for p in sorted(pool_img.iterdir()):
        if not p.is_file():
            continue
        stem = p.stem
        ow, oh = size_of(p)
        out_sizes[f"{ow}x{oh}"] += 1

        mpath = pool_msk / f"{stem}.png"
        if not mpath.exists():
            cand = list(pool_msk.glob(f"{stem}.*"))
            mpath = cand[0] if cand else None
        if mpath is None or size_of(mpath) != (ow, oh):
            mask_mismatch.append(stem)

        rec = {
            "stem": stem,
            "out_size": [ow, oh],
            "out_megapixels": round(ow * oh / 1e6, 4),
            "out_pixels": ow * oh,
            "pixels_vs_target": round(ow * oh / TARGET_PIXELS, 6),
        }

        src = src_idx.get(stem)
        if src is None:
            missing_src.append(stem)
        else:
            sw, sh = size_of(src)
            src_sizes[f"{sw}x{sh}"] += 1
            distortion = (ow / oh) / (sw / sh)
            aspect_err.append(abs(distortion - 1.0))
            rec.update(
                {
                    "src": str(src),
                    "src_size": [sw, sh],
                    "src_megapixels": round(sw * sh / 1e6, 4),
                    "scale": round((ow * oh / (sw * sh)) ** 0.5, 4),
                    "aspect_distortion": round(distortion, 6),
                }
            )
        px_ratio.append(ow * oh / TARGET_PIXELS)
        records[stem] = rec

    used = len(records)
    total_src = sum(1 for d in cfg["dirs"] if d.exists() for _ in d.iterdir())
    return {
        "source_dirs": [str(d) for d in cfg["dirs"]],
        "src_note": cfg.get("src_note"),
        "mask_note": cfg["mask_note"],
        "images_total_source": total_src,
        "images_used": used,
        "images_dropped": max(0, total_src - used),
        "dropped_reason": cfg["dropped_reason"],
        "pool": str(POOL_ROOT / fruit),
        "src_sizes": dict(src_sizes.most_common()),
        "output_sizes": dict(out_sizes.most_common()),
        "aspect_distortion_max": round(max(aspect_err), 6) if aspect_err else None,
        "pixels_vs_target_min": round(min(px_ratio), 6) if px_ratio else None,
        "pixels_vs_target_max": round(max(px_ratio), 6) if px_ratio else None,
        "missing_source": missing_src,
        "mask_size_mismatch": mask_mismatch,
        "records": records,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 요약만 출력")
    ap.add_argument("--out", default=str(POOL_ROOT / "manifest.json"))
    args = ap.parse_args()

    fruits = {}
    for fruit, cfg in SOURCES.items():
        if not (POOL_ROOT / fruit / "images").exists():
            print(f"[skip] {fruit}: 풀 폴더 없음")
            continue
        fruits[fruit] = build_fruit(fruit, cfg)
        f = fruits[fruit]
        print(
            f"[{fruit:10s}] 사용 {f['images_used']:>5} / 원본 {f['images_total_source']:>5}"
            f" | 해상도 {len(f['output_sizes'])}종"
            f" | 비율왜곡 최대 {f['aspect_distortion_max']}"
            f" | 화소 {f['pixels_vs_target_min']}~{f['pixels_vs_target_max']}"
            f" | 원본없음 {len(f['missing_source'])} | 마스크불일치 {len(f['mask_size_mismatch'])}"
        )

    doc = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generated_by": "tools/rebuild_resized_manifest.py (실제 파일 측정으로 재생성)",
        "mode": "aspect-preserving, equal pixel count",
        "target_pixels": TARGET_PIXELS,
        "multiple_of": MULTIPLE_OF,
        "note": "0806 교수님미팅 지시. 비율 유지 + 총 화소 수 1440x1440 기준으로 통일",
        "totals": {
            "images": sum(f["images_used"] for f in fruits.values()),
            "fruits": len(fruits),
        },
        "fruits": fruits,
    }

    if args.dry_run:
        print("\n[dry-run] 파일 쓰지 않음")
        return
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {args.out}  (총 {doc['totals']['images']}장)")


if __name__ == "__main__":
    main()
