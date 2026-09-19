# -*- coding: utf-8 -*-
"""폰용 전체 정리 md 를 PDF 로 만든다 (초안).

pdfdoc.Doc 의 cover / h1 / h2 / p / bullets / steps 만 쓴다.
이모지는 전부 지운다 (한글 PDF 글꼴에 없어서 두부 네모가 찍힌다).

쓰는 법:
    python3 make_phone_summary_pdf.py <입력.md> <출력.pdf>
    python3 make_phone_summary_pdf.py <입력.md> <출력.pdf> --title "제목"

md 규칙 (이 스크립트가 아는 것만):
    # 제목        -> 표지 제목 (본문에는 안 찍는다)
    ## 큰 절       -> h1
    ### 작은 절     -> h2
    - 항목         -> bullets (이어지는 - 줄을 한 묶음으로)
    1. 항목        -> steps (들여쓴 다음 줄은 같은 항목에 이어 붙임)
    그 밖의 줄      -> p (빈 줄까지 이어 붙여 한 문단으로)
    작성: / 최종 수정: 줄 -> 표지
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdfdoc import Doc  # noqa: E402

# 이모지·기호 그림문자 영역 (한글 글꼴에 없는 것들)
EMOJI = re.compile(
    '[\U0001F000-\U0001FAFF'      # 그림문자 전반
    '\U00002190-\U000021FF'       # 화살표
    '\U00002300-\U000023FF'       # 기타 기술 기호
    '\U00002600-\U000027BF'       # 날씨·별·체크 등
    '\U00002B00-\U00002BFF'
    '\uFE0E\uFE0F'                # 변이 선택자
    '\u200D'                      # 이음 문자
    ']+'
)


def clean(s):
    """이모지를 지우고 양끝 공백을 없앤다."""
    return EMOJI.sub('', s).strip()


def parse(md_text):
    """md 를 (종류, 내용) 목록으로 바꾼다."""
    title, date_lines = '', []
    blocks = []
    para, bl, st = [], [], []

    def flush_para():
        if para:
            blocks.append(('p', ' '.join(para)))
            para.clear()

    def flush_bullets():
        if bl:
            blocks.append(('bullets', list(bl)))
            bl.clear()

    def flush_steps():
        if st:
            blocks.append(('steps', list(st)))
            st.clear()

    def flush_all():
        flush_para()
        flush_bullets()
        flush_steps()

    for raw in md_text.splitlines():
        line = clean(raw.rstrip())
        indented = raw.startswith(('   ', '\t')) and line

        if not line:
            # 빈 줄은 문단만 끊는다. 번호 목록·불릿은 사이에 빈 줄이 있어도 한 묶음으로 둔다
            flush_para()
            continue

        if line.startswith('작성:') or line.startswith('최종 수정:'):
            flush_all()
            date_lines.append(line)
            continue

        if line.startswith('### '):
            flush_all()
            blocks.append(('h2', line[4:]))
            continue
        if line.startswith('## '):
            flush_all()
            blocks.append(('h1', line[3:]))
            continue
        if line.startswith('# '):
            flush_all()
            title = title or line[2:]
            continue

        if line.startswith('- '):
            flush_para()
            flush_steps()
            bl.append(line[2:])
            continue

        m = re.match(r'^(\d+)\.\s+(.*)$', line)
        if m and not indented:
            flush_para()
            flush_bullets()
            st.append(m.group(2))
            continue

        # 들여쓴 줄은 바로 앞 항목에 이어 붙인다
        if indented and st:
            st[-1] = st[-1] + ' ' + line
            continue
        if indented and bl:
            bl[-1] = bl[-1] + ' ' + line
            continue

        flush_bullets()
        flush_steps()
        para.append(line)

    flush_all()
    return title, date_lines, blocks


def build(md_path, pdf_path, title=None, subtitle='', date=''):
    md_text = Path(md_path).read_text(encoding='utf-8')
    md_title, date_lines, blocks = parse(md_text)
    title = title or md_title or Path(md_path).stem

    doc_date = date or (date_lines[0].split(':', 1)[1].strip() if date_lines else '')
    d = Doc(pdf_path, title=title, subtitle=subtitle, date=doc_date)

    cover = list(date_lines)
    cover.append(f'원본 md: {md_path}')
    d.cover(cover)

    for kind, payload in blocks:
        if kind == 'h1':
            d.h1(payload)
        elif kind == 'h2':
            d.h2(payload)
        elif kind == 'p':
            d.p(payload)
        elif kind == 'bullets':
            d.bullets(payload)
        elif kind == 'steps':
            d.steps(payload)

    d.save()
    return len(blocks)


def main():
    ap = argparse.ArgumentParser(description='폰용 전체 정리 md 를 PDF 로 만든다')
    ap.add_argument('md', help='입력 md 경로')
    ap.add_argument('pdf', help='출력 PDF 경로')
    ap.add_argument('--title', default=None, help='표지 제목 (없으면 md 의 # 줄)')
    ap.add_argument('--subtitle', default='', help='표지 부제')
    ap.add_argument('--date', default='', help='표지에 찍을 날짜')
    a = ap.parse_args()

    n = build(a.md, a.pdf, a.title, a.subtitle, a.date)
    print(f'블록 {n}개')


if __name__ == '__main__':
    main()
