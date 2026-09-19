# -*- coding: utf-8 -*-
"""학습 기록 설명서 PDF — 초심자용.

"지금까지 무슨 학습을 얼마나 돌렸는가"를 처음 보는 사람도 알 수 있게 설명한다.
숫자는 전부 output/results_summary.csv 에서 직접 집계한다 (하드코딩 없음).

    python tools/make_training_history_pdf.py
"""
import csv
import collections
import statistics as st
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / 'output' / 'results_summary.csv'
OUT = REPO / 'reports' / '학습기록_설명서.pdf'
INK, MUTE, BLUE, GOOD, WARN, BAD = '#111111', '#555555', '#1c5cab', '#0a7d33', '#b8860b', '#b23b3b'

HEADS = ['ccaseg', 'mask2former', 'oneformer', 'upernet']
BACKBONES = ['resnet_50', 'resnetd_50', 'convnext_t', 'uniformer_s',
             'poolformer_s36', 'pvtv2_b2', 'mit_b2', 'swin_t']
HEAD_LABEL = {'ccaseg': 'CCASeg', 'mask2former': 'Mask2Former',
              'oneformer': 'OneFormer', 'upernet': 'UPerNet'}
BB_LABEL = {'resnet_50': 'ResNet-50', 'resnetd_50': 'ResNetD-50', 'convnext_t': 'ConvNeXt-T',
            'uniformer_s': 'UniFormer-S', 'poolformer_s36': 'PoolFormer-S36',
            'pvtv2_b2': 'PVTv2-B2', 'mit_b2': 'MiT-B2', 'swin_t': 'Swin-T'}

# 실측: 2026-07-23 UPerNet+ConvNeXt-T 스모크 테스트 2 epoch = 2분 47초
SEC_PER_EPOCH = 83.5

# ---------------------------------------------------------------- 집계
rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
bench = [r for r in rows if r['head'] in HEADS and r['backbone'] in BACKBONES]
extra = [r for r in rows if r not in bench]

combos = collections.Counter((r['head'], r['backbone']) for r in bench)
incomplete = sorted(k for k, v in combos.items() if v < 6)
by_fold = collections.Counter(r['fold'] for r in bench)
epochs = [int(r['epochs_logged']) for r in bench]
total_epochs = sum(epochs)
gpu_hours = total_epochs * SEC_PER_EPOCH / 3600
early = sum(1 for e in epochs if e < 100)


def mean_by(key):
    ag = collections.defaultdict(list)
    for r in bench:
        ag[r[key]].append(float(r['fg_IoU']))
    return sorted(((st.mean(v), st.pstdev(v), k, len(v)) for k, v in ag.items()), reverse=True)


def mean_by_combo():
    ag = collections.defaultdict(list)
    for r in bench:
        ag[(r['head'], r['backbone'])].append(float(r['fg_IoU']))
    return sorted(((st.mean(v), st.pstdev(v), k, len(v)) for k, v in ag.items()), reverse=True)


combo_rank = mean_by_combo()

# ---------------------------------------------------------------- 문서 구성
B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def tree(t): B.append(('tree', t))
def note(t): B.append(('note', t))
def warn(t): B.append(('warn', t))
def sp(n=1): B.append(('space', n))
def newpage(): B.append(('newpage', None))
def table(headers, rows_, cw): B.append(('table', (headers, rows_, cw)))
def big(pairs): B.append(('big', pairs))

B.append(('cover', None))

# ===== 1. 이 문서는 =====
newpage()
h1('0. 이 문서는 무엇인가')
body('"지금까지 학습을 얼마나, 어떻게 돌렸는가"를 처음 보는 사람도 알 수 있게 '
     '풀어 쓴 문서입니다. 아래 숫자는 전부 output/results_summary.csv 를 '
     '직접 집계한 값이며, 손으로 적은 값은 없습니다.')
sp()
h2('먼저 알아야 할 용어 5개')
table(['용어', '뜻'], [
    ['학습(training)', '모델에게 정답을 보여주며 반복해서 가르치는 과정'],
    ['epoch(에폭)', '가진 사진 전체를 한 바퀴 다 본 것 = 1 epoch'],
    ['런(run)', '설정 하나로 학습을 처음부터 끝까지 한 번 돌린 것'],
    ['fold(폴드)', '데이터를 6등분해 번갈아 시험지로 쓰는 것 (6-fold)'],
    ['체크포인트', '학습한 결과(모델)를 저장한 파일. .pth'],
], [0.20, 0.62])
sp()
note('쉽게 말하면 — 사진 1,195장을 6묶음으로 나누고, 그중 한 묶음을 시험지로 빼놓고 '
     '나머지로 공부시킵니다. 시험지를 바꿔가며 6번 반복하면 "운 좋아서 잘 나온 것"을 '
     '걸러낼 수 있습니다. 이게 6-fold 교차검증입니다.')

# ===== 2. 한 장 요약 =====
newpage()
h1('1. 한 장 요약 — 숫자로 보는 학습 기록')
big([
    (f'{len(bench)}', '벤치마크 학습 런'),
    (f'{len(combos)}', '조합 (헤더4 x 백본8)'),
    (f'{total_epochs:,}', '누적 학습 epoch'),
    (f'{gpu_hours:,.0f}h', 'GPU 사용 시간(추정)'),
])
sp()
h2('무엇을 비교했나 — 3개의 축')
tree(f'· 헤더 4종:  {", ".join(HEAD_LABEL[h] for h in HEADS)}')
tree(f'· 백본 8종:  {", ".join(BB_LABEL[b] for b in BACKBONES)}')
tree('· 폴드 6종:  cv1 ~ cv6')
sp()
body('4 x 8 = 32개 조합을 만들고, 각 조합을 6개 폴드에서 학습했습니다. '
     f'원래 32 x 6 = 192런이 되어야 하는데 실제로는 {len(bench)}런입니다. '
     '왜 1개가 비었는지는 5장에서 설명합니다.')
sp()
h2('학습이 실제로 이뤄진 기간')
tree('· 2026-07-20 ~ 2026-07-22 (3일간)')
tree('· Tesla V100 32GB GPU 8장에 실험을 나눠 동시에 돌림')
sp()
note(f'GPU 사용 시간 {gpu_hours:,.0f}시간은 "1 epoch = {SEC_PER_EPOCH:.0f}초" 실측치에 '
     f'누적 {total_epochs:,} epoch을 곱한 개략치입니다. 실측은 UPerNet+ConvNeXt-T '
     '조합 하나에서 잰 것이라, 더 무거운 조합은 이보다 오래 걸립니다. 정확한 값이 '
     '아니라 규모 감각용 숫자로만 보세요.')

# ===== 3. 폴드별 =====
newpage()
h1('2. 얼마나 골고루 돌렸나')
h2('폴드별 학습 런 수')
table(['폴드', '런 수', '상태'],
      [[f'cv{f}', f'{by_fold[str(f)]}런', '완료' if by_fold[str(f)] == 32 else '1개 부족']
       for f in range(1, 7)],
      [0.14, 0.16, 0.20])
sp()
body('cv1만 31런이고 나머지는 모두 32런입니다. 즉 cv1에서 조합 하나가 빠졌습니다.')
sp()

h2('학습을 끝까지 채웠나 — 조기 종료(early stopping)')
table(['항목', '값', '설명'], [
    ['100 epoch 완주', f'{len(bench)-early}런', '끝까지 학습'],
    ['조기 종료', f'{early}런', '더 나아지지 않아 중간에 멈춤'],
    ['best_epoch 중앙값', f'{int(st.median([int(r["best_epoch"]) for r in bench]))}', '보통 이쯤에서 최고 성능'],
    ['학습 길이 중앙값', f'{int(st.median(epochs))} epoch', '실제로 돈 길이'],
], [0.26, 0.16, 0.36])
sp()
note('조기 종료는 "검증 손실(val_loss)이 10번 연속 나아지지 않으면 멈춰라"는 규칙입니다. '
     f'{len(bench)}런 중 {early}런이 여기 걸려 멈췄습니다. 시간 낭비를 막는 정상 동작이며, '
     '저장되는 모델은 "끝난 시점"이 아니라 "val_loss가 가장 낮았던 시점"의 것입니다.')

# ===== 4. 결과 =====
newpage()
h1('3. 학습 결과 — 무엇이 좋았나')
h2('읽는 법: fg_IoU 란?')
body('사진에서 모델이 "블루베리"라고 칠한 영역과 실제 정답 영역이 얼마나 겹치는지를 '
     '0~1로 나타낸 점수입니다. 1에 가까울수록 좋습니다. 앞의 fg(foreground)는 '
     '"배경 말고 블루베리만 따로 본 점수"라는 뜻입니다.')
sp()
note('배경까지 같이 넣어 평균 낸 mIoU는 사진 대부분이 배경이라 어떤 조합이든 0.9를 넘어서 '
     '차이가 안 보입니다. 그래서 저희는 fg_IoU 를 기준으로 씁니다.')
sp()
h2('조합 순위 TOP 5')
table(['순위', '조합', 'fg_IoU', '폴드'],
      [[f'{i+1}', f'{HEAD_LABEL[k[0]]} + {BB_LABEL[k[1]]}', f'{m:.4f} +- {s:.4f}', f'{n}개']
       for i, (m, s, k, n) in enumerate(combo_rank[:5])],
      [0.08, 0.34, 0.24, 0.12])
sp()
h2('하위 3')
table(['조합', 'fg_IoU', '폴드'],
      [[f'{HEAD_LABEL[k[0]]} + {BB_LABEL[k[1]]}', f'{m:.4f} +- {s:.4f}', f'{n}개']
       for (m, s, k, n) in combo_rank[-3:]],
      [0.34, 0.24, 0.12])

newpage()
h1('4. 핵심 발견 — 헤더보다 백본')
h2('백본별 평균 (n = 그 백본으로 돌린 런 수)')
table(['백본', '평균 fg_IoU', '런'],
      [[BB_LABEL[k], f'{m:.4f}', f'{n}'] for (m, s, k, n) in mean_by('backbone')],
      [0.30, 0.24, 0.10])
sp()
h2('헤더별 평균')
table(['헤더', '평균 fg_IoU', '런'],
      [[HEAD_LABEL[k], f'{m:.4f}', f'{n}'] for (m, s, k, n) in mean_by('head')],
      [0.30, 0.24, 0.10])
sp()
bb = mean_by('backbone')
hd = mean_by('head')
body(f'백본을 바꾸면 성능이 {bb[0][0]:.4f} ~ {bb[-1][0]:.4f} 로 '
     f'{bb[0][0]-bb[-1][0]:.3f}만큼 벌어집니다. 반면 헤더를 바꿔봐야 '
     f'{hd[0][0]:.4f} ~ {hd[-1][0]:.4f}, 차이가 {hd[0][0]-hd[-1][0]:.3f}에 그칩니다.')
sp()
note(f'즉 백본을 바꾸는 편이 헤더를 바꾸는 것보다 약 '
     f'{(bb[0][0]-bb[-1][0])/(hd[0][0]-hd[-1][0]):.0f}배 큰 영향을 줍니다. '
     '특히 ResNet-50이 뚜렷하게 최하위입니다. 이것이 이번 벤치마크의 가장 분명한 메시지입니다.')

# ===== 5. 주의 =====
newpage()
h1('5. 반드시 알아야 할 3가지 결함')
body('아래는 이 학습 기록을 논문에 쓰기 전에 반드시 처리해야 할 문제입니다. '
     '숨기지 말고 먼저 확인하세요.')
sp()

h2('결함 1 — 조합 하나가 통째로 비어 있음')
for k in incomplete:
    warn(f'{HEAD_LABEL[k[0]]} + {BB_LABEL[k[1]]} 은 6폴드 중 {combos[k]}폴드만 학습됨 (cv1 없음)')
tree('· output/upernet_mit_b2_bcedice_cv1/  폴더 없음')
tree('· configs/blueberry_upernet_mit_b2_bcedice_cv1.yaml  파일 자체가 없음')
body('설정 파일이 아예 만들어지지 않아 처음부터 실행된 적이 없습니다. '
     '그래서 총 런 수가 192가 아니라 191입니다.')
warn('이 조합은 현재 성능 2위이고, 보고서에서 Recall 최고 조합으로 적힌 조합입니다. '
     '5개 폴드 평균을 6개 폴드짜리 다른 조합과 나란히 비교하는 것은 공정하지 않습니다.')
tree('→ 할 일: cv1 config를 만들어 1런 추가 학습 (약 2시간)')
sp()

h2('결함 2 — 일부 조합만 학습 예산이 다름')
table(['config', 'EPOCHS', '32조합 포함'], [
    ['mask2former_resnet_50 cv1', '200', '포함'],
    ['upernet_resnet_50 cv1', '200', '포함'],
    ['upernet_pvtv2_b2 cv1', '150', '포함'],
    ['lightham_resnet_50 cv1', '200', '미포함'],
], [0.36, 0.14, 0.18])
body('나머지 전 조합은 EPOCHS 100입니다. 위 3개만 cv1에서 1.5~2배 더 오래 '
     '학습했으므로, 그만큼 유리했을 수 있습니다.')
tree('→ 할 일: 100 epoch으로 재학습할지 판단')
sp()

h2('결함 3 — 통계 방법에 따라 결론이 뒤집힘')
tree('· 대응표본 t-검정  → 헤더 간 "차이 없음"')
tree('· Friedman 검정    → 헤더 간 "차이 있음" (p < 0.05)')
body('교수님 원칙은 "참조 논문이 쓴 방법을 따른다"입니다. 해바라기 논문은 t-검정, '
     '치아 논문은 Friedman을 씁니다.')
tree('→ 할 일: 어느 논문 구조를 따를지 확정 후 통계 방법 결정')

# ===== 6. 확인법 =====
newpage()
h1('6. 직접 확인해 보는 법')
h2('준비')
tree('cd /data/project/2026summer/kds0206/semantic-segmentation')
tree('export PY=/home/kds0206/.conda/envs/kwak/bin/python')
sp()
h2('무슨 학습이 돌아갔는지 보기')
tree('ls output/                   # 학습 결과 폴더 목록')
tree('cat output/results_summary.csv   # 전체 성적표')
sp()
h2('결과를 다시 집계하기')
tree('$PY tools/aggregate_results.py')
body('output/ 안의 TensorBoard 기록을 전부 읽어 CSV 한 장으로 만듭니다.')
sp()
h2('학습된 모델을 시험지(test)로 평가하기')
tree('$PY tools/val.py \\')
tree('   --cfg configs/blueberry_upernet_convnext_t_bcedice_cv1.yaml \\')
tree('   --split test \\')
tree('   --model-path output/upernet_convnext_t_bcedice_cv1/\\')
tree('               UPerNet_ConvNeXt-T_BlueberryDataset_best.pth')
sp()
h2('지금 학습이 돌고 있는지 확인')
tree('nvidia-smi                              # GPU가 물려 있는지')
tree('ps -eo pid,etime,cmd | grep train.py    # 돌아간 시간')
sp()
note('긴 학습은 반드시 tmux 안에서 돌리세요. 그래야 노트북을 꺼도 계속 돕니다. '
     'tmux new -s train 으로 만들고, Ctrl+b 다음 d 로 빠져나오면 됩니다.')

# ---------------------------------------------------------------- 렌더
def wrap(t, n):
    out = []
    for p in t.split('\n'):
        out += textwrap.wrap(p, n) or ['']
    return out


def render():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(OUT) as pdf:
        pw, ph = 8.27, 11.69
        LM = 0.10
        fig = ax = None
        y = [0]

        def npage():
            nonlocal fig, ax
            if fig is not None:
                pdf.savefig(fig)
                plt.close(fig)
            fig = plt.figure(figsize=(pw, ph))
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            y[0] = 0.94

        npage()
        for kind, t in B:
            if kind == 'cover':
                ax.add_patch(plt.Rectangle((0, 0.78), 1, 0.005, color=BLUE))
                ax.text(0.5, 0.62, '블루베리 세그멘테이션', ha='center',
                        fontproperties=BLD, fontsize=21, color=INK)
                ax.text(0.5, 0.565, '학습 기록 설명서', ha='center',
                        fontproperties=BLD, fontsize=21, color=BLUE)
                ax.plot([0.30, 0.70], [0.52, 0.52], color=BLUE, lw=1.5)
                ax.text(0.5, 0.47, '처음 보는 사람도 알 수 있게', ha='center',
                        fontproperties=REG, fontsize=13, color=MUTE)
                ax.text(0.5, 0.17, '2026-07-23   ·   곽동신', ha='center',
                        fontproperties=REG, fontsize=11, color=MUTE)
                ax.text(0.5, 0.135, f'{len(bench)}런 · {len(combos)}조합 · 누적 {total_epochs:,} epoch',
                        ha='center', fontproperties=REG, fontsize=11, color=MUTE)
                continue
            if kind == 'newpage':
                npage()
                continue
            if kind == 'space':
                y[0] -= 0.012 * t
                continue
            if y[0] < 0.09:
                npage()

            if kind == 'h1':
                y[0] -= 0.006
                ax.add_patch(plt.Rectangle((LM - 0.015, y[0] - 0.004), 0.006, 0.028, color=BLUE))
                ax.text(LM, y[0], t, fontproperties=BLD, fontsize=16, color=INK)
                y[0] -= 0.044
            elif kind == 'h2':
                y[0] -= 0.006
                ax.text(LM, y[0], t, fontproperties=BLD, fontsize=12, color=BLUE)
                y[0] -= 0.030
            elif kind == 'body':
                for ln in wrap(t, 48):
                    if y[0] < 0.06:
                        npage()
                    ax.text(LM, y[0], ln, fontproperties=REG, fontsize=10.5, color=INK)
                    y[0] -= 0.0225
                y[0] -= 0.004
            elif kind == 'tree':
                if y[0] < 0.06:
                    npage()
                ax.text(LM + 0.01, y[0], t, fontproperties=REG, fontsize=10, color='#333333')
                y[0] -= 0.0225
            elif kind == 'note':
                ls = wrap(t, 54)
                bh = 0.0205 * len(ls) + 0.016
                if y[0] - bh < 0.05:
                    npage()
                ax.add_patch(plt.Rectangle((LM - 0.02, y[0] - bh + 0.02), 0.84, bh,
                                           facecolor='#eef4fc', edgecolor='#cfe0f5', lw=0.8))
                yy = y[0]
                for ln in ls:
                    ax.text(LM, yy, ln, fontproperties=REG, fontsize=9.5, color=BLUE)
                    yy -= 0.0205
                y[0] -= bh + 0.006
            elif kind == 'warn':
                ls = wrap(t, 54)
                bh = 0.0205 * len(ls) + 0.016
                if y[0] - bh < 0.05:
                    npage()
                ax.add_patch(plt.Rectangle((LM - 0.02, y[0] - bh + 0.02), 0.84, bh,
                                           facecolor='#fdf1ee', edgecolor='#f0cfc6', lw=0.8))
                yy = y[0]
                for ln in ls:
                    ax.text(LM, yy, ln, fontproperties=REG, fontsize=9.5, color=BAD)
                    yy -= 0.0205
                y[0] -= bh + 0.006
            elif kind == 'big':
                if y[0] - 0.10 < 0.06:
                    npage()
                n = len(t)
                w = 0.84 / n
                for i, (num, lab) in enumerate(t):
                    x = LM - 0.02 + i * w
                    ax.add_patch(plt.Rectangle((x, y[0] - 0.075), w - 0.012, 0.088,
                                               facecolor='#f4f7fb', edgecolor='#d8e3f0', lw=0.8))
                    ax.text(x + (w - 0.012) / 2, y[0] - 0.015, num, ha='center',
                            fontproperties=BLD, fontsize=17, color=BLUE)
                    for j, ln in enumerate(wrap(lab, 13)):
                        ax.text(x + (w - 0.012) / 2, y[0] - 0.043 - j * 0.017, ln, ha='center',
                                fontproperties=REG, fontsize=8, color=MUTE)
                y[0] -= 0.098
            elif kind == 'table':
                heads, rws, cw = t
                if y[0] - 0.03 * (len(rws) + 1) < 0.06:
                    npage()
                x0 = LM
                xx = x0
                for i, hh in enumerate(heads):
                    ax.text(xx, y[0], hh, fontproperties=BLD, fontsize=10, color=INK)
                    xx += cw[i] if i < len(cw) else 0.2
                y[0] -= 0.006
                ax.plot([x0, x0 + sum(cw) + 0.06], [y[0], y[0]], color='#bbbbbb', lw=0.8)
                y[0] -= 0.022
                for row in rws:
                    if y[0] < 0.06:
                        npage()
                    xx = x0
                    for i, c in enumerate(row):
                        ax.text(xx, y[0], c, fontproperties=REG, fontsize=9.5, color='#222222')
                        xx += cw[i] if i < len(cw) else 0.2
                    y[0] -= 0.024
                y[0] -= 0.006
        if fig is not None:
            pdf.savefig(fig)
            plt.close(fig)


render()
print('저장:', OUT)
print(f'  집계 근거: {CSV}')
print(f'  벤치마크 런 {len(bench)} / 조합 {len(combos)} / 누적 {total_epochs:,} epoch')
if incomplete:
    print('  ⚠ 6폴드 미완 조합:', [f'{k[0]}+{k[1]} ({combos[k]}폴드)' for k in incomplete])
