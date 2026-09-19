#!/usr/bin/env python
"""'화소 수'와 '해상도'가 어떻게 다른지, 교수님이 무엇을 맞추라고 하셨는지 그림으로 설명.

만드는 그림: reports/figures/fig_pixel_vs_resolution.png (+ .pdf)
  1행 — 같은 화소 수(2,073,600), 다른 해상도 3가지를 실제 비율로 그림
  2행 — 512x512 크롭이 사진의 몇 %를 덮는가: 통일 전 vs 통일 후

숫자는 전부 이 파일 안에서 계산합니다(하드코딩된 결론 없음).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

OUT = Path("/data/project/2026summer/kds0206/semantic-segmentation/reports/figures")
TARGET = 1440 * 1440          # 2,073,600
CROP = 512 * 512              # 262,144

INK, BLUE, RED, GREEN, GREY = "#222222", "#1f6feb", "#d1242f", "#1a7f37", "#8c959f"

# 같은 화소 수, 다른 해상도
SHAPES = [(1440, 1440, "정사각형 1:1", "블루베리 Camera 1~3"),
          (1080, 1920, "세로로 김 9:16", "포도·사과·블루베리 4K"),
          (1920, 1080, "가로로 김 16:9", "복숭아 일부")]

# 통일 전 원본 해상도
BEFORE = [("복숭아\n(제일 큰 것)", 4032, 3024),
          ("블루베리 4K\n(Camera 4)", 2160, 3840),
          ("포도\nCERTH", 2160, 3840),
          ("블루베리\n(Camera 1~3)", 1440, 1440),
          ("복숭아\n(제일 작은 것)", 1080, 1440),
          ("사과\nMinneApple", 720, 1280)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(13.5, 12.0))
    gs = fig.add_gridspec(4, 3, height_ratios=[0.40, 1.05, 0.22, 1.15],
                          hspace=0.30, wspace=0.18)

    # ── 제목 ────────────────────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, :]); ax.axis("off")
    ax.text(0.5, 1.18, "화소 수 vs 해상도 — 교수님이 맞추라고 하신 건 무엇인가",
            ha="center", va="top", fontproperties=BLD, fontsize=21, color=INK)
    ax.text(0.5, 0.44,
            "해상도 = 가로 몇 개 × 세로 몇 개  (사진의 모양과 크기)\n"
            "화소 수 = 가로 × 세로  (사진에 담긴 정보의 총량)",
            ha="center", va="center", fontproperties=REG, fontsize=13, color=INK)
    ax.text(0.5, 0.02, "→ 교수님이 통일하라고 하신 것은 «화소 수» 입니다. 해상도는 서로 달라도 됩니다.",
            ha="center", va="bottom", fontproperties=BLD, fontsize=14, color=BLUE)

    # ── 1행: 같은 화소 수, 다른 해상도 ──────────────────────────────────
    for i, (w, h, shape_txt, who) in enumerate(SHAPES):
        ax = fig.add_subplot(gs[1, i]); ax.axis("off")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        s = 0.52 / max(w, h)                       # 실제 비율 그대로 축소
        bw, bh = w * s, h * s
        cy = 0.60                                   # 상자 세로 중심 (세로 범위 0.34~0.86)
        ax.add_patch(Rectangle((0.5 - bw / 2, cy - bh / 2), bw, bh,
                               facecolor="#dbeafe", edgecolor=BLUE, linewidth=2))
        ax.text(0.5, 0.95, f"{w} × {h}", ha="center", va="top",
                fontproperties=BLD, fontsize=15, color=BLUE)
        ax.text(0.5, 0.26, f"{shape_txt}\n{who}", ha="center", va="top",
                fontproperties=REG, fontsize=10.5, color=GREY)
        ax.text(0.5, 0.05, f"화소 {w*h:,}", ha="center", va="top",
                fontproperties=BLD, fontsize=12, color=GREEN)

    # ── 2행: 1행 요약 문장 (겹치지 않게 전용 칸) ─────────────────────────
    ax = fig.add_subplot(gs[2, :]); ax.axis("off")
    ax.text(0.5, 0.80, "▲ 모양(해상도)은 전부 다르지만 화소 수는 셋 다 똑같이 2,073,600 입니다.",
            ha="center", va="top", fontproperties=BLD, fontsize=12.5, color=GREEN)
    ax.text(0.5, 0.22,
            "종이에 비유하면 — 해상도는 «가로세로 길이», 화소 수는 «넓이». 넓이가 같아도 모양은 다를 수 있습니다.",
            ha="center", va="top", fontproperties=REG, fontsize=11, color=GREY)

    # ── 3행: 512 크롭이 덮는 비율 ───────────────────────────────────────
    ax = fig.add_subplot(gs[3, :])
    names = [b[0] for b in BEFORE]
    pcts = [CROP / (b[1] * b[2]) * 100 for b in BEFORE]
    after = CROP / TARGET * 100

    y = range(len(names))
    ax.barh(list(y), pcts, color="#fca5a5", edgecolor=RED, height=0.55, label="통일 전 (원본)")
    ax.axvline(after, color=GREEN, linewidth=2.5, linestyle="--")
    ax.text(after, -0.85, f"통일 후 — 전부 {after:.2f}%", ha="center", va="bottom",
            fontproperties=BLD, fontsize=12, color=GREEN)

    for i, (p, b) in enumerate(zip(pcts, BEFORE)):
        ax.text(p + 0.4, i, f"{p:.2f}%   ({b[1]}×{b[2]})",
                va="center", fontproperties=REG, fontsize=10.5, color=INK)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontproperties=REG, fontsize=10.5)
    ax.set_ylim(len(names) - 0.5, -1.3)          # 위쪽에 '통일 후' 문구 자리 확보
    ax.set_xlim(0, max(pcts) * 1.32)
    ax.set_xlabel("512×512 크롭 한 장이 사진 전체에서 차지하는 비율 (%)",
                  fontproperties=REG, fontsize=11.5)
    ax.set_title(f"왜 화소 수를 맞춰야 하나 — 학습은 512×512 로 잘라서 합니다 "
                 f"(통일 전 격차 {max(pcts)/min(pcts):.1f}배 → 통일 후 1.0배)",
                 fontproperties=BLD, fontsize=13.5, color=INK, pad=12)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="x", labelsize=10)

    fig.text(0.5, 0.015,
             "화소 수가 제각각이면 같은 512 크롭이라도 어떤 사진은 전체의 2%만, 어떤 사진은 28%를 봅니다. "
             "= 모델이 보는 «확대 배율»이 데이터셋마다 달라져 공정한 비교가 안 됩니다.",
             ha="center", fontproperties=REG, fontsize=11, color=INK)

    for ext in ("png", "pdf"):
        p = OUT / f"fig_pixel_vs_resolution.{ext}"
        fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
        print("저장:", p)


if __name__ == "__main__":
    main()
