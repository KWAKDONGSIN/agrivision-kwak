# 이 사이클(260921_편의)의 코드·문서만 비밀값을 가려 공개 사본에 복사한다. 260921_모바일 것을 그대로 따랐다.
#
# 수집 규칙(무엇을 가리고 무엇을 빼는가)은 여기에 베껴 오지 않는다 —
# cycles/260920_structure/codex_resume/collect_public.py 의 add()·blocked()·clean() 을
# 그대로 실행해 쓴다(Z1·Z2 가 «베끼지 말고 그대로 실행» 을 배운 자리다).
#
# 쓰는 곳: python3 cycles/260921_편의/prepare_public.py [대상폴더]
#          대상폴더를 안 주면 /data/project/2026summer/kds0206/_git_agrivision-kwak 다.
# 커밋·push 는 하지 않는다(이 세션은 git 쓰기 권한이 없다 — auto/STUCK 참고).
# 두 번 돌려도 README·NOT_UPLOADED 가 겹쳐 붙지 않는다(표식으로 막는다).
import sys, json, datetime
from pathlib import Path

C = Path(__file__).resolve().parent                 # cycles/260921_편의
T = C.parents[1]                                    # 260916_라벨링툴
W = Path('/data/project/2026summer/kds0206')
G = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else W / '_git_agrivision-kwak'
assert (G / 'labeltool').is_dir(), f'공개 사본이 아니다: {G}'

MARK = '## 2026-09-21 편의·안정성 갱신'   # 두 번 붙는 것을 막는 표식

ns = {}
source = (T / 'cycles/260920_structure/codex_resume/collect_public.py').read_text()
exec(source.split("for sub in ('app','tests','scripts','export'):")[0], ns)
ns['G'] = G                                          # add() 가 쓰는 대상 폴더를 이 스크립트의 것으로
add, blocked = ns['add'], ns['blocked']

# ① 앱·시험·스크립트 — 모바일 사이클과 같은 세 그루터기, 같은 두 제외
SKIP = {'app/static/help/demo_260921/index.html', 'app/static/시연_PDF원문.html'}
for sub in ('app', 'tests', 'scripts'):
    for p in (T / sub).rglob('*'):
        rel = p.relative_to(T)
        if not p.is_file() or p.is_symlink() or blocked(rel) or str(rel) in SKIP:
            continue
        add(p, Path('labeltool') / rel, doc=(p.suffix == '.md'))

# ② 이 사이클의 계획·체크리스트·기록과 보고서
for p in sorted(C.glob('*.md')):
    add(p, Path('labeltool/reviews/편의_260921') / p.name, doc=True)
add(C / 'auto/STATUS.md', Path('labeltool/reviews/편의_260921/STATUS.md'), doc=True)
for name in ('prepare_public.py', 'audit_public.py'):
    add(C / name, Path('labeltool/reviews/편의_260921') / name)

# ③ 작업 기록
add(W / '작업기록.md', Path('worklog/작업기록.md'), doc=True)
add(T / '.ai-context/CURRENT.md', Path('labeltool/reviews/편의_260921/CURRENT.md'), doc=True)

# ④ 첫 README 와 제외 목록에 이번 사이클 한 덩어리 (이미 있으면 안 붙인다)
p = G / 'README.md'; s = p.read_text()
if MARK not in s:
    p.write_text(s + f'''
{MARK}

그림판·포토샵·윈도우 관습을 따라 편의 10가지와 안정성 6가지를 더하고, 무채색 토큰 한 벌로
색을 접었습니다. 요소 id·단축키·API 규칙은 바꾸지 않았습니다.
최신 검증은 labeltool/reviews/편의_260921/checklist.md, 결정과 까닭은 같은 폴더
context-notes.md 입니다. 실제 휴대폰 확인은 아직 못 했습니다.
''')
p = G / 'NOT_UPLOADED.md'; s = p.read_text()
if MARK not in s:
    p.write_text(s + f'''
{MARK} 추가 제외

사용법 그림(png)과 화면 대조용 스크린샷·모래상자·기준선 보관본은 공개하지 않습니다.
내부 툴에서는 로그인 뒤 사용법 문서에서 볼 수 있습니다.
''')
p = G / 'labeltool/README.md'; s = p.read_text()
if MARK[3:] not in s:          # 이 줄만 «## » 없이 붙으므로 표식도 «## » 를 뗀 것으로 본다
    p.write_text(s + f'\n{MARK[3:]}: reviews/편의_260921/checklist.md 를 읽으세요.\n')

(C / 'evidence').mkdir(exist_ok=True)
(C / 'evidence/public_collection.json').write_text(json.dumps(
    {'at': datetime.datetime.now().isoformat(), 'target': str(G),
     'copied': ns['copied'], 'redactions': ns['redactions'], 'excluded': ns['excluded']},
    ensure_ascii=False, indent=1))
print('대상', G)
print('복사', len(ns['copied']), '· 가린 파일', len(ns['redactions']), '· 제외', len(ns['excluded']))
