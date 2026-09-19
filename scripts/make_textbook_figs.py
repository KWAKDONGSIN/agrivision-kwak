# -*- coding: utf-8 -*-
"""교재용 개념 설명 그림을 만든다 (reports/figures/textbook/).

전부 matplotlib으로 그리며, 실제 데이터셋 사진을 써서 "우리 데이터로 설명"한다.

사용:  $PY tools/make_textbook_figs.py
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
OUT = REPO / 'reports/figures/textbook'
FS30 = BASE / 'dataset_fruitseg30'
BB = BASE / 'dataset_6fold/cv1'

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
INK, MUTE, BLUE, GOOD, BAD, ORNG = '#111827', '#6b7280', '#2563eb', '#0a7d33', '#b23b3b', '#d97706'


def save(fig, name, dpi=140):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    fig.savefig(p, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'[fig] {p}')


def pick(cls='Orange', n=1, split='train'):
    d = FS30 / split / 'images'
    fs = sorted(p for p in d.iterdir() if p.stem.startswith(cls + '__'))
    return fs[n]


def load(p):
    im = np.array(Image.open(p).convert('RGB'))
    mk = np.array(Image.open(p.parent.parent / 'masks' / f'{p.stem}.png').convert('L')) > 0
    return im, mk


def box(ax, x, y, w, h, text, fc='#eef3fb', ec=BLUE, fs=10, bold=True, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.012',
                                facecolor=fc, edgecolor=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontproperties=BLD if bold else REG, fontsize=fs, color=tc)


def arrow(ax, x1, y1, x2, y2, color=MUTE, lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                 mutation_scale=14, color=color, lw=lw))


# ------------------------------------------------------------------ 1. 픽셀
def fig_pixel_zoom():
    im, mk = load(pick('Orange', 2))
    # 과일 경계선을 지나는 자리를 골라야 색이 변하는 게 보인다
    rows = np.where(mk.any(axis=1))[0]
    r = rows[len(rows) // 2]                       # 과일 한가운데 높이의 줄
    c = np.where(mk[r])[0][0]                      # 그 줄에서 과일이 시작되는 지점
    y0, x0 = int(r) - 6, int(c) - 6
    y0, x0 = max(0, min(y0, im.shape[0] - 13)), max(0, min(x0, im.shape[1] - 13))

    fig = plt.figure(figsize=(11, 4.4))
    ax1 = fig.add_axes([0.02, 0.10, 0.28, 0.80])
    ax1.imshow(im); ax1.axis('off')
    ax1.set_title('① 우리 눈에 보이는 사진', fontproperties=BLD, fontsize=12, color=INK)
    ax1.add_patch(Rectangle((x0 - 24, y0 - 24), 60, 60, fill=False, edgecolor='red', lw=2))

    crop = im[y0:y0 + 12, x0:x0 + 12]
    ax2 = fig.add_axes([0.34, 0.10, 0.26, 0.80])
    ax2.imshow(crop, interpolation='nearest')
    ax2.set_xticks([]); ax2.set_yticks([])
    ax2.set_title('② 아주 크게 확대하면 = 네모칸(픽셀)', fontproperties=BLD, fontsize=12, color=INK)
    for i in range(13):
        ax2.axhline(i - .5, color='white', lw=.6)
        ax2.axvline(i - .5, color='white', lw=.6)

    ax3 = fig.add_axes([0.64, 0.10, 0.34, 0.80])
    ax3.axis('off')
    ax3.set_title('③ 컴퓨터가 보는 것 = 숫자표', fontproperties=BLD, fontsize=12, color=INK)
    sub = crop[:6, :6]
    for r in range(6):
        for c in range(6):
            rgb = sub[r, c]
            ax3.add_patch(Rectangle((c, 5 - r), 1, 1, facecolor=np.array(rgb) / 255,
                                    edgecolor='#cccccc'))
            ax3.text(c + .5, 5 - r + .5, f'{rgb[0]}\n{rgb[1]}\n{rgb[2]}', ha='center', va='center',
                     fontsize=6.2, color='white' if rgb.mean() < 128 else '#111111',
                     fontproperties=REG)
    ax3.set_xlim(-0.2, 6.2); ax3.set_ylim(-0.85, 6.3)
    ax3.text(3, -0.55, '칸마다 빨강/초록/파랑 밝기 (0~255)', ha='center',
             fontproperties=REG, fontsize=9.5, color=MUTE)
    save(fig, 'tb_pixel_zoom.png')


# ------------------------------------------------------- 2. 세 가지 작업 비교
def fig_task_compare():
    im, mk = load(pick('Apple_Gala', 3))
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.7))
    axes[0].imshow(im); axes[0].set_title('원본 사진', fontproperties=BLD, fontsize=12)
    axes[1].imshow(im)
    axes[1].text(0.5, 1.06, '분류 (Classification)', transform=axes[1].transAxes,
                 ha='center', fontproperties=BLD, fontsize=12)
    axes[1].text(0.5, 0.5, '"사과"', transform=axes[1].transAxes, ha='center', va='center',
                 fontproperties=BLD, fontsize=26, color='white',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor=BLUE, alpha=.85))
    ys, xs = np.where(mk)
    axes[2].imshow(im)
    axes[2].add_patch(Rectangle((xs.min(), ys.min()), xs.max() - xs.min(), ys.max() - ys.min(),
                                fill=False, edgecolor='#22c55e', lw=3.5))
    axes[2].set_title('객체 탐지 (Detection)', fontproperties=BLD, fontsize=12)
    ov = im.copy()
    ov[mk] = (0.4 * ov[mk] + 0.6 * np.array([230, 60, 60])).astype(np.uint8)
    axes[3].imshow(ov)
    axes[3].set_title('세그멘테이션 ← 우리가 하는 것', fontproperties=BLD, fontsize=12, color=BAD)
    for a in axes:
        a.axis('off')
    fig.text(0.5, 0.005, '분류 = 이름표 한 개  /  탐지 = 네모 상자  /  세그멘테이션 = 픽셀 하나하나 색칠',
             ha='center', fontproperties=REG, fontsize=11, color=MUTE)
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    save(fig, 'tb_task_compare.png')


# --------------------------------------------------- 3. 마스크는 0과 1의 표
def fig_mask_numbers():
    im, mk = load(pick('Kiwi', 1))
    fig = plt.figure(figsize=(11.5, 4.0))
    ax1 = fig.add_axes([0.02, 0.10, 0.26, 0.80]); ax1.imshow(im); ax1.axis('off')
    ax1.set_title('사진', fontproperties=BLD, fontsize=12)
    ax2 = fig.add_axes([0.31, 0.10, 0.26, 0.80])
    ax2.imshow(mk, cmap='gray'); ax2.axis('off')
    ax2.set_title('정답 마스크 (흰색=과일)', fontproperties=BLD, fontsize=12)
    r0, c0 = 200, 180
    ax1.add_patch(Rectangle((c0, r0), 90, 90, fill=False, edgecolor='red', lw=2))
    ax2.add_patch(Rectangle((c0, r0), 90, 90, fill=False, edgecolor='red', lw=2))
    ax3 = fig.add_axes([0.62, 0.10, 0.36, 0.80]); ax3.axis('off')
    ax3.set_title('빨간 네모 안을 숫자로 보면', fontproperties=BLD, fontsize=12)
    sub = mk[r0:r0 + 90:9, c0:c0 + 90:9].astype(int)
    for r in range(10):
        for c in range(10):
            v = sub[r, c]
            ax3.add_patch(Rectangle((c, 9 - r), 1, 1,
                                    facecolor='#111827' if v == 0 else '#f8fafc',
                                    edgecolor='#94a3b8', lw=.6))
            ax3.text(c + .5, 9 - r + .5, str(v), ha='center', va='center', fontsize=8,
                     color='#e5e7eb' if v == 0 else '#111827', fontproperties=REG)
    ax3.set_xlim(-.2, 10.2); ax3.set_ylim(-.6, 10.2)
    ax3.text(5, -0.45, '0 = 배경,  1 = 과일.  모델은 이 표를 맞히는 연습을 합니다.',
             ha='center', fontproperties=REG, fontsize=10, color=MUTE)
    save(fig, 'tb_mask_numbers.png')


# ------------------------------------------------------------ 4. 학습 루프
def fig_train_loop():
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis('off')
    steps = [
        (0.2, 4.6, '① 사진 2장 꺼내기\n(batch)', '#eef3fb'),
        (2.5, 4.6, '② 뒤집기·돌리기\n(증강)', '#eef3fb'),
        (4.8, 4.6, '③ 모델에 넣기\n(백본→헤더)', '#eef3fb'),
        (7.1, 4.6, '④ 예측 그림\n나옴', '#eef3fb'),
    ]
    for x, y, t, c in steps:
        box(ax, x, y, 2.0, 1.0, t, fc=c, fs=10)
    for x in (2.2, 4.5, 6.8):
        arrow(ax, x, 5.1, x + 0.3, 5.1)
    arrow(ax, 8.1, 4.55, 8.1, 3.7)
    box(ax, 7.1, 2.6, 2.0, 1.0, '⑤ 정답과 비교\n= loss 계산', fc='#fdf2ef', ec=BAD, fs=10)
    arrow(ax, 7.05, 3.1, 6.4, 3.1)
    box(ax, 4.3, 2.6, 2.0, 1.0, '⑥ 틀린 만큼\n모델 값 수정', fc='#eef7f0', ec=GOOD, fs=10)
    arrow(ax, 4.25, 3.1, 1.2, 3.1)
    arrow(ax, 1.2, 3.1, 1.2, 4.55)
    ax.add_patch(Rectangle((0.05, 2.15), 9.4, 3.65, fill=False, edgecolor='#cbd5e1',
                           lw=1.2, linestyle='--'))
    ax.text(0.25, 2.32, '이 한 바퀴가 "1 스텝(iteration)" 입니다',
            fontproperties=REG, fontsize=10, color=MUTE)
    ax.text(0.2, 5.95, '사진 전체를 한 바퀴 다 돌면 = 1 에폭(epoch).  우리는 이걸 100~200번 반복합니다.',
            fontproperties=BLD, fontsize=12, color=INK)
    box(ax, 0.2, 0.7, 4.3, 1.1, '5 에폭마다 한 번:\n검증(val) 사진으로 중간 점검', fc='#fffbeb',
        ec=ORNG, fs=10)
    box(ax, 5.0, 0.7, 4.4, 1.1, '지금까지 중 가장 좋으면\n_best.pth 파일로 저장', fc='#eef7f0',
        ec=GOOD, fs=10)
    save(fig, 'tb_train_loop.png')


# -------------------------------------------------- 5. 경사하강 (언덕 내려가기)
def fig_gradient():
    x = np.linspace(-3, 3, 400)
    y = x ** 2 + 0.6 * np.sin(3 * x) + 1
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9), sharey=True)
    cases = [('학습률이 너무 작음', 0.06, BLUE, '조금씩만 내려가서\n너무 오래 걸림'),
             ('적당한 학습률', 0.22, GOOD, '적당히 내려가\n바닥에 잘 도착'),
             ('학습률이 너무 큼', 0.85, BAD, '껑충 뛰어넘어\n바닥을 못 찾음')]
    for ax, (ttl, lr, col, desc) in zip(axes, cases):
        ax.plot(x, y, color='#94a3b8', lw=2)
        p = -2.6
        pts = [p]
        for _ in range(9):
            g = 2 * p + 1.8 * np.cos(3 * p)
            p = p - lr * g
            p = np.clip(p, -3, 3)
            pts.append(p)
        py = [v ** 2 + 0.6 * np.sin(3 * v) + 1 for v in pts]
        ax.plot(pts, py, 'o-', color=col, ms=5, lw=1.4)
        ax.set_title(ttl, fontproperties=BLD, fontsize=12, color=col)
        ax.text(0.5, 0.86, desc, transform=ax.transAxes, ha='center',
                fontproperties=REG, fontsize=10, color=MUTE)
        ax.set_xticks([]); ax.set_yticks([])
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_ylabel('loss (틀린 정도)', fontproperties=REG, fontsize=11)
    fig.text(0.5, -0.02, '공이 골짜기 바닥으로 굴러 내려가듯, 모델은 loss가 낮아지는 쪽으로 조금씩 값을 바꿉니다. '
                         '한 걸음의 크기가 학습률(LR)입니다.',
             ha='center', fontproperties=REG, fontsize=10.5, color=INK)
    fig.tight_layout()
    save(fig, 'tb_gradient.png')


# ------------------------------------------------------------ 6. 배치와 누적
def fig_batch_accum():
    fig, ax = plt.subplots(figsize=(11.5, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis('off')
    ax.text(0.1, 4.7, 'BATCH_SIZE 2 + ACCUM_STEPS 4  =  한 번에 8장을 본 것과 같은 효과',
            fontproperties=BLD, fontsize=13, color=INK)
    for i in range(4):
        x = 0.3 + i * 2.35
        box(ax, x, 3.0, 2.0, 0.9, f'{i+1}번째\n사진 2장 계산', fc='#eef3fb', fs=9.5)
        arrow(ax, x + 1.0, 2.95, x + 1.0, 2.4)
        box(ax, x, 1.5, 2.0, 0.85, '고칠 양만\n쌓아둠', fc='#f8fafc', ec='#94a3b8', fs=9.5)
    arrow(ax, 4.9, 1.45, 4.9, 0.95)
    box(ax, 2.6, 0.15, 4.6, 0.75, '4번 모은 뒤 한꺼번에 모델 수정 (optimizer.step)',
        fc='#eef7f0', ec=GOOD, fs=10.5)
    ax.text(0.1, 0.35, 'GPU 메모리가\n작아도 큰 배치\n효과를 냄', fontproperties=REG,
            fontsize=9.5, color=MUTE)
    save(fig, 'tb_batch_accum.png')


# --------------------------------------------------------- 7. 데이터 분할
def fig_split():
    fig, ax = plt.subplots(figsize=(11.5, 3.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis('off')
    segs = [('train (학습)', 7.0, '#2563eb', '모델이 보고 배우는 사진'),
            ('val (검증)', 1.0, '#d97706', '학습 중 중간 점검'),
            ('test (시험)', 2.0, '#0a7d33', '끝나고 딱 한 번 채점')]
    x = 0.3
    for name, w, col, desc in segs:
        ax.add_patch(Rectangle((x, 1.5), w * 0.93, 0.8, facecolor=col, alpha=.85,
                               edgecolor='white', lw=2))
        ax.text(x + w * 0.465, 1.9, name, ha='center', va='center',
                fontproperties=BLD, fontsize=12, color='white')
        ax.text(x + w * 0.465, 1.25, f'{int(w*10)}%', ha='center',
                fontproperties=BLD, fontsize=11, color=col)
        ax.text(x + w * 0.465, 0.85, desc, ha='center', fontproperties=REG,
                fontsize=9.5, color=MUTE)
        x += w * 0.93 + 0.05
    ax.text(0.3, 2.65, '전체 사진을 7 : 1 : 2 로 나눕니다', fontproperties=BLD,
            fontsize=13, color=INK)
    ax.text(0.3, 0.25, 'test 사진을 학습에 쓰면 = 시험문제를 미리 보고 시험 보는 것. 점수가 거짓이 됩니다.',
            fontproperties=REG, fontsize=10.5, color=BAD)
    save(fig, 'tb_split.png')


# --------------------------------------------------------- 8. 데이터 증강
def fig_augment():
    im, mk = load(pick('Guava', 1))
    im = np.array(Image.fromarray(im).resize((320, 320)))
    mk = np.array(Image.fromarray(mk.astype(np.uint8) * 255).resize((320, 320), Image.NEAREST)) > 0

    def ov(a, m):
        o = a.copy(); o[m] = (0.45 * o[m] + 0.55 * np.array([230, 60, 60])).astype(np.uint8)
        return o

    variants = [('원본', im, mk),
                ('좌우 뒤집기\n(HFlip)', im[:, ::-1], mk[:, ::-1]),
                ('돌리기\n(Rotation 60°)', np.array(Image.fromarray(im).rotate(35)),
                 np.array(Image.fromarray(mk.astype(np.uint8) * 255).rotate(35)) > 0),
                ('일부만 잘라내기\n(RandomCrop)', im[40:280, 60:300], mk[40:280, 60:300])]
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.7))
    for ax, (t, a, m) in zip(axes, variants):
        ax.imshow(ov(a, m)); ax.axis('off')
        ax.set_title(t, fontproperties=BLD, fontsize=11)
    fig.suptitle('같은 사진 1장을 매번 다르게 보여주면, 사진을 통째로 외우지 못합니다 (데이터 증강)',
                 fontproperties=BLD, fontsize=13, color=INK)
    fig.text(0.5, 0.02, '중요: 사진을 돌리면 정답 마스크도 똑같이 돌려야 합니다. 코드가 둘을 같이 처리합니다.',
             ha='center', fontproperties=REG, fontsize=10.5, color=MUTE)
    fig.tight_layout(rect=[0, 0.06, 1, 0.93])
    save(fig, 'tb_augment.png')


# ------------------------------------------------------ 9. 백본과 헤더 구조
def fig_backbone_head():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis('off')
    box(ax, 0.2, 2.1, 1.5, 1.2, '사진\n512×512', fc='#f8fafc', ec='#94a3b8')
    arrow(ax, 1.75, 2.7, 2.2, 2.7)
    ax.add_patch(FancyBboxPatch((2.25, 1.6), 3.6, 2.3, boxstyle='round,pad=0.02',
                                facecolor='#eef3fb', edgecolor=BLUE, lw=1.8))
    ax.text(4.05, 3.6, '백본 (Backbone)', ha='center', fontproperties=BLD, fontsize=12.5, color=BLUE)
    ax.text(4.05, 3.25, '"사진을 보는 눈"', ha='center', fontproperties=REG, fontsize=10, color=MUTE)
    for i, (w, lbl) in enumerate([(1.0, '가장자리·색'), (0.78, '무늬'), (0.56, '모양'), (0.36, '"과일 같은 것"')]):
        x = 2.5 + i * 0.85
        ax.add_patch(Rectangle((x, 2.0 - 0), 0.55, w * 0.9, facecolor=BLUE, alpha=.25 + i * .18,
                               edgecolor=BLUE))
        ax.text(x + 0.27, 1.85, lbl, ha='center', va='top', fontproperties=REG,
                fontsize=7.6, color=MUTE, rotation=0)
    arrow(ax, 5.9, 2.7, 6.4, 2.7)
    ax.add_patch(FancyBboxPatch((6.45, 1.6), 3.0, 2.3, boxstyle='round,pad=0.02',
                                facecolor='#eef7f0', edgecolor=GOOD, lw=1.8))
    ax.text(7.95, 3.6, '헤더 (Head)', ha='center', fontproperties=BLD, fontsize=12.5, color=GOOD)
    ax.text(7.95, 3.25, '"본 것을 그림으로 그리는 손"', ha='center', fontproperties=REG,
            fontsize=9.5, color=MUTE)
    ax.text(7.95, 2.45, '작게 요약된 정보를\n다시 원래 크기로 펴서\n픽셀마다 판정',
            ha='center', va='center', fontproperties=REG, fontsize=9.5, color=INK)
    arrow(ax, 9.5, 2.7, 10.0, 2.7)
    box(ax, 10.05, 2.1, 1.7, 1.2, '예측 마스크\n512×512', fc='#fdf2ef', ec=BAD)
    ax.text(0.2, 4.6, '이미지 모델은 두 부분으로 되어 있습니다', fontproperties=BLD,
            fontsize=13.5, color=INK)
    ax.text(0.2, 0.9, '우리 연구: 백본 8종 × 헤더 4종 = 32가지 조합을 전부 같은 조건으로 비교',
            fontproperties=BLD, fontsize=11.5, color=BLUE)
    ax.text(0.2, 0.45, '백본 예: ResNet-50, ConvNeXt-T, Swin-T, MiT-B2 …    '
                       '헤더 예: UPerNet, CCASeg, Mask2Former, OneFormer',
            fontproperties=REG, fontsize=10, color=MUTE)
    save(fig, 'tb_backbone_head.png')


# ------------------------------------------------------------- 10. IoU 그림
def fig_iou():
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
    gt = np.zeros((100, 100), bool); gt[25:80, 20:70] = True
    pr = np.zeros((100, 100), bool); pr[35:90, 33:83] = True
    panels = [('정답 (사람)', gt, '#ef4444'), ('예측 (모델)', pr, '#3b82f6')]
    for ax, (t, m, c) in zip(axes[:2], panels):
        rgb = np.ones((100, 100, 3))
        rgb[m] = matplotlib.colors.to_rgb(c)
        ax.imshow(rgb); ax.set_title(t, fontproperties=BLD, fontsize=12); ax.axis('off')
    inter, union = gt & pr, gt | pr
    rgb = np.ones((100, 100, 3))
    rgb[gt & ~pr] = matplotlib.colors.to_rgb('#fca5a5')
    rgb[pr & ~gt] = matplotlib.colors.to_rgb('#93c5fd')
    rgb[inter] = matplotlib.colors.to_rgb('#7c3aed')
    axes[2].imshow(rgb); axes[2].axis('off')
    axes[2].set_title('겹쳐보면', fontproperties=BLD, fontsize=12)
    axes[2].text(50, 108, '보라 = 둘 다 (겹친 부분)', ha='center', fontproperties=REG,
                 fontsize=9.5, color='#7c3aed')
    axes[3].axis('off')
    axes[3].text(0.5, 0.78, 'IoU = 겹친 부분 ÷ 전체 부분', ha='center',
                 fontproperties=BLD, fontsize=13, color=INK, transform=axes[3].transAxes)
    axes[3].text(0.5, 0.55, f'= {inter.sum():,} ÷ {union.sum():,}', ha='center',
                 fontproperties=REG, fontsize=13, color=INK, transform=axes[3].transAxes)
    axes[3].text(0.5, 0.36, f'= {inter.sum()/union.sum():.3f}', ha='center',
                 fontproperties=BLD, fontsize=17, color=GOOD, transform=axes[3].transAxes)
    axes[3].text(0.5, 0.16, '1에 가까울수록 정답과 똑같음', ha='center',
                 fontproperties=REG, fontsize=10, color=MUTE, transform=axes[3].transAxes)
    fig.tight_layout()
    save(fig, 'tb_iou.png')


# -------------------------------------------------- 11. Precision / Recall
def fig_precision_recall():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.0))
    gt = np.zeros((100, 100), bool); gt[25:80, 20:70] = True
    for ax, (title, pr, expl) in zip(axes, [
            ('Precision (정밀도) — 헛다리를 안 짚나',
             np.pad(np.ones((40, 35), bool), ((30, 30), (25, 40))),
             '모델이 "과일"이라 한 것 중\n진짜 과일의 비율'),
            ('Recall (재현율) — 놓치지 않나',
             np.pad(np.ones((55, 65), bool), ((20, 25), (15, 20))),
             '진짜 과일 중\n모델이 찾아낸 비율')]):
        pr = pr[:100, :100].astype(bool)
        rgb = np.ones((100, 100, 3))
        rgb[gt & ~pr] = matplotlib.colors.to_rgb('#fca5a5')
        rgb[pr & ~gt] = matplotlib.colors.to_rgb('#fcd34d')
        rgb[gt & pr] = matplotlib.colors.to_rgb('#34d399')
        ax.imshow(rgb); ax.axis('off')
        ax.set_title(title, fontproperties=BLD, fontsize=12)
        tp, fp, fn = (gt & pr).sum(), (pr & ~gt).sum(), (gt & ~pr).sum()
        ax.text(50, 112, f'초록(맞음) {tp:,}   노랑(헛다리) {fp:,}   빨강(놓침) {fn:,}',
                ha='center', fontproperties=REG, fontsize=9.5, color=MUTE)
        ax.text(50, 124, f'Precision {tp/(tp+fp):.2f}    Recall {tp/(tp+fn):.2f}',
                ha='center', fontproperties=BLD, fontsize=11, color=INK)
        ax.text(105, 50, expl, va='center', fontproperties=REG, fontsize=10, color=MUTE)
    fig.tight_layout()
    save(fig, 'tb_precision_recall.png')


# ---------------------------------------------------------- 12. 학습률 스케줄
def fig_lr_schedule():
    iters = np.arange(0, 100)
    warm = 10
    lr0 = 1e-4
    lr = np.where(iters < warm,
                  lr0 * (0.1 + 0.9 * iters / warm),
                  lr0 * (1 - (iters - warm) / (100 - warm)) ** 0.9)
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.plot(iters, lr, color=BLUE, lw=2.4)
    ax.axvspan(0, warm, color='#fef3c7', alpha=.8)
    ax.text(warm / 2, lr0 * 0.55, '워밍업\n(천천히 시작)', ha='center',
            fontproperties=BLD, fontsize=10, color=ORNG)
    ax.text(55, lr0 * 0.6, '점점 줄이기 (poly)\n= 마무리는 조심조심',
            fontproperties=BLD, fontsize=10, color=BLUE)
    ax.set_xlabel('학습 진행 (에폭)', fontproperties=REG, fontsize=11)
    ax.set_ylabel('학습률 LR', fontproperties=REG, fontsize=11)
    ax.set_title('warmuppolylr — yaml의 SCHEDULER가 하는 일',
                 fontproperties=BLD, fontsize=12.5, color=INK)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=.25)
    fig.tight_layout()
    save(fig, 'tb_lr_schedule.png')


# ------------------------------------------------------------ 13. 과적합
def fig_overfit():
    e = np.arange(1, 101)
    tr = 1.2 * np.exp(-e / 22) + 0.06
    va_good = 1.25 * np.exp(-e / 20) + 0.12
    va_bad = 1.25 * np.exp(-e / 14) + 0.10 + np.clip((e - 45) / 100, 0, None) ** 1.5
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.9), sharey=True)
    for ax, (va, ttl, col) in zip(axes, [(va_good, '정상 — 둘 다 내려감', GOOD),
                                         (va_bad, '과적합 — 검증만 다시 올라감', BAD)]):
        ax.plot(e, tr, color=BLUE, lw=2, label='train loss (배운 사진)')
        ax.plot(e, va, color=ORNG, lw=2, label='val loss (안 본 사진)')
        ax.set_title(ttl, fontproperties=BLD, fontsize=12, color=col)
        ax.set_xlabel('에폭', fontproperties=REG, fontsize=10.5)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(alpha=.22)
        leg = ax.legend(prop=REG, fontsize=9.5, frameon=False)
    axes[1].axvline(45, color=BAD, ls='--', lw=1.4)
    axes[1].text(47, 0.9, '여기부터\n"외우기" 시작', fontproperties=BLD, fontsize=9.5, color=BAD)
    axes[0].set_ylabel('loss', fontproperties=REG, fontsize=11)
    fig.text(0.5, -0.02, 'best 체크포인트는 val loss가 가장 낮았던 시점에 저장됩니다. '
                         'early stopping은 더 안 좋아지면 학습을 멈추는 장치입니다.',
             ha='center', fontproperties=REG, fontsize=10.5, color=INK)
    fig.tight_layout()
    save(fig, 'tb_overfit.png')


# -------------------------------------------------------- 14. 6-fold 교차검증
def fig_6fold():
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.4); ax.axis('off')
    ax.text(0.2, 7.0, '6-fold 교차검증 — 시험 범위를 6번 바꿔가며 채점',
            fontproperties=BLD, fontsize=13.5, color=INK)
    for f in range(6):
        y = 5.7 - f * 0.85
        ax.text(0.2, y + 0.18, f'cv{f+1}', fontproperties=BLD, fontsize=10.5, color=INK)
        for b in range(6):
            x = 1.2 + b * 1.65
            is_test = (b == f)
            ax.add_patch(Rectangle((x, y), 1.55, 0.55,
                                   facecolor='#0a7d33' if is_test else '#2563eb',
                                   alpha=.85 if is_test else .35, edgecolor='white', lw=1.6))
            ax.text(x + 0.78, y + 0.28, '시험' if is_test else '학습', ha='center', va='center',
                    fontproperties=BLD if is_test else REG, fontsize=8.5,
                    color='white' if is_test else '#1e3a8a')
    ax.text(0.2, 0.55, '한 번만 나누면 "운 좋은 분할"일 수 있습니다. 6번 다 해보고 평균을 내면 믿을 수 있습니다.',
            fontproperties=REG, fontsize=10.5, color=MUTE)
    ax.text(0.2, 0.15, '우리 블루베리 실험: 32조합 × 6폴드 = 191런 (한 조합의 cv1이 빠져 192가 아님)',
            fontproperties=REG, fontsize=10.5, color=BAD)
    save(fig, 'tb_6fold.png')


# ---------------------------------------------------------- 15. yaml 구조 지도
def fig_yaml_map():
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis('off')
    ax.text(0.15, 6.7, 'yaml 파일 한 장에 실험 조건이 전부 들어 있습니다',
            fontproperties=BLD, fontsize=13.5, color=INK)
    groups = [
        ('MODEL', '어떤 모델을 쓸까', ['NAME (헤더)', 'BACKBONE (백본)', 'PRETRAINED (미리 배운 값)'], BLUE, 0.15, 4.5),
        ('DATASET', '어떤 데이터를 쓸까', ['NAME (데이터 종류)', 'ROOT (사진 폴더)', 'IGNORE_LABEL'], GOOD, 3.45, 4.5),
        ('TRAIN', '어떻게 학습할까', ['IMAGE_SIZE / BATCH_SIZE', 'EPOCHS / AUGMENT', 'ACCUM / EARLY_STOP'], ORNG, 6.75, 4.5),
        ('LOSS', '무엇을 줄일까', ['NAME (BCEDice)', 'BCE_WEIGHT / DICE_WEIGHT'], BAD, 0.15, 2.2),
        ('OPTIMIZER / SCHEDULER', '얼마나 크게 고칠까', ['NAME (adamw)', 'LR (학습률)', 'WARMUP / POWER'], '#7c3aed', 3.45, 2.2),
        ('EVAL / TEST', '어떻게 채점할까', ['IMAGE_SIZE', 'MODEL_PATH', 'MSF (다중 스케일)'], '#0891b2', 6.75, 2.2),
    ]
    for name, sub, items, col, x, y in groups:
        ax.add_patch(FancyBboxPatch((x, y), 3.05, 1.95, boxstyle='round,pad=0.03',
                                    facecolor='white', edgecolor=col, lw=1.8))
        ax.add_patch(Rectangle((x, y + 1.55), 3.05, 0.4, facecolor=col, alpha=.16,
                               edgecolor='none'))
        ax.text(x + 0.12, y + 1.66, name, fontproperties=BLD, fontsize=11, color=col)
        ax.text(x + 0.12, y + 1.32, sub, fontproperties=REG, fontsize=9.3, color=MUTE)
        for i, it in enumerate(items):
            ax.text(x + 0.16, y + 1.0 - i * 0.30, '· ' + it, fontproperties=REG,
                    fontsize=9.2, color=INK)
    ax.text(0.15, 1.75, '교수님이 강조하신 점 (0723 미팅 녹취록 원문)',
            fontproperties=BLD, fontsize=11.5, color=INK)
    # 여러 줄 글은 va='top'을 줘야 첫 줄이 위로 밀려 올라가 제목과 겹치지 않습니다.
    ax.text(0.15, 1.45, '"나중에는 그러니까 야물 파일에서 그 부분만 바꿔서 그냥 돌리면 되거든요.\n'
                        ' 그러면 이제 그게 다 돌아가는지 이런 것들도 좀 확인해 봐야 되는 거고"',
            fontproperties=REG, fontsize=10.5, color=BLUE, va='top', linespacing=1.5)
    ax.text(0.15, 0.3, '그래서 하드코딩되어 있던 증강 설정도 2026-07-23에 yaml로 옮겼습니다.',
            fontproperties=REG, fontsize=10, color=MUTE)
    save(fig, 'tb_yaml_map.png')


# ------------------------------------------------------------ 16. 폴더 지도
def fig_folder_map():
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
    ax.text(0.15, 7.6, '서버 폴더 지도 — /data/project/2026summer/kds0206/',
            fontproperties=BLD, fontsize=13, color=INK)
    rows = [
        ('semantic-segmentation/', '코드가 전부 여기 (git 저장소)', BLUE, 0),
        ('  ├ configs/', '실험 설정 yaml 파일들 (약 280개)', BLUE, 1),
        ('  ├ semseg/', '모델·데이터·증강 코드 본체', BLUE, 1),
        ('  ├ tools/', 'train.py, val.py 등 실행 스크립트', BLUE, 1),
        ('  ├ output/', '학습 결과·체크포인트(.pth)·로그', BLUE, 1),
        ('  ├ reports/', '표·그림·PDF 보고서', BLUE, 1),
        ('  └ logs/', '실행 로그 텍스트', BLUE, 1),
        ('dataset_6fold/cv1~cv6/', '블루베리 사진 (56GB)', GOOD, 0),
        ('dataset_minneapple/', 'MinneApple 사과 (심볼릭 링크)', GOOD, 0),
        ('dataset_fruitseg30/', 'FruitSeg30 과일 30종 (심볼릭 링크)', GOOD, 0),
        ('weights/', '미리 학습된 백본 가중치 (3.8GB)', ORNG, 0),
        ('문서/', '발표자료·계획 문서·이 교재', '#7c3aed', 0),
        ('연구실 블루베리/', '논문·미팅 녹취·조사자료 455개', '#7c3aed', 0),
        ('작업기록.md', '지금까지 무엇을 했는지 전부', BAD, 0),
    ]
    y = 7.0
    for name, desc, col, indent in rows:
        ax.text(0.2 + indent * 0.25, y, name, fontproperties=BLD if indent == 0 else REG,
                fontsize=10.5 if indent == 0 else 9.8, color=col)
        ax.text(4.3, y, desc, fontproperties=REG, fontsize=9.8, color=MUTE)
        y -= 0.42
    ax.text(0.2, 0.55, '규칙: output/ 안의 .pth 파일은 절대 지우지 않습니다 (다시 만들려면 몇 시간)',
            fontproperties=BLD, fontsize=10, color=BAD)
    ax.text(0.2, 0.15, '규칙: 폴더·파일 이름 규칙을 바꾸면 집계 스크립트가 결과를 못 찾습니다',
            fontproperties=BLD, fontsize=10, color=BAD)
    save(fig, 'tb_folder_map.png')


# ------------------------------------------------------- 17. 정규화 설명
def fig_normalize():
    im, _ = load(pick('Banana', 1))
    arr = im.astype(np.float32) / 255
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    norm = (arr - mean) / std
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.8))
    axes[0].imshow(im); axes[0].axis('off')
    axes[0].set_title('사진', fontproperties=BLD, fontsize=12)
    axes[1].hist(arr.ravel(), bins=50, color=BLUE, alpha=.85)
    axes[1].set_title('정규화 전 — 0 ~ 1', fontproperties=BLD, fontsize=12)
    axes[2].hist(norm.ravel(), bins=50, color=GOOD, alpha=.85)
    axes[2].set_title('정규화 후 — 0 근처로 모임', fontproperties=BLD, fontsize=12)
    for ax in axes[1:]:
        ax.set_ylabel('픽셀 수', fontproperties=REG, fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
    fig.text(0.5, -0.02, '숫자를 0 근처로 모아주면 학습이 훨씬 안정적입니다. '
                         'MEAN/STD 값은 ImageNet 사진 100만 장의 평균으로, 관례처럼 씁니다.',
             ha='center', fontproperties=REG, fontsize=10.5, color=INK)
    fig.tight_layout()
    save(fig, 'tb_normalize.png')


# -------------------------------------------- 18. 전경 비율 비교 (블루베리 vs)
def fig_fg_compare():
    fig, ax = plt.subplots(figsize=(10.5, 4.0))
    names = ['블루베리\n(우리 원래 데이터)', 'MinneApple\n(사과)', 'FruitSeg30\n(과일 30종)']
    vals = [2.4, 2.6, 35.8]
    cols = ['#2563eb', '#0a7d33', '#d97706']
    bars = ax.bar(names, vals, color=cols, alpha=.85, width=.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f'{v}%', ha='center',
                fontproperties=BLD, fontsize=13, color=INK)
    ax.set_ylabel('사진에서 과일이 차지하는 픽셀 비율 (%)', fontproperties=REG, fontsize=11)
    ax.set_title('같은 "과일 찾기"라도 데이터셋마다 난이도가 완전히 다릅니다',
                 fontproperties=BLD, fontsize=13, color=INK)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(REG); lbl.set_fontsize(10.5)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.25)
    ax.text(0.02, 0.86, '전경이 2%대면 "전부 배경"이라 찍어도 정확도 97%\n'
                        '→ mIoU가 쓸모없어지고 fg_IoU를 봐야 하는 이유',
            transform=ax.transAxes, fontproperties=REG, fontsize=10, color=BAD)
    fig.tight_layout()
    save(fig, 'tb_fg_compare.png')


def main():
    fig_pixel_zoom()
    fig_task_compare()
    fig_mask_numbers()
    fig_train_loop()
    fig_gradient()
    fig_batch_accum()
    fig_split()
    fig_augment()
    fig_backbone_head()
    fig_iou()
    fig_precision_recall()
    fig_lr_schedule()
    fig_overfit()
    fig_6fold()
    fig_yaml_map()
    fig_folder_map()
    fig_normalize()
    fig_fg_compare()
    print('[done] 교재용 그림 완성')


if __name__ == '__main__':
    main()
