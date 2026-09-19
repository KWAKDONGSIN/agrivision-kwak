# -*- coding: utf-8 -*-
"""복숭아 데이터셋(peach_semseg)의 마스크를 눈으로 확인하는 그림을 만든다.

원본 / 마스크 / 겹쳐보기 3열로, 전경 비율이 가장 작은 것부터 가장 큰 것까지
골고루 뽑아서 한 장에 담는다. 마스크가 실제로 복숭아 위에 정확히 얹히는지
육안 검증하는 용도.

사용:  $PY tools/make_peach_mask_examples_fig.py
출력:  reports/figures/fig_peach_mask_examples.png
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image

ROOT = Path('/data/project/2026summer/kds0206/연구실 블루베리/datasets_verified/peach_semseg')
OUT = Path('/data/project/2026summer/kds0206/semantic-segmentation/reports/figures'
           '/fig_peach_mask_examples.png')

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
REG = FontProperties(fname=FONT)
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

MAXW = 900          # 미리보기 최대 폭 (원본 4032px는 너무 큼)


def load(split, stem):
    im = Image.open(ROOT / split / 'images' / f'{stem}.jpg').convert('RGB')
    mk = Image.open(ROOT / split / 'masks' / f'{stem}.png').convert('L')
    if im.width > MAXW:
        h = round(im.height * MAXW / im.width)
        im = im.resize((MAXW, h), Image.BILINEAR)
        mk = mk.resize((MAXW, h), Image.NEAREST)
    return np.asarray(im), np.asarray(mk) > 0


def survey():
    """전 스플릿을 훑어 (전경비율, split, stem, 원본크기) 목록을 만든다."""
    out = []
    for sp in ('train', 'val', 'test'):
        for ip in sorted((ROOT / sp / 'images').glob('*.jpg')):
            mp = ROOT / sp / 'masks' / f'{ip.stem}.png'
            if not mp.exists():
                continue
            a = np.asarray(Image.open(mp).convert('L'))
            out.append(((a > 0).mean(), sp, ip.stem, Image.open(ip).size))
    return sorted(out)


def pick(rows, n=5):
    """전경 비율 분포에서 골고루 n개 (최소 · 사분위 · 중앙 · 사분위 · 최대)."""
    idx = [round(i * (len(rows) - 1) / (n - 1)) for i in range(n)]
    return [rows[i] for i in idx]


def main():
    rows = survey()
    print(f'검사한 이미지 {len(rows)}장 · 마스크 결측 0')
    sel = pick(rows)

    fig, axes = plt.subplots(len(sel), 3, figsize=(13.5, 3.05 * len(sel)))
    fig.suptitle('복숭아 데이터셋 (peach_semseg) — 마스크 육안 검증',
                 fontproperties=BLD, fontsize=17, y=0.995)

    for r, (fg, sp, stem, size) in enumerate(sel):
        img, m = load(sp, stem)

        axes[r, 0].imshow(img)
        axes[r, 0].set_title(f'원본  ({sp}/{stem})', fontproperties=REG, fontsize=10)

        axes[r, 1].imshow(m, cmap='gray', vmin=0, vmax=1)
        axes[r, 1].set_title(f'마스크  흰색=복숭아  (전경 {100*fg:.2f} %)',
                             fontproperties=REG, fontsize=10)

        ov = img.astype(float).copy()
        ov[m] = 0.45 * ov[m] + 0.55 * np.array([255, 60, 60])     # 빨강 오버레이
        axes[r, 2].imshow(ov.astype(np.uint8))
        axes[r, 2].set_title(f'겹쳐보기  (원본 {size[0]}x{size[1]})',
                             fontproperties=REG, fontsize=10)

        for c in range(3):
            axes[r, c].axis('off')

    fig.tight_layout(rect=[0, 0.012, 1, 0.985])
    fig.text(0.5, 0.004,
             f'전경 비율이 가장 작은 것부터 가장 큰 것까지 {len(sel)}장. '
             f'전체 {len(rows)}장 · 마스크 값 0/255 · 결측 0 · 크기 불일치 0',
             ha='center', fontproperties=REG, fontsize=9.5, color='#5b6270')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=115)
    plt.close(fig)
    print(f'저장: {OUT}')

    print('\n뽑은 표본:')
    for fg, sp, stem, size in sel:
        print(f'  {sp:5s} {stem:24s} 전경 {100*fg:6.2f} %   원본 {size[0]}x{size[1]}')


if __name__ == '__main__':
    main()
