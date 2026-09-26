# 260925 «전부 업그레이드» 사이클 — 툴 코드(app/tests/scripts/ai_helper 코드)와 이번 사이클 문서·기록을 비밀값을 가려 공개 사본에 복사한다
# 260923_그림판툴/prepare_public.py 와 같은 방식. 수집 규칙은 collect_public.py 의 add()·blocked()·clean() 을 그대로 실행해 쓴다.
# 쓰는 곳: python3 cycles/260925_업그레이드/prepare_public.py [대상폴더]
# 커밋·push 는 하지 않는다(그 다음 단계에서 audit_public.py 검사 뒤 한다). 두 번 돌려도 README 덩어리는 한 번만 붙는다.
import sys, json, datetime
from pathlib import Path

C = Path(__file__).resolve().parent                                   # cycles/260925_업그레이드
T = C.parents[1]                                                      # 260916_라벨링툴
W = Path('/data/project/2026summer/kds0206')
G = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else W / '_git_agrivision-kwak'
assert (G / 'labeltool').is_dir(), f'공개 사본이 아니다: {G}'

MARK = '## 2026-09-26 그림판 «전부 업그레이드» 사이클 반영'
REV = Path('labeltool/reviews/업그레이드_260925')

ns = {}
source = (T / 'cycles/260920_structure/codex_resume/collect_public.py').read_text()
exec(source.split("for sub in ('app','tests','scripts','export'):")[0], ns)
ns['G'] = G
ns['textsuffix'].add('.mjs')   # 브라우저 시험(.mjs)은 글자 파일인데 원래 규칙엔 없어 «바이너리» 로 빠졌다(공개본에 paint_e2e.mjs 가 이미 있음) — 2026-09-26
add, blocked = ns['add'], ns['blocked']

# ① 앱·시험·스크립트
SKIP = {'app/static/help/demo_260921/index.html', 'app/static/시연_PDF원문.html'}
# rglob 대신 os.walk 로 — tests/_sandbox(83만 파일) 같은 막힌 폴더는 들어가지 않고 건너뛴다(2026-09-26, 안 그러면 몇 분 걸림)
import os
for sub in ('app', 'tests', 'scripts'):
    for root, dirs, files in os.walk(T / sub):
        dirs[:] = [d for d in dirs if not blocked(Path(root, d).relative_to(T))]
        for f in files:
            p = Path(root, f); rel = p.relative_to(T)
            if not p.is_file() or p.is_symlink() or blocked(rel) or str(rel) in SKIP:
                continue
            add(p, Path('labeltool') / rel, doc=(p.suffix == '.md'))

# ② AI 도우미·초벌 스크립트 — 코드만(가중치·데이터셋·학습 결과·로그는 올리지 않는다)
for p in (T / 'ai_helper').rglob('*'):
    rel = p.relative_to(T)
    parts = set(rel.parts)
    if not p.is_file() or p.is_symlink() or parts & {'weights', 'runs', 'logs', 'yolo_ds', 'yolo_ds_v2', 'yolo_ds_v3', '__pycache__'}:
        continue
    if p.suffix not in ('.py', '.sh', '.md') or p.name.startswith('_backup'):
        continue
    add(p, Path('labeltool') / rel, doc=(p.suffix == '.md'))

# ③ 이번 사이클 문서(가리기 규칙 통과) — 카톡·메일 초안은 올리지 않는다. 사용법 문서는 S02 로 갱신돼 다시 올린다
for name in ('260923_그림판툴_사용법.md',
             '260925_그림판_감사.md', '260925_그림판_감사_두번째의견.md', '260925_녹취지시_툴대조.md',
             '260925_데이터셋0924_비교.md', '260925_라벨링툴_리서치.md', '260925_참고논문폴더_툴관련요약.md',
             '260925_팀원작업환경_조사.md'):
    add(W / '문서' / name, Path('docs') / name, doc=True)

# ④ 이 사이클의 계획·체크리스트·기록·검토 결과·레인 스크립트 (로그·라운드 출력·스크린샷·기준선 원본은 뺀다)
for name in ('plan.md', 'checklist.md', 'context-notes.md', 'prepare_public.py', 'audit_public.py'):
    add(C / name, REV / name, doc=name.endswith('.md'))
for name in ('STATUS.md', 'X01_codex.md', 'X02_codex.md', 'E02_회귀_260925.md', 'baseline_260925.md', 'S01_사용법점검.md',
             'prompt_common.md', 'prompt_codex.md', 'run_lane.sh', 'start_all.sh', 'claim.py', 'f1_sandbox.sh', 'f1_audit.mjs',
             'C01_make_sample_list.mjs'):
    add(C / 'auto' / name, REV / 'auto' / name, doc=name.endswith('.md'))
for p in sorted((C / 'codex_review').glob('*.md')):
    add(p, REV / 'codex_review' / p.name, doc=True)

# ⑤ 작업 기록
add(W / '작업기록.md', Path('worklog/작업기록.md'), doc=True)

# ⑥ README 에 한 덩어리 (이미 있으면 안 붙인다)
p = G / 'README.md'; s = p.read_text()
if MARK not in s:
    p.write_text(s + f'''
{MARK}

녹음·논문·인터넷 조사·팀원 작업환경을 전부 대조해 그림판을 한 번에 손봤습니다(코드 C01~C25, 자동 4레인 09-25~09-26).
카운팅 100장 표본 모드 · 닮은 사진 표시 · 확정 수와 내보내기 · 다음 사진 미리 받기와 /instances 캐시 ·
키보드·보조기기 접근성 · 글자 대비 · «비슷한 열매 한꺼번에 찾기»(SAM 특징) · «헷갈리는 순» 정렬 · 저장 뒤 의심 열매 표시 ·
✨ 결과 모양 경고 · 사진당 작업 시간 기록 · Codex 두 차례 검토로 찾은 버그 5개(저장 확인 없는 목록 갱신 · 저장 중 편집 ·
도우미 음수 슬라이스 · worklog NaN · 긴 드래그 작업 시간) 고침. 요소 id·단축키·API 규칙은 바꾸지 않았습니다.
검증은 labeltool/reviews/업그레이드_260925/checklist.md, 결정과 까닭은 같은 폴더 context-notes.md,
사용법은 docs/260923_그림판툴_사용법.md(2026-09-26 갱신)입니다.
''')
p = G / 'labeltool/README.md'; s = p.read_text()
if MARK[3:] not in s:
    p.write_text(s + f'\n{MARK[3:]}: reviews/업그레이드_260925/checklist.md 와 ../docs/260923_그림판툴_사용법.md 를 읽으세요.\n')

(C / 'evidence').mkdir(exist_ok=True)
(C / 'evidence/public_collection.json').write_text(json.dumps(
    {'at': datetime.datetime.now().isoformat(), 'target': str(G),
     'copied': ns['copied'], 'redactions': ns['redactions'], 'excluded': ns['excluded']},
    ensure_ascii=False, indent=1))
print('대상', G)
print('복사', len(ns['copied']), '· 가린 파일', len(ns['redactions']), '· 제외', len(ns['excluded']))
for r in ns['redactions']:
    print('  가림:', r)
for e in ns['excluded']:
    if not e['file'].endswith('.png'):
        print('  제외:', e)
