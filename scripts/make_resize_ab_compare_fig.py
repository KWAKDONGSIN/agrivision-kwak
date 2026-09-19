#!/usr/bin/env python
"""
리사이즈 방식 A안 / B안 비교 그림 — 교수님께 보여드리고 확정받기 위한 것.

  A안 (datasets_resized_2mp)  : 비율 유지 + 총 화소 수만 1440x1440(=2,073,600)에 통일
                                → 해상도가 데이터셋마다 다름 (1440x1440, 1080x1920, ...)
  B안 (datasets_resized_1440) : 전부 똑같은 1440x1440 로 통일
                                → 규격은 하나, 대신 세로로 긴 사진이 가로로 늘어남

0806 녹취록에서 교수님은 B안을 먼저 말씀하셨다가("다 거의 1440으로 하면 좋지 않을까요")
곧바로 "어떤 거는 길고 작은 게 있잖아요, 이게 그러면 이렇게 늘어지는 건데" 라고 하시며
A안("비율은 유지하고 화소 개수가 거의 동일하도록")으로 정하셨다. 이 그림은 그 '늘어짐'이
실제로 얼마나 되는지 눈으로 확인하기 위한 것.

출력: reports/resize_compare/00_A안_B안_비교.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
A_ROOT = ROOT / "datasets_resized_2mp"
B_ROOT = ROOT / "datasets_resized_1440"
OUT = ROOT / "semantic-segmentation/reports/resize_compare"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과", "peach": "복숭아", "grape": "포도"}

FONTS = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def font(sz: int):
    for f in FONTS:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def fit_box(im: Image.Image, bw: int, bh: int) -> Image.Image:
    """비율을 유지한 채 bw x bh 상자 안에 넣고 남는 곳은 흰색.
    (그림을 보여줄 때 이 함수는 왜곡을 만들지 않는다 — 왜곡은 원본 파일에 이미 있다)"""
    s = min(bw / im.width, bh / im.height)
    small = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    canvas = Image.new("RGB", (bw, bh), (245, 245, 245))
    canvas.paste(small, ((bw - small.width) // 2, (bh - small.height) // 2))
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    BW, BH = 360, 360          # 각 칸 크기
    padx, pady = 20, 16
    head, cap, labw = 118, 46, 170

    rows = []
    for fr in FRUITS:
        a_dir, b_dir = A_ROOT / fr / "images", B_ROOT / fr / "images"
        if not a_dir.is_dir() or not b_dir.is_dir():
            print(f"[{fr}] 건너뜀 (A안 또는 B안 결과 없음)")
            continue
        # 그 데이터셋에서 **가장 흔한 해상도**의 사진을 고른다.
        # (예외적인 1장을 뽑으면 대표성이 없다 — 블루베리 1920x1080 은 1,067장 중 1장뿐)
        from collections import Counter
        names = sorted(p.name for p in a_dir.iterdir() if (b_dir / p.name).exists())
        if not names:
            continue
        sz = Counter()
        for n in names:
            with Image.open(a_dir / n) as im:
                sz[im.size] += 1
        common = sz.most_common(1)[0][0]
        pick = next(n for n in names
                    if Image.open(a_dir / n).size == common)
        a_im, b_im = Image.open(a_dir / pick).convert("RGB"), Image.open(b_dir / pick).convert("RGB")
        rows.append((fr, pick, a_im, b_im))

    if not rows:
        raise SystemExit("비교할 것이 없습니다.")

    W = labw + 2 * (BW + padx) + padx
    H = head + len(rows) * (BH + cap + pady) + pady
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((padx, 12), "리사이즈 방식 비교 — 어느 쪽으로 갈지 확정 필요",
           fill=(0, 0, 0), font=font(30))
    d.text((labw, 56), "A안  비율 유지 + 화소 수만 통일", fill=(0, 110, 0), font=font(21))
    d.text((labw, 82), "(0806 녹취 12:27 교수님 결정)", fill=(0, 110, 0), font=font(16))
    d.text((labw + BW + padx, 56), "B안  전부 1440x1440", fill=(190, 0, 0), font=font(21))
    d.text((labw + BW + padx, 82), "(규격은 하나, 대신 늘어남)", fill=(190, 0, 0), font=font(16))

    for r, (fr, name, a_im, b_im) in enumerate(rows):
        y = head + r * (BH + cap + pady)
        d.text((padx, y + BH // 2 - 26), KOR[fr], fill=(0, 0, 0), font=font(24))
        d.text((padx, y + BH // 2 + 4), f"{a_im.width}x{a_im.height}",
               fill=(0, 110, 0), font=font(17))
        d.text((padx, y + BH // 2 + 26), f"→ 1440x1440", fill=(190, 0, 0), font=font(17))

        for c, (im, color) in enumerate([(a_im, (0, 110, 0)), (b_im, (190, 0, 0))]):
            x = labw + c * (BW + padx)
            sheet.paste(fit_box(im, BW, BH), (x, y))
            d.rectangle([x, y, x + BW - 1, y + BH - 1], outline=color, width=3)
            dist = (b_im.width / b_im.height) / (a_im.width / a_im.height) if c == 1 else 1.0
            note = (f"{im.width}x{im.height}" if c == 0
                    else f"{im.width}x{im.height}   가로로 {dist:.2f}배 늘어남"
                         if abs(dist - 1) > 0.01 else f"{im.width}x{im.height}   왜곡 없음")
            d.text((x + 2, y + BH + 5), note, fill=color, font=font(17))
        d.text((labw, y + BH + 26), f"파일: {name}", fill=(120, 120, 120), font=font(14))

    p = out / "00_A안_B안_비교.png"
    sheet.save(p)
    print(f"저장: {p}")


if __name__ == "__main__":
    main()
