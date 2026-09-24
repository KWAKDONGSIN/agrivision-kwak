# 260923 그림판 사이클 — 툴 코드(app/tests/scripts/ai_helper 코드)와 오늘 문서를 비밀값을 가려 공개 사본에 복사한다
# 260921_편의/prepare_public.py 와 같은 방식. 수집 규칙은 collect_public.py 의 add()·blocked()·clean() 을 그대로 실행해 쓴다.
# 쓰는 곳: python3 cycles/260923_그림판툴/prepare_public.py [대상폴더]
# 커밋·push 는 하지 않는다(그 다음 단계에서 audit_public.py 검사 뒤 사람/세션이 한다).
import sys, json, datetime, shutil
from pathlib import Path

C = Path(__file__).resolve().parent                                   # kds0206/cycles/260922_툴_간편화
W = Path('/data/project/2026summer/kds0206')
T = Path('/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴')
G = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else W / '_git_agrivision-kwak'
assert (G / 'labeltool').is_dir(), f'공개 사본이 아니다: {G}'

MARK = '## 2026-09-23 그림판 갱신'

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

# ② AI 도우미·초벌 스크립트 — 코드만(가중치·데이터셋·학습 결과·로그는 올리지 않는다)
for p in (T / 'ai_helper').rglob('*'):
    rel = p.relative_to(T)
    parts = set(rel.parts)
    if not p.is_file() or p.is_symlink() or parts & {'weights', 'runs', 'logs', 'yolo_ds', 'yolo_ds_v2', 'yolo_ds_v3', '__pycache__'}:
        continue
    if p.suffix not in ('.py', '.sh', '.md') or p.name.startswith('_backup'):
        continue
    add(p, Path('labeltool') / rel, doc=(p.suffix == '.md'))

# ③ 오늘 문서(가리기 규칙 통과) — 카톡 초안·메일 초안은 올리지 않는다
for name in ('260923_그림판툴_사용법.md', '260923_인스턴스_현황과_선택지.md', '260923_유사도방법_정리.md', '260923_인스턴스_데이터셋_후보조사.md'):
    add(W / '문서' / name, Path('docs') / name, doc=True)

# ④ 이 사이클의 계획·체크리스트·기록
for name in ('plan.md', 'checklist.md', 'context-notes.md', 'prepare_public.py'):
    add(C / name, Path('labeltool/reviews/그림판_260923') / name, doc=name.endswith('.md'))

# ⑤ 작업 기록
add(W / '작업기록.md', Path('worklog/작업기록.md'), doc=True)

# ⑥ README 에 한 덩어리 (이미 있으면 안 붙인다)
p = G / 'README.md'; s = p.read_text()
if MARK not in s:
    p.write_text(s + f'''
{MARK}

첫 화면(/)을 윈도 그림판 모양의 새 라벨 화면으로 바꿨습니다(labeltool/app/static/paint/). 색 하나 = 열매 하나,
저장 한 번에 마스크·번호·상자. ✨ 클릭 칠하기(SAM2.1 도우미, labeltool/ai_helper/sam_server.py) ·
모델 초벌(YOLO11m-seg, labeltool/ai_helper/draft/) · 번호를 원본 정답으로 나누기. 옛 화면은 /old.
AI 판정은 화면에서 뺐습니다(파일은 보존). 사용법 docs/260923_그림판툴_사용법.md · 현황 docs/260923_인스턴스_현황과_선택지.md
''')
p = G / 'labeltool/README.md'; s = p.read_text()
if MARK[3:] not in s:
    p.write_text(s + f'\n{MARK[3:]}: reviews/그림판_260923/ 와 ../docs/260923_그림판툴_사용법.md 를 읽으세요.\n')

(C / 'evidence').mkdir(exist_ok=True)
(C / 'evidence/public_collection.json').write_text(json.dumps(
    {'at': datetime.datetime.now().isoformat(), 'target': str(G),
     'copied': ns['copied'], 'redactions': ns['redactions'], 'excluded': ns['excluded']},
    ensure_ascii=False, indent=1))
print('대상', G)
print('복사', len(ns['copied']), '· 가린 파일', len(ns['redactions']), '· 제외', len(ns['excluded']))
for e in ns['excluded']:
    print('  제외:', e)
