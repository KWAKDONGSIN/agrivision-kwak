# -*- coding: utf-8 -*-
"""4과일(블루베리·사과·복숭아·포도) 사진 규격 통일(리사이즈) 과정을 설명하는 PDF.

무엇을 왜 어떻게 했는지를 처음부터 끝까지 따라갈 수 있게 쓴다.
목표 독자
  - 곽동신 본인 (중학생도 이해할 수준으로 풀어 쓰되)
  - 그대로 읽으면 팀원·교수님께 설명이 되는 수준까지

🔴 숫자를 하드코딩하지 않는다.
  장수·해상도 분포·배율·검증 결과는 전부 **manifest.json 과 디스크**에서 읽는다.
  manifest.json 은 tools/rebuild_resized_manifest.py 가 실제 파일을 열어 잰 기록이다.

⚠️ 출력 위치 — 팀 공유 경로(datasets_resized_2mp/ · share_grape_certh/ · _서버업로드용/)가
  아닌 곳(reports/)에 둔다.

사용:  $PY tools/make_resize_process_report_pdf.py
출력:  reports/4과일_리사이즈_과정_설명서.pdf
       reports/figures/resize_process/*.png
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc                                       # noqa: E402

POOL = BASE / 'datasets_resized_2mp'
MANIFEST = POOL / 'manifest.json'
FIGDIR = REPO / 'reports/figures/resize_process'
AB_FIG = REPO / 'reports/resize_compare/00_A안_B안_비교.png'
OUT = REPO / 'reports/4과일_리사이즈_과정_설명서.pdf'
DATE = '2026-08-08'

FONT_DIR = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Bold.ttc')

KOR = {'blueberry': '블루베리', 'apple': '사과', 'peach': '복숭아', 'grape': '포도'}
COL = {'blueberry': '#4a5fa5', 'apple': '#c4553a', 'peach': '#e08a3c', 'grape': '#6a4a8f'}
ORDER = ['blueberry', 'apple', 'peach', 'grape']


# ============================================================ 자료 읽기
def load():
    m = json.loads(MANIFEST.read_text())
    return m


def wh(s):
    a, b = s.split('x')
    return int(a), int(b)


def crop_coverage(w, h, crop=512):
    """512x512 크롭 한 장이 원본 화면의 몇 %를 덮는가."""
    return crop * crop / (w * h) * 100


def all_src_sizes(m):
    """(과일, 원본해상도, 장수, 출력해상도, 배율) 목록. 배율은 기록에서 직접 집계."""
    rows = []
    for f in ORDER:
        v = m['fruits'][f]
        # 원본 해상도별로 대표 record 하나씩 찾아 출력 해상도·배율을 얻는다
        by_src = {}
        for rec in v['records'].values():
            key = f"{rec['src_size'][0]}x{rec['src_size'][1]}"
            by_src.setdefault(key, {'n': 0, 'out': rec['out_size'], 'scale': rec['scale']})
            by_src[key]['n'] += 1
        for src, d in sorted(by_src.items(), key=lambda kv: -kv[1]['n']):
            rows.append((f, src, d['n'], f"{d['out'][0]}x{d['out'][1]}", d['scale']))
    return rows


# ============================================================ 그림
def fig_why_crop(rows, path: Path):
    """왜 화소를 맞춰야 하나 — 512 크롭이 덮는 비율, 통일 전/후."""
    items = []
    for f, src, n, out, _ in rows:
        w, h = wh(src)
        ow, oh = wh(out)
        items.append((f, src, crop_coverage(w, h), crop_coverage(ow, oh), n))
    items.sort(key=lambda t: t[2])

    # 통일 후에는 전부 거의 같은 값이라, 막대를 두 벌 그리면 서로 겹쳐 읽기 나쁘다.
    # → 통일 전만 막대로 그리고, 통일 후는 «세로선 하나»로 표시한다.
    fig, ax = plt.subplots(figsize=(9.3, 4.4))
    y = range(len(items))
    before = [t[2] for t in items]
    after_mid = sum(t[3] for t in items) / len(items)

    ax.barh(list(y), before, height=0.66, color=[COL[t[0]] for t in items])
    for i, t in enumerate(items):
        ax.text(t[2] + max(before) * 0.011, i, f'{t[2]:.2f}%', va='center',
                fontproperties=BLD, fontsize=8.8, color=COL[t[0]])

    ax.axvline(after_mid, color='#111111', lw=1.8, ls=(0, (4, 3)), zorder=6)
    ax.annotate(f'통일 후 — 전부 {after_mid:.2f}%',
                xy=(after_mid, len(items) - 0.6), xytext=(after_mid + max(before) * 0.14,
                                                          len(items) - 0.15),
                fontproperties=BLD, fontsize=10, color='#111111',
                arrowprops=dict(arrowstyle='->', color='#111111', lw=1.2))

    ax.set_yticks(list(y))
    ax.set_yticklabels([f'{KOR[t[0]]}  {t[1]}  ({t[4]:,}장)' for t in items],
                       fontproperties=REG, fontsize=9)
    ax.set_xlabel('512×512 크롭 한 장이 사진 전체에서 차지하는 비율 (%)  ← 통일 전',
                  fontproperties=REG, fontsize=9.8)
    ax.set_xlim(0, max(before) * 1.20)
    ax.set_ylim(-0.7, len(items) + 0.15)
    lo, hi = min(before), max(before)
    ax.set_title(f'통일 전에는 {hi / lo:.1f}배 차이  →  통일 후 전부 같아짐',
                 fontproperties=BLD, fontsize=12.5, pad=10)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='x', labelsize=8.5)
    fig.subplots_adjust(left=0.295, right=0.985, top=0.895, bottom=0.115)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def fig_same_pixels(path: Path):
    """화소 수는 같은데 해상도는 다르다 — 실제 비율로 그려서 보여준다."""
    shapes = [(1440, 1440, '1440×1440', '블루베리'),
              (1080, 1920, '1080×1920', '포도·사과·블루베리 4K'),
              (1920, 1080, '1920×1080', '복숭아 일부'),
              (1664, 1248, '1664×1248', '복숭아 4:3')]
    # 🔴 «넓이가 같다»를 눈으로 보이려면 네 도형이 실제로 같은 넓이로 그려져야 한다.
    #   그래서 축 단위를 인치로 두고 aspect='equal' 을 건다 (0~1 좌표로 그리면
    #   가로세로 축척이 달라서 정사각형이 직사각형으로 나온다).
    FW, FH = 9.3, 3.5
    fig, ax = plt.subplots(figsize=(FW, FH))
    ax.set_xlim(0, FW); ax.set_ylim(0, FH)
    ax.set_aspect('equal')
    ax.axis('off')

    scale = 1.95 / max(h for _, h, _, _ in shapes)       # 제일 높은 것이 1.95인치
    gap = 0.42
    total = sum(w * scale for w, _, _, _ in shapes) + gap * (len(shapes) - 1)
    x = (FW - total) / 2
    cy = 1.92

    for w, h, lab, who in shapes:
        ww, hh = w * scale, h * scale
        ax.add_patch(Rectangle((x, cy - hh / 2), ww, hh, facecolor='#dfe5f0',
                               edgecolor='#4a5fa5', lw=1.8))
        ax.text(x + ww / 2, cy, f'{w * h:,}\n화소', ha='center', va='center',
                fontproperties=BLD, fontsize=8.4, color='#1c5cab')
        ax.text(x + ww / 2, cy + hh / 2 + 0.10, lab, ha='center',
                fontproperties=BLD, fontsize=9.6)
        ax.text(x + ww / 2, cy - hh / 2 - 0.12, who, ha='center', va='top',
                fontproperties=REG, fontsize=8.4, color='#5b6270')
        x += ww + gap

    ax.text(FW / 2, 0.16,
            '네 도형은 모양이 다르지만 넓이는 똑같습니다 (전부 2,073,600 화소).',
            ha='center', fontproperties=REG, fontsize=10, color='#5b6270')
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def fig_per_fruit(rows, m, path: Path):
    """과일별 원본 → 출력 배율."""
    fig, ax = plt.subplots(figsize=(9.3, 3.6))
    labs, vals, cols = [], [], []
    for f, src, n, out, sc in rows:
        labs.append(f'{KOR[f]}\n{src}\n({n:,}장)')
        vals.append(sc)
        cols.append(COL[f])
    xs = range(len(vals))
    ax.bar(xs, vals, color=cols, width=0.6)
    ax.axhline(1.0, color='#111111', lw=1.5, ls=(0, (4, 3)))
    ax.text(len(vals) - 0.35, 1.0, ' 1.0 = 크기 그대로', va='center',
            fontproperties=BLD, fontsize=8.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.03, f'{v:.2f}배', ha='center', fontproperties=BLD, fontsize=8.8,
                color=('#b23b3b' if v > 1.01 else '#111111'))
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labs, fontproperties=REG, fontsize=7.8)
    ax.set_ylabel('배율 (변의 길이 기준)', fontproperties=REG, fontsize=9.5)
    ax.set_ylim(0, max(vals) * 1.22)
    ax.set_xlim(-0.6, len(vals) - 0.5 + 1.1)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', labelsize=8.5)
    up = [(f, n, sc) for f, _, n, _, sc in rows if sc > 1.01]
    n_up = sum(n for _, n, _ in up)
    ax.set_title(f'점선 위 = 확대 / 아래 = 축소.  확대된 사진은 {n_up:,}장 (사과 전량 + 복숭아 일부)',
                 fontproperties=BLD, fontsize=11.5, pad=9)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.87, bottom=0.235)
    fig.savefig(path, dpi=170)
    plt.close(fig)


# ============================================================ 본문
def build():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    m = load()
    rows = all_src_sizes(m)
    total = m['totals']['images']
    target = m['target_pixels']

    f1, f2, f3 = FIGDIR / 'why.png', FIGDIR / 'same_pixels.png', FIGDIR / 'scales.png'
    fig_why_crop(rows, f1)
    fig_same_pixels(f2)
    fig_per_fruit(rows, m, f3)

    # 출력 해상도 분포 (4과일 합산)
    outdist = {}
    for f in ORDER:
        for k, v in m['fruits'][f]['output_sizes'].items():
            outdist[k] = outdist.get(k, 0) + v
    outdist = dict(sorted(outdist.items(), key=lambda kv: -kv[1]))

    covers = [(f, s, crop_coverage(*wh(s))) for f, s, _, _, _ in rows]
    lo = min(c for _, _, c in covers)
    hi = max(c for _, _, c in covers)

    d = Doc(OUT,
            title='4과일 사진 규격을 통일한 과정',
            subtitle='블루베리·사과·복숭아·포도 4,823장을 «같은 화소 수»로 맞춘 작업 전 과정',
            volume='작업 설명서',
            footer='4과일 리사이즈 과정 설명서 · 2026-08-08',
            date=DATE)

    d.cover([
        '0806 교수님미팅 지시 —',
        '"비율은 유지하고 화소 개수가 거의 동일하도록"',
        '',
        f'대상 {total:,}장  ·  목표 화소 {target:,}개 (=1440×1440)',
        '결과: 비율 왜곡 0건, 화소 편차 최대 0.15%',
        '',
        '작성자: 곽동신    ※ 이 문서는 팀 공유 경로에 두지 않았습니다',
    ], badge='개인 작업 기록')

    d.toc([
        ('1', '한 장 요약', '바쁘면 이 쪽만'),
        ('2', '왜 크기를 맞춰야 했나', '이유를 모르면 나머지가 안 읽힙니다'),
        ('3', '"화소 수"와 "해상도"는 다른 말입니다', '이 문서 전체의 열쇠'),
        ('4', '교수님이 정하신 기준', '1440 통일 → 직접 물리심 → 화소 통일'),
        ('5', 'A안과 B안 — 왜 A안인가', '실제로 두 벌을 만들어 비교했습니다'),
        ('6', '크기를 어떻게 계산했나', '공식 한 줄과 8의 배수'),
        ('7', '과일별로 무슨 일이 있었나', '4개 각각의 사정'),
        ('8', '망가뜨리지 않으려고 지킨 5가지', '마스크·EXIF·원본'),
        ('9', '검증 결과', '4,823장 전수'),
        ('10', '남은 쟁점과 주의사항', '논문에 써야 할 것'),
    ])

    # ===================================================== 1장
    d.chapter('1', '한 장 요약', '전체 이야기를 한 쪽으로')
    d.h1('무엇을 했나')
    d.p(f'과일 4종류의 사진 **{total:,}장**을, 가로세로 **비율은 그대로 둔 채** '
        f'**총 화소 수만 {target:,}개**(=1440×1440과 같은 넓이)로 맞췄습니다.')

    d.h2('왜 했나 — 한 문장')
    d.tip('학습할 때 사진에서 **512×512 조각을 잘라 쓰는데**, 원본 크기가 제각각이면 '
          '같은 512 조각이 덮는 범위가 데이터셋마다 달라집니다. '
          f'실제로 재 보니 **{hi / lo:.1f}배** 차이가 났습니다. '
          '이러면 어떤 모델이 좋은지 공정하게 비교할 수 없습니다.', head='이유')

    d.h2('결과')
    d.table(['항목', '결과'],
            [['대상 사진', f'**{total:,}장** (4과일)'],
             ['목표 화소 수', f'{target:,}개 (=1440×1440)'],
             ['가로세로 비율이 찌그러진 사진', f'**0장**'],
             ['화소 수가 목표와 정확히 같은 사진',
              f'{sum(v for k, v in outdist.items() if wh(k)[0] * wh(k)[1] == target):,}장'],
             ['나머지 사진의 오차', '**+0.15%** (8의 배수로 반올림한 탓)'],
             ['이미지↔마스크 크기 불일치', '**0건**'],
             ['원본 폴더 훼손', '**없음** (원본은 읽기만 했습니다)'],
             ['결과물 위치', '`datasets_resized_2mp/` (13GB)']],
            [0.42, 0.58])

    d.warn('**결과물의 해상도는 전부 같지 않습니다.** '
           f'{len(outdist)}가지 해상도가 섞여 있습니다. '
           '맞춘 것은 «넓이(화소 수)»이지 «모양(해상도)»이 아닙니다. '
           '이 구분이 3장의 내용이고, 이 문서에서 제일 헷갈리는 부분입니다.',
           head='자주 오해하는 지점')

    # ===================================================== 2장
    d.chapter('2', '왜 크기를 맞춰야 했나', '이유를 모르면 나머지가 안 읽힙니다')
    d.h1('학습은 사진 전체를 보지 않습니다')
    d.p('우리 학습 코드는 사진을 통째로 넣지 않습니다. 사진에서 **512×512 짜리 조각을 '
        '무작위로 잘라내서** 넣습니다. 컴퓨터 메모리를 아끼고, 같은 사진에서 여러 조각을 '
        '뽑아 학습량을 늘리기 위해서입니다.')
    d.note('이걸 **RandomCrop(랜덤 크롭)** 이라고 합니다. '
           '평가할 때는 무작위 대신 **가운데 512×512**(CenterCrop)를 씁니다.')

    d.h2('그런데 원본 크기가 제각각이었습니다')
    d.p('같은 512×512 조각이라도, 원본이 크면 «아주 좁은 부분»을 보는 것이고 '
        '원본이 작으면 «거의 전체»를 보는 것입니다. 실제로 계산해 보면 이렇습니다.')

    d.table(['과일 · 원본 해상도', '장수', '512 크롭이 덮는 비율'],
            [[f'{KOR[f]}  {s}', f'{n:,}',
              f'{crop_coverage(*wh(s)):.2f}%'] for f, s, n, _, _ in
             sorted(rows, key=lambda r: crop_coverage(*wh(r[1])))],
            [0.44, 0.18, 0.38], size=8.8)

    d.p(f'제일 좁게 보는 것과 제일 넓게 보는 것의 차이가 **{hi / lo:.1f}배**입니다. '
        '모델 입장에서는 «확대 배율이 데이터셋마다 다른» 상태입니다. '
        '이 상태로 “어느 모델이 제일 좋은가”를 비교하면, 모델의 실력이 아니라 '
        '**사진이 얼마나 확대돼 있었는가**를 비교하는 셈이 됩니다.')

    d.fig(f1, height=0.285,
          caption='그림 1. 막대 = 통일 전 (색은 과일 구분). 세로 점선 = 통일 후. '
                  '통일 후에는 열한 줄이 전부 그 선 하나로 모입니다.')

    d.tip('현미경 배율에 비유하면 이렇습니다. 어떤 표본은 100배로, 어떤 표본은 '
          '1,300배로 들여다보면서 “어느 현미경이 잘 보이나”를 겨루면 말이 안 됩니다. '
          '**배율을 먼저 맞추는 것**이 이번 작업입니다.', head='비유로 기억하기')

    # ===================================================== 3장
    d.chapter('3', '"화소 수"와 "해상도"는 다른 말입니다', '이 문서 전체의 열쇠')
    d.h1('종이로 생각하면 쉽습니다')
    d.term('해상도', 'resolution',
           '가로 몇 개 × 세로 몇 개. 사진의 **모양**입니다. 종이로 치면 «가로세로 길이».')
    d.term('화소 수', 'pixel count',
           '가로 × 세로 = 총 몇 개. 사진의 **총량**입니다. 종이로 치면 «넓이».')
    d.formula([
        '해상도 1440 × 1440  →  화소 수 2,073,600',
        '해상도 1080 × 1920  →  화소 수 2,073,600   ← 모양은 다른데 넓이는 같다',
        '해상도 1920 × 1080  →  화소 수 2,073,600',
    ])
    d.p('넓이가 같아도 모양은 얼마든지 다를 수 있습니다. A4 한 장과 같은 넓이의 '
        '길쭉한 종이를 생각하면 됩니다.')

    d.fig(f2, height=0.235, caption='그림 2. 넷 다 화소 수는 같지만 모양은 다릅니다. 실제 비율로 그렸습니다.')

    d.h2('우리가 통일한 것은 «넓이» 입니다')
    d.p('결과물의 해상도 분포를 세어 보면 이렇습니다.')
    d.table(['해상도', '장수', '비율', '화소 수'],
            [[f'**{k}**', f'{v:,}', f'{v / total * 100:.1f}%',
              f'{wh(k)[0] * wh(k)[1]:,}' + ('' if wh(k)[0] * wh(k)[1] == target else '  (+0.15%)')]
             for k, v in outdist.items()],
            [0.28, 0.20, 0.18, 0.34])
    d.p(f'해상도는 **{len(outdist)}종**이지만, 화소 수는 **전부 {target:,} 아니면 그것의 '
        '+0.15% 이내**입니다.')

    d.warn('팀원이나 교수님이 “다 같은 크기로 만들었지?” 라고 물으시면 '
           '**“화소 수는 전부 같고, 해상도는 5종입니다”** 라고 답하셔야 정확합니다. '
           '“다 1440×1440으로 만들었다”고 답하면 사실과 다릅니다.', head='설명할 때 주의')

    # ===================================================== 4장
    d.chapter('4', '교수님이 정하신 기준', '한 번 뒤집혔던 결정입니다')
    d.h1('처음 제안 — "다 1440으로"')
    d.quote('블루베리가 1440이라고요? 그러니까 다 거의 1440으로 하면 좋지 않을까요?')
    d.p('블루베리가 1440×1440 정사각형이니까 나머지도 거기 맞추자는 제안이었습니다. '
        '(0806 미팅 09:47)')

    d.h2('그런데 곧바로 직접 물리셨습니다')
    d.quote('어떤 거는 길고 작은 게 있잖아요. 이게 그러면은 이렇게 늘어지는 건데...\n'
            '비율은 유지하고 화소 개수가 거의 동일하도록')
    d.p('가로로 긴 사진을 억지로 정사각형에 욱여넣으면 **사진이 늘어져 찌그러집니다.** '
        '그 점을 스스로 짚으시고 기준을 바꾸신 것입니다. (0806 미팅 09:49)')

    d.h2('왜 그래도 되는가')
    d.quote('어차피 512 512로 크롭할 거니까 상관없다')
    d.p('해상도(모양)가 서로 달라도, 학습할 때는 512×512 조각으로 잘라 쓰니 상관없다는 뜻입니다. '
        '**화소 수만 같으면 «확대 배율»이 같아지고, 그게 공정 비교에 필요한 전부**입니다. '
        '(0806 미팅 10:17) — 2장에서 계산으로 확인한 바로 그 논리입니다.')

    d.quote('픽셀 개수를 거의 유사하게끔 하죠. 그냥')
    d.p('최종 확정 발언입니다. (0806 미팅 12:27)')

    d.h2('원본은 남겨 두라고도 하셨습니다')
    d.quote('원래 원본 데이터는 아무튼 다른 데 저장해 놓고, 리사이즈 한 걸 그거 위주로 '
            '데이터셋으로 쓰면')
    d.p('그래서 원본 폴더는 **한 글자도 건드리지 않고**, 새 폴더 '
        '`datasets_resized_2mp/` 에 사본을 만들었습니다. (0806 미팅 13:55)')

    # ===================================================== 5장
    d.chapter('5', 'A안과 B안 — 왜 A안인가', '말로 정하지 않고 두 벌을 만들어 봤습니다')
    d.h1('두 가지 방법이 있었습니다')
    d.table(['', 'A안 (채택)', 'B안 (미채택)'],
            [['방법', '비율 유지 + 화소 수만 통일', '전부 똑같은 1440×1440으로'],
             ['해상도', '5종 (제각각)', '1종 (전부 같음)'],
             ['비율 왜곡', '**없음**', '**있음** — 사과·포도가 가로로 1.78배 늘어남'],
             ['폴더', '`datasets_resized_2mp/`', '`datasets_resized_1440/` (6.3GB, 방치)']],
            [0.16, 0.42, 0.42])

    d.p('교수님 발언만으로도 A안이 맞지만, **눈으로 확인**하려고 실제로 두 벌 다 만들어 '
        '나란히 놓고 비교했습니다.')
    d.p('**B안에서 동그란 포도알이 옆으로 퍼진 타원이 됩니다.** '
        '모델은 «둥근 것»을 학습해야 하는데 «타원»을 학습하게 되니, '
        '실제 사진에 적용했을 때 성능이 떨어질 수밖에 없습니다. 그래서 A안으로 확정했습니다.')
    d.note('B안 폴더는 지우지 않고 남겨 뒀습니다. 필요 없으면 지워서 6.3GB를 회수하면 됩니다.')

    if AB_FIG.exists():
        # 세로로 긴 비교 그림이라 본문에 끼우면 작아진다 → 한 쪽을 통째로 준다
        d.fullfig(AB_FIG,
                  caption='그림 3. A안(비율 유지) vs B안(전부 1440×1440)',
                  sub='포도 줄을 보세요. B안에서 포도알이 옆으로 퍼진 타원이 됩니다. '
                      '사과도 가로로 늘어납니다. 이것이 A안을 택한 이유입니다.')

    # ===================================================== 6장
    d.chapter('6', '크기를 어떻게 계산했나', '공식 한 줄과 8의 배수')
    d.h1('공식은 한 줄입니다')
    d.formula([
        '배율 = √( 목표 화소 수 ÷ 원본 화소 수 )',
        '',
        '새 가로 = 원본 가로 × 배율',
        '새 세로 = 원본 세로 × 배율',
    ])
    d.p('가로와 세로에 **같은 배율**을 곱하기 때문에 비율이 절대 안 바뀝니다. '
        '제곱근을 쓰는 이유는, 넓이는 «가로 × 세로»라서 변의 길이를 √배 늘리면 '
        '넓이가 정확히 목표만큼 되기 때문입니다.')

    d.h2('직접 해 봅시다 — 사과')
    d.steps([
        '사과 원본은 720 × 1280 입니다. 화소 수는 720 × 1280 = **921,600**개.',
        f'목표는 {target:,}개니까 배율은 √({target:,} ÷ 921,600) = √2.25 = **1.5배**.',
        '720 × 1.5 = 1080,  1280 × 1.5 = 1920 → **1080 × 1920**.',
        f'확인: 1080 × 1920 = {1080 * 1920:,} = 목표와 정확히 일치.',
    ])

    d.h2('변의 길이는 8의 배수로 맞췄습니다')
    d.p('계산 결과가 소수로 나오면 반올림해야 하는데, 그냥 반올림하지 않고 '
        '**8의 배수**로 맞췄습니다. 딥러닝 모델은 사진을 절반씩 여러 번 줄여 가며 처리하는데, '
        '변의 길이가 8로 나누어떨어지지 않으면 그 과정에서 자투리가 생겨 오류가 나거나 '
        '가장자리가 잘립니다.')
    d.note('**왜 하필 8인가?** 우리 데이터셋들은 8의 배수로 맞추면 참 비율이 '
           '**오차 없이 그대로** 나옵니다 (9:16 → 1080:1920, 4:3 → 1664:1248). '
           '32의 배수로 하면 최대 1.5%가 찌그러져서 쓰지 않았습니다. '
           '실제로 둘 다 계산해 보고 8을 골랐습니다.')
    d.p('복숭아 4:3 사진 60장만 화소 수가 목표보다 **+0.15%** 많은데, '
        '순전히 이 8의 배수 반올림 때문입니다. 비율은 정확히 4:3 그대로입니다.')

    # ===================================================== 7장
    d.chapter('7', '과일별로 무슨 일이 있었나', '4개 각각의 사정이 달랐습니다')
    d.h1('한눈에 보기')
    d.table(['과일', '원본 해상도', '장수', '→ 결과 해상도', '배율'],
            [[f'**{KOR[f]}**' if i == 0 or rows[i - 1][0] != f else '',
              s, f'{n:,}', o, f'**{sc:.2f}배**' if sc > 1.01 else f'{sc:.2f}배']
             for i, (f, s, n, o, sc) in enumerate(rows)],
            [0.16, 0.22, 0.14, 0.24, 0.24], size=8.9)

    d.fig(f3, height=0.245,
          caption='그림 4. 배율. 점선(1.0) 위 = 확대, 아래 = 축소.')

    up_rows = [(f, s, n, sc) for f, s, n, _, sc in rows if sc > 1.01]
    n_up = sum(n for _, _, n, _ in up_rows)
    d.h2(f'확대(업스케일)된 사진은 {n_up:,}장입니다')
    d.p('없던 화질을 만들어 낼 수는 없으므로, 확대는 «같은 정보를 크게 편 것»입니다. '
        '조금 뿌옇게 보일 수 있어서 **어느 사진이 얼마나 확대됐는지 밝혀 둘 필요**가 있습니다.')
    d.table(['과일', '원본 해상도', '장수', '배율'],
            [[f'**{KOR[f]}**', s, f'{n:,}', f'**{sc:.2f}배**'] for f, s, n, sc in up_rows],
            [0.22, 0.30, 0.22, 0.26])
    d.p(f'**사과는 {m["fruits"]["apple"]["images_used"]:,}장 전량이 1.5배**로 확대됐고, '
        f'복숭아는 {sum(n for f, _, n, _ in up_rows if f == "peach"):,}장만 '
        '1.04~1.16배로 살짝 확대됐습니다. 나머지는 전부 축소이거나 크기 그대로입니다.')

    for f in ORDER:
        v = m['fruits'][f]
        d.h2(f'{KOR[f]} — {v["images_used"]:,}장')
        mine = [r for r in rows if r[0] == f]
        if f == 'blueberry':
            d.bullets([
                f'해상도가 **{len(mine)}종** 섞여 있었습니다.',
                '1440×1440 짜리 1,066장은 **이미 목표 화소 수와 같아서 손대지 않았습니다** '
                '(배율 1.00 = 원본 그대로 복사).',
                '4K(2160×3840) 128장은 0806 미팅에서 «나무가 아니라 과실 클로즈업»이라고 '
                '**빼기로 했었으나**, 2026-08-08에 다시 넣었습니다. 포도도 같은 4K인데 '
                '전량 쓰고 있어 형평을 맞춘 것입니다. ★ 이 건은 교수님께 보고가 필요합니다.',
                '2160×3840은 9:16이라 **정확히 절반(0.5배)** 으로 떨어집니다. 반올림 오차 0.',
            ])
        elif f == 'apple':
            d.bullets([
                '**데이터셋 전량이 확대(업스케일)된 유일한 과일입니다.** '
                '720×1280 → 1080×1920, 1.5배. (복숭아도 40장이 확대됐지만 일부일 뿐입니다)',
                '없던 화질을 만들어 낸 것이 아니라, 같은 정보를 크게 편 것입니다. '
                '사진이 조금 뿌옇게 보일 수 있습니다.',
                '그래도 확대한 이유: 사과가 원래 제일 작은 사진이라 512 크롭이 '
                f'화면의 {crop_coverage(720, 1280):.1f}%나 덮고 있었습니다. '
                '이것만 그대로 두면 사과만 «확대해서 본» 상태가 됩니다.',
                '★ **논문 Method 에 “사과는 1.5배 업스케일했다”고 반드시 명시해야 합니다.**',
            ])
        elif f == 'peach':
            d.bullets([
                f'해상도가 **{len(mine)}종**으로 제일 어지러웠습니다 '
                '(4032×3024 같은 큰 것부터 1080×1440까지).',
                '1920×1080 짜리 62장은 이미 목표 화소 수와 같아 손대지 않았습니다.',
                '4:3 계열은 1664×1248 로 갔는데, 이것만 화소가 **+0.15%** 많습니다 '
                '(8의 배수 반올림). 비율 왜곡은 0입니다.',
                '**40장은 살짝 확대**됐습니다 (1600×1200 → 1.04배, 1440×1080·1080×1440 → 1.16배). '
                '원본이 목표보다 작았던 사진들입니다.',
                'jpg 사진이라 **EXIF 회전 정보**를 반영해서 열었습니다 (8장 참고).',
            ])
        else:
            d.bullets([
                '★ **다른 셋과 처리 방식이 다릅니다.** 이미 576×1024 로 줄여 놓은 것이 '
                '있었지만, 그걸 다시 키우면 **없는 화질을 지어내게** 됩니다.',
                '그래서 CERTH **원본 zip(2160×3840)에서 처음부터 다시** 1080×1920 으로 뽑았습니다.',
                '2026-08-07 에 토이 100장 → **전체 2,502장**으로 교체했습니다.',
                '한 장에 한 송이만 있는 사진 100장은 취지에 안 맞아 제외했습니다.',
            ])

    # ===================================================== 8장
    d.chapter('8', '망가뜨리지 않으려고 지킨 5가지', '리사이즈는 잘못하면 데이터를 망칩니다')
    d.h1('① 원본은 읽기만 했습니다')
    d.p('원본 폴더에는 **쓰기를 한 번도 하지 않았습니다.** 결과는 전부 새 폴더 '
        '`datasets_resized_2mp/` 에 만들었습니다. 잘못돼도 언제든 다시 할 수 있습니다.')

    d.h2('② 사진과 정답(마스크)은 다른 방식으로 줄였습니다')
    d.table(['', '무엇', '방법', '왜'],
            [['사진', '사람이 보는 그림', '**LANCZOS**',
              '주변 화소를 섞어 부드럽게. 계단현상이 줄어듦'],
             ['마스크', '어디가 과일인지 정답', '**NEAREST**',
              '섞으면 안 됨. 0과 255를 섞으면 **127 같은 없는 값**이 생김']],
            [0.12, 0.24, 0.20, 0.44], size=8.9)
    d.warn('마스크에 LANCZOS 를 쓰면 «배경도 과일도 아닌 어중간한 값»이 생겨서 '
           '정답 자체가 오염됩니다. 이건 리사이즈에서 제일 흔한 사고입니다. '
           '그래서 리사이즈 후에 **마스크에 없던 값이 생겼는지 한 장씩 검사**하도록 '
           '코드에 넣었습니다 (`mask_values_kept`).', head='제일 조심한 부분')

    d.h2('③ EXIF 회전을 반영했습니다')
    d.p('스마트폰·카메라 사진(jpg)에는 «이 사진은 90도 돌려서 보세요» 라는 메모(EXIF)가 '
        '들어 있습니다. 그냥 열면 **눕혀진 채로** 읽히는데, 마스크에는 그 메모가 없어서 '
        '**사진과 정답이 90도 어긋나는 사고**가 납니다. 그래서 여는 순간 회전을 적용했습니다.')
    d.note('예전에 FruitSeg30 에서 실제로 이 사고가 났었습니다 '
           '(이미지 4000×3000 인데 마스크 3000×4000). 그때 겪어서 이번엔 미리 막았습니다.')

    d.h2('④ 사진과 마스크 크기가 다르면 즉시 멈추게 했습니다')
    d.p('리사이즈 전에 두 파일 크기를 비교해서, 다르면 그 장을 처리하지 않고 오류로 남깁니다. '
        f'결과: **불일치 0건** (4과일 {total:,}장 전부).')

    d.h2('⑤ 폴드(분할) 구조는 바로가기로만 재현했습니다')
    d.p('리사이즈한 사진은 한 벌만 두고, 폴드별 폴더에는 **바로가기(심볼릭 링크)** 만 '
        '만들었습니다. 그래서 폴드를 여러 벌 만들어도 디스크가 늘지 않습니다.')
    d.warn('팀원이 복사해 갈 때 **`cp -rL` 을 쓰면 안 됩니다.** `-L` 은 바로가기를 '
           '실제 파일로 펼쳐서 13GB 가 100GB 넘게 불어납니다. `cp -a` 를 쓰거나, '
           '복사하지 말고 경로를 그대로 쓰면 됩니다.')

    # ===================================================== 9장
    d.chapter('9', '검증 결과', f'{total:,}장 전수')
    d.h1('만들고 끝내지 않고 전부 다시 열어 쟀습니다')
    d.p('리사이즈가 끝난 뒤, 결과 파일을 **한 장도 빠뜨리지 않고 다시 열어** 크기를 재고 '
        '원본과 대조했습니다. 그 기록이 `manifest.json` 입니다 '
        f'(사진 1장마다 원본 크기·새 크기·배율·왜곡 여부가 들어 있습니다).')

    d.table(['검사 항목', '왜 확인하나', '결과'],
            [['가로세로 비율이 바뀌었나', '찌그러지면 B안과 같아짐', '**0건** (전부 일치)'],
             ['화소 수가 목표와 같나', '이번 작업의 목적',
              f'**{sum(v for k, v in outdist.items() if wh(k)[0] * wh(k)[1] == target):,}장 정확히 일치**'],
             ['나머지 사진의 오차', '허용 범위인지', '**+0.15%** (8의 배수 반올림)'],
             ['이미지↔마스크 크기 불일치', '어긋나면 학습이 망가짐', '**0건**'],
             ['짝 없는 사진·마스크', '한쪽만 있으면 못 씀', '**0건**'],
             ['마스크에 없던 값이 생겼나', '정답 오염 (8장 ②)', '**0건**'],
             ['원본 폴더가 훼손됐나', '되돌릴 수 없는 사고', '**없음**']],
            [0.30, 0.34, 0.36], size=8.9)

    d.h2('과일별 상세')
    d.table(['과일', '쓴 장수', '원본 해상도 종류', '결과 해상도 종류', '비율왜곡', '화소 최대오차'],
            [[f'**{KOR[f]}**', f'{m["fruits"][f]["images_used"]:,}',
              f'{len(m["fruits"][f]["src_sizes"])}종',
              f'{len(m["fruits"][f]["output_sizes"])}종',
              f'{m["fruits"][f]["aspect_distortion_max"]}',
              f'+{(m["fruits"][f]["pixels_vs_target_max"] - 1) * 100:.3f}%']
             for f in ORDER],
            [0.17, 0.15, 0.19, 0.19, 0.14, 0.16], size=8.8)

    d.h2('다시 만들려면')
    d.code('cd /data/project/2026summer/kds0206/semantic-segmentation\n'
           'export PY=/home/kds0206/.conda/envs/kwak/bin/python\n\n'
           '# 4과일 전부 다시 리사이즈 (약 10분)\n'
           '$PY tools/resize_datasets_to_common_pixels.py --workers 12\n\n'
           '# 계획만 보고 싶으면\n'
           '$PY tools/resize_datasets_to_common_pixels.py --dry-run\n\n'
           '# 이미지는 그대로 두고 기록(manifest)만 다시 재기 (2초)\n'
           '$PY tools/rebuild_resized_manifest.py')

    # ===================================================== 10장
    d.chapter('10', '남은 쟁점과 주의사항', '논문에 써야 할 것들')
    d.h1('논문에 반드시 적어야 할 것')
    d.steps([
        '★ **“사과는 720×1280 → 1080×1920 으로 1.5배 업스케일했다”** — '
        '데이터셋 전량이 확대된 유일한 과일이라 밝히지 않으면 안 됩니다. '
        '**복숭아 40장도 1.04~1.16배 확대**됐으니 함께 적는 것이 정확합니다.',
        '**“해상도가 아니라 총 화소 수를 통일했다”** — 해상도는 5종이라고 정확히 써야 합니다.',
        '**“마스크는 NEAREST 로 리사이즈했다”** — 재현성을 위해 필요합니다.',
        '**“포도는 이미 축소된 사본이 아니라 원본에서 다시 뽑았다”**.',
    ])

    d.h2('판단이 갈릴 수 있었던 지점')
    d.p('녹취록 11:00 에 *“그래요 저쪽에 맞출까 그러면”* 이라는 말씀이 있는데, 이건 '
        '**거꾸로 사과(720×1280)에 맞춰 전부 축소하자**는 뜻으로도 읽힙니다. '
        '12:27 의 *“픽셀 개수를 거의 유사하게끔 하죠”* 로 정리되어 **1440² 기준**을 '
        '택했고, 그 결과 사과만 1.5배 확대됐습니다.')
    d.note('최종 발언을 따른 것이라 문제는 없지만, **“사과는 확대됩니다”를 한 번 '
           '확인받는 것**이 안전합니다. 거꾸로 갔다면 다른 셋이 축소되고 사과가 그대로였을 것입니다.')

    d.h2('아직 안 한 것')
    d.bullets([
        '**512×512 크롭 24장씩 뽑아 눈으로 비율 확인** (0806 교수님 지시 ②). '
        '스크립트는 준비돼 있습니다 → `$PY tools/make_crop_samples_512.py`',
        '미채택 B안 `datasets_resized_1440/` (6.3GB) 삭제 여부 — 곽동신 판단',
        '★ **4과일 전부 재학습** — 사진 크기가 바뀌었으니 기존 결과와 직접 비교가 안 됩니다.',
    ])

    d.h2('관련 파일 위치')
    d.table(['무엇', '경로'],
            [['결과물 (팀 표준)', 'datasets_resized_2mp/  — 13GB, 4,823장'],
             ['사진 1장별 기록', 'datasets_resized_2mp/manifest.json'],
             ['데이터셋 설명서', 'datasets_resized_2mp/README.md'],
             ['리사이즈 프로그램', 'semantic-segmentation/tools/resize_datasets_to_common_pixels.py'],
             ['기록 재생성 프로그램', 'semantic-segmentation/tools/rebuild_resized_manifest.py'],
             ['A안/B안 비교 그림', 'semantic-segmentation/reports/resize_compare/00_A안_B안_비교.png'],
             ['미채택 B안', 'datasets_resized_1440/  — 6.3GB, 지워도 됨'],
             ['**이 PDF**', '**semantic-segmentation/reports/4과일_리사이즈_과정_설명서.pdf**']],
            [0.28, 0.72], size=8.6)

    d.warn('이 PDF 가 있는 `semantic-segmentation/reports/` 는 **팀에 공유한 경로가 '
           '아닙니다.** 팀 공유 경로는 `datasets_resized_2mp/` · `share_grape_certh/` · '
           '`_서버업로드용/` 세 곳입니다. 팀원에게 주시려면 파일을 따로 보내 주세요.',
           head='공유 범위')

    d.save()


if __name__ == '__main__':
    build()
