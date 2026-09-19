#!/usr/bin/env python
"""블루베리 4K(2160x3840, Camera 4) 128장을 규격에 맞춰 리사이즈해 풀에 추가한다.

배경
----
2026-08-06 교수님미팅에서 이 128장은 **제외**하기로 했습니다(03:24 "그거는 빼는 게 맞네요").
제외 사유는 해상도가 아니라 **촬영 구도**였습니다 — 곽동신이 03:02 에
"포케이 사진은 이렇게 딱 블루베리만 찍어놓은 거더라고요" 라고 보고했고,
교수님이 03:36 에 "저게 우리가 말했던 약간 **사람의 눈높이**에서" 라고 하신 흐름입니다.
(포도 CERTH 도 원본이 2160x3840 4K 지만 포도밭 전경이라 전량 사용했습니다.)

2026-08-08 곽동신 지시로 **이 128장도 같은 규격(2,073,600 화소)으로 변환**합니다.
2160x3840 은 9:16 이라 정확히 **1080x1920 (0.5배)** 로 떨어집니다. 비율 왜곡 0, 반올림 0.

🔴 이 스크립트의 «분할 만들기» 부분은 2026-08-08 오후에 폐기되었습니다
---------------------------------------------------------------------
팀 요청으로 블루베리 분할을 **1,195장 전량 7:1:2** 로 다시 떴습니다.
지금 팀 표준 분할을 만드는 스크립트는 **`tools/make_blueberry_folds_712.py`** 입니다.
이 스크립트는 «128장 리사이즈» 기록용으로만 남겨둡니다. 다시 돌리실 일이 있으면
반드시 `--skip-splits` 를 붙이세요. 안 붙이면 폐기된 `splits/blueberry_full1195/` 가
되살아납니다(팀 표준 `splits/blueberry/` 를 덮어쓰지는 않습니다).

안전장치
--------
- 이미 풀에 있는 1,067장은 **건드리지 않습니다.** 같은 이름이 있으면 즉시 중단합니다.
- 분할은 `splits/blueberry_full1195/` 에만 씁니다 (위 경고 참고).
- 원본 `dataset_6fold/` 는 읽기만 합니다.

사용:
    python tools/add_blueberry_4k_128.py --dry-run
    python tools/add_blueberry_4k_128.py
    python tools/add_blueberry_4k_128.py --skip-splits   # 리사이즈만
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

BASE = Path("/data/project/2026summer/kds0206")
SRC_ROOT = BASE / "dataset_6fold"          # 원본 6폴드 (읽기 전용)
POOL = BASE / "datasets_resized_2mp/blueberry"
SPLIT_ROOT = BASE / "datasets_resized_2mp/splits"
NEW_SPLIT = SPLIT_ROOT / "blueberry_full1195"

TARGET_PIXELS = 1440 * 1440
MULTIPLE = 8
FOURK = (2160, 3840)
FOLDS = [f"cv{i}" for i in range(1, 7)]
PARTS = ["train", "val", "test"]
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def exif_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        w, h = im.size
        try:
            orientation = im.getexif().get(0x0112, 1) if im.format in {"JPEG", "MPO", "TIFF"} else 1
        except Exception:
            orientation = 1
    return (h, w) if orientation in (5, 6, 7, 8) else (w, h)


def target_size(w: int, h: int) -> tuple[int, int]:
    """비율 유지 + 총 화소를 TARGET_PIXELS 에 맞춤 (원 스크립트와 동일한 계산)."""
    scale = (TARGET_PIXELS / (w * h)) ** 0.5
    nw = max(MULTIPLE, int(round(w * scale / MULTIPLE)) * MULTIPLE)
    nh = max(MULTIPLE, int(round(h * scale / MULTIPLE)) * MULTIPLE)
    return nw, nh


def find_4k_pairs() -> dict[str, tuple[Path, Path]]:
    """dataset_6fold 전체에서 2160x3840 인 (이미지, 마스크) 쌍을 stem 으로 모은다."""
    pairs: dict[str, tuple[Path, Path]] = {}
    for cv in FOLDS:
        for part in PARTS:
            idir, mdir = SRC_ROOT / cv / part / "images", SRC_ROOT / cv / part / "masks"
            if not idir.is_dir():
                continue
            masks = {p.stem: p for p in mdir.iterdir() if p.suffix.lower() in IMG_EXT}
            for p in sorted(idir.iterdir()):
                if p.suffix.lower() not in IMG_EXT or p.stem in pairs:
                    continue
                if exif_size(p) != FOURK:
                    continue
                m = masks.get(p.stem)
                if m is None:
                    raise SystemExit(f"마스크가 없습니다: {p}")
                pairs[p.stem] = (p, m)
    return pairs


def process_one(job: tuple) -> dict:
    stem, img_src, mask_src = job
    img_src, mask_src = Path(img_src), Path(mask_src)
    img_dst = POOL / "images" / f"{stem}.png"
    mask_dst = POOL / "masks" / f"{stem}.png"

    with Image.open(mask_src) as mk_probe:
        msize = mk_probe.size
    with Image.open(img_src) as im_probe:
        w0, h0 = ImageOps.exif_transpose(im_probe).size
    if msize != (w0, h0):
        return {"stem": stem, "error": f"이미지 {w0}x{h0} vs 마스크 {msize} 불일치"}

    nw, nh = target_size(w0, h0)

    with Image.open(img_src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.resize((nw, nh), Image.LANCZOS).save(img_dst, "PNG", optimize=False)

    with Image.open(mask_src) as mk:
        before = set(np.unique(np.array(mk)).tolist())
        mk_out = mk.resize((nw, nh), Image.NEAREST)      # 마스크는 반드시 NEAREST
        after = set(np.unique(np.array(mk_out)).tolist())
        mk_out.save(mask_dst, "PNG", optimize=False)

    return {
        "stem": stem,
        "src": str(img_src),
        "src_size": [w0, h0],
        "out_size": [nw, nh],
        "scale": round((nw * nh / (w0 * h0)) ** 0.5, 4),
        "aspect_distortion": round((nw / nh) / (w0 / h0), 6),
        "out_pixels": nw * nh,
        "mask_values_kept": after <= before,
    }


def build_full_splits() -> dict:
    """dataset_6fold 의 원래 분할 소속을 그대로 심볼릭 링크로 재현 (1,195장 전량)."""
    pool_img, pool_msk = POOL / "images", POOL / "masks"
    have = {p.stem for p in pool_img.iterdir()}
    counts: dict[str, dict] = {}
    missing: list[str] = []

    for cv in FOLDS:
        for part in PARTS:
            sdir = SRC_ROOT / cv / part / "images"
            if not sdir.is_dir():
                continue
            di, dm = NEW_SPLIT / cv / part / "images", NEW_SPLIT / cv / part / "masks"
            di.mkdir(parents=True, exist_ok=True)
            dm.mkdir(parents=True, exist_ok=True)
            n = 0
            for p in sorted(sdir.iterdir()):
                if p.suffix.lower() not in IMG_EXT:
                    continue
                if p.stem not in have:
                    missing.append(f"{cv}/{part}/{p.stem}")
                    continue
                for dst_dir, pool_dir in ((di, pool_img), (dm, pool_msk)):
                    link = dst_dir / f"{p.stem}.png"
                    if link.is_symlink() or link.exists():
                        link.unlink()
                    link.symlink_to(os.path.relpath(pool_dir / f"{p.stem}.png", dst_dir))
                n += 1
            counts.setdefault(cv, {})[part] = n
    return {"counts": counts, "missing": missing}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--skip-splits", action="store_true")
    args = ap.parse_args()

    pairs = find_4k_pairs()
    print(f"찾은 4K(2160x3840) 쌍: {len(pairs)}장")
    if not pairs:
        raise SystemExit("4K 사진을 찾지 못했습니다.")

    nw, nh = target_size(*FOURK)
    print(f"변환 규격: {FOURK[0]}x{FOURK[1]} → {nw}x{nh}  "
          f"({nw*nh:,} 화소, 목표 대비 {nw*nh/TARGET_PIXELS*100:.2f}%, "
          f"비율 {(nw/nh)/(FOURK[0]/FOURK[1]):.4f})")

    # 안전장치: 기존 1,067장을 덮어쓰지 않는다
    clash = [s for s in pairs if (POOL / "images" / f"{s}.png").exists()]
    if clash:
        raise SystemExit(f"⛔ 이미 풀에 있는 이름 {len(clash)}개: {clash[:3]} … 중단합니다.")
    print(f"이름 충돌 없음 (기존 풀 {len(list((POOL/'images').iterdir()))}장은 그대로 둡니다)")

    if args.dry_run:
        print("\n[dry-run] 파일을 쓰지 않았습니다.")
        return

    jobs = [(s, str(i), str(m)) for s, (i, m) in sorted(pairs.items())]
    recs = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k, r in enumerate(ex.map(process_one, jobs, chunksize=4), 1):
            recs.append(r)
            if k % 32 == 0 or k == len(jobs):
                print(f"  {k}/{len(jobs)}")

    errs = [r for r in recs if r.get("error")]
    if errs:
        print(f"\n⛔ 실패 {len(errs)}건:")
        for r in errs[:5]:
            print("   ", r["stem"], r["error"])
        raise SystemExit(1)

    sizes = {tuple(r["out_size"]) for r in recs}
    bad_ratio = [r for r in recs if abs(r["aspect_distortion"] - 1.0) > 1e-9]
    bad_mask = [r for r in recs if not r["mask_values_kept"]]
    print(f"\n✅ 변환 {len(recs)}장 | 출력 크기 {sizes} | 비율왜곡 {len(bad_ratio)}건 | "
          f"마스크 값 오염 {len(bad_mask)}건")

    out = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "added": len(recs), "records": {r["stem"]: r for r in recs}}
    if not args.skip_splits:
        out["splits"] = build_full_splits()
        print("\n■ splits/blueberry_full1195/ (1,195장 전량 분할)")
        for cv, c in out["splits"]["counts"].items():
            print(f"   {cv}: train {c['train']} / val {c['val']} / test {c['test']} "
                  f"= {sum(c.values())}")
        if out["splits"]["missing"]:
            print(f"   ⚠️ 풀에 없어 건너뜀 {len(out['splits']['missing'])}건")

    log = BASE / "semantic-segmentation/output/blueberry_4k_added_260808.json"
    log.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n기록: {log}")
    print(f"풀 총 장수: {len(list((POOL/'images').iterdir()))}장")


if __name__ == "__main__":
    main()
