#!/usr/bin/env python
"""0810 랩미팅 지시 ② — «이미지 한 장당 과실 개수» 통계 plot (MinneApple 3쪽 형식).

녹취 근거 (reports/0810 랩미팅.txt)
  12:02 "이미지 한 장에 121개 오브젝트가 있는 그런 게 이제 한 1% 돼 있고...
         한 장에 여러 개의 오브젝트들이 있다. 100개 이상의 50개 이상의 오브젝트들이
         있는 게 이 정도나 많이 있다. 이런 거 보여주는 거잖아요.
         그니까 «데이터셋이 다르다. 이거를 통계적으로 보여준» 거거든요."
  13:11 "벤치마크 논문들이 여러 개 있을 텐데 굳이 왜 이런 데이터셋을 새롭게 해야 되느냐
         → 이런 특성에 있어 가지고 구별이 되기 때문에 요것만 따로 해서
         뭐가 제일 좋은지 알아볼 필요가 있다. 뭐 이런 식인 거죠."
  14:20 "리사이즈 한 걸로. 이미지 한 장당 개수 계산하면 돼요."

= 이 그림의 목적은 «성능 자랑»이 아니라 **논문의 존재 이유를 통계로 방어**하는 것.

그림 3판
  (a) 이미지 한 장에 개체가 몇 개 있나  — 분포 (y = 사진 비율 %)
  (b) 개체가 N개 이상인 사진이 몇 %인가 — 누적 (교수님이 말한 "50개 이상, 100개 이상")
  (c) 카테고리는 1종인데 개체는 몇 개인가 — 총량

입력  output/object_stats_4fruits.json   (tools/count_objects_4fruits.py 산출)
출력  reports/figures/fig_objects_per_image_4fruits.{png,pdf}
"""
from __future__ import annotations

import argparse
import textwrap
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

ROOT = Path("/data/project/2026summer/kds0206")
STATS = ROOT / "semantic-segmentation/output/object_stats_4fruits_split.json"
OUT = ROOT / "semantic-segmentation/reports/figures/fig_objects_per_image_4fruits"

ORDER = ["blueberry", "apple", "peach", "grape"]
COLOR = {"blueberry": "#3b5bdb", "apple": "#e03131",
         "peach": "#f08c00", "grape": "#7048e8"}
INK = "#1f2937"

# ── 비교용 «일반 사물 데이터셋» 수치 ─────────────────────────────
# 출처: MinneApple 논문(arXiv:1909.06441v2) p.4 V. Dataset Statistics 본문에
#      «글자로 적혀 있는» 값만 옮겼다. 그림에서 눈으로 읽은 값은 쓰지 않는다.
#   "MinneApple contains 1.5 categories and 41.2 instances on average per image.
#    In contrast, the COCO dataset has 3.5 categories and 7.7 instances, and the
#    ImageNet and PASCAL VOC datasets both have less than two categories and
#    three instances per image on average."
# MinneApple 자체는 막대에 넣지 않는다 — «우리 사과»가 곧 MinneApple 이라 중복이다.
# 논문 기재 41.2개는 우리 측정(인스턴스ID 40.4개)의 «검증값»으로 캡션에만 적는다.
REF = [
    ("COCO", 7.7, "#d1d5db"),
    ("ImageNet Det.", 3.0, "#d1d5db"),
    ("PASCAL VOC", 3.0, "#d1d5db"),
]
# 논문 Fig.3(a) 형식 산점도용. 전부 p.4 본문의 «글자로 적힌» 값이다.
#   "MinneApple contains 1.5 categories and 41.2 instances on average per image.
#    ... COCO ... has 3.5 categories and 7.7 instances, and the ImageNet and PASCAL VOC
#    datasets both have less than two categories and three instances per image"
# ImageNet·VOC 는 «2 미만 / 3 미만»으로만 적혀 있어 상한값(2, 3)에 찍고 «<» 를 붙인다.
REF_SCATTER = [
    ("MinneApple(논문)", 1.5, 41.2, ""),
    ("COCO", 3.5, 7.7, ""),
    # ImageNet Det. 와 PASCAL VOC 는 논문에 «둘 다 2종 미만·3개 미만»으로만 적혀 있어
    # 좌표가 같다. 점 2개를 겹쳐 찍으면 글자가 포개지므로 하나로 합쳐 표기한다.
    ("ImageNet Det. · PASCAL VOC", 2.0, 3.0, "\n(둘 다 «2종 미만 · 3개 미만»)"),
]

# ⚠️ 2026-08-12 보강 — MinneApple 은 ImageNet·PASCAL VOC 를 «둘 다 3개 미만»으로 뭉뚱그렸으나,
#   COCO 원논문(Lin et al., ECCV 2014)은 ImageNet 3.0 / PASCAL 2.3 으로 따로 적는다.
#   막대는 MinneApple 기재를 따르되, 각주에 원논문 값을 함께 밝혀 반박 여지를 없앤다.
REF_CITE = ("비교값 출처: MinneApple 논문(arXiv:1909.06441v2) p.4 본문. ImageNet·PASCAL VOC는 «3개 미만»으로만 "
            "기재돼 3.0으로 표기. COCO 원논문(Lin et al., ECCV 2014)은 ImageNet 3.0 · PASCAL VOC 2.3 으로 구분한다.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", default=str(STATS))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    d = json.loads(Path(a.stats).read_text())
    F = d["fruits"]

    fig, axes2d = plt.subplots(2, 2, figsize=(13.6, 11.4))
    axes = axes2d.ravel()

    # ── (a) 이미지당 개체 수 분포 ────────────────────────────────
    ax = axes[0]
    bins = np.arange(0, 125, 5)
    for k in ORDER:
        c = np.array(F[k]["per_image_counts"])
        h, _ = np.histogram(np.clip(c, 0, 120), bins=bins)
        pct = h / len(c) * 100
        ax.step(bins[:-1], pct, where="post", lw=2.1, color=COLOR[k],
                label=f"{F[k]['kor']} (평균 {F[k]['per_image']['mean']:.1f})")
    ax.set_xlabel("사진 한 장에 들어 있는 개체 수", fontproperties=REG, fontsize=12)
    ax.set_ylabel("해당 사진의 비율 (%)", fontproperties=REG, fontsize=12)
    ax.set_title("(a) 한 장에 개체가 몇 개나 있나", fontproperties=BLD, fontsize=13.5)
    lg = ax.legend(prop=REG, fontsize=10.5, frameon=False)
    ax.grid(alpha=.25, ls=":")
    # 🔴 120 을 넘는 장은 마지막 칸에 합쳐 넣었다(블루베리 최대 204). 그 사실을 축에 밝힌다.
    over = max(F[k]["per_image"]["max"] for k in ORDER)
    ax.set_xticks([0, 20, 40, 60, 80, 100, 120])
    ax.set_xticklabels(["0", "20", "40", "60", "80", "100", "120+"])
    ax.axvline(120, color="#9ca3af", lw=1.0, ls="--", alpha=.8)
    ax.text(119, ax.get_ylim()[1] * 0.97, f"마지막 칸 = 120개 이상 전부 (최대 {over}개)",
            ha="right", va="top", fontproperties=REG, fontsize=9.3, color="#6b7280")

    # ── (b) 논문 Fig.3(a) 형식 — «종류는 적은데 개체는 많다» ────────
    ax = axes[1]
    for k in ORDER:
        ax.scatter(1.0, F[k]["per_image"]["mean"], s=180, color=COLOR[k],
                   edgecolor="white", lw=1.4, zorder=3)
    # 🔴 글자는 «자기 점»의 위아래에 붙어야 한다. 예전에는 ORDER 순서대로 번갈아 놓아서
    #   값이 큰 사과가 아래, 작은 블루베리가 위로 적혀 그림과 반대로 읽혔다(2026-08-10).
    #   → 값이 가까운 점끼리 묶어 «큰 쪽은 위, 작은 쪽은 아래»로 놓는다.
    vals = {k: F[k]["per_image"]["mean"] for k in ORDER}
    for k in ORDER:
        v = vals[k]
        near_above = any(v < vals[o] <= v * 1.6 for o in ORDER if o != k)
        dy = -14 if near_above else 5          # 위에 이웃이 있으면 나는 아래로
        ax.annotate(F[k]["kor"], (1.0, v), xytext=(9, dy),
                    textcoords="offset points", fontproperties=BLD, fontsize=11,
                    color=COLOR[k], va="bottom" if dy > 0 else "top")
    for (nm, cx, cy, note) in REF_SCATTER:
        ax.scatter(cx, cy, s=150, color="#9ca3af", edgecolor="white", lw=1.2, zorder=2)
        ax.annotate(nm + note, (cx, cy), xytext=(10, 6), textcoords="offset points",
                    fontproperties=REG, fontsize=9.6, color="#4b5563", linespacing=1.4)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.75, 9.0); ax.set_ylim(2.0, 120)
    ax.set_xticks([1, 2, 3.5]); ax.set_xticklabels(["1", "2", "3.5"])
    ax.set_yticks([3, 10, 40, 100]); ax.set_yticklabels(["3", "10", "40", "100"])
    ax.set_xlabel("사진 한 장에 들어 있는 «종류» 수", fontproperties=REG, fontsize=12)
    ax.set_ylabel("사진 한 장에 들어 있는 개체 수", fontproperties=REG, fontsize=12)
    ax.set_title("(b) 종류는 적은데 개체는 아주 많다  (논문 Fig.3a 형식)",
                 fontproperties=BLD, fontsize=13.5)
    ax.grid(alpha=.25, ls=":", which="both")
    ax.text(0.03, 0.04, "← 왼쪽 위로 갈수록 «한 종류를 빽빽하게»",
            transform=ax.transAxes, ha="left", fontproperties=REG,
            fontsize=9.5, color="#6b7280")

    # ── (c) 일반 사물 데이터셋과 장당 개체 수 비교 ─────────────────
    ax = axes[2]
    labs = [F[k]["kor"] + ("\n(MinneApple)" if k == "apple" else "")
            for k in ORDER] + [r[0] for r in REF]
    vals = [F[k]["per_image"]["mean"] for k in ORDER] + [r[1] for r in REF]
    cols = [COLOR[k] for k in ORDER] + [r[2] for r in REF]
    bars = ax.barh(labs[::-1], vals[::-1], color=cols[::-1], height=.62)
    for b, v in zip(bars, vals[::-1]):
        ax.text(v + max(vals) * .015, b.get_y() + b.get_height() / 2, f"{v:.1f}",
                va="center", fontproperties=BLD, fontsize=11, color=INK)
    # 구분선은 «MinneApple 아래»에 긋는다. 우리 사과가 곧 MinneApple 이므로
    # MinneApple 논문값은 «일반 사물 데이터셋»이 아니라 «우리 측정의 검증값»이다.
    ax.axhline(len(REF) - 0.5, color="#9ca3af", lw=1.2, ls="--")
    ax.text(max(vals) * .99, len(REF) - 0.32, "↑ 우리 데이터셋",
            ha="right", fontproperties=REG, fontsize=9.5, color="#6b7280")
    ax.text(max(vals) * .99, len(REF) - 0.70, "↓ 일반 사물 데이터셋",
            ha="right", va="top", fontproperties=REG, fontsize=9.5, color="#6b7280")
    ax.set_xlabel("사진 한 장당 평균 개체 수", fontproperties=REG, fontsize=12)
    ax.set_title("(c) 장당 개체 수를 나란히 비교하면",
                 fontproperties=BLD, fontsize=13.5)
    ax.set_xlim(0, max(vals) * 1.16)
    ax.grid(axis="x", alpha=.25, ls=":")
    for t in ax.get_yticklabels():
        t.set_fontproperties(REG)
        t.set_fontsize(11)

    # ── (d) 카테고리 1종 vs 총 개체 수 ───────────────────────────
    ax = axes[3]
    names = [F[k]["kor"] for k in ORDER]
    tot = [F[k]["objects_total"] for k in ORDER]
    imgs = [F[k]["images"] for k in ORDER]
    bars = ax.bar(names, tot, color=[COLOR[k] for k in ORDER], width=.62)
    for b, t, n in zip(bars, tot, imgs):
        cx = b.get_x() + b.get_width() / 2
        ax.text(cx, t + max(tot) * 0.025, f"{t:,}개",
                ha="center", fontproperties=BLD, fontsize=11, color=INK)
        # 막대가 짧으면 안쪽 흰 글씨가 숫자와 겹친다 → 막대 위쪽 바깥에 회색으로
        if t > max(tot) * 0.18:
            ax.text(cx, t * 0.5, f"사진\n{n:,}장", ha="center", va="center",
                    fontproperties=REG, fontsize=10, color="white")
        else:
            ax.text(cx, t + max(tot) * 0.075, f"사진 {n:,}장", ha="center",
                    fontproperties=REG, fontsize=9.5, color="#4b5563")
    ax.set_ylabel("데이터셋 전체 개체 수", fontproperties=REG, fontsize=12)
    ax.set_title("(d) 종류는 1가지인데 개체는 이만큼",
                 fontproperties=BLD, fontsize=13.5)
    ax.set_ylim(0, max(tot) * 1.18)
    ax.grid(axis="y", alpha=.25, ls=":")
    for t in ax.get_xticklabels():
        t.set_fontproperties(REG)
        t.set_fontsize(11.5)

    for axx in axes:
        for t in axx.get_yticklabels():
            t.set_fontproperties(REG)

    fig.suptitle("그림 3.  4개 과일 데이터셋의 «개체 밀도» 특성 — 왜 이 데이터셋을 따로 다뤄야 하는가",
                 fontproperties=BLD, fontsize=15.5, y=0.975)
    # 3번째 줄 = 교수님 02:5x "땅바닥에 떨어진 거는 안 세는 거죠" → 라벨 정책 명시.
    # 개수 통계 자체의 정의에 영향을 주므로 이 그림에도 반드시 적는다.
    ga = F["apple"].get("accuracy_vs_groundtruth", {})
    gp = F["peach"].get("accuracy_vs_groundtruth", {})
    # 🔴 캡션은 «줄 길이»를 직접 세어 접는다. 손으로 줄바꿈을 넣으면 글꼴·그림 폭이
    #   조금만 달라져도 양끝이 잘린다(2026-08-10에 실제로 잘렸음).
    paras = [
        "리사이즈본(datasets_resized_2mp) 4,823장 전수. 개수는 «정답 인스턴스 어노테이션»으로 셌습니다 — "
        "사과는 마스크 픽셀값이 인스턴스 ID, 복숭아는 peach-data COCO 폴리곤, "
        "포도는 CERTH COCO 인스턴스 마스크(송이 단위).",
        f"정답으로 알고리즘을 검증하면 — 사과 {ga.get('exact_mean', 0):.1f}개 vs 분리 알고리즘 "
        f"{ga.get('watershed_mean', 0):.1f}개({ga.get('watershed_bias_pct', 0):+.1f}%), "
        f"복숭아 {gp.get('exact_mean', 0):.1f}개 vs {gp.get('watershed_mean', 0):.1f}개"
        f"({gp.get('watershed_bias_pct', 0):+.1f}%). 두 데이터셋에서 정답으로 검증된 값입니다.",
        "※ 블루베리만 정답 어노테이션이 없어(원본이 이진 마스크뿐) 분리 알고리즘 값입니다 — 오차를 잴 수 없습니다.",
        "포도는 라벨이 «송이» 단위라 개수도 송이 수입니다. 이진 마스크를 덩어리로 세면 15,102개가 나오는데, "
        "잎·가지에 가려 한 송이가 여러 조각으로 끊긴 것을 따로 센 값이라 쓰지 않습니다.",
        "우리 사과가 곧 MinneApple 입니다. 논문 기재 41.2개 vs 우리 정답 40.4개 — 거의 일치합니다.",
        "※ 땅에 떨어진 과실은 원칙적으로 라벨 대상이 아닙니다"
        " (MinneApple 논문 p.4: \"the ones on the ground ... were not tagged\") — 단 우리 사과 일부(42장 중 5장)에 낙과 라벨이 남아 규칙 미정(교수님 확인 대기).",
        REF_CITE,
    ]
    wrapped = []
    for para in paras:
        wrapped += textwrap.wrap(para, width=124) or [""]
    fig.text(0.5, 0.172, "\n".join(wrapped),
             ha="center", va="top", fontproperties=REG, fontsize=9.8,
             color="#4b5563", linespacing=1.55)
    # 캡션 6줄을 아래에 «자리를 만들어» 넣는다. bbox_inches="tight" 와 음수 y 를 같이 쓰면
    # 패널과 캡션 사이에 커다란 빈 띠가 생긴다 (2026-08-10에 실제로 생겼음).
    fig.tight_layout(rect=[0, 0.195, 1, 0.945])

    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{outp}.{ext}", dpi=150)
    print(f"저장: {outp}.png / .pdf")

    # 논문 표에 그대로 쓸 수 있는 숫자도 찍어 둔다
    print("\n[논문 표용]")
    print(f"{'과일':<6}{'장수':>7}{'총개체':>9}{'장당평균':>9}{'중앙':>6}{'최대':>6}"
          f"{'50+%':>7}{'100+%':>7}{'지름중앙px':>11}")
    for k in ORDER:
        s, p = F[k], F[k]["per_image"]
        print(f"{s['kor']:<6}{s['images']:>7,}{s['objects_total']:>9,}{p['mean']:>9.1f}"
              f"{p['median']:>6.0f}{p['max']:>6d}{p['ge50_pct']:>7.1f}{p['ge100_pct']:>7.1f}"
              f"{s['diameter_px_median']:>11.1f}")


if __name__ == "__main__":
    main()
