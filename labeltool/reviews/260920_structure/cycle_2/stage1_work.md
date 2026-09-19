작성: 2026-09-20

# 구조 정리 5사이클 — 사이클 2 (서버 분리) 1차 작업

작업: Opus 5 · 시각은 전부 `date` 실측 · 시간 제한 없음
지시: `문서/260919_툴_구조정리_인수인계_5사이클_지시.md` §2·§4(사이클 2 행)·§5 ·
`cycles/260920_structure/cycle_1/stage3_final.md` §2 · `cycle_1/stage2_review.md` §10·§11
소유: `app/*.py` · 새 `app/core`·`app/api`·`app/domain` · `export/*.py` · `tests/`
**`app/static/**` 은 한 글자도 쓰지 않았다**(같은 시간에 구조 사이클 3 이 쪼개고 있다 — 읽기만 했다).

---

## 0. 한 장 요약

| 항목 | 값 |
|---|---|
| `app/server.py` | **2,052줄 → 93줄** (앱 만들기 + `register()` 호출 + `run.sh` 진입점) |
| 서버 파이썬 파일 | **5개 → 21개**(껍데기 4 + `server.py` + `core` 4 + `api` 8 + `domain` 4) |
| 줄 수 합계(app/*.py) | 3,432 → **3,924** (+492 · 늘어난 것은 머리말·규칙 함수 docstring) |
| 시작 관문(정본 · 00:39:57→00:46:58) | ①②③⑤ **0칸** · ④ 24칸(새 파일 — 참고) |
| 시험(격리 모래상자) | **991 통과 / 0 실패** (전: 833/1) · `merged` **536/0**(전 535/1) · 브라우저 108/0 |
| 주소(라우트) | **37/37 완전히 같다**(규칙·엔드포인트·메서드) |
| 실서버 | 5111 · PID **1467097**(00:04:44 기동) **건드리지 않았다**(전환은 사이클 5) |
| 새 시험 | `unit/u6_py_contract`(24) · `api/t3_login_rate`(7) · `api/t4_flag`(17) |

---

## 1. 시작 관문 (손대기 **전**)

```
00:39:57 → 00:46:58 · bash tests/run_all.sh --check-baseline   (정본 app/ · 리팩터 전 코드)
  ① API 응답 0칸 · ② 내보내기 지문 0칸 · ⑤ 라우트·쓰기 0칸 · ④ 코드지문 **0칸**
  ③ 4칸(경고) — 같은 시간에 이 명령이 두 번 겹쳐 `_out/bundles.tsv` 가 api 줄을 잃었다(§9-1)
  merged 535 / 1  ← 알려진 `F7-c` 하나뿐
```
**④ 가 0칸**이므로 기준선 = 디스크 = 실서버 코드였다(다른 세션이 코드를 고치지 않았다) → 작업 시작.
증거: `cycles/260920_structure/cycle_2/stage1/logs/`(이 폴더의 모든 로그는 실행 그대로다).

모래상자에서도 손대기 **전**에 한 번 돌려 같은 값을 확인했다(00:48:05→00:53:25 · `logs/sb_before_check.log`):
①②③④⑤ **전부 0칸** · 833 통과 / 1 실패.

---

## 2. 무엇을 어떻게 옮겼나 — **사람이 베껴 적지 않았다**

옮기기는 손으로 하지 않고 **도구 두 개**가 했다. 그래서 «옮기다 한 글자가 바뀌는» 일이 없다.

| 도구 | 하는 일 |
|---|---|
| `stage1/tools/blocks.py` | 원본 파일의 최상위 문장을 **앞 주석까지 붙여** 블록으로 자른다(ast) |
| `stage1/tools/compose.py` | 그 블록을 새 파일에 **글자 그대로** 붙인다. 바꾸는 것은 import 줄과 들여쓰기(라우트를 `register()` 안으로)뿐이고, 그 밖의 손질 **29건**을 표로 찍는다 |
| `stage1/tools/pass2_rules.py` | 주석에만 있던 규칙을 `domain/rules.py` 의 **이름 있는 함수**로, 매직 넘버에 이름을 붙인다(**44건**, 전부 표로 찍는다) |
| `stage1/tools/refcheck.py` | `py_compile` 이 못 잡는 «없는 이름»(NameError)을 ast+symtable 로 찾는다 → **17파일 0건** |
| `stage1/tools/routemap.py` | 서버를 띄우지 않고 주소표만 뽑는다 → 전/후 대조 |
| `stage1/tools/contract_probe.py` | 파이썬 공개 이름·상수값·주소표를 얼린다(→ `tests/fixtures/py_contract_260920.json`) |
| `stage1/tools/fill_rules_table.py` | 규칙표 초안의 «구조 2·3 뒤» 칸을 새 코드에서 찾아 채운다 |

원본 사본(백업 대신 · `_backup_` 을 새로 만들지 않았다): `stage1/before/`
 · `before/app/{server,boxes,instances,dupes,maskio}.py`·`run.sh` · `before/export/*.py`
 · `before/tests/sandbox.py` · `before/merged_tests/`(고친 통합 시험 5개의 원본)

---

## 3. 전/후 파일·줄 수

### 3-1. 전 (2026-09-19 23:19 판 = 기준선 판)

| 파일 | 줄 |
|---|---:|
| `app/server.py` | **2,052** |
| `app/instances.py` | 690 |
| `app/boxes.py` | 491 |
| `app/dupes.py` | 113 |
| `app/maskio.py` | 86 |
| **합계** | **3,432** |
| (참고) `export/export_dataset.py` | 447 |
| (참고) `export/make_delete_script.py` | 118 |

### 3-2. 후 (2026-09-20 01:35 정본 반영)

| 파일 | 줄 | 무엇 |
|---|---:|---|
| `app/server.py` | **93** | 앱 만들기 · `CTX` 한 꾸러미 · `register()` 8번 · `__main__` |
| `app/boxes.py` | 19 | **호환 껍데기**(다시 내보내기만) |
| `app/instances.py` | 23 | 호환 껍데기 |
| `app/dupes.py` | 19 | 호환 껍데기 |
| `app/maskio.py` | 18 | 호환 껍데기 |
| `app/core/paths.py` | 197 | 경로·과일·데이터셋 폴더·파일 목록 캐시·상수 |
| `app/core/util.py` | 118 | 시각·숫자·자물쇠·오류 응답·로그 |
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| `app/core/status_store.py` | 180 | **`status.json` 쓰는 길 하나** |
| `app/domain/maskio.py` | 127 | 마스크 PNG(0/255 · uint16) 파일 형식 |
| `app/domain/statusfmt.py` | 186 | status 항목의 꼴 · 작업자 B·C 산출물 읽기 |
| `app/domain/rules.py` | 246 | **데이터 규칙(이름 있는 함수)** + 이름 붙인 수 |
| `app/domain/dupes.py` | 69 | 근접 중복 묶음 |
| `app/api/photos.py` | 367 | `/` `/box` `/static/<fn>` `/api/fruits` `/api/list` `/api/item` `/img` `/mask` `/thumb` |
| `app/api/masks.py` | 314 | `/api/component` `/api/save` `/api/revert` `/api/status` |
| `app/api/boxes.py` | 404 | `/api/boxes`(GET·POST) `/api/boxes_seed` `/api/boxes_export` `/api/boxes_stats` |
| `app/api/instances.py` | 636 | `/instances` `/api/instance_info` `/api/save_instances` `/api/revert_instances` `/api/instance_errors` + 개수 캐시 |
| `app/api/counts.py` | 85 | `/api/instance_stats` + `counts_of()`·`COUNT_TEAM` |
| `app/api/dupes.py` | 258 | 중복 6개(`/api/duplicate_preview` … `/api/export_excluded`) |
| `app/api/export.py` | 309 | `/api/export_start` `/api/export_status` `/api/export_list` `/api/export_plan` |
| `app/api/dashboard.py` | 66 | `/api/stats` `/api/health` |
| `__init__.py` × 3 | 6 | 묶음 표시(2줄씩) |
| **합계** | **3,924** | |

**줄이 492줄 늘었다.** 솔직히 적자면: 파일마다 «여기가 무엇을 하는 곳인가» 머리말(21개)과
`domain/rules.py` 의 규칙 함수 10개 docstring 이 늘어난 몫이고, **옮긴 코드 자체는 한 줄도
늘지 않았다**(`compose.py` 가 글자 그대로 옮긴다). 지시서 §1 의 목표는 «줄 수 줄이기» 가 아니라
«처음 온 사람이 반나절에 기능 하나를 고칠 수 있게» 이므로 이 맞바꿈을 택했다.

---

## 4. 모듈 구조도

```
app/
  server.py            93줄 — 앱 만들기 + register 호출만  ← run.sh 가 이 파일을 띄운다
  core/                «어디에 무엇이 있나»
    paths.py           APP_DIR·ROOT·DATA_DIR·CACHE_DIR·EXPORTS_DIR·DATASET·dataset_for()
                       FRUITS · MAX_UPLOAD_BYTES · status_file()·img_path()·gt_path()·fixed_path()
                       ·proposal_path()·inst_fixed_path()·box_json_path()
                       stems_of()·stem_set()·check() · fixed_set()·box_set()·n_boxes_of()
                       ·has_proposals()·_prop_names() · _mtime()/mtime_of()
    util.py            lock_for()·now_str()·as_int()·short_path()·err_json()
                       register_errors(app)(413·404·400·500) · log_warn()·log_exc()
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
                       register(app, ctx) → `/login` + before_request
    status_store.py    read_status·write_status·backup_status·update_status·write_status_entry
                       ·confirm_status·clear_confirm      ← **status.json 을 여는 곳은 여기뿐**
  domain/              «파일 형식과 규칙»
    maskio.py          load_mask_bool·load_mask_raw·save_mask_atomic·bool_to_png_bytes
                       ·raw_to_png_bytes·mask_value_report · read_u16·png_u16_bytes
                       ·write_u16_atomic·ids_of
    statusfmt.py       STATUSES·CONFIRM_KINDS·src_of·confirmed_of·verdict_of·ai_boxes_status
                       load_scores·load_inspection·split_flags·flag_counts·load_duplicates
    rules.py           **규칙 = 이름 있는 함수**(§6) + 이름 붙인 수 13개
    dupes.py           load_duplicate_groups·representative_map·duplicate_exclusions·excluded_stems
  api/                 «주소». 파일마다 `register(app, ctx)` 하나
    photos.py  masks.py  boxes.py  instances.py  counts.py  dupes.py  export.py  dashboard.py
  boxes.py instances.py dupes.py maskio.py    ← **호환 껍데기**(§7)
  static/              손대지 않았다 (구조 사이클 3 소유)
```

의존 방향은 **위에서 아래로만** 이다: `server → api → (core, domain)` · `core → domain`(상수 두 개) ·
`domain` 은 서로만 본다. 되돌아 올라가는 import 는 없다(`refcheck.py` 가 돌 때 순환이면 터진다).

`server.py` 가 넘기는 꾸러미 `CTX` 의 열쇠 이름은 **0917 부터 `boxes.py`·`instances.py` 가 쓰던
그대로**다(`check`·`DATA_DIR`·`img_path`·`lock_for`·`err_json`·`labeled`·`now_str`·`FRUITS`·
`confirm_status`·`clear_confirm`·…). 그래서 그 두 파일의 `register()` 몸통은 **한 글자도 바뀌지 않았다.**

---

## 5. `status.json` 쓰기 경로 통합

| | 전 | 후 |
|---|---|---|
| 파일 경로를 계산하는 곳 | **2곳** — `server.status_file()` · `dupes.read_status()` 안에서 직접 `os.path.join` | **1곳** — `core/paths.py status_file()` |
| 읽기 구현 | **2개** — `server.read_status()` · `dupes.read_status()` (글자만 다른 같은 코드) | **1개** — `core/status_store.read_status()`(`app/dupes.py` 가 그것을 다시 내보낸다) |
| 파일을 실제로 쓰는 함수 | `server.write_status()` · `server.backup_status()` | `core/status_store.write_status()` · `backup_status()` (같은 함수, 한 모듈) |
| 그 위에서 항목을 고치는 함수 | `update_status`·`write_status_entry`·`confirm_status`·`clear_confirm` (server.py) | 같은 이름 그대로 **`core/status_store.py` 안에만** |
| `write_status()` 를 직접 부르는 라우트 | 4개(중복 일괄/되돌리기·묶음 제외/되돌리기) | 같은 4개 — `api/dupes.py` 가 `core.status_store.write_status` 를 부른다 |
| `export/`·툴 밖에서 읽는 길 | `from dupes import read_status` | **그대로 돈다**(껍데기) |

즉 **«쓰는 길» 은 원래도 `write_status()` 하나였고, 이번에 «경로·읽기 구현» 두 벌을 한 벌로
합쳤다.** `data/<과일>/status.json` 이라는 글자가 코드에 나오는 자리는 2곳 → **1곳**이다
(나머지 12곳은 전부 설명 주석·머리말이다 — §11 재현 명령으로 셀 수 있다).

---

## 6. 규칙 → **이름 있는 함수** (`app/domain/rules.py`)

| 규칙 | 함수 | 전에는 어디에 |
|---|---|---|
| **이진본이 번호본을 자른다**(N1) | `cut_by_binary(inst, binary)` | `instances.load_inst()` 안 3줄 + 주석 |
| **N6 쓰기 규칙** — 번호가 있던 화소만 이진본에서 뺀다 | `keep_numberless_foreground(bfg, cur, shape)` | `api_save_instances()` 안 한 줄 + 주석 12줄 |
| 번호 **0개 저장은 400으로 막는다** | `zero_instance_save_blocked(n_ids, bfg)` | 같은 함수 안 `if ids.size == 0 and bfg.any()` |
| 상자 **0개 저장 = 그 작업의 되돌리기** | `is_box_clear_save(boxes)` | `boxes.register()` 안 `if not boxes:` |
| 개수 유도(번호 확정 > 상자 확정 · **어긋나면 비움**) | `human_count(...)` | `boxes.py`(그대로 옮김) |
| 마스크 저장이 **«제외» 를 뒤집지 않는다** | `mask_save_keeps_exclude(status)` | `server._save_verdict()` 안 `!= "exclude"` |
| 제외를 지킬 때 **메모 앞부분을 지킨다** | `merge_exclude_note(old, note)` | 같은 함수 안 2줄 + 주석 8줄 |
| 번호 저장이 **exclude·flag 를 뒤집지 않는다** | `status_after_instance_save(prev)` | `api_save_instances()` 안 한 줄 |
| **«AI» 로 시작하는 이름은 400** | `ai_name_rejected(by)` | `server.api_status()` 안 `by.startswith("AI")` |
| **flag·exclude 는 내보내기에 안 나간다** | `goes_out(status)` · `CONFIRM_OUT` | `("ok","fixed")` 를 4곳에 손으로 적었다 |
| 근접 중복 **묶음 대표 고르기** | `pick_representative(group, status)` | `dupes.py`(그대로 옮김) |
| 상자 정리(3,000개 상한 · 2픽셀 미만 버림) | `clean()` · `MAX_BOXES` · `MIN_SIDE` · `CLASSES` | `boxes.py`(그대로 옮김) |
| 번호마다 상자 하나(4화소 미만 버림) | `boxes_of(lab, min_px, limit)` | `boxes.py`(그대로 옮김) |
| 중복 제외 표식 | `SRC_DUP_BULK` · `SRC_DUP_GROUP` | `server.py` 머리 |

**일부러 옮기지 않은 규칙**(한 곳에만 두는 것이 옳아서 · `rules.py` 끝에 «어디에 있나» 로 적어 두었다):
되돌리기가 확정을 지운다 → `status_store.clear_confirm()` · 묶음 확정에서 이미 확정한 구성원은
건너뛴다 → `status_store.confirm_status()` · 옛 판정을 `prev` 에 한 벌 남긴다 → `update_status()`.

**이름 붙인 수 13개**(매직 넘버 금지): `NAME_MAX 40` · `NOTE_MAX 300` ·
`PAGE_SIZE_DEFAULT 120`/`MIN 20`/`MAX 500` · `CONFIRM_STEMS_MAX 500` · `UNDO_STEMS_MAX 200` ·
`EXPORT_LIST_MAX 200` · `DUP_SAMPLE_MAX 20` · `THUMB_PX 200` · `THUMB_QUALITY 72` ·
`LABEL_CACHE_MAX 4` · `LOGIN_FAIL_SLEEP 0.5` (+ `core/paths.py MAX_UPLOAD_BYTES 64MB` ·
`domain/rules.py MAX_BOXES 3000`·`MIN_SIDE 2`).
값은 **하나도 바뀌지 않았다** — 바뀌었으면 ①②⑤ 가 즉시 다르다고 말한다.

---

## 7. 호환 껍데기 — 툴 **밖**에서 이름으로 부르는 곳을 살린다

`app/boxes.py`(19줄) · `app/instances.py`(23줄) · `app/dupes.py`(19줄) · `app/maskio.py`(18줄)
는 코드가 없는 **다시 내보내기 모듈**이다.

| 부르는 곳 | 무엇을 | 확인 |
|---|---|---|
| `semantic-segmentation/tools/build_merged_dataset.py:1481` `import boxes` | `export_boxes_to()` | merged 536/0 · 로그에 «자체 구현» **0번** |
| `tools/tests_merged_260918/counts/test_counts.py:158` `import instances` | `INST.*` | `counts/test_counts.py` 62/0 |
| `export/export_dataset.py` | `from maskio import …` · `from dupes import …` · `from instances import …` · `from boxes import human_count, team_count` | `②` 내보내기 지문 0칸 |
| 지난 사이클 시험 | `import boxes`·`import instances`·`import maskio` | `u1`·`u2`·`u3` 그대로 통과 |

### 새 시험 `tests/unit/u6_py_contract.py` (24항목 · 서버를 띄우지 않는다)
리팩터 **전** 코드에서 얼려 둔 `tests/fixtures/py_contract_260920.json` 과 견준다:
① 공개 함수·상수 이름이 전부 아직 있나 ② 상수 **값**이 같나 ③ 주소표 37개가 규칙·엔드포인트·
메서드까지 같나 ④ 곁따라 들어온 모듈 별칭 변화는 **경고**만 ⑤ 껍데기 4개가 30줄 이하인가.

실측(전 → 후 · 함수·상수만):
```
boxes      16 → 16  (사라진 것 없음)        maskio  6 → 10 (uint16 4개가 합쳐졌다 — 더하기)
dupes      13 → 13  (사라진 것 없음)        instances 36 → 36 (사라진 것 없음)
상수 값 13종 전부 같다 · 주소 37개 전부 같다
```
모듈 별칭 변화(계약 아님 · 경고): `boxes.ndimage` 빠짐(규칙 함수가 `domain/rules.py` 로 가서
여기서 `scipy` 를 더 쓰지 않는다) · `instances.paths` 더함 · `maskio.io` 더함.

### `build_merged_dataset.py` — 조용한 폴백을 없앴다
사이클 1 2차 §7-4 가 «가장 위험한 것» 으로 꼽은 자리다. 고친 것(그 파일 한 곳만):
1. `except Exception` 폴백을 쓰면 `TOOL_BOXES_FALLBACK` 에 **기록**하고,
   `write_fruit()` 가 `problems` 에 한 줄 남기고, **`verify()` 가 실패**로 센다(맨 앞에 넣어
   «40건 넘으면 생략» 에 밀리지 않게).
2. 폴백에도 **«줄 0개 json 은 txt 를 만들지 않는다»** 규칙을 넣었다(0919 개수 사이클5 규칙).
   전에는 폴백이 0바이트 YOLO txt 를 만들어 검출 학습이 «이 사진에는 열매가 없다» 로 읽었다.
확인: merged 로그에 «자체 구현» 0번 = 지금은 폴백을 타지 않는다(껍데기가 살아 있다).

---

## 8. 관문 결과 — «동작 무변경» 증거

### 8-1. 모래상자 (전/후 같은 시험·같은 자료)

| | 전 `logs/sb_before_check.log` | 후 `logs/sb_final_browser.log` |
|---|---|---|
| ① API 응답(고정 표본 12장) | **0칸** | **0칸** |
| ② 내보내기 산출 지문 | **0칸** | **0칸** |
| ⑤ 나머지 라우트·쓰기 경로 | **0칸** | **0칸** |
| ③ 회귀 묶음 | 0칸 | 9칸 **전부 경고**(새 묶음 3개 · merged 535/1→536/0 · u4 7→8) |
| ④ 코드 지문 | 0칸 | 24칸(새 파일 21 + 고친 5 — **참고용**) |
| 합계 | 833 통과 / 1 실패 | **991 통과 / 0 실패** |

브라우저 묶음(진짜 파이어폭스 1366×768)도 통과: `b1_browser` 81/0 · `t2_ui` 27/0.

### 8-2. 정본 (`app/` 에 반영한 뒤 한 번 더)
`logs/live_final.log` — §12 에 결과 표. 실서버(PID 1467097)는 **재시작하지 않았다**
(파이썬은 뜰 때 읽은 코드를 들고 있으므로 디스크를 바꿔도 돌고 있는 서버는 그대로다).

### 8-3. 주소 37개 — 전/후 같은 입력 → 같은 출력
```
routes/routes_before.json   (before/app)      37개
routes/routes_after.json    (모래상자 app)     37개   ← 규칙·엔드포인트·메서드까지 완전히 같다
routes/routes_after_live.json (정본 app)       37개   ← 같다
```
그리고 그 37개 **전부에 실제로 요청을 보내는** 것이 기준선 ①(50+50 응답)과 ⑤(118칸)이고,
둘 다 «다른 칸 0개» 다. 즉 «같은 입력 → 같은 출력» 이 37/37 확인됐다.

---

## 9. 시험 위생 (사이클 1 3차가 넘긴 것)

| # | 넘겨받은 것 | 한 것 |
|---|---|---|
| 1 | `test_fixes_m2.py F7-c` 손 단정 **977** | **동적 계수로 바꿨다** — «빈 툴 json 을 **감춘** 빌드» 를 한 번 더 돌려 상자 줄 수를 견준다(고치기 전 코드에서는 4줄 달라지고, 고친 뒤에는 늘 같다). 사람이 판정을 바꿔도 두 빌드가 같이 움직인다. → merged **536/0**(처음으로 전부 통과) |
| 2 | 공용 `T/data` 를 읽는 merged 시험 4개 | **얼린 표본**으로. `tests/fixtures/tool_data_260920/`(4과일 × `status.json`·`duplicates.json`)를 얼리고, `tests/merged/run_merged.sh` 가 «판정·묶음만 얼리고 나머지는 심볼릭 링크» 사본을 만들어 `MERGED_TOOL_DATA` 로 넘긴다. `build_merged_dataset.py`·`test_fixes_m3.py`·`test_fix_m5c.py`·`test_build_merged.py` 가 그 변수를 보면 그것을 쓴다(없으면 예전 그대로 — 실제 빌드는 늘 지금 자료를 본다) |
| 3 | 얼린 표본에 `flag` 한 장 | **기준선을 늘리지 않고** 새 시험 `tests/api/t4_flag.py`(17항목)로 덮었다. 까닭: 기준선을 늘리면 `--rebaseline` 이 필요하고 그 기준선을 **구조 사이클 3 이 같이 쓰고 있다**(§10 못 한 것 1번) |
| 4 | `/login` **429** 라우트 덮기 | 새 시험 `tests/api/t3_login_rate.py`(7항목) — 2차 검수 권고대로 **자기 서버 하나만** 띄워 잠그고 끝낸다(잠금 창이 다른 시험을 오염시키지 않는다) |
| 5 | `sandbox.py sync(src=)` | 넣었다. `sync(src="…/_archive/pre_refactor_260920")` 한 줄로 «되돌린 판으로 전체 시험» 이 된다(자료는 늘 지금 것) |
| 6 | 남긴 백업 36개(`cnt4*`·`cnt5*`) → 아카이브 | **13개 옮겼다**(`app/` 10 · `export/` 1 · `scripts/` 2). `app/static/` 의 **12개는 손대지 않았다** — 구조 사이클 3 소유다. `INDEX.md` 에 표로 추가. 폴백 확인: `u4_archive_fallback` 8/0 |
| 7 | 죽는 정본 시험 20개는 목록만 | 아래 §9-2 |
| + | `u5_js_contract` 42항목 | 그대로 통과(화면을 건드리지 않았으므로) |

### 9-1. 시험 틀에서 고친 것 두 가지(둘 다 «좋아진 것을 실패라고 말하던» 자리)
- `baseline/snapshot.py diff_bundles()` — **시험 묶음이 새로 늘어난 것**(`⟨없던 묶음⟩`)을 경고로.
  전에는 `u6`·`t3`·`t4` 를 더하면 ③ 이 거짓 실패였다(더한 시험이 벌을 받는 셈).
- 같은 함수 — **실패 수가 줄어든 것**도 경고로. README §4 ③ 은 «실패 수가 **늘거나** 통과 수가
  **줄면** 실패» 라고 적어 두었는데 코드는 «달라지면 실패» 였다. 그래서 `F7-c` 를 고쳐
  merged 가 535/1 → **536/0** 이 되자 ③ 이 «실패 1개» 라고 말했다(01:35 실측).
- `run_all.sh` — `syntax` 묶음이 `app/core/*.py`·`app/api/*.py`·`app/domain/*.py` 도 본다(글롭이라
  파일이 늘어도 고칠 필요가 없고, **묶음 줄은 늘지 않아** ③ 이 흔들리지 않는다).
  `api` 묶음에 `t3_login_rate`·`t4_flag` 를 **이름으로** 더했다(글롭을 쓰지 않는다 — 2차 검수 §8-2).
- `lib/sandbox.py grape_seeded()` — `SEED_DIRS` 가 `app/api/instances.py` 로 옮겨 갔으므로 두 자리를
  다 본다(옛 판에서도 돈다). 포도는 지금도 **꺼져 있다**(교수님 확인 8번 대기 — 값 안 바꿨다).
- `unit/u4_archive_fallback.py 단위4-4` — «원래 자리에 남아 있는 백업» 의 보기로 쓰던
  `_backup_260919_cnt4_server.py` 를 이번에 아카이브로 옮겼으므로, 시험이 **스스로 임시 파일 한 개를
  만들어** 순서를 확인하고 곧바로 치운다(`단위4-4b` 가 «남기지 않았다» 를 지킨다).

### 9-2. 백업 13개를 옮겨서 **죽는 정본 시험 14개** (목록만 · 원본 무수정)
```
cycles/260919_count/cycle_4/stage1/{lib_cnt4.py, b3_chars.py, b5_oldserver.py}
cycles/260919_count/cycle_4/stage2/{lib_cnt4b.py, b3_chars.py, b5_oldserver.py}
cycles/260919_count/cycle_5/stage1/{lib_cnt5.py, b3_chars.py, b5_oldserver.py, c5_fix.py}
cycles/260919_count/cycle_5/stage2/{lib_cnt5.py, b3_chars.py, b5_oldserver.py, c5_fix.py}
```
되살리는 세 방법은 `_archive/backups_260920/INDEX.md` 끝(권장: `tests/` 판을 쓴다 — `backup_src()`
폴백이 아카이브를 대신 본다). 사이클 기록이므로 **원본은 한 글자도 고치지 않았다.**
사이클 1 이 «20개» 로 셌던 것은 그때 남아 있던 백업 27개 기준이고, 이번에 옮긴 13개로 실제로
경로가 깨지는 파일은 위 14개다(`tests/unit/u4_archive_fallback.py` 는 폴백이 있어 산다).

---

## 10. 못 한 것 · 남긴 것 (솔직히)

1. **기준선을 다시 뜨지 않았다.** `flag` 한 장을 ⑤ 에 더하는 것(2차 §10-3)과 `merged 536/0` 으로
   ③ 을 갱신하는 것(`tests/README.md` §4-2)은 **둘 다 `--rebaseline` 이 필요**한데, 지금 그
   기준선을 **구조 사이클 3 이 같이 쓰고 있다**(같은 `tests/fixtures/baseline_260920/`).
   리팩터 중에 기준선을 흔들면 상대 사이클의 관문이 무의미해진다 → **사이클 5(전환)가 뜬다.**
   대신 flag 갈래는 `t4_flag`(17항목), 429 갈래는 `t3_login_rate`(7항목)로 덮었다.
2. **`app/static/` 의 백업 12개**를 옮기지 못했다(구조 3 소유). `INDEX.md` 에 목록을 남겼다.
3. **80줄 넘는 «논리» 함수 3개를 쪼개지 않았다** — 동작 무변경이 먼저다(§10-1 표).
4. `tests/browser/{b2_export,b4_fallback,b5_oldserver}` 미도입(1차·2차가 못 한 것 그대로).
5. `app/README.md` 재작성은 **사이클 4** 몫이다(이번에는 손대지 않았다 — 같은 파일을 두 사이클이
   쥐면 안 된다). 다만 `server.py` 머리말에 «어디에 무엇이 있나» 표를 넣어 두었다.
6. 화면 배율 2x/3x 상자 이동 결함(1차가 기준선으로 굳힌 것)은 **이번에도 고치지 않았다**(열린 문제).
7. `api/*.py` 의 `register()` 가 길어졌다(최대 `photos.register` 326줄) — 그 안의 라우트 함수는
   하나하나 짧고, `register` 는 **담는 그릇**이다. 쪼개려면 라우트를 모듈 최상위로 올리고
   `app.add_url_rule` 로 붙이는 방법이 있는데, 그러면 함수 몸통을 손대야 해서 이번에는 두었다.

### 10-1. 80줄 넘는 함수 — 못 쪼갠 목록

| 함수 | 줄 | 왜 그대로 두었나 |
|---|---:|---|
| `api/photos.py api_list()` | 141 | 걸러내기 9종 + 정렬 4종 + 쪽 나누기가 한 흐름이다. 쪼개면 `items` 만드는 순서가 바뀔 위험이 있고 ① 의 응답 JSON 이 곧 계약이다 |
| `api/instances.py api_save_instances()` | 105 | N6 쓰기·메모 잇기·`prev` 지키기가 **한 자물쇠 안**에서 순서대로 일어난다(순서가 규칙이다 — 0918 주석 참조) |
| `api/boxes.py export_boxes_to()` | 92 | CLI·`/box` 화면·통합 데이터셋 **셋이 같은 함수**를 쓴다. 바이트 동일(②)이 조건이라 손대지 않았다 |
| `register()` 8개 | 66~326 | 라우트를 담는 그릇(위 10-7) |

---

## 11. 2차 검수가 **그대로 재현**할 명령

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
C=$T/cycles/260920_structure/cycle_2/stage1
PY=/home/kds0206/.conda/envs/kwak/bin/python

# ① 관문 (정본) — ①②⑤ 0칸 · ③ 경고만 · merged 536/0 · 991 통과 / 0 실패
bash $T/tests/run_all.sh --browser --check-baseline; echo "rc=$?"

# ② 빠른 관문 (약 40초)
bash $T/tests/run_all.sh --no-merged --only=syntax,unit,sim,api

# ③ 옮기기가 «글자 그대로» 인지 다시 만들어 본다(모래상자를 새로 짠다)
cd $C && $PY tools/compose.py && $PY tools/pass2_rules.py     # 반드시 이 순서
diff -r --brief $C/sandbox/app/core $T/app/core               # 차이가 없어야 한다
diff -r --brief $C/sandbox/app/api  $T/app/api
diff -r --brief $C/sandbox/app/domain $T/app/domain

# ④ «없는 이름» 찾기 (py_compile 이 못 잡는 NameError)
cd $C && $PY tools/refcheck.py $T/app core/paths.py core/util.py core/status_store.py \
  core/auth.py domain/rules.py domain/maskio.py domain/statusfmt.py domain/dupes.py \
  api/photos.py api/masks.py api/boxes.py api/instances.py api/counts.py api/dupes.py \
  api/export.py api/dashboard.py server.py

# ⑤ 주소 37개 전/후 대조
cd $C && $PY tools/routemap.py $C/before/app $C/routes/x_before.json \
        && $PY tools/routemap.py $T/app      $C/routes/x_after.json \
        && $PY -c "import json;a=json.load(open('$C/routes/x_before.json'));b=json.load(open('$C/routes/x_after.json'));print('같다' if a['routes']==b['routes'] else '다르다', len(a['routes']),'/',len(b['routes']))"

# ⑥ 파이썬 공개 이름 계약 (얼린 것과 견주기)
bash $T/tests/run_all.sh --only=unit     # u6_py_contract 24항목

# ⑦ status.json 이라는 글자가 코드에 나오는 자리 세기(설명 주석까지 다 나온다)
cd $T/app && grep -rn "status.json" server.py core api domain | grep -v '"""' | grep -v '^\s*#'

# ⑧ 되돌리기 — 리팩터 전 판으로 전체 시험(새로 넣은 sync(src=))
cd $T/tests/browser && $PY -c "import sandbox as L; L.sync(src=L.T+'/_archive/pre_refactor_260920'); print('옛 판으로 모래상자를 맞췄습니다')"
```

되돌리는 길(전환 전이라 언제든): `_archive/pre_refactor_260920/`(사이클 1 이 뜬 스냅샷 1,592파일) ·
이번 원본 사본 `cycles/260920_structure/cycle_2/stage1/before/`.

---

## 12. 정본 관문 결과 (실측)

(§8-2 · `logs/live_final.log`)

### 12-1. 실측 (01:36:23 → 01:42:00 · `logs/live_final.log`)

```
① API 응답(고정 표본)      : 다른 칸 0개
② 내보내기 산출 지문        : 다른 칸 0개
⑤ 나머지 라우트·쓰기 경로   : 다른 칸 6개   ← 아래 12-2 (전부 app/static — 구조 사이클 3)
③ 회귀 묶음               : 12칸 전부 «경고»(실패로 세는 것 0개)
④ 코드 지문               : 27칸(새 파일 21 + 껍데기·server 5 + app/static 3 — 참고용)
```

### 12-2. ⑤ 6칸은 **전부 구조 사이클 3 의 화면 분리**다 — 서버 쪽은 0칸

| 다른 칸 | 기준선 | 지금 | 무엇 |
|---|---:|---:|---|
| `r_page_index/bytes`·`sha256` | 29,900 | 31,724 | `app/static/index.html` (01:06 수정) |
| `r_page_box/bytes`·`sha256` | 29,900 | 31,724 | 같은 파일(`/box` 도 index.html 을 준다) |
| `r_static_app_js/bytes`·`sha256` | 145,377 | **1,578** | `app/static/app.js` 를 `static/js/*` 로 쪼갰다(01:07) |

실측 근거(읽기만 · 01:42:27):
```
app/static/app.js   1,578바이트  2026-09-20 01:07      app/static/js/   01:36 (새 폴더)
app/static/ui.js      928바이트  2026-09-20 01:07      app/static/index.html 31,724 01:06
```
내 반영은 **01:35:50** 이고, 이 파일들은 그보다 **먼저(01:06~01:07)** 바뀌었다.
⑤ 의 나머지 **112칸**(GET·POST 응답·`status.json`·`boxes/*.json`·`boxes_yolo/*.txt`·`masks_fixed`·
`instances_fixed`·`excluded_list.txt` 까지)은 **한 칸도 다르지 않다** = 서버 동작 무변경.
그리고 격리된 모래상자(§8-1)에서는 ⑤ 가 **118칸 전부 0** 이다 — 그쪽은 화면이 옛 판이라서다.

### 12-3. 표의 줄이 두 번씩 찍힌 것도 같은 까닭 (믿으면 안 되는 칸)

같은 시간에 **구조 사이클 3 도 정본에서 `run_all.sh` 를 돌렸다.** 두 실행이 공용
`tests/_out/bundles.tsv` 한 파일에 같이 쓰기 때문에 표가 섞였다(`api/t1_api` 두 줄 ·
`merged` 두 줄 · 구조 3 의 새 묶음 `unit/u7_keys_doc`·`unit/u8_js_globals` 가 내 표에 등장 ·
`merged 411/518`·`t2_ui 23/4`). **이 표의 합계(1,723/5)는 두 사이클이 섞인 수여서 쓸 수 없다.**

이번 사이클의 숫자는 **격리된 모래상자 실행**(§8-1 · `logs/sb_final_browser.log`)을 쓴다:
**991 통과 / 0 실패 · merged 536/0 · browser 108/0 · ①②③⑤ 0칸.**
`t2_ui 나-1` 실패도 화면 문구(«③ 한 줄») 이야기여서 구조 3 의 작업 중 상태다 — 내 모래상자에서는
`t2_ui` 27/0 으로 통과했다.

### 12-4. 정본 = 모래상자 임을 따로 확인

```
diff -r --brief 모래상자/app/{core,api,domain}  정본/app/{core,api,domain}   → `__pycache__` 의 .pyc 만 다름
cmp server.py boxes.py instances.py dupes.py maskio.py                       → 전부 같음
주소표: 정본 37개 = 리팩터 전 37개 (규칙·엔드포인트·메서드까지)
실서버 PID 1467097 (00:04:44 기동) — 01:42:27 에도 그대로. 재시작·쓰기 없음
```

### 12-5. 2차에게 남기는 부탁

구조 사이클 3 이 끝난 **뒤에** `bash tests/run_all.sh --browser --check-baseline` 를 한 번 더
돌려 주세요(두 사이클이 겹치지 않는 시간에). 그때 ⑤ 는 화면 3칸만 남고(그것은 구조 3 이 설명),
③ 은 새 묶음만 경고로 남습니다. **기준선을 다시 뜨는 것은 사이클 5(전환) 의 일입니다**(§10-1).


---

## 13. 산출물 목록

```
cycles/260920_structure/cycle_2/
  stage1_work.md                       ← 이 문서
  stage1/README_5_규칙표_after.md       규칙표 초안의 «구조 2·3 뒤» 칸을 채운 사본
  stage1/before/                       리팩터 전 원본 사본(app 6 · export 2 · tests 1 · merged_tests 5)
  stage1/sandbox/                      작업한 모래상자(app·export·scripts·tests·data·_archive)
  stage1/tools/                        blocks·compose·pass2_rules·refcheck·routemap·contract_probe·fill_rules_table
  stage1/routes/                       routes_before.json · routes_after.json · routes_after_live.json
  stage1/contract_before.json          얼린 공개 이름·상수·주소표(= tests/fixtures/py_contract_260920.json)
  stage1/logs/                         sb_before_check · sb_quick1 · sb_unit2·3 · sb_api2·3·4 · sb_after_check
                                       · sb_final_browser · live_final
정본에 반영한 것
  app/server.py(93줄) · app/{boxes,instances,dupes,maskio}.py(껍데기) · app/core/ · app/api/ · app/domain/
  tests/run_all.sh · tests/lib/sandbox.py · tests/baseline/snapshot.py · tests/merged/run_merged.sh
  tests/unit/{u4_archive_fallback,u6_py_contract}.py · tests/api/{t3_login_rate,t4_flag}.py
  tests/fixtures/py_contract_260920.json · tests/fixtures/tool_data_260920/
  _archive/backups_260920/{app,export,scripts}/ + INDEX.md (13개 추가)
툴 밖(지시서 §3 이 시킨 것만)
  semantic-segmentation/tools/build_merged_dataset.py           폴백 기록·verify 실패·0줄 규칙·MERGED_TOOL_DATA
  semantic-segmentation/tools/tests_merged_260918/stage2/test_fixes_m2.py   F7-c 동적 계수
  … /stage3/test_fixes_m3.py · /stage5/test_fix_m5c.py · /test_build_merged.py   MERGED_TOOL_DATA
  (원본은 전부 stage1/before/merged_tests/ 에 사본을 남겼다)
```
