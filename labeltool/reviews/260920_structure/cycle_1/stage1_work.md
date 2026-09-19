작성: 2026-09-19

# 툴 구조 정리 5사이클 — **사이클 1 (공격적) 1차 작업** 보고서

작업자: Opus 5 · 시각은 전부 서버 `date` 실측(추정값 없음)
시작 **2026-09-19 21:47** · 끝 **23:17** (1시간 30분)

지시서: `kds0206/문서/260919_툴_구조정리_인수인계_5사이클_지시.md` §0·§1(라)·§2·§4 사이클1 행·§5
병렬 지시: `kds0206/문서/260919_속도단축_병렬화_지시.md` §1 (1번 — 카운팅 사이클 5 와 동시 진행)

## 0. 한 장 요약

| 만든 것 | 경로 | 숫자 |
|---|---|---|
| 리팩터 전 스냅샷 | `T/_archive/pre_refactor_260920/` | 파일 **1,592개** · 37MB · `MANIFEST.txt` 1,608줄 |
| 백업 아카이브 | `T/_archive/backups_260920/` | **205개 옮김** (원래 상대경로 유지) · `INDEX.md` |
| 시험 모음 | `T/tests/` | 묶음 **6개** · 단정 **890개** (실패 1 — §4-2 · 내 작업 탓이 아니다) · 455초 |
| 기준선 | `T/tests/fixtures/baseline_260920/` | 항목 **243개** = API **100** + 내보내기 **99** + 묶음 **14** + 코드지문 30 (①②③ **213개가 합격 기준** · ④ 30개는 참고) |
| 문서 | `T/tests/README.md` · `T/tests/ORIGIN.md` · 두 아카이브의 `README.md`·`INDEX.md` | – |

**합격 확인 (전체 통과 실행 · 22:40:37 → 22:48:11)**
`bash tests/run_all.sh --browser --check-baseline` → **884 통과 / 0 실패 · rc 0 · 454초** ·
기준선 ①②③ **다른 칸 0개**.

**그 뒤 22:55:23 에 팀원이 실서버에서 복숭아 한 장을 «문제 있음» 으로 확정**해서
통합 시험 하나(`stage2/test_fixes_m2.py F7-c`, «복숭아 상자 977줄» 을 **손으로 적어 둔** 단정)가
975줄이 되어 실패로 돌았다. **내가 만든 것이 아니고 내 작업 탓도 아니다**(원인·증거 §4-2).
그래서 최종 실행(23:04→23:11 `--rebaseline`, 23:12→23:17 `--check-baseline`)은
**890 통과 / 1 실패 · 455초**이고, 기준선 대조는 **①②③④ 전부 «다른 칸 0개»** 다.

⛔ 지킨 것: 실서버(5111 · PID 964494) **재시작·쓰기 0** — 작업 끝에도 `login=200`·가동 1시간 32분 ·
`app/*.py`·`app/static/*`·`export/*` **수정 0** · 공용 `T/data` **쓰기 0** ·
`T/exports` 쓰기 0 · 삭제 0(옮기기만) · GPU 0 · 새 패키지 0 · `pkill` 0 · `작업기록.md` 미갱신(상위 세션 몫).

«공용 `T/data` 쓰기 0» 을 어떻게 아나: 네 `status.json` 중 **사과·포도·블루베리 셋은 21:58 스냅샷과
sha256 이 같고**, 복숭아만 22:55:23 에 바뀌었는데 그 기록의 `by` 가 **«익명»**(웹에서 누른 사람)이다.
내 시험들이 쓰는 이름은 `기준선`·`곽동신` 인데 **네 파일 어디에도 없다.**
실서버 로그에 그 시각 112.149.154.206 의 요청이 찍혀 있다.

## 1. 스냅샷 `_archive/pre_refactor_260920/`

- 뜬 시각 **21:58**. `cp -a` 로 `app/`·`export/`·`scripts/` **전체**(`_backup_*`·`cache/`·`logs/` 포함).
- `MANIFEST.txt` — `<sha256>  <바이트>  <상대경로>` 1,592줄 + 맨 끝에 §status.json·§duplicates.json
  (공용 `data/` 는 90MB 라 담지 않고 **지문·mtime 만** 8줄).
- `README.md` — «리팩터 전 판» 이 무엇이고 **되돌리는 법**(실서버 끄기 → 지금 판을 `rollback_*` 로 치우기 →
  `cp -a` → 다시 켜기 → `sha256sum -c` 로 확인)까지 한 벌.
- **무결성 실측(23:22)**: `sha256sum -c` **1,592개 전부 OK · 실패 0**.
  ⚠ 확인 명령을 한 번 고쳤다 — 사진 이름에 **빈칸이 있는 것이 171개**(`Camera 1 Video (1)_1.png` 등)라
  `awk $3` 로 경로를 자르면 374개가 조용히 빠졌다(처음 판은 1,218개만 검사했다).
  지금은 «79번째 글자부터가 경로» 로 자른다. 그 명령이 `README.md` 에 들어 있다.
- 이 스냅샷은 **실서버가 그 때 돌리던 코드와 같은 판**이다. 작업 끝(22:48)에 다시 md5 를 재어
  `server.py dfde8c1b…`·`boxes.py bf10b322…`·`instances.py 3d77b583…`·`app.js c774ae54…`·
  `ui.js 0e1d7cd6…`·`export_dataset.py b8e8b05e…` 가 **21:58 과 한 글자도 다르지 않음**을 확인했다.

## 2. 백업 아카이브 `_archive/backups_260920/` — **205개 옮김**

### 2-1. 실제 개수를 셌다 (지시서의 «195개» 와 다르다)

| 폴더 | `_backup_*` 개수 | 처리 |
|---|---:|---|
| `app/` | 93 | 옮김 (cnt4·cnt4b 7개 제외) |
| `app/static/` | 107 | 옮김 (cnt4·cnt4b 7개 제외) |
| `app/static/help/` | 12 | 옮김 (cnt4·cnt4b 10개 제외) |
| `app/__pycache__/` | 3 | 옮김 (cnt4 1개 제외) |
| `export/` | 14 | 옮김 (cnt4 1개 제외) |
| `scripts/` | 3 | 옮김 (cnt4·cnt4b 2개 제외) |
| **합계** | **232** | **205 옮김 · 27 남김** |
| (그 뒤 카운팅 5 가 새로 만든 것) | +7 | 남김 — 지금 `app/`·`export/`·`scripts/` 에 **34개** |

지시서의 «195개» 는 `app/` + `app/static/` 만 센 값(=200, 그 뒤 카운팅 사이클이 몇 개 더 늘렸다).
`app/static/help/`·`__pycache__`·`export/`·`scripts/` 를 합쳐 **232개**가 실제 숫자다.
태그는 **48종**(`260916` ~ `260919_cnt1c`) — 어느 사이클이 남긴 것인지 `INDEX.md` 에 표로.

### 2-2. 옮기기 전 grep — 실제 코드는 `_backup_` 을 **한 군데도** 안 읽는다

`app/{server,boxes,instances,dupes,maskio}.py` · `app/run.sh` · `app/static/{app.js,ui.js,index.html,
help.html,style.css}` · `export/*.py` · `scripts/*.py` 를 전부 `grep '_backup_'` 했다.
걸린 것은 `server.py` 의 세 줄인데 **`_status_backup_<시각>.json`** — 이름만 비슷한 **다른 것**
(서버가 `data/` 에 만드는 status 백업)이다. 그래서 «코드가 참조하는 백업» 은 **0건**.

### 2-3. 그런데 «시험» 은 읽는다 → 두 세대(27개)는 남겼다

사이클 시험 스크립트 13개가 `T/app/_backup_*` 을 «옛 서버 재현용» 으로 읽는다
(`lib_c4.py`·`lib_cnt4.py`·`lib_cnt4b.py`·`t3_chars*.py`·`ab_revert.py`·`c1_fix.py`·`s6_drag.py` …).
그중 **2026-09-19 22:00 현재 돌고 있는** 「상자+개수 세기」 사이클이 읽는 것은
`_backup_260919_cnt4_*` 와 `_backup_260919_cnt4b_*` 두 세대다. 그것들만 원래 자리에 남겼다.

| 읽는 곳 | 읽는 파일 |
|---|---|
| `cycles/260919_count/cycle_4/stage2/lib_cnt4b.py` (`PREFIX="_backup_260919_cnt4_"`) | `app/_backup_260919_cnt4_{server,boxes,instances}.py` · `export/_backup_260919_cnt4_export_dataset.py` |
| 같은 폴더 `b3_chars.py` | `app/static/_backup_260919_cnt4_{app.js,ui.js,index.html,help.html,style.css}` |

**남긴 27개 목록** (INDEX.md §«남겨 둔 것» 에도 있다):
`app/` 6 + `app/__pycache__/` 1 + `app/static/` 7 + `app/static/help/` 10 + `export/` 1 + `scripts/` 2.
23:20 에 다시 세니 **34개** — 카운팅 사이클 5 가 작업 중에 `_backup_260919_cnt5_*` 5개와
`_backup_260919_cnt5b_*` 2개(`app/boxes.py`·`static/ui.js`)를 더 만들었다.

⚠ **작업 중 새로 생긴 것 5개**: 22:05~22:09 사이에 카운팅 사이클 5 가
`app/_backup_260919_cnt5_{README.md,boxes.py}` · `app/static/_backup_260919_cnt5_{app.js,ui.js,help.html}`
를 만들었다. 즉 그 사이클이 `boxes.py`(22:05) · `app.js`(22:07) · `ui.js`(22:04) · `help.html`(22:09) 를
**실제로 소수정했다.** → 기준선은 그 소수정 **뒤**(22:26·22:40)에 떴으므로 지금 판을 담고 있다.
(사이클 5 가 더 고치면 `--rebaseline` 한 줄로 다시 뜬다.)

### 2-4. 옮기지 않은 폴더 (범위 밖 — INDEX.md 에도 사유 적음)

`final/` 17개(논문 데이터절 초안·민감도 보고서·`protocol_splits_v4_reviewed/*.csv`·`manifest.json` —
툴 코드가 아니고 태그 `260916_peach`·`260916_grape`·`260917_c4_grape`·`260917_c5_*` 가 사이클
스크립트에서 이름으로 불린다) · `inspect/` 10 · `site/` 5 · `ai_pass/` 1 · 툴 폴더 맨 위 문서 백업 3 ·
`data/grape/` 1(**공용 `data/` 쓰기 금지**) · `cycles/**` 수천(모래상자 사본 — 손대면 재현이 깨진다).

### 2-5. 옮긴 뒤 확인

```
app/      README.md  __pycache__  boxes.py  cache  dupes.py  instances.py  logs
          maskio.py  run.sh  server.py  static     (+ cnt4·cnt4b·cnt5 백업만)
app/static/  app.js  help  help.html  index.html  style.css  ui.js   (+ 위와 같은 백업만)
export/   __pycache__  export_dataset.py  make_delete_script.py      (+ cnt4 1개)
scripts/  __pycache__  ff.py  make_grape_instances.py  make_help_figs_260917.py  (+ cnt4·cnt4b)
```

`py_compile` 7파일 OK · `node --check app.js·ui.js` OK · `bash -n run.sh` OK ·
모래상자 기동 OK · 실서버 `login=200`.

### 2-6. 🔴 이 이동으로 **죽는 정본 시험 45개** (총괄 지시로 목록화 — 23:00 실측)

지난 사이클 시험들이 «옛 판 서버» 를 재현하려고 `T/app/_backup_<태그>_server.py` 같은 파일을
**직접 연다.** 옮겼으니 지금 `FileNotFoundError` 로 죽는다. 원본은 **손대지 않았다**(사이클 기록).
`grep -rn '_backup_' cycles tests` 를 사이클 폴더 153곳에 돌려(모래상자 사본 제외) 123줄 ·
참조 스크립트 **63개**를 찾았고, 그중 **옮긴 태그를 쓰는 45개**가 죽는다.

| 사이클 | 죽는 스크립트 | 쓰는 태그 |
|---|---|---|
| `260917_ui` | `cycle_2/stage1/help_shots.py` · `cycle_3/stage1/t_ab.py` | `ui3`·`ui5` |
| `260917_신기능` | `cycle_2/stage1/ev_peach.py` · `cycle_2/stage1_server/parity_instances.py` · `cycle_4/stage1/boxes_parity.py` · `cycle_4/stage2/parity2.py` · `cycle_6_n6/stage2/readrule_diff.py` | `c2`·`c2c`·`c4`·`c5c` |
| `260918_paint` cycle_2 | `stage1/t4_paint8.py` · `stage2/{lib_s2.py,s4_paint8.py,fix_260918_c2b.py}` · **`stage2b/{lib_c2c.py,fix_260918_c2c.py}`** | `c2`·`c2b`·`c2c` |
| `260918_paint` cycle_3 | `stage1/{lib_c3.py,fix_260918_c3.py,fix_260918_c3_docs.py}` · `stage2/{lib_c3b.py,a7_equiv.py,fix_260918_c3b.py}` · `stage2c/{lib_c3c.py,fix_260918_c3c.py}` | `c3`·`c3b`·`c3c` |
| `260918_paint` cycle_4 | **`stage1/lib_c4.py`** · `stage1/{t3_chars.py,fix_expect_c4.py}` · `stage2/{lib_s2c4.py,s6_drag.py}` · `stage2c/lib_s2c4c.py` | `c4`·`c4b` |
| `260918_paint` cycle_5 | `stage1/lib_c5.py` · `stage2/lib_c5b.py` · `stage2c/{lib_c5c.py,r4_zero.py}` | `c4`·`c5c` |
| `260918_paint` (맨 위) | `stage2/{s5_fix.py,s5_fix_recheck.py}` | `paint2` |
| `260919_count` cycle_1 | `stage1/{ab_revert.py,t3_chars_cnt1.py}` · `stage2/{lib_c1b.py,a4_perf.py,a5_fixed.py,t3_chars_cnt1b.py}` · `stage2c/{lib_c1c.py,c1_fix.py,t3_chars_cnt1c.py}` | `cnt1`·`cnt1b`·`cnt1c`·`c4` |
| `cycle_5` (0916 판) | `stage1/scripts/{add_cycle5_section.py,fix_stale.py,fix_worklog.py}` | `c5` |

**살아 있는 8개**(`cnt4`·`cnt4b` 만 쓰므로 — 그래서 그 두 세대를 남겼다):
`260919_count/cycle_4/stage1/{lib_cnt4.py,b3_chars.py,b5_oldserver.py,regen_figs.sh}` ·
`.../stage2/{lib_cnt4b.py,b3_chars.py,b5_oldserver.py}` · `260917_ab/.../extra_checks.py`(`r3` 태그는 안 옮겼다) ·
`cycles/cycle_1/stage2/scripts/s2_recheck.py`(`260916_peach·grape` 태그 = `final/`·`data/` 에 있고 안 옮겼다).

**굵게 표시한 세 파일이 핵심이다** — `lib_c2c.py`·`lib_c4.py` 같은 **각 사이클의 `lib_*.py` 한 개**가
복사를 맡고 있어서, 그 한 파일만 고치면 그 사이클 전체(`s1_api`·`s5`·`s8`·`t4_paint8` …)가 산다.
되살리는 세 가지 방법을 `INDEX.md` 끝에 적어 두었다(① `tests/` 판을 쓴다 ② `cp -a` 로 잠깐 되돌린다
③ 그 `lib_*.py` 에 폴백 한 줄).

### 2-7. `tests/` 판은 폴백으로 **산다** (md5 로 증명)

`tests/lib/sandbox.py` 의 `backup_src(sub, name)` 이 «원래 자리 → 없으면
`_archive/backups_260920/<원래 상대경로>`» 순으로 찾는다. 실측:

```
app      server.py         -> _archive/backups_260920/app/_backup_260918_c4_server.py
app      boxes.py          -> _archive/backups_260920/app/_backup_260918_c4_boxes.py
app      instances.py      -> _archive/backups_260920/app/_backup_260918_c4_instances.py
export   export_dataset.py -> _archive/backups_260920/export/_backup_260918_c4_export_dataset.py
```

`tests/browser/t2_ui.py` 의 [라] 묶음이 그 길로 **옛 판 서버를 실제로 띄워** 통과했다
(라-1~라-4 · `sb_old/app/server.py` md5 `221b5527…` = 아카이브 파일과 **같고** 지금 판 `dfde8c1b…` 와 **다르다**).
이 폴백이 지워지지 않게 **`tests/unit/u4_archive_fallback.py` (7항목)** 를 새로 만들어 못박았다.

## 3. `T/tests/` — 구조도

```
tests/
  run_all.sh          ← 한 줄 명령. --browser · --rebaseline · --check-baseline · --no-merged · --only=
  README.md           ← 무엇을 어떻게 돌리나 · 기준선 뜻 · 다시 뜨는 때 · 안 덮는 것
  ORIGIN.md           ← 어느 사이클 어느 파일에서 복사해 왔나 · 안 가져온 것과 이유 · 고친 기대값 2곳
  lib/
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    paths.js             node 시뮬이 쓰는 app.js·ui.js 경로
  unit/     u1_boxes_selftest.py (5) · u2_maskio.py (10) · u3_instances_u16.py (10)
            u4_archive_fallback.py (7)  ← 아카이브 폴백이 살아 있나 (§2-7)
  sim/      sim.js · boxsim.js (50) · modesim.js (31) + 녹취 응답 json 5개
  api/      t1_api.py (34) · regress_all.py (100)
  browser/  b1_browser.py (81) · t2_ui.py (27)        ← --browser 일 때만
  merged/   run_merged.sh   ← tests_merged_260918 을 **격리 사본**에서 호출 (536)
  baseline/ snapshot.py  ← --rebaseline / --check / --restems / --refreeze-status
  fixtures/
    stems.txt              고정 표본 12장 (과일마다 이름 오름차순 첫 3장)
    status_260920/         그 12장 몫의 status.json·duplicates.json 을 **얼린 것**(8파일)
    baseline_260920/       기준선 (api/*.json 100 · api_sha256.txt · exports.json · bundles.json
                                   · code_sha256.json · stems.json · README.md)
  _sandbox/   ← 스스로 만든다. 지워도 된다 (sb_main · sb_reg · sb_base · sb_old · dataset_sample · merged)
  _out/       ← 로그·중간 json. 지워도 된다
```

### 3-1. 모래상자를 스스로 만든다

- `sb_main`·`sb_reg`·`sb_base` 는 `app`+`export`+`data` **실복사**(각 102MB · rsync · 하드링크 0).
- `dataset_sample/` 은 고정 표본 12장만 담은 작은 «원본 폴더»(39MB · 실복사).
- 서버는 `free_port()` 가 **빈 포트**를 고른다(5401~·5501~·5601~). **`KEEP_OUT = {5100,5101,5102,
  5104,5105,5111}`** 로 실서버·교수님·주피터 포트는 아예 목록에서 뺐고, 이미 쓰이는 포트면 **멈춘다.**
- 끝나면 `p.terminate()` 로 **내가 띄운 PID 만** 끈다. `pkill` 을 쓰지 않는다.
- 스크린샷은 `~/ff_shots/tests_260920/` 에만(이번에 **14장**).

### 3-2. 통합 시험(`tests_merged_260918`)을 «사본에서» 부르는 이유 — 실측 근거

원본 시험들은 자기 폴더 안 `sandbox/` 에 쓴다. 2026-09-19 21:32 에 그 폴더가 고쳐지고 있었다
(`counts/sandbox` mtime 21:32 · `stage5/sandbox_m5c` 20:57) — **카운팅 사이클 5 가 같은 폴더에서
같은 시험을 돌리고 있었다.** 거기서 내가 또 돌리면 서로 덮어쓴다. 그래서
`run_merged.sh` 가 돌릴 때마다 원본을 **읽어** `tests/_sandbox/merged/` 로 rsync 하고(모래상자·로그 제외),
`tools/*.py` 를 심볼릭 링크로 걸어 `TOOLS = dirname(HERE)` 가 맞게 한다.
**원본 시험 파일은 한 글자도 고치지 않았다**(지시대로 «그대로 두고 호출만»).
통과하면 사본의 모래상자를 치운다(한 번에 약 5.6GB 가 쌓이므로) — 실패하면 봐야 하니 남긴다.

## 4. `run_all.sh` 결과 표 (실측)

### 4-0. 최종 실행 — `--rebaseline` (23:04:07 → 23:11:43) 과 `--check-baseline` (23:12 → 23:17)

```
bash tests/run_all.sh --browser --rebaseline      # 890/1 · 455초
bash tests/run_all.sh --check-baseline            # 782/1 · 299초 · 기준선 ①②③④ 다른 칸 0개
```

| 묶음 | 통과 | 실패 | 초 | rc |
|---|---:|---:|---:|---:|
| syntax/py_compile (8파일) | – | – | 0 | 0 |
| syntax/node_app.js | – | – | 0 | 0 |
| syntax/node_ui.js | – | – | 0 | 0 |
| syntax/bash_run.sh | – | – | 0 | 0 |
| unit/u1_boxes_selftest | 5 | 0 | 1 | 0 |
| unit/u2_maskio | 10 | 0 | 0 | 0 |
| unit/u3_instances_u16 | 10 | 0 | 1 | 0 |
| unit/u4_archive_fallback | 7 | 0 | 1 | 0 |
| sim/boxsim | 50 | 0 | 0 | 0 |
| sim/modesim | 31 | 0 | 0 | 0 |
| sim/sim | – | – | 0 | 0 |
| api/t1_api | 34 | 0 | 6 | 0 |
| api/regress_all | 100 | 0 | 8 | 0 |
| **merged/tests_merged_260918** | **535** | **1** | 268 | **1** |
| browser/prep_sandbox | – | – | 1 | 0 |
| browser/b1_browser | 81 | 0 | 60 | 0 |
| browser/t2_ui | 27 | 0 | 96 | 0 |
| baseline/rebaseline | – | – | 13 | 0 |
| **합계** | **890** | **1** | **455** | **1** |

통합 시험 안쪽(268초): `test_build_merged.py` 68/0·71초 · **`stage2/test_fixes_m2.py` 12/1·111초** ·
`stage3/test_fixes_m3.py` 20/0·31초 · `stage4/test_confirm_kinds.py` 200/0·14초 ·
`stage5/test_spec.py` 106/0·28초 · `stage5/test_fix_m5c.py` 67/0·7초 · `counts/test_counts.py` 62/0·5초.

`--browser` 없이는 **299초** · `--no-merged` 를 더하면 **약 30초**.

### 4-0b. 전체 통과 실행 (22:40:37 → 22:48:11 · 팀원이 복숭아를 확정하기 **전**)

같은 명령에서 **884 통과 / 0 실패 · rc 0 · 454초** · 기준선 ①②③ 다른 칸 0개.
(그 뒤 `unit/u4` 7항목이 늘어 890 이 되었고, `merged` 하나가 실패로 돌았다.)

### 4-2. 🔴 남은 실패 1건의 원인 — 팀원이 복숭아 한 장을 확정했다 (내 작업 탓이 아니다)

- **실패 단정**: `tests_merged_260918/stage2/test_fixes_m2.py` 의
  `check("F7-c 복숭아 상자 줄 수가 늘었다(973 → 977)", allt == 977)` → 지금 **975줄**.
- **원인(실측)**: `T/data/peach/status.json` 의 `210629-t2-of13-03` 에
  `"confirmed": {"at": "2026-09-19 22:55:23", "by": "익명", "status": "flag"}` 가 생겼다.
  사람이 «문제 있음» 으로 확정한 사진은 내보내기·통합빌드가 **뺀다**(`export_dataset.py` E5).
  그 사진의 상자 **2줄**이 빠져 977 → 975 가 됐다.
- **내가 아님을 증명**: 그 기록의 `by` 는 «익명»(웹에서 누른 사람) · 실서버 로그에 같은 시각
  112.149.154.206 요청 · 내 시험이 쓰는 이름(`기준선`·`곽동신`)은 네 `status.json` 어디에도 없다 ·
  22:08 에 카운팅 5 가 `build_merged_dataset.py` 를 고쳤지만 **22:40 실행은 그 뒤인데도 977 로 통과**했다.
- **성격**: `F7-c` 가 «977» 을 **손으로 적어 둔** 단정이고, 그 수가 **공용 팀 자료**에 매달려 있다.
  즉 그 시험은 **밀폐(hermetic)되어 있지 않다.** 팀원이 라벨을 고치면 언제든 또 깨진다.
- **내가 하지 않은 것**: 그 시험을 고치지 않았다(지시: «그대로 두고 호출만»).
  고칠 사람은 통합 데이터셋 담당이고, 고치는 방향은 «977 을 적지 말고 **직전 빌드에서 세어** 견주기» 다.
- **그 사이 쓸 명령**: 구조 사이클 2 의 «동작 무변경» 관문은 밀폐된 묶음만 보면 된다 —
  `bash tests/run_all.sh --no-merged --only=syntax,unit,sim,api` (약 30초, 전부 통과) +
  `bash tests/run_all.sh --check-baseline` 의 ①②③ «다른 칸 0개».
- **기준선 ③ 을 어떻게 뒀나**: 통과 수는 `merged/` 만 **경고**로, 실패 수는 어느 묶음이든 **실패**로
  본다(`snapshot.py NOT_HERMETIC`). 지금 기준선은 «merged 535/1» 을 담고 있다 —
  **F7-c 가 고쳐지면 536/0 으로 다시 떠야 한다.**

### 4-3. 돌려 보고 잡은 «낡은 기대값» 2곳 (코드는 안 고쳤다)

시험을 그냥 복사만 하고 돌려 보지 않았으면 못 잡았을 것이다. 자세한 것은 `tests/ORIGIN.md` §기대값.

1. **`b1_browser.py` 포도 초벌 출처** — 처음 가져온 stage1(19:36) 판은 `certh_gt` 를 기대하는데
   지금 코드는 `cc4` 다. `app/instances.py` 의 `SEED_DIRS` 에서 **포도가 주석으로 꺼져 있다**
   («교수님 확인 8번 뒤에 되살릴 줄»). 실패 3건. → 그 사이클 **2차 판(stage2 21:01)**
   이 이미 `GRAPE_ON = False` 로 고쳐 둔 것을 가져오고, 한 걸음 더 나가
   **`GRAPE_ON = L.grape_seeded()`** — `SEED_DIRS` 를 **읽어서** 정하게 했다.
   포도를 켜는 날 시험을 손대지 않아도 기대값이 따라간다. → **81/0**.
2. **`t2_ui.py` 나-1** — 0918 판은 «**AI 초벌** 번호 … 맞으면 Enter» 를 요구하는데 0919 사이클이
   그 낱말을 **출처 이름**으로 바꿨다(지금 문구 «원본 정답 번호 1개 — 맞으면 Enter»).
   → «번호 + 출처 낱말 하나(초벌·정답·박성문·고친·4-연결) + Enter» 로 고쳤다. → **27/0**.

## 5. 기준선 `tests/fixtures/baseline_260920/`

### 5-1. 담은 것 (243항목)

| | 무엇 | 개수 | 다르면 |
|---|---|---:|---|
| ① | 고정 표본 API 응답 JSON — **변하는 칸을 지운 뒤** + `api_sha256.txt` | **100** | 실패 |
| ② | 모래상자 내보내기 산출 파일 지문 | **99** | 실패 |
| ③ | 회귀 묶음별 통과/실패 수 | **14** | 실패(단, `merged/` 통과 수는 경고 — §4-2) |
| ④ | 정적 파일·서버 코드 sha256 | **30** | **경고만**(리팩터가 하는 일) |

① 부른 주소(**50개를 두 번** — 손대기 «전» `api_*` 과 확정을 만든 «뒤» `api2_*`):
`/api/fruits` · `/api/export_list` · 과일마다 `/api/list?page_size=120&page=1` ·
`/api/export_plan?confirmed_only=1` 과 `=0` · 표본 12장마다 `/api/item` · `/api/boxes`(GET) ·
`/api/instance_info`. (2 + 4×3 + 12×3 = 50) × 2 = **100**

② 네 과일 × `kinds=[mask,instances,boxes,counts]` · **`confirmed_only=false` = «AI 제안 포함»**
\+ 사과는 `confirmed_only=true` = «사람 확정만» 갈래도 한 벌.
실제로 나온 것: `images/` `masks/` `instances/` `boxes/*.txt` `boxes/boxes_all.json`
`counts.csv` `manifest.csv` `job.json` — 사과 10 · 블루베리 16 · 포도 13 · 복숭아 16 ·
사과(사람 확정만) 9 + 상태칸 7×5 = **99**.

③ `syntax`·`unit`·`sim`·`api`·`merged` 14줄. **`browser/`·`baseline/` 줄은 일부러 넣지 않았다** —
`--browser` 를 주느냐에 따라 기준선이 달라지면 안 되기 때문.

### 5-1b. 🔴 «확정» 이 기준선에 하나도 없던 것을 실측으로 잡아 메웠다

처음 뜬 기준선(50 + 83)을 검사해 보니 표본 12장 전부 `confirmed`·`confirmed_boxes`·
`confirmed_instances` 가 **모두 `None`** 이었다. 이유는 **공용 `data/status.json` 네 개에
`confirmed_*` 기록이 한 건도 없기 때문**이다(확정 기능이 새것이라 아직 아무도 안 썼다 — 실측).
그대로 두면 「상자+개수 세기」 사이클이 만든 **확정 규칙 전체가 기준선 밖**에 있었다.

메운 방법: JSON 을 손으로 지어내지 않고 **서버에게 시켰다.** `snapshot.py take()` 순서를
① → 상자 저장 → `/api/status` 확정 → `①b` → ② 로 바꿨다.

| 단계 | 무엇 |
|---|---|
| ① `api_*` | 얼린 자료 그대로(확정 0건) — «아무것도 안 한 상태» 의 응답 |
| 상자 저장 | 표본 12장에 **고정 상자 2개씩**(사진 크기의 고정 비율이라 늘 같은 좌표) |
| 확정 | 과일마다 3장에 한 종류씩 — `mask=ok`(1장) · `boxes=fixed`(저장이 자동 확정) · `instances=ok`(1장). **12건 전부 200** |
| ①b `api2_*` | 그 뒤의 응답 50개 |
| ② | 내보내기 — 이제 `boxes/*.txt` 12장과 «사람 확정만» 갈래까지 나온다 |

확인: `api2_item__*` **12/12** 가 확정 값을 담았다 —
`(confirmed, confirmed_boxes, confirmed_instances)` 가 과일마다
`('ok','fixed',None)` · `(None,'fixed',None)` · `(None,'fixed','ok')`.
즉 «한 종류를 확정해도 다른 종류는 그대로» 라는 규칙이 응답에 박혔다.
① 50→**100** · ② 83→**99**. 다시 떠서 대조 → ①②③④ 전부 «다른 칸 0개».

### 5-2. 표본을 «고정» 한 두 가지 장치 (이게 핵심이다)

1. **표본 데이터셋** `_sandbox/dataset_sample/` — 12장만. 네 과일 전부 만들어서
   `dupes.dataset_for()` 가 이 폴더 하나만 보게 했다. 덕분에 내보내기가 4,071장이 아니라 12장 →
   **기준선 한 번이 10초**(네 과일 전체면 수 분·수 GB).
2. **얼린 판정 자료** `fixtures/status_260920/` — 그 12장 몫의 `status.json`·`duplicates.json` 만
   떼어 `fixtures/` 에 굳혔다. 공용 `data/status.json` 을 그대로 쓰면 **사람이 실서버에서 라벨을
   고칠 때마다 기준선이 흔들린다.** 얼렸으므로 기준선은 **코드만의 함수**다.

② 가 상자 YOLO txt 까지 덮게, ① 을 **먼저 뜬 뒤** 표본 12장에 **고정 상자 2개씩**을 저장한다
(좌표가 사진 크기의 고정 비율이라 늘 같다). 그 전에는 `n_boxes=0` 이라 txt 가 한 장도 안 나왔다.

### 5-3. 지운 «변하는 칸» (실측으로 찾았다)

첫 판을 뜨고 바로 대조했을 때 **2칸이 흔들렸다** —
`grape/boxes/boxes_all.json` · `peach/boxes/boxes_all.json`. 안을 열어 보니 `"at": "2026-09-19 22:12:32"`.
그래서 규칙을 이렇게 굳혔다.

| 종류 | 어떻게 |
|---|---|
| **이름으로** 지우는 칸 | `at · by · started · finished · mtime · ts · time · now · pid · elapsed · sec(s) · seconds · took · job · out · dir · data_root · port · sig · generated · updated · created · date · when · host · url · path · outdir · log · version · build · uptime · started_at · finished_at · counted_at` → 값을 `⟨지움⟩` 으로 (**칸 자체는 남긴다** — 칸이 사라지면 잡히게) |
| **값으로** 지우는 칸 | `2026-09-19 22:00` 꼴 · `260919_220945` 꼴(내보내기 폴더 이름) · `22:00:00` 꼴 · `/data/project/` · `/home/` 으로 시작하는 절대경로 |
| 내보내기 `*.json` | 그냥 sha256 을 뜨지 않고 **위 규칙으로 지운 뒤** 지문을 뜬다 (`boxes_all.json` 의 `at`, `job.json` 의 시각·폴더 이름) |
| 내보내기 `*.csv` (`manifest.csv`·`counts.csv`) | 머리글이 `…at·time·date·mtime·when·job·dir·out·path·by` 로 끝나는 **칸을 빼고** 남은 칸만 이어 붙여 지문 |

**안정성 확인**: `--rebaseline` 뒤 `--check` 를 **세 번**(22:13·22:14·22:26) 돌려 ①②④ 모두 «다른 칸 0개».
마지막 전체 실행(22:48)에서도 ①②③④ 전부 0개.

## 6. 기준선이 덮지 못하는 길 — 스스로 아는 것 (2차가 공격할 자리)

| 안 덮는 것 | 왜 | 지금 무엇이 대신 보나 |
|---|---|---|
| 고정 표본 **12장 밖의 4,059장** | 다 내보내면 수 분·수 GB | `api` 묶음이 네 과일 **전체** 목록·큐·확정·내보내기 계획을 본다(단, 바이트 동일은 아님) |
| 사과 **2장이 통째로 빠진 것** — 표본 3장 중 1장만 나갔다(`__n_dropped=2`) | 그 2장이 중복·제외 판정이라 정상 동작이다. 그래도 «나가는 쪽» 표본이 1장뿐 | `regress_all` 이 사과 확정·내보내기를 따로 본다 |
| **포도 번호본**(`certh_gt`) 경로 | `SEED_DIRS` 에 포도가 꺼져 있어 지금은 `cc4` 만 지난다 | 없음. 교수님이 켜는 날 `--rebaseline` 이 필요하다(`L.grape_seeded()` 가 시험 기대값은 따라간다) |
| **두 사람이 같은 사진을 동시에** 저장 (0919 Codex 지적: 옛 화면 저장이 남의 번호를 지운다) | 기준선은 한 요청씩만 본다 | **아무것도 안 본다 — 미결** |
| 마스크 «확정» 뒤 번호 저장이 이진본을 바꾸는 N6 주변 | 표본 12장에 그 상태를 만들어 두지 않았다 | `api` 묶음의 마스크 저장·되돌리기(`regress_all` ④⑤) |
| `api_revert_instances` 가 브러시 전용 수정본까지 지우는 문제(Codex 지적 ②) | 표본에 그 상태가 없다 | `regress_all` 의 «되돌리기» 칸은 정상 경로만 본다 |
| 상자 «전부 탈락» 과 «빈 목록» 구별(Codex 지적 ④) | 서버 응답 칸 이름만 비교한다 | `unit/u1-3` 이 `clean([])` 만 못박는다 |
| 그리기·확대·붓·Ctrl+Z 같은 **화면 손놀림** | JSON 으로 잴 수 없다 | `sim` 묶음(함수 단위 81항목) + `--browser`(108항목) |
| `app/static/help/*.png` 다시 만들기 | 그리는 스크립트가 실서비스 그림을 덮어쓴다(사이클3 2차 확인) | 일부러 안 돌린다 |
| 실서버 `data/status.json`(사람이 쌓은 판정) | 일부러 얼렸다 | **안 본다 — 이건 «자료» 이고 코드 동작이 아니다** |
| 성능(느려졌는지) | 표의 «초» 칸만 적는다 | 사람이 본다. 합격 기준이 아니다 |
| `app/cache/thumbs` 썸네일 · `logs/` | 다시 만들어지는 것 | 안 본다 |
| **`merged` 묶음 자체가 밀폐되어 있지 않다** | 공용 `data/*/status.json` 을 읽어 «977줄» 같은 수를 손으로 적어 둔 단정이 있다(§4-2) | 없음. 그 시험의 주인이 «직전 빌드에서 세어 견주기» 로 고쳐야 한다 |
| 근접 중복 «묶음 확정» · `masks_fixed` 2장 이상 · `instances_fixed` · 판정 `flag` | 표본 12장에 그 상태가 없다(실측 §8-2) | `api/regress_all` 이 실제 자료로 본다(바이트 동일은 아님) |
| `make_delete_script.py`·`make_grape_instances.py`·`make_help_figs_260917.py` | 한 번 쓰는 도구 | `py_compile` 만 |
| `dupes.py`·`instances.py` 의 **캐시 무효화**(`sig_of`·`stale_stems`) | 표본이 작아 캐시가 늘 새것 | 안 본다 |

## 7. 2차(검수)가 그대로 재현하는 명령

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴

# ① 전부 한 번에 (브라우저 포함 · 약 455초) + 기준선 대조
#    ⚠ 지금은 rc=1 로 끝난다 — 통합 시험 F7-c 하나 때문이고 원인은 §4-2 에 있다
bash $T/tests/run_all.sh --browser --check-baseline ; echo "rc=$?"

# ②-A 밀폐된 묶음만 (약 30초 · **전부 통과해야 한다**) ← 구조 사이클 2·3 의 관문으로 이것을 쓴다
bash $T/tests/run_all.sh --no-merged --only=syntax,unit,sim,api ; echo "rc=$?"

# ②-B 아카이브 폴백이 살아 있나 (1초)
bash $T/tests/run_all.sh --only=unit

# ③ 기준선을 다시 떠서 «두 번 떠도 같은가» 를 확인 (카운팅 사이클 5 소수정 뒤에도 이것)
bash $T/tests/run_all.sh --rebaseline && bash $T/tests/run_all.sh --check-baseline

# ④ 기준선만 (run_all 없이 · 약 10초씩)
PYTHONPATH=$T/tests/lib /home/kds0206/.conda/envs/kwak/bin/python $T/tests/baseline/snapshot.py --rebaseline
PYTHONPATH=$T/tests/lib /home/kds0206/.conda/envs/kwak/bin/python $T/tests/baseline/snapshot.py --check

# ⑤ 스냅샷이 맞는지
cd $T/_archive/pre_refactor_260920 && \
  sha256sum -c <(awk 'NF==3 && $3 ~ /^(app|export|scripts)\//{print $1"  "$3}' MANIFEST.txt) | tail -3

# ⑥ 옮긴 백업 개수·남긴 것
find $T/_archive/backups_260920 -type f -name '_backup_*' | wc -l          # 205
find $T/app $T/export $T/scripts -name '_backup_*' -type f | sort          # 남긴 것(cnt4·cnt4b + 사이클5가 새로 만든 cnt5)

# ⑥-b 아카이브 이동으로 죽는 정본 시험 45개를 다시 세기 (§2-6)
#      (사이클 폴더가 커서 모래상자 사본은 건너뛴다 — 아래는 목록만 다시 뽑는 얼개)
grep -rn '_backup_' $T/tests/lib/sandbox.py | head -3        # 폴백이 여기 있다

# ⑦ 실제 코드가 백업을 참조하지 않는지 다시 확인
for f in $T/app/server.py $T/app/boxes.py $T/app/instances.py $T/app/dupes.py $T/app/maskio.py \
         $T/app/run.sh $T/app/static/app.js $T/app/static/ui.js $T/app/static/index.html \
         $T/app/static/help.html $T/app/static/style.css $T/export/*.py $T/scripts/*.py; do
  grep -Hn '_backup_' "$f"; done        # `_status_backup_` 세 줄(server.py)만 나와야 한다

# ⑧ 실서버를 안 건드렸는지
ps -o pid,etime,cmd -p 964494 ; curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5111/login
ls -la --time-style=full-iso $T/data/*/status.json        # MANIFEST.txt 끝의 mtime 과 같아야 한다
```

## 8. 2차 검수에게 — 공격할 자리를 먼저 적어 둔다

1. **§6 표가 정직한가.** 덮지 못하는 길을 더 찾아라. 특히 «① API 50개» 가 정말 서버의 주요 주소를
   다 지나는가(`/api/save`·`/api/revert`·`/api/status`·`/api/export_start` 는 **GET 이 아니라서 ① 에 없다** —
   `api` 묶음이 대신 본다고 적었는데 그것으로 «바이트 동일» 이 증명되는가?).
2. **얼린 판정 자료가 표본을 «쉬운 것» 으로 만들지 않았나.** 1차가 이미 재 봤다(§5-1b) —
   확정은 0건이어서 `api2_*` 를 만들어 메웠지만 **아직 비어 있는 것이 남았다**:
   `masks_fixed` **1장뿐**(복숭아 `210629-t1-01`) · `instances_fixed` **0장** · 근접 중복 묶음 **0개** ·
   `status` 기록 자체가 없는 장 5개(포도 3 · 블루베리 2) · 판정 종류는 `fixed`·`ok`·`exclude`·
   `unreviewed` 만 있고 **`flag` 가 없다**. 이 다섯 구멍을 어떻게 메울지(또는 못 메운다고 적을지) 판정해 달라.
3. **`⟨지움⟩` 규칙이 너무 넓다.** 이름이 `path`·`url`·`version`·`date` 인 칸을 통째로 지웠다 —
   그 칸에 **뜻 있는 값**이 들어 있으면 리팩터가 그것을 깨도 잡히지 않는다. 실제로 몇 칸이 지워졌는지 세어라.
4. **`merged` 묶음의 격리 사본이 원본과 같은 것을 재는가.** 심볼릭 링크로 `tools/*.py` 를 걸었으므로
   `__file__` 이 사본 쪽을 가리킨다. 그 때문에 결과가 달라지는 시험이 있는지.
5. **기준선 ③(묶음 통과/실패 수)** 은 `-` 를 문자열로 담고 있다. 시험을 하나 **추가**하면 ③ 이 달라져
   «실패» 가 된다 — 그게 맞는 설계인가, 아니면 «줄어들 때만» 실패여야 하나.
6. **남긴 27+5개 백업.** 구조 사이클 2 가 카운팅 사이클 5 가 끝났는지 어떻게 안다고 적었나
   (INDEX.md 의 한 줄 명령이 정말 안전한가).
7. **`tests/_sandbox` 가 449MB 남는다.** 통합 시험이 통과하면 치우지만 `sb_*` 3개(306MB)는 남는다.
   `--clean` 플래그가 없다 — 있어야 하나.

## 9. 다음 사람이 반드시 할 것 (순서)

1. 🔴 **카운팅 사이클 5 의 3차(판정)가 끝나면 기준선을 다시 뜬다.** 한 줄이다:
   `bash tests/run_all.sh --rebaseline` (약 13초 + 묶음 시간).
   지금 기준선은 **23:11 디스크 판**이다 — 카운팅 5 **1차 소수정까지 반영**됐다
   (`ui.js` 22:04 · `boxes.py` 22:05 · `app.js` 22:07 · `help.html` 22:09 ·
   `build_merged_dataset.py` 22:08). 2차·3차가 더 고치면 그만큼 다시 떠야 한다.
   ⚠ **실서버(PID 964494)는 21:44 에 뜬 «카운팅 4 파이썬»** 을 메모리에 들고 있고 정적 파일만 새것을
   내보낸다 — 즉 «실서버 프로세스» 와 «디스크 코드» 가 지금 다르다. 기준선은 **디스크 코드** 기준이다.
   카운팅 4 판 그대로의 코드는 `_archive/pre_refactor_260920/` 에 남아 있다(21:58 판).
2. 🔴 **`stage2/test_fixes_m2.py F7-c` 를 통합 데이터셋 담당이 고친다**(§4-2). 고치면
   `--rebaseline` 로 ③ 을 «merged 536/0» 으로 되돌린다.
3. **남긴 백업 27+5개**(cnt4·cnt4b·cnt5)를 구조 사이클 2 가 같은 규칙으로 옮긴다
   (한 줄 명령은 `INDEX.md` §«남겨 둔 것»).
4. **죽는 정본 시험 45개**(§2-6)를 어떻게 할지 판정한다 — 되살릴지, 그대로 둘지.
5. `tests/browser/` 에 `b2_export`·`b4_fallback`·`b5_oldserver` 를 더한다(카운팅 5 가 끝난 뒤).

## 10. 못 한 것 (솔직히)

- `final/`·`inspect/`·`site/`·`ai_pass/` 의 `_backup_*` **34개는 옮기지 않았다**(§2-4 사유).
  지시서가 `final/` 을 이름으로 적었으므로 **2차가 판정해 달라.**
- `tests/browser/` 에 **`b2_export`·`b4_fallback`·`b5_oldserver` 를 못 가져왔다** — 22:00 현재
  다른 세션이 쥔 파일이라서(§ORIGIN.md). 구조 사이클 2 가 가져오면 브라우저 묶음이 두 배가 된다.
- `--clean` 플래그와 `tests/_sandbox` 자동 정리를 `merged` 묶음에만 넣었다.
- `app/README.md` 에 «백업은 `_archive/backups_260920/` 로 갔다» 는 한 줄을 **못 적었다** —
  그 파일을 카운팅 사이클 5 가 쥐고 있어서(22:00 기준 mtime 21:10). 사이클 4 의 README 재작성 몫.
- 기준선 ② 는 «AI 제안 포함» 네 과일 + «사람 확정만» **사과 한 과일**만 뜬다. 나머지 세 과일의
  «사람 확정만» 갈래는 `/api/export_plan`(①) 계획으로만 본다.
- **`merged` 묶음의 실패 1건을 못 없앴다**(§4-2). 남의 시험이고 고치지 말라는 지시가 있었다.
  그래서 `bash tests/run_all.sh` 는 **지금 rc=1** 로 끝난다. 밀폐된 묶음만 돌리는
  `--no-merged --only=syntax,unit,sim,api` 는 전부 통과한다.
- 표본 12장이 **중복 묶음 0 · `masks_fixed` 1장 · `instances_fixed` 0 · 판정 `flag` 0** 이다(§8-2).
  네 구멍을 어떻게 메울지 2차가 판정해 달라.
- `tests/_sandbox` 를 비우는 `--clean` 플래그를 넣지 않았다. 통합 시험 사본은 **통과하면** 스스로
  치우지만(통과 뒤 449MB) **실패하면 봐야 하니 남긴다** — 그래서 23:20 실측 `tests/` 는 **6.1GB** 다
  (그 안 `_sandbox/merged` 가 5.6GB). F7-c 가 고쳐지면 다음 실행에서 자동으로 449MB 로 줄어든다.
  지금 당장 치우려면:
  ```bash
  T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
  find $T/tests/_sandbox/merged/tests_merged_260918 -maxdepth 2 -type d \
       \( -name 'sandbox' -o -name 'sandbox_*' \) -exec rm -rf {} +
  ```
  (`tests/_sandbox` 와 `tests/_out` 은 통째로 지워도 다시 만들어진다.)
