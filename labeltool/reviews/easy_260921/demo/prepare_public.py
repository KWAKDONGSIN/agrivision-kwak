# 시연의 공개 가능한 코드·문서만 기존 비밀 가리기를 거쳐 복사한다.
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent;C=R.parent;T=R.parents[2];W=Path('/data/project/2026summer/kds0206');G=W/'_git_agrivision-kwak'
assert (R/'rehearsal2.rc').read_text()=='0' and (R/'published_checks.json').exists()
A=T/'_archive/pre_demo_public_260920'
if not A.exists():shutil.copytree(G,A,ignore=shutil.ignore_patterns('.git'))
ns={};source=(T/'cycles/260920_structure/codex_resume/collect_public.py').read_text();exec(source.split("for sub in ('app','tests','scripts','export'):")[0],ns);add=ns['add']
for name in ['how_to.html','시연.html']:add(T/'app/static'/name,Path('labeltool/app/static')/name)
for p in C.glob('*.md'):add(p,Path('labeltool/reviews/easy_260921')/p.name,doc=True)
for p in R.iterdir():
 if p.is_file() and p.suffix in ['.py','.md']:add(p,Path('labeltool/reviews/easy_260921/demo')/p.name,doc=p.suffix=='.md')
add(W/'작업기록.md',Path('worklog/작업기록.md'),doc=True)
p=G/'NOT_UPLOADED.md';s=p.read_text();tag='## 2026-09-20 DEMO 추가 제외'
if tag not in s:s+='\n'+tag+'\n\n시연 사진·전 과정 화면·후보 확대·팀원 자료·원시 검증JSON·연습 사본은 제외했다. 폰PDF와 PDF인쇄원문은 로그인 장애 대응의 비밀번호 설정 위치를 포함하므로 공개본에서는 보수적으로 제외하고 인증된 운영 페이지와 로컬 문서에만 제공한다. 공개 텍스트 대본은 관련 줄을 가렸다.\n'
p.write_text(s)
p=G/'README.md';s=p.read_text();tag='## 2026-09-20 DEMO 갱신'
if tag not in s:s+='\n'+tag+'\n\n시연 최종 보고는 labeltool/reviews/easy_260921/demo/DEMO_완료보고.md, 실제31동작 대본은 labeltool/reviews/easy_260921/랩미팅_툴시연_대본.md에 있습니다. 사진과 폰PDF는 인증된 내부 운영 환경에서 제공합니다.\n'
p.write_text(s)
(R/'public_collection.json').write_text(json.dumps({'copied':ns['copied'],'redactions':ns['redactions'],'excluded':ns['excluded']},ensure_ascii=False,indent=2));print('공개 문서·코드',len(ns['copied']))
