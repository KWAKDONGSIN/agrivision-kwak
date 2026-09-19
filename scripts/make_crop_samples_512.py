#!/usr/bin/env python
"""
0806 교수님미팅 지시 ② — 화소 수를 통일한 뒤 512x512 랜덤 크롭을 데이터셋마다
20~30장씩 이미지로 뽑아 **눈으로** 비율이 비슷한지 확인한다.

녹취록 근거 (문서/0806 교수님미팅.txt 12:33~13:37)
  "일단은 리사이즈를 아까 전에 해상도를 픽셀 개수를 맞추는 개수만큼으로 이제 리사이즈를 다 하고,
   그다음에 512 512로 랜덤 크롭한 이제 20개 정도 24개 각각 데이터셋마다 (뽑아 놓아 보세요).
   ... 좀 비슷하게 눈으로 봤을 때 '어 이거 비슷비슷하네' 이렇게, 아니면은 어떤 게 너무
   두드러지게 좀 이상해 보인다 그러면 좀 조정을 또 해야죠.
   그리고 AI도 그래야지 비슷비슷해 보일 거 아니에요."

크롭 방식은 학습 코드(semseg/augmentations.py 의 RandomCrop)와 **동일**하게 맞췄다.
  - 512보다 작은 변은 오른쪽/아래에 0 패딩
  - 그 뒤 좌상단 좌표를 균등 무작위로 뽑아 512x512 잘라냄

출력
  reports/crop_samples_512/<fruit>/crop_XX.png        크롭 원본 24장
  reports/crop_samples_512/<fruit>/_contact_sheet.png 24장 모아 보기 (전경% 표기)
  reports/crop_samples_512/00_4개데이터셋_비교.png      4과일 나란히 비교 1장
  reports/crop_samples_512/crop_stats.json            전경 비율 통계
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL_ROOT = ROOT / "datasets_resized_2mp"
OUT_ROOT = ROOT / "semantic-segmentation/reports/crop_samples_512"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과(MinneApple)",
       "peach": "복숭아", "grape": "포도(CERTH)"}

CROP = 512
N_SAMPLES = 24

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def get_font(size: int):
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def random_crop(img: np.ndarray, mask: np.ndarray, rng: random.Random):
    """학습 RandomCrop 과 같은 규칙: 모자라면 0 패딩 후 균등 무작위 위치."""
    H, W = img.shape[:2]
    pad_h, pad_w = max(0, CROP - H), max(0, CROP - W)
    if pad_h or pad_w:
        img = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)))
        mask = np.pad(mask, ((0, pad_h), (0, pad_w)))
        H, W = img.shape[:2]
    top = rng.randint(0, H - CROP) if H > CROP else 0
    left = rng.randint(0, W - CROP) if W > CROP else 0
    return (img[top:top + CROP, left:left + CROP],
            mask[top:top + CROP, left:left + CROP], top, left)


def load_mask(p: Path) -> np.ndarray:
    """어떤 마스크 형식이든 (H,W) 이진 배열로. 사과는 인스턴스ID라 >0 처리."""
    a = np.array(Image.open(p))
    if a.ndim == 3:
        a = a[..., 0]
    return (a > 0).astype(np.uint8)


def overlay(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """정답 영역을 빨갛게 반투명으로 덮어 눈으로 크기를 가늠하게 한다."""
    out = img.astype(np.float32).copy()
    m = mask.astype(bool)
    out[m] = out[m] * 0.45 + np.array([255, 40, 40], np.float32) * 0.55
    return out.astype(np.uint8)


def contact_sheet(tiles: list[tuple[np.ndarray, str]], title: str,
                  cols: int = 6, thumb: int = 256) -> Image.Image:
    rows = (len(tiles) + cols - 1) // cols
    pad, head, cap = 8, 56, 22
    W = cols * (thumb + pad) + pad
    H = head + rows * (thumb + cap + pad) + pad
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), title, fill=(0, 0, 0), font=get_font(26))
    for i, (arr, label) in enumerate(tiles):
        r, c = divmod(i, cols)
        x = pad + c * (thumb + pad)
        y = head + r * (thumb + cap + pad)
        sheet.paste(Image.fromarray(arr).resize((thumb, thumb), Image.LANCZOS), (x, y))
        d.text((x + 2, y + thumb + 3), label, fill=(30, 30, 30), font=get_font(16))
    return sheet


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruits", nargs="+", default=FRUITS)
    ap.add_argument("--pool", default=str(POOL_ROOT))
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--n", type=int, default=N_SAMPLES)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    pool_root, out_root = Path(args.pool), Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    stats, best_rows = {}, []

    for fruit in args.fruits:
        idir, mdir = pool_root / fruit / "images", pool_root / fruit / "masks"
        if not idir.is_dir():
            print(f"[{fruit}] 리사이즈 결과가 아직 없습니다: {idir}")
            continue
        files = sorted(idir.iterdir())
        rng = random.Random(args.seed)
        picks = rng.sample(files, min(args.n, len(files)))

        fdir = out_root / fruit
        fdir.mkdir(parents=True, exist_ok=True)
        tiles, ratios = [], []
        for i, p in enumerate(picks):
            img = np.array(Image.open(p).convert("RGB"))
            mask = load_mask(mdir / f"{p.stem}.png")
            ci, cm, top, left = random_crop(img, mask, rng)
            fg = float(cm.mean())
            ratios.append(fg)
            Image.fromarray(ci).save(fdir / f"crop_{i:02d}.png")
            Image.fromarray(overlay(ci, cm)).save(fdir / f"crop_{i:02d}_overlay.png")
            tiles.append((overlay(ci, cm), f"{i:02d}  전경 {fg*100:.1f}%"))

        arr = np.array(ratios)
        stats[fruit] = {
            "n_samples": len(ratios),
            "fg_ratio_mean_pct": round(float(arr.mean()) * 100, 2),
            "fg_ratio_median_pct": round(float(np.median(arr)) * 100, 2),
            "fg_ratio_min_pct": round(float(arr.min()) * 100, 2),
            "fg_ratio_max_pct": round(float(arr.max()) * 100, 2),
            "pool_images": len(files),
        }
        title = (f"{KOR[fruit]} — 512x512 랜덤 크롭 {len(ratios)}장 "
                 f"(전경 평균 {arr.mean()*100:.1f}%)  ※ 빨간 부분이 정답 과일")
        contact_sheet(tiles, title).save(fdir / "_contact_sheet.png")
        print(f"[{fruit}] {len(ratios)}장 · 전경 평균 {arr.mean()*100:.2f}% → {fdir}")
        best_rows.append((fruit, tiles[:6], arr.mean()))

    # ---- 4과일 비교 1장 ----
    if len(best_rows) >= 2:
        thumb, pad, head, cap, labw = 230, 10, 60, 20, 250
        cols = max(len(r[1]) for r in best_rows)
        W = labw + cols * (thumb + pad) + pad
        H = head + len(best_rows) * (thumb + cap + pad) + pad
        sheet = Image.new("RGB", (W, H), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        d.text((pad, 16), "4개 데이터셋 512x512 크롭 비교 — 화소 수를 2,073,600으로 통일한 뒤",
               fill=(0, 0, 0), font=get_font(26))
        for r, (fruit, tls, mean) in enumerate(best_rows):
            y = head + r * (thumb + cap + pad)
            d.text((pad, y + thumb // 2 - 20), f"{KOR[fruit]}", fill=(0, 0, 0), font=get_font(22))
            d.text((pad, y + thumb // 2 + 8), f"전경 평균 {mean*100:.1f}%",
                   fill=(90, 90, 90), font=get_font(18))
            for c, (arr_img, label) in enumerate(tls):
                x = labw + c * (thumb + pad)
                sheet.paste(Image.fromarray(arr_img).resize((thumb, thumb), Image.LANCZOS), (x, y))
                d.text((x + 2, y + thumb + 2), label.split("  ")[1],
                       fill=(30, 30, 30), font=get_font(15))
        sheet.save(out_root / "00_4개데이터셋_비교.png")
        print(f"\n비교 그림: {out_root/'00_4개데이터셋_비교.png'}")

    with open(out_root / "crop_stats.json", "w") as f:
        json.dump({"crop": CROP, "seed": args.seed, "stats": stats}, f,
                  indent=2, ensure_ascii=False)
    print(f"통계: {out_root/'crop_stats.json'}")
    for k, v in stats.items():
        print(f"  {KOR[k]:<16} 전경 평균 {v['fg_ratio_mean_pct']:>5.2f}% "
              f"(중앙 {v['fg_ratio_median_pct']:.2f}% / {v['fg_ratio_min_pct']:.2f}~"
              f"{v['fg_ratio_max_pct']:.2f}%)")


if __name__ == "__main__":
    main()
