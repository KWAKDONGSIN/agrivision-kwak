대행: Codex
# 기준선 baseline_260920

작성: 2026-09-19

`tests/run_all.sh --rebaseline` 이 만든 폴더입니다. **리팩터 전 코드**(카운팅 사이클 4 판 ·
실서버 PID 964494 와 같은 판)의 «동작» 을 숫자로 굳혀 둔 것입니다.

| 파일 | 무엇 | 개수 |
|---|---|---:|
| `api/*.json` + `api_sha256.txt` | 고정 표본 API 응답(변하는 칸 지움) | 100 |
| `exports.json` | 내보내기 산출 파일 sha256 | 119 |
| `bundles.json` | 회귀 묶음별 통과/실패 | 21 |
| `code_sha256.json` | 정적 파일·서버 코드 sha256(**참고용**) | 52 |
| `stems.json` | 고정 표본 12장 | 12 |
| `routes.json` | ⑤ 나머지 라우트·쓰기 경로·쓰기 뒤 디스크 | 118 |

- 고정 표본 목록: `tests/fixtures/stems.txt`
- 얼려 둔 판정 자료: `tests/fixtures/status_260920/` (표본 12장 몫만)
- 대조: `bash tests/run_all.sh --check-baseline`
- `api/*.json` 안의 `⟨지움⟩` 은 «시각·PID·경로·사람 이름처럼 돌릴 때마다 달라지는 칸» 입니다.
  구조(어느 칸이 있었는지)는 남겨 두었으므로 **칸이 사라지면 잡힙니다.**
- `code_sha256.json` 이 달라지는 것은 **정상**입니다(리팩터가 하는 일). 실패로 세지 않습니다.
- 옛 기준선은 지우지 않고 `tests/fixtures/_baseline_prev/<날짜시각>/` 에 최근 10판 남깁니다.
  «전과 무엇이 달라졌나» 는 `diff -r` 로 봅니다(이 폴더는 git 밖입니다).
