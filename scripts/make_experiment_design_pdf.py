# -*- coding: utf-8 -*-
"""실험 설계 이해 발표자료 PDF (2026-09-15 랩미팅용).

md 3개(순서도 2판 · 쉬운말 정리 · 외부 AI 대조)를 pdfdoc.Doc 으로 변환한다.
사용:  ~/.conda/envs/kwak/bin/python tools/make_experiment_design_pdf.py
출력:  문서/260912_실험설계_이해_발표자료.pdf
"""
import re, sys
from pathlib import Path
REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from pdfdoc import Doc  # noqa: E402

DOC = BASE / '문서'
OUT = DOC / '260912_실험설계_이해_발표자료.pdf'

def clean(t):
    t = re.sub(r'`([^`]*)`', r'\1', t)
    t = t.replace('✗', '(X)').replace('🔴', '').replace('🟡', '').replace('✅', '[완료]').replace('▶', '').replace('⏳', '').replace('❌', '[추정]').replace('🆕', '')
    return t.strip()

def md_to_doc(d, path, skip_head_lines=0, max_h=None):
    lines = path.read_text(encoding='utf-8').splitlines()[skip_head_lines:]
    i = 0; para = []; bullets = []; table = []
    def flush():
        nonlocal para, bullets, table
        if para: d.p(clean(' '.join(para))); para = []
        if bullets: d.bullets([clean(b) for b in bullets]); bullets = []
        if table:
            rows = [[clean(c) for c in r.replace('|C|', 'C크기').strip().strip('|').split('|')] for r in table if not re.match(r'^\s*\|?\s*-{2,}', r)]
            if rows:
                hdr, body = rows[0], rows[1:]
                n = len(hdr); body = [(r + [''] * n)[:n] for r in body]
                w = [1.0 / n] * n
                d.table(hdr, body, w, size=8.2)
            table = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            flush(); j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith('```'):
                buf.append(lines[j]); j += 1
            if 'mermaid' not in ln:
                d.code('\n'.join(clean(b) for b in buf))
            i = j + 1; continue
        if ln.lstrip().startswith('|'):
            if para or bullets: flush()
            table.append(ln); i += 1; continue
        if table: flush()
        m = re.match(r'^(#{1,4})\s+(.*)', ln)
        if m:
            flush(); lvl = len(m.group(1)); t = clean(m.group(2))
            if 'mermaid' in t: i += 1; continue
            if lvl <= 2: d.h1(t)
            elif lvl == 3: d.h2(t)
            else: d.h3(t)
            i += 1; continue
        if re.match(r'^\s*[-*]\s+', ln) or re.match(r'^\s*\d+\.\s+', ln):
            if para: flush()
            bullets.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', ln)); i += 1; continue
        if ln.strip() == '' or ln.startswith('>'):
            flush(); i += 1; continue
        para.append(ln); i += 1
    flush()

d = Doc(OUT, '실험 설계 이해 — 파일럿 → 선별 → 본실험',
        '2026-09-15 랩미팅 발표자료 (교수님 프로토콜 2026-09-11 판 기준)',
        '', footer='실험 설계 이해 발표자료 · 2026-09-12 · 곽동신', date='2026-09-12')
d.cover([
    '작성: 2026-09-12 · 곽동신 (서버 클로드 정리)',
    '',
    '① 순서도 그림 + 5분 발표 대본 + 예상 질문 + 교수님께 여쭐 것 4개',
    '② 교수님 설계를 쉬운 말로 풀어 쓴 정리 (11절)',
    '③ 같은 과제를 GPT·로컬 클로드·딥시크·제미나이에게 시켜 대조한 결과',
    '',
    '근거: platform/planning/안내.md · 260905_00·01·02·05·06 · 260906_파일럿_단계_및_결정규칙.md',
    '     04_experiments/260911_파일럿0/README.md (2026-09-11 수정본)',
], badge='09-08 순서도 1판은 폐기 — 09-11 변경(결정 29·30) 반영판')
d.toc([
    (1, '순서도와 발표 대본', '그림 한 장, 5분 대본, 예상 질문 11개, 교수님께 여쭐 것 4개'),
    (2, '교수님 설계 쉬운 말 정리', '무엇이 바뀌었나, 데이터 분할, 단계별 결정 권한, 선별 규칙, 평가, 미정 항목'),
    (3, '외부 AI 4개 대조', 'GPT·로컬 클로드·딥시크·제미나이 결과를 원문 기준으로 비교한 결과'),
])
d.chapter(1, '순서도와 발표 대본', '교수님이 "이해한 바대로 설명해 보라"고 하신 것. 그림을 먼저 보고 대본을 읽는다.')
d.fullfig(DOC / '260912_실험설계_순서도_2판.png', '실험 설계 순서도 2판 (2026-09-12)', '회색 = 완료(이력) · 노랑 테두리 = 실행 중 · 주황 = 파일럿 · 초록 = 본실험 · 보라 = 산출')
md_to_doc(d, DOC / '260912_실험설계_순서도_2판.md', skip_head_lines=8)
d.chapter(2, '교수님 설계 쉬운 말 정리', '발표 대본의 교과서. 막히는 개념이 있으면 여기서 찾는다.')
md_to_doc(d, DOC / '260912_교수님_실험설계_쉬운말정리.md', skip_head_lines=6)
d.chapter(3, '외부 AI 4개 대조', '같은 원문·같은 프롬프트로 독립적으로 풀게 한 뒤 원문 기준으로 대조. 내가 제대로 이해했는지 확인하는 용도.')
md_to_doc(d, DOC / '260912_external_ai_task/05_compare.md', skip_head_lines=6)
d.save()
print('saved', OUT)
