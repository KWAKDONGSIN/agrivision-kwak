작성: 2026-09-22 16:50

# 계획 — 툴 «최대한 간편하게» (팀 요청 09-22 오후)

사용자 지시(16:40~16:48). «다각형 대신 칠해진 열매를 클릭하면 번호가 붙게» · «지우개로 모든 라벨을 지울 수 있게» · «포도·사과 AI 판정 재확인 결과를 반영» · «컴퓨터가 꺼져도 돌아가게(자동 진행기)» · «최대한 빠르게, Codex 든 Claude 든».

원칙. 정적 파일만 고치면 재시작 없음(새로고침으로 반영). 파이썬을 고치면 `bash app/run.sh restart`(사용자 승인 있음). 고치기 전 `_backup_260922_<태그>_<파일>` 백업. 모래상자(`tests/lib/sandbox.py` + 헤드리스 파이어폭스)로 실측한 뒤 `run_all.sh --no-merged --only=syntax,sim`. 깃은 `prepare_public.py`(이 폴더 것) → `audit_public.py` → 커밋 → `GIT_SSH_COMMAND='ssh -i ~/.ssh/agrivision_deploy -o IdentitiesOnly=yes' git push origin main`. 실서버 5111 은 자기 PID 만. GPU 안 건드림. 사람 확정(confirmed) 값은 절대 안 바꿈.
