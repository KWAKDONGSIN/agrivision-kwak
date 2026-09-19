# -*- coding: utf-8 -*-
"""FruitSeg30 데이터셋 사진 갤러리를 대량으로 만든다 (발표 PPT / PDF 삽입용).

곽동신 님이 서버에서 이미지를 직접 열어보기 어려우므로, 데이터셋 사진을
"최대한 많이" 그림 파일로 뽑아 PPT·PDF에 그대로 붙일 수 있게 한다.

만드는 그림 (reports/figures/gallery/):
  gal_all30_orig.png      30개 과일 원본 한 장씩 (5x6)
  gal_all30_mask.png      30개 과일 정답 마스크 한 장씩
  gal_all30_overlay.png   30개 과일 겹쳐보기 한 장씩
  gal_triplet_p1..p6.png  과일 5종씩 x (원본/마스크/겹쳐보기) 상세
  gal_variety_p1..p4.png  같은 과일 여러 장 (촬영 다양성 확인용)

GPU를 쓰지 않는다. 예측 결과 갤러리는 make_fruitseg30_pred_gallery.py 참조.

사용:  $PY tools/make_fruitseg30_gallery_figs.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
DATASET = Path('/data/project/2026summer/kds0206/dataset_fruitseg30')
OUTDIR = REPO / 'reports' / 'figures' / 'gallery'

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
INK, MUTE = '#111827', '#6b7280'
FRUIT_RGB = np.array([255, 60, 60])          # 겹쳐보기에서 과일을 칠할 색(빨강)

# 파일명이 <클래스>__<번호>.jpg 라서 클래스를 파일명에서 얻는다
def class_of(p: Path) -> str:
    return p.stem.split('__')[0]


def load_pair(img_path: Path):
    """이미지와 짝 마스크를 읽어 (RGB배열, 0/1마스크)로 돌려준다."""
    mask_path = img_path.parent.parent / 'masks' / f'{img_path.stem}.png'
    im = np.array(Image.open(img_path).convert('RGB'))
    mk = np.array(Image.open(mask_path).convert('L'))
    if mk.shape[:2] != im.shape[:2]:                       # 혹시 모를 크기 차이 방어
        mk = np.array(Image.fromarray(mk).resize((im.shape[1], im.shape[0]), Image.NEAREST))
    return im, (mk > 0).astype(np.uint8)


def overlay(im, binm, alpha=0.45):
    ov = im.copy()
    ov[binm == 1] = ((1 - alpha) * ov[binm == 1] + alpha * FRUIT_RGB).astype(np.uint8)
    return ov


def ko(name: str) -> str:
    """파일명 클래스를 사람이 읽기 좋은 이름으로."""
    return name.replace('_', ' ')


def collect(split='train'):
    """{클래스: [이미지경로, ...]} (파일명 번호순)"""
    img_dir = DATASET / split / 'images'
    per = {}
    for p in sorted(img_dir.iterdir()):
        per.setdefault(class_of(p), []).append(p)
    for c in per:
        per[c].sort(key=lambda q: int(q.stem.split('__')[1]))
    return per


# ------------------------------------------------------- ① 30종 한 장씩 x 3종류
def fig_all30(per, kind, out: Path):
    """kind: 'orig' | 'mask' | 'overlay'"""
    classes = sorted(per)
    ncol, nrow = 5, 6
    fig, axes = plt.subplots(nrow, ncol, figsize=(11.0, 13.6))
    title = {'orig': 'FruitSeg30 — 과일 30종 원본 사진 (종류당 1장)',
             'mask': 'FruitSeg30 — 정답 마스크 (흰색 = 과일, 검은색 = 배경)',
             'overlay': 'FruitSeg30 — 원본 위에 정답을 빨갛게 겹쳐본 것'}[kind]
    for k, ax in enumerate(axes.ravel()):
        ax.axis('off')
        if k >= len(classes):
            continue
        c = classes[k]
        im, binm = load_pair(per[c][0])
        if kind == 'orig':
            ax.imshow(im)
        elif kind == 'mask':
            ax.imshow(binm * 255, cmap='gray', vmin=0, vmax=255)
        else:
            ax.imshow(overlay(im, binm))
        ax.set_title(f'{k + 1}. {ko(c)}', fontproperties=REG, fontsize=8.5, color=INK, pad=3)
    fig.suptitle(title, fontproperties=BLD, fontsize=15, color=INK, y=0.985)
    fig.tight_layout(rect=[0, 0.005, 1, 0.965])
    fig.savefig(out, dpi=115)
    plt.close(fig)
    print(f'[fig] {out}')


# ------------------------------------------- ② 5종씩 상세 (원본/마스크/겹쳐보기)
def fig_triplets(per, out_prefix: Path, per_page=5):
    classes = sorted(per)
    pages = [classes[i:i + per_page] for i in range(0, len(classes), per_page)]
    for pi, chunk in enumerate(pages, 1):
        fig, axes = plt.subplots(len(chunk), 3, figsize=(8.4, 2.75 * len(chunk)))
        axes = np.atleast_2d(axes)
        for r, c in enumerate(chunk):
            im, binm = load_pair(per[c][0])
            fg = binm.mean() * 100
            for col, (arr, cm) in enumerate([(im, None), (binm * 255, 'gray'), (overlay(im, binm), None)]):
                ax = axes[r, col]
                ax.imshow(arr, cmap=cm, vmin=0 if cm else None, vmax=255 if cm else None)
                ax.axis('off')
                if r == 0:
                    ax.set_title(['① 원본 사진', '② 정답 마스크', '③ 겹쳐보기'][col],
                                 fontproperties=BLD, fontsize=11, color=INK, pad=6)
            axes[r, 0].text(-0.04, 0.5, f'{ko(c)}\n(과일 {fg:.0f}%)', transform=axes[r, 0].transAxes,
                            rotation=90, va='center', ha='center',
                            fontproperties=REG, fontsize=8.5, color=MUTE)
        fig.suptitle(f'FruitSeg30 상세 예시 ({pi}/{len(pages)}) — 사람이 손으로 칠한 정답이 ②입니다',
                     fontproperties=BLD, fontsize=13, color=INK)
        fig.tight_layout(rect=[0.015, 0, 1, 0.955])
        out = Path(f'{out_prefix}_p{pi}.png')
        fig.savefig(out, dpi=115)
        plt.close(fig)
        print(f'[fig] {out}')
    return len(pages)


# ----------------------------------------- ③ 같은 과일 여러 장 (촬영 다양성 확인)
def fig_variety(per, out_prefix: Path, classes_per_page=3, shots=6):
    """사진마다 배경·개수·조명이 다르다는 걸 보여준다."""
    # 장수가 많은 클래스를 우선 (다양성이 잘 보임)
    ranked = sorted(per, key=lambda c: -len(per[c]))[:12]
    ranked = sorted(ranked)
    pages = [ranked[i:i + classes_per_page] for i in range(0, len(ranked), classes_per_page)]
    for pi, chunk in enumerate(pages, 1):
        fig, axes = plt.subplots(len(chunk) * 2, shots, figsize=(2.0 * shots, 2.15 * len(chunk) * 2))
        axes = np.atleast_2d(axes)
        for r, c in enumerate(chunk):
            files = per[c]
            idx = [int(i * (len(files) - 1) / max(shots - 1, 1)) for i in range(shots)]
            for j, fi in enumerate(idx):
                im, binm = load_pair(files[fi])
                axes[2 * r, j].imshow(im)
                axes[2 * r + 1, j].imshow(overlay(im, binm))
                for rr in (2 * r, 2 * r + 1):
                    axes[rr, j].axis('off')
            axes[2 * r, 0].text(-0.06, 0.5, f'{ko(c)}\n원본', transform=axes[2 * r, 0].transAxes,
                                rotation=90, va='center', ha='center',
                                fontproperties=BLD, fontsize=8.5, color=INK)
            axes[2 * r + 1, 0].text(-0.06, 0.5, '정답 겹침', transform=axes[2 * r + 1, 0].transAxes,
                                    rotation=90, va='center', ha='center',
                                    fontproperties=REG, fontsize=8.5, color=MUTE)
        fig.suptitle(f'같은 과일도 사진마다 다릅니다 ({pi}/{len(pages)}) — 배경·개수·조명·각도',
                     fontproperties=BLD, fontsize=13, color=INK)
        fig.tight_layout(rect=[0.02, 0, 1, 0.955])
        out = Path(f'{out_prefix}_p{pi}.png')
        fig.savefig(out, dpi=105)
        plt.close(fig)
        print(f'[fig] {out}')
    return len(pages)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    per = collect('train')
    print(f'[info] 클래스 {len(per)}개, 학습 이미지 {sum(len(v) for v in per.values())}장')

    for kind in ('orig', 'mask', 'overlay'):
        fig_all30(per, kind, OUTDIR / f'gal_all30_{kind}.png')
    n_tri = fig_triplets(per, OUTDIR / 'gal_triplet')
    n_var = fig_variety(per, OUTDIR / 'gal_variety')
    print(f'[done] 30종그림 3장 + 상세 {n_tri}장 + 다양성 {n_var}장 → {OUTDIR}')


if __name__ == '__main__':
    main()
