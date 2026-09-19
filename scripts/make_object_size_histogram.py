"""개체 크기 히스토그램 + 데이터셋 통계 그림 생성 (MinneApple Figure 4 재현)

작성: 2026-07-23 (0723 교수님 미팅 지시)
교수님: "MinneApple Figure 4처럼 개체 1개 마스크의 픽셀 면적 분포를 우리도 그려달라"

- MinneApple 마스크: 픽셀값이 인스턴스 ID(1..N) → 개체 면적을 정확히 계산
- 블루베리 마스크: 0/255 이진 → connected components로 근사 (붙은 개체는 과소계수)

산출물: reports/figures/fig_object_size_hist.{pdf,png}
        reports/figures/fig_objects_per_image.{pdf,png}
        output/object_size_stats.json  (숫자 재사용용)

숫자를 하드코딩하지 않고 마스크에서 직접 계산합니다.
"""
import json
import glob
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
BLD = FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

BLUE = "#2563eb"
GREEN = "#16a34a"
INK = "#1f2937"

ROOT = "/data/project/2026summer/kds0206"
MINNE_TRAIN = f"{ROOT}/dataset_minneapple/train/masks"
BLUE_TRAIN = f"{ROOT}/dataset_6fold/cv1/train/masks"


def minneapple_stats(maskdir, limit=None):
    """마스크 픽셀값 = 인스턴스 ID. 값별 픽셀 수 = 개체 면적."""
    fs = sorted(glob.glob(maskdir + "/*.png"))
    if limit:
        fs = fs[:limit]
    areas, per_img, fg = [], [], []
    for f in fs:
        a = np.array(Image.open(f))
        ids = np.unique(a)
        ids = ids[ids > 0]
        per_img.append(len(ids))
        fg.append(float((a > 0).mean()))
        counts = np.bincount(a.ravel())
        for i in ids:
            areas.append(int(counts[i]))
    return np.array(areas), np.array(per_img), np.array(fg), len(fs)


def blueberry_stats(maskdir, limit=None):
    """0/255 이진 마스크 → connected components로 개체 근사."""
    fs = sorted(glob.glob(maskdir + "/*"))
    if limit:
        fs = fs[:limit]
    areas, per_img, fg = [], [], []
    for f in fs:
        a = np.array(Image.open(f).convert("L")) > 127
        lab, n = ndimage.label(a)
        per_img.append(n)
        fg.append(float(a.mean()))
        if n:
            areas += list(np.bincount(lab.ravel())[1:])
    return np.array(areas), np.array(per_img), np.array(fg), len(fs)


def summarize(name, areas, per_img, fg, nimg, res):
    return {
        "name": name,
        "n_images": int(nimg),
        "resolution": res,
        "n_objects": int(areas.size),
        "obj_per_img_mean": float(per_img.mean()),
        "obj_per_img_median": float(np.median(per_img)),
        "obj_per_img_max": int(per_img.max()),
        "area_mean": float(areas.mean()),
        "area_median": float(np.median(areas)),
        "area_p5": float(np.percentile(areas, 5)),
        "area_p95": float(np.percentile(areas, 95)),
        "side_median": float(np.sqrt(np.median(areas))),
        "fg_ratio": float(fg.mean()),
        # 해상도 차이를 없앤 '화면 대비 비율' — 크기 비교는 반드시 이 값으로
        "area_frac_median": float(np.median(areas) / (res[0] * res[1])),
    }


def main():
    print("[1/3] MinneApple 통계 계산 중...")
    m_area, m_per, m_fg, m_n = minneapple_stats(MINNE_TRAIN)
    m = summarize("MinneApple (train)", m_area, m_per, m_fg, m_n, (1280, 720))

    print("[2/3] 블루베리 통계 계산 중 (표본 200장)...")
    b_area, b_per, b_fg, b_n = blueberry_stats(BLUE_TRAIN, limit=200)
    b = summarize("블루베리 (cv1 train, 표본)", b_area, b_per, b_fg, b_n, (1920, 1080))

    os.makedirs(f"{ROOT}/semantic-segmentation/output", exist_ok=True)
    os.makedirs(f"{ROOT}/semantic-segmentation/reports/figures", exist_ok=True)
    with open(f"{ROOT}/semantic-segmentation/output/object_size_stats.json", "w") as f:
        json.dump({"minneapple": m, "blueberry": b}, f, ensure_ascii=False, indent=2)

    print("[3/3] 그림 그리는 중...")

    # --- 그림 1: 개체 면적 히스토그램 (MinneApple Fig.4 형식) ---
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, area, col, title, stat in [
        (axes[0], m_area, GREEN, "MinneApple (사과)", m),
        (axes[1], b_area, BLUE, "블루베리 (우리 데이터)", b),
    ]:
        clip = np.clip(area, 0, 3000)
        ax.hist(clip, bins=60, color=col, alpha=0.85, edgecolor="white", linewidth=0.3)
        ax.axvline(stat["area_median"], color=INK, ls="--", lw=1.3)
        ax.text(stat["area_median"] + 60, ax.get_ylim()[1] * 0.9,
                f"중앙값 {stat['area_median']:.0f}px\n(한 변 ≈ {stat['side_median']:.0f}px)",
                fontproperties=REG, fontsize=9, color=INK)
        ax.set_title(f"{title}", fontproperties=BLD, fontsize=13, color=col)
        ax.set_xlabel("개체 1개의 면적 (픽셀 수, 3000에서 절단)", fontproperties=REG, fontsize=10)
        ax.set_ylabel("개체 수", fontproperties=REG, fontsize=10)
        for lb in ax.get_xticklabels() + ax.get_yticklabels():
            lb.set_fontproperties(REG)
    fig.suptitle("개체 크기 분포 — MinneApple Figure 4 재현",
                 fontproperties=BLD, fontsize=15, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    for ext in ("pdf", "png"):
        fig.savefig(f"{ROOT}/semantic-segmentation/reports/figures/fig_object_size_hist.{ext}",
                    dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- 그림 2: 이미지당 개체 수 분포 ---
    fig, ax = plt.subplots(figsize=(8, 4))
    bins = np.arange(0, 200, 10)
    ax.hist(m_per, bins=bins, color=GREEN, alpha=0.6, label=f"MinneApple (평균 {m['obj_per_img_mean']:.1f})")
    ax.hist(b_per, bins=bins, color=BLUE, alpha=0.6, label=f"블루베리 (평균 {b['obj_per_img_mean']:.1f})")
    ax.set_xlabel("이미지 1장당 개체 수", fontproperties=REG, fontsize=11)
    ax.set_ylabel("이미지 수", fontproperties=REG, fontsize=11)
    ax.set_title("이미지 1장당 개체 수 — '종류는 하나, 개수는 많다'",
                 fontproperties=BLD, fontsize=13, color=INK)
    leg = ax.legend(prop=REG, fontsize=11)
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontproperties(REG)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{ROOT}/semantic-segmentation/reports/figures/fig_objects_per_image.{ext}",
                    dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("\n=== 요약 ===")
    for d in (m, b):
        print(f"{d['name']}: 이미지 {d['n_images']} / 개체 {d['n_objects']:,} / "
              f"장당 평균 {d['obj_per_img_mean']:.1f} / 면적중앙 {d['area_median']:.0f}px / "
              f"화면대비 {d['area_frac_median']*100:.4f}% / 전경 {d['fg_ratio']*100:.2f}%")
    print("\n저장: reports/figures/fig_object_size_hist.*, fig_objects_per_image.*")
    print("      output/object_size_stats.json")


if __name__ == "__main__":
    main()
