#!/usr/bin/env python
"""0810 랩미팅 지시 ④ 근거 — «센터크롭 평가의 문제»를 한 장으로 보여준다.

녹취 근거 (reports/0810 랩미팅.txt)
  03:42 교수님 "평가할 때는 센터 크롭한다고 그랬죠.
                «센터에는 반드시 한 개 이상 거의 들어가나요?»"
  37:46 교수님 "이렇게 센터 크롭으로 평가하는 게 일반적인지, 아니면
                원본 이미지를 그냥 평가하는 게 맞는 건지... 그리고 패치를 잘 붙이면
                원본이 만들 수 있으니까 마스크 이미지를, 그것도 한번 좀 알아보고요."

이 그림이 답하는 것
  (a) 실제 사진 한 장에서 «채점되는 영역»이 얼마나 좁은가 — 눈으로
  (b) 4과일 각각 «가운데 크롭에 열매가 하나도 안 들어오는 사진»이 몇 %인가 — 숫자

예시 사진 고르는 규칙 (체리피킹 방지)
  가운데 크롭에 개체가 0개인 사진들 중에서, «사진 전체 개체 수»가 그 부분집합의
  중앙값인 장. 즉 «가장 심한 장»이 아니라 «그런 경우의 전형»을 고른다.

출력  reports/figures/fig_centercrop_problem.{png,pdf}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

Image.MAX_IMAGE_PIXELS = None

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
STATS = ROOT / "semantic-segmentation/output/object_stats_4fruits_split.json"
OUT = ROOT / "semantic-segmentation/reports/figures/fig_centercrop_problem"

CROP = 512
RED = "#dc2626"
GREEN = "#22c55e"
ORDER = ["blueberry", "apple", "peach", "grape"]
COLOR = {"blueberry": "#3b5bdb", "apple": "#e03131",
         "peach": "#f08c00", "grape": "#7048e8"}


def pick_example(fruit: str, stats: dict):
    """가운데 크롭이 «비어 있는» 경우의 전형적인 장을 고른다."""
    s = stats["fruits"][fruit]
    counts = np.array(s["per_image_counts"])
    centers = np.array(s["per_image_center"])
    masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
    cand = np.nonzero((centers == 0) & (counts > 0))[0]
    if len(cand) == 0:
        cand = np.nonzero(counts > 0)[0]
    med = np.median(counts[cand])
    i = int(cand[int(np.argmin(np.abs(counts[cand] - med)))])
    mp = masks[i]
    imgs = {p.stem: p for p in (POOL / fruit / "images").iterdir() if p.is_file()}
    return imgs[mp.stem], mp, int(counts[i]), int(centers[i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruit", default="grape", help="예시로 쓸 과일")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    stats = json.loads(STATS.read_text())
    s = stats["fruits"][a.fruit]
    ip, mp, n_img, n_cen = pick_example(a.fruit, stats)

    img = np.array(Image.open(ip).convert("RGB")).astype(float)
    m = np.array(Image.open(mp))
    if m.ndim == 3:
        m = m[..., 0]
    binary = m > 0
    H, W = binary.shape
    ctop, cleft = (max(H, CROP) - CROP) // 2, (max(W, CROP) - CROP) // 2

    # 마스크를 초록으로 얹고, 크롭 «바깥»은 어둡게 = 채점 안 되는 영역
    vis = img.copy()
    vis[binary] = 0.45 * vis[binary] + 0.55 * np.array([34, 197, 94])
    dim = np.full((H, W, 1), 0.32)
    dim[ctop:ctop + CROP, cleft:cleft + CROP] = 1.0
    vis = (vis * dim).clip(0, 255).astype(np.uint8)

    scored_pct = CROP * CROP / (H * W) * 100

    # 캡션은 «전용 행»에 넣는다. fig.text + bbox_inches="tight" 조합은 여백을
    # 다시 잘라내서 캡션이 그래프 위에 얹히므로, 격자로 자리를 확보해야 안전하다.
    fig = plt.figure(figsize=(14.6, 9.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.32],
                          height_ratios=[1.0, 0.30], wspace=.18, hspace=.06)

    # ── (a) 사진 한 장 ────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(vis)
    ax.add_patch(Rectangle((cleft, ctop), CROP, CROP, fill=False, ec=RED, lw=3.4))
    ax.text(cleft + 8, ctop - 14, "평가가 채점하는 유일한 영역", color=RED,
            fontproperties=BLD, fontsize=12,
            bbox=dict(fc="white", ec=RED, lw=1.2, alpha=.95, pad=2.5))
    ax.set_title(f"(a) {s['kor']} 사진 한 장 — 초록 = 정답 {s['unit']} {n_img}개",
                 fontproperties=BLD, fontsize=14, pad=8)
    ax.axis("off")
    cap_a = (f"밝은 사각형 안만 채점됩니다. 어두운 부분, 즉 사진의 {100 - scored_pct:.1f}%는\n"
             f"채점에 아예 쓰이지 않습니다.\n"
             f"박스 안에 초록이 보이지만 그것은 큰 {s['unit']}의 «잘린 일부»입니다.\n"
             f"{s['unit']} {n_img}개 중 온전히 들어온 것은 {n_cen}개입니다.")

    # ── (b) 4과일 숫자 ────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1])
    names = [stats["fruits"][k]["kor"] for k in ORDER]
    empty = [100 - stats["fruits"][k]["center_crop_512"]["ge1_pct"] for k in ORDER]
    bars = ax.barh(names[::-1], empty[::-1],
                   color=[COLOR[k] for k in ORDER][::-1], height=.58)
    for b, v in zip(bars, empty[::-1]):
        ax.text(v + 0.6, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
                va="center", fontproperties=BLD, fontsize=13, color="#1f2937")
    ax.set_xlabel("가운데 크롭에 열매가 «온전히» 하나도 안 들어오는 사진의 비율 (%)",
                  fontproperties=REG, fontsize=12)
    ax.set_title("(b) 채점할 열매가 없는 사진이 이만큼 있습니다",
                 fontproperties=BLD, fontsize=14, pad=8)
    ax.set_xlim(0, max(empty) * 1.32)
    ax.grid(axis="x", alpha=.25, ls=":")
    for t in ax.get_yticklabels():
        t.set_fontproperties(REG)
        t.set_fontsize(13)
    for t in ax.get_xticklabels():
        t.set_fontproperties(REG)
    cap_b = ("포도는 세 장에 한 장꼴입니다.\n"
             "평가 점수가 «모델 실력»이 아니라\n"
             "«가운데에 열매가 있었는지»에 좌우된다는 뜻입니다.")

    # ── 캡션 전용 행 ──────────────────────────────────────────────
    # 오른쪽은 막대그래프의 x축 라벨이 이 행까지 내려오므로 캡션을 더 아래에서 시작한다.
    for col, cap, ytop in ((0, cap_a, 1.00), (1, cap_b, 0.30)):
        axt = fig.add_subplot(gs[1, col])
        axt.axis("off")
        axt.text(0.5, ytop, cap, ha="center", va="top", transform=axt.transAxes,
                 fontproperties=REG, fontsize=11.3, color="#374151", linespacing=1.6)

    fig.suptitle(f"센터크롭 평가의 문제 — 사진의 {100 - scored_pct:.0f}%를 안 보고 점수를 매기고 있습니다",
                 fontproperties=BLD, fontsize=16.5, y=0.985)
    fig.text(0.5, 0.012,
             "리사이즈본 4,823장 전수 기준. 예시 사진은 «가운데 크롭에 온전한 송이가 없는 사진들 중 전형적인 장»을 규칙으로 골랐습니다 (가장 심한 장이 아님).\n"
             "«온전히» = 개체의 중심이 크롭 안에 들어온 것. 잘려서 일부만 걸친 것은 세지 않았습니다.",
             ha="center", va="top", fontproperties=REG, fontsize=10.3,
             color="#6b7280", linespacing=1.5)

    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{outp}.{ext}", dpi=150, bbox_inches="tight")
    print(f"저장: {outp}.png / .pdf")
    print(f"예시: {ip.name} | 사진 전체 {n_img}{s['unit']} → 채점 {n_cen}{s['unit']}"
          f" | 채점 면적 {scored_pct:.1f}%")
    for k in ORDER:
        f = stats["fruits"][k]
        print(f"  {f['kor']:<5} 빈 크롭 {100 - f['center_crop_512']['ge1_pct']:5.1f}%")


if __name__ == "__main__":
    main()
