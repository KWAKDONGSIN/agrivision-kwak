# -*- coding: utf-8 -*-
"""사과·블루베리 데이터 검수 최종 보고서 PDF — 뺀 사진·사람 확인 사진 전부. 작성: 2026-09-17
실행: /home/kds0206/.conda/envs/kwak/bin/python tools/make_apple_blueberry_review_pdf_260917.py
출력: 문서/260917_사과블루베리_검수_최종보고서.pdf   (숫자는 전부 manifest.csv 를 직접 세어 넣는다)
최종 수정: 2026-09-18 (**판정값 동결 03:07:53 · manifest 에 session 칸 04:12:36** — «2단계»(남긴 사진끼리 안 본 이웃 300쌍 눈 판정)까지 반영.
  §3-4 «얼마나 솎을 것인가» 신설: 간격별 곡선표·간격 솎기 대안표를 gap_eye/curve_eye CSV 와 원본 파일명에서 그 자리에 센다.
  숫자는 전부 manifest·CSV 에서 그 자리에 센다 — 본문 문장에 손으로 적은 장수는 없다)
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdfdoc import Doc

K = Path('/data/project/2026summer/kds0206')
T = Path('/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴')
I = T / 'inspect/260917_apple_blueberry'
SRC = K / 'datasets_resized_2mp'
REV = K / 'datasets_reviewed_260917'
OUT = K / '문서/260917_사과블루베리_검수_최종보고서.pdf'
FIG = K / 'semantic-segmentation/reports/ab_review_260917'
FIG.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 13)
rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8')))
KO = {'apple': '사과', 'blueberry': '블루베리'}
man = {f: rd(REV / f / 'manifest.csv') for f in KO}
cnt = {f: Counter(r['action'] for r in man[f]) for f in KO}
short = lambda s: s.replace('Camera ', 'C').replace(' Video ', 'V').replace('20150919_', '0919_').replace('20150921_', '0921_')

# ── 동결판 숫자를 여기서 전부 센다 (본문 문장에 숫자를 손으로 적지 않기 위해) ─────────────
V2D = I / 'round3_final/v2'
SPL = Path('/data/project/2026summer/platform/04_experiments/260908_파일럿/protocol_splits/v3_seed3407')
kept = {f: [r for r in man[f] if r['action'] != 'excluded_duplicate'] for f in KO}
keptset = {f: {r['stem'] for r in kept[f]} for f in KO}
nkept = {f: len(kept[f]) for f in KO}
col = lambda f, c: sum(bool(r[c]) for r in kept[f])                       # 남긴 사진만 센다
sgc = {f: Counter(r['split_group'] for r in kept[f]) for f in KO}
sess = {f: Counter(r['session'] for r in kept[f]) for f in KO}       # 촬영 단위(2026-09-18 04:12:36 신설 칸)
rel = {f: [{k: v.strip() for k, v in r.items()} for r in rd(V2D / f'relations_v2_{f}.csv')] for f in KO}
nrel = {f: Counter(r['kind'] for r in rel[f]) for f in KO}
ngrp = {f: len(rd(V2D / f'exclusion_v2_{f}.csv')) for f in KO}
MAJ = {frozenset((r['a'].strip(), r['b'].strip())): r['majority'].strip() for r in rd(V2D / 'interrater_majority.csv')}
eye = Counter()
for p in sorted(V2D.glob('tier1_eye_part*.csv')) + [V2D / 'tier1_eye_recheck111.csv']:
    for r in rd(p):
        v, m = r['verdict'].strip(), MAJ.get(frozenset((r['a'].strip(), r['b'].strip())))
        if m: v = 'near_identical' if m == 'near_identical' else ('overlap_shifted' if v == 'near_identical' else v)
        eye[(r['fruit'].strip(), v)] += 1
n_eye = sum(eye.values())
n_inter = len(MAJ)                                                        # 판정자 간 일치도를 잰 쌍 수

# ── 2단계(남긴 사진끼리 안 본 이웃) · 간격별 곡선 · 간격 솎기 대안표 — 전부 원천 CSV 에서 센다 ─────
GAPKEY = {}                                                               # {쌍: 프레임 간격}
for _f, in (('gap_unseen_key.csv',), ('curve_pairs_key.csv',)):
    for r in rd(V2D / _f): GAPKEY[frozenset((r['a'], r['b']))] = int(r['gap'])
gap_rows = [r for p in sorted(V2D.glob('gap_eye_part*.csv')) for r in rd(p)]         # 2단계 눈 판정 300쌍
curve_rows = [r for p in sorted(V2D.glob('curve_eye_part*.csv')) for r in rd(p)]     # 곡선용 먼 간격 252쌍
n_gap, n_curve = len(gap_rows), len(curve_rows)
gap_ni = sum(r['verdict'].strip() == 'near_identical' for r in gap_rows)
gap_ov = sum(r['verdict'].strip() == 'overlap_shifted' for r in gap_rows)
gap_full = sum(r['kind'] == 'full' for r in rd(V2D / 'gap_unseen_key.csv'))          # 확인 범위 전수 몫
curve_ni = sum(r['verdict'].strip() == 'near_identical' for r in curve_rows)
CURVE = defaultdict(lambda: [0, 0, 0])                                    # (출처, 간격) → [쌍, 거의 같음, 다른 장면]
for r in gap_rows + curve_rows:
    a, b, v = r['a'].strip(), r['b'].strip(), r['verdict'].strip()
    t = CURVE[('현장(MinneApple)' if a.startswith('2015') else 'dataset1~4', GAPKEY[frozenset((a, b))])]
    t[0] += 1; t[1] += v == 'near_identical'; t[2] += v == 'different'
n_frameadj = sum(r['verdict'] == 'true_duplicate' for r in rd(I / 'round3_apple_frameadj/frameadj208_verdicts.csv'))
CURVE[('현장(MinneApple)', 5)] = [n_frameadj, n_frameadj, 0]              # 3차 보충 검수(전부 진짜 중복)
n_pair_curve = sum(v[0] for v in CURVE.values())
n_diff_curve = sum(v[2] for v in CURVE.values())
below20 = {}                                                              # 비율이 처음 20% 아래로 떨어지는 간격
for src in ('현장(MinneApple)', 'dataset1~4'):
    gs = sorted(g for (s, g) in CURVE if s == src)
    below20[src] = next((g for g in gs if 100 * CURVE[(src, g)][1] / CURVE[(src, g)][0] < 20), None)

_ses = lambda s: re.match(r'(.*?)(\d+)$', s).group(1)
_frm = lambda s: int(re.match(r'(.*?)(\d+)$', s).group(2))
_by = defaultdict(dict)
for r in man['apple']: _by[_ses(r['stem'])][_frm(r['stem'])] = r['stem']
STRIDE = []                                                               # (이름, 현장 G, dataset G, 남는 장수, flag 수)
for gm, gd in ((30, 60), (40, 90), (60, 90), (90, 120), (120, 180), (180, 240)):
    keepg = set()
    for p, dd in _by.items():
        G, last = (gm if p.startswith('2015') else gd), None
        for fr in sorted(dd):
            if last is None or fr - last >= G: keepg.add(dd[fr]); last = fr
    mm = {r['stem']: r['action'] for r in man['apple']}
    STRIDE.append((f'keep_G{gm}_{gd}', gm, gd, len(keepg), sum(mm[s] == 'needs_human' for s in keepg)))


def graph(f, kind, only_kept=False):
    E = defaultdict(set)
    for r in rel[f]:
        if r['kind'] != kind: continue
        if only_kept and not (r['a'] in keptset[f] and r['b'] in keptset[f]): continue
        E[r['a']].add(r['b']); E[r['b']].add(r['a'])
    return E


def comps(E):
    seen, out = set(), []
    for s in E:
        if s in seen: continue
        st, c = [s], []; seen.add(s)
        while st:
            x = st.pop(); c.append(x)
            for y in E[x]:
                if y not in seen: seen.add(y); st.append(y)
        out.append(c)
    return out


def mis(comp, E):
    """성분의 최대 독립 집합 크기 — 비트마스크 분기한정(고립·차수1 축약 + 최대차수 분기)."""
    comp = sorted(comp); idx = {s: i for i, s in enumerate(comp)}
    nb = [0] * len(comp)
    for s in comp:
        m = 0
        for t in E[s]:
            if t in idx: m |= 1 << idx[t]
        nb[idx[s]] = m
    memo, pc = {}, lambda x: bin(x).count('1')

    def solve(mask):
        if mask == 0: return 0
        if mask in memo: return memo[mask]
        lo = (mask & -mask).bit_length() - 1
        part, fr = 1 << lo, nb[lo] & mask
        while fr & ~part:
            v = ((fr & ~part) & -((fr & ~part))).bit_length() - 1
            part |= 1 << v; fr |= nb[v] & mask
        if part != mask:
            memo[mask] = r = solve(part) + solve(mask & ~part); return r
        for i in range(len(comp)):
            if mask >> i & 1 and pc(nb[i] & mask) <= 1:
                memo[mask] = r = 1 + solve(mask & ~((1 << i) | nb[i])); return r
        v = max((pc(nb[i] & mask), i) for i in range(len(comp)) if mask >> i & 1)[1]
        memo[mask] = r = max(1 + solve(mask & ~((1 << v) | nb[v])), solve(mask & ~(1 << v)))
        return r
    return solve((1 << len(comp)) - 1)


# «탐욕이 최대 독립 집합보다 몇 장 더 뺐나» 는 더 이상 계산하지 않는다 — 제외가 2단계 구조(1단계 결과를
# 고정하고 남긴 사진 안에서만 더 고름)가 되어 단순 비교가 성립하지 않는다. 근거: cycle_5/stage2/number_dict_final.md §5
thin = {}                       # «겹치는 이웃» 을 솎으면 몇 장 남나
for f in KO:
    O = graph(f, 'overlap_neighbor', only_kept=True)
    cs = comps(O)
    thin[f] = dict(photos=len(O), groups=len(cs), one=nkept[f] - len(O) + len(cs),
                   indep=nkept[f] - len(O) + sum(mis(c, O) for c in cs),
                   pairs=nrel[f]['overlap_neighbor'], eye=eye[(f, 'overlap_shifted')])


def fold_cross(f, col_name):
    """옛 분할표에서 «한 묶음이 서로 다른 폴드에 걸치는» 개수 (그 칸이 채워진 사진만 셈)."""
    p = SPL / f'{f}.csv'
    if not p.exists(): return None
    sp = rd(p); key = 'sample_id' if 'sample_id' in sp[0] else list(sp[0])[0]
    fold = {r[key]: r[col_name] for r in sp if r.get(col_name)}
    g = rd(V2D / f'exclusion_v2_{f}.csv')
    dup = sum(len({fold[s] for s in [r['keep_stem']] + r['drop_stems'].split('|') if s in fold}) > 1 for r in g)
    sg = defaultdict(set)
    for r in man[f]:
        if r['split_group'] and r['stem'] in fold: sg[r['split_group']].add(fold[r['stem']])
    return dup, sum(len(v) > 1 for v in sg.values()), len(fold)


AGREE = [['사과', '60', '80% (0.56)', '78% (0.51)', '88% (0.72)', '44 (73%)'],
         ['블루베리', '29', '72% (0.43)', '79% (0.58)', '59% (0.17)', '16 (55%)'],
         ['**전체**', '**89**', '78% (0.54)', '79% (0.56)', '79% (0.55)', '**60 (67%)**']]


def thumb(fruit, stem, w=190, h=150, boxes=()):
    im = Image.open(SRC / fruit / 'images' / (stem + '.png')).convert('RGB')
    if boxes:
        m = np.array(Image.open(SRC / fruit / 'masks' / (stem + '.png')))
        m = (m.max(axis=2) if m.ndim == 3 else m) > 0
        a = np.array(im); a[m] = (0.6 * a[m] + 0.4 * np.array([230, 40, 40])).astype(np.uint8); im = Image.fromarray(a)
        d = ImageDraw.Draw(im)
        for b in boxes: d.rectangle(b, outline=(255, 235, 0), width=max(4, im.width // 250))
    im.thumbnail((w, h)); return im


def grid(cells, name, cols=6, cw=200, ch=178):
    """cells=[(PIL, 글자, 테두리색)] → 한 쪽에 cols×7 칸씩 PNG 여러 장"""
    out = []
    for p in range(0, len(cells), cols * 7):
        part = cells[p:p + cols * 7]; rows = -(-len(part) // cols)
        sh = Image.new('RGB', (cols * cw, rows * ch), 'white'); d = ImageDraw.Draw(sh)
        for i, (im, label, color) in enumerate(part):
            x, y = (i % cols) * cw, (i // cols) * ch
            sh.paste(im, (x + (cw - im.width) // 2, y + 4))
            d.rectangle([x + 2, y + 2, x + cw - 3, y + ch - 3], outline=color, width=4)
            d.text((x + 6, y + ch - 22), label, fill='black', font=FONT)
        q = FIG / f'{name}_{p // (cols * 7):02d}.png'; sh.save(q); out.append(q)
    return out


def dup_cells(fruit):
    g = defaultdict(list)
    for r in man[fruit]:
        if r['action'] == 'excluded_duplicate': g[re.search(r'대표 (.+?) 만', r['note']).group(1)].append(r['stem'])
    cells = []
    for k in sorted(g):
        cells.append((thumb(fruit, k), '남김 ' + short(k)[-22:], (30, 160, 70)))
        cells += [(thumb(fruit, s), '뺌 ' + short(s)[-23:], (210, 50, 40)) for s in sorted(g[k])]
    return cells, len(g)


def flag_cells(fruit):
    cells = []
    for r in man[fruit]:
        if r['action'] != 'needs_human': continue
        boxes = [tuple(map(int, b.split(','))) for b in re.findall(r'(\d+,\d+,\d+,\d+)', r['note'])]
        cells.append((thumb(fruit, r['stem'], 300, 236, boxes or [(0, 0, 1, 1)]), short(r['stem'])[-30:], (230, 140, 30)))
    return cells


d = Doc(OUT, title='사과·블루베리 데이터 검수 최종 보고서', subtitle='0915 랩미팅 지시 — 복숭아·포도에 이어 같은 방식으로 · 뺀 사진과 사람이 볼 사진 전부', date='2026-09-17')
d.cover(lines=['담당: 곽동신', '검수 3회: Opus 5 → Opus 5(과일별 2명) → Fable 5.1 (최종 판정·실행) + 보충 검수 1회 + 판정자 간 일치도 측정',
               '원본 datasets_resized_2mp 무변경 · 결과는 새 폴더 datasets_reviewed_260917',
               '판정값 동결 2026-09-18 03:07:53 · manifest 에 촬영 단위(session) 칸 추가 04:12:36'], badge='최종 동결판')

d.h1('0. 한눈에 보기')
d.table(['항목', '사과', '블루베리'], [
    ['원본 장수', format(len(man['apple']), ','), format(len(man['blueberry']), ',')],
    ['새 폴더 장수(남긴 것)', '**%s**' % format(nkept['apple'], ','), '**%s**' % format(nkept['blueberry'], ',')],
    ['뺀 사진(거의 같은 사진)', '**%d장** (대표 %d묶음)' % (cnt['apple']['excluded_duplicate'], ngrp['apple']), '**%d장** (대표 %d묶음)' % (cnt['blueberry']['excluded_duplicate'], ngrp['blueberry'])],
    ['사람이 툴에서 볼 것(flag)', '**%d장**' % cnt['apple']['needs_human'], '**%d장**' % cnt['blueberry']['needs_human']],
    ['«겹치는 이웃»(같은 나무·다른 구도) — 빼지 않고 표시만', '%d장' % col('apple', 'overlap_neighbors'), '%d장' % col('blueberry', 'overlap_neighbors')],
    ['교수님 결정 대기로 표시만 한 사진(폴더에 남은 것)', '%d장' % col('apple', 'rule_pending'), '%d장' % col('blueberry', 'rule_pending')],
    ['분할용 묶음(`split_group`, 남긴 사진 기준)', '%s개 (사진 2장 이상 %d)' % (format(len(sgc['apple']), ','), sum(v > 1 for v in sgc['apple'].values())), '%s개 (%d)' % (format(len(sgc['blueberry']), ','), sum(v > 1 for v in sgc['blueberry'].values()))],
    ['**촬영 단위(`session`) — 분할의 권고 기준**', '**%d개** (가장 큰 촬영 %d장)' % (len(sess['apple']), max(sess['apple'].values())), '**%d개** (최대 %d장)' % (len(sess['blueberry']), max(sess['blueberry'].values()))],
    ['자동으로 고친 마스크', '0', '0'],
    ['사진↔마스크가 다른 장면(포도에서 나온 버그)', '0 / 1,001 전수', '0 / 1,195 전수'],
    ['이 폴더를 얼마나 더 솎을지', '**교수님 결정 대기** (§3-4 · 우리 권고 = 촬영 단위 분할 + 294장)', '결정 사항 없음'],
], [.4, .3, .3])
d.note('숫자는 이 PDF 를 만들 때 `datasets_reviewed_260917/<과일>/manifest.csv` 와 근거 CSV 를 직접 세어 넣은 값입니다(2026-09-18 03:07:53 최종 동결판). `rule_pending` 은 뺀 사진 행에도 붙어 있어 폴더에 남은 사진만 셌습니다(행 전체로는 사과 39·블루베리 244). 사과 마스크는 **열매 번호(인스턴스) 그대로** 복사했습니다(0/255 로 바꾸면 카운팅 정답이 사라짐). 라벨링 툴 `data/` 에도 같은 숫자를 반영했습니다.')
d.warn('마스크를 자동으로 고치지 않은 이유: 사과는 AI 가 찾은 덩어리가 사과의 일부라 **사과 전체를 다시 그리고 번호를 붙여야** 하고, 블루베리는 AI 가 **흰 꽃을 열매로 착각**하는 데다 후보의 대부분이 «어디까지 칠하나» 라는 규칙 문제였습니다. 그래서 전부 툴의 «문제 있음» 표시로 넘겼습니다.', head='왜 고친 마스크가 0 인가')

d.h1('1. 교수님 말씀 → 확인한 것')
d.table(['녹취(0915)', '확인 결과'], [
    ['«사과… 중간이 비어야 되는데 동그랗게 라벨링»', '**실재하고, 출처에 따라 갈립니다.** MinneApple 사진은 잎에 가려진 부분까지 원으로 통째 칠했고(의심 상위 150개체 중 92), dataset1~3 사진은 잎·옆 사과를 피해 보이는 부분만 칠했습니다. 한 데이터셋에 두 규칙이 섞여 있습니다(그림 2·3)'],
    ['«블루베리 같은 것도 없는 것들 추가»', 'AI 가 «라벨 없음» 으로 짚은 후보 상위 300개를 전부 확대: 마른 꽃부리 155 · 판단 불가 51 · 잎 42 · 초점 밖 뒷줄 27 · 꽃 16 · 오검출 6 · **진짜 누락 3**. 개수로는 거의 다 라벨돼 있고, 쟁점은 시든 꽃잎·어린 초록 열매·뒷줄을 칠할지의 **규칙**입니다(그림 5)'],
    ['«영상 프레임별로 하면 거의 똑같잖아요… 걸러내고»', '사과: 같은 나무를 걸어가며 찍은 연속 프레임이 많음 — **눈으로 «거의 같은 사진» 이라고 확인된 관계만**으로 **%d장** 제외(그림 1). 블루베리: 4번 카메라 접사 영상은 한 송이를 확대만 함(그림 4) + 1·2·3번 카메라에서 눈으로 확인된 %d쌍 — **%d장** 제외. 같은 나무를 **다른 구도**로 찍은 «겹치는 이웃» 은 빼지 않고 표시만 함(분할 때 같은 그룹으로 묶을 것)' % (cnt['apple']['excluded_duplicate'], eye[('blueberry', 'near_identical')], cnt['blueberry']['excluded_duplicate'])],
], [.34, .66])

d.h1('2. 어떻게 검수했나')
d.table(['회차', '누가', '무엇을'], [
    ['1차', 'Opus 5', '두 과일 중복·누락 후보·의심 플래그·무작위 60장. 시간 안에 일부만 직접 봄(예: 누락 후보 300 중 사과 52·블루베리 80)'],
    ['2차', 'Opus 5 × 2(과일별)', '1차 판정을 가린 채 다시 봄 + 1차가 못 본 것 전부: 누락 후보 300/300, 의심 전부, 무작위 60/60, 사과 중복 123그룹(2차가 본 값), 블루베리 영상 120개, 어긋남 전수 자동 점검'],
    ['보충', 'Opus 5', '사과 프레임 인접 208쌍(2차가 24쌍만 본 것)을 전부 눈으로 — 208/208 진짜 중복'],
    ['3차', 'Fable 5.1', '갈린 쟁점 8건을 시트를 직접 열어 판정, 실행(새 폴더·툴 반영·이 PDF)'],
    ['재검수', 'Opus 5 × 2 → Fable', '5회 재검수 사이클 1: 남긴 사진 안에서 중복을 다시 찾음(후보 13,114쌍 전수 점수화). Fable 이 «거의 같은 사진(화면 약 80% 이상 같음)» 과 «겹치는 이웃» 을 가르는 2단 기준을 확정'],
    ['보충 눈 판정', 'Opus 5 × 4', '자동 겹침 0.8 이상 %d쌍(사과 %d·블루베리 %d)을 점수를 가린 채 전부 눈으로 — 거의 같은 사진 %d / 겹치는 이웃 %d / 다른 장면 0'
     % (n_eye, eye[('apple', 'near_identical')] + eye[('apple', 'overlap_shifted')], eye[('blueberry', 'near_identical')] + eye[('blueberry', 'overlap_shifted')],
        eye[('apple', 'near_identical')] + eye[('blueberry', 'near_identical')], eye[('apple', 'overlap_shifted')] + eye[('blueberry', 'overlap_shifted')])],
    ['판정자 간\n일치도 측정', 'Opus 5 × 2 (판정자 A·B)', '같은 %d쌍(사과 60·블루베리 29)을 기존 판정과 서로를 못 본 채 다시 판정 → 일치율·카파를 냄(§3-1). **이 %d쌍은 세 판정의 다수결로 확정**해 데이터셋을 다시 만듦 = **1차 동결판(01:33, 사과 547장)**' % (n_inter, n_inter)],
    ['**2단계\n눈 판정**', 'Opus 5 × 2 (판정자 2명)', '총괄 검수가 **«남긴 사진끼리 같은 촬영·가까운 프레임인데 한 번도 판정받은 적 없는 쌍이 있다»** 를 찾아냄 → 그 쌍 **%d개**(확인 범위 전수 %d + 더 먼 간격 표본 %d)를 **간격을 모르는 채** 눈으로 판정 = 거의 같은 사진 **%d** / 겹치는 이웃 %d / 다른 장면 0 → 1단계에서 뺀 사진은 그대로 두고 남긴 사진 안에서만 더 골라 **%d장 추가 제외** = **최종 동결판(03:07:53, 사과 %d장)**'
     % (n_gap, gap_full, n_gap - gap_full, gap_ni, gap_ov, cnt['apple']['excluded_duplicate'] - 454, nkept['apple'])],
    ['간격별 곡선\n측정', 'Opus 5 × 2', '전체 사과 사진에서 **더 먼 간격의 쌍 %d개**를 같은 방식으로 판정 → 간격별 «거의 같은 사진» 비율 곡선(§3-4). 여기서 «얼마나 솎을 것인가» 의 선택지가 나옴' % n_curve],
], [.1, .22, .68])
d.p('1차와 2차의 일치율은 사과 중복 100% · 블루베리 4번 카메라 100% 였지만, 누락 후보 세부 분류는 사과 37%·블루베리 51% 로 낮았습니다. 갈린 이유는 대부분 «낙과·뒷줄·마른 꽃부리를 열매로 볼 것인가» 라는 규칙 차이였고, 3차는 이것들을 오류가 아니라 **교수님 결정 대기**로 분류했습니다.')

d.h1('3. 사과')
d.h2('3-1. 거의 같은 사진')
d.p('같은 촬영에서 몇 프레임 간격으로 뽑힌 이웃 사진은 같은 나무·같은 열매입니다. 자동 탐지(해시)는 절반도 못 잡아서, 1차 해시 탐지 47그룹을 2차가 해시 묶음 71그룹(전부 진짜)·완화 묶음 76그룹(진짜 75)으로 다시 보고, 여기에 5프레임 이웃 232쌍 + 자동 겹침 0.8 이상 %d쌍(두 과일 합계 — **사과 몫은 %d쌍**) + **남긴 사진끼리의 안 본 이웃 %d쌍**을 더해 **전부 눈으로 판정**했습니다(1단계 사과 %d쌍 중 %d쌍 + 2단계 %d쌍 중 %d쌍이 «거의 같은 사진», 확인된 관계 **%s개**). 사슬처럼 이어 붙이면 한 촬영에서 1장만 남아 과하므로, «확인된 관계가 있는 두 장이 함께 남지 않게» 만 골랐고 사람 확인 사진을 먼저 남겼습니다.'
    % (n_eye, eye[('apple', 'near_identical')] + eye[('apple', 'overlap_shifted')], n_gap,
       eye[('apple', 'near_identical')] + eye[('apple', 'overlap_shifted')], eye[('apple', 'near_identical')],
       n_gap, gap_ni, format(nrel['apple']['near_identical'], ',')))
d.warn('자동 점수만으로 자르면 안 됩니다. 자동 겹침 0.9 이상인 쌍도 눈으로 보면 60~80%% 만 «거의 같은 사진» 이었고, 나머지는 걸어가며 구도가 옮겨 간 «겹치는 이웃» 이었습니다. 그래서 «겹치는 이웃» 은 지우지 않고 `overlap_neighbors` 칸에 적어, 분할표를 만들 때 같은 그룹으로 묶게 했습니다.\n\n'
       '**줄어든 경위**: 첫 판 **687장**(2026-09-17 22:22, 해시·5프레임 이웃만) → **549장**(0918 00:22, 자동 겹침 0.8 이상 %d쌍을 전부 눈 판정) → **547장**(01:33, 판정자 3명의 다수결 반영) → **%d장**(03:07:53, 남긴 사진끼리 안 본 이웃 %d쌍을 눈 판정해 %d장 추가 제외). '
       '**확인하는 범위를 넓힐 때마다 더 나왔습니다** — 왜 그런지는 §3-4 입니다.'
       % (n_eye, nkept['apple'], n_gap, cnt['apple']['excluded_duplicate'] - 454), head='왜 첫 판(687장)에서 %d장으로 줄었나' % nkept['apple'])
d.p('**«거의 같은 사진인가» 는 자로 잰 값이 아니라 판정입니다.** 그래서 같은 %d쌍을 기존 판정(O)과 새 판정자 A·B 가 서로의 답을 못 본 채 다시 판정해 일치도를 쟀습니다. 아래 표의 괄호 안은 카파(우연히 맞을 확률을 뺀 값, 1 이면 완전 일치)입니다.' % n_inter)
d.table(['범위', '쌍', 'O–A 일치(κ)', 'O–B 일치(κ)', 'A–B 일치(κ)', '셋 다 일치'], AGREE, [.16, .1, .19, .19, .19, .17])
d.warn('이 %d쌍은 **세 판정의 다수결**로 확정했습니다(사과 9쌍·블루베리 1쌍이 뒤집힘). 사과 제외의 근거인 관계 %s개는 **100%% 사람 눈 판정**이어서, 판정자 기준이 달라지면 남는 장수가 움직입니다 — 이 89쌍으로는 **약 ±16장** 규모였습니다.\n\n'
       '**2단계·곡선 판정에서 더 큰 판정자 차이가 실측됐습니다.** 같은 표본을 반씩(서로 겹치는 쌍 0) 나눠 본 두 판정자의 «거의 같은 사진» 비율이 **%.1f%% 대 %.1f%%**(2단계 %d쌍) · **%.1f%% 대 %.1f%%**(곡선 %d쌍)로 갈렸습니다. 간격 구성이 비슷한데도 간격마다 한쪽이 계속 더 후했으므로 판정자 효과로 봐야 하고, §3-4 곡선의 비율에는 **±10~15%%p** 가 붙습니다.\n\n'
       '블루베리는 A–B 일치가 59%%(κ 0.17)로 가장 낮아, 3번 카메라 %d장 제외도 다수결로 정했습니다(4번 카메라 %d장은 눈 판정이 아니라 «한 영상당 1장» 이라는 파일명 규칙).'
       % (n_inter, format(nrel['apple']['near_identical'], ','),
          100 * sum(r['verdict'].strip() == 'near_identical' for r in rd(V2D / 'gap_eye_part1.csv')) / len(rd(V2D / 'gap_eye_part1.csv')),
          100 * sum(r['verdict'].strip() == 'near_identical' for r in rd(V2D / 'gap_eye_part2.csv')) / len(rd(V2D / 'gap_eye_part2.csv')), n_gap,
          100 * sum(r['verdict'].strip() == 'near_identical' for r in rd(V2D / 'curve_eye_part1.csv')) / len(rd(V2D / 'curve_eye_part1.csv')),
          100 * sum(r['verdict'].strip() == 'near_identical' for r in rd(V2D / 'curve_eye_part2.csv')) / len(rd(V2D / 'curve_eye_part2.csv')), n_curve,
          cnt['blueberry']['excluded_duplicate'] - 71, 71), head='판정자가 바뀌면 숫자가 얼마나 움직이나')
d.fullfig(I / 'round2_apple/sheets/apple_frameadj/g000.jpg', caption='그림 1. 사과 5프레임 이웃 — 같은 나무, 같은 그림자', sub='20150919_174151_image101 ↔ image106. 해시는 이 쌍을 못 잡았습니다.')
d.h2('3-2. «동그랗게 라벨링» 의 정체')
d.p('교수님이 0915 에 짚으신 «중간이 비어야 되는데 동그랗게» 를 사진으로 확인했습니다. **같은 «사과» 안에서 출처마다 라벨 관행이 다릅니다.** 다음 두 쪽의 그림 2(MinneApple)는 잎에 가려진 부분까지 원으로 통째 칠했고, 그림 3(dataset1)은 잎과 옆 사과를 피해 보이는 부분만 칠했습니다. 어느 쪽으로 통일할지는 §5 의 첫 질문입니다. 마스크는 손대지 않았습니다.')
d.fullfig(I / 'round2_apple/sheets/apple_amodal2/a000.jpg', caption='그림 2. MinneApple — 가려진 부분까지 통째로 칠함', sub='왼쪽부터 사진 · 원본 라벨 · AI 제안 · 라벨에만 있는 영역(자홍). 잎이 가로지른 사과, 잎 뒤에 숨은 사과가 원으로 칠해져 있습니다.')
d.fullfig(I / 'round2_apple/sheets/apple_check1201/a000.jpg', caption='그림 3. dataset1 — 보이는 부분만 정밀하게 칠함', sub='같은 사과 데이터셋 안인데 출처가 다르면 규칙이 다릅니다. 1차가 «동그랗게» 의 증거로 든 dataset1_front_1201 은 실제로는 서로 닿은 두 개체였습니다.')
d.h2('3-3. 분할표와의 관계')
_fa, _fb = fold_cross('apple', 'main_fold'), fold_cross('blueberry', 'main_fold')
d.p('교수님 v3 분할표는 MinneApple 670장을 촬영 시퀀스 단위로 묶어서, 5프레임 이웃 409쌍 중 학습/시험으로 갈라지는 쌍은 **0** 입니다(직접 셈). 그런데 중복을 눈으로 다시 보고 나니 **사과는 제외 그룹 %d개 중 %d개, 분할용 묶음(`split_group`) %d개 중 %d개가 그 표의 `main_fold` 를 넘습니다**(그 칸이 채워진 %s장 기준으로 직접 셈. 블루베리는 어느 것도 넘지 않아 %d개·%d개입니다). dataset1~4 의 331장은 장마다 따로 묶여 있으니, 분할표를 다시 만들 때 dataset1~4 도 영상 이름으로 묶을 것을 권합니다.'
    % (ngrp['apple'], _fa[0], len(sgc['apple']), _fa[1], format(_fa[2], ','), _fb[0], _fb[1]))
d.p('`manifest.csv` 에는 묶음 칸이 둘 있습니다. **`session` = 촬영 단위**(사과는 파일명에서 끝 번호를 뗀 것, 블루베리는 «Camera N Video (X)»)이고 **`split_group` = 확인된 관계로 이어 붙인 덩어리**입니다. 둘 다 빈칸이 없습니다. 확인: 확인된 관계 %s개 중 `split_group` 을 넘는 것 **0개** · `session` 을 넘는 것 **0개** · `split_group` 이 두 `session` 에 걸친 경우 **0개**. 실제로 5-폴드를 만들어 봐도 폴드를 넘는 관계가 **0** 입니다(촬영 기준 폴드 크기 사과 84·78·78·95·94 — 촬영이 %d개뿐이라 ±10%% 흔들립니다 · 블루베리 223·223·223·223·222). **즉 누수를 막기 위해 사진을 더 지울 필요는 없습니다.**'
    % (format(sum(nrel['apple'].values()) + sum(nrel['blueberry'].values()), ','), len(sess['apple'])))
d.warn('**분할은 `session`(촬영) 단위 GroupKFold 를 권고합니다.** `split_group` 은 «그보다 잘게 나눌 때 지켜야 하는 최소 조건» 으로 쓰십시오. '
       '이유: 위의 «폴드를 넘는 관계 0» 은 **«확인된 관계 기준» 0** 일 뿐이고, 아직 아무도 눈으로 보지 않은 쌍이 **254개** 남아 있어(§3-4 마지막) 그중 일부가 서로 다른 `split_group` 에 들어 있을 수 있습니다. '
       '더 거친 묶음인 `session` 을 기본으로 쓰면 그 위험까지 덮습니다.', head='어느 칸으로 폴드를 나눌 것인가')

# ── §3-4 얼마나 솎을 것인가 (2026-09-18 최종 동결에서 신설) ─────────────────────
d.h2('3-4. 얼마나 솎을 것인가 — 멈춤점이 없습니다')
d.warn('사과 사진은 **천천히 걸으며 찍은 영상**에서 뽑은 것입니다. 그래서 «거의 같은 사진» 이 있다/없다로 갈리지 않고 **연속체**입니다. 위 §3-1 에서 보신 대로 확인하는 범위를 넓힐 때마다 더 나왔습니다(**687 → 549 → 547 → %d**). '
       '**쌍을 하나씩 지우는 방식에는 자연스러운 멈춤점이 없습니다.** 게다가 이 판정은 자로 잰 값이 아니라 판정이고 판정자 차이가 큽니다(§3-1 마지막 상자). '
       '그래서 저희가 임의로 한 단계 더 자르지 않고, **간격별 곡선과 결정적 대안표를 만들어 교수님 결정으로 올립니다.**', head='왜 «여기까지» 를 저희가 못 정하는가')
d.p('**프레임 간격별 «거의 같은 사진» 비율을 실제로 쟀습니다.** 판정자에게는 파일 목록만 주고 **간격·점수를 알려 주지 않았습니다**. 기준은 §3-1 과 같습니다(화면 약 80%% 이상 같음 · 표식 이동 20%% 이내 · 배율 차 거의 없음). 합 **%d쌍**이고, «전혀 다른 장면» 판정은 **%d건** — 같은 촬영 안에서는 아무리 멀어도 같은 과수원이라는 뜻입니다.'
    % (n_pair_curve, n_diff_curve))
d.table(['출처', '프레임 간격', '본 쌍', '거의 같은 사진', '비율', '다른 장면'],
        [[s, str(g), format(v[0], ','), str(v[1]), ('**%.0f%%**' % (100 * v[1] / v[0])) if 100 * v[1] / v[0] < 20 else '%.0f%%' % (100 * v[1] / v[0]), str(v[2])]
         for (s, g), v in sorted(CURVE.items(), key=lambda kv: (kv[0][0], kv[0][1]))], [.24, .16, .15, .19, .13, .13])
d.p('**비율이 처음 20%% 아래로 떨어지는 지점은 현장 %d프레임 · dataset %d프레임**입니다(굵게 표시한 칸). 간격 5 의 100%% 는 3차 보충 검수에서 %d쌍을 전수로 본 값입니다.'
    % (below20['현장(MinneApple)'], below20['dataset1~4'], n_frameadj))
d.p('이 곡선을 그대로 규칙으로 바꾼 것이 아래 **간격 솎기 대안**입니다. «같은 촬영에서 프레임 번호가 G 이상 떨어진 사진만 차례로 남긴다» — **눈 판정이 전혀 들어가지 않으므로 누가 다시 돌려도 같은 결과**가 나옵니다(논문에 규칙 한 줄로 쓸 수 있습니다). 목록은 `round3_final/v2/stride_variants_apple.csv` 에 이미 만들어 뒀습니다(원본 %s행 · 대안별 0/1 열).'
    % format(len(man['apple']), ','))
d.table(['대안', '현장 G', 'dataset G', '남는 장수', '그중 사람 확인(flag)'],
        [[('**%s** ← 곡선 20%% 지점' % nm) if (gm, gd) == (below20['현장(MinneApple)'], below20['dataset1~4']) else nm,
          str(gm), str(gd), '**%s**' % format(n, ','), str(nf)] for nm, gm, gd, n, nf in STRIDE]
        + [['(지금 이 폴더 = `keep_current`)', '—', '—', '**%s**' % format(nkept['apple'], ','), str(cnt['apple']['needs_human'])]],
        [.34, .14, .16, .18, .18])
d.p('**교수님께 드리는 선택지 — 자세한 것은 `문서/260917_교수님확인_7건.md` 16번입니다.**')
d.steps(['**①  지금 판 그대로 %d장** — 눈으로 확인된 관계를 전부 반영한 판. 실제로 본 것만 뺐다는 것이 장점이고, 판정자에 따라 흔들린다는 것이 단점입니다.' % nkept['apple'],
         '**②  간격 솎기 %s장 중 하나** — 재현 가능하고 규칙이 한 줄입니다. 곡선상 20%% 지점은 **%s장**입니다. 실제로 다른 사진도 규칙에 걸려 빠질 수 있다는 것이 단점입니다.'
         % (' / '.join(format(n, ',') for _, _, _, n, _ in STRIDE[:3]), format([n for nm, _, _, n, _ in STRIDE if nm == 'keep_G%d_%d' % (below20['현장(MinneApple)'], below20['dataset1~4'])][0], ',')),
         '**③  솎지 않고 촬영 단위로 묶기만** — 표본을 안 버리고 누수는 분할로 막습니다. «표본 수가 부풀려졌다» 는 지적을 받을 수 있다는 것이 단점입니다.'],
        )
d.note('**셋 중 무엇을 고르셔도 폴드 누수는 `session`(촬영) 단위 분할로 막습니다**(§3-3). 지우는 것은 누수 때문이 아니라 «표본 수를 정직하게 세기» 위한 것입니다. 그리고 ②를 고르셔도 **이 폴더의 사진을 지우지 않습니다** — CSV 의 해당 열로 학습 목록만 걸러 쓰면 됩니다.')
d.warn('**우리 권고를 한 줄로 적으면 이렇습니다.** «촬영(`session`) 단위로 폴드를 나누고, 장수는 간격 솎기 `keep_G%d_%d`(**%s장** — 위 곡선이 20%% 아래로 꺾이는 지점)를 씁니다. 눈 판정이 안 들어가 **누가 다시 돌려도 같은 결과**입니다. 지금 폴더의 %s장 판은 눈 판정에 기대므로 **차선**입니다. **최종 선택은 교수님.»**\n\n'
       '덧붙여 두 가지를 함께 지키겠습니다. ① 이 폴더를 «중복 제거된 데이터셋» 이라고 부르지 않고 **«눈 검토 기반 부분 중복 제거(판정자 일치 κ 0.51~0.72)»** 라고 씁니다. ② 사과는 amodal·modal 라벨이 섞여 있으므로 **성능을 출처별(MinneApple / dataset1~4)로 나눠 보고**합니다.'
       % (below20['현장(MinneApple)'], below20['dataset1~4'],
          format([n for nm, _, _, n, _ in STRIDE if nm == 'keep_G%d_%d' % (below20['현장(MinneApple)'], below20['dataset1~4'])][0], ','),
          format(nkept['apple'], ',')), head='우리 권고 (DeepSeek 확인 결과를 총괄이 수용)')
d.warn('«확인 범위» 안(현장 간격 %d 이하 · dataset %d 이하)에는 아무도 안 본 쌍이 **0개**입니다. 범위 **밖**(현장 25~60 · dataset 60)에는 아직 아무도 안 본 쌍이 **254쌍** 있고, 위 곡선을 곱하면 그중 **약 70쌍**이 «거의 같은 사진» 일 것으로 추정됩니다(±20쌍). 이것이 ①번 %d장의 알려진 한계 크기입니다 — ②를 고르시면 이 한계는 사라집니다.'
       % (20, 30, nkept['apple']), head='①번을 고르실 때 같이 적어야 하는 한계')

d.h1('4. 블루베리')
d.fullfig(I / 'round2_blueberry/sheets/dup_cam4/001.jpg', caption='그림 4. 블루베리 4번 카메라 — 한 송이를 확대만 한 프레임', sub='Camera 4 Video (5) 의 프레임 1·61·121·181. 영상 33개가 전부 이런 식이라 영상마다 대표 1장만 남겼습니다.')
d.fullfig(I / 'round2_blueberry/sheets/cand/c004.jpg', caption='그림 5. 블루베리 «라벨 없음» 후보의 실제 모습', sub='하늘색 네모가 AI 만 잡은 곳, 자홍이 원본 라벨. 초점 밖 뒷줄 열매 · 마른 꽃부리 · 막 맺힌 초록 열매 — 빠뜨린 것이 아니라 «칠할 대상인가» 가 정해지지 않은 것들입니다.')
d.p('명백한 마스크 오류는 3장(전부 2번 카메라의 두 영상: `Camera 2 Video (9)_541` · `(7)_121` · `(7)_361`)이고, 무작위 60장에서는 0장이었습니다. 검출 팀의 watershed 초벌 번호 45,124개는 전부 원본 라벨 안에 있습니다 — 라벨이 빠뜨린 열매는 카운팅 정답에서도 빠지지만, 진짜 누락이 3개뿐이라 영향은 장당 0.003알입니다.')

d.h1('5. 교수님께 여쭐 것')
d.steps(['**사과를 얼마나 솎을까요 — 가장 중요한 질문입니다(§3-4)**: ① 지금 판 **%s장** · '
         '② 간격 솎기 **%s장** 중 하나(곡선 20%% 지점은 %s장) · ③ 솎지 않고 촬영 단위로 묶기만. '
         '«거의 같은 사진» 이 연속체라 멈춤점이 없어서 저희가 정하지 못했습니다'
         % (format(nkept['apple'], ','), ' / '.join(format(n, ',') for _, _, _, n, _ in STRIDE[:3]),
            format([n for nm, _, _, n, _ in STRIDE if nm == 'keep_G%d_%d' % (below20['현장(MinneApple)'], below20['dataset1~4'])][0], ',')),
         '**사과 — 가려진 부분까지(amodal) vs 보이는 것만(modal)**: 출처마다 다릅니다. 어느 쪽으로 통일할까요?',
         '**사과 — 낙과와 뒷줄 나무**: 낙과가 보이는 42장 중 5장만 라벨돼 있습니다. 셀까요?',
         '**블루베리 — 마른 꽃부리·어린 초록 열매·초점 밖 뒷줄 열매**를 열매로 칠할까요? (후보의 절반 이상이 마른 꽃부리)',
         '**블루베리 — 같은 포기가 겹쳐 보이는 50쌍(사진 93장, 이어 보면 묶음 43개)**을 뺄까요? '
         '(묶음마다 1장씩만 남기면 %s → **1,074장**. 분할이 영상 단위라 누수는 없고 표본 수만 부풀립니다)' % format(nkept['blueberry'], ','),
         '**사과 «겹치는 이웃» %d장**을 더 솎아낼까요, 분할에서 같은 폴드로 묶기만 할까요? '
         '(묶음마다 1장이면 %d → **%d장**, 서로 겹치지만 않게 솎으면 **%d장**. 이 관계 %d쌍 중 눈으로 본 것은 %d쌍뿐입니다. 위 첫 질문과 같은 질문의 일부입니다)'
         % (thin['apple']['photos'], nkept['apple'], thin['apple']['one'], thin['apple']['indep'], thin['apple']['pairs'], thin['apple']['eye'] + gap_ov),
         '**«거의 같은 사진» 판정을 사람이 표본으로 다시 볼까요?** AI 판정자끼리도 사과 78~88%·블루베리 59~79% 만 일치하고, '
         '같은 표본을 반씩 나눠 본 두 판정자는 78% 대 60% 였습니다(§3-1). 수십 쌍만 직접 봐 주시면 이 기준이 사람 눈과 맞는지 확인됩니다',
         '중복을 뺀 뒤 **분할표를 다시 만들어야** 합니다(폴드별로 불균등하게 빠짐). **`manifest.csv` 의 `session` 칸을 `GroupKFold` 에 넣는 것을 권고**합니다',
         '**교수님이 0915 에 보신 «동그랗게» 사진이 어느 쪽이었는지** 짚어 주시겠습니까 — 그림 2(MinneApple, 가려진 데까지) 인지 그림 3(dataset1, 보이는 것만) 인지. '
         '참고로 사과 라벨 개체 중 «구멍» 이 있는 것은 38,781개 중 **180개(0.46%)** 이므로, 쟁점은 «중간이 안 비었다» 가 아니라 **가려진 부분을 원으로 메웠다** 는 쪽입니다'])

for f in KO:
    cells, ng = dup_cells(f)
    d.h1('부록 %s. %s — 뺀 사진 전부 (%d장, 남긴 대표 %d장)' % ('A' if f == 'apple' else 'B', KO[f], cnt[f]['excluded_duplicate'], ng))
    d.p('초록 테두리 = 남긴 사진, 그 뒤의 빨강 테두리 = 그 사진과 거의 같아서 뺀 사진. 파일은 지우지 않았고 새 폴더에 넣지 않았을 뿐입니다.')
    for q in grid(cells, 'dup_' + f): d.fullfig(q)
for f in KO:
    cells = flag_cells(f)
    d.h1('부록 %s. %s — 사람이 툴에서 볼 사진 (%d장)' % ('C' if f == 'apple' else 'D', KO[f], len(cells)))
    d.p('빨강 = 원본 라벨, 노랑 네모 = AI 가 «라벨 없는 열매» 로 짚은 자리. 툴에서 상태 «문제 있음» 으로 걸러 보면 같은 사진들이 나오고, 메모에 좌표가 들어 있습니다.')
    for q in grid(cells, 'flag_' + f, cols=4, cw=310, ch=264): d.fullfig(q)

d.h1('부록 E. 파일 위치')
d.table(['무엇', '어디'], [
    ['새 데이터셋', '`kds0206/datasets_reviewed_260917/{apple,blueberry}/` + `manifest.csv`(stem · image_source · mask_source · action · note · rule_pending · overlap_neighbors · **split_group** · **session**(촬영 단위 — 분할의 권고 기준)). 첫 판은 `_v1_260917/`'],
    ['숫자 사전(최종 동결판)', '`260916_라벨링툴/cycles/260917_ab/cycle_5/stage2/number_dict_final.md` — 이 PDF 의 모든 숫자를 원천에서 다시 센 표(그 앞 판 `cycle_3/stage3/number_dict.md` 는 547장 기준이니 인용하지 말 것)'],
    ['간격별 곡선 · 간격 솎기 대안표', '`inspect/…/round3_final/v2/curve_stride_apple.md` · `stride_variants_apple.csv`(생성기 `curve_and_stride.py`) — §3-4 의 원천'],
    ['2단계 눈 판정', '`inspect/…/round3_final/v2/gap_eye_part{1,2}.csv`(열쇠 `gap_unseen_key.csv`) · 곡선용 `curve_eye_part{1,2}.csv`(열쇠 `curve_pairs_key.csv`)'],
    ['총괄 판정서', '`kds0206/문서/260918_사과블루베리_5회검수_최종판정.md` — 열린 문제 46건 · 한계 문장 · 사람이 할 일 순서'],
    ['판정자 간 일치도', '`inspect/…/round3_final/v2/interrater_{pairs,A,B,majority}.csv` · `interrater_agreement.md`'],
    ['3차 판정서', '`260916_라벨링툴/inspect/260917_apple_blueberry/260917_사과블루베리_3차판정.md`'],
    ['1차·2차·보충', '같은 폴더의 `round1/` · `round2_apple/` · `round2_blueberry/` · `round3_apple_frameadj/` · `round3_final/`'],
    ['실행 스크립트', '`inspect/…/round3_final/v2/build_exclusion_v2.py` → `260916_라벨링툴/final/build_reviewed_dataset_260917_v2.py`(멱등). 첫 판 `…_260917.py` 는 다시 돌리지 말 것'],
    ['재검수 기록', '`260916_라벨링툴/cycles/260917_ab/cycle_<n>/`'],
    ['툴 반영', '`data/{apple,blueberry}/status.json`(제외·문제 있음만) · `duplicates.json`(옛 것 `duplicates_round1.json`)'],
], [.22, .78])
d.save()
print('saved', OUT, {f: dict(cnt[f]) for f in KO})
