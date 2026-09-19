#!/usr/bin/env python
"""
팀 공유용 «한 장짜리» 설명 그림.

위: 지금 학습이 실제로 보는 512 크롭 (과일마다 열매 크기가 제각각)
아래: 새로 만든 512 타일 (열매가 전부 비슷한 크기로 보임)

출력: semantic-segmentation/reports/tiled_512/00_타일링_한장설명.png
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None

SRC = Path("/data/project/2026summer/kds0206/datasets_resized_2mp")
TILED = Path("/data/project/2026summer/kds0206/datasets_tiled_512")
OUT = Path(__file__).resolve().parents[1] / "reports" / "tiled_512"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과", "peach": "복숭아", "grape": "포도"}

FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

CELL = 340
GAP = 22
LEFT = 150
PAD = 34


def f(sz: int, bold: bool = False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def _diam(mask_path: Path) -> float | None:
    """마스크 한 장의 개체 지름(등가원) 중앙값."""
    import math

    import numpy as np
    from scipy import ndimage
    a = np.array(Image.open(mask_path).convert("L"))
    b = a > 0
    if not b.any():
        return None
    lab, n = ndimage.label(b)
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())[1:]
    sizes = sizes[sizes >= 30]
    if sizes.size == 0:
        return None
    return float(np.median(2.0 * np.sqrt(sizes / math.pi)))


def pick(fruit: str, target_diam: float):
    """«그 과일을 대표하는» 사진을 고릅니다.

    전경이 가장 많은 타일을 고르면 유난히 가까이 찍힌 장이 뽑혀서 그림이 실제보다
    과장됩니다. 그래서 개체 지름이 **과일 중앙값에 가장 가까운** 사진을 고르고,
    그 사진 안에서 열매가 잘 보이는 타일을 씁니다.
    """
    import random

    rows_by_stem: dict[str, list[tuple]] = {}
    with open(TILED / fruit / "index.csv") as fh:
        for r in csv.DictReader(fh):
            rows_by_stem.setdefault(r["src_stem"], []).append(
                (r["tile"], int(r["row"]), int(r["col"]),
                 int(r["window_px"]), float(r["fg_percent"])))

    # 열매가 충분히 든 사진들만 후보로
    cands = [s for s, v in rows_by_stem.items() if max(x[4] for x in v) >= 6.0]
    if not cands:
        cands = list(rows_by_stem)
    rng = random.Random(7)
    if len(cands) > 150:
        cands = rng.sample(cands, 150)

    best, best_err = None, None
    for stem in cands:
        d = _diam(SRC / fruit / "masks" / f"{stem}.png")
        if d is None:
            continue
        err = abs(d - target_diam)
        if best_err is None or err < best_err:
            best, best_err = stem, err

    tiles = sorted(rows_by_stem[best], key=lambda x: -x[4])
    tile, row, col, window, fg = tiles[0]
    return best, row, col, window, fg, tile


def starts(length: int, window: int, cover: float = 0.97):
    import math
    if window >= length:
        return [0]
    n = max(1, math.ceil(length * cover / window))
    if n == 1:
        return [(length - window) // 2]
    step = (length - window) / (n - 1)
    return [int(round(i * step)) for i in range(n)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    manifest_diam = {}
    import json
    man = json.loads((TILED / "manifest.json").read_text())
    for fr, v in man["fruits"].items():
        manifest_diam[fr] = v["diam_median_px"]

    panels = {}
    for fruit in FRUITS:
        stem, row, col, window, fg, tile_name = pick(fruit, manifest_diam[fruit])
        img = Image.open(SRC / fruit / "images" / f"{stem}.png").convert("RGB")
        W, H = img.size
        ys, xs = starts(H, window), starts(W, window)
        y, x = ys[row], xs[col]
        cy, cx = y + window // 2, x + window // 2

        # 「지금」 = 원본 화소 그대로 512 크롭 (학습이 지금 보는 것)
        x0 = max(0, min(W - 512, cx - 256))
        y0 = max(0, min(H - 512, cy - 256))
        now = img.crop((x0, y0, x0 + 512, y0 + 512))

        # 「바꾼 뒤」 = 새로 만든 타일
        new = Image.open(TILED / fruit / "images" / tile_name).convert("RGB")

        panels[fruit] = (now.resize((CELL, CELL), Image.LANCZOS),
                         new.resize((CELL, CELL), Image.LANCZOS),
                         window, tile_name)

    Wpx = LEFT + 4 * CELL + 3 * GAP + PAD
    head_h = 160
    colh = 40
    cap = 58
    foot_h = 250
    Hpx = head_h + colh + (CELL + cap) * 2 + 26 + foot_h

    canvas = Image.new("RGB", (Wpx, Hpx), (255, 255, 255))
    d = ImageDraw.Draw(canvas)

    d.text((PAD, 26), "4개 데이터셋을 «똑같아 보이게» 맞춰봤습니다", fill=(15, 15, 15), font=f(38, True))
    d.text((PAD, 78),
           "① 열매가 화면에 같은 크기로 보이도록 과일별 배율을 맞추고  "
           "② 전부 512×512 조각으로 잘랐습니다",
           fill=(40, 40, 40), font=f(21))
    d.text((PAD, 110),
           "⛔ 기존 데이터(datasets_resized_2mp)와 팀 공유 경로는 한 장도 건드리지 않았습니다. 새 폴더에 따로 만들었습니다.",
           fill=(170, 0, 0), font=f(19))

    y_col = head_h
    for i, fruit in enumerate(FRUITS):
        x = LEFT + i * (CELL + GAP)
        d.text((x + CELL // 2 - 34, y_col + 4), KOR[fruit], fill=(15, 15, 15), font=f(26, True))

    y1 = head_h + colh
    y2 = y1 + CELL + cap

    d.text((PAD, y1 + CELL // 2 - 34), "지금", fill=(150, 0, 0), font=f(28, True))
    d.text((PAD, y1 + CELL // 2 + 4), "(현재 학습이\n 보는 512 크롭)", fill=(150, 0, 0), font=f(15))
    d.text((PAD, y2 + CELL // 2 - 34), "바꾼 뒤", fill=(0, 110, 40), font=f(28, True))
    d.text((PAD, y2 + CELL // 2 + 4), "(새 512 타일)", fill=(0, 110, 40), font=f(15))

    for i, fruit in enumerate(FRUITS):
        now, new, window, tile_name = panels[fruit]
        x = LEFT + i * (CELL + GAP)
        canvas.paste(now, (x, y1))
        d.rectangle([x, y1, x + CELL, y1 + CELL], outline=(150, 0, 0), width=3)
        d.text((x, y1 + CELL + 8),
               f"열매 지름 약 {manifest_diam[fruit]:.0f}px", fill=(150, 0, 0), font=f(19, True))
        d.text((x, y1 + CELL + 33),
               "과일마다 3.6배까지 차이", fill=(120, 120, 120), font=f(15))

        canvas.paste(new, (x, y2))
        d.rectangle([x, y2, x + CELL, y2 + CELL], outline=(0, 110, 40), width=3)
        d.text((x, y2 + CELL + 8), "열매 지름 72px", fill=(0, 110, 40), font=f(19, True))
        d.text((x, y2 + CELL + 33),
               f"{window}px 창 → 512로 통일", fill=(120, 120, 120), font=f(15))

    # ── 아래 요약 상자
    fy = y2 + CELL + cap + 20
    d.rectangle([PAD, fy, Wpx - PAD, Hpx - 20], fill=(246, 248, 250), outline=(200, 205, 210), width=2)
    t = man["totals"]
    lines = [
        (f"만든 것 : 원본 {t['src_images']:,}장  →  512×512 타일 {t['tiles']:,}장  "
         f"(폴드 배정은 기존과 동일. 같은 사진에서 나온 타일은 같은 split 으로 묶어 누수 0)", (15, 15, 15), 21, True),
        ("경로     : /data/project/2026summer/kds0206/datasets_tiled_512/", (0, 60, 160), 21, True),
        ("", (0, 0, 0), 8, False),
        ("※ \"어차피 512로 크롭해서 학습하는데 의미가 있나?\" — 맞습니다. 사진의 «크기»는 크롭 때문에 이미 같았습니다.",
         (60, 60, 60), 19, False),
        ("   달랐던 건 ① 열매가 «보이는 크기»(크롭으로는 안 고쳐짐) 와 ② 평가할 때 채점되는 범위(지금은 가운데 일부만) 입니다.",
         (60, 60, 60), 19, False),
        ("   이 두 개를 한꺼번에 맞춘 것이 이번 작업입니다. 아직 «후보»이고, 기존 실험을 대체하지 않습니다.",
         (60, 60, 60), 19, False),
    ]
    ty = fy + 16
    for txt, color, sz, bold in lines:
        if txt:
            d.text((PAD + 18, ty), txt, fill=color, font=f(sz, bold))
        ty += sz + 12

    out = OUT / "00_타일링_한장설명.png"
    canvas.save(out, optimize=True)
    print(f"[✓] {out}  ({canvas.size[0]}x{canvas.size[1]})")


if __name__ == "__main__":
    main()
