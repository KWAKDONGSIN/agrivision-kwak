#!/usr/bin/env python
"""
0806 교수님미팅 지시 — 4개 데이터셋(블루베리·사과·복숭아·포도)의 **총 화소 수**를 통일한다.

녹취록 근거 (문서/0806 교수님미팅.txt)
  09:47~10:09  교수님 "블루베리가 1440이라고요? 다 거의 1440으로 하면 좋지 않을까요?
                       ... 지금 비율은 유지하고 그냥 화소 개수가 거의 동일하도록"
  12:27        교수님 "픽셀 개수를 거의 유사하게끔 하죠. 그냥"
  13:55        교수님 "원래 원본 데이터는 아무튼 다른 데 저장해 놓고,
                       리사이즈 한 걸 그거 위주로 데이터셋으로 쓰면"
  03:24        교수님 "블루베리 4K라는 거는 그거는 빼는 게 맞네요"  ← 과실 클로즈업이라 취지에 안 맞음

따라서 이 스크립트는
  1) **원본을 절대 건드리지 않고** 새 폴더에 리사이즈 사본을 만든다
  2) 가로세로 **비율을 유지**한 채 총 화소 수를 1440x1440(=2,073,600)에 맞춘다
  3) 블루베리의 2160x3840(4K, Camera 4) 128장은 **제외**한다
  4) 기존 분할(폴드) 구조를 심볼릭 링크로 그대로 재현한다 (디스크 추가 0)

변의 길이는 8의 배수로 반올림한다. 이 데이터셋들은 8의 배수로 맞추면
아래처럼 **참 비율이 오차 없이 그대로 나온다** (32의 배수로 하면 최대 1.5% 찌그러짐):
    2160x3840 -> 1080x1920 (9:16 그대로)      720x1280 -> 1080x1920 (9:16 그대로)
    1600x1200 -> 1664x1248 (4:3 그대로)       4032x3024 -> 1664x1248 (4:3 그대로)
    1440x1440 -> 1440x1440 (변화 없음)        1920x1080 -> 1920x1080 (변화 없음)

사용법
    python tools/resize_datasets_to_common_pixels.py                 # 전부
    python tools/resize_datasets_to_common_pixels.py --fruits peach  # 하나만
    python tools/resize_datasets_to_common_pixels.py --dry-run       # 계획만 출력
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
OUT_ROOT = ROOT / "datasets_resized_2mp"

TARGET_PIXELS = 1440 * 1440  # 2,073,600 — 교수님이 제시한 기준
MULTIPLE = 8
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# ---------------------------------------------------------------------------
# 원본 위치. 전부 **읽기만** 한다.
#   dirs   : {images,masks} 를 품은 폴더들. 여러 개면 합쳐서 중복 stem 제거
#   splits : 리사이즈 후 심볼릭 링크로 재현할 분할 구조 (표시이름 -> 폴더)
#   drop_sizes : (w,h) 가 이 목록에 있으면 제외 (EXIF 반영 후 크기 기준)
# ---------------------------------------------------------------------------
SOURCES: dict[str, dict] = {
    "blueberry": {
        "dirs": [ROOT / "dataset_6fold/cv1" / s for s in ("train", "val", "test")],
        "splits": {f"cv{k}": ROOT / f"dataset_6fold/cv{k}" for k in range(1, 7)},
        "drop_sizes": [(2160, 3840)],  # 4K = Camera 4 클로즈업. 교수님 지시로 제외
        "drop_reason": "4K(2160x3840) Camera 4 — 나무가 아니라 과실만 클로즈업한 사진",
        "mask_note": "RGB 3채널, 값 0/255 (이진)",
    },
    "apple": {
        # 최상위 dataset_minneapple/ 은 링크가 전부 끊겨 있음(0730 사고). 실파일 쪽을 쓴다.
        "dirs": [ROOT / "연구실 블루베리/dataset_minneapple" / s for s in ("train", "val", "test")],
        # single = 원 논문의 연도 분할(2015 train / 2016 test).
        # cv1~cv5 = 팀 규칙(7:1:2 5폴드, seed3407)으로 이미 고정해 둔 분할.
        "splits": {"single": ROOT / "연구실 블루베리/dataset_minneapple",
                   **{f"cv{k}": ROOT / f"연구실 블루베리/dataset_minneapple_5fold_712_seed3407/cv{k}"
                      for k in range(1, 6)}},
        "drop_sizes": [],
        "drop_reason": None,
        "mask_note": "1채널, 값 0=배경 / 1..N=사과 개체 번호(인스턴스 ID). 학습 시 >0 이진화됨",
    },
    "peach": {
        "dirs": [ROOT / "연구실 블루베리/datasets_verified/peach_semseg" / s
                 for s in ("train", "val", "test")],
        "splits": {"single": ROOT / "연구실 블루베리/datasets_verified/peach_semseg"},
        "drop_sizes": [],
        "drop_reason": None,
        "mask_note": "1채널, 값 0/255 (이진)",
    },
    "grape": {
        # tools/prepare_certh_grape.py --resize 1920 로 CERTH 원본(2160x3840)에서 새로 뽑은 것.
        # 기존 576x1024 짜리를 다시 키우면 없는 해상도를 지어내게 되므로 원본에서 다시 만든다.
        # 2026-08-07: 토이 100장 → **전체 2,502장**(mimc train2000+valid251+test251)으로 교체.
        "dirs": [ROOT / "incoming/certh_grape_full_1920"],
        # 폴드는 tools/make_folds.py 가 직접 만든다(복숭아와 동일). 여기서 미러링하지 않는다.
        "splits": {},
        "drop_sizes": [],
        "drop_reason": None,
        "mask_note": "1채널, 값 0/255 (이진). 성숙도 3클래스를 하나로 합친 것",
    },
}


# ---------------------------------------------------------------------------
def exif_size(path: Path) -> tuple[int, int]:
    """EXIF 회전을 반영한 실제 표시 크기."""
    with Image.open(path) as im:
        w, h = im.size
        try:
            orientation = im.getexif().get(0x0112, 1)
        except Exception:
            orientation = 1
    return (h, w) if orientation in (5, 6, 7, 8) else (w, h)


def target_size(w: int, h: int, target_px: int = TARGET_PIXELS,
                multiple: int = MULTIPLE) -> tuple[int, int]:
    """비율을 유지한 채 총 화소 수가 target_px 에 가장 가까워지는 크기."""
    scale = (target_px / (w * h)) ** 0.5
    nw = max(multiple, int(round(w * scale / multiple)) * multiple)
    nh = max(multiple, int(round(h * scale / multiple)) * multiple)
    return nw, nh


def collect(fruit: str) -> tuple[dict[str, tuple[Path, Path]], list[dict]]:
    """stem -> (이미지경로, 마스크경로). 중복 stem 은 처음 것만."""
    spec = SOURCES[fruit]
    pairs: dict[str, tuple[Path, Path]] = {}
    dropped: list[dict] = []
    drop = {tuple(s) for s in spec["drop_sizes"]}

    for d in spec["dirs"]:
        idir, mdir = d / "images", d / "masks"
        if not idir.is_dir():
            raise SystemExit(f"[{fruit}] 원본 폴더가 없습니다: {idir}")
        masks = {p.stem: p for p in mdir.iterdir() if p.suffix.lower() in IMG_EXT}
        for p in sorted(idir.iterdir()):
            if p.suffix.lower() not in IMG_EXT or p.stem in pairs:
                continue
            m = masks.get(p.stem)
            if m is None:
                raise SystemExit(f"[{fruit}] 마스크가 없습니다: {p}")
            w, h = exif_size(p)
            if (w, h) in drop:
                dropped.append({"file": p.name, "size": [w, h]})
                continue
            pairs[p.stem] = (p, m)
    return pairs, dropped


def center_box(w: int, h: int, tw: int, th: int) -> tuple[int, int, int, int]:
    """원본에서 목표 비율과 같은 최대 크기의 중앙 사각형 (crop 모드용)."""
    if w * th > tw * h:            # 원본이 더 가로로 넓다 → 좌우를 자른다
        cw, ch = int(round(h * tw / th)), h
    else:                          # 원본이 더 세로로 길다 → 위아래를 자른다
        cw, ch = w, int(round(w * th / tw))
    return ((w - cw) // 2, (h - ch) // 2, (w - cw) // 2 + cw, (h - ch) // 2 + ch)


def process_one(job: tuple) -> dict:
    """이미지 1장 + 마스크 1장을 리사이즈해 PNG 로 저장. 워커 프로세스에서 실행.

    fixed 가 None 이면  → 비율 유지 + 총 화소 수 통일 (교수님 최종 결정, 기본값)
    fixed 가 (W,H) 이면 → 전부 똑같은 W x H 로 통일. fit 으로 비율 처리 방식을 고른다
        stretch : 그냥 늘려 맞춘다 (비율 왜곡. 교수님이 "늘어진다"고 우려하신 그 방식)
        crop    : 중앙을 목표 비율로 잘라낸 뒤 리사이즈 (왜곡 0, 가장자리 손실)
        pad     : 비율 유지해 축소한 뒤 남는 여백을 0으로 채움 (왜곡 0, 검은 여백)
    """
    stem, img_src, mask_src, img_dst, mask_dst, force, fixed, fit = job
    img_src, mask_src = Path(img_src), Path(mask_src)
    img_dst, mask_dst = Path(img_dst), Path(mask_dst)

    if img_dst.exists() and mask_dst.exists() and not force:
        with Image.open(img_dst) as im:
            nw, nh = im.size
        return {"stem": stem, "skipped": True, "out_size": [nw, nh]}

    with Image.open(mask_src) as mk_probe:
        msize = mk_probe.size
    with Image.open(img_src) as im_probe:
        w0, h0 = ImageOps.exif_transpose(im_probe).size
    if msize != (w0, h0):
        return {"stem": stem, "error": f"이미지 {w0}x{h0} vs 마스크 {msize} 크기 불일치"}

    def transform(im: Image.Image, resample) -> tuple[Image.Image, int, int]:
        w, h = im.size
        if fixed is None:
            nw, nh = target_size(w, h)
            return (im if (nw, nh) == (w, h) else im.resize((nw, nh), resample)), nw, nh
        tw, th = fixed
        if fit == "crop":
            im = im.crop(center_box(w, h, tw, th))
        elif fit == "pad":
            s = min(tw / w, th / h)
            sw, sh = max(1, int(round(w * s))), max(1, int(round(h * s)))
            small = im.resize((sw, sh), resample)
            canvas = Image.new(im.mode, (tw, th), 0)
            canvas.paste(small, ((tw - sw) // 2, (th - sh) // 2))
            return canvas, tw, th
        return (im if im.size == (tw, th) else im.resize((tw, th), resample)), tw, th

    with Image.open(img_src) as im:
        im = ImageOps.exif_transpose(im)          # EXIF 회전 반영 (복숭아 jpg 대비)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        w, h = im.size
        # 축소·확대 모두 LANCZOS 가 가장 안전하다 (에일리어싱 억제)
        im_out, nw, nh = transform(im, Image.LANCZOS)
        img_dst.parent.mkdir(parents=True, exist_ok=True)
        im_out.save(img_dst, "PNG", optimize=False)

    with Image.open(mask_src) as mk:
        # 마스크는 반드시 NEAREST. 보간하면 없는 라벨값이 생긴다.
        mk_out, _, _ = transform(mk, Image.NEAREST)
        arr_before = np.unique(np.array(mk))
        arr_after = np.unique(np.array(mk_out))
        mask_dst.parent.mkdir(parents=True, exist_ok=True)
        mk_out.save(mask_dst, "PNG", optimize=False)

    # 가로세로비가 얼마나 찌그러졌는지 (1.0 이면 왜곡 없음)
    distort = round(((nw / nh) / (w / h)), 4)
    return {
        "stem": stem,
        "src": str(img_src),
        "src_size": [w, h],
        "out_size": [nw, nh],
        "src_megapixels": round(w * h / 1e6, 3),
        "out_megapixels": round(nw * nh / 1e6, 3),
        "scale": round((nw * nh / (w * h)) ** 0.5, 4),
        "aspect_distortion": distort,
        "mask_values_kept": bool(set(arr_after.tolist()) <= set(arr_before.tolist())),
        "skipped": False,
    }


def link_splits(fruit: str, pool: Path, records: dict) -> dict:
    """원본 분할 구조를 심볼릭 링크로 재현한다. 실파일 복사 없음."""
    spec = SOURCES[fruit]
    out = {}
    for split_name, split_root in spec["splits"].items():
        if not split_root.is_dir():
            out[split_name] = {"error": f"원본 분할 폴더 없음: {split_root}"}
            continue
        counts = {}
        for part in ("train", "val", "test"):
            src_imgs = split_root / part / "images"
            if not src_imgs.is_dir():
                continue
            n_ok = n_gone = 0
            for p in sorted(src_imgs.iterdir()):
                if p.suffix.lower() not in IMG_EXT:
                    continue
                if p.stem not in records:      # 제외된 4K 등
                    n_gone += 1
                    continue
                for kind in ("images", "masks"):
                    dst_dir = OUT_ROOT / "splits" / fruit / split_name / part / kind
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    dst = dst_dir / f"{p.stem}.png"
                    tgt = pool / kind / f"{p.stem}.png"
                    if dst.is_symlink() or dst.exists():
                        dst.unlink()
                    os.symlink(os.path.relpath(tgt, dst_dir), dst)
                n_ok += 1
            counts[part] = {"kept": n_ok, "dropped": n_gone}
        out[split_name] = counts
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruits", nargs="+", default=list(SOURCES),
                    choices=list(SOURCES))
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--force", action="store_true", help="이미 있는 결과도 다시 만든다")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fixed", default=None, metavar="WxH",
                    help="전부 똑같은 크기로 통일한다. 예: --fixed 1440x1440. "
                         "지정 안 하면 비율 유지 + 화소 수 통일(기본, 교수님 최종 결정)")
    ap.add_argument("--fit", default="stretch", choices=["stretch", "crop", "pad"],
                    help="--fixed 일 때 비율 처리 방식 (기본 stretch=늘려 맞춤)")
    args = ap.parse_args()

    fixed = None
    if args.fixed:
        fw, fh = (int(v) for v in args.fixed.lower().split("x"))
        fixed = (fw, fh)

    out_root = Path(args.out)
    summary = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": (f"fixed {fixed[0]}x{fixed[1]} ({args.fit})" if fixed
                 else "aspect-preserving, equal pixel count"),
        "target_pixels": (fixed[0] * fixed[1]) if fixed else TARGET_PIXELS,
        "multiple_of": MULTIPLE,
        "note": ("모든 사진을 똑같은 한 규격으로 통일한 판" if fixed else
                 "0806 교수님미팅 지시. 비율 유지 + 총 화소 수 1440x1440 기준으로 통일"),
        "fruits": {},
    }

    for fruit in args.fruits:
        spec = SOURCES[fruit]
        pairs, dropped = collect(fruit)
        pool = out_root / fruit
        print(f"\n■ {fruit}: 원본 {len(pairs) + len(dropped)}장 → 사용 {len(pairs)}장 "
              f"(제외 {len(dropped)}장)")
        if dropped:
            print(f"   제외 사유: {spec['drop_reason']}")

        if args.dry_run:
            from collections import Counter
            plan = Counter()
            for stem, (ip, _) in pairs.items():
                w, h = exif_size(ip)
                plan[((w, h), fixed if fixed else target_size(w, h))] += 1
            for (src, dst), n in plan.most_common():
                d = (dst[0] / dst[1]) / (src[0] / src[1])
                print(f"   {src[0]}x{src[1]} → {dst[0]}x{dst[1]}  ({n}장, "
                      f"{dst[0] * dst[1] / 1e6:.3f}MP, 비율왜곡 {d:.3f}배)")
            continue

        jobs = [(stem, str(ip), str(mp),
                 str(pool / "images" / f"{stem}.png"),
                 str(pool / "masks" / f"{stem}.png"),
                 args.force, fixed, args.fit)
                for stem, (ip, mp) in sorted(pairs.items())]

        records, errors = {}, []
        done = 0
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(process_one, j) for j in jobs]
            for f in as_completed(futs):
                r = f.result()
                done += 1
                if "error" in r:
                    errors.append(r)
                else:
                    records[r["stem"]] = r
                if done % 200 == 0 or done == len(jobs):
                    print(f"   {done}/{len(jobs)}", flush=True)

        if errors:
            print(f"   [!] 실패 {len(errors)}건")
            for e in errors[:5]:
                print("      ", e)

        links = link_splits(fruit, pool, records)
        from collections import Counter
        size_hist = Counter(tuple(r["out_size"]) for r in records.values() if "out_size" in r)
        dist_hist = Counter(r.get("aspect_distortion") for r in records.values()
                            if r.get("aspect_distortion") is not None)

        summary["fruits"][fruit] = {
            "source_dirs": [str(d) for d in spec["dirs"]],
            "mask_note": spec["mask_note"],
            "images_total_source": len(pairs) + len(dropped),
            "images_used": len(records),
            "images_dropped": len(dropped),
            "dropped_reason": spec["drop_reason"],
            "dropped_files": dropped,
            "errors": errors,
            "output_sizes": {f"{w}x{h}": n for (w, h), n in size_hist.most_common()},
            "aspect_distortion": {str(k): n for k, n in dist_hist.most_common()},
            "splits": links,
            "pool": str(pool),
            "records": records,
        }
        print(f"   출력 크기: {dict(summary['fruits'][fruit]['output_sizes'])}")
        print(f"   분할 링크: {json.dumps(links, ensure_ascii=False)}")

    if args.dry_run:
        return

    out_root.mkdir(parents=True, exist_ok=True)
    with open(out_root / "manifest.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n저장: {out_root/'manifest.json'}")


if __name__ == "__main__":
    sys.exit(main())
