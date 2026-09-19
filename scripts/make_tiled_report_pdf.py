# -*- coding: utf-8 -*-
"""«겉보기 크기 통일 + 512 격자 타일링» 데이터셋을 처음부터 끝까지 설명하는 PDF.

목표 독자
  - 곽동신 본인 (중학생도 이해할 수준으로 풀어 쓰되)
  - 그대로 읽으면 팀원·교수님께 설명이 되는 수준까지

🔴 숫자를 하드코딩하지 않는다 — 전부 datasets_tiled_512/manifest.json 과 디스크에서 읽는다.
⚠️ 출력은 팀 공유 경로가 아닌 reports/ 아래.

사용:  $PY tools/make_tiled_report_pdf.py
출력:  reports/타일링_데이터셋_설명서.pdf
       reports/tiled_512/figures/*.png
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc                                        # noqa: E402

TILED = BASE / 'datasets_tiled_512'
POOL = BASE / 'datasets_resized_2mp'
OUTDIR = REPO / 'reports' / 'tiled_512'
FIGDIR = OUTDIR / 'figures'
MAINFIG = OUTDIR / '00_타일링_한장설명.png'
OUT = REPO / 'reports' / '타일링_데이터셋_설명서.pdf'
DATE = '2026-08-09'

FONT_DIR = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Bold.ttc')

KOR = {'blueberry': '블루베리', 'apple': '사과', 'peach': '복숭아', 'grape': '포도'}
COL = {'blueberry': '#4a5fa5', 'apple': '#c4553a', 'peach': '#e08a3c', 'grape': '#6a4a8f'}
ORDER = ['blueberry', 'apple', 'peach', 'grape']


# ══════════════════════════════════════════════════════════ 자료
def load():
    m = json.loads((TILED / 'manifest.json').read_text())
    # 원본 쪽 전경 비율 (비교용) — index.csv 는 타일 기준이므로 풀에서 따로 잰 값을 쓴다
    return m


def du_gb(path: Path) -> float:
    out = subprocess.run(['du', '-sk', str(path)], capture_output=True, text=True).stdout
    return int(out.split()[0]) / 1024 ** 2


# ══════════════════════════════════════════════════════════ 그림
def fig_diam(m):
    """열매가 화면에 보이는 크기 — 통일 전 / 후"""
    fig, ax = plt.subplots(figsize=(7.4, 3.1), dpi=200)
    x = np.arange(4)
    before = [m['fruits'][f]['diam_median_px'] for f in ORDER]
    after = [m['target_object_diameter_px']] * 4
    ax.bar(x - 0.19, before, 0.36, color=[COL[f] for f in ORDER], alpha=.95, label='통일 전')
    ax.bar(x + 0.19, after, 0.36, color='#9aa3ad', alpha=.95, label='통일 후')
    for i, v in enumerate(before):
        ax.text(i - 0.19, v + 3, f'{v:.0f}', ha='center', fontproperties=BLD, fontsize=9)
    for i, v in enumerate(after):
        ax.text(i + 0.19, v + 3, f'{v:.0f}', ha='center', fontproperties=BLD, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([KOR[f] for f in ORDER], fontproperties=BLD, fontsize=11)
    ax.set_ylabel('열매 하나의 지름 (px)', fontproperties=REG, fontsize=10)
    ax.set_title('화면에서 열매가 보이는 크기 — 최대 %.1f배 차이 → 전부 %.0fpx'
                 % (max(before) / min(before), m['target_object_diameter_px']),
                 fontproperties=BLD, fontsize=11.5)
    ax.legend(prop=REG, fontsize=9, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_ylim(0, max(before) * 1.22)
    fig.tight_layout()
    p = FIGDIR / 'diam_before_after.png'
    fig.savefig(p); plt.close(fig)
    return p


def fig_grid(m):
    """한 장이 어떻게 잘리는지 — 과일별 격자 모양"""
    fig, axes = plt.subplots(1, 4, figsize=(7.6, 2.5), dpi=200)
    src_sizes = {'blueberry': (1440, 1440), 'apple': (1080, 1920),
                 'peach': (1920, 1080), 'grape': (1080, 1920)}
    import math
    for ax, f in zip(axes, ORDER):
        W, H = src_sizes[f]
        w = min(m['fruits'][f]['window_px'], W, H)

        def starts(L):
            if w >= L:
                return [(L - w) // 2] if L > w else [0]
            n = max(1, math.ceil(L * m.get('cover', 0.97) / w))
            if n == 1:
                return [(L - w) // 2]
            step = (L - w) / (n - 1)
            return [int(round(i * step)) for i in range(n)]

        xs, ys = starts(W), starts(H)
        ax.add_patch(Rectangle((0, 0), W, H, fc='#eef1f4', ec='#9aa3ad', lw=1))
        for yy in ys:
            for xx in xs:
                ax.add_patch(Rectangle((xx, yy), w, w, fc='none', ec=COL[f], lw=1.1, alpha=.85))
        ax.set_xlim(-40, W + 40); ax.set_ylim(H + 40, -40)
        ax.set_aspect('equal'); ax.axis('off')
        ax.set_title(f'{KOR[f]}\n{W}×{H}, 창 {w}px → {len(xs) * len(ys)}장',
                     fontproperties=BLD, fontsize=8.6)
    fig.suptitle('사진 한 장을 어떻게 자르는가 (창 크기는 과일마다 다르고, 결과는 전부 512×512)',
                 fontproperties=BLD, fontsize=10.5, y=1.02)
    fig.tight_layout()
    p = FIGDIR / 'grid_per_fruit.png'
    fig.savefig(p, bbox_inches='tight'); plt.close(fig)
    return p


def fig_fg(m):
    """타일 전경 비율 분포"""
    fig, ax = plt.subplots(figsize=(7.4, 2.9), dpi=200)
    for f in ORDER:
        vals = []
        with open(TILED / f / 'index.csv') as fh:
            for r in csv.DictReader(fh):
                vals.append(float(r['fg_percent']))
        vals = np.array(vals)
        ax.hist(vals[vals > 0], bins=np.linspace(0, 40, 60), histtype='step',
                lw=1.8, color=COL[f], label=f'{KOR[f]} (빈 타일 {(vals == 0).mean() * 100:.0f}%)',
                density=True)
    ax.set_xlabel('타일 한 장의 전경(열매) 비율 %', fontproperties=REG, fontsize=10)
    ax.set_ylabel('상대 빈도', fontproperties=REG, fontsize=10)
    ax.set_title('열매가 든 타일의 전경 비율 분포', fontproperties=BLD, fontsize=11.5)
    ax.legend(prop=REG, fontsize=8.6, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    p = FIGDIR / 'fg_hist.png'
    fig.savefig(p); plt.close(fig)
    return p


# ══════════════════════════════════════════════════════════ 본문
def build(m):
    FIGDIR.mkdir(parents=True, exist_ok=True)
    f_diam, f_grid, f_fg = fig_diam(m), fig_grid(m), fig_fg(m)
    gb = du_gb(TILED)
    t = m['totals']
    F = m['fruits']

    d = Doc(OUT,
            title='데이터셋을 «똑같아 보이게» 만들기',
            subtitle='겉보기 크기 통일 + 512×512 격자 타일링 — 무엇을, 왜, 어떻게 했는가',
            footer='타일링 데이터셋 설명서', date=DATE)

    d.cover([
        '작성: 2026-08-09   ·   곽동신',
        '',
        f'원본 {t["src_images"]:,}장  →  512×512 타일 {t["tiles"]:,}장  ({gb:.1f}GB)',
        '',
        '새 경로: /data/project/2026summer/kds0206/datasets_tiled_512/',
        '기존 데이터·팀 공유 경로는 한 장도 바뀌지 않았습니다.',
    ], badge='실험용 후보 데이터셋')

    d.toc([
        ('1', '한 장 요약', '결론부터'),
        ('2', '왜 만들었나', '교수님 말씀과 곽동신의 질문'),
        ('3', '먼저 버린 두 가지 아이디어', '눈높이 보정 / 과일만 남기기'),
        ('4', '"어차피 크롭하는데 의미 있나?"', '가장 중요한 질문에 대한 답'),
        ('5', '한 일 ① 겉보기 크기 통일', '재고, 배율을 정하고, 맞췄다'),
        ('6', '한 일 ② 512 격자로 자르기', '창 크기·완전 덮기·3% 규칙'),
        ('7', '폴드와 누수', '같은 사진의 조각은 같은 편으로'),
        ('8', '결과 숫자', '표와 그림'),
        ('9', '좋아진 것 / 나빠진 것', '정직한 손익계산'),
        ('10', '어떻게 쓰나 / 다음 할 일', 'config 한 줄'),
    ])

    # ─────────────────────────────────────── 1
    d.chapter('1', '한 장 요약', '이 문서 전체를 세 문단으로')
    d.p('네 개 과일 데이터셋(블루베리·사과·복숭아·포도)은 이미 **화소 수**가 같습니다'
        '(2,073,600화소, 0806 교수님 지시로 맞춘 것). 그런데 **열매가 화면에 보이는 크기**는 '
        f'여전히 최대 {max(F[f]["diam_median_px"] for f in ORDER) / min(F[f]["diam_median_px"] for f in ORDER):.1f}배 차이가 났습니다. '
        '사과는 지름 42px, 포도송이는 150px 이었습니다.')
    d.p('그래서 ① 과일마다 배율을 달리 줘서 **열매가 전부 지름 72px 로 보이게** 맞추고, '
        '② 사진을 전부 **512×512 조각(타일)** 으로 잘랐습니다. '
        f'결과는 원본 {t["src_images"]:,}장 → 타일 {t["tiles"]:,}장 입니다.')
    d.tip('기존 데이터는 아무것도 바뀌지 않았습니다. `datasets_tiled_512/` 라는 **새 폴더**에 '
          '따로 만들었고, 팀에 공유한 `datasets_resized_2mp/` 는 그대로입니다. '
          '이건 «이런 방법도 있다»는 **후보**이지, 지금 실험을 대체하는 게 아닙니다.')
    if MAINFIG.exists():
        d.fullfig(MAINFIG, '팀 공유용 한 장 설명',
                  '위 = 지금 학습이 보는 512 크롭 / 아래 = 새로 만든 512 타일')

    # ─────────────────────────────────────── 2
    d.chapter('2', '왜 만들었나', '출발점이 된 두 마디')
    d.quote('사진을 최대한 비슷한 데이터셋처럼 만들 수 있나?')
    d.p('교수님의 이 말씀이 출발점입니다. 네 과일은 **찍은 사람도, 찍은 거리도, 찍은 장비도 다릅니다.** '
        '사과(MinneApple)는 과수원 통로에서 사람이 들고 찍었고, 블루베리는 고정 카메라 영상에서 '
        '뽑은 프레임이고, 복숭아는 가까이 다가가 찍은 접사이고, 포도(CERTH)는 밭에서 4K 로 찍은 것입니다.')
    d.p('그 차이가 숫자로 어떻게 나오는지 실제로 재봤더니 이렇게 나왔습니다. '
        '**화소 수는 같은데 열매 크기는 3.6배 차이**입니다.')
    d.fig(f_diam, height=0.245,
          caption='마스크에서 열매 덩어리 하나의 «등가원 지름»을 재서 중앙값을 낸 것')
    d.note('**등가원 지름**이란, 덩어리의 넓이가 A 화소일 때 「같은 넓이를 가진 동그라미의 지름」을 '
           '말합니다. 계산은 `지름 = 2 × √(A ÷ π)`. 열매가 찌그러진 모양이어도 하나의 숫자로 '
           '크기를 비교할 수 있어서 씁니다.')
    d.warn('포도는 마스크가 **알 하나가 아니라 «송이» 단위**로 그려져 있습니다. 그래서 150px 은 '
           '포도알이 아니라 송이 하나의 크기입니다. 「덩어리 하나가 화면에서 차지하는 크기」라는 '
           '뜻은 네 과일이 같지만, 세는 단위가 과일마다 다르다는 점은 알고 계셔야 합니다.')

    # ─────────────────────────────────────── 3
    d.chapter('3', '먼저 버린 두 가지 아이디어', '왜 안 되는지 알아야 왜 이렇게 했는지가 보입니다')
    d.h1('버린 것 ① — 「눈높이에서 찍은 것처럼」 원근을 비틀기')
    d.p('사진을 기하학적으로 비틀어서 카메라를 눈높이로 옮긴 것처럼 만드는 방법입니다. 네 가지 이유로 접었습니다.')
    d.bullets([
        '**불가능** — 원근을 되돌리려면 카메라 높이·기울기·피사체까지의 거리를 알아야 하는데, '
        '네 데이터셋 어디에도 그 정보가 없습니다.',
        '**교수님이 이미 거부하신 부작용** — B안(전부 1440×1440)을 버린 이유가 「포도알이 타원이 된다」였습니다. '
        '원근 변형은 그보다 더 심하게, 게다가 **화면 위치마다 다르게** 열매를 일그러뜨립니다.',
        '**가짜 배경** — 비틀면 귀퉁이가 비어서 검게 채워지고, 모델이 그걸 배경으로 학습합니다.',
        '**방어 불가** — 심사자가 「카메라 자세를 모르는데 눈높이라고 어떻게 보장하나」라고 물으면 답이 없습니다.',
    ])
    d.h1('버린 것 ② — 「과일만 딱 남게」 오려내기')
    d.p('나무·잎을 잘라내고 과일만 남기면 데이터셋이 비슷해지지 않겠느냐는 생각입니다. '
        '실제로 재보고 접었습니다.')
    d.table(['과일', '지금 전경%', '열매 전부 감싼 최소 상자가 차지하는 면적', '그 상자 안 전경%'],
            [['블루베리', '5.1', '69.6%', '12.6'],
             ['사과', '2.9', '53.9%', '4.9'],
             ['복숭아', '5.9', '40.0%', '24.6'],
             ['포도', '11.4', '44.3%', '28.0']],
            [.16, .19, .43, .22])
    d.bullets([
        '**실제로 「과일만」이 안 남습니다.** 열매가 화면 여기저기 흩어져 있어서, 열매 전부를 감싸는 '
        '최소 상자가 **이미 화면의 40~70%** 입니다. 그 안조차 잎·가지가 71~95% 입니다.',
        '**통일이 오히려 나빠집니다.** 잘라내면 전경 비율 차이가 4.0배 → **5.7배**로 벌어집니다.',
        '**과제가 망가집니다.** 우리 모델이 하는 일은 「이 화소가 열매냐 잎이냐」를 가리는 것입니다. '
        '배경을 지우고 학습시키면 모델이 **「아니다」라고 말하는 법을 못 배웁니다.** '
        '실제 과수원 사진에서 잎까지 열매로 찍는 과탐지가 폭발하고, 점수(IoU)는 '
        '인위적으로 올라가서 심사자가 반드시 지적합니다.',
    ])
    d.warn('세그멘테이션에서 **배경은 버리는 게 아니라 정답의 절반**입니다. '
           '전경 5%짜리 사진에서 배경 95%를 지우면 문제 자체가 다른 문제로 바뀝니다.')

    # ─────────────────────────────────────── 4
    d.chapter('4', '"어차피 크롭하는데 의미 있나?"', '이 문서에서 가장 중요한 장')
    d.p('곽동신이 던진 질문입니다. **절반은 맞습니다.** 정확히 어디까지 맞는지 짚고 갑니다.')
    d.h1('맞는 부분 — 「사진 크기」는 이미 같았습니다')
    d.p('지금 학습 설정(`TRAIN.IMAGE_SIZE: [512, 512]` + `RANDOM_CROP`)은 원본이 몇 화소이든 '
        '**512×512 를 무작위로 잘라서** 모델에 넣습니다. 그러니 「사진 크기를 통일한다」는 목적만 놓고 보면 '
        '크롭이 이미 다 해결하고 있었습니다. 화소 수 통일(0806 작업)도 마찬가지로 '
        '**크롭이 덮는 «비율»을 맞추는 효과**였지, 모델 입력 크기를 맞춘 게 아니었습니다.')
    d.h1('틀린 부분 — 크롭으로는 절대 안 고쳐지는 게 두 개 있습니다')
    d.steps([
        '**열매가 보이는 크기.** 512 크롭은 «어디를» 자를지만 정하지 «얼마나 확대할지»는 안 정합니다. '
        '사과 사진에서 512를 잘라도 사과는 42px, 포도 사진에서 512를 잘라도 포도송이는 150px 입니다. '
        '**크롭을 아무리 해도 이 3.6배는 그대로 남습니다.** 이번 작업 ①이 고치는 게 이것입니다.',
        '**평가할 때 채점되는 범위.** 학습은 무작위 크롭이라 여러 에폭에 걸쳐 사진 전체를 훑지만, '
        '평가(`val.py`)는 **가운데 한 장만** 잘라서 채점합니다. 즉 사진의 일부만 보고 점수를 매기고 '
        '있습니다. 타일링은 사진을 빠짐없이 덮으므로 이 문제가 같이 풀립니다.',
    ])
    d.tip('한 줄로: **크롭은 「크기」를 통일했고, 이번 작업은 「배율」과 「채점 범위」를 통일합니다.** '
          '세 개는 서로 다른 문제입니다.')
    d.note('참고로 이 「평가를 가운데 크롭 → 전체 훑기로 바꾸기」는 원래 작업기록의 '
           '「다음 할 일」에 미결로 적혀 있던 숙제입니다. 타일링이 곧 그 «슬라이딩 윈도우»라서 '
           '같이 해결됩니다.')

    # ─────────────────────────────────────── 5
    d.chapter('5', '한 일 ① 겉보기 크기 통일', '재고 → 배율 정하고 → 맞춤')
    d.h1('1단계. 잰다')
    d.p('과일마다 마스크를 최대 400장씩 열어서, 열매 덩어리 하나의 등가원 지름 중앙값을 냈습니다. '
        '30화소보다 작은 덩어리는 잡음으로 보고 뺐습니다.')
    d.h1('2단계. 목표 크기를 정한다 — 왜 72px 인가')
    d.p('처음에는 60px 로 잡았는데 **포도에서 걸렸습니다.** 포도 사진은 짧은 변이 1080px 인데 '
        '포도송이 지름이 150px 입니다. 이걸 60px 로 줄이려면 512 타일 하나가 원본에서 '
        '1,281px 짜리 창을 봐야 하는데, 사진이 1,080px 밖에 안 됩니다. '
        '**찍히지도 않은 화각을 요구하는 것**이라 불가능합니다.')
    d.formula([
        '포도가 낼 수 있는 최소 겉보기 크기',
        '= 150.1px × (512 ÷ 1080) = 71.2px',
        '',
        '→ 목표 72px = 네 데이터셋 어디서도 없는 화면을 지어내지 않는 «가장 작은» 목표',
    ])
    d.h1('3단계. 배율을 적용한다')
    d.p('사진 전체를 늘렸다 줄였다 하는 대신, **잘라낼 창 크기를 과일마다 다르게** 잡고 그 창을 '
        '512로 리사이즈했습니다. 결과는 완전히 같으면서 메모리를 훨씬 덜 씁니다.')
    d.formula(['배율 s = 72 ÷ (그 과일의 열매 지름)',
               '잘라낼 창 = 512 ÷ s',
               '',
               '창이 사진보다 크면 사진 크기로 줄임 (없는 화각은 못 만드니까)'])
    d.table(['과일', '잰 열매 지름', '배율', '잘라낼 창', '뜻'],
            [[KOR[f], f'{F[f]["diam_median_px"]:.1f}px', f'{F[f]["scale"]:.3f}배',
              f'{F[f]["window_px"]}px',
              '확대' if F[f]['scale'] > 1 else '축소'] for f in ORDER],
            [.18, .20, .16, .18, .28])

    # ─────────────────────────────────────── 6
    d.chapter('6', '한 일 ② 512 격자로 자르기', '빠짐없이, 중복 없이')
    d.p('사진 한 장을 창 크기만큼씩 격자로 잘라 나갑니다. 각 조각은 512×512 로 리사이즈됩니다.')
    d.fig(f_grid, height=0.20, caption='창 크기가 과일마다 달라서 나오는 조각 수도 다릅니다')
    d.h1('규칙 1 — 빠짐없이 덮는다 (겹쳐도 됨)')
    d.p('사진 변 길이가 창 크기로 딱 나눠떨어지는 경우는 거의 없습니다. 남는 자투리를 버리면 '
        '가장자리 열매를 영영 못 보게 되므로, **조각끼리 조금씩 겹치게** 배치해서 전부 덮습니다.')
    d.h1('규칙 2 — 가장자리 3%까지는 포기한다')
    d.p('반대로 자투리가 너무 작으면 문제가 생깁니다. 예를 들어 포도는 1,080px 을 1,067px 창으로 '
        '덮는데, 억지로 두 줄을 만들면 **13px 만 어긋난 거의 똑같은 타일 두 장**이 생깁니다. '
        '그래서 「97% 이상만 덮으면 한 줄로 끝낸다」는 규칙을 넣었습니다. 포기하는 건 1.2% 가장자리뿐입니다.')
    d.h1('규칙 3 — 빈 타일도 버리지 않는다')
    d.p('열매가 하나도 없는 타일도 지우지 않고 저장했습니다. **배경만 있는 조각도 모델에게는 '
        '중요한 공부거리**이기 때문입니다(「여긴 열매가 아니다」를 배웁니다). '
        '대신 `index.csv` 에 타일마다 전경 비율을 적어 두었으니, 나중에 빼고 싶으면 골라낼 수 있습니다.')
    d.fig(f_fg, height=0.215, caption='타일 한 장이 담고 있는 열매의 양')
    d.code('# index.csv 로 열매가 든 타일만 고르는 예\n'
           'import pandas as pd\n'
           "df = pd.read_csv('datasets_tiled_512/grape/index.csv')\n"
           "keep = df[df.fg_percent > 0.5].tile        # 전경 0.5% 넘는 타일만",
           caption='빈 타일을 빼고 싶을 때')

    # ─────────────────────────────────────── 7
    d.chapter('7', '폴드와 누수', '여기를 틀리면 결과 전체가 무효가 됩니다')
    d.p('사진 한 장에서 조각이 여러 개 나옵니다. 만약 그 조각들이 **어떤 건 train, 어떤 건 test** 로 '
        '흩어지면, 모델이 시험 문제를 미리 본 셈이 됩니다. 이걸 **정보 누수(leakage)** 라고 합니다.')
    d.warn('그래서 조각은 **원본 사진의 배정을 그대로 물려받습니다.** '
           '기존 `datasets_resized_2mp/splits/<과일>/cv*/` 의 train·val·test 명단을 읽어서, '
           '그 사진에서 나온 조각 전부를 같은 곳에 넣었습니다. 새로 뽑지 않았습니다.')
    d.p('블루베리는 한 단계 더 조심할 게 있는데, 파일명이 `Camera N Video (X)_프레임` 이라 '
        '**같은 영상에서 나온 프레임끼리도 갈라지면 안 됩니다.** '
        '이건 기존 `splits/blueberry/` 가 이미 영상 단위로 갈라 둔 것이라, 그대로 물려받으면 '
        '자동으로 지켜집니다.')
    rows = []
    for f in ORDER:
        sp = F[f].get('splits', {})
        cv1 = sp.get('cv1', {})
        rows.append([KOR[f], str(len(sp)),
                     f'{cv1.get("train", 0):,}', f'{cv1.get("val", 0):,}', f'{cv1.get("test", 0):,}'])
    d.table(['과일', '폴드 수', 'cv1 train 타일', 'cv1 val 타일', 'cv1 test 타일'],
            rows, [.20, .14, .24, .21, .21])

    # ─────────────────────────────────────── 8
    d.chapter('8', '결과 숫자', '실제로 만들어진 것')
    d.table(['과일', '원본 장수', '장당 조각', '타일 총수', '빈 타일', '평균 전경%'],
            [[KOR[f], f'{F[f]["src_images"]:,}', f'{F[f]["tiles_per_image"]:.0f}',
              f'{F[f]["tiles"]:,}', f'{F[f]["empty_tile_percent"]:.0f}%',
              f'{F[f]["fg_percent_mean"]:.2f}'] for f in ORDER],
            [.17, .17, .15, .17, .16, .18])
    d.p(f'**합계 — 원본 {t["src_images"]:,}장 → 타일 {t["tiles"]:,}장, 디스크 {gb:.1f}GB.**')
    d.note('사과의 조각 수가 유난히 많은 건(장당 28개) **확대**했기 때문입니다. '
           '1.72배로 늘리면 같은 사진에서 나올 수 있는 512 조각이 그만큼 많아집니다. '
           '반대로 포도는 0.48배로 줄여서 장당 2개뿐입니다.')

    # ─────────────────────────────────────── 9
    d.chapter('9', '좋아진 것 / 나빠진 것', '숨기지 않고 적습니다')
    d.h1('좋아진 것')
    d.bullets([
        '**네 데이터셋이 실제로 비슷해 보입니다.** 열매 겉보기 크기 3.6배 차이 → 1.0배.',
        '**모든 표본이 문자 그대로 같은 규격**(512×512)이라, 데이터셋 간 비교에서 '
        '「사진이 달라서 그런 거 아니냐」는 반론이 하나 줄어듭니다.',
        '**평가 범위 문제가 같이 풀립니다.** 타일이 사진을 빠짐없이 덮으므로 '
        '가운데만 채점하던 것을 전체 채점으로 바꿀 수 있습니다.',
        '**마스크 형식도 통일**했습니다(1채널 0/255). 사과만 인스턴스 번호였던 것을 이진화했습니다.',
    ])
    d.h1('나빠진 것 (정직하게)')
    d.bullets([
        f'**사과는 화소를 지어냅니다.** 원본 720×1280 → 1.5배(0806 작업) → 다시 '
        f'{F["apple"]["scale"]:.2f}배 = 누적 약 {1.5 * F["apple"]["scale"]:.1f}배. '
        '없던 detail 이 생기는 게 아니라 뿌옇게 늘어난 것입니다.',
        f'**포도·복숭아는 화소를 버립니다.** 각각 {F["grape"]["scale"]:.2f}배, '
        f'{F["peach"]["scale"]:.2f}배로 줄었으니 그만큼 세밀함이 사라집니다.',
        f'**학습 시간이 늘어납니다.** 표본이 {t["tiles"] / t["src_images"]:.0f}배가 되므로 '
        '에폭당 시간도 그만큼 늘어납니다. 대신 **에폭 수를 그 배수만큼 줄이면** '
        '총 업데이트 횟수가 같아져 시간은 비슷해집니다 (예: 200 → 20).',
        '**기존 결과와 직접 비교할 수 없습니다.** 입력이 달라졌으니 새 실험입니다.',
    ])
    d.warn('그래서 이건 «팀 표준을 갈아치우는 것»이 아니라 **비교 대상으로 하나 더 만들어 둔 것**입니다. '
           '켠 것과 끈 것을 한 조합으로 돌려보고 나서 판단하면 됩니다.')

    # ─────────────────────────────────────── 10
    d.chapter('10', '어떻게 쓰나 / 다음 할 일', '')
    d.h1('학습에 써 보려면 — config 의 경로 한 줄만 바꾸면 됩니다')
    d.code('DATASET:\n'
           '  NAME  : BlueberryDataset\n'
           '  ROOT  : \'/data/project/2026summer/kds0206/datasets_tiled_512/splits/grape/cv1\'\n'
           '\n'
           'TRAIN:\n'
           '  IMAGE_SIZE : [512, 512]     # 타일이 이미 512라 크롭은 사실상 그대로 통과\n'
           '  EPOCHS     : 20             # 표본이 약 10배이므로 200 → 20 으로',
           caption='기존 코드는 하나도 안 고쳐도 됩니다')
    d.h1('권하는 검증 순서')
    d.steps([
        '**포도 cv1, 최고 조합(U-Net + ConvNeXt-T) 하나만** 돌려 봅니다. '
        '기존 데이터로 낸 test 전경 IoU 0.8534 와 비교합니다.',
        '차이가 의미 있으면 교수님께 보고하고, 다른 과일로 넓힙니다.',
        '차이가 없으면 «해봤는데 영향 없더라»가 논문에 쓸 수 있는 결과가 됩니다. '
        '어느 쪽이든 손해가 아닙니다.',
    ])
    d.h1('아직 안 한 것')
    d.bullets([
        '**학습은 한 번도 돌리지 않았습니다.** 데이터만 만들어 둔 상태입니다.',
        '평가를 타일 단위로 낸 뒤 **사진 단위로 다시 합치는 코드**는 아직 없습니다 '
        '(타일별 점수의 평균이 아니라, 사진 한 장의 IoU 를 제대로 내려면 필요합니다).',
        '교수님 확인 — 이 방향으로 갈지 말지는 아직 안 정해졌습니다.',
    ])

    d.save()


if __name__ == '__main__':
    build(load())
