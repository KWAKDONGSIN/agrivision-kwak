작성: 2026-09-20

# 구조 정리 5사이클 — 사이클 1 (기준선·tests·아카이브) 3차 판정 (Fable 5.1)

판정 시각(실측): 2026-09-20 00:38 · 근거: 1차 `stage1_work.md`(498줄) · 2차(공격적) `stage2_review.md`(584줄, 증거 `stage2_evidence/`)

## 1. 판정 — **합격. 기준선 확정 = 00:24:11 판(①②③④⑤ 0칸, 카운팅 5 코드 = 실서버 PID 1467097).**
| 항목 | 판정 |
|---|---|
| 스냅샷 `_archive/pre_refactor_260920/`(1,592파일 sha256 OK, 되돌리기 리허설 성공) · 아카이브 205개(`INDEX.md`) | 수용 |
| `tests/run_all.sh` 6묶음 · 아카이브 폴백 `lib/sandbox.py` · `--rebaseline`/`--check-baseline`/`--clean` | 수용 |
| 2차: 라우트 덮개 **11/37 → 37/37**(⑤ routes.json 118) — 카운팅 5 의 `export_boxes_to` 응답 3칸 변경을 1차 기준선이 못 잡았음을 실증 | **수용 — 이번 사이클의 핵심 발견** |
| 2차: `--check-baseline` 거짓 실패 · 지운 칸 26개(사과 stem·note) 되살림 · 옛 기준선 보존 `_baseline_prev/` · `u5_js_contract` 42항목 · `sim.js` 단정 0→9 · modesim 씨값 · `--clean` 12G→3.7M | 수용 |
| 리허설 2(정본 시험 `lib_s2.py` 한 줄로 77/0 · 스냅샷 복원 50항목 0칸) | 수용 |
| 유일한 실패 `test_fixes_m2 F7-c`(손 단정 977, 22:55 사람 확정으로 975) + 공용 `T/data` 읽는 merged 시험 4개 | **구조 2**: 손 단정을 얼린 표본/동적 계수로 |

## 2. 구조 2·3 에 내리는 결정
- **관문**: 시작 전 `run_all.sh --check-baseline` ④ 0칸 확인 → 작업 → `--browser --check-baseline` ①②③⑤ 0칸 + merged 실패는 F7-c 뿐(구조 2 가 고치면 0). 빠른 관문 `--no-merged --only=syntax,unit,sim,api`.
- **파일 소유**: 구조 2 = `app/*.py`·`core/`·`api/`·`domain/`·`export/*.py`·`tests/`(공용 — 구조 3 은 `tests/sim/`·`tests/browser/` 만 추가 가능) / 구조 3 = `app/static/**` 만. 서로 읽기만. 모래상자·포트 분리.
- **호환 껍데기(높음)**: 구조 2 는 `app/boxes.py`·`app/instances.py`·`app/dupes.py`·`app/maskio.py` 를 **얇은 재수출 모듈**로 남긴다(`from api.boxes import *` 식) — `build_merged_dataset.py:1480` `import boxes`, `counts/test_counts.py:158` `import instances`, 옛 사이클 시험이 계속 돌게. 그리고 `build_merged_dataset.py` 의 `except Exception` 자체 구현 폴백은 **조용히 떨어지지 않게**(폴백 사용 시 `problems` 기록 + verify 실패) — 0줄 json 규칙이 폴백에도 있어야 함(구조 2 가 그 파일 한 곳만 고침, 카운팅 판정과 충돌 없음).
- **JS 시뮬 로딩(높음)**: 구조 3 은 `app.js` 를 쪼개기 전에 `tests/sim/` 로더를 «쪼개진 파일을 순서대로 이어 붙여 cut 표식» 방식으로 바꿔 90항목이 살아남게 하고, 함수 이름 25개·전역 `S`·`API`·`UI` 계약(u5)을 통과.
- 얼린 표본에 `flag` 판정 한 장 추가 · `/login` 429 라우트 덮기 · `sandbox.py sync(src=)` — 구조 2 시험 위생.
- 남긴 백업 36개(`cnt4*`·`cnt5*`): 카운팅 코드가 굳었으므로 **구조 2 가 아카이브로 옮기고**(폴백 있음) 죽는 정본 시험 35개 중 lib 를 안 거치는 20개는 목록만(원본 무수정).
- 화면 배율 2x/3x 상자 이동 결함(sim.js 가 굳힌 것)은 **동작 무변경 원칙상 이번엔 고치지 않고** 열린 문제로.

## 3. 남긴 것
사람: `scripts/ff.py` 기본 주소 실서버(시험 전 `LABELTOOL_URL`) · 삭제 목록 · 사용자 이름 칸.
