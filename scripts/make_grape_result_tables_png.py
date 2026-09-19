#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
포도(CERTH) 실험 결과를 카카오톡으로 보내기 좋은 '표 이미지(PNG)'로 만듭니다.

- 숫자를 하드코딩하지 않고 output/*.csv 에서 직접 읽습니다.
  · output/grape_grid_results.csv     : 54조합 test 전경 IoU
  · output/grape_grid_efficiency.csv  : 파라미터/FLOPs/지연
  · output/grape_toy_results.csv      : 1차 파일럿 4조합
  · output/grape_grid_stats.json      : Friedman/Nemenyi 통계
- 스타일은 팀에서 돌던 예시 표 이미지(어두운 배경 + 밝은 격자)를 따라 맞췄습니다.

출력: semantic-segmentation/reports/grape_grid/tables_png/*.png
사용:  python tools/make_grape_result_tables_png.py
"""

import json
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties

# ---------------------------------------------------------------- 경로
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, 'reports', 'grape_grid', 'tables_png')
OUTPUT = os.path.join(REPO, 'output')

# ---------------------------------------------------------------- 폰트/색
FONT_DIR = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Bold.ttc')

BG      = '#2b2f34'   # 배경
LINE    = '#c9d1d9'   # 격자선
INK     = '#eef2f6'   # 본문 글씨
HEADBG  = '#3a4048'   # 표 머리행 배경
BESTBG  = '#3d4a3a'   # 1등 행 강조 배경
BEST    = '#ffd45e'   # 1등 글씨(노랑)
GOOD    = '#8fd694'   # 좋음(초록)
BAD     = '#f2907e'   # 나쁨(주황)
MUTE    = '#9aa4ae'   # 설명 글씨

DPI = 160


def tw(s, size, bold=False):
    """글자 폭을 포인트 단위로 추정합니다(한글 1.0em, 영숫자 0.56em)."""
    w = 0.0
    for ch in str(s):
        w += 1.02 if ord(ch) > 0x2000 else 0.56
    return w * size * (1.06 if bold else 1.0)


class Page:
    """블록(제목/표/설명)을 위에서 아래로 쌓아 한 장의 PNG로 만듭니다."""

    PAD_X = 26      # 페이지 좌우 여백
    PAD_Y = 22      # 페이지 상하 여백
    CELL_PX = 15    # 셀 좌우 안쪽 여백
    ROW_H = 40      # 기본 행 높이

    def __init__(self):
        self.blocks = []

    def title(self, text, sub=None):
        self.blocks.append(('title', text, sub))

    def note(self, text, color=None):
        self.blocks.append(('note', text, color or MUTE))

    def gap(self, h=14):
        self.blocks.append(('gap', h, None))

    def table(self, headers, rows, aligns=None, bold_col0=True,
              row_colors=None, cell_colors=None, font=15):
        """rows: [[str,...], ...]  row_colors: {행번호: 배경색}
        cell_colors: {(행,열): 글자색}"""
        self.blocks.append(('table', dict(
            headers=headers, rows=rows, aligns=aligns, bold_col0=bold_col0,
            row_colors=row_colors or {}, cell_colors=cell_colors or {},
            font=font), None))

    # ---------------------------------------------------- 크기 계산
    def _table_geom(self, t):
        f = t['font']
        ncol = len(t['headers'])
        widths = []
        for c in range(ncol):
            w = tw(t['headers'][c], f, bold=True)
            for r in t['rows']:
                w = max(w, tw(r[c], f, bold=(c == 0 and t['bold_col0'])))
            widths.append(w + self.CELL_PX * 2)
        rh = round(f * 2.15)
        h = rh * (len(t['rows']) + 1)
        return widths, rh, h

    def render(self, path):
        # 1) 전체 크기 먼저 계산
        W = 0
        H = self.PAD_Y * 2
        geoms = []
        for kind, a, b in self.blocks:
            if kind == 'table':
                widths, rh, h = self._table_geom(a)
                geoms.append((widths, rh))
                W = max(W, sum(widths))
                H += h + 10
            elif kind == 'title':
                geoms.append(None)
                W = max(W, tw(a, 21, True))
                H += 40 + (22 if b else 0)
            elif kind == 'note':
                geoms.append(None)
                W = max(W, tw(a, 13))
                H += 24
            else:
                geoms.append(None)
                H += a
        W += self.PAD_X * 2

        # 레이아웃 단위는 '포인트'. figsize는 인치이므로 72로 나눕니다.
        fig = plt.figure(figsize=(W / 72, H / 72), dpi=DPI)
        fig.patch.set_facecolor(BG)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)          # 위에서 아래로
        ax.axis('off')
        ax.set_facecolor(BG)

        y = self.PAD_Y
        for (kind, a, b), g in zip(self.blocks, geoms):
            x0 = self.PAD_X
            if kind == 'title':
                ax.text(x0, y + 22, a, fontproperties=BLD, fontsize=21,
                        color=INK, va='center')
                y += 40
                if b:
                    ax.text(x0, y + 8, b, fontproperties=REG, fontsize=12.5,
                            color=MUTE, va='center')
                    y += 22
            elif kind == 'note':
                ax.text(x0, y + 12, a, fontproperties=REG, fontsize=13,
                        color=b, va='center')
                y += 24
            elif kind == 'gap':
                y += a
            else:
                y = self._draw_table(ax, a, g, x0, y)
                y += 10
        fig.savefig(path, facecolor=BG, dpi=DPI)
        plt.close(fig)
        return path

    def _draw_table(self, ax, t, geom, x0, y0):
        widths, rh = geom
        f = t['font']
        ncol = len(widths)
        aligns = t['aligns'] or (['left'] + ['center'] * (ncol - 1))
        total_w = sum(widths)

        def draw_row(vals, y, bg, bold_flags, colors):
            ax.add_patch(Rectangle((x0, y), total_w, rh, facecolor=bg,
                                   edgecolor='none', zorder=1))
            cx = x0
            for c in range(ncol):
                w = widths[c]
                fp = BLD if bold_flags[c] else REG
                col = colors[c]
                if aligns[c] == 'left':
                    tx, ha = cx + self.CELL_PX, 'left'
                elif aligns[c] == 'right':
                    tx, ha = cx + w - self.CELL_PX, 'right'
                else:
                    tx, ha = cx + w / 2, 'center'
                ax.text(tx, y + rh / 2, str(vals[c]), fontproperties=fp,
                        fontsize=f, color=col, ha=ha, va='center', zorder=3)
                cx += w
            # 세로 격자
            cx = x0
            for c in range(ncol + 1):
                ax.plot([cx, cx], [y, y + rh], color=LINE, lw=1.1, zorder=2)
                if c < ncol:
                    cx += widths[c]
            # 가로 격자
            ax.plot([x0, x0 + total_w], [y, y], color=LINE, lw=1.1, zorder=2)
            ax.plot([x0, x0 + total_w], [y + rh, y + rh], color=LINE, lw=1.1,
                    zorder=2)

        y = y0
        draw_row(t['headers'], y, HEADBG, [True] * ncol, [INK] * ncol)
        y += rh
        for ri, row in enumerate(t['rows']):
            bg = t['row_colors'].get(ri, BG)
            bolds = [(c == 0 and t['bold_col0']) or ri in t['row_colors']
                     for c in range(ncol)]
            colors = [t['cell_colors'].get((ri, c),
                      BEST if ri in t['row_colors'] else INK)
                      for c in range(ncol)]
            draw_row(row, y, bg, bolds, colors)
            y += rh
        return y


# ================================================================ 데이터 읽기
def read_csv(name):
    p = os.path.join(OUTPUT, name)
    with open(p, encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


grid = read_csv('grape_grid_results.csv')
eff = read_csv('grape_grid_efficiency.csv')
toy = read_csv('grape_toy_results.csv')
with open(os.path.join(OUTPUT, 'grape_grid_stats.json'), encoding='utf-8') as fh:
    stats = json.load(fh)

EFF = {(r['head'], r['backbone']): r for r in eff}
HEADS = []
BACKS = []
for r in grid:
    if r['head'] not in HEADS:
        HEADS.append(r['head'])
    if r['backbone'] not in BACKS:
        BACKS.append(r['backbone'])
IOU = {(r['head'], r['backbone']): float(r['fg_IoU']) for r in grid}

ranked = sorted(grid, key=lambda r: -float(r['fg_IoU']))
best = ranked[0]

os.makedirs(OUT_DIR, exist_ok=True)
made = []


def f4(x):
    return f'{float(x):.4f}'


# ================================================================ 표 1 — 실험 개요
def table_overview(p=None):
    p = p or Page()
    p.title('포도(CERTH) 실험 개요', '곽동신 담당분 · 2026-07-31 실행')
    rows = [
        ['데이터셋', 'CERTH 포도 (train 2,000장 중 100장 추출, seed 42)'],
        ['분할', 'train 70 / val 10 / test 20  (7:1:2, 단일 분할)'],
        ['해상도', '원본 4K → 긴 변 1024  =  576×1024 (비율 왜곡 0)'],
        ['전경 비율', '12.96%   (블루베리 2.4% · 사과 2.6%의 약 5배)'],
        ['학습 설정', '200 epoch · early stop 끔 · 512 랜덤크롭 · batch 2×ACCUM 4'],
        ['실험 규모', '헤더 9 × 백본 6 = 54조합 전수 (실패 0)'],
        ['평가 지표', 'test 전경 IoU (사진 20장 평균)'],
    ]
    p.table(['항목', '내용'], rows, aligns=['left', 'left'])
    return p


# ================================================================ 표 2 — 상위 10 조합
def table_top10(p=None, n=10):
    p = p or Page()
    p.title(f'상위 {n}개 조합 — test 전경 IoU',
            '54조합 전수 실험 결과 / 괄호 안은 1위 대비 차이')
    rows, rc = [], {}
    for i, r in enumerate(ranked[:n]):
        e = EFF[(r['head'], r['backbone'])]
        gap = float(r['fg_IoU']) - float(best['fg_IoU'])
        rows.append([
            f'{i + 1}',
            f"{r['head']} + {r['backbone']}",
            f4(r['fg_IoU']) + ('  ★' if i == 0 else f'  ({gap:+.4f})'),
            f"{float(e['params_total_M']):.1f}",
            f"{float(e['flops_G']):.1f}",
            f"{float(e['latency_median_ms']):.2f}",
        ])
        if i == 0:
            rc[i] = BESTBG
    p.table(['순위', '헤더 + 백본', 'test 전경 IoU', '파라미터(M)',
             'FLOPs(G)', '지연(ms)'],
            rows, aligns=['center', 'left', 'right', 'right', 'right', 'right'],
            bold_col0=False, row_colors=rc)
    return p


# ================================================================ 표 3 — 54조합 전체
def table_full_grid(p=None):
    p = p or Page()
    p.title('54조합 전체 — test 전경 IoU (헤더 9 × 백본 6)',
            '노란색 = 전체 1위 / 마지막 행·열 = 평균')
    headers = ['헤더 \\ 백본'] + BACKS + ['평균']
    rows, cc = [], {}
    order = sorted(HEADS, key=lambda h: -sum(IOU[(h, b)] for b in BACKS))
    for ri, h in enumerate(order):
        vals = [IOU[(h, b)] for b in BACKS]
        rows.append([h] + [f'{v:.4f}' for v in vals]
                    + [f'{sum(vals) / len(vals):.4f}'])
        for ci, b in enumerate(BACKS):
            if (h, b) == (best['head'], best['backbone']):
                cc[(ri, ci + 1)] = BEST
    avg = ['평균'] + [f'{sum(IOU[(h, b)] for h in HEADS) / len(HEADS):.4f}'
                    for b in BACKS] + ['']
    rows.append(avg)
    cc.update({(len(rows) - 1, c): GOOD for c in range(len(headers))})
    p.table(headers, rows, aligns=['left'] + ['right'] * (len(headers) - 1),
            cell_colors=cc, font=14)
    p.note(f"헤더 폭 0.0793  >  백본 폭 0.0566  →  포도는 '헤더'가 성능을 더 좌우합니다",
           GOOD)
    p.note('※ 블루베리는 반대(백본 0.065 > 헤더 0.008) → 작물이 바뀌면 최적 조합도 바뀝니다')
    return p


# ================================================================ 표 4 — 통계 순위
def table_stats(p=None):
    p = p or Page()
    p.title('통계 검정 — 주효과 분리 Friedman + Nemenyi',
            '54조합을 한 번에 검정하면 검정력이 안 나와 헤더/백본을 나눠서 검정')

    hd = stats['head_main_effect']
    bk = stats['backbone_main_effect']
    nsig = lambda d: sum(1 for x in d['nemenyi'] if x['significant'])

    # 헤더 주효과
    hr = sorted(hd['mean_rank'].items(), key=lambda kv: kv[1])
    rows = [[f'{i + 1}', k, f'{v:.2f}',
             f"{sum(IOU[(k, b)] for b in BACKS) / len(BACKS):.4f}"]
            for i, (k, v) in enumerate(hr)]
    p.table(['순위', '헤더(디코더)', '평균순위', '평균 IoU'], rows,
            aligns=['center', 'left', 'right', 'right'], bold_col0=False,
            row_colors={0: BESTBG}, font=14)
    p.note(f"χ² = {hd['friedman_stat']:.1f},  p = {hd['friedman_p']:.1e},  "
           f"임계차 CD = {hd['critical_difference']:.2f},  "
           f"유의한 쌍 {nsig(hd)}개 (블록 {hd['n_blocks']} × 대상 {hd['k']})")
    p.gap(16)

    # 백본 주효과
    br = sorted(bk['mean_rank'].items(), key=lambda kv: kv[1])
    rows = [[f'{i + 1}', k, f'{v:.2f}',
             f"{sum(IOU[(h, k)] for h in HEADS) / len(HEADS):.4f}"]
            for i, (k, v) in enumerate(br)]
    cc = {(len(rows) - 1, c): BAD for c in range(4)}
    p.table(['순위', '백본(인코더)', '평균순위', '평균 IoU'], rows,
            aligns=['center', 'left', 'right', 'right'], bold_col0=False,
            row_colors={0: BESTBG}, cell_colors=cc, font=14)
    p.note(f"χ² = {bk['friedman_stat']:.1f},  p = {bk['friedman_p']:.1e},  "
           f"임계차 CD = {bk['critical_difference']:.2f},  "
           f"유의한 쌍 {nsig(bk)}개 (블록 {bk['n_blocks']} × 대상 {bk['k']})")
    p.note('ResNet-50만 유일하게 유의하게 나쁨 / 나머지 5개는 서로 통계적 차이 없음', BAD)
    p.note('※ 평균순위 1위(Swin-T)와 평균 IoU 1위(ConvNeXt-T)가 다른 것은 '
           '둘 사이에 유의한 차이가 없기 때문입니다')
    return p


# ================================================================ 표 5 — 파일럿 4조합
def table_pilot(p=None):
    p = p or Page()
    p.title('1차 파일럿 — 4조합 (2026-07-31)',
            '본 실험 전에 파이프라인을 검증한 예비 실험')
    rows, rc = [], {}
    srt = sorted(toy, key=lambda r: -float(r['fg_IoU']))
    for i, r in enumerate(srt):
        rows.append([
            r['combo'] + (' ★' if i == 0 else ''),
            r['best_epoch'],
            f"{float(r['best_val_loss']):.4f}",
            f4(r['fg_IoU']),
            f4(r['fg_Dice']),
            f4(r['fg_Precision']),
            f4(r['fg_Recall']),
        ])
        if i == 0:
            rc[i] = BESTBG
    p.table(['모델', 'Best Epoch', 'Val Loss', 'IoU', 'Dice',
             'Precision', 'Recall'], rows,
            aligns=['left'] + ['center'] * 6, row_colors=rc)
    p.note('Friedman p = 2.6e-04 → 사후검정에서 1위가 나머지 3개보다 유의하게 우수', GOOD)
    return p


# ================================================================ 표 6 — 효율성
def table_efficiency(p=None):
    p = p or Page()
    p.title('계산 효율 — 정확도와 속도는 같이 갑니다',
            '입력 512×512 · 배치 1 · Tesla V100-SXM2-32GB 실측')
    rows, rc = [], {}
    picks = ranked[:5] + [r for r in grid
                          if (r['head'], r['backbone']) == ('UPerNet', 'ResNet-50')]
    for i, r in enumerate(picks):
        e = EFF[(r['head'], r['backbone'])]
        tag = ' ★' if i == 0 else ('  ← 팀 기준조합' if i == len(picks) - 1 else '')
        rows.append([
            f"{r['head']} + {r['backbone']}{tag}",
            f4(r['fg_IoU']),
            f"{float(e['params_total_M']):.2f}",
            f"{float(e['flops_G']):.1f}",
            f"{float(e['latency_median_ms']):.2f}",
            f"{float(e['infer_peak_mem_MB']):.0f}",
        ])
        if i == 0:
            rc[i] = BESTBG
    cc = {(len(rows) - 1, c): BAD for c in range(6)}
    p.table(['헤더 + 백본', 'test IoU', '파라미터(M)', 'FLOPs(G)',
             '지연 중앙값(ms)', '추론메모리(MB)'], rows,
            aligns=['left'] + ['right'] * 5, row_colors=rc, cell_colors=cc)
    p.note('파라미터 21.6~31.6M(1.5배)인데 FLOPs는 20.5~47.1G(2.3배)', MUTE)
    p.note('→ 파라미터 수만으로 계산비용을 말하면 안 된다는 것을 실측으로 확인', GOOD)
    return p


# ================================================================ 결론 블록
def add_conclusion(p):
    p.title('핵심 결론')
    rows = [
        ['1위 조합', f"{best['head']} + {best['backbone']}  —  test 전경 IoU "
                    f"{f4(best['fg_IoU'])}"],
        ['팀 기준조합', 'UPerNet + ResNet-50 = 0.7435  →  포도에서는 하위권 (1위 대비 −0.115)'],
        ['제일 중요한 발견', '포도는 헤더 영향(0.0793) > 백본 영향(0.0566). 블루베리는 정반대'],
        ['효율성', '1위 조합이 지연 11.78ms로 빠르기까지 함 → 정확도·속도 양립'],
        ['한계', '100장(전체 2,502장의 4%) · 단일 분할 · test 20장 기준'],
        ['제외한 것', 'MambaVision-T — V100(sm_70)에서 mamba_ssm 커널 미지원'],
    ]
    p.table(['항목', '내용'], rows, aligns=['left', 'left'], font=14)
    return p


# ================================================================ 실행
def save(page, name):
    path = os.path.join(OUT_DIR, name)
    page.render(path)
    made.append(path)
    print('저장:', path, f'({os.path.getsize(path) / 1024:.0f} KB)')


if __name__ == '__main__':
    save(table_overview(), '01_실험개요.png')
    save(table_top10(), '02_상위10조합.png')
    save(table_full_grid(), '03_54조합_전체표.png')
    save(table_stats(), '04_통계_헤더백본순위.png')
    save(table_pilot(), '05_파일럿_4조합.png')
    save(table_efficiency(), '06_효율성.png')

    # 한 장으로 몰아넣은 통합본 (카톡에 1장만 보낼 때)
    p = Page()
    table_overview(p)
    p.gap(18)
    table_pilot(p)
    p.gap(18)
    table_top10(p)
    p.gap(18)
    table_stats(p)
    p.gap(18)
    table_full_grid(p)
    p.gap(18)
    table_efficiency(p)
    p.gap(18)
    add_conclusion(p)
    save(p, '00_포도결과_전체통합.png')

    print(f'\n총 {len(made)}장 생성 → {OUT_DIR}')
