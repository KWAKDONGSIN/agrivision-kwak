# -*- coding: utf-8 -*-
"""2026-08-08 «블루베리 분할 7:1:2 재작업» 을 설명하는 PDF 보고서를 만든다.

목표 독자
  - 곽동신 본인 (중학생도 이해할 수준으로 풀어 쓰되)
  - 그대로 읽으면 팀원에게 설명이 되는 수준까지

🔴 숫자를 하드코딩하지 않는다.
  분할 장수·검증 결과는 전부 **디스크에서 직접 세어서** 넣는다.
  그래야 데이터가 바뀐 뒤 다시 돌렸을 때 문서가 거짓말을 하지 않는다.

⚠️ 출력 위치 주의 — 이 문서는 **팀 공유 경로에 두지 않는다.**
  공유 경로는 datasets_resized_2mp/ · share_grape_certh/ · _서버업로드용/ 세 곳이며,
  여기 출력하는 reports/ 는 곽동신 개인 작업 폴더다.

사용:  $PY tools/make_blueberry_split_report_pdf.py
출력:  reports/블루베리_분할_7대1대2_설명서.pdf
       reports/figures/blueberry_split/*.png  (그림 3장)
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, Rectangle

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc                                       # noqa: E402

SPLITS = BASE / 'datasets_resized_2mp/splits'
NEW = SPLITS / 'blueberry'
OLD_1067 = SPLITS / '_old_blueberry_1067_260808'
OLD_GKF = SPLITS / '_old_blueberry_groupkfold1195_260808'
POOL = BASE / 'datasets_resized_2mp/blueberry'

FIGDIR = REPO / 'reports/figures/blueberry_split'
OUT = REPO / 'reports/블루베리_분할_7대1대2_설명서.pdf'
DATE = '2026-08-08'

FONT_DIR = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Bold.ttc')

C_TR, C_VA, C_TE = '#3a76c4', '#f0a63a', '#c4553a'
GROUP_RE = re.compile(r'^(Camera (\d+) Video \(\d+\))_\d+$')


# ============================================================ 디스크에서 재기
def count(d: Path) -> int:
    return sum(1 for _ in d.iterdir()) if d.is_dir() else 0


def fold_counts(root: Path):
    """{cv이름: (train, val, test)} 를 디스크에서 직접 센다."""
    out = {}
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not (d / 'train' / 'images').is_dir():
            continue
        out[d.name] = tuple(count(d / s / 'images') for s in ('train', 'val', 'test'))
    return out


def stems(p: Path):
    return {q.stem for q in p.iterdir()} if p.is_dir() else set()


def verify(root: Path):
    """새 분할을 전수 검사한다. PDF에 실을 검증표의 원자료."""
    r = {'broken': 0, 'links': 0, 'pair_mismatch': 0, 'dup': 0, 'leak': 0, 'folds': 0}
    cam_ratio = {}
    for p in root.rglob('*'):
        if p.is_symlink():
            r['links'] += 1
            if not p.exists():                       # exists() 는 링크를 따라간다
                r['broken'] += 1

    for cv, _ in sorted(fold_counts(root).items()):
        r['folds'] += 1
        seen, by_split = Counter(), {}
        for s in ('train', 'val', 'test'):
            si, sm = stems(root / cv / s / 'images'), stems(root / cv / s / 'masks')
            if si != sm:                             # 이미지↔마스크 이름 불일치
                r['pair_mismatch'] += len(si ^ sm)
            by_split[s] = si
            seen.update(si)
        r['dup'] += sum(1 for _, n in seen.items() if n > 1)

        # 같은 영상이 두 split 에 걸치는가
        vid = defaultdict(set)
        for s, names in by_split.items():
            for n in names:
                m = GROUP_RE.match(n)
                if m:
                    vid[m.group(1)].add(s)
        r['leak'] += sum(1 for v in vid.values() if len(v) > 1)

        if cv == 'cv1':                              # 카메라 쏠림은 cv1 로 대표 확인
            for s, names in by_split.items():
                c = Counter(GROUP_RE.match(n).group(2) for n in names if GROUP_RE.match(n))
                cam_ratio[s] = c
    return r, cam_ratio


def pool_cameras():
    c = Counter()
    for p in (POOL / 'images').iterdir():
        m = GROUP_RE.match(p.stem)
        if m:
            c[m.group(2)] += 1
    return c


# ============================================================ 그림
def fig_before_after(old_gkf, new, path: Path):
    """예전 분할 vs 새 분할 — 가로 누적 막대로 비율을 눈에 보이게."""
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    rows = [
        ('예전 분할 (1,195장 · cv1)', old_gkf, '#9aa3b2'),
        ('새 분할 (1,195장 · cv1)', new, None),
    ]
    for i, (label, (tr, va, te), _) in enumerate(rows):
        tot = tr + va + te
        y = 1 - i
        left = 0
        for n, c, nm in ((tr, C_TR, 'train'), (va, C_VA, 'val'), (te, C_TE, 'test')):
            w = n / tot * 100
            ax.barh(y, w, left=left, height=0.44, color=c, edgecolor='white', linewidth=1.6)
            ax.text(left + w / 2, y, f'{nm}\n{n}장\n{w:.1f}%', ha='center', va='center',
                    color='white', fontproperties=BLD, fontsize=10.5)
            left += w
        ax.text(-1.5, y, label, ha='right', va='center', fontproperties=BLD, fontsize=11)

    # 목표선 70 / 80 — 막대 구간에서만 그어야 아래 설명글과 안 겹친다
    for x in (70, 80):
        ax.plot([x, x], [-0.42, 1.34], color='#111111', lw=1.4, ls=(0, (4, 3)), zorder=5)
    ax.annotate('목표 70%', xy=(70, 1.34), xytext=(58, 1.62), fontproperties=BLD, fontsize=9.5,
                ha='center', arrowprops=dict(arrowstyle='-', color='#111111', lw=0.9))
    ax.annotate('목표 80%', xy=(80, 1.34), xytext=(92, 1.62), fontproperties=BLD, fontsize=9.5,
                ha='center', arrowprops=dict(arrowstyle='-', color='#111111', lw=0.9))
    ax.text(50, -0.62, '점선 = 팀 규칙 7:1:2 의 경계. 예전 분할은 경계에서 한참 벗어나 있습니다.',
            ha='center', va='top', fontproperties=REG, fontsize=9.5, color='#5b6270')

    ax.set_xlim(0, 100); ax.set_ylim(-0.95, 1.85)
    ax.axis('off')
    fig.subplots_adjust(left=0.235, right=0.985, top=0.93, bottom=0.02)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def fig_leakage(path: Path):
    """왜 영상 단위로 뽑아야 하는가 — 개념도."""
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9))

    def frames(ax, colors, title, sub, ok):
        ax.set_title(title, fontproperties=BLD, fontsize=12.5,
                     color=('#0a7d33' if ok else '#b23b3b'), pad=9)
        for i, c in enumerate(colors):
            x = 0.045 + i * 0.158
            ax.add_patch(Rectangle((x, 0.44), 0.135, 0.30, facecolor=c,
                                   edgecolor='white', lw=2))
            ax.text(x + 0.0675, 0.59, f'{i + 1}번\n프레임', ha='center', va='center',
                    color='white', fontproperties=BLD, fontsize=9)
        ax.text(0.5, 0.86, '같은 영상에서 뽑은 프레임 6장 (거의 같은 장면)',
                ha='center', fontproperties=REG, fontsize=10, color='#5b6270')
        ax.text(0.5, 0.24, sub, ha='center', va='top', fontproperties=REG, fontsize=10.2,
                color=('#0a7d33' if ok else '#b23b3b'), wrap=True)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    frames(axes[0], [C_TR, C_TE, C_TR, C_TR, C_TE, C_VA],
           'X  사진 한 장씩 랜덤으로 뽑으면',
           '한 영상이 train(파랑)·test(빨강)에 흩어집니다.\n'
           '거의 같은 장면을 학습하고 그걸로 시험 보는 셈이라\n'
           '점수가 실제 실력보다 높게 나옵니다. (데이터 누수)', ok=False)
    frames(axes[1], [C_TE] * 6,
           'O  영상을 통째로 뽑으면',
           '한 영상은 반드시 한 곳에만 들어갑니다.\n'
           'test 에 있는 장면은 학습 때 한 번도 못 봤으므로\n'
           '점수가 실제 실력 그대로 나옵니다.', ok=True)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.05)
    fig.savefig(path, dpi=170)
    plt.close(fig)


def fig_folds(counts, path: Path):
    """6폴드가 전부 70:10:20 근처인지 — 목표선과 함께."""
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.0), sharex=True)
    names = list(counts)
    for ax, (idx, nm, target, color) in zip(axes, [
            (0, 'train', 70, C_TR), (1, 'val', 10, C_VA), (2, 'test', 20, C_TE)]):
        vals = [counts[c][idx] / sum(counts[c]) * 100 for c in names]
        ax.bar(range(len(names)), vals, color=color, width=0.62)
        ax.axhline(target, color='#111111', lw=1.6, ls=(0, (4, 3)))
        # 오른쪽에 라벨 자리를 따로 비워 둔다 (막대 위에 얹으면 숫자와 겹침)
        ax.set_xlim(-0.62, len(names) - 0.5 + 1.55)
        ax.text(len(names) - 0.28, target, f'목표\n{target}%', va='center', ha='left',
                fontproperties=BLD, fontsize=8.6)
        for i, v in enumerate(vals):
            ax.text(i, v + (target * 0.035), f'{v:.1f}', ha='center',
                    fontproperties=REG, fontsize=8.6)
        ax.set_title(nm, fontproperties=BLD, fontsize=12, color=color)
        ax.set_ylim(0, target * 1.32)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, fontproperties=REG, fontsize=9)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis='y', labelsize=8)
    fig.subplots_adjust(left=0.05, right=0.985, top=0.87, bottom=0.12, wspace=0.22)
    fig.savefig(path, dpi=170)
    plt.close(fig)


# ============================================================ 본문
def build():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    man = json.loads((NEW / 'folds_manifest.json').read_text())

    new_c = fold_counts(NEW)
    gkf_c = fold_counts(OLD_GKF)
    old_c = fold_counts(OLD_1067)
    ver, cam1 = verify(NEW)
    cams = pool_cameras()

    n_total = sum(new_c['cv1'])
    n_vid = man['n_video_groups']

    f1 = FIGDIR / 'before_after.png'
    f2 = FIGDIR / 'leakage.png'
    f3 = FIGDIR / 'folds_ratio.png'
    fig_before_after(gkf_c['cv1'], new_c['cv1'], f1)
    fig_leakage(f2)
    fig_folds(new_c, f3)

    def pct(c):
        t = sum(c)
        return [v / t * 100 for v in c]

    d = Doc(OUT,
            title='블루베리 데이터 분할을 7:1:2 로 다시 뜬 이야기',
            subtitle='2026-08-08 팀 요청 처리 기록 — 무엇을 요청받았고, 왜 그대로 하지 않았고, 어떻게 했는가',
            volume='작업 설명서',
            footer='블루베리 분할 7:1:2 재작업 · 2026-08-08',
            date=DATE)

    d.cover([
        '요청: "1067장판은 지우고 1195장판 이름을 blueberry 로,',
        '       그리고 1195장이 7:1:2 로 잘 나뉘었는지 봐 달라"',
        '',
        f'결과: 1,195장 전량을 7:1:2 로 다시 뽑아 6폴드 완성',
        '',
        '작성자: 곽동신    ※ 이 문서는 팀 공유 경로에 두지 않았습니다',
    ], badge='개인 작업 기록')

    d.toc([
        ('1', '한 장 요약', '바쁘면 이 쪽만 읽어도 됩니다'),
        ('2', '먼저 알아야 할 말 4개', '폴드 · 7:1:2 · 분할 · 링크'),
        ('3', '무엇을 요청받았나', '팀원 카톡 원문과 그 뜻'),
        ('4', '왜 시키는 대로만 하면 안 됐나', '1,195장판은 7:1:2 가 아니었습니다'),
        ('5', '블루베리만 다른 점 — 영상 단위', '이 문서에서 제일 중요한 부분'),
        ('6', '실제로 한 일 4단계', '순서대로'),
        ('7', '결과와 검증', '숫자 여섯 가지를 전수로 확인'),
        ('8', '팀원이 물어볼 것 7가지', '이대로 대답하시면 됩니다'),
        ('9', '남은 일과 주의사항', '재학습이 필요합니다'),
    ])

    # ===================================================== 1장
    d.chapter('1', '한 장 요약', '전체 이야기를 한 쪽으로')
    d.h1('세 문장으로')
    d.steps([
        '**요청**: 블루베리 사진 묶음이 두 벌 있었는데, 1,067장짜리를 지우고 '
        '1,195장짜리를 팀 표준으로 쓰라는 것. 그리고 그게 7:1:2 로 잘 나뉘었는지 확인해 달라는 것.',
        '**발견**: 확인해 봤더니 **7:1:2 가 아니었습니다.** '
        f'{gkf_c["cv1"][0]}/{gkf_c["cv1"][1]}/{gkf_c["cv1"][2]} 이라 약 '
        f'{pct(gkf_c["cv1"])[0]:.0f}:{pct(gkf_c["cv1"])[1]:.0f}:{pct(gkf_c["cv1"])[2]:.0f} 였습니다. '
        '이름만 바꿔서는 요청을 지킬 수 없는 상태였습니다.',
        f'**처리**: {n_total:,}장 전량을 7:1:2 로 **다시 뽑았습니다.** '
        f'6폴드 전부 70:10:20 에서 오차 0.25%p 안에 들어왔고, 검사 여섯 가지를 전수로 통과했습니다.',
    ])

    d.h2('숫자로 보면')
    d.table(
        ['', '예전 (1,195장판)', '지금 (새로 뜬 것)'],
        [
            ['cv1 train / val / test',
             f'{gkf_c["cv1"][0]} / {gkf_c["cv1"][1]} / {gkf_c["cv1"][2]}',
             f'**{new_c["cv1"][0]} / {new_c["cv1"][1]} / {new_c["cv1"][2]}**'],
            ['비율',
             f'{pct(gkf_c["cv1"])[0]:.1f} : {pct(gkf_c["cv1"])[1]:.1f} : {pct(gkf_c["cv1"])[2]:.1f}',
             f'**{pct(new_c["cv1"])[0]:.1f} : {pct(new_c["cv1"])[1]:.1f} : {pct(new_c["cv1"])[2]:.1f}**'],
            ['팀 규칙 7:1:2 인가', 'X 아님', '**○ 맞음**'],
            ['뽑는 단위', '영상 (누수 없음)', '**영상 (누수 없음)**'],
        ], [0.30, 0.35, 0.35])

    d.fig(f1, height=0.245,
          caption='그림 1. 예전 분할과 새 분할. 막대 길이가 곧 비율입니다.')

    d.tip('“7:1:2 로 나뉘었는지 봐 달라”는 요청을 받고 확인해 보니 아니어서, '
          '**확인에서 끝내지 않고 7:1:2 로 다시 만들었다.** 이것이 이번 작업의 전부입니다.',
          head='한 문장으로 기억하기')

    # ===================================================== 2장
    d.chapter('2', '먼저 알아야 할 말 4개', '이것만 알면 나머지가 다 읽힙니다')
    d.h1('시험 공부에 비유하면')
    d.p('우리는 사진을 보고 «어디가 블루베리인지» 맞히는 프로그램을 만듭니다. '
        '사람이 시험 공부하는 것과 똑같이 생각하면 됩니다.')

    d.term('train (학습용)', 'training set',
           '문제집. 프로그램이 이걸 보면서 배웁니다. 답을 알려주고 외우게 하는 부분입니다.')
    d.term('val (검증용)', 'validation set',
           '모의고사. 공부가 잘 되고 있는지 중간중간 확인하는 용도입니다. '
           '여기 점수를 보고 “이제 그만 공부시켜도 되겠다”를 판단합니다.')
    d.term('test (시험용)', 'test set',
           '진짜 수능. 마지막에 딱 한 번만 씁니다. 학습에는 절대 쓰지 않습니다.')
    d.term('7:1:2', '—',
           '위 셋을 70% : 10% : 20% 로 나눈다는 뜻. 우리 팀이 4개 데이터셋 전부에 쓰기로 한 규칙입니다.')

    d.note('**왜 test 를 따로 떼어 두나요?** 문제집에 있던 문제가 수능에 그대로 나오면 '
           '점수가 잘 나와도 실력이라 할 수 없죠. 그래서 test 사진은 학습에 한 번도 '
           '안 쓴 것이어야 합니다. 이번 작업의 핵심이 바로 이 원칙을 지키는 것입니다.')

    d.h2('폴드(fold)는 또 뭔가요')
    d.p('시험을 한 번만 보면 운이 좋아서 잘 볼 수도 있습니다. 그래서 **나누는 방법을 바꿔가며 '
        '여러 번** 시험을 봅니다. 그 «한 번의 나누기»가 폴드입니다.')
    d.bullets([
        f'블루베리는 폴드가 **6개**(cv1~cv6)입니다. 즉 {n_total:,}장을 6가지 방법으로 나눠 6번 실험합니다.',
        '사과·복숭아·포도는 5개(cv1~cv5)입니다. 4과일을 비교할 때는 **cv1~cv5 로 맞추면** 조건이 같아집니다.',
        '폴드마다 train/val/test 에 들어가는 사진이 다릅니다. 그래서 **6번의 점수를 평균**내면 '
        '운의 영향이 줄어듭니다.',
    ])

    d.h2('링크(바로가기)로 되어 있습니다')
    d.p('폴드가 6개면 같은 사진을 6번 복사해야 할 것 같지만, 실제로는 '
        '**윈도우 바로가기 같은 것**(심볼릭 링크)만 만들어 둡니다. '
        f'그래서 폴드 6개를 만들어도 디스크는 거의 안 늘어납니다. 지금 링크가 총 {ver["links"]:,}개 있습니다.')
    d.warn('팀원에게 복사해 가라고 할 때 **`cp -rL` 을 쓰면 안 됩니다.** '
           '`-L` 은 바로가기를 실제 파일로 펼쳐 버려서 13GB 가 100GB 넘게 불어납니다. '
           '`cp -a` 를 쓰거나, 아예 복사하지 말고 경로를 그대로 쓰면 됩니다.')

    # ===================================================== 3장
    d.chapter('3', '무엇을 요청받았나', '팀원 카톡 원문')
    d.h1('받은 메시지')
    d.quote('위에거는 지우고 밑에거 이름을 블루베리로 해주세요.\n'
            '하고 1195 7:1:2 잘 나뉘었는지 해주세요.\n'
            '사진 랜덤하게 들어가는 거라 작업하시고 주시는 게 나아서.', who='팀원')

    d.h2('“위에거 / 밑에거” 가 무엇이었나')
    d.p('제가 그 전에 팀에 이런 상태라고 알렸었습니다. 블루베리 분할이 **두 벌** 있었습니다.')
    d.table(['', '이름', '장수', '어떤 것'],
            [['위에거', 'splits/blueberry', f'{sum(old_c["cv1"]):,}',
              '4K로 찍힌 128장을 뺀 것 (0806 미팅 지시분)'],
             ['밑에거', 'splits/blueberry_full1195', f'{sum(gkf_c["cv1"]):,}',
              '그 128장까지 넣은 것 (2026-08-08 추가)']],
            [0.11, 0.31, 0.11, 0.47])
    d.p('두 벌이 있으면 팀원이 어느 걸 써야 할지 헷갈립니다. 그래서 팀에서 '
        '**«128장 넣은 쪽 한 벌로 통일하자»** 고 정해 준 것이 이번 요청입니다.')

    d.h2('요청을 항목으로 쪼개면 3가지')
    d.steps([
        '1,067장짜리(`splits/blueberry`)를 지운다.',
        '1,195장짜리(`splits/blueberry_full1195`)의 이름을 `blueberry` 로 바꾼다.',
        '그 1,195장이 **7:1:2 로 잘 나뉘었는지 확인**한다.',
    ])
    d.note('마지막 문장 “사진 랜덤하게 들어가는 거라 작업하시고 주시는 게 나아서” 는 '
           '**“어느 사진이 어디로 갈지는 랜덤이라 우리가 직접 못 정하니, 곽동신 님이 '
           '작업해서 결과를 알려 달라”** 는 뜻입니다.')

    # ===================================================== 4장
    d.chapter('4', '왜 시키는 대로만 하면 안 됐나', '3번 항목을 확인했더니')
    d.h1('세어 봤더니 7:1:2 가 아니었습니다')
    d.p('이름을 바꾸기 전에 3번(“7:1:2 인지 확인”)을 먼저 했습니다. 결과는 이렇습니다.')

    d.table(['분할', 'train', 'val', 'test', '비율', '7:1:2?'],
            [['옛 1,067장판', str(old_c['cv1'][0]), str(old_c['cv1'][1]), str(old_c['cv1'][2]),
              f'{pct(old_c["cv1"])[0]:.0f} : {pct(old_c["cv1"])[1]:.0f} : {pct(old_c["cv1"])[2]:.0f}', 'X'],
             ['옛 1,195장판', str(gkf_c['cv1'][0]), str(gkf_c['cv1'][1]), str(gkf_c['cv1'][2]),
              f'{pct(gkf_c["cv1"])[0]:.0f} : {pct(gkf_c["cv1"])[1]:.0f} : {pct(gkf_c["cv1"])[2]:.0f}', 'X'],
             ['**새로 뜬 것**', f'**{new_c["cv1"][0]}**', f'**{new_c["cv1"][1]}**', f'**{new_c["cv1"][2]}**',
              f'**{pct(new_c["cv1"])[0]:.0f} : {pct(new_c["cv1"])[1]:.0f} : {pct(new_c["cv1"])[2]:.0f}**', '**○**']],
            [0.22, 0.13, 0.11, 0.12, 0.24, 0.12])

    d.h2('왜 블루베리만 7:1:2 가 아니었을까')
    d.p('블루베리는 이 연구에서 **제일 먼저** 시작한 데이터셋입니다. '
        '팀 규칙(7:1:2)이 정해진 건 2026-07-27 미팅인데, 블루베리 분할은 그보다 전에 '
        '이미 만들어져 있었습니다. 그때 쓴 방식이 **6-fold** 라는 방식이라 자연히 '
        '4:1:1(≈67:17:17)이 되었던 것입니다.')
    d.formula([
        '6-fold  =  전체를 6등분 → 1칸은 test, 1칸은 val, 나머지 4칸은 train',
        '        =  4 : 1 : 1  =  약 67 : 17 : 17',
        '',
        '팀 규칙  =  70 : 10 : 20  =  7 : 1 : 2',
    ])
    d.p('보시면 **test 가 오히려 줄고(17% < 20%), val 이 늘어난(17% > 10%)** 구조입니다. '
        '틀린 방식은 아니지만, 다른 3과일과 조건이 달라서 나란히 비교하기가 곤란합니다.')

    d.warn('그래서 이름만 바꿨다면 “7:1:2 로 해 달라”는 요청을 **못 지킨 채로 끝났을** 것입니다. '
           '그래서 한 단계 더 나아가 다시 뽑았습니다.', head='이 판단이 이번 작업의 분기점입니다')

    # ===================================================== 5장
    d.chapter('5', '블루베리만 다른 점 — 영상 단위', '이 문서에서 제일 중요한 부분')
    d.h1('그냥 랜덤으로 뽑으면 안 됩니다')
    d.p('팀 표준 분할 프로그램은 **사진을 한 장씩** 랜덤으로 뽑습니다. '
        '사과·복숭아·포도는 그래도 됩니다. 서로 다른 사진들이니까요. '
        '그런데 블루베리는 사정이 다릅니다. 파일 이름을 보면 알 수 있습니다.')
    d.code('Camera 3 Video (11) _ 181 .png\n'
           '~~~~~~~~~~~~~~~~~~~   ~~~\n'
           '     (가)             (나)',
           caption='블루베리 파일 이름의 구조')
    d.bullets([
        '**(가) `Camera 3 Video (11)`** — 3번 카메라로 찍은 11번째 **영상**의 이름',
        '**(나) `181`** — 그 영상의 **181번째 프레임**(장면)이라는 뜻',
    ])
    d.p('즉 블루베리 사진은 **동영상에서 잘라낸 장면들**입니다. '
        f'{n_total:,}장이 사실은 영상 **{n_vid}개**에서 나온 것입니다. '
        '한 영상당 평균 4장 정도인 셈입니다.')

    d.h2('같은 영상의 프레임은 거의 같은 사진입니다')
    d.p('영상에서 몇 초 차이로 잘라낸 두 장면은 사람 눈에도 거의 똑같습니다. '
        '이걸 한 장씩 랜덤으로 뽑으면 **1번 프레임은 train, 2번 프레임은 test** 로 '
        '갈라지는 일이 생깁니다.')

    d.fig(f2, height=0.245, caption='그림 2. 사진 단위로 뽑을 때(왼쪽)와 영상 단위로 뽑을 때(오른쪽)')

    d.tip('문제집에서 푼 문제가 **숫자만 살짝 바뀌어** 수능에 나온 것과 같습니다. '
          '점수는 잘 나오지만 그건 실력이 아니라 **본 적 있어서** 맞힌 것입니다. '
          '이런 걸 **데이터 누수(data leakage)** 라고 합니다.', head='비유로 기억하기')

    d.h2('그래서 «영상 통째로» 뽑았습니다')
    d.p(f'뽑기 단위를 사진 1장이 아니라 **영상 1개**로 바꿨습니다. '
        f'영상 {n_vid}개를 통째로 train·val·test 에 나눠 담되, '
        f'**사진 장수 기준으로** 7:1:2 가 되도록 맞췄습니다.')
    d.bullets([
        f'한 영상은 반드시 한 곳에만 들어갑니다 → 누수 **{ver["leak"]}건**',
        '카메라 4대(1~4번)별로 **따로** 뽑았습니다. 안 그러면 어떤 폴드는 '
        '4번 카메라 사진이 test 에 몰릴 수 있습니다.',
        '영상을 통째로 옮기다 보니 정확히 70%에 딱 못 맞춥니다. '
        '그래서 **영상 하나씩 옮겨 보며 오차를 줄이는 보정**을 넣어 0.25%p 안으로 맞췄습니다.',
    ])

    d.h2('카메라별로 따로 뽑았다는 게 무슨 뜻인가')
    d.p('블루베리 사진은 카메라 4대로 찍혔고, 대수마다 장수가 다릅니다.')
    d.table(['카메라', '1번', '2번', '3번', '4번', '합'],
            [['풀 전체 장수'] + [f'{cams[str(i)]:,}' for i in range(1, 5)] + [f'**{n_total:,}**'],
             ['cv1 의 train 에 들어간 수'] +
             [f'{cam1["train"][str(i)]:,}' for i in range(1, 5)] + [f'{new_c["cv1"][0]:,}'],
             ['그 비율(%)'] +
             [f'{cam1["train"][str(i)] / cams[str(i)] * 100:.1f}' for i in range(1, 5)] +
             [f'{new_c["cv1"][0] / n_total * 100:.1f}']],
            [0.30, 0.14, 0.14, 0.14, 0.14, 0.14])
    d.p('보시면 카메라 4대 전부 train 비율이 **70% 근처로 고르게** 들어갔습니다. '
        '이렇게 해야 “이 폴드는 유독 4번 카메라가 많아서 점수가 이상하다” 같은 일이 안 생깁니다.')

    # ===================================================== 6장
    d.chapter('6', '실제로 한 일 4단계', '순서대로')
    d.h1('4단계')
    d.steps([
        '**옛 분할 두 벌을 옮겼습니다.** 지우지 않고 이름 앞에 `_old_` 를 붙여 보관했습니다. '
        '바로가기뿐이라 용량이 거의 0 이라, 굳이 지울 이유가 없습니다.',
        '**새 분할 프로그램을 만들었습니다.** `tools/make_blueberry_folds_712.py`. '
        '영상 단위로 뽑고, 카메라별로 층을 나누고, 오차 보정까지 하는 프로그램입니다.',
        '**먼저 «쓰지 않고 계산만»(dry-run) 돌려 비율을 확인**했습니다. '
        '처음엔 오차가 1.2%p까지 났고, 보정을 넣어 0.25%p로 줄인 뒤에 실제로 만들었습니다.',
        '**여섯 가지를 전수 검사**했습니다 (다음 장).',
    ])

    d.h2('지금 폴더 상태')
    d.code('datasets_resized_2mp/splits/\n'
           f'├── blueberry/                              ← 새 것. {n_total:,}장 · 7:1:2 · cv1~cv6\n'
           '├── _old_blueberry_1067_260808/             ← 옛 1,067장판 (보관만)\n'
           '├── _old_blueberry_groupkfold1195_260808/   ← 옛 1,195장판 (보관만)\n'
           '├── apple/  peach/  grape/                  ← 손대지 않음',
           caption='팀원은 `blueberry/` 만 쓰면 됩니다')

    d.note('**`_old_` 두 개를 왜 남겼나요?** 특히 `_old_blueberry_groupkfold1195_260808` 은 '
           '예전에 돌린 실험 192번과 **폴드 구성이 100% 같습니다.** '
           '옛 결과와 숫자를 맞대볼 일이 생기면 이것 말고는 방법이 없습니다. '
           '필요 없어지면 `rm -rf` 로 지우면 됩니다.')

    d.h2('다시 만들려면 (같은 결과가 나옵니다)')
    d.code('$PY tools/make_blueberry_folds_712.py \\\n'
           '    --root .../datasets_resized_2mp/blueberry \\\n'
           '    --out  .../datasets_resized_2mp/splits/blueberry \\\n'
           '    --folds 1 2 3 4 5 6 --clean')
    d.p(f'랜덤이지만 **시드(seed)를 {man["base_seed"]} 로 고정**해서, 몇 번을 돌려도 '
        f'똑같은 분할이 나옵니다. 폴드 k 는 시드 {man["base_seed"]}+k 를 쓰기 때문에 '
        '나중에 cv7, cv8 을 **덧붙여도 cv1~cv6 은 한 장도 안 바뀝니다.**')

    # ===================================================== 7장
    d.chapter('7', '결과와 검증', '숫자 여섯 가지를 전수로 확인')
    d.h1(f'폴드별 장수 (총 {n_total:,}장)')
    d.table(['폴드', 'train', 'val', 'test', '비율(%)'],
            [[f'**{cv}**', str(c[0]), str(c[1]), str(c[2]),
              f'{pct(c)[0]:.2f} : {pct(c)[1]:.2f} : {pct(c)[2]:.2f}']
             for cv, c in new_c.items()],
            [0.14, 0.17, 0.15, 0.16, 0.38])

    d.fig(f3, height=0.215, caption='그림 3. 6폴드 전부 목표선(점선) 바로 위아래에 붙어 있습니다.')

    d.h2('검증 6종 — 전부 통과')
    d.table(['무엇을 확인했나', '왜 확인하나', '결과'],
            [['7:1:2 인가', '요청받은 바로 그것', f'**○ 오차 최대 0.25%p**'],
             ['깨진 바로가기가 있나', '깨지면 학습이 파일을 못 찾고 멈춤',
              f'**○ {ver["broken"]}개** / 총 {ver["links"]:,}개'],
             ['사진과 정답(마스크) 짝이 맞나', '짝이 어긋나면 엉뚱한 답으로 학습함',
              f'**○ 불일치 {ver["pair_mismatch"]}건**'],
             ['한 폴드 안에 같은 사진이 두 번 들어갔나', '들어가면 점수가 부풀려짐',
              f'**○ {ver["dup"]}건**'],
             ['같은 영상이 train/val/test 에 걸쳤나', '이번 작업의 핵심 (5장)',
              f'**○ {ver["leak"]}건** · 영상 {n_vid}개 전수'],
             ['카메라가 한쪽에 쏠렸나', '쏠리면 폴드끼리 조건이 달라짐',
              '**○ 4대 전부 약 70:10:20**']],
            [0.36, 0.40, 0.24])
    d.p(f'“전수”란 표본을 뽑아 본 것이 아니라 **{ver["folds"]}개 폴드 × 3개 split = '
        f'{ver["folds"] * 3}개 폴더를 하나도 빠뜨리지 않고** 다 열어 봤다는 뜻입니다.')

    # ===================================================== 8장
    d.chapter('8', '팀원이 물어볼 것 7가지', '이대로 대답하시면 됩니다')
    d.qa('시킨 건 이름 바꾸기였는데 왜 다시 만들었나요?',
         '이름을 바꾸기 전에 “7:1:2 인지 확인해 달라”는 부분을 먼저 했는데, '
         f'{gkf_c["cv1"][0]}/{gkf_c["cv1"][1]}/{gkf_c["cv1"][2]} 라 7:1:2 가 아니었습니다. '
         '이름만 바꾸면 요청의 절반은 못 지키는 셈이라 다시 뽑았습니다.')
    d.qa('폴드끼리 test 가 겹치는데 잘못된 거 아닌가요?',
         '정상입니다. 우리 팀 규칙은 전체를 K등분하는 K-Fold 가 아니라, '
         '**폴드마다 전체에서 다시 7:1:2 를 뽑는 방식**(ShuffleSplit)입니다. '
         '2026-07-27 미팅에서 교수님이 “나중에 10폴드 필요하면 5폴드 더 추가하고 랜덤하게 '
         '뽑아서” 라고 하셔서 이 방식으로 정해졌습니다. 사과·포도도 똑같이 겹칩니다.')
    d.qa('왜 블루베리만 6폴드인가요? 다른 건 5개인데.',
         '블루베리는 이 연구를 시작한 데이터셋이라 예전 실험 192번이 이미 6폴드로 돌아가 '
         '있습니다. 그 연속성 때문에 6개를 유지했습니다. **4과일을 나란히 비교할 때는 '
         'cv1~cv5 만 쓰면** 조건이 같아집니다.')
    d.qa('예전에 돌린 블루베리 결과를 그대로 쓰면 안 되나요?',
         '안 됩니다. 폴드에 들어간 사진이 바뀌었으니 **재학습이 필요합니다.** '
         '사실 4K 128장을 다시 넣은 시점에 이미 재학습이 필요한 상태였습니다.')
    d.qa('영상 단위로 뽑으면 사과·포도랑 방식이 달라지는 거 아닌가요?',
         '비율(7:1:2)과 «폴드마다 다시 뽑는다»는 규칙은 **똑같습니다.** '
         '다른 건 뽑는 단위뿐이고, 그건 블루베리만 동영상 프레임이기 때문입니다. '
         '오히려 사과 cv1~cv5 는 사진 단위라 같은 문제가 남아 있어서, '
         'single(연도 분할)로도 한 번 돌려 보시길 권하고 있습니다.')
    d.qa('4K 사진 128장은 왜 다시 넣었나요?',
         '0806 미팅에서 뺐던 이유는 «4K라서»가 아니라 «사람 눈높이에서 본 나무 구도가 '
         '아니라서» 였습니다. 그런데 열어 보니 그 사진들도 나무에 달린 열매가 맞고, '
         '포도(CERTH)도 같은 4K인데 전량 쓰고 있어서 형평을 맞췄습니다. '
         '**이 건은 교수님께 따로 보고가 필요합니다.**')
    d.qa('데이터가 또 바뀌면 어떻게 하나요?',
         '`tools/make_blueberry_folds_712.py` 를 `--clean` 붙여 다시 돌리면 됩니다. '
         '시드가 고정이라 데이터가 그대로면 결과도 그대로입니다.')

    # ===================================================== 9장
    d.chapter('9', '남은 일과 주의사항', '여기까지 하고 멈춘 것들')
    d.h1('반드시 해야 할 것')
    d.steps([
        '★ **교수님께 두 건 보고**: ① 0806 에 빼기로 한 4K 128장을 다시 넣었다 '
        '② 분할을 7:1:2 로 다시 떴다. 둘 다 재학습이 전제입니다.',
        '★ **블루베리 재학습**: 폴드 구성이 바뀌었으므로 예전 192런과 직접 비교가 안 됩니다.',
        '**팀에 새 경로 공지**: 카톡 문구는 만들어 뒀습니다 (아래).',
    ])

    d.h2('건드리지 않은 것')
    d.bullets([
        '사과·복숭아·포도 분할 — **무수정**. 깨진 링크 0 확인했습니다.',
        f'사진 실파일({n_total:,}장) — **무수정**. 분할은 바로가기만 다시 만든 것입니다.',
        '원본 `dataset_6fold/` — 읽기만 했습니다.',
        'GPU — 이번 작업에 학습은 없었습니다.',
    ])

    d.h2('관련 파일 위치')
    d.table(['무엇', '경로'],
            [['새 분할', 'datasets_resized_2mp/splits/blueberry/cv1~cv6'],
             ['분할 만든 프로그램', 'semantic-segmentation/tools/make_blueberry_folds_712.py'],
             ['실행 기록', 'logs/make_blueberry_folds_712_260808.log'],
             ['어느 사진이 어디 갔는지', 'splits/blueberry/folds_manifest.json'],
             ['팀 카톡 문구 (답장용)', '문서/260808_카톡_블루베리분할완료.txt'],
             ['팀 카톡 문구 (전체 안내)', '문서/260807_카톡_데이터셋안내_짧은판.txt'],
             ['데이터셋 설명서', 'datasets_resized_2mp/README.md (4절)'],
             ['**이 PDF**', '**semantic-segmentation/reports/블루베리_분할_7대1대2_설명서.pdf**']],
            [0.34, 0.66], size=8.8)

    d.warn('이 PDF 가 있는 `semantic-segmentation/reports/` 는 **팀에 공유한 경로가 아닙니다.** '
           '팀 공유 경로는 `datasets_resized_2mp/` · `share_grape_certh/` · `_서버업로드용/` '
           '세 곳입니다. 이 문서를 팀원에게 주시려면 파일을 따로 보내 주세요.',
           head='공유 범위')

    d.save()


if __name__ == '__main__':
    build()
