# 이 시험들은 어디서 왔나 (ORIGIN)

작성: 2026-09-19

`tests/` 안의 시험은 **새로 쓴 것이 아니라 사이클마다 흩어져 있던 것을 복사해 온 것**입니다.
원본은 그 자리에 그대로 두었습니다(사이클 기록이라 지우지 않습니다).
바뀐 것은 **경로·포트 하드코딩뿐**이고, 그것도 `tests/lib/` 한 군데로 모았습니다.

## 복사해 온 것

| tests/ 안 | 원본 | 손댄 곳 |
|---|---|---|
| `api/t1_api.py` | `cycles/260918_paint/cycle_4/stage1/t1_api.py` | `import lib_c4 as L` → `import sandbox as L` (1줄) |
| `api/regress_all.py` | `cycles/260918_paint/cycle_4/stage1/regress_all.py` | 위와 같은 1줄 + `PORT = 5313` → `L.free_port(5501)` + `SB` → `L.SB_REG` (3줄) |
| `browser/t2_ui.py` | `cycles/260918_paint/cycle_4/stage1/t2_ui.py` | 위 1줄 + 단정 «나-1» 의 기대 문구(아래 §기대값) |
| `browser/b1_browser.py` | `cycles/260919_count/cycle_4/**stage2**/b1_browser.py` (21:01 판) | `import lib_cnt4b as M` → `import sandbox as M` (1줄) + `GRAPE_ON = False` → **`L.grape_seeded()`** (아래 §기대값) |
| `sim/sim.js` | `cycles/260917_신기능/cycle_1/stage1/sim.js` (= `cycles/cycle_1/stage1/sim.js` 와 동일 md5) | 없음 |
| `sim/boxsim.js` | `cycles/260917_신기능/cycle_2/stage1_client/boxsim.js` | `app.js` 경로 1줄 → `require("../lib/paths.js").APP_JS` |
| `sim/modesim.js` | `cycles/260917_신기능/cycle_2/stage2/modesim.js` | 위와 같은 1줄 |
| `sim/*.json` | 같은 `stage1_client/` 의 녹취 응답 5개 | 없음 |
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| `merged/run_merged.sh` | 새로 쓴 것(호출만) | 원본 시험은 `semantic-segmentation/tools/tests_merged_260918/` 에 **그대로** |
| `unit/u1~u3` | 새로 쓴 것. `u1` 은 `app/boxes.py` 의 `demo()` 를 부르는 것뿐(예전 `runall.sh` 의 `$PY app/boxes.py` 와 같은 일) | – |
| `baseline/snapshot.py` | 새로 쓴 것 | – |

## 일부러 가져오지 **않은** 것 (이유 있음)

| 원본 | 왜 안 가져왔나 |
|---|---|
| `cycles/260918_paint/cycle_4/stage1/t3_chars.py` · `260919_count/*/b3_chars.py` · `t3_chars_cnt1*.py` | **«전 대비 늘어난 글자 수»** 를 재는 시험이다. «전» 이 그 사이클의 `_backup_*` 이라 사이클마다 기준이 옮겨 간다 → 늘 돌리는 회귀에 넣으면 뜻이 없다. 사이클마다 그 자리에서 돌린다 |
| `cycles/260918_paint/cycle_4/stage1/mk_reg_c4.py`·`mk_reg_c4b.py`·`reg_c4*/` · `260919_count/*/mk_reg_cnt4*.py` | 앞 사이클 시험을 **포트·경로만 바꿔 복제하는 생성기**다. 지금은 `tests/lib/sandbox.py` 하나가 그 일을 하므로 복제가 필요 없다 |
| `cycles/260918_paint/cycle_4/stage1/fix_expect_c4.py`·`rerun_fixed.sh`·`final_check.sh` | 그 사이클의 기대값을 고치던 일회용 |
| `cycles/260919_count/cycle_4/stage2/b2_export.py`·`b4_fallback.py`·`b5_oldserver.py`·`grape_onoff.py`·`s_scenario.py` | 2026-09-19 22:00 현재 **다른 세션이 쓰고 있는 파일**이다(카운팅 사이클 5 진행 중). 그 사이클이 끝난 뒤 **구조 사이클 2** 가 `tests/browser/` 로 가져오면 된다 |
| `cycles/260917_신기능/cycle_2/stage1/sim.js`(14KB)·`cycle_2/stage2/bbsim.js` | `boxsim.js`·`modesim.js` 가 같은 구간을 더 넓게 덮는다(원본 판정서 기준) |
| `cycles/260918_paint/cycle_4/stage2/*`(`s1`~`s6`) · `cycles/260919_count/cycle_1/stage2c/*` | 그 사이클의 **공격적 검수** 묶음. 지금 코드에 대한 회귀로는 `t1_api`·`regress_all`·`b1_browser` 가 같은 길을 지난다. 필요하면 원본 위치에서 그대로 돌아간다 |

## 원본 «재현 명령» 이 적혀 있는 곳

각 사이클의 `stage1_work.md`·`stage2_review.md` §«재현 명령». 특히
`cycles/260918_paint/cycle_4/stage1/runall.sh` 가 0918 판의 «한 번에» 명령이고,
`cycles/260919_count/cycle_4/stage1/runall_cnt4.sh` 가 0919 판입니다.
`tests/run_all.sh` 는 그 둘에서 **늘 돌려야 하는 것만** 남긴 것입니다.


## 기대값을 고친 두 곳 (실측으로 잡았습니다 — 2026-09-19 22:32~22:39)

옮겨 온 시험 두 개가 **그 사이클 당시의 문구·설정을 그대로 적어 두고 있어서** 지금 코드에서 실패했습니다.
코드는 한 글자도 고치지 않았고, **시험의 기대값만** 지금 코드가 실제로 하는 일에 맞췄습니다.

### ① `browser/b1_browser.py` — 포도 초벌 출처

- 처음 가져온 판(stage1 19:36)은 포도 기대값이 `certh_gt` 였는데 지금 코드는 **`cc4`** 를 준다.
  `app/instances.py` 의 `SEED_DIRS` 에서 **포도가 주석으로 꺼져 있다**(«교수님 확인 8번 뒤에 되살릴 줄»).
  ③ 번호 단추도 그래서 잠긴다. 실측: `grape/edit: 서버 seed_source = certh_gt | cc4` 실패 3건.
- 그 사이클의 **2차 판(stage2 21:01)** 이 이미 `GRAPE_ON = False` 로 고쳐 두었더군요. 그것을 가져왔고,
  거기서 한 걸음 더 나가 **`GRAPE_ON = L.grape_seeded()`** 로 바꿨습니다 —
  `app/instances.py` 의 `SEED_DIRS` 를 **읽어서** 정하므로, 교수님이 포도를 켜는 날
  시험을 손대지 않아도 기대값이 따라갑니다. 손으로 적은 기대값은 반드시 낡습니다.
- 고친 뒤: **81항목 전부 통과**(원본 `stage2/b1_final.log` 21:42 와 같은 81/0).

### ② `browser/t2_ui.py` 단정 «나-1» — ③ 하단 한 줄

- 0918 판은 «**AI 초벌** 번호 … 맞으면 Enter» 라는 글자를 요구했는데, 0919 «개수 세기» 사이클이
  그 한 낱말을 **출처 이름**으로 바꿨습니다. 지금 실제 문구: «원본 정답 번호 1개 — 맞으면 Enter».
- 그래서 «초벌» 이라는 글자를 요구하지 않고 «**번호** + 출처 낱말 하나(초벌·정답·박성문·고친·4-연결) +
  **Enter**» 를 요구하도록 바꿨습니다. «출처를 지어내지 않는가» 는 `b1_browser` 가 서버 응답과
  대조해 보고 있으므로 덮이는 길이 줄지 않습니다.
- 고친 뒤: **27항목 전부 통과**.

이 두 가지는 «동작이 바뀌었다» 는 뜻이 **아닙니다** — 시험이 낡았던 것입니다. 기준선(①②③)은
고친 뒤에 떴으므로 지금 코드를 정확히 담고 있습니다.
