대행: Codex
작성: 2026-09-20
검증시각: 2026-09-20T13:01:35.591215+09:00

# 1차 작업

## 범위와 판정

A~E 준비 완료. 실서버 PID1467097은 유지하고 파일만 반영했다. 2차 새 사본 검수와3차 최종판정은 별도다.

## 수행

- 기존 시작시각·84파일 SHA 보존. 덮기 전 _archive/pre_finish_260920에 app/scripts/export/tests 실복사.
- 옛 복원 사본 포트5601에서4과일·4사진. 첫 시도 공백 URL 인코딩 오류는 시험 코드 수정 후 새 사본 재현.
- 후보 API8파일·README 및ff.py 반영. 공통clean에서 비유한 좌표ValueError, 저장·팀원초벌 호출부400. 정상·혼합·빈목록 유지.
- 단독 보호91단정. URL없으면 드라이버 시작 전 중단.
- 원래 기준선 baseline_260920_pre_split에 보존, --rebaseline으로 새 지문 수집. 기존15회귀묶음 임계값은 유지. 차이는 정적6칸, API·산출 지문 동일. 승인자·전후값은 BASELINE_CHANGELOG.
- bash tests/run_all.sh --browser --check-baseline 결과1193/0·510초·rc0. 이전1124에는 후보의 추가22단정이 포함됐고 이번1193은 기존1102+새91이다. 서로 다른 묶음 합계를 같은 시험수처럼 비교하지 않는다.
- 실제12장 비교12/12바이트 동일·36상태 동일·오류0. 오래된 복원 스냅샷을 처음 비교자로 고른 결과는 별도 보존. 그 판의 카운팅 문구3곳은 최종 구조검수 기준과 달라 올바른 기존 기준 사본으로 재실행했다.
- 포트5671 새 서버에서 비로그인401→로그인→4과일·첫사진item/boxes/PNG→상자1저장·되돌리기→내보내기 안내. 기존 상자·판정 바이트복원. pre_finish 복원84지문·재기동4과일 성공.
- 전환하기.md와after_restart_smoke.py 준비. 실5111에 쓰기시험·재시작은 실행하지 않았다.

## 증거

evidence/rollback_old.json, applied_candidate.json, ff_guard.json, baseline_changes.json, full_regression.log, full_regression.rc, full_bundles.tsv, browser12.json, smoke.json, rollback_pre_finish.json.

## 남은 일

2차 새 사본·새 포트 검수→최종판정·폰용보고→비밀검사·업로드→FINISH_DONE. 전환 자체는 사람이 한다.

## 2차 발견 반영 후1차 보완

core/domain8파일의 타입·설명 누락을 반영했다. 최종 전체명령은 동일하며 1193/0·501초·rc0이다. 증거 full_regression_final2.log·full_regression_final2.rc·full_bundles_final.tsv. 앞선510초 결과와구분한다.
