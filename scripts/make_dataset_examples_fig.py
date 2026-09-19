"""데이터셋 예시 그림 — 원본 사진 + 마스크(라벨)를 나란히
작성: 2026-07-23 (0723 교수님 지시: "원본 이미지 + 마스크 예시를 나란히 넣기")

블루베리 2쌍 + MinneApple 2쌍 = 4행. 산출물 reports/figures/fig_dataset_examples_pairs.{pdf,png}
"""
import glob
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
ROOT = "/data/project/2026summer/kds0206"

# (원본 dir, 마스크 dir, 라벨)
SETS = [
    (f"{ROOT}/dataset_6fold/cv1/train/images", f"{ROOT}/dataset_6fold/cv1/train/masks", "블루베리"),
    (f"{ROOT}/dataset_minneapple/train/images", f"{ROOT}/dataset_minneapple/train/masks", "MinneApple(사과)"),
]


def load_pair(imgdir, mskdir, idx):
    imgs = sorted(glob.glob(imgdir + "/*"))
    f = imgs[idx]
    img = Image.open(f).convert("RGB")
    name = f.split("/")[-1]
    # 같은 이름의 마스크
    m = sorted(glob.glob(f"{mskdir}/{name.rsplit('.',1)[0]}.*"))
    mask = np.array(Image.open(m[0]).convert("L"))
    binm = (mask > 0).astype(float)  # 0/255 든 인스턴스ID든 전경=1
    return np.array(img), binm, name


rows = []
for imgdir, mskdir, label in SETS:
    for idx in (0, len(glob.glob(imgdir + "/*")) // 2):
        rows.append((*load_pair(imgdir, mskdir, idx), label))

fig, axes = plt.subplots(len(rows), 3, figsize=(11, 3.0 * len(rows)))
for r, (img, mask, name, label) in enumerate(rows):
    axes[r, 0].imshow(img)
    axes[r, 0].set_ylabel(label, fontproperties=BLD, fontsize=12, color="#1f2937")
    axes[r, 1].imshow(mask, cmap="gray")
    # 오버레이
    ov = img.copy().astype(float)
    red = np.zeros_like(ov); red[..., 0] = 255
    a = (mask[..., None] * 0.45)
    ov = (ov * (1 - a) + red * a).astype(np.uint8)
    axes[r, 2].imshow(ov)
    for c, t in enumerate(["① 원본 사진", "② 마스크(정답 라벨)", "③ 겹쳐보기"]):
        if r == 0:
            axes[r, c].set_title(t, fontproperties=BLD, fontsize=12)
        axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
    fg = mask.mean() * 100
    axes[r, 0].set_xlabel(f"{name}  (전경 {fg:.1f}%)", fontproperties=REG, fontsize=8)

fig.suptitle("데이터셋 구성 — 원본 사진과 마스크(정답)는 1:1로 짝지어져 있습니다",
             fontproperties=BLD, fontsize=14, color="#1f2937")
fig.tight_layout(rect=[0, 0, 1, 0.97])
for ext in ("pdf", "png"):
    fig.savefig(f"{ROOT}/semantic-segmentation/reports/figures/fig_dataset_examples_pairs.{ext}",
                dpi=140, bbox_inches="tight")
print("저장: reports/figures/fig_dataset_examples_pairs.{pdf,png}")
