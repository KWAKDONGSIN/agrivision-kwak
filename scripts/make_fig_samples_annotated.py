"""지시 1번 — MinneApple 논문 **Fig.2 형식**의 «라벨 칠한 샘플 사진» + 512 크롭 선.

팀 역할분담 메모: "1. fig.2 원본 이미지에 crop되는 선 표시 / 데이터 통계를 보여주라"
여기서 «fig.2»는 MinneApple 논문(arXiv:1909.06441v2) **3쪽 Fig.2** —
   "Samples of annotated images of the detection, segmentation and counting datasets.
    The detection/segmentation datasets are annotated with object instance masks..."
즉 **라벨(인스턴스 마스크)을 색으로 칠한 샘플 사진**이다. 여기에 우리 요구사항인
«512 크롭이 어디를 보는지»를 빨간 선으로 얹는다.

녹취 근거 (reports/0810 랩미팅.txt)
  02:15 참석자1 "이 논문에다가 크롭한 사진"
  02:18 교수님 "빨간색 박스로 이렇게 칠해서 요 정도 사이즈다라고 표시해 주면 될 것 같거든요"
  02:20 교수님 "대략 몇 개 정도 들어간다고 볼 수 있는 거잖아요"
  02:5x 교수님 "땅바닥에 떨어진 거는 안 세는 거죠 ... 그런 것도 얘기를 좀 써주는 게 좋을 것 같고"

그림 구성 — 4과일 × 3장 (총 12장)
  각 칸: 원본 사진 + **개체별로 다른 색을 칠한 라벨** + 빨간 512 크롭 선 + 주황 랜덤크롭 선
  칸 제목: 그 사진의 개체 수 / 가운데 크롭에 들어오는 개체 수
  줄 왼쪽: 그 과일 전체 통계

샘플 고르는 규칙 (손으로 집지 않는다 — 재현 가능해야 방어된다)
  개체 수가 그 과일의 **25 / 50 / 75 백분위**에 가장 가까운 장 3장.
  → «적은 편 / 보통 / 많은 편»이 한 줄에 다 보인다.

입력  datasets_resized_2mp/<fruit>/{images,masks} + output/object_stats_4fruits_split.json
출력  reports/figures/fig_samples_annotated_4fruits.{png,pdf}
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
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from skimage.color import label2rgb

from instance_split import centroids_of, label_instances

Image.MAX_IMAGE_PIXELS = None

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
STATS = ROOT / "semantic-segmentation/output/object_stats_4fruits_split.json"
OUT = ROOT / "semantic-segmentation/reports/figures/fig_samples_annotated_4fruits"

FRUITS = ["blueberry", "apple", "peach", "grape"]
CROP = 512
RED = "#dc2626"
FAINT = "#f59e0b"
PCTS = [25, 50, 75]          # 샘플 3장을 뽑을 백분위
MAX_SIDE = 900               # 그림에 넣기 전 축소 (파일 크기·렌더 시간)


def pick_samples(fruit: str, stats: dict) -> list[tuple[Path, Path, int]]:
    """개체 수가 25/50/75 백분위에 가장 가까운 장 3개.

    🔴 조건 하나 추가 (2026-08-10) — **가운데 512 크롭에 개체가 1개 이상 들어오는 장**만
    고른다. 포도는 그런 장이 61.8% 인데 우연히 3장 모두 «가운데 0송이»가 뽑혀서,
    그림만 보면 «포도는 크롭에 아무것도 안 들어온다»로 읽혔다.
    백분위 기준선은 **전체 분포** 그대로 두고 후보만 좁히는 것이라 규칙은 유지된다.
    """
    s = stats["fruits"][fruit]
    counts = np.array(s["per_image_counts"])
    centers = np.array(s["per_image_center"])
    masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
    assert len(masks) == len(counts) == len(centers), f"{fruit}: 통계 길이 불일치"

    cand = np.nonzero(centers >= 1)[0]
    if len(cand) < len(PCTS):                 # 그런 장이 거의 없으면 조건을 푼다
        cand = np.arange(len(counts))

    imgs = {p.stem: p for p in (POOL / fruit / "images").iterdir() if p.is_file()}
    chosen: list[int] = []
    for q in PCTS:
        target = np.percentile(counts, q)     # 기준선은 «전체» 분포에서 잡는다
        order = cand[np.argsort(np.abs(counts[cand] - target))]
        for i in order:
            if int(i) not in chosen:
                chosen.append(int(i))
                break
    return [(imgs[masks[i].stem], masks[i], int(counts[i])) for i in chosen]


def shrink(img: np.ndarray, lab: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """긴 변이 MAX_SIDE 가 되게 줄인다. 라벨은 최근접(값이 ID라 보간 금지)."""
    H, W = lab.shape
    k = max(H, W) / MAX_SIDE
    if k <= 1:
        return img, lab, 1.0
    nh, nw = int(round(H / k)), int(round(W / k))
    img_s = np.array(Image.fromarray(img).resize((nw, nh), Image.BILINEAR))
    lab_s = np.array(Image.fromarray(lab.astype(np.int32), mode="I")
                     .resize((nw, nh), Image.NEAREST))
    return img_s, lab_s, H / nh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    stats = json.loads(STATS.read_text())
    ncol = len(PCTS)
    nrow = len(FRUITS)

    # 🔴 과일마다 «통계 한 줄»을 넣어야 하는데, 그림 축에 얹으면 옆 칸 사진과 겹친다.
    #   (2026-08-10에 실제로 겹쳤음) → gridspec 에 **캡션 전용 행**을 따로 만든다.
    # 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**: 아래 캡션이 **여덟 줄**인데 자리는 여섯 줄치뿐이라
    #   마지막 두 줄(«※ 땅에 떨어진 과실 …» = 교수님이 넣으라고 한 문장)이 **그림 밖으로 잘려** 보이지
    #   않았다(실측: 그림 높이 3,120px · 마지막 글자 3,117px · 아래 여백 2px). 캡션 높이는
    #   8줄 × 10.2pt × 1.6 = 1.81in 인데 0.062×19.5in = 1.21in 만 있었다.
    #   → 그림을 0.9in 높이고(1.5 → 2.4) 그 0.9in 을 **전부 캡션 자리로** 준다. 위 패널의 크기·위치는
    #     인치로 그대로다(bottom·top 을 0.9in 만큼 올려 잡았다). 캡션 글꼴·글자는 한 자도 안 고쳤다.
    fig = plt.figure(figsize=(4.35 * ncol, 4.5 * nrow + 2.4))
    _H = 4.5 * nrow + 2.4                      # 그림 높이(인치) — 아래 비율을 인치로 계산하려고
    gs = GridSpec(nrow * 2, ncol, figure=fig,
                  height_ratios=[1.0, 0.11] * nrow,
                  hspace=0.22, wspace=0.05,
                  left=0.015, right=0.985,
                  top=(0.955 * (4.5 * nrow + 1.5) + 0.9) / _H,
                  bottom=(0.075 * (4.5 * nrow + 1.5) + 0.9) / _H)
    axes = np.empty((nrow, ncol), dtype=object)
    cap_axes = []
    for r in range(nrow):
        for c in range(ncol):
            axes[r, c] = fig.add_subplot(gs[2 * r, c])
        cax = fig.add_subplot(gs[2 * r + 1, :])
        cax.axis("off")
        cap_axes.append(cax)

    fig.suptitle("그림 2.  라벨을 칠한 샘플 사진 + 512 크롭이 보는 영역  "
                 "(MinneApple 논문 Fig.2 형식)",
                 fontproperties=BLD, fontsize=16, y=0.985)

    methods = {}
    for r, fruit in enumerate(FRUITS):
        s = stats["fruits"][fruit]
        unit = s["unit"]
        for c, (ip, mp, n_img) in enumerate(pick_samples(fruit, stats)):
            img = np.array(Image.open(ip).convert("RGB"))
            raw = np.array(Image.open(mp))
            if raw.ndim == 3:
                raw = raw[..., 0]

            lab, idx, method = label_instances(raw, fruit, stem=mp.stem, prefer_gt=True)
            methods[fruit] = method
            cent = centroids_of(lab, idx)

            H, W = raw.shape
            ctop, cleft = (max(H, CROP) - CROP) // 2, (max(W, CROP) - CROP) // 2
            if len(cent):
                inside = ((cent[:, 0] >= ctop) & (cent[:, 0] < ctop + CROP) &
                          (cent[:, 1] >= cleft) & (cent[:, 1] < cleft + CROP))
                n_cen = int(inside.sum())
            else:
                n_cen = 0

            keep = np.isin(lab, idx)
            shown = np.where(keep, lab, 0).astype(np.int32)
            img_s, lab_s, scale = shrink(img, shown)

            ax = axes[r, c]
            ax.imshow(img_s)
            if lab_s.max() > 0:
                ax.imshow(label2rgb(lab_s, bg_label=0, bg_color=None), alpha=0.55)

            # 512 크롭 선 (축소 배율만큼 줄여서 그린다)
            box = CROP / scale
            ax.add_patch(Rectangle((cleft / scale, ctop / scale), box, box,
                                   fill=False, ec=RED, lw=2.6))
            rng = np.random.default_rng(11 + c)
            for _ in range(2):
                t = int(rng.integers(0, max(1, H - CROP + 1))) / scale
                l = int(rng.integers(0, max(1, W - CROP + 1))) / scale
                ax.add_patch(Rectangle((l, t), box, box, fill=False,
                                       ec=FAINT, lw=1.5, ls="--", alpha=.9))
            ax.text(cleft / scale + 5, ctop / scale + box * 0.075, "512×512",
                    color=RED, fontsize=9.5, fontproperties=BLD,
                    bbox=dict(fc="white", ec=RED, lw=1.0, alpha=.9, pad=1.8))

            ax.set_title(f"{s['kor']} — 사진 전체 {n_img}{unit} · 가운데 크롭 {n_cen}{unit}",
                         fontproperties=BLD, fontsize=11, pad=5)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_color("#9ca3af")

        # 캡션 전용 행에 그 과일 전체 통계 (교수님 "데이터 통계를 보여주라")
        p, rc, cc = s["per_image"], s["random_crop_512"], s["center_crop_512"]
        cap_axes[r].text(
            0.5, 0.75,
            f"[{s['kor']}]  전체 {s['images']:,}장  ·  장당 평균 {p['mean']:.1f}{unit} "
            f"(중앙 {p['median']:.0f} · 최대 {p['max']})  ·  랜덤크롭 512 한 장에 {rc['mean']:.1f}{unit}"
            f"  ·  가운데 크롭에 1{unit} 이상 {cc['ge1_pct']:.1f}%"
            f"  ·  개체 지름 중앙 {s['diameter_px_median']:.0f}px  ·  전경 {s['fg_ratio_mean_pct']:.1f}%",
            transform=cap_axes[r].transAxes, ha="center", va="top",
            fontproperties=REG, fontsize=10.4, color="#374151")

    # 캡션 시작 높이도 같이 0.9in 올린다(위 주석 — 8줄이 다 들어가게).
    fig.text(0.5, (0.062 * (4.5 * nrow + 1.5) + 0.9) / _H,
             "색이 다르면 «다른 개체»라는 뜻입니다.  빨간 실선 = 평가 때 쓰는 가운데 512 크롭,  "
             "주황 점선 = 학습 때 쓰는 랜덤 크롭 위치 예시 2개.\n"
             "«가운데 크롭 N개»는 개체의 중심점이 크롭 안에 있는 것을 센 값입니다. 열매가 다 들어와야 하는 것은 아닙니다.\n"
             "샘플 3장은 개체 수가 그 과일의 25 / 50 / 75 백분위에 가장 가까운 장입니다 "
             "(손으로 고르지 않음 — 적은 편·보통·많은 편이 한 줄에 다 보이게).\n"
             "단, 가운데 크롭이 비어 있으면 크롭 안 개수를 보여줄 수 없어 «가운데 크롭에 1개 이상 "
             "들어오는 장» 중에서 골랐습니다. 그런 장의 비율은 줄마다 적어 두었습니다.\n"
             "라벨 칠하는 방법: 사과는 라벨 자체에 열매 번호가 들어 있어 «정답»을 그대로 칠했고, "
             "나머지 3과일은 이진 라벨이라 분리 알고리즘 결과를 칠했습니다.\n"
             "포도는 라벨이 «송이» 단위로 그려져 있어 송이 하나가 한 색입니다.\n"
             # 🔴 사이클4 2차: 이 문장을 **한 줄로 두면 그림 폭(2,088px)을 넘어 양쪽이 잘린다**
             #   (실측 2026-09-19 20:26). 글자는 한 자도 고치지 않고 줄바꿈만 넣는다.
             "※ 땅에 떨어진 과실은 원칙적으로 라벨 대상이 아닙니다 (MinneApple 논문 p.4: "
             "\"the ones on the ground and trees in the background were not tagged\").\n"
             "다만 우리 사과 일부(낙과 보이는 42장 중 5장)에 라벨이 남아 규칙 미정이라 위 개수는 그 상태 그대로입니다.",
             ha="center", va="top", fontproperties=REG, fontsize=10.2,
             color="#4b5563", linespacing=1.6)

    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{outp}.{ext}", dpi=160 if ext == "png" else None)
    print(f"저장: {outp}.png / .pdf")


if __name__ == "__main__":
    main()
