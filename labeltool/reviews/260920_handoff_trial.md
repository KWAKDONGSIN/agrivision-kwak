대행: Codex (Claude 한도 초과)

# 대화 맥락 없는 새 에이전트 인수인계 시험

작성: 2026-09-20, KST(+09:00). 제품 대화 맥락 없이 별도 에이전트가 지정된 연습 사본에서 직접 수행했다. 하위 에이전트는 사용하지 않았다.

작업 폴더: `cycles/260920_structure/codex_resume/handoff_trial`.
처음 읽은 파일은 이 폴더의 `app/README.md` 하나였다. README를 읽기 전 소스·다른 지침을 탐색하지 않았다.
README 첫 읽기와 소스 위치 확인 시각은 도구 실행의 `date -Is` 출력이며, 이후 시작·종료 시각은 `handoff_evidence/*_start.txt`, `*_end.txt`에도 보관했다.

## 실측 결과

| 항목 | 시작(KST) | 완료(KST) | 소요 | 기준 | 판정 |
|---|---|---|---|---|---|
| (다) 첫 README에서 «이진본이 번호본을 자른다» 위치를 찾고 실제 정의 확인 | 02:50:38 | 02:50:45 | 7초 | 30초 | 통과 |
| (가) 첫 README 읽기부터 모래상자 서버 실행과 1차 전체 시험 완료 | 02:50:38 | 02:59:11 | 513초 / 8분 33초 | 30분 | 통과 |
| (나) 레시피에 따른 응답 수정부터 실제 저장 검증과 2차 전체 시험 완료 | 02:59:42 | 03:07:53 | 491초 / 8분 11초 | 2시간 | 통과 |

참고: (나)의 전용 확인 스크립트와 대상 응답 위치는 1차 시험이 실행 중일 때 미리 읽고 준비했다. 준비 시간을 빼서 결과를 과장하지 않도록, **최초 README 읽기부터 2차 완료까지 포함해도 1,035초 / 17분 15초**임을 함께 기록한다.

- 1차 서버 실행+시험 명령 묶음: 02:51:01~02:59:11, 490초. 실제 `tests/run_all.sh --browser` 보고 시간은 488초.
- 1차 전체 결과: **23묶음, 단정 1,102 통과 / 0 실패, rc=0**.
- 2차 실제 저장 검증: 02:59:42~02:59:45. 2차 전체 시험: 02:59:45~03:07:53, 488초.
- 2차 전체 결과: **23묶음, 단정 1,102 통과 / 0 실패, rc=0**.
- 두 번 모두 unit 210, sim 90, API 158, merged 536, browser 108 단정이 통과했다. 문법 4묶음과 브라우저 준비 묶음은 rc=0이며 단정 수 합계에 넣지 않았다.

## 실행 명령과 확인 결과

모든 명령은 지정 작업 폴더에서 아래 환경을 먼저 설정했다. 긴 실행은 `timeout`을 적용했다.

```bash
export CODEX_REVIEW_ROOT=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/cycles/260920_structure/codex_resume
export PYTHONPATH="$CODEX_REVIEW_ROOT/safety"
export PATH="$CODEX_REVIEW_ROOT/bin:$PATH"
```

1. 02:50:38: `date -Is; cat app/README.md; date -Is`.
2. 02:50:45: `date -Is; rg -n 'def cut_by_binary|def load_inst' app/domain/rules.py app/api/instances.py; date -Is`.
   README §5의 A1이 `domain/rules.py:cut_by_binary()` → `api/instances.py:load_inst()`를 가리켰다.
   실제 정의는 각각 `app/domain/rules.py:228`, `app/api/instances.py:144`였다.
3. `sed -n '1,230p' tests/run_all.sh`, `sed -n '1,260p' tests/lib/sandbox.py`로 실행 범위와 서버 종료 방식을 확인했다.
4. 02:51:01: README 서버 실행 예제를 다음과 같이 실행했다.

```bash
PY=/home/kds0206/.conda/envs/kwak/bin/python
PYTHONPATH="tests/lib:$PYTHONPATH" timeout 120 "$PY" - <<'PYCODE'
import sandbox as L
p = L.start(port=L.free_port(5901), sb=L.T, pw='handoff-local')
try:
    print('서버 실행 확인. 로그인 화면 응답은 start()가 확인했습니다.')
finally:
    L.stop(p)
PYCODE
timeout 1800 bash tests/run_all.sh --browser > handoff_evidence/first_run.log 2>&1
```

로그인 화면 응답 확인 완료. 포트 5901, PID 1885029를 직접 시작하고 종료했다.
`first_run_rc.txt`, `first_run_bundles.tsv`, `first_run_logs/`에 1차 결과를 별도 보관했다.

5. `sed -n '260,365p' tests/lib/sandbox.py`, `rg -n 'def api_boxes_save|jsonify|def api_list' app/api/boxes.py app/api/photos.py`, `sed -n '220,277p' app/api/boxes.py`로 API와 성공 응답 위치를 읽었다.
   원래 코드는 `handoff_evidence/boxes_before.py`와 `boxes_before.sha256`에 보관했다.
6. 02:59:42: 1차 성공을 확인한 뒤, Python 문자열 치환으로 `app/api/boxes.py:270`의 성공 응답 한 줄에만 `"handoff_probe": True`를 추가했다. 대상 문자열이 정확히 한 번 존재함을 단정했다.
   변경 전후 차이는 `handoff_evidence/probe_change.diff`에 보관했다.

```diff
-        return jsonify({"ok": True, "n_boxes": len(boxes), "dropped": dropped,
+        return jsonify({"ok": True, "handoff_probe": True, "n_boxes": len(boxes), "dropped": dropped,
```

빈 상자 응답, 요청 검증, 디스크 레코드, 저장과 확정 로직은 고치지 않았다.

7. 실제 요청 확인과 2차 전체 시험:

```bash
PYTHONPATH="tests/lib:$PYTHONPATH" timeout 120 /home/kds0206/.conda/envs/kwak/bin/python -u handoff_evidence/verify_probe.py
 timeout 1800 bash tests/run_all.sh --browser > handoff_evidence/second_run.log 2>&1
```

확인 스크립트는 `L.sync(sb=tests/_sandbox/handoff_probe)`로 별도 복사본을 만들고 포트 5901, PID 1914016의 서버에서 인증 후 **`POST /api/boxes`**를 실행했다. 요청은 `fruit=peach`, `stem=210629-t1-01`, `by=handoff trial`, 상자 하나(`id=1`, `cls=fruit`, `xyxy=[10,20,40,50]`, `src=human`)였다.

02:59:45의 실제 응답은 **HTTP 200 / ok=true / handoff_probe=true / n_boxes=1 / dropped=0 / over=0**이었다. 이를 모두 직접 단정했으며 저장 파일의 boxes 배열도 한 개임을 단정했다.
`tests/_sandbox/handoff_probe/data/peach/boxes/210629-t1-01.json`과 같은 과일의 `status.json`을 다시 읽어 재귀 검사했고, **두 JSON 모두 `handoff_probe` 필드가 없다**. 요청 결과와 디스크 JSON 내용은 `handoff_evidence/probe_result.json`, 전체 출력은 `probe.log`에 보관했다. 이 검증 서버도 종료했다.

## 막힌 곳과 한계

- 실행을 중단시킨 오류는 없었다. 다만 **최초 README §1 예제의 `PYTHONPATH=tests/lib`는 기존 PYTHONPATH를 덮어 보존 래퍼를 누락시킬 수 있었다.** 상위 시험 지시를 지키기 위해 `PYTHONPATH="tests/lib:$PYTHONPATH"`로 실행했다. README는 §6에서 별도 보존 래퍼를 쓰라고 하지만 §1 예제는 이를 보존하지 않는 문서 문제다. 시험 사본의 README는 수정하지 않고 이 문제를 부모에게 알렸다. 이는 오류가 없었던 것으로 숨기지 않는다.
- 두 번의 `browser/t2_ui`에는 기존 경고 한 건이 있었다: 시험 도구가 프로필을 새로 만들어 «창을 완전히 닫았다 열기»를 직접 재현하지 못해 새로고침으로 대신했다. 해당 기능의 완전한 재시작 지속성까지 검증했다고 주장하지 않는다.
- `--check-baseline` 및 `--rebaseline`은 실행하지 않았다. README에 적힌 원래 엄격 기준선의 정적 6칸 차이가 해결됐다는 뜻이 아니다. 전체 회귀 통과와 기준선 통과를 구별한다.
- 연습 수정은 이 사본에만 남겨 보관했다. 제품 후보와 운영 서버에 반영하지 않았다. 이 인수인계 시험 결과만으로 운영 전환을 승인하지 않는다.

## 작업 경계와 종료 확인

원본 데이터·다른 작업자의 폴더는 읽기만 했고, 실서버 5111 및 5100·5101·5105·5001에 요청하거나 해당 프로세스를 종료하지 않았다. GPU 학습, 삭제 명령, pkill은 실행하지 않았다. 기존 시험 도구의 정리 동작은 지정된 보존 래퍼를 상속해 보관 경로로 이동하게 했다. `_archive` 심볼릭 링크는 읽기만 했다.
브라우저는 기존 `scripts/ff.py` 경로로 실행했고 스크린샷은 `~/ff_shots/tests_260920/`에만 생성됐다.

PID 기록: `handoff_evidence/remaining_pids.json`. /proc에서 이 시험 폴더 아래 cwd를 가진 프로세스(검사 명령 자신·조상 제외)를 확인했고 **잔여 0개**였다. 두 전체 시험과 직접 검증에서 로그에 기록된 서버 PID는 시작/종료 목록이 일치하고 /proc에 남은 PID도 0개였다.

## 증거 파일

- `handoff_evidence/first_run.log`, `first_run_bundles.tsv`, `first_run_logs/`, `first_run_start.txt`, `first_run_end.txt`, `first_run_rc.txt`
- `handoff_evidence/second_run.log`, `second_run_bundles.tsv`, `second_run_logs/`, `second_phase_start.txt`, `second_run_start.txt`, `second_run_end.txt`, `second_run_rc.txt`
- `handoff_evidence/verify_probe.py`, `probe.log`, `probe_result.json`, `probe_change.diff`, `boxes_before.py`, `boxes_before.sha256`
- `handoff_evidence/remaining_pids.json`

최종 PID 검사 실제 시각: 2026-09-20T03:10:05.201735+09:00. 보고서 작성 실제 시각: 2026-09-20T03:10:05.202745+09:00.
