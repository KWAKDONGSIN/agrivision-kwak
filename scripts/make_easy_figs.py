# -*- coding: utf-8 -*-
"""「아주 쉬운 설명서」 전용 그림을 만든다.

기존 reports/figures/textbook/ 의 개념 그림이 '네모와 화살표'로 설명한 것을
**우리 서버의 진짜 사진·진짜 예측·진짜 숫자**로 다시 그린 판이다.

만드는 것 (reports/figures/easy/):
  eg_what_we_do.png     이 연구가 하는 일 한 장 (원본 → 모델 → 예측)
  eg_pixel_grid.png     사진을 확대해 픽셀 숫자(RGB)와 마스크 숫자(0/1)를 나란히
  eg_journey.png        사진 한 장이 겪는 여정 6단계
  eg_prob_threshold.png 모델이 뱉는 '확률'과 0.5로 자르는 순간 (GPU 추론 1장)
  eg_iou_real.png       진짜 예측으로 IoU 손계산 (픽셀 수까지 표시)
  eg_confusion.png      TP/FP/FN/TN 2x2 + IoU/Dice/정밀도/재현율 한꺼번에 계산
  eg_batch_math.png     1,383장 → 692 iteration → 200에폭이 무슨 뜻인가
  eg_three_datasets.png 블루베리 / MinneApple / FruitSeg30 난이도 비교
  eg_loss_annotated.png 진짜 loss 곡선에 '여기가 best' 주석
  eg_good_bad.png       잘 맞힌 사진 vs 못 맞힌 사진

사용:  CUDA_VISIBLE_DEVICES=<빈GPU> $PY tools/make_easy_figs.py
       (GPU가 없거나 실패하면 eg_prob_threshold.png만 건너뛴다)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from PIL import Image

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
ROOT = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO))

OUT = REPO / 'reports/figures/easy'
OUT.mkdir(parents=True, exist_ok=True)
CACHE = REPO / 'output/_fruitseg30_pred_cache'
FS = ROOT / 'dataset_fruitseg30'
BB = ROOT / 'dataset_6fold/cv1'
MA = ROOT / 'dataset_minneapple'

FD = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FD + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FD + 'NotoSansCJK-Bold.ttc')

INK, MUTE = '#111827', '#6b7280'
BLUE, GOOD, BAD, WARN = '#1c5cab', '#0a7d33', '#b23b3b', '#8a6d00'
GREEN_A = np.array([40, 190, 90])
RED_A = np.array([230, 60, 60])
YEL_A = np.array([245, 190, 40])


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  저장: {p.relative_to(REPO)}')


def t(ax, x, y, s, size=11, bold=False, color=INK, ha='center', va='center', **kw):
    ax.text(x, y, s, fontproperties=BLD if bold else REG, fontsize=size,
            color=color, ha=ha, va=va, transform=ax.transAxes, **kw)


def blank(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def arrow(fig, x0, x1, y, label='', color=BLUE):
    fig.patches.append(mpatches.FancyArrow(
        x0, y, x1 - x0, 0, width=0.006, head_width=0.022, head_length=0.012,
        transform=fig.transFigure, color=color, length_includes_head=True))
    if label:
        fig.text((x0 + x1) / 2, y + 0.035, label, fontproperties=BLD, fontsize=10.5,
                 color=color, ha='center')


def load_fs(name):
    """FruitSeg30 test 한 장 → (원본 RGB, 정답 bool, 예측 bool)"""
    stem = Path(name).stem
    im = np.array(Image.open(FS / 'test/images' / name).convert('RGB'))
    gt = np.array(Image.open(FS / 'test/masks' / f'{stem}.png').convert('L')) > 0
    pr = np.load(CACHE / f'{stem}.npy').astype(bool)
    return im, gt, pr


def records():
    d = json.loads((REPO / 'output/fruitseg30_per_image_iou.json').read_text())
    return d['per_image'], d


def diff_map(im, gt, pr):
    ov = im.copy()
    for m, c in ((gt & pr, GREEN_A), (gt & ~pr, RED_A), (~gt & pr, YEL_A)):
        ov[m] = (0.35 * ov[m] + 0.65 * c).astype(np.uint8)
    return ov


# ────────────────────────────────────────────────────── ① 우리가 하는 일
def fig_what_we_do(rec):
    r = [x for x in rec if 0.93 < x['iou'] < 0.97][len([x for x in rec if 0.93 < x['iou'] < 0.97]) // 2]
    im, gt, pr = load_fs(r['file'])
    # A4 본문 폭(약 6.9인치)으로 줄여 실릴 것을 감안해 그림을 작게 만든다.
    # (그림이 넓을수록 인쇄됐을 때 글씨가 작아진다)
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 4.4))
    titles = ['① 우리가 주는 것 — 사진',
              '② 사람이 칠해 준 정답 — 마스크',
              '③ 컴퓨터가 그린 답 — 예측']
    subs = ['그냥 카메라로 찍은 사진입니다',
            '과일이면 흰색, 아니면 검은색\n(사람이 직접 칠했습니다)',
            f'학습이 끝난 모델이 그린 것\n이 사진 점수 IoU = {r["iou"]:.3f}']
    ov = im.copy(); ov[pr] = (0.45 * ov[pr] + 0.55 * GREEN_A).astype(np.uint8)
    for ax, img, ti, su, c in zip(axes, [im, gt.astype(np.uint8) * 255, ov],
                                  titles, subs, [INK, INK, GOOD]):
        ax.imshow(img, cmap='gray' if img.ndim == 2 else None)
        blank(ax)
        ax.set_title(ti, fontproperties=BLD, fontsize=13, color=c, pad=12)
        t(ax, 0.5, -0.09, su, size=10.5, color=MUTE, va='top')
    fig.text(0.5, 0.005, f'실제 test 사진 {r["file"]} · 학습된 UPerNet + ResNet-50 이 그린 진짜 결과입니다',
             fontproperties=REG, fontsize=10, color=MUTE, ha='center')
    fig.subplots_adjust(bottom=0.16)
    save(fig, 'eg_what_we_do.png')


# ────────────────────────────────────────────── ② 사진은 숫자다 (픽셀 격자)
def fig_pixel_grid(rec):
    # 밝고 경계가 뚜렷한 사진을 고른다 (어두운 사진은 확대해도 숫자가 다 비슷해 설명이 안 됨)
    cand = [x for x in rec if x['cls'].startswith('Apple') and x['iou'] > 0.97]
    r = cand[0] if cand else sorted(rec, key=lambda x: -x['iou'])[3]
    im, gt, _ = load_fs(r['file'])
    ys, xs = np.where(gt)
    cy = int(ys.mean())
    row = gt[cy]                              # 과일 한가운데 높이의 가로줄
    edge = int(np.argmax(row))                # 그 줄에서 배경→과일로 바뀌는 첫 지점
    x0 = max(0, edge - 2); y0 = max(0, cy - 3)
    K = 6
    patch = im[y0:y0 + K, x0:x0 + K]
    pm = gt[y0:y0 + K, x0:x0 + K].astype(int)

    # 2×2 구성 (A4 세로 페이지에 크게 실리도록)
    fig = plt.figure(figsize=(9.2, 8.8))
    ax0 = fig.add_axes([0.06, 0.545, 0.38, 0.36])
    ax0.imshow(im); blank(ax0)
    # 6×6칸은 512×512 안에서 점이나 다름없어 안 보인다 → 안내용 큰 네모를 같이 그린다
    ax0.add_patch(plt.Rectangle((x0 - 30, y0 - 30), 66, 66, fill=False, ec='#e11d48',
                                lw=1.2, ls='--'))
    ax0.add_patch(plt.Rectangle((x0, y0), K, K, fill=False, ec='#e11d48', lw=2.5))
    ax0.set_title('① 사진 한 장 (512 × 512)', fontproperties=BLD, fontsize=13, pad=8)
    t(ax0, 0.5, -0.06, f'빨간 점 = 확대할 {K} × {K} 칸\n(과일 가장자리를 골랐습니다)',
      size=10.5, color='#e11d48', va='top')

    ax1 = fig.add_axes([0.56, 0.545, 0.38, 0.36])
    ax1.imshow(patch, interpolation='nearest'); blank(ax1)
    for i in range(K):
        for j in range(K):
            v = patch[i, j]
            ax1.text(j, i, f'{v[0]}\n{v[1]}\n{v[2]}', ha='center', va='center',
                     fontsize=8.5, fontproperties=REG, linespacing=1.05,
                     color='white' if v.mean() < 120 else 'black')
    ax1.set_title('② 확대하면 = 숫자', fontproperties=BLD, fontsize=13, pad=8)
    t(ax1, 0.5, -0.06, '칸마다 빨강 · 초록 · 파랑 값\n(각각 0 ~ 255)',
      size=10.5, color=MUTE, va='top')

    ax2 = fig.add_axes([0.06, 0.075, 0.38, 0.36])
    ax2.imshow(pm, cmap='gray', vmin=0, vmax=1, interpolation='nearest')
    blank(ax2)
    for s in ax2.spines.values():
        s.set_visible(True); s.set_color('#94a3b8')
    for i in range(K):
        for j in range(K):
            ax2.text(j, i, str(pm[i, j]), ha='center', va='center', fontsize=15,
                     fontproperties=BLD, color='#e11d48' if pm[i, j] else '#22d3ee')
    ax2.set_title('③ 같은 자리의 정답 = 0 또는 1', fontproperties=BLD, fontsize=13, pad=8)
    t(ax2, 0.5, -0.06, '흰 칸 = 1(과일) · 검은 칸 = 0(배경)', size=10.5, color=INK, va='top')

    ax3 = fig.add_axes([0.56, 0.075, 0.38, 0.36]); blank(ax3)
    ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)
    ax3.add_patch(plt.Rectangle((0, 0), 1, 1, fc='#f8fafc', ec='#cbd5e1'))
    t(ax3, 0.5, 0.90, '정리하면', size=13, bold=True)
    for i, (lab, val) in enumerate([
            ('사진 한 장의 숫자 개수', '512 × 512 × 3 = 786,432개'),
            ('정답 한 장의 숫자 개수', '512 × 512 = 262,144개'),
            ('정답에 들어가는 값', '0 또는 1, 두 가지뿐'),
            ('모델이 하는 일', '왼쪽 표를 보고\n오른쪽 표를 만들어 내는 것')]):
        t(ax3, 0.5, 0.74 - i * 0.185, lab, size=10.5, color=MUTE)
        t(ax3, 0.5, 0.665 - i * 0.185, val, size=11.5, bold=True, color=INK)
    save(fig, 'eg_pixel_grid.png')


# ─────────────────────────────────────────────── ③ 사진 한 장의 여정
def fig_journey(rec):
    r = [x for x in rec if x['iou'] > 0.97][0]
    im, gt, pr = load_fs(r['file'])
    small = np.array(Image.fromarray(im).resize((160, 160)))
    aug = np.array(Image.fromarray(small[:, ::-1]).rotate(28, resample=Image.BILINEAR))
    ovl = im.copy(); ovl[pr] = (0.45 * ovl[pr] + 0.55 * GREEN_A).astype(np.uint8)
    px = small[80, 80].astype(float)                      # 가운데 픽셀 하나
    nz = (px / 255 - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])

    panels = [
        ('img', small, '1. 원본 사진', '512×512 로 맞춤 (일부는\n4000×3000 이라 줄였음)'),
        ('num', None, '2. 숫자로 바꾸기', '0~255 를 평균 0 근처로\n(정규화 NORMALIZE)'),
        ('img', aug, '3. 흔들어 주기', '좌우뒤집기 · 회전 · 자르기\n(증강 AUGMENTATION)'),
        ('box', None, '4. 모델 통과', 'ResNet-50 이 보고\nUPerNet 이 그림'),
        ('img', gt.astype(np.uint8) * 255, '5. 정답과 비교', '틀린 만큼이 loss.\n그만큼 모델을 고침'),
        ('img', ovl, '6. 완성된 예측', f'200에폭 반복 후\nIoU {r["iou"]:.3f}'),
    ]
    # 2줄 × 3칸 (A4 세로 페이지에 크게 실리도록)
    fig = plt.figure(figsize=(9.6, 7.6))
    W, H = 0.26, 0.335
    xs = [0.045 + (k % 3) * 0.325 for k in range(6)]
    ys = [0.545 if k < 3 else 0.075 for k in range(6)]
    for x, Y, (kind, img, ti, su) in zip(xs, ys, panels):
        ax = fig.add_axes([x, Y, W, H]); blank(ax)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        if kind == 'img':
            ax.imshow(img, cmap='gray' if img.ndim == 2 else None,
                      extent=(0, 1, 0, 1), aspect='auto')
        elif kind == 'box':
            ax.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fc='#eef2ff', ec=BLUE, lw=2))
            t(ax, 0.5, 0.66, '모델', size=18, bold=True, color=BLUE)
            t(ax, 0.5, 0.38, '숫자 수천만 개로\n이루어진 함수', size=11, color=BLUE)
        else:
            ax.add_patch(plt.Rectangle((0.02, 0.02), 0.96, 0.96, fc='#f8fafc', ec='#cbd5e1'))
            t(ax, 0.5, 0.86, '가운데 픽셀 한 개', size=10, color=MUTE)
            t(ax, 0.5, 0.68, f'R {px[0]:.0f}  G {px[1]:.0f}  B {px[2]:.0f}', size=12, bold=True)
            t(ax, 0.5, 0.52, '↓', size=16, bold=True, color=BLUE)
            t(ax, 0.5, 0.36, f'{nz[0]:+.2f}  {nz[1]:+.2f}  {nz[2]:+.2f}',
              size=12, bold=True, color=BLUE)
            t(ax, 0.5, 0.15, '값의 크기를 맞춰 줘야\n학습이 잘 됩니다', size=9.5, color=MUTE)
        fig.text(x + W / 2, Y + H + 0.022, ti, fontproperties=BLD, fontsize=12.5,
                 ha='center', va='bottom')
        fig.text(x + W / 2, Y - 0.014, su, fontproperties=REG, fontsize=10,
                 color=MUTE, ha='center', va='top')
    for k in range(6):
        if k in (2, 5):
            continue
        fig.text(xs[k] + W + 0.033, ys[k] + H / 2, '→', fontproperties=BLD, fontsize=22,
                 color=BLUE, ha='center', va='center')
    save(fig, 'eg_journey.png')


# ──────────────────────────────── ④ 확률과 0.5 (GPU 추론 1장)
def fig_prob_threshold(rec):
    try:
        import torch
        import yaml
        from torch.nn import functional as F
        from semseg.models import UPerNet                       # noqa
        from semseg.augmentations import get_eval_augmentation  # noqa
        from semseg.datasets import BlueberryDataset            # noqa

        cfg = yaml.safe_load((REPO / 'configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml').read_text())
        dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        tr = get_eval_augmentation(cfg['TEST']['IMAGE_SIZE'],
                                   seg_fill=cfg['DATASET']['IGNORE_LABEL'], augment=False)
        ds = BlueberryDataset(cfg['DATASET']['ROOT'], 'test', tr)
        model = UPerNet(cfg['MODEL']['BACKBONE'], 1)
        model.load_state_dict(torch.load(cfg['TEST']['MODEL_PATH'], map_location='cpu'))
        model = model.to(dev).eval()

        target = sorted(rec, key=lambda x: x['iou'])[len(rec) // 3]['file']
        idx = [i for i in range(len(ds)) if ds.files[i].name == target][0]
        image, label = ds[idx]
        with torch.no_grad():
            lo = model(image.unsqueeze(0).to(dev))
            if lo.shape[-2:] != label.shape[-2:]:
                lo = F.interpolate(lo, size=label.shape[-2:], mode='bilinear', align_corners=False)
            prob = torch.sigmoid(lo).squeeze().cpu().numpy()
    except Exception as e:                                     # noqa: BLE001
        print(f'  [건너뜀] eg_prob_threshold.png — GPU 추론 실패: {e}')
        return

    im, gt, _ = load_fs(target)
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 8.6))   # A4 세로용 2×2
    axes = axes.ravel()
    axes[0].imshow(im); axes[0].set_title('① 원본 사진', fontproperties=BLD, fontsize=13, pad=10)
    h = axes[1].imshow(prob, cmap='inferno', vmin=0, vmax=1)
    axes[1].set_title('② 모델이 뱉은 것 = 확률 (0~1)', fontproperties=BLD, fontsize=13, pad=10)
    fig.colorbar(h, ax=axes[1], fraction=0.046)
    axes[2].imshow(prob >= 0.5, cmap='gray')
    axes[2].set_title('③ 0.5 이상만 남기면 = 예측', fontproperties=BLD, fontsize=13,
                      pad=10, color=GOOD)
    axes[3].imshow(gt, cmap='gray')
    axes[3].set_title('④ 사람이 칠한 정답', fontproperties=BLD, fontsize=13, pad=10)
    for ax in axes:
        blank(ax)
    hi = float((prob > 0.99).mean() * 100); lo_ = float((prob < 0.01).mean() * 100)
    mid = float(((prob >= 0.4) & (prob <= 0.6)).mean() * 100)
    fig.text(0.5, 0.025,
             f'이 사진에서 확률 0.99 이상인 칸 {hi:.1f}% · 0.01 이하 {lo_:.1f}% ·\n'
             f'애매한 0.4~0.6 은 {mid:.2f}% 뿐 → 모델이 거의 확신하고 있습니다',
             fontproperties=REG, fontsize=11, color=MUTE, ha='center')
    fig.subplots_adjust(bottom=0.10, top=0.95, hspace=0.12)
    save(fig, 'eg_prob_threshold.png')


# ───────────────────────────────────── ⑤ 진짜 예측으로 IoU 손계산
def fig_iou_real(rec):
    r = sorted(rec, key=lambda x: abs(x['iou'] - 0.90))[0]
    im, gt, pr = load_fs(r['file'])
    tp = int((gt & pr).sum()); fp = int((~gt & pr).sum()); fn = int((gt & ~pr).sum())
    union = tp + fp + fn
    # 위: 사진 4장 / 아래: 계산 과정 (A4 세로에 맞춘 2단 구성)
    fig = plt.figure(figsize=(9.6, 7.4))
    for k, (img, ti, cl) in enumerate([
            (im, '원본', INK),
            (gt.astype(np.uint8) * 255, f'정답 = 흰 칸 {tp + fn:,}개', INK),
            (pr.astype(np.uint8) * 255, f'예측 = 흰 칸 {tp + fp:,}개', BLUE),
            (diff_map(im, gt, pr), '겹쳐보기', GOOD)]):
        # 정사각형 사진이 축 안에서 위아래로 뜨지 않도록 높이를 폭에 맞춘다
        ax = fig.add_axes([0.035 + k * 0.238, 0.615, 0.215, 0.215 * 9.6 / 7.4])
        ax.imshow(img, cmap='gray' if img.ndim == 2 else None); blank(ax)
        ax.set_title(ti, fontproperties=BLD, fontsize=11.5, color=cl, pad=8)
    ax = fig.add_axes([0.035, 0.045, 0.93, 0.52]); blank(ax)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, fc='#f8fafc', ec='#cbd5e1'))
    t(ax, 0.5, 0.92, 'IoU 를 손으로 계산하면', size=14, bold=True)
    rows = [('초록 — 맞게 찾음 (TP)', f'{tp:,} 칸', GOOD),
            ('빨강 — 과일인데 놓침 (FN)', f'{fn:,} 칸', BAD),
            ('노랑 — 배경인데 과일이랬음 (FP)', f'{fp:,} 칸', WARN)]
    for i, (lab, v, c) in enumerate(rows):
        t(ax, 0.06, 0.77 - i * 0.10, lab, size=11.5, color=c, ha='left')
        t(ax, 0.55, 0.77 - i * 0.10, v, size=12, bold=True, color=c, ha='right')
    t(ax, 0.78, 0.72, 'IoU  =  겹친 칸', size=11.5, color=MUTE)
    t(ax, 0.78, 0.64, '÷  둘 중 하나라도 칠한 칸', size=11.5, color=MUTE)
    t(ax, 0.5, 0.40, f'{tp:,}  ÷  ({tp:,} + {fn:,} + {fp:,})  =  {tp:,} ÷ {union:,}', size=12)
    t(ax, 0.5, 0.24, f'=  {tp / union:.4f}', size=22, bold=True, color=GOOD)
    t(ax, 0.5, 0.08, f'{r["file"]}  ·  IoU 가 딱 0.90 인 사진을 골랐습니다 (390장 평균은 0.964)',
      size=10, color=MUTE)
    save(fig, 'eg_iou_real.png')
    return r, tp, fp, fn


# ────────────────────────────── ⑥ 2×2 혼동행렬 + 지표 4개 한꺼번에
def fig_confusion(r, tp, fp, fn):
    total = 512 * 512
    tn = total - tp - fp - fn
    prec, rec_ = tp / (tp + fp), tp / (tp + fn)
    iou, dice = tp / (tp + fp + fn), 2 * tp / (2 * tp + fp + fn)
    acc = (tp + tn) / total
    # 위: 2×2 표 / 아래: 그 숫자로 만드는 점수 5개 (A4 세로 2단)
    fig = plt.figure(figsize=(9.6, 9.0))
    ax = fig.add_axes([0.06, 0.55, 0.88, 0.41]); blank(ax)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    t(ax, 0.5, 0.97, '칸 한 개마다 네 가지 중 하나입니다', size=14, bold=True)
    t(ax, 0.38, 0.86, '모델이 「과일」', size=11.5, bold=True, color=BLUE)
    t(ax, 0.76, 0.86, '모델이 「배경」', size=11.5, bold=True, color=BLUE)
    t(ax, 0.10, 0.63, '정답이\n「과일」', size=11.5, bold=True)
    t(ax, 0.10, 0.27, '정답이\n「배경」', size=11.5, bold=True)
    cells = [(0.22, 0.47, GREEN_A, 'TP 맞게 찾음', tp),
             (0.60, 0.47, RED_A, 'FN 놓침', fn),
             (0.22, 0.11, YEL_A, 'FP 헛다리', fp),
             (0.60, 0.11, np.array([200, 200, 205]), 'TN 배경 맞음', tn)]
    for x, y, c, lab, v in cells:
        ax.add_patch(plt.Rectangle((x, y), 0.32, 0.32, fc=np.array(c) / 255 * 0.35 + 0.65,
                                   ec='#94a3b8', transform=ax.transAxes))
        t(ax, x + 0.16, y + 0.21, lab, size=11.5, bold=True)
        t(ax, x + 0.16, y + 0.10, f'{v:,} 칸', size=14, bold=True, color=INK)

    ax2 = fig.add_axes([0.06, 0.045, 0.88, 0.46]); blank(ax2)
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
    ax2.add_patch(plt.Rectangle((0, 0), 1, 1, fc='#f8fafc', ec='#cbd5e1'))
    t(ax2, 0.5, 0.95, '같은 숫자로 점수 다섯 개를 다 만들 수 있습니다', size=13.5, bold=True)
    items = [('정확도 (Accuracy)', f'(TP+TN) ÷ 전체 = {acc:.4f}',
              '← 배경까지 세서 항상 높게 나옵니다. 그래서 안 씁니다', BAD),
             ('정밀도 (Precision)', f'TP ÷ (TP+FP) = {prec:.4f}',
              '과일이라 한 것 중 진짜 과일 비율', INK),
             ('재현율 (Recall)', f'TP ÷ (TP+FN) = {rec_:.4f}',
              '진짜 과일 중 찾아낸 비율', INK),
             ('IoU', f'TP ÷ (TP+FP+FN) = {iou:.4f}',
              '우리 대표 점수. 가장 엄격합니다', GOOD),
             ('Dice (F1)', f'2TP ÷ (2TP+FP+FN) = {dice:.4f}',
              'IoU 와 형제. 항상 IoU 보다 큽니다', GOOD)]
    for i, (n, f_, ex, c) in enumerate(items):
        y = 0.82 - i * 0.165
        t(ax2, 0.04, y, n, size=12, bold=True, color=c, ha='left')
        t(ax2, 0.44, y, f_, size=11.5, color=c, ha='left')
        t(ax2, 0.04, y - 0.06, ex, size=10, color=MUTE, ha='left')
    fig.text(0.5, 0.008, f'{r["file"]} 한 장의 실제 숫자입니다 (512×512 = 262,144칸)',
             fontproperties=REG, fontsize=10, color=MUTE, ha='center')
    save(fig, 'eg_confusion.png')


# ─────────────────────────────── ⑦ 에폭·배치·이터레이션을 진짜 숫자로
def fig_batch_math():
    n_train, bs, accum, epochs = 1383, 2, 4, 200
    it = n_train // bs
    upd = it // accum
    fig = plt.figure(figsize=(9.6, 5.4))
    ax = fig.add_axes([0, 0, 1, 1]); blank(ax); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    t(ax, 0.5, 0.95, 'yaml 의 숫자 세 줄이 실제로 무슨 뜻인가', size=15, bold=True)
    boxes = [
        (0.04, 'BATCH_SIZE : 2', f'사진 {bs}장씩 묶어서 봅니다',
         f'{n_train:,}장 ÷ {bs} = {it:,}번', '한 에폭에 이만큼 반복', BLUE),
        (0.37, 'ACCUM_STEPS : 4', f'{accum}번 모아서 한 번 고칩니다',
         f'{it:,} ÷ {accum} = {upd:,}번', '실제로 모델이 바뀌는 횟수', WARN),
        (0.70, 'EPOCHS : 200', '전체 사진을 200바퀴 봅니다',
         f'{it:,} × {epochs} = {it * epochs:,}번', '학습 내내 반복한 총 횟수', GOOD)]
    for x, title, sub, calc, calcsub, c in boxes:
        ax.add_patch(plt.Rectangle((x, 0.34), 0.26, 0.5, fc='#f8fafc', ec=c, lw=2))
        t(ax, x + 0.13, 0.78, title, size=13, bold=True, color=c)
        t(ax, x + 0.13, 0.70, sub, size=10.5, color=INK)
        ax.add_patch(plt.Rectangle((x + 0.02, 0.46), 0.22, 0.14, fc='white', ec='#cbd5e1'))
        t(ax, x + 0.13, 0.545, calc, size=12, bold=True, color=c)
        t(ax, x + 0.13, 0.485, calcsub, size=9, color=MUTE)
        t(ax, x + 0.13, 0.395, '↓', size=14, bold=True, color=c)
    t(ax, 0.5, 0.26, f'배치 2장은 왜 이렇게 작은가?  →  V100 메모리를 아끼려고.\n'
                     f'대신 ACCUM 4로 모아서 "사실상 {bs * accum}장"처럼 학습합니다.',
      size=11.5)
    t(ax, 0.5, 0.13, '실측: 한 에폭 58.5초 × 200에폭 = 3시간 42분.  '
                     'Peak VRAM 463.77MB (V100 32GB의 1.4%)', size=11.5, color=GOOD)
    t(ax, 0.5, 0.04, '숫자는 내 config 와 logs/fruitseg30_pipeline.log 실측값입니다',
      size=9.5, color=MUTE)
    save(fig, 'eg_batch_math.png')


# ───────────────────────────────── ⑧ 데이터셋 3개 난이도 비교
def _first(d, n=1):
    fs = sorted([p for p in d.iterdir()
                 if p.suffix.lower() in ('.jpg', '.png', '.jpeg', '.bmp')])
    return fs[:n]


def fig_three_datasets():
    """세 데이터셋의 난이도 비교.

    ⚠️ 점수는 '무엇으로 잰 값인가'가 셋 다 다르다. 그래서 칸마다 명시한다.
       (블루베리=6폴드 val 평균 / MinneApple=백본이 ConvNeXt-T / FruitSeg30=test)
    """
    picks = []
    for base, name, fgr, nobj, score, how in (
            (BB, '블루베리 (우리 연구 주력)', 2.4, '약 43개', 0.798,
             'UPerNet+ResNet-50\n6폴드 val 평균'),
            (MA, 'MinneApple (사과밭)', 3.1, '약 42개', 0.687,
             'UPerNet+ConvNeXt-T\ntest (백본이 다름!)'),
            (FS, 'FruitSeg30 (내 담당)', 35.8, '1개', 0.962,
             'UPerNet+ResNet-50\ntest')):
        try:
            ip = _first(base / 'test/images')[0]
            if base is FS:
                cand = FS / 'test/images/Watermelon__1.jpg'
                ip = cand if cand.exists() else ip
            mp = base / 'test/masks' / f'{ip.stem}.png'
            picks.append((name, ip, mp if mp.exists() else None, fgr, nobj, score, how))
        except Exception as e:                                 # noqa: BLE001
            print(f'  [건너뜀] {name}: {e}')

    n = len(picks)
    fig, axes = plt.subplots(2, n, figsize=(4.6 * n, 9.2))
    if n == 1:
        axes = axes.reshape(2, 1)
    for k, (name, ip, mp, fgr, nobj, score, how) in enumerate(picks):
        im = np.array(Image.open(ip).convert('RGB').resize((420, 420)))
        axes[0, k].imshow(im); blank(axes[0, k])
        axes[0, k].set_title(name, fontproperties=BLD, fontsize=13.5, pad=10,
                             color=GOOD if '내 담당' in name else INK)
        if mp and Path(mp).exists():
            m = np.array(Image.open(mp).convert('L').resize((420, 420), Image.NEAREST)) > 0
            axes[1, k].imshow(m, cmap='gray')
        else:
            axes[1, k].text(0.5, 0.5, '마스크 없음', ha='center', va='center',
                            fontproperties=REG, fontsize=12, color=MUTE)
        blank(axes[1, k])
        t(axes[1, k], 0.5, -0.04,
          f'화면에서 과일이 차지하는 비율 {fgr}%\n한 장에 열매 {nobj}',
          size=11.5, color=INK, va='top')
        t(axes[1, k], 0.5, -0.155, f'전경 IoU {score:.3f}', size=14, bold=True,
          color=GOOD if '내 담당' in name else INK, va='top')
        t(axes[1, k], 0.5, -0.215, how, size=9, color=BAD, va='top')
    fig.text(0.5, 0.035,
             '과일이 클수록·적을수록 점수가 높습니다. 모델이 좋아서가 아니라 '
             '"문제가 쉬워서"입니다.',
             fontproperties=BLD, fontsize=12.5, color=INK, ha='center')
    fig.text(0.5, 0.008,
             '주의 — 세 숫자는 잰 방법이 다릅니다(빨간 글씨). 그대로 나란히 놓고 '
             '"어느 모델이 낫다"고 말하면 안 됩니다.',
             fontproperties=REG, fontsize=10.5, color=BAD, ha='center')
    fig.subplots_adjust(bottom=0.2, hspace=0.05)
    save(fig, 'eg_three_datasets.png')


# ───────────────────────────────── ⑨ 진짜 loss 곡선에 주석
def fig_loss_annotated():
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    d = REPO / 'output/fruitseg_runs/upernet_resnet_50_bcedice_200ep/logs'
    ea = EventAccumulator(str(d), size_guidance={'scalars': 0}); ea.Reload()

    def sc(tag):
        # TensorBoard step 은 0부터(train.py:289 `for epoch in range(epochs)`),
        # 화면 로그는 epoch+1 로 찍힌다(train.py:304). 사람이 읽는 쪽에 맞춰 +1 한다.
        e = ea.Scalars(tag)
        return np.array([x.step + 1 for x in e]), np.array([x.value for x in e])
    ts, tv = sc('train/loss')
    vs, vv = sc('val/loss')
    bi = int(np.argmin(vv)); be, bl = int(vs[bi]), float(vv[bi])
    ivs, ivv = sc('val/fg_IoU')

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.plot(ts, tv, color='#94a3b8', lw=1.4, label='train loss (배우는 중 성적)')
    ax.plot(vs, vv, color=BLUE, lw=2.2, label='val loss (안 본 사진 성적) ← 이걸 봅니다')
    ax.scatter([be], [bl], s=160, color=BAD, zorder=5)
    ax.annotate(f'여기가 best\n{be}에폭 · val loss {bl:.4f}\n→ 이때의 모델을 저장해 씁니다',
                xy=(be, bl), xytext=(be + 22, bl + 0.16), fontproperties=BLD, fontsize=11,
                color=BAD, arrowprops=dict(arrowstyle='->', color=BAD, lw=1.8))
    ax2 = ax.twinx()
    ax2.plot(ivs, ivv, color=GOOD, lw=1.6, ls='--', alpha=0.8)
    ax2.set_ylabel('val 과일 IoU (초록 점선)', fontproperties=BLD, fontsize=11, color=GOOD)
    ax2.tick_params(labelcolor=GOOD)
    ax.set_xlabel('에폭 (전체 사진을 몇 바퀴 봤나)', fontproperties=BLD, fontsize=12)
    ax.set_ylabel('loss (낮을수록 좋음)', fontproperties=BLD, fontsize=12)
    ax.set_title('내 FruitSeg30 학습의 진짜 곡선 — 200에폭, 3시간 42분',
                 fontproperties=BLD, fontsize=14, pad=14)
    leg = ax.legend(loc='upper right', prop=REG, fontsize=11)
    leg.get_frame().set_edgecolor('#cbd5e1')
    ax.grid(alpha=0.25)
    fig.text(0.5, -0.02,
             f'맨 처음 loss {tv[0]:.3f} → 마지막 {tv[-1]:.4f}. '
             f'val 은 {be}에폭에서 가장 낮았고 그 뒤로는 더 좋아지지 않았습니다(= 과적합 시작).',
             fontproperties=REG, fontsize=10.5, color=MUTE, ha='center')
    fig.subplots_adjust(bottom=0.14)
    save(fig, 'eg_loss_annotated.png')
    return be, bl


# ───────────────────────────────── ⑩ 잘 맞힌 것 vs 못 맞힌 것
def fig_good_bad(rec):
    best = max(rec, key=lambda x: x['iou'])
    worst = min(rec, key=lambda x: x['iou'])
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 9))
    for row, r, tag, c in ((0, best, '가장 잘 맞힌 사진', GOOD),
                           (1, worst, '가장 못 맞힌 사진', BAD)):
        im, gt, pr = load_fs(r['file'])
        for col, (img, ti) in enumerate([(im, '원본'), (gt.astype(np.uint8) * 255, '정답'),
                                         (diff_map(im, gt, pr), '초록=맞음 빨강=놓침 노랑=헛다리')]):
            ax = axes[row, col]
            ax.imshow(img, cmap='gray' if img.ndim == 2 else None); blank(ax)
            if col == 0:
                ax.set_ylabel(f'{tag}\nIoU {r["iou"]:.3f}', fontproperties=BLD,
                              fontsize=12, color=c, labelpad=12)
                ax.axis('on'); ax.set_xticks([]); ax.set_yticks([])
                for s in ax.spines.values():
                    s.set_visible(False)
            if row == 0:
                ax.set_title(ti, fontproperties=BLD, fontsize=11.5, pad=8)
        t(axes[row, 2], 0.5, -0.05, f'{r["file"]}  ({r["cls"].replace("_", " ")})',
          size=9.5, color=MUTE, va='top')
    fig.text(0.5, 0.02,
             '못 맞힌 쪽은 잎사귀·그림자가 많거나 정답 자체가 애매한 사진입니다 '
             '(파인애플·포도가 대표적).',
             fontproperties=REG, fontsize=11, color=MUTE, ha='center')
    fig.subplots_adjust(bottom=0.08, hspace=0.14)
    save(fig, 'eg_good_bad.png')
    return best, worst


def main():
    rec, meta = records()
    print('그림 생성 시작 →', OUT)
    fig_what_we_do(rec)
    fig_pixel_grid(rec)
    fig_journey(rec)
    r, tp, fp, fn = fig_iou_real(rec)
    fig_confusion(r, tp, fp, fn)
    fig_batch_math()
    fig_three_datasets()
    be, bl = fig_loss_annotated()
    best, worst = fig_good_bad(rec)
    fig_prob_threshold(rec)

    summary = {
        'iou_example': {'file': r['file'], 'tp': tp, 'fp': fp, 'fn': fn,
                        'iou': tp / (tp + fp + fn)},
        'best_epoch': be, 'best_val_loss': bl,
        'best_image': {'file': best['file'], 'iou': best['iou']},
        'worst_image': {'file': worst['file'], 'iou': worst['iou']},
        'mean_iou': meta['mean_iou'], 'median_iou': meta['median_iou'],
    }
    (REPO / 'output/easy_guide_numbers.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))
    print('\n숫자 요약 저장: output/easy_guide_numbers.json')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
