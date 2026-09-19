작성: 2026-09-14

## 2026-09-14 확인 — HamNet 헤더 구현 여부 · Codex 연동 상태

### 왜 했나
- 12×12 grid 에 새로 들어온 HamNet(H025) 헤더가 우리 코드에 실제로 구현돼 있는지 확인
- Codex 를 붙여서 같은 연구를 2차 검토시킬 수 있는지, 이미 연결돼 있는지 확인

### 한 일
- 공용 코드 `platform/03_code/semantic-segmentation` 에서 LightHamHead 구현 검색
- 개인 레포 `kds0206/semantic-segmentation` 의 같은 이름 파일과 비교
- 서버의 Codex 설치·로그인·Claude Code 연동 상태 조사
- `codex exec` 비대화형 호출이 되는지 1회 시험

### 결과
- LightHamHead: 공용 코드에 있음. `semseg/models/heads/lightham.py` (NMF2D · Hamburger · LightHamHead, SegNeXt/mmseg ham_head 포팅). 모델 래퍼 `semseg/models/lightham.py`, 두 `__init__.py` 에 등록. stage 1~3 만 사용, ham_channels 256, MU 반복 train 6 / eval 7, R=64
- 주의: 개인 레포 `kds0206/semantic-segmentation/semseg/models/heads/lightham.py` 의 LightHamHead 는 이름만 같고 NMF·Hamburger 가 없음. 개인 레포로 HamNet 결과를 내면 안 됨. factorial 은 공용 03_code 사용(동결기록 34행)
- `platform/planning/frozen/실행설정.yaml` 73행의 "H025 HamNet 레포 미구현" 주석은 낡은 것(공용 코드엔 구현됨). 교수님 파일이라 수정하지 않음
- Codex: 서버에 설치돼 있음(`~/.npm-global/bin/codex`, codex-cli 0.144.6, 2026-07-20 설치). ChatGPT 계정 로그인 상태
- Codex 와 Claude Code 연결(MCP·플러그인)은 없음. 지침 공유는 `semantic-segmentation/AGENTS.md → CLAUDE.md` 심볼릭 링크 하나뿐
- 곽동신 계정의 Codex 세션 기록 없음(로그인만 하고 사용 이력 0회)
- `codex exec --sandbox read-only --skip-git-repo-check "..."` 로 호출하면 응답 옴(시험 1회, 5,293 토큰). git 저장소 밖에서는 `--skip-git-repo-check` 가 없으면 거부됨
- 교수님(ahnbi3) 계정은 별도 codex 0.153.4 를 09-05 부터 상시 실행 중

### 막힌 것
- 없음

### 다음
- [ ] Codex 2차 검토 방식 결정: (1) Claude 가 `codex exec` 로 읽기 전용 호출해 의견 병기 (2) 터미널 2개 병행 (3) MCP 정식 연결(버전 업데이트 필요할 수 있음)
- [ ] 실행설정.yaml 73행 낡은 주석은 교수님께 알려서 정리

### 관련 파일
- `platform/03_code/semantic-segmentation/semseg/models/heads/lightham.py`
- `platform/03_code/semantic-segmentation/semseg/models/lightham.py`
- `platform/04_experiments/260908_파일럿/코드_스냅샷/semseg/models/heads/lightham.py`
- `platform/planning/frozen/260908_체크포인트_동결기록.md`
- `platform/planning/frozen/실행설정.yaml`
- `kds0206/semantic-segmentation/AGENTS.md` (→ CLAUDE.md 링크)
- `kds0206/작업기록.md` (2026-09-14 항목)
