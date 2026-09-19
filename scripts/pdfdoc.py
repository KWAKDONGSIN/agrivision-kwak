# -*- coding: utf-8 -*-
"""한글 PDF 교재를 만들기 위한 공용 렌더러.

matplotlib만으로 A4 문서를 그린다 (LaTeX 설치 불필요).
- 본문에서 **강조** 표시를 쓰면 실제 굵은 글씨로 나온다 (글자 폭을 재서 이어 붙임)
- 제목/소제목/표/색상박스/코드블록/그림/전면그림/용어카드 지원
- 쪽번호와 꼬리말 자동

사용법:
    from pdfdoc import Doc
    d = Doc('/경로/파일.pdf', title='제목', subtitle='부제', volume='1권')
    d.h1('큰 제목'); d.p('본문 **강조** 포함'); d.table([...], [...], [.3,.5])
    d.save()
"""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

FONT_DIR = '/usr/share/fonts/opentype/noto/'
REG = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname=FONT_DIR + 'NotoSansCJK-Bold.ttc')
MONO = FontProperties(family='DejaVu Sans Mono')

INK = '#111111'
MUTE = '#5b6270'
BLUE = '#1c5cab'
GOOD = '#0a7d33'
WARN = '#8a6d00'
BAD = '#b23b3b'
LINE = '#c9ced8'

PW, PH = 8.27, 11.69          # A4 (inch)
LM, RM = 0.095, 0.925         # 좌우 여백 (그림 좌표 0~1)
TOP, BOT = 0.935, 0.062       # 본문 상/하한


class Doc:
    def __init__(self, out, title, subtitle='', volume='', footer='', date='2026-07-26'):
        self.out = Path(out)
        self.title, self.subtitle, self.volume = title, subtitle, volume
        self.footer = footer or title
        self.date = date          # 표지 하단에 찍히는 작성일 (기본값은 교재 8권 작성일)
        self.blocks = []
        self._toc = []

    # ------------------------------------------------------------ 블록 추가
    def _add(self, kind, payload):
        self.blocks.append((kind, payload))

    def cover(self, lines=None, badge=''):
        self._add('cover', (lines or [], badge))

    def toc(self, items):
        """items: [(번호, 제목, 한줄설명), ...]"""
        self._add('toc', items)

    def chapter(self, num, name, summary=''):
        """장 표지 (한 쪽 전체)"""
        self._add('chapter', (num, name, summary))
        self._toc.append((num, name))

    def h1(self, t): self._add('h1', t)
    def h2(self, t): self._add('h2', t)
    def h3(self, t): self._add('h3', t)
    def p(self, t): self._add('p', t)
    def bullets(self, items): self._add('bullets', items)
    def steps(self, items): self._add('steps', items)
    def code(self, t, caption=''): self._add('code', (t, caption))
    def formula(self, lines): self._add('formula', lines)
    def note(self, t, head='알아두기'): self._add(('box', 'note'), (head, t))
    def tip(self, t, head='이렇게 기억하세요'): self._add(('box', 'good'), (head, t))
    def warn(self, t, head='주의'): self._add(('box', 'warn'), (head, t))
    def quote(self, t, who='안홍렬 교수님'): self._add('quote', (t, who))
    def table(self, headers, rows, widths, size=9.3): self._add('table', (headers, rows, widths, size))
    def fig(self, path, height=0.28, caption=''): self._add('fig', (str(path), height, caption))
    def fullfig(self, path, caption='', sub=''): self._add('fullfig', (str(path), caption, sub))
    def gap(self, n=1): self._add('gap', n)
    def pagebreak(self): self._add('pagebreak', None)
    def qa(self, q, a): self._add('qa', (q, a))
    def term(self, word, eng, mean): self._add('term', (word, eng, mean))

    # ------------------------------------------------------------ 렌더링
    def save(self):
        with PdfPages(self.out) as pdf:
            self._render(pdf)
        print(f'저장: {self.out}')

    # 글자 폭 측정용 (강조 섞인 줄을 이어 붙이려면 필요)
    def _w(self, fig, s, fp, size):
        if not s:
            return 0.0
        t = fig.text(0, 0, s, fontproperties=fp, fontsize=size)
        try:
            bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
            return bb.width / fig.bbox.width
        finally:
            t.remove()

    @staticmethod
    def _runs(text):
        """'가 **나** 다' -> [('가 ',False), ('나',True), (' 다',False)]"""
        out = []
        text = text.replace('`', '')            # 마크다운 코드 표시는 지운다
        for i, part in enumerate(text.split('**')):
            if part:
                out.append((part, i % 2 == 1))
        return out or [('', False)]

    def _wrap_runs(self, fig, text, size, max_w):
        """강조 정보를 유지한 채 줄바꿈. [[(조각, 굵게), ...], ...] 반환."""
        lines, cur, cur_w = [], [], 0.0
        for seg, bold in self._runs(text):
            fp = BLD if bold else REG
            # 공백을 유지하며 어절 단위로 자른다
            token = ''
            for ch in seg:
                token += ch
                if ch == ' ':
                    w = self._w(fig, token, fp, size)
                    if cur_w + w > max_w and cur:
                        lines.append(cur); cur, cur_w = [], 0.0
                        token = token.lstrip()
                        w = self._w(fig, token, fp, size)
                    cur.append((token, bold)); cur_w += w; token = ''
            if token:
                w = self._w(fig, token, fp, size)
                if cur_w + w > max_w and cur:
                    lines.append(cur); cur, cur_w = [], 0.0
                    w = self._w(fig, token, fp, size)
                cur.append((token, bold)); cur_w += w
        if cur:
            lines.append(cur)
        return lines or [[('', False)]]

    def _render(self, pdf):
        st = {'fig': None, 'ax': None, 'y': 0.0, 'page': 0, 'first': True}

        def flush():
            if st['fig'] is not None:
                self._footer(st['fig'], st['ax'], st['page'])
                pdf.savefig(st['fig'])
                plt.close(st['fig'])

        def newpage(numbered=True):
            # 아직 아무것도 그리지 않은 빈 쪽이면 새로 만들지 않고 그대로 쓴다.
            # (toc 가 끝에서 newpage 를 부르고 chapter 가 또 부르기 때문에
            #  그냥 두면 차례 뒤에 빈 쪽이 한 장 끼어든다)
            cur = st['ax']
            if cur is not None and not (cur.texts or cur.patches or cur.images):
                if numbered and st['page'] == 0:
                    st['page'] = 1
                st['y'] = TOP
                return
            flush()
            f = plt.figure(figsize=(PW, PH))
            a = f.add_axes([0, 0, 1, 1]); a.axis('off')
            a.set_xlim(0, 1); a.set_ylim(0, 1)
            st['fig'], st['ax'] = f, a
            st['page'] = st['page'] + 1 if numbered else 0
            st['y'] = TOP

        def need(h):
            if st['y'] - h < BOT:
                newpage()

        newpage(numbered=False)

        for kind, payload in self.blocks:
            f, a = st['fig'], st['ax']

            if kind == 'cover':
                lines, badge = payload
                a.add_patch(plt.Rectangle((0, 0.80), 1, 0.006, color=BLUE))
                a.add_patch(plt.Rectangle((0, 0.145), 1, 0.006, color=BLUE))
                if self.volume:
                    a.text(0.5, 0.715, self.volume, ha='center',
                           fontproperties=BLD, fontsize=15, color=BLUE)
                a.text(0.5, 0.625, self.title, ha='center',
                       fontproperties=BLD, fontsize=27, color=INK)
                if self.subtitle:
                    for i, s in enumerate(textwrap.wrap(self.subtitle, 34)):
                        a.text(0.5, 0.565 - i * 0.032, s, ha='center',
                               fontproperties=REG, fontsize=13, color=MUTE)
                if badge:
                    a.text(0.5, 0.44, badge, ha='center',
                           fontproperties=BLD, fontsize=12, color=GOOD)
                for i, s in enumerate(lines):
                    a.text(0.5, 0.36 - i * 0.028, s, ha='center',
                           fontproperties=REG, fontsize=10.5, color=MUTE)
                a.text(0.5, 0.10, f'곽동신  ·  {self.date}', ha='center',
                       fontproperties=REG, fontsize=10.5, color=MUTE)
                a.text(0.5, 0.068, '블루베리 세그멘테이션 연구 · 안홍렬 교수님 연구실',
                       ha='center', fontproperties=REG, fontsize=9.5, color=MUTE)
                newpage()
                continue

            if kind == 'toc':
                a.text(LM, TOP, '이 책의 차례', fontproperties=BLD, fontsize=19, color=INK)
                y = TOP - 0.058
                for num, name, desc in payload:
                    a.text(LM, y, str(num), fontproperties=BLD, fontsize=12, color=BLUE)
                    a.text(LM + 0.045, y, name, fontproperties=BLD, fontsize=12, color=INK)
                    y -= 0.026
                    for ln in textwrap.wrap(desc, 46):
                        a.text(LM + 0.045, y, ln, fontproperties=REG, fontsize=9.8, color=MUTE)
                        y -= 0.021
                    y -= 0.014
                    if y < BOT + 0.05:
                        newpage(); a = st['ax']; y = TOP
                st['y'] = y
                newpage()
                continue

            if kind == 'chapter':
                num, name, summary = payload
                newpage()
                a = st['ax']
                a.add_patch(plt.Rectangle((LM - 0.02, 0.56), 0.83, 0.006, color=BLUE))
                a.text(LM, 0.66, f'{num}장', fontproperties=BLD, fontsize=14, color=BLUE)
                for i, s in enumerate(textwrap.wrap(name, 20)):
                    a.text(LM, 0.615 - i * 0.045, s, fontproperties=BLD, fontsize=23, color=INK)
                y = 0.51
                for ln in textwrap.wrap(summary, 42):
                    a.text(LM, y, ln, fontproperties=REG, fontsize=11.5, color=MUTE)
                    y -= 0.026
                st['y'] = BOT - 1
                continue

            if kind == 'pagebreak':
                newpage(); continue

            if kind == 'gap':
                st['y'] -= 0.013 * payload; continue

            if kind == 'fullfig':
                path, cap, sub = payload
                newpage()
                f, a = st['fig'], st['ax']
                a.text(LM - 0.015, 0.952, cap, fontproperties=BLD, fontsize=13.5, color=INK)
                if sub:
                    a.text(LM - 0.015, 0.926, sub, fontproperties=REG, fontsize=9.8, color=MUTE)
                try:
                    im = mpimg.imread(path)
                    h, w = im.shape[0], im.shape[1]
                    dw, box_h = 0.88, 0.845
                    dh = dw * (h / w) * (PW / PH)
                    if dh > box_h:
                        dw *= box_h / dh; dh = box_h
                    axim = f.add_axes([(1 - dw) / 2, 0.905 - dh, dw, dh])
                    axim.imshow(im); axim.axis('off')
                except Exception as e:
                    a.text(LM, 0.5, f'[그림 없음: {path} — {e}]',
                           fontproperties=REG, fontsize=9, color=BAD)
                st['y'] = BOT - 1
                continue

            # ---- 여기부터는 흐름 배치
            if st['y'] < BOT + 0.02:
                newpage()
            f, a = st['fig'], st['ax']

            if kind == 'h1':
                need(0.075)
                f, a = st['fig'], st['ax']
                st['y'] -= 0.008
                a.add_patch(plt.Rectangle((LM - 0.014, st['y'] - 0.004), 0.005, 0.028, color=BLUE))
                a.text(LM, st['y'], payload, fontproperties=BLD, fontsize=15.5, color=INK)
                st['y'] -= 0.047

            elif kind == 'h2':
                need(0.06)
                f, a = st['fig'], st['ax']
                st['y'] -= 0.006
                a.text(LM, st['y'], payload, fontproperties=BLD, fontsize=12.5, color=BLUE)
                st['y'] -= 0.034

            elif kind == 'h3':
                need(0.05)
                f, a = st['fig'], st['ax']
                a.text(LM, st['y'], payload, fontproperties=BLD, fontsize=11, color=INK)
                st['y'] -= 0.030

            elif kind == 'p':
                for para in payload.split('\n'):
                    for ln in self._wrap_runs(f, para, 10.4, RM - LM):
                        if st['y'] < BOT:
                            newpage(); f, a = st['fig'], st['ax']
                        x = LM
                        for seg, bold in ln:
                            a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                                   fontsize=10.4, color=INK)
                            x += self._w(f, seg, BLD if bold else REG, 10.4)
                        st['y'] -= 0.0232
                st['y'] -= 0.008

            elif kind in ('bullets', 'steps'):
                for i, item in enumerate(payload, 1):
                    mark = '·' if kind == 'bullets' else f'{i}.'
                    lines = self._wrap_runs(f, item, 10.2, RM - LM - 0.035)
                    for j, ln in enumerate(lines):
                        if st['y'] < BOT:
                            newpage(); f, a = st['fig'], st['ax']
                        if j == 0:
                            a.text(LM + 0.004, st['y'], mark, fontproperties=BLD,
                                   fontsize=10.2, color=BLUE)
                        x = LM + 0.035
                        for seg, bold in ln:
                            a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                                   fontsize=10.2, color=INK)
                            x += self._w(f, seg, BLD if bold else REG, 10.2)
                        st['y'] -= 0.0228
                    st['y'] -= 0.004
                st['y'] -= 0.006

            elif kind == 'code':
                txt, cap = payload
                lines = txt.split('\n')
                h = 0.0205 * len(lines) + 0.022 + (0.022 if cap else 0)
                need(h)
                f, a = st['fig'], st['ax']
                if cap:
                    a.text(LM, st['y'], cap, fontproperties=BLD, fontsize=9.8, color=MUTE)
                    st['y'] -= 0.024
                a.add_patch(plt.Rectangle((LM - 0.018, st['y'] - 0.0205 * len(lines) + 0.014),
                                          RM - LM + 0.032, 0.0205 * len(lines) + 0.012,
                                          facecolor='#f5f6f8', edgecolor='#e0e3e9', lw=0.8))
                for ln in lines:
                    # DejaVu Mono에는 한글이 없다 → 한글이 섞인 줄은 한글 폰트로 그린다
                    han = any('가' <= c <= '힣' for c in ln)
                    a.text(LM, st['y'], ln, fontproperties=REG if han else MONO,
                           fontsize=8.9 if not han else 9.2, color='#1b2733')
                    st['y'] -= 0.0205
                st['y'] -= 0.012

            elif kind == 'formula':
                need(0.026 * len(payload) + 0.02)
                f, a = st['fig'], st['ax']
                a.add_patch(plt.Rectangle((LM - 0.018, st['y'] - 0.026 * len(payload) + 0.016),
                                          RM - LM + 0.032, 0.026 * len(payload) + 0.010,
                                          facecolor='#f5f6f8', edgecolor='#e0e3e9', lw=0.8))
                for ln in payload:
                    a.text(0.5, st['y'], ln, ha='center', fontproperties=REG,
                           fontsize=10.5, color='#1b2733')
                    st['y'] -= 0.026
                st['y'] -= 0.012

            elif isinstance(kind, tuple) and kind[0] == 'box':
                head, body = payload
                style = {'note': (BLUE, '#eef3fb', '#cfe0f5'),
                         'good': (GOOD, '#eef7f0', '#c9e6d2'),
                         'warn': (BAD, '#fdf2ef', '#f2d3ca')}[kind[1]]
                lines = []
                for para in body.split('\n'):
                    lines += self._wrap_runs(f, para, 9.8, RM - LM - 0.02)
                h = 0.0212 * len(lines) + 0.048
                need(h)
                f, a = st['fig'], st['ax']
                top = st['y'] + 0.016
                a.add_patch(plt.Rectangle((LM - 0.02, top - h), RM - LM + 0.034, h,
                                          facecolor=style[1], edgecolor=style[2], lw=0.9))
                a.add_patch(plt.Rectangle((LM - 0.02, top - h), 0.005, h, facecolor=style[0],
                                          edgecolor='none'))
                a.text(LM, st['y'], head, fontproperties=BLD, fontsize=9.8, color=style[0])
                st['y'] -= 0.024
                for ln in lines:
                    x = LM
                    for seg, bold in ln:
                        a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                               fontsize=9.8, color='#243040')
                        x += self._w(f, seg, BLD if bold else REG, 9.8)
                    st['y'] -= 0.0212
                st['y'] -= 0.022

            elif kind == 'quote':
                txt, who = payload
                lines = []
                for para in txt.split('\n'):
                    lines += self._wrap_runs(f, para, 10.0, RM - LM - 0.05)
                h = 0.0225 * len(lines) + 0.042
                need(h)
                f, a = st['fig'], st['ax']
                top = st['y'] + 0.016
                a.add_patch(plt.Rectangle((LM - 0.005, top - h), 0.005, h,
                                          facecolor='#9aa4b5', edgecolor='none'))
                for ln in lines:
                    x = LM + 0.028
                    for seg, bold in ln:
                        a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                               fontsize=10.0, color='#3a4453', style='italic')
                        x += self._w(f, seg, BLD if bold else REG, 10.0)
                    st['y'] -= 0.0225
                a.text(LM + 0.028, st['y'], f'— {who}', fontproperties=REG,
                       fontsize=9.3, color=MUTE)
                st['y'] -= 0.030

            elif kind == 'term':
                word, eng, mean = payload
                lines = self._wrap_runs(f, mean, 9.8, RM - LM - 0.03)
                h = 0.0212 * len(lines) + 0.046
                need(h)
                f, a = st['fig'], st['ax']
                top = st['y'] + 0.016
                a.add_patch(plt.Rectangle((LM - 0.02, top - h), RM - LM + 0.034, h,
                                          facecolor='#fbfaf4', edgecolor='#e6e1cf', lw=0.9))
                a.text(LM, st['y'], word, fontproperties=BLD, fontsize=10.4, color=INK)
                wlen = self._w(f, word + '  ', BLD, 10.4)
                a.text(LM + wlen, st['y'], eng, fontproperties=REG, fontsize=9.2, color=MUTE)
                st['y'] -= 0.024
                for ln in lines:
                    x = LM
                    for seg, bold in ln:
                        a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                               fontsize=9.8, color='#243040')
                        x += self._w(f, seg, BLD if bold else REG, 9.8)
                    st['y'] -= 0.0212
                st['y'] -= 0.020

            elif kind == 'qa':
                q, ans = payload
                ql = self._wrap_runs(f, q, 10.2, RM - LM - 0.035)
                al = self._wrap_runs(f, ans, 10.0, RM - LM - 0.035)
                need(0.023 * (len(ql) + len(al)) + 0.03)
                f, a = st['fig'], st['ax']
                a.text(LM, st['y'], 'Q', fontproperties=BLD, fontsize=11, color=BLUE)
                for j, ln in enumerate(ql):
                    x = LM + 0.03
                    for seg, bold in ln:
                        a.text(x, st['y'], seg, fontproperties=BLD, fontsize=10.2, color=INK)
                        x += self._w(f, seg, BLD, 10.2)
                    st['y'] -= 0.0232
                st['y'] -= 0.004
                a.text(LM, st['y'], 'A', fontproperties=BLD, fontsize=11, color=GOOD)
                for ln in al:
                    if st['y'] < BOT:
                        newpage(); f, a = st['fig'], st['ax']
                    x = LM + 0.03
                    for seg, bold in ln:
                        a.text(x, st['y'], seg, fontproperties=BLD if bold else REG,
                               fontsize=10.0, color='#243040')
                        x += self._w(f, seg, BLD if bold else REG, 10.0)
                    st['y'] -= 0.0228
                st['y'] -= 0.016

            elif kind == 'table':
                heads, rows, widths, size = payload
                total = RM - LM
                cw = [total * w / sum(widths) for w in widths]
                # 각 칸을 폭에 맞춰 미리 줄바꿈
                pre = []
                for row in rows:
                    cells = []
                    for i, c in enumerate(row):
                        lines = []
                        for part in str(c).split('\n'):     # 칸 안의 줄바꿈을 먼저 처리
                            lines += self._wrap_runs(f, part, size, cw[i] - 0.012)
                        cells.append(lines)
                    pre.append((cells, max(len(c) for c in cells)))
                need(0.03 + sum(0.0205 * n + 0.008 for _, n in pre[:3]) + 0.02)
                f, a = st['fig'], st['ax']
                x = LM
                for i, hh in enumerate(heads):
                    a.text(x, st['y'], str(hh), fontproperties=BLD, fontsize=size + 0.4, color=INK)
                    x += cw[i]
                st['y'] -= 0.008
                a.plot([LM - 0.005, RM], [st['y'], st['y']], color='#9aa4b5', lw=0.9)
                st['y'] -= 0.020
                for cells, nmax in pre:
                    if st['y'] - (0.0205 * nmax) < BOT:
                        newpage(); f, a = st['fig'], st['ax']
                        x = LM
                        for i, hh in enumerate(heads):
                            a.text(x, st['y'], str(hh), fontproperties=BLD,
                                   fontsize=size + 0.4, color=INK)
                            x += cw[i]
                        st['y'] -= 0.008
                        a.plot([LM - 0.005, RM], [st['y'], st['y']], color='#9aa4b5', lw=0.9)
                        st['y'] -= 0.020
                    x = LM
                    for i, clines in enumerate(cells):
                        yy = st['y']
                        for ln in clines:
                            xx = x
                            for seg, bold in ln:
                                a.text(xx, yy, seg, fontproperties=BLD if bold else REG,
                                       fontsize=size, color='#243040')
                                xx += self._w(f, seg, BLD if bold else REG, size)
                            yy -= 0.0195
                        x += cw[i]
                    st['y'] -= 0.0195 * nmax + 0.009
                    a.plot([LM - 0.005, RM], [st['y'] + 0.010, st['y'] + 0.010],
                           color='#e3e6ec', lw=0.6)
                st['y'] -= 0.012

            elif kind == 'fig':
                path, height, cap = payload
                need(height + (0.03 if cap else 0.01))
                f, a = st['fig'], st['ax']
                try:
                    im = mpimg.imread(path)
                    h, w = im.shape[0], im.shape[1]
                    dw = RM - LM
                    dh = dw * (h / w) * (PW / PH)
                    if dh > height:
                        dw *= height / dh; dh = height
                    axim = f.add_axes([LM + ((RM - LM) - dw) / 2, st['y'] - dh, dw, dh])
                    axim.imshow(im); axim.axis('off')
                    st['y'] -= dh + 0.010
                except Exception as e:
                    a.text(LM, st['y'], f'[그림 없음: {Path(path).name} — {e}]',
                           fontproperties=REG, fontsize=9, color=BAD)
                    st['y'] -= 0.03
                if cap:
                    for ln in textwrap.wrap(cap, 62):
                        a.text(0.5, st['y'], ln, ha='center', fontproperties=REG,
                               fontsize=9.2, color=MUTE)
                        st['y'] -= 0.020
                st['y'] -= 0.010

        flush()

    def _footer(self, fig, ax, page):
        ax.plot([LM - 0.02, RM + 0.014], [0.042, 0.042], color=LINE, lw=0.7)
        ax.text(LM - 0.02, 0.026, self.footer, fontproperties=REG, fontsize=8.2, color=MUTE)
        if page:
            ax.text(RM + 0.014, 0.026, str(page), ha='right',
                    fontproperties=REG, fontsize=8.6, color=MUTE)
