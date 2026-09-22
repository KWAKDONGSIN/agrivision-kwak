# 260922 툴 기술설명 사이클 — 툴 코드(app/tests/scripts)와 기술설명 md·PDF 를 비밀값을 가려 공개 사본에 복사한다
# 260921_편의/prepare_public.py 와 같은 방식. 수집 규칙은 collect_public.py 의 add()·blocked()·clean() 을 그대로 실행해 쓴다.
# 쓰는 곳: python3 cycles/260922_툴기술설명/prepare_public.py [대상폴더]
# 커밋·push 는 하지 않는다(그 다음 단계에서 audit_public.py 검사 뒤 사람/세션이 한다).
import sys, json, datetime, shutil
from pathlib import Path

C = Path(__file__).resolve().parent                                   # kds0206/cycles/260922_툴기술설명
W = Path('/data/project/2026summer/kds0206')
T = Path('/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴')
G = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else W / '_git_agrivision-kwak'
assert (G / 'labeltool').is_dir(), f'공개 사본이 아니다: {G}'

MARK = '## 2026-09-22 기술설명 갱신'

ns = {}
source = (T / 'cycles/260920_structure/codex_resume/collect_public.py').read_text()
exec(source.split("for sub in ('app','tests','scripts','export'):")[0], ns)
ns['G'] = G
add, blocked = ns['add'], ns['blocked']

# ① 앱·시험·스크립트 (watchdog.sh 의 restart.flag 변경이 여기서 따라간다)
SKIP = {'app/static/help/demo_260921/index.html', 'app/static/시연_PDF원문.html'}
for sub in ('app', 'tests', 'scripts'):
    for p in (T / sub).rglob('*'):
        rel = p.relative_to(T)
        if not p.is_file() or p.is_symlink() or blocked(rel) or str(rel) in SKIP:
            continue
        add(p, Path('labeltool') / rel, doc=(p.suffix == '.md'))

# ② 기술설명 md(가리기 규칙 통과) + PDF(사용자 지시 «깃에 옮겨줘» 로 이 한 부만 올린다)
add(W / '문서/260922_툴_기술설명.md', Path('docs/260922_툴_기술설명.md'), doc=True)
add(W / '문서/260922_툴_기술설명.pdf', Path('docs/260922_툴_기술설명.pdf'))
add(W / 'semantic-segmentation/tools/make_tool_tech_pdf_260922.py', Path('scripts/make_tool_tech_pdf_260922.py'))

# ③ 이 사이클의 계획·체크리스트·기록
for name in ('plan.md', 'checklist.md', 'context-notes.md', 'prepare_public.py'):
    add(C / name, Path('labeltool/reviews/기술설명_260922') / name, doc=name.endswith('.md'))

# ④ 작업 기록
add(W / '작업기록.md', Path('worklog/작업기록.md'), doc=True)

# ⑤ README 에 한 덩어리 (이미 있으면 안 붙인다)
p = G / 'README.md'; s = p.read_text()
if MARK not in s:
    p.write_text(s + f'''
{MARK}

툴을 어떤 기술로 어떻게 만들었는지, 언제 저장되는지, 팀원이 어떻게 고치는지를
docs/260922_툴_기술설명.md (같은 이름 PDF) 에 적었습니다. 감시자(scripts/watchdog.sh)에
팀원용 재시작 신호 `app/logs/restart.flag` 를 더했습니다. 요소 id·단축키·API 규칙은 바꾸지 않았습니다.
''')
p = G / 'labeltool/README.md'; s = p.read_text()
if MARK[3:] not in s:
    p.write_text(s + f'\n{MARK[3:]}: reviews/기술설명_260922/checklist.md 와 ../docs/260922_툴_기술설명.md 를 읽으세요.\n')

(C / 'evidence').mkdir(exist_ok=True)
(C / 'evidence/public_collection.json').write_text(json.dumps(
    {'at': datetime.datetime.now().isoformat(), 'target': str(G),
     'copied': ns['copied'], 'redactions': ns['redactions'], 'excluded': ns['excluded']},
    ensure_ascii=False, indent=1))
print('대상', G)
print('복사', len(ns['copied']), '· 가린 파일', len(ns['redactions']), '· 제외', len(ns['excluded']))
for e in ns['excluded']:
    print('  제외:', e)
