# 자동 라운드 — 라벨링 툴(그림판) «전부 업그레이드» 사이클 (한 라운드 = 체크리스트 한 항목)

너는 자동으로 깨어난 Claude 다. 사용자(곽동신, 데이터사이언스 초보)는 컴퓨터를 꺼 두었다.
한국어로 일하고, 한국어 문장은 마침표로 끝낸다(문장 끝에 콜론 금지). 사람에게 질문하지 말고 합리적 기본값으로 진행한다.

## 먼저 읽을 것
1. `/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/cycles/260925_업그레이드/plan.md`
2. 같은 폴더 `checklist.md`, `context-notes.md` 끝부분, `auto/STATUS.md` 끝부분
3. `/data/project/2026summer/kds0206/작업기록.md` 의 「1. 현재 상태」 윗부분만(전체를 읽지 말 것)

## 자료 위치
- 실서버 앱: `260916_라벨링툴/app/` (포트 5111, 그림판 = `app/static/paint/`), ✨ 도우미 `ai_helper/sam_server.py` (127.0.0.1:5112, GPU7)
- 녹음 txt: `/data/project/2026summer/platform/00_meetings/*.txt`, `kds0206/연구실 블루베리/06_교수님미팅_기록/*.txt`
- 논문·조사: `kds0206/연구실 블루베리/01_*`, `03_*`, `kds0206/문서/`
- 팀원(읽기만): `platform/work/{choi_inhun,im_seonghu,park_seongmoon}`, `/data/project/2026summer/{jjw0602,lsh0616,nsm0404,plant,dup_review,defect-seg-benchmark}`
- 이미 나온 결과는 다시 만들지 말고 이어서 쓴다. 예: `kds0206/문서/260925_팀원작업환경_조사.md`, `cycles/260925_업그레이드/codex_review/codex_review.md` 가 있으면 읽고 검증·보완만.
- 시험: `tests/run_all.sh`, `tests/browser/run_paint_e2e.sh <포트>`. 전체 시험은 `flock <사이클>/auto/tests.lock bash tests/run_all.sh ...` 로 한 번에 하나만.

## 한도 아끼기 (연구실 계정은 여럿이 같이 쓴다)
- 필요한 파일의 필요한 부분만 읽는다. 큰 파일은 grep 으로 찾아서 부분만.
- 하위 에이전트를 띄우지 않는다. 인터넷은 WebSearch/WebFetch 만. 유료 API(fal·ElevenLabs·Exa) 금지.
- 두 번째 의견이 필요하면 jev 도구(mcp__jev__*)를 쓴다.

## 반드시 지킬 것
- 남의 프로세스 kill 금지(5100·5105 교수님, 5101 Jupyter, 다른 사람 python). 내가 띄운 모래상자 서버만 끈다.
- 원본 데이터(`data/`, `dataset_*`, `datasets_*`)와 팀원 폴더는 읽기만. 시험 쓰기는 `tests/_sandbox/` 안에서만. `rm -rf` 금지.
- 앱 코드(`app/`, `ai_helper/`)는 **w1 레인만** 고친다. 다른 레인은 고칠 것을 `checklist.md` 의 「코드」 구역 맨 아래에
  `- [ ] 코드 C<번호> 내용 (근거: 파일경로)` 로 추가만 한다. 코드 항목은 전체 30개를 넘기지 않는다.
- 고치기 전 그 파일을 끝까지 읽고, 같은 폴더에 `_backup_260925_<항목>_<파일명>` 백업을 남긴다. 요소 id·단축키·API 규칙 유지, 새 CDN 금지.
- 정적 파일(html·css·js)은 재시작 없이 반영된다. 파이썬을 고쳤으면 모래상자 시험 통과 뒤 `touch app/logs/restart.flag`(감시자가 1분 안에 재시작).
- GPU 는 5·6번만(7번은 ✨ 도우미). 쓰기 전 `nvidia-smi` 로 비었는지 확인. 긴 작업은 `setsid nohup` 으로.
- 기존 체크포인트·결과 덮어쓰기 금지. 데이터셋 정본 전환·카톡 발송·GitHub force push 금지. GitHub push 는 Z01 에서만.
- 새 문서는 `kds0206/문서/260925_제목.md`, 본문 첫 줄 `작성: 2026-09-25`. 새 소스 파일 첫 줄은 한국어 한 줄 주석.
- 시각을 적을 때는 반드시 `date` 로 잰다. 짐작한 시각을 쓰지 않는다.

## 끝낼 때
- `checklist.md` 의 내 항목 표시 갱신. `context-notes.md` 맨 아래에 시각과 «무엇을 왜» 2~4줄.
- `auto/STATUS.md` 에 한 줄. `작업기록.md` 「2. 작업 이력」 맨 위에 짧은 항목(만든·고친 파일 경로 포함)과 `최종 수정:` 갱신.
