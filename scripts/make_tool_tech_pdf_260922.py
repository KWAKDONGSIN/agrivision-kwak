# 문서/260922_툴_기술설명.md 를 읽어 같은 내용의 A4 PDF 를 만드는 생성기 (md 가 정본, PDF 는 재생성)
# -*- coding: utf-8 -*-
"""라벨링 툴 기술설명 PDF.

작성: 2026-09-22
사용:  ~/.conda/envs/kwak/bin/python tools/make_tool_tech_pdf_260922.py
출력:  문서/260922_툴_기술설명.pdf
재료:  문서/260922_툴_기술설명.md  (고칠 때는 md 를 고치고 이 스크립트를 다시 돌린다)
원칙:  md 의 글자를 그대로 옮긴다. 숫자·경로를 여기서 새로 만들지 않는다.
       md 의 «## » 는 큰 제목, «### » 는 작은 제목, «- » 는 글머리, «1. » 는 순서, «|» 는 표, ``` 는 코드.
"""
import re
import sys
from pathlib import Path

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc  # noqa: E402

SRC = BASE / '문서' / '260922_툴_기술설명.md'
OUT = BASE / '문서' / '260922_툴_기술설명.pdf'


def inline(s):
    """pdfdoc 는 **굵게** 만 안다. 코드 표시(`…`)는 글자만 남긴다."""
    return re.sub(r'`([^`]*)`', r'\1', s).strip()


def main():
    lines = SRC.read_text(encoding='utf-8').splitlines()
    d = Doc(OUT, '라벨링·검수 툴', subtitle='어떤 기술로 어떻게 만들었나',
            volume='기술설명', footer='곽동신 · 2026-09-22 · 서버 실측 기준', date='2026-09-22')
    d.cover(lines=['네 과일 마스크·상자·번호를 사람이 고치고 판정하는 웹툴',
                   'Flask + 순수 JS/Canvas · 파일 저장 · 시험 1,358개',
                   '만든 사람: 곽동신 (AI 바이브 코딩, 2026-09-16 ~ 09-22)'],
            badge='')

    para, bullets, steps, table, code = [], [], [], [], None

    def flush():
        nonlocal para, bullets, steps, table
        if para:
            d.p(inline(' '.join(para))); para = []
        if bullets:
            d.bullets([inline(b) for b in bullets]); bullets = []
        if steps:
            d.steps([inline(b) for b in steps]); steps = []
        if table:
            rows = [[inline(c) for c in r] for r in table]
            head, body = rows[0], rows[1:]
            n = len(head)
            # 첫 칸을 조금 좁게, 나머지는 같게
            widths = [0.22] + [(0.78 / (n - 1))] * (n - 1) if n > 1 else [1.0]
            d.table(head, body, widths, size=8.6); table = []

    for raw in lines:
        line = raw.rstrip()
        if code is not None:
            if line.startswith('```'):
                d.code('\n'.join(code)); code = None
            else:
                code.append(line)
            continue
        if line.startswith('```'):
            flush(); code = []; continue
        if not line.strip():
            flush(); continue
        if line.startswith('작성:') or line.startswith('# '):
            continue                                   # 표지에 있다
        if line.startswith('## '):
            flush(); d.h1(inline(line[3:])); continue
        if line.startswith('### '):
            flush(); d.h2(inline(line[4:])); continue
        if line.startswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', line):
                continue                               # 구분선
            cells = [c.strip() for c in line.strip('|').split('|')]
            if para or bullets or steps:
                flush()
            table.append(cells); continue
        if line.startswith('- '):
            if para or steps or table:
                flush()
            bullets.append(line[2:]); continue
        m = re.match(r'^\s*(\d+)\.\s+(.*)$', line)
        if m and not para:
            if bullets or table:
                flush()
            steps.append(m.group(2)); continue
        if line.startswith('  ') and (bullets or steps):
            # 글머리 밑에 들여쓴 이어지는 줄
            tgt = bullets if bullets else steps
            tgt[-1] = tgt[-1] + ' ' + line.strip(); continue
        if bullets or steps or table:
            flush()
        para.append(line.strip())
    flush()
    d.save()
    print('저장:', OUT, OUT.stat().st_size, '바이트')


if __name__ == '__main__':
    main()
