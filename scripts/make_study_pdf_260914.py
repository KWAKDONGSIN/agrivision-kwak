# -*- coding: utf-8 -*-
"""공부용 핸드폰 PDF — 노션 수정판(실험 설계 정리 + HamNet 공부) 전문을 핸드폰 비율로.

작성: 2026-09-14
사용:  ~/.conda/envs/kwak/bin/python tools/make_study_pdf_260914.py
입력:  문서/260914_노션붙여넣기_실험설계정리_HamNet_수정판.md (내용을 줄이지 않고 전부 담는다)
출력:  문서/260914_공부용_실험설계정리_HamNet_핸드폰.pdf
규칙:  «14일 수정/추가» 문단 → 파란 상자, "결론:"·"주의:" → 초록/주황 상자, 그림 2장 삽입, 표 대신 불릿(핸드폰 폭).
"""
import re, sys
from pathlib import Path
REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
import pdfdoc  # noqa: E402
pdfdoc.PW, pdfdoc.PH = 4.4, 8.4
from pdfdoc import Doc  # noqa: E402

SRC = BASE / '문서' / '260914_노션붙여넣기_실험설계정리_HamNet_수정판.md'
OUT = BASE / '문서' / '260914_공부용_실험설계정리_HamNet_핸드폰.pdf'
IMG = {'03_flowchart_v2.png': BASE / '문서' / '260912_실험설계_순서도_2판.png',
       'ChatGPT Image': BASE / '문서' / 'ChatGPT Image 2026년 9월 12일 오후 07_57_02.png'}

def clean(t):
    t = t.replace('`', '')
    return t.strip()

d = Doc(OUT, '공부 노트', subtitle='실험 설계 정리 + HamNet · 2026-09-14 수정판 전문',
        footer='곽동신 · 2026-09-14 · 공부용', date='2026-09-14')
d.cover(lines=['1부  실험 설계 이해 정리 (16절)', '2부  HamNet 모델 공부 (15절)',
               '노션에 올린 수정판과 같은 내용'], badge='공부용')

lines = SRC.read_text(encoding='utf-8').splitlines()
i = 0; para = []; bullets = []; part = 0
def flush():
    global para, bullets
    if para:
        txt = clean(' '.join(para)); para = []
        if '«14일 수정' in txt or '«14일 추가' in txt:
            d.note(txt, head='14일에 고친 곳')
        elif txt.startswith('결론:'):
            d.tip(txt[3:].strip(), head='결론')
        elif txt.startswith('주의:') or txt.startswith('- 주의:'):
            d.warn(txt.split(':', 1)[1].strip(), head='주의')
        elif txt.startswith('(이 자리에 이미지 블록으로'):
            key = '03_flowchart_v2.png' if '03_flowchart' in txt else 'ChatGPT Image'
            d.fullfig(IMG[key], caption='순서도 2판' if key.startswith('03') else 'GPT 가 그린 순서도(2026-09-12)')
        elif len(txt) <= 22 and not txt.endswith('.') and not txt.endswith('다') and ':' not in txt:
            d.h3(txt)                       # "단계별 역할", "규칙", "해석" 같은 소제목 줄
        else:
            d.p(txt)
    if bullets:
        items = [clean(b) for b in bullets]; bullets = []
        boxed = [b for b in items if '«14일 수정' in b or '«14일 추가' in b]
        plain = [b for b in items if b not in boxed]
        if plain: d.bullets(plain)
        for b in boxed: d.note(b, head='14일에 고친 곳')

while i < len(lines):
    ln = lines[i]
    if ln.strip() == '---':
        flush(); part += 1; d.pagebreak(); i += 1; continue
    m = re.match(r'^(#{1,3})\s+(.*)', ln)
    if m:
        flush(); lvl = len(m.group(1)); t = clean(m.group(2))
        if lvl == 1:
            d.pagebreak(); d.h1('1부. 실험 설계 이해 정리' if part == 0 else '2부. HamNet 모델 공부'); d.p(t)
        else:
            d.h2(t)
        i += 1; continue
    if re.match(r'^\s*[-*]\s+', ln) or re.match(r'^\s*\d+\.\s+', ln):
        if para: flush()
        bullets.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', ln)); i += 1; continue
    if not ln.strip():
        flush(); i += 1; continue
    if bullets: flush()
    para.append(ln.strip()); i += 1
flush()
d.save()
