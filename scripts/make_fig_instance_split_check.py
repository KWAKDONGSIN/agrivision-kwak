"""«과일 하나하나가 구별되는가»를 눈으로 확인하는 그림.

0810 랩미팅 04:02 교수님:
  "오브젝트가 우리가 개수 셀 수 있나요? ... 오브젝트 디텍션이면 바운딩 박스가 있어서
   1개가 어디 있는지 몇 개가 들어가는지 알 수 있는데 얘는 그게 없잖아요"

즉 «개수»보다 먼저 **개체가 한 알씩 구별되는가**가 요구사항이다. 이 그림은 그것을 보여준다.
  왼쪽   원본 사진 (512 크롭)
  가운데  옛 방법 — connected components. 붙어 있는 열매가 **한 덩어리 한 색**
  오른쪽  새 방법 — 거리변환+watershed. **한 알 = 한 색**, 중심에 점

사과는 정답(인스턴스 ID)이 있으므로 제목에 «정답 N개»를 같이 적어 검증이 되게 한다.

출력  reports/figures/fig_instance_split_check.{png,pdf}
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image
from skimage.color import label2rgb

from instance_split import MIN_AREA, centroids_of, label_cc, label_instances, split_instances

Image.MAX_IMAGE_PIXELS = None

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
OUT = ROOT / "semantic-segmentation/reports/figures/fig_instance_split_check"

FRUITS = ["blueberry", "apple", "peach", "grape"]
KOR = {"blueberry": "블루베리", "apple": "사과", "peach": "복숭아", "grape": "포도"}
UNIT = {"blueberry": "알", "apple": "알", "peach": "알", "grape": "송이"}
CROP = 512


def densest_window(binary: np.ndarray) -> tuple[int, int]:
    """전경이 가장 빽빽한 512 창의 좌상단. 붙어 있는 열매가 제일 잘 보이는 곳."""
    H, W = binary.shape
    if H <= CROP and W <= CROP:
        return 0, 0
    # 64px 격자로 성기게 훑는다 (전수 탐색은 불필요)
    best, pos = -1, (0, 0)
    ii = np.integral = binary.cumsum(0).cumsum(1)
    for top in range(0, max(1, H - CROP + 1), 64):
        for left in range(0, max(1, W - CROP + 1), 64):
            b, r = top + CROP - 1, left + CROP - 1
            s = ii[b, r]
            if top:
                s -= ii[top - 1, r]
            if left:
                s -= ii[b, left - 1]
            if top and left:
                s += ii[top - 1, left - 1]
            if s > best:
                best, pos = s, (top, left)
    return pos


def pick_image(fruit: str) -> tuple[Path, Path]:
    """전경 비율이 중앙값인 장 = 그 과일의 «전형적인» 사진."""
    masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
    step = max(1, len(masks) // 40)
    cand = masks[::step]
    ratios = []
    for p in cand:
        a = np.array(Image.open(p))
        if a.ndim == 3:
            a = a[..., 0]
        ratios.append((a > 0).mean())
    i = int(np.argsort(ratios)[len(ratios) // 2])
    mp = cand[i]
    imgs = {p.stem: p for p in (POOL / fruit / "images").iterdir() if p.is_file()}
    return imgs[mp.stem], mp


def panel(ax, rgb, lab, idx, title, dots=False):
    ax.imshow(rgb)
    if len(idx):
        keep = np.isin(lab, idx)
        shown = np.where(keep, lab, 0)
        ax.imshow(label2rgb(shown, bg_label=0, bg_color=None), alpha=0.55)
        if dots:
            c = centroids_of(lab, idx)
            ax.plot(c[:, 1], c[:, 0], "o", ms=2.6, mfc="white", mec="black", mew=0.6, ls="")
    ax.set_title(title, fontproperties=BLD, fontsize=11, pad=6)
    ax.set_xticks([]); ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    fig, axes = plt.subplots(len(FRUITS), 4, figsize=(15.0, 3.9 * len(FRUITS)))
    fig.suptitle("부록 그림.  개수를 무엇으로 셌나 — 두 알고리즘과 «정답» 대조",
                 fontproperties=BLD, fontsize=15, y=0.995)

    for r, fruit in enumerate(FRUITS):
        ip, mp = pick_image(fruit)
        img = np.array(Image.open(ip).convert("RGB"))
        m = np.array(Image.open(mp))
        if m.ndim == 3:
            m = m[..., 0]
        binary = m > 0

        top, left = densest_window(binary)
        sub_img = img[top:top + CROP, left:left + CROP]
        sub_bin = binary[top:top + CROP, left:left + CROP]
        sub_raw = m[top:top + CROP, left:left + CROP]

        lab_cc, idx_cc = label_cc(sub_bin)
        lab_ws, idx_ws = split_instances(sub_bin)

        # 정답 어노테이션 — 사진 전체에서 뽑아 같은 창으로 자른다
        lab_full, idx_full, how = label_instances(m, fruit, stem=mp.stem, prefer_gt=True)
        has_gt = "정답" in how
        if has_gt:
            sub_gt = lab_full[top:top + CROP, left:left + CROP]
            idx_gt = np.unique(sub_gt); idx_gt = idx_gt[idx_gt > 0]
        else:
            sub_gt, idx_gt = np.zeros_like(lab_cc), np.zeros(0, int)

        axes[r, 0].imshow(sub_img)
        axes[r, 0].set_title(f"{KOR[fruit]} — 512 크롭 원본",
                             fontproperties=BLD, fontsize=11, pad=6)
        axes[r, 0].set_xticks([]); axes[r, 0].set_yticks([])

        mark = "" if has_gt else "  ← 채택"
        panel(axes[r, 1], sub_img, lab_cc, idx_cc,
              f"덩어리 그대로  {len(idx_cc)}{UNIT[fruit]}")
        panel(axes[r, 2], sub_img, lab_ws, idx_ws,
              f"한 알씩 분리  {len(idx_ws)}{UNIT[fruit]}{mark}", dots=True)
        if has_gt:
            panel(axes[r, 3], sub_img, sub_gt, idx_gt,
                  f"정답  {len(idx_gt)}{UNIT[fruit]}  ← 채택", dots=True)
        else:
            axes[r, 3].imshow(sub_img, alpha=0.25)
            axes[r, 3].text(0.5, 0.5, "정답 라벨 없음\n(원본이 이진 마스크뿐)",
                            transform=axes[r, 3].transAxes, ha="center", va="center",
                            fontproperties=BLD, fontsize=12, color="#b91c1c")
            axes[r, 3].set_title("정답", fontproperties=BLD, fontsize=11, pad=6)
            axes[r, 3].set_xticks([]); axes[r, 3].set_yticks([])

    cap = ("색이 다르면 «서로 다른 개체»라는 뜻입니다(흰 점 = 그 개체의 중심).\n"
           "정답 출처 — 사과: 마스크 픽셀값이 인스턴스 ID · 복숭아: peach-data COCO 폴리곤 · "
           "포도: CERTH COCO 인스턴스 마스크(송이 단위).\n"
           "이 셋은 정답을 그대로 썼습니다. 블루베리만 정답이 없어 분리 알고리즘(거리변환+watershed)을 씁니다.\n"
           "포도에서 «덩어리 그대로»가 정답보다 많은 것은 잎·가지에 가려 한 송이가 여러 조각으로 끊기기 때문입니다.")
    fig.text(0.5, 0.005, cap, ha="center", va="bottom", fontproperties=REG,
             fontsize=9.5, color="#374151", linespacing=1.6)

    fig.tight_layout(rect=[0, 0.045, 1, 0.985])
    for ext in ("png", "pdf"):
        p = Path(f"{a.out}.{ext}")
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=170 if ext == "png" else None, bbox_inches=None)
        print("저장:", p)


if __name__ == "__main__":
    main()
