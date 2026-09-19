#!/usr/bin/env python
"""0810 랩미팅 지시 ① — fig.2 «원본 이미지에 crop 되는 영역을 빨간 선으로 표시».

녹취 근거 (reports/0810 랩미팅.txt)
  02:10 "그거를 이따가 어차피 표시를 해 주면 될 것 같은데 512 512 정도를"
  02:18 "크롭한 사진도 한번 좀 해보세요. 아무튼 넣고 나중에 빼면 되니까.
         아니면 여기다가도 512 이렇게 «빨간색 박스로 이렇게 칠해서 요 정도
         사이즈다»라고 표시해 주면 될 것 같거든요."
  02:20 "어떤 거는 예를 들어서 «대략 몇 개 정도 들어간다»고 볼 수 있는 거잖아요.
         실제 오브젝트가 몇 개 정도 들어갈, 그레이프 같은 경우에는
         «1개가 들어갈까 말까» 할 것 같은데요"
  03:27 "우리가 이제 AI는 512 512 사이즈로 크롭하는데"

그림 구성 (4과일 × 2열)
  왼쪽  원본 전체 + 빨간 사각형 = 학습이 실제로 보는 512x512 영역
        (평가와 같은 위치인 «가운데»에 그림. 랜덤크롭 위치도 옅은 선으로 2개 더)
  오른쪽 그 빨간 박스 안을 실제 크기로 잘라낸 것 + 그 안의 개체 수

대표 사진 고르는 규칙: 개체 수가 그 과일 «중앙값에 가장 가까운» 장.
  (전경이 가장 많은 장을 고르면 과장돼 보임 — 2026-08-09 타일링 그림에서 겪은 문제)

입력  datasets_resized_2mp/<fruit>/{images,masks} + output/object_stats_4fruits.json
출력  reports/figures/fig_crop_overlay_4fruits.{png,pdf}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from skimage.color import label2rgb

from instance_split import centroids_of, label_instances

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
OUT = ROOT / "semantic-segmentation/reports/figures/fig_crop_overlay_4fruits"

FRUITS = ["blueberry", "apple", "peach", "grape"]
CROP = 512
RED = "#dc2626"
FAINT = "#f59e0b"
MIN_AREA = 10


def pick_representative(fruit: str, stats: dict) -> tuple[Path, Path, int]:
    """대표 사진 고르기 — «그 크롭이 전형인 장».

    처음에는 «사진 전체의 개체 수»가 중앙값인 장을 골랐는데, 사진 전체가 평범해도
    하필 가운데가 잎사귀면 크롭이 비어서 4과일 중 3개가 «0개»로 나왔다.
    그러면 교수님 요구(02:20 "대략 몇 개 정도 들어간다")를 못 보여준다.

    그래서 두 조건을 같이 본다. 둘 다 중앙값에 가까울수록 좋다.
      ① 사진 전체 개체 수       가 그 과일의 중앙값에 가까울 것
      ② 가운데 512 크롭 개체 수  가 그 과일의 중앙값에 가까울 것   ← 새로 추가
    손으로 특정 장을 집는 게 아니라 규칙이므로 재현 가능하고 캡션에 적어 방어할 수 있다.
    """
    s = stats["fruits"][fruit]
    counts = np.array(s["per_image_counts"])
    centers = np.array(s["per_image_center"])
    masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
    assert len(masks) == len(counts) == len(centers), f"{fruit}: 통계 길이 불일치"

    # 크롭이 비어 있는 장은 대표에서 제외한다.
    cand = np.nonzero(centers > 0)[0]
    if len(cand) == 0:
        cand = np.arange(len(counts))

    med_img = np.median(counts)
    med_cen = np.median(centers[centers > 0]) if (centers > 0).any() else 0.0
    d_img = np.abs(counts[cand] - med_img).astype(float)
    d_cen = np.abs(centers[cand] - med_cen).astype(float)
    # 크롭이 그림의 «주인공»이므로 ②에 3배 가중치
    score = 1.0 * (d_img / (d_img.max() or 1)) + 3.0 * (d_cen / (d_cen.max() or 1))
    i = int(cand[int(np.argmin(score))])

    mp = masks[i]
    imgs = {p.stem: p for p in (POOL / fruit / "images").iterdir() if p.is_file()}
    return imgs[mp.stem], mp, int(counts[i])


def load_pair(ip: Path, mp: Path):
    img = np.array(Image.open(ip).convert("RGB"))
    m = np.array(Image.open(mp))
    if m.ndim == 3:
        m = m[..., 0]
    return img, (m > 0), m


def count_in(raw: np.ndarray, top: int, left: int, fruit: str, stem: str) -> tuple[int, int, np.ndarray, np.ndarray]:
    """크롭 안 개체 수를 «중심 기준»과 «걸친 것 포함» 두 가지로 센다.

    - 중심 기준(centroid): 통계용 정의. 걸친 개체를 이중으로 안 셈.
    - 걸친 것 포함(overlap): 눈으로 보이는 개수와 맞음. 그림에 같이 적어야
      "분명히 보이는데 왜 0개냐"는 오해가 안 생긴다.

    개체 정의는 통계와 **같은 것**을 써야 한다(2026-08-10) — 정답 어노테이션이 있는
    사과·복숭아·포도는 정답으로, 블루베리만 분리 알고리즘으로 센다.
    """
    lab, idx, _ = label_instances(raw, fruit, stem=stem)
    if not len(idx):
        return 0, 0, lab, idx
    cent = centroids_of(lab, idx)
    n_cent = int(((cent[:, 0] >= top) & (cent[:, 0] < top + CROP) &
                  (cent[:, 1] >= left) & (cent[:, 1] < left + CROP)).sum())
    H, W = raw.shape
    win = lab[max(0, top):min(H, top + CROP), max(0, left):min(W, left + CROP)]
    present = np.unique(win)
    n_ovl = int(len(np.intersect1d(present[present > 0], idx)))
    return n_cent, n_ovl, lab, idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    stats = json.loads(STATS.read_text())
    fig, axes = plt.subplots(len(FRUITS), 3, figsize=(14.6, 4.1 * len(FRUITS)),
                             gridspec_kw={"width_ratios": [1.55, 1.0, 1.0]})

    for r, fruit in enumerate(FRUITS):
        s = stats["fruits"][fruit]
        ip, mp, n_img = pick_representative(fruit, stats)
        img, binary, raw = load_pair(ip, mp)
        H, W = binary.shape
        ctop, cleft = (max(H, CROP) - CROP) // 2, (max(W, CROP) - CROP) // 2
        n_center, n_ovl, lab, idx = count_in(raw, ctop, cleft, fruit, mp.stem)

        # ── 왼쪽: 원본 + 빨간 사각형 ────────────────────────────
        axL = axes[r, 0]
        axL.imshow(img)
        rng = np.random.default_rng(7)
        for _ in range(2):   # 랜덤크롭 위치 예시 2개 (옅게)
            t = int(rng.integers(0, max(1, H - CROP + 1)))
            l = int(rng.integers(0, max(1, W - CROP + 1)))
            axL.add_patch(Rectangle((l, t), CROP, CROP, fill=False,
                                    ec=FAINT, lw=1.6, ls="--", alpha=.85))
        axL.add_patch(Rectangle((cleft, ctop), CROP, CROP, fill=False, ec=RED, lw=3.0))
        axL.text(cleft + 8, ctop + 40, "512×512", color=RED, fontsize=12,
                 fontproperties=BLD,
                 bbox=dict(fc="white", ec=RED, lw=1.2, alpha=.9, pad=2.2))
        axL.set_title(f"{s['kor']} — 원본 {W}×{H}  (사진 전체 {n_img}{s['unit']})",
                      fontproperties=BLD, fontsize=13, pad=7)
        axL.axis("off")
        # 이 과일 «전체»의 통계 — 사진 한 장의 우연에 좌우되지 않게 같이 적는다
        rc, cc = s["random_crop_512"], s["center_crop_512"]
        axL.text(0.5, -0.035,
                 f"전체 {s['images']:,}장 평균 {s['per_image']['mean']:.1f}{s['unit']}  ·  "
                 f"랜덤크롭 512 한 장에 평균 {rc['mean']:.1f}{s['unit']}  ·  "
                 f"가운데 크롭에 1{s['unit']} 이상 들어오는 사진 {cc['ge1_pct']:.1f}%",
                 transform=axL.transAxes, ha="center", va="top",
                 fontproperties=REG, fontsize=10.2, color="#374151")

        # ── 가운데: 그 512 크롭 (사진 그대로 = AI 입력) ─────────
        pad = np.zeros((max(H, CROP), max(W, CROP), 3), np.uint8)
        pad[:H, :W] = img
        crop_img = pad[ctop:ctop + CROP, cleft:cleft + CROP]

        axM = axes[r, 1]
        axM.imshow(crop_img)
        axM.add_patch(Rectangle((0, 0), CROP - 1, CROP - 1, fill=False, ec=RED, lw=3.0))
        axM.set_title("AI가 실제로 보는 512×512 (입력)",
                      fontproperties=BLD, fontsize=12.5, color=RED, pad=7)
        axM.axis("off")

        # ── 오른쪽: 같은 크롭에 라벨을 칠한 것 (정답) ────────────
        labpad = np.zeros((max(H, CROP), max(W, CROP)), np.int32)
        labpad[:H, :W] = np.where(np.isin(lab, idx), lab, 0)
        crop_lab = labpad[ctop:ctop + CROP, cleft:cleft + CROP]

        axR = axes[r, 2]
        axR.imshow(crop_img)
        if crop_lab.max() > 0:
            axR.imshow(label2rgb(crop_lab, bg_label=0, bg_color=None), alpha=0.55)
        axR.add_patch(Rectangle((0, 0), CROP - 1, CROP - 1, fill=False, ec=RED, lw=3.0))
        axR.set_title(f"그 안의 정답 → 중심이 크롭 안 {n_center}{s['unit']}"
                      f"  (걸치기만 해도 세면 {n_ovl}{s['unit']})",
                      fontproperties=BLD, fontsize=12.5, color=RED, pad=7)
        axR.axis("off")

    fig.suptitle("그림 2-1.  512 크롭 확대 — 입력과 정답을 나란히 (빨간 사각형 = 512×512)",
                 fontproperties=BLD, fontsize=16, y=0.997)
    # 마지막 줄 = 교수님 02:5x "땅바닥에 떨어진 거는 안 세는 거죠 ... 그런 것도
    # 얘기를 좀 써주는 게 좋을 것 같고" → 라벨 정책을 그림에 명시한다.
    fig.text(0.5, 0.004,
             "빨간 실선 = 평가 때 쓰는 가운데 512 크롭 ·  주황 점선 = 학습 때 쓰는 랜덤 크롭 위치 예시 2개.\n"
             "대표 사진은 «사진 전체 개체 수»와 «가운데 크롭 개체 수»가 둘 다 그 과일의 중앙값에 가까운 장으로 골랐습니다 (과장 방지).\n"
             "세는 기준은 «개체의 중심점이 크롭 안에 있는가» 입니다. 열매가 다 들어와야 하는 것이 아니고, 잘려도 중심이 안에 있으면 1개로 셉니다.\n"
             "(걸치기만 해도 세면 몇 개인지도 괄호로 같이 적었습니다 — 눈으로 보이는 개수와 맞춰 보시라고.)\n"
             "개체는 붙어 있는 열매를 거리변환+watershed 로 «한 알씩» 분리해 셌습니다 (포도만 라벨이 송이 단위라 송이로 셈).\n"
             "※ 땅에 떨어진 과실은 원칙적으로 라벨 대상이 아니지만(MinneApple p.4·복숭아 원논문 p.5 모두 낙과 제외), 사과 일부(낙과 보이는 42장 중 5장)에 라벨이 남아 규칙 미정입니다(교수님 확인 대기). 위 개수는 그 상태 그대로입니다.",
             ha="center", fontproperties=REG, fontsize=10.2, color="#4b5563")
    # 캡션이 5줄이라 아래 여백을 그만큼 비워 둔다. 좁히면 마지막 줄 과일의
    # 통계 한 줄과 캡션이 겹친다 (2026-08-10에 실제로 겹쳤음).
    fig.tight_layout(rect=[0, 0.062, 1, 0.985])

    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(f"{outp}.{ext}", dpi=150, bbox_inches="tight")
    print(f"저장: {outp}.png / .pdf")


if __name__ == "__main__":
    main()
