작성: 2026-09-20

# 구조 정리 5사이클 — 사이클 3 «화면(JS) 분리» 1차 작업 기록 (Opus 5)

시각은 전부 서버 `date` 실측입니다. 시작 **2026-09-20 00:39** · 1차 작업 끝 **01:51**(맨 끝 «시각표»).
지시: `문서/260919_툴_구조정리_인수인계_5사이클_지시.md` §2·§4(사이클 3)·§5 ·
`cycles/260920_structure/cycle_1/stage3_final.md` §2 · `cycle_1/stage2_review.md` §2·§11.

**한 줄 결론 — 했습니다. 화면 코드 `app.js`(2,664줄)+`ui.js`(1,337줄) → `app/static/js/*.js` 12파일,
전역 152개 → 3개(`S`·`API`·`UI`), 단축키 표 한 곳(`keys.js`), 동작은 바뀌지 않았습니다**
(브라우저 14걸음 상태 JSON **다른 칸 0개** · 스크린샷 14장 중 **13장이 바이트까지 동일**,
나머지 한 장은 화면에 찍히는 서버 시각뿐 · 콘솔 오류 0 · 시뮬 90항목·u5 42항목 그대로 통과).

---

## 0. 시작 관문 (00:39~00:44)

| 무엇 | 결과 |
|---|---|
| `bash tests/run_all.sh --no-merged --only=syntax,unit,sim` | **164/0** (syntax 4 · u1~u5 74 · boxsim 50 · modesim 31 · sim 9) rc=0 |
| `--check-baseline` ④ | 구조 사이클 2 가 **같은 시각에** 정본 기준선 대조를 돌리고 있어(01:02 `cycle_2/stage1/logs/sb_before_check.log`) 정본에서 두 번 돌리지 않았습니다. ④(정적 파일 지문)는 제가 정본 `app/static/` 을 **손대기 전**이라 0칸이 보장됩니다 — 실제로 `before/` 사본과 정본 파일의 sha256 을 01:5x 반영 직전에 다시 대조했습니다(§8). |

⚠ **동시에 도는 사이클 2**: `cycle_2/stage1/sandbox` 에서 서버(파이썬) 분리를 하고 있습니다.
제가 만진 것은 `app/static/**` 와 `tests/sim/`·`tests/browser/`·`tests/unit/u7·u8`(새 파일)뿐이고,
`app/*.py`·`core/`·`api/`·`domain/`·`export/` 는 **읽기만** 했습니다.

---

## 1. 전후 — 파일·줄 수

| | 전 (2026-09-19 22:07·23:36) | 후 (2026-09-20) |
|---|---|---|
| 파일 | `app.js` **2,664줄** · `ui.js` **1,337줄** (2파일 4,001줄) | `js/*.js` **12파일 4,309줄** + 옛 `app.js` 18줄·`ui.js` 10줄(안내·다리) |
| 한 파일 최대 | **2,664줄** | **874줄** (`instances.js`) |
| 전역(깊이 0 선언) | **152개** (`app.js` 최상위 전부 · `ui.js` 는 이미 IIFE 여서 0) | **3개** — `S` · `API` · `UI` |
| `window.<이름>` | 5개 | 5개 (그대로 — §6 «못 한 것») |
| 단축키 표 | 없음(코드 + `index.html` 풍선말 두 군데) | `keys.js` 의 `KEYS` **32줄** + `u7` 이 도움말·코드와 대조 |

| # | 파일 | 줄 | 함수 | 내놓는 이름 | 역할 |
|---|---|---:|---:|---:|---|
| 1 | `js/state.js` | 72 | 1 | 6 | 상태 `S` 와 전역 셋 · 공용 낱말표 |
| 2 | `js/api.js` | 86 | 6 | 8 | 서버 부르기 · `$`·`flash`·`who`·`errMsg`·`escapeHtml` |
| 3 | `js/view.js` | 530 | 22 | 16 | 캔버스·확대·화면/작업/보기 전환·레이어 칩·0.2초 tick |
| 4 | `js/mask.js` | 340 | 21 | 18 | 마스크 읽기·붓·다각형·자동채움·되돌리기 |
| 5 | `js/boxes.js` | 364 | 21 | 20 | 상자 그리기·초벌·저장·YOLO 내보내기 |
| 6 | `js/instances.js` | 874 | 48 | 22 | 열매 번호 편집(위쪽 INSTCORE = 순수 함수) |
| 7 | `js/counts.js` | 681 | 19 | 12 | 사람 확정·판정·하단 한 줄·개수 칸 |
| 8 | `js/list.js` | 695 | 20 | 16 | 사진 목록·사진 열기·묶음·현황 |
| 9 | `js/export.js` | 312 | 13 | 1 | «데이터 정리» 탭 |
| 10 | `js/tour.js` | 100 | 5 | 4 | 첫 방문 안내 3장 |
| 11 | `js/keys.js` | 129 | 0 | 1 | **단축키 표 한 장** + 키 손잡이 등록 |
| 12 | `js/main.js` | 126 | 0 | 0 | 연결과 시작(`loadFruits()`) |

자세한 역할 표(구조 4 README 2절 재료): **`cycle_3/stage1/README_2_파일별역할_js.md`**

늘어난 308줄은 **파일마다의 머리 주석(역할·옮겨 온 원본 줄 범위)과 «가져오는 것/내놓는 것» 칸**입니다.
코드 줄은 한 줄도 늘지 않았습니다(§3 덮개 참고).

---

## 2. 의존 순서 — «위에서 아래로»

`index.html` 의 `<script>` 순서가 곧 의존 방향입니다. 아래 파일은 **위 파일이 만든 것만** 씁니다.

```
state.js   S · API · UI          (전역 셋을 만드는 유일한 파일)
   ↓
api.js     API.get/post · $ · $$ · flash · who · errMsg · escapeHtml · ensureWho
   ↓
view.js    cv · ctx · draw · fitView · zoomToNote · toImg · showView · curTask · tick …
   ↓
mask.js    makeLayer · paintGtLayer · pushUndo · strokeTo · applyPolygon · setTool …
   ↓
boxes.js   loadBoxes · saveBoxes · drawBoxes · boxMouseDown/Move/Up …   ← 시뮬이 글자를 떼어 가는 파일
   ↓
instances.js  loadInstances · setNumMode · numKey · drawNumOverlay · saveInstances …
   ↓
counts.js  confirmVerdict · doAction · renderTodo · renderCntChip · enterConfirm …
   ↓
list.js    loadFruits · loadList · openItem · refreshCard · loadDash …
   ↓
export.js  expOpen (데이터 정리 탭)
   ↓
tour.js    tourOpen · onTourKey
   ↓
keys.js    KEYS 표 + 모든 keydown/keyup 등록
   ↓
main.js    캔버스 마우스 · 위쪽 탭 · 0.2초 tick · loadFruits() 로 시작
```

**되돌아 부르는 자리는 6곳뿐**이고 전부 `UI.이름()` 으로 적어 눈에 보이게 했습니다
(불러올 때가 아니라 **부를 때** 찾습니다):

| 자리 | 무엇을 되돌아 부르나 | 왜 |
|---|---|---|
| `view.js draw()` | `UI.drawNumOverlay()` · `UI.drawErrBoxes()` · `UI.drawBoxes()` | 겹마다 «그려라» 고 부른다. 겹은 아래 파일이다 |
| `view.js showView()` | `UI.loadDash()` | «현황» 탭은 목록 파일에 있다 |
| `view.js setTask()` | `UI.setNumMode()` | ③ 번호 켜기 |
| `view.js tick()` | `UI.renderTodo()` | 하단 한 줄은 counts.js |
| `instances.js revertInstances()` | `UI.openItem()` | 되돌린 뒤 사진을 다시 연다 |
| `boxes.js`·`instances.js` 저장 | `cntSet`·`markTaskConfirmed`·`clearTaskConfirmed` (부를 때 찾는 얇은 껍데기) | ⚠ 아래 |

⚠ 마지막 줄만 «부를 때 찾는 화살표 함수»(`const cntSet = (...a) => UI.cntSet(...a);`)로 두었습니다.
까닭: 그 코드는 **시뮬이 글자 그대로 떼어 가는 구간** 안에 있고 `typeof cntSet === "function"` 가드가
들어 있습니다. 이름이 아예 없으면 브라우저에서도 조용히 건너뛰어 **동작이 바뀝니다**
(저장해도 개수 칸·확정이 안 바뀜). 이름을 두면 브라우저에서는 늘 불리고, node 시뮬은 그 줄을
떼어 가지 않으므로 예전처럼 «없으면 건너뛴다» 가 그대로 유지됩니다.

---

## 3. 어떻게 옮겼나 — 손이 아니라 스크립트

`cycle_3/stage1/split_js.py` 가 **원본의 줄 범위**를 파일마다 적어 두고 그대로 붙입니다.

- **덮개(coverage)**: `app.js` 2,664줄 중 옮긴 줄 2,613 · `ui.js` 1,337줄 중 1,303 ·
  **남은 «글자 있는» 줄 0** (나머지는 빈 줄과 머리 주석·IIFE 껍데기). 한 줄이 두 번 쓰이면 **멈춥니다**.
- **글자를 바꾼 곳은 19군데뿐**이고 전부 `EDITS` 표에 이유와 함께 있습니다:

| 파일 | 곳 | 무엇 |
|---|---:|---|
| `view.js` | 12 | 되돌아 부르는 자리 5곳(`UI.…`) · 후보 확대 순번을 `S.noteZoomAt` 로(3곳) · `let noteZoomAt` 줄 삭제 · `Q` 키 손잡이를 이름 있는 함수로 |
| `tour.js` | 2 | 안내 창 키 손잡이 2개를 이름 있는 함수로(등록은 keys.js) |
| `counts.js` | 2 | `Enter` 키 손잡이를 이름 있는 함수로 |
| `api.js` | 1 | «이름 묻기» 키 손잡이를 이름 있는 함수로 |
| `list.js` | 1 | `noteZoomAt = -1` → `S.noteZoomAt = -1` |
| `instances.js` | 1 | `openItem(…)` → `UI.openItem(…)` |

«이름 있는 함수로» 바꾼 5곳은 **몸통 글자를 한 자도 고치지 않고** 머리만
`window.addEventListener("keydown", (e) => {` → `function onXxxKey(e) {` 로 바꾼 것입니다.
그래야 ① 단축키 등록이 `keys.js` 한 곳에 모이고 ② 회귀 시뮬 `modesim.js` 가 찾는
«`window.addEventListener("keydown", (e) => {`» 가 덩어리 안에 **딱 하나**(주 손잡이)만 남습니다.

- **밖에서 오는 이름 검사**: `check_free_names.py` 가 파일마다 «그 파일 안에서 못 찾는 이름» 을 셉니다.
  처음 돌렸을 때 **진짜 빠진 것 7개**를 잡았습니다(`COL`·`FLAG_KO`·`NUM_WHY`·`noteZoomAt`·`cv`·
  `openItem`·`ensureWho`/`who`). 지금은 **12파일 전부 0개**입니다.

---

## 4. 시뮬 로더 — «이어 붙인 한 덩어리»

`tests/sim/lib/load_bundle.js` (새 파일):

- `index.html` 의 `<script src="/static/…">` 를 **적힌 순서대로** 읽어 이어 붙인 한 덩어리를 돌려줍니다.
  순서를 시험이 따로 적어 두지 않습니다(적어 두면 낡습니다).
- `boxsim.js`·`modesim.js` 는 **두 줄만** 바뀌었습니다(`fs.readFileSync(APP_JS)` → `load_bundle.simSource()`).
  자르는 문구·단정·기대값은 **한 글자도 바꾸지 않았습니다.**
- 스위치: `SIM_SRC=appjs node boxsim.js` 면 예전처럼 `app.js` 한 파일만 읽습니다(옛 로더 보존).
- **쪼개기 전에 먼저 확인**했습니다(01:05): `app.js` 한 파일 판에서도 덩어리 로더로
  boxsim **50/50** · modesim **31/31** · sim **9/9** — 옛 로더와 같은 결과.
- 파일 자리: 처음에 `tests/sim/load_bundle.js` 로 두었더니 `run_all.sh` 의 `sim/*.js` 글롭이
  **그것까지 시험으로 돌려** 묶음이 하나 늘었습니다(기준선 ③ 이 흔들립니다). → `tests/sim/lib/` 로 옮겼습니다.

`tests/sim/sim.js` 는 손대지 않았습니다(원래 `app.js` 를 읽지 않습니다). §7 «찾은 것» 2번 참고.

---

## 5. 관문 결과

### 5-1. 모래상자 `cycle_3/stage1/sandbox`

| 묶음 | 결과 |
|---|---|
| syntax (py_compile · node --check) | 통과 |
| unit u1·u2·u3·u4 | 5/0 · 10/0 · 10/0 · 7/0 |
| **unit u5_js_contract** | **42/0** (쪼개기 전과 같음) · 경고 1 = «최상위 이름 225개» ← u5 의 세는 법이 IIFE 안까지 세기 때문(§6) |
| **unit u7_keys_doc (신설)** | **69/0** — 단축키 표 ↔ `help.html` ↔ 손잡이 코드 |
| **unit u8_js_globals (신설)** | **42/0** — 전역이 정확히 `S`·`API`·`UI` 셋 · 12파일 `node --check` |
| sim boxsim · modesim · sim | **50/0 · 31/0 · 9/0** |
| api t1_api · regress_all | **34/0 · 100/0** |
| merged | (아래 «시각표» 참고) |
| **browser b3_struct3 (신설)** | **29/0** — 14걸음 스크린샷 + 상태 · 콘솔 오류 0 |
| **browser b4_oldcache (신설)** | **11/0** — 옛 index.html 로 들어와도 화면이 산다 |
| 기준선 ①②③⑤ | (아래 «시각표») |

### 5-2. 브라우저 10장 시나리오 — 전후 대조 (진짜 파이어폭스 1366×768)

같은 시나리오를 **쪼개기 전 트리**(`sandbox_before`)와 **쪼갠 트리**(`sandbox`)에서 한 번씩 돌려
걸음마다 ① 스크린샷 ② 상태 JSON(30칸: 도구·모드·상자 수·되돌리기 칸수·배율·하단 한 줄·개수 칸·
레이어 체크·카드 수·패널 보임…)을 남기고 글자까지 대조했습니다.

| 걸음 | 무엇 | 상태 JSON | 스크린샷 |
|---|---|---|---|
| 01 | 복숭아 목록 | 같음 | **바이트 동일** |
| 02 | 사진 열기(`210629-t1-01`) | 같음 | 바이트 동일 |
| 03 | `Q` 보기 전환(원본만) | 같음 | 바이트 동일 |
| 04 | `B` 붓으로 칠하기(저장 안 함) | 같음 | 바이트 동일 |
| 05 | 되돌리기 | 같음 | 바이트 동일 |
| 06 | `D` 차이 보기 | 같음 | 바이트 동일 |
| 07 | `X` 상자 모드 + ✨ 초벌 | 같음 | 바이트 동일 |
| 08 | 상자 하나 그리기 | 같음 | 바이트 동일 |
| 09 | `K` 번호 편집 모드 | 같음 | 바이트 동일 |
| 10 | 오른쪽 패널 펴기 | 같음 | 바이트 동일 |
| 11 | «현황» 탭 | 같음 | **10바이트 다름** = 화면에 찍힌 서버 시각(`#dashtime` 01:19:45 ↔ 01:22:49). 두 그림을 눈으로 대조했습니다 — 그 한 줄 말고는 같습니다 |
| 12 | «데이터 정리» 탭 | 같음 | 바이트 동일 |
| 13 | `?` 첫 방문 안내 | 같음 | 바이트 동일 |
| 90 | **옛 서버**(파이썬만 옛 판) + 새 화면 | 같음 | 바이트 동일 |

`--diff` 결과: **다른 칸 0개**.
스크린샷: `~/ff_shots/st3/before/` · `~/ff_shots/st3/after/` (각 14장).
상태 JSON: `sandbox_before/tests/_out/b3_struct3_before.json` · `sandbox/tests/_out/b3_struct3_after.json`.

### 5-3. 콘솔 오류

`window.onerror` + `unhandledrejection` 를 걸어 걸음마다 셌습니다 — **전·후 모두 0**.
불러올 때 터진 파일이 없는지는 따로 봅니다: **파일 12개마다 «그 파일만 내놓는 이름» 하나**를
브라우저에서 확인(`UI.statusKo`·`UI.flash`·`UI.fitView`·`UI.setTool`·`UI.saveBoxes`·`UI.numKey`·
`UI.doAction`·`UI.openItem`·`window.expOpen`·`UI.tourOpen`·`UI.KEYS`·`S.fruit`) → 12/12.

### 5-4. 옛 서버 가드

옛 파이썬(`_backup_260918_c4_*`) + **새 화면**으로 띄운 서버에서 사진을 열어 하단 한 줄·개수 칸을
대조했습니다 — 전후 같고 콘솔 오류 0. (가드 문구 자체는 `t2_ui.py` 라-1~라-4 가 지킵니다.)


### 5-5. 정본 반영 뒤 관문 (01:42:57~01:51:19 · `logs/final_gate2.log`)

`bash tests/run_all.sh --browser --check-baseline` — **단정 1,102개 · 실패 0개**.

| 묶음 | 통과/실패 |
|---|---|
| syntax 4묶음 | rc 0 |
| unit u1·u2·u3·u4·u5·**u6**·**u7**·**u8** | 5/0 · 10/0 · 10/0 · 8/0 · **42/0** · 24/0 · **69/0** · **42/0** |
| sim boxsim·modesim·sim | **50/0 · 31/0 · 9/0** |
| api t1·regress_all·t3·t4 | 34/0 · 100/0 · 7/0 · 17/0 |
| merged | **536/0** (사이클 1 이 남긴 `F7-c` 도 통과) |
| browser b1_browser · t2_ui | **81/0 · 27/0** |

기준선 대조: **① 0칸 · ② 0칸 · ③ 실패로 세는 것 0개 · ⑤ 6칸**.

> `u6_py_contract`·`t3_login_rate`·`t4_flag`·`app/core/`·`app/api/`·`app/domain/` 은 **구조 사이클 2**
> 가 같은 시각(01:3x)에 정본에 반영한 서버 분리입니다. 제 것이 아닙니다. 두 사이클의 결과가 한 트리에서
> **같이 통과**했다는 뜻이기도 합니다.

### 5-6. 🔴 ⑤ 가 0칸이 될 수 없는 까닭 — 사이클 1 관문 정의의 빈틈

| 칸 | 기준선 | 지금 | 무엇 |
|---|---|---|---|
| `r_page_index/bytes`·`sha256` | 29,900 · f5159131… | 31,724 · 45a680a8… | `GET /` 가 돌려주는 **`index.html` 바이트** |
| `r_page_box/bytes`·`sha256` | 같음 | 같음 | `GET /box` — 같은 `index.html` |
| `r_static_app_js/bytes`·`sha256` | 145,377 · 0f58ea45… | 1,578 · 2674b4bf… | `GET /static/app.js` — 이제 «다리» 18줄 |

사이클 1 의 관문은 «④ 는 당연히 다르고 ①②③⑤ 는 0칸» 이었습니다. 그런데 **⑤ 안에도 정적 파일 지문이
세 개** 들어 있습니다(`r_page_index`·`r_page_box`·`r_static_app_js`). 화면을 고치는 사이클은
**⑤ 를 0칸으로 만들 수 없습니다.** 서버 동작(라우트 응답의 구조·쓰기 뒤 디스크 상태)은 **0칸**입니다.

**제안(고치지 않고 적어만 둡니다)** — 둘 중 하나:
- (가) 그 세 칸을 ⑤ 에서 ④(경고)로 옮긴다 — «정적 파일 지문» 은 한 곳(④)에서만 본다.
- (나) 구조 사이클 5 가 **전체 통과를 확인한 뒤** `--rebaseline` 로 기준선을 새로 뜬다.
  ⚠ `--rebaseline` 은 ①②③④⑤ 를 **통째로** 새로 씁니다. 사이클 2·3 이 둘 다 끝난 뒤에 해야 하고,
  뜨기 전에 «지금 판이 옳다» 를 위 1,102 단정으로 확인해야 합니다. 저는 **뜨지 않았습니다**
  (사이클 2 가 아직 도는 중이었고, 기준선은 두 사이클이 함께 쓰는 자산이기 때문입니다).

### 5-7. 정본 시나리오 재측정 (01:36~01:37)

정본에 반영한 **뒤에도** 같은 14걸음을 돌렸습니다(`--tag after_main`): **29/0 · 상태 다른 칸 0개**.
스크린샷은 14장 중 12장이 바이트까지 같고, 다른 두 장은
`11_dash`(화면에 찍히는 서버 시각)와 `04_brush`(붓질 획의 안티에일리어싱 — 두 그림을 눈으로 대조했습니다.
획의 자리·색·길이가 같고, 상태 JSON 의 `nUndo`·`edDirty` 도 같습니다. 모래상자 판에서는 이 장도
바이트까지 같았습니다 → 드래그 시각이 밀리초 단위로 달라 생기는 차이입니다).

### 5-7b. `style.css`·`help.html`

`help.html` 에는 `<script>` 가 없어 고칠 것이 없었습니다.
`style.css` 는 **주석 세 줄**이 «ui.js tick 이 …» 처럼 이제 없는 파일을 가리켜 자리를 갱신했습니다
(`js/view.js 의 tick` · `js/main.js 맨 아래`). **CSS 규칙은 한 글자도 바뀌지 않았습니다.**
고친 뒤 빠른 관문 재확인: **458 단정 · 실패 0** (01:53 · `logs/final_quick.log`).
이 때문에 ④ 에 `app/static/style.css` 한 칸이 더 생깁니다(경고).

### 5-8. ⚠ 같은 트리에서 관문을 **둘이 동시에** 돌리면 안 됩니다 (01:36 실측)

첫 번째 정본 관문(`final_gate.log`)은 **구조 사이클 2 의 관문과 겹쳐 돌았습니다.** 결과가 엉켰습니다:
`tests/_out/bundles.tsv` 에 두 실행의 줄이 섞여 묶음이 두 번씩 찍히고, `browser/prep_sandbox` 가
**같은 `tests/_sandbox/sb_main`** 을 서로 지우며 `t2_ui` 가 23/4·26/1 로 깨졌습니다.
겹치지 않게 다시 돌린 것이 위 5-5(1,102/0)입니다.
→ **구조 4·5 에 넘기는 규칙: 정본 관문은 한 번에 하나만.** (모래상자는 사이클마다 따로라 괜찮습니다.)

---

## 6. 단축키 «표 한 곳» — 어디까지 했나 (솔직히)

**한 것**: `js/keys.js` 에 표 하나(`KEYS`, 32줄: 키 · 뜻 · 손잡이가 있는 파일 · 그 파일에 반드시 있는 글자)
+ **모든** `keydown`/`keyup` 등록을 이 파일 한 곳으로 모았습니다(다른 파일의 손잡이는 이름 있는 함수로
꺼내 여기서 붙입니다 — 등록 순서는 쪼개기 전과 같습니다).
새 시험 `tests/unit/u7_keys_doc.py` **69항목**이 ① 표 → `help.html` «단축키 한 장» ② 도움말 → 표
③ 표가 적은 파일에 그 글자가 정말 있나 ④ 같은 키가 두 번 있지 않나 를 대조합니다.

**안 한 것(일부러)**: «손잡이가 표를 **읽어서** 갈라진다» 는 식의 표 주도 방식으로 **바꾸지 않았습니다.**
- 이유 1 — 지시서 §5 의 첫 규칙이 «동작을 바꾸지 않는다» 입니다. 그 `switch` 문은 회귀 시뮬
  `modesim.js` **31항목**이 **글자 그대로 떼어 내** 돌리는 코드이고, 분기마다 조건이 다릅니다
  (`S.numMode && numKey(e)` 먼저 · Ctrl 갈래 · `X` 는 번호 모드에서 의미가 바뀜 · `#btn-ai` 가
  꺼져 있으면 `2` 무시 …). 표로 옮기면 그 31항목이 지키던 «모드마다 제 갈래» 규칙을 다시 써야 합니다.
- 이유 2 — 표를 읽는 손잡이는 `modesim` 이 떼어 갈 때 표가 **같이 떼어지지 않아** 시험이 죽습니다.
  살리려면 시뮬에 표를 주입해야 하고, 그것은 «시험이 코드를 따라가는» 방향이 아닙니다.
- 그래서 **진실은 표에 두고, 갈라지면 기계가 잡게** 했습니다(u7 ③번 검사 = 표가 적은 글자가
  그 파일에 정말 있는가). 표 주도 손잡이는 **동작을 바꿔도 되는 사이클**의 후보로 남깁니다.

---

## 7. 찾은 것 (고치지 않고 적어만 둡니다 — 동작 무변경 원칙)

1. **`u5_js_contract.py` 의 «최상위 이름» 세는 법이 낡았습니다.** 줄 맨 앞의 `function|const|let|var`
   를 세는데, 쪼갠 파일들은 IIFE **안**을 들여쓰지 않으므로(그래야 `modesim` 이 `\n}\n` 로 함수를
   자릅니다) 안쪽 이름까지 **225개**로 셉니다. 진짜 전역은 3개입니다. u5 는 사이클 1 의 기준선
   파일이라 **건드리지 않았고**, 대신 괄호 깊이로 세는 `u8_js_globals.py` 를 새로 만들었습니다.
   → 2차·구조 4 가 u5 의 그 칸을 «u8 로 옮겼다» 고 적거나, 세는 법을 깊이 기준으로 고치면 됩니다.
2. **`tests/sim/sim.js` 의 «C. 드래그 이동거리» 표는 지금 코드와 다른 규칙을 굳히고 있습니다.**
   sim.js 의 `simMove()` 는 **손으로 옮겨 적은 사본**인데, 사건마다 `drag.px` 를 갱신하고 반올림을
   누적합니다 — 그래서 2x 는 두 배, 3x 이상은 0px 이 나옵니다. 그런데 **지금 `boxes.js boxMouseMove()`
   는 처음 잡은 자리에서의 «전체» 이동량으로 계산**합니다(1459~1465줄 주석 «한 칸마다 반올림해서
   더하면 …»). 즉 그 표는 **이미 고쳐진 옛 결함**을 굳히고 있습니다(cycle_1 2차 §2-4 는 이것을
   «지금 동작» 이라고 적었습니다). 확인은 `boxsim.js` 로 진짜 함수를 떼어 재면 됩니다.
   이번 사이클에서는 **아무것도 바꾸지 않았습니다**(sim 9/9 그대로).
3. `window.` 로 오가는 옛 연결선 5개(`zoomToNote`·`SEEDSRCKO`·`seedSrcKo`·`renderCntChip`·`expOpen`)는
   그대로 두었습니다. 부르는 쪽(`ui.js` 안에서 `window.` 로 찾던 자리)까지 같이 고쳐야 하는데,
   그 자리들은 «서버가 옛 판이면» 갈래와 얽혀 있어 동작 무변경 폭을 넘습니다. u8 이 목록을 경고로 찍습니다.
4. `instances.js` 가 **874줄**로 제일 큽니다(순수 함수 INSTCORE 232줄 포함). 파일 수를 10~12 로
   묶어 두라는 지시 때문에 더 쪼개지 않았습니다. 더 쪼갠다면 `instcore.js`(DOM 을 안 쓰는 순수 함수)가
   자연스러운 경계입니다.

---

## 8. 정본 반영 절차 — «Ctrl+F5 전에 깨지지 않게»

### 왜 조심해야 하나
정적 파일은 **서버를 다시 켜지 않아도 그 자리에서 바로 나갑니다.** 실서버(5111, PID 1467097)를
지금 쓰고 있는 사람의 브라우저는 아직 **옛 `index.html`** 을 들고 있을 수 있고, 그 옛 index 는
`/static/app.js` 와 `/static/ui.js` 두 개만 부릅니다.

### 무엇을 했나 — 옛 `app.js` 를 «다리» 로 남겼습니다
- `app/static/app.js` (18줄): 문서를 **읽는 중일 때만**(`document.readyState === "loading"`)
  `document.write` 로 새 12파일을 **순서대로** 불러 줍니다.
- `app/static/ui.js` (10줄): 안내만. (여기서 또 부르면 두 번 실립니다.)
- 새 `index.html` 로 들어온 사람은 `app.js` 를 아예 부르지 않으므로 **두 번 실릴 일이 없습니다.**

### 실측 (`tests/browser/b4_oldcache.py` · 진짜 파이어폭스 · 11/0)
모래상자 안에서 «지금 index 의 `<script>` 칸만 옛 두 줄로 바꾼 쪽» 을 만들어 열었습니다
(= 캐시에 옛 index 가 있는 사람과 같은 상황).

| 확인 | 결과 |
|---|---|
| 화면이 산다(과일 칸이 채워진다) | ✔ |
| 전역 셋이 다 있다 = 다리가 12파일을 순서대로 불렀다 | ✔ |
| 다리가 부른 파일이 살아 있다(mask·boxes·instances·keys) | ✔ |
| 사진이 열린다 · 단축키가 듣는다(`X`) | ✔ |
| 콘솔 오류 | **0** |
| 새 index 에서는 옛 `app.js` 를 부르지 않는다 | ✔ (script 0개) |

스크린샷: `~/ff_shots/st3/oldcache/old_index_bridge.png`

### 반영 순서 (이 차례를 지킵니다 — 어느 순간에도 화면이 죽지 않습니다)
1. `app/static/js/` 12파일 **추가** — 아무도 부르지 않으므로 화면에 영향 0
2. `app/static/ui.js` → 안내 10줄 (이 순간 옛 index 는 «옛 app.js + 빈 ui.js» = 화면은 살아 있고
   덧칠(하단 한 줄·칩)만 잠깐 빠집니다)
3. `app/static/app.js` → 다리 18줄 (이때부터 옛 index 도 새 12파일로 돕니다)
4. **맨 마지막에** `app/static/index.html` (2·3·4 는 한 명령으로 잇달아 — 창은 1초 미만)
5. 반영 직후 정본에서 관문을 한 번 더

> ⚠ 다리는 한시적입니다. 모두가 한 번씩 새로고침한 뒤(며칠 뒤) `app.js`·`ui.js` 를 지워도 됩니다.
> 그때 `u8_js_globals.py` 의 «옛 파일» 검사는 스스로 경고로 바뀝니다(그렇게 적어 두었습니다).

---

## 9. 2차 검수가 그대로 재현할 명령

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
C=$T/cycles/260920_structure/cycle_3/stage1

# ① 쪼개기를 «다시» 해 본다 — 원본(before/)에서 같은 12파일이 나오는가(글자까지)
python3 $C/split_js.py --src $C/before --out /tmp/js_again
diff -r /tmp/js_again $T/app/static/js && echo "같음"

# ② 파일마다 «밖에서 오는 이름» 0 인가
python3 $C/check_free_names.py $T/app/static/js

# ③ 빠른 관문 (약 25초)
bash $T/tests/run_all.sh --no-merged --only=syntax,unit,sim,api

# ④ 시뮬을 옛 로더로도 돌려 본다(스위치가 살아 있는가)
cd $T/tests/sim && SIM_SRC=appjs node boxsim.js | tail -1   # ← 옛 app.js 는 이제 «다리» 라 0개 구간을 못 찾는다(정상)
cd $T/tests/sim && node boxsim.js | tail -1                 # ← 덩어리: 50/50

# ⑤ 진짜 브라우저 (1366×768 · 스크린샷 ~/ff_shots/st3/)
cd $T && TESTS_SHOTS=$HOME/ff_shots/st3 python3 tests/browser/b3_struct3.py --tag after2
cd $T && TESTS_SHOTS=$HOME/ff_shots/st3 python3 tests/browser/b4_oldcache.py
python3 tests/browser/b3_struct3.py --diff \
  $C/sandbox_before/tests/_out/b3_struct3_before.json $T/tests/_out/b3_struct3_after2.json

# ⑥ 전체 관문
bash $T/tests/run_all.sh --browser --check-baseline
```

⚠ ④의 `SIM_SRC=appjs` 는 **반영 뒤에는 실패하는 것이 정상**입니다(옛 `app.js` 가 다리 18줄이라
구간이 없습니다). 옛 로더를 진짜로 써 보려면 `before/app.js` 를 가리키게 해야 합니다 —
스위치는 «되돌릴 길» 로 남겨 둔 것이고, 기본 길은 덩어리입니다.

---

## 10. 산출물 목록

| 무엇 | 어디 |
|---|---|
| 쪼개기 전 원본 사본 | `cycle_3/stage1/before/` (`app.js`·`ui.js`·`index.html`·`style.css`·`help.html` + 손댄 시험 3개·`paths.js`) |
| 쪼개는 스크립트(재현용) | `cycle_3/stage1/split_js.py` |
| 밖에서 오는 이름 검사 | `cycle_3/stage1/check_free_names.py` |
| 모래상자(쪼갠 판) | `cycle_3/stage1/sandbox/` |
| 모래상자(쪼개기 전 판) | `cycle_3/stage1/sandbox_before/` |
| 새 화면 코드 | `app/static/js/*.js` 12개 |
| 시뮬 로더 | `tests/sim/lib/load_bundle.js` (+ `boxsim.js`·`modesim.js` 두 줄) |
| 새 시험 | `tests/unit/u7_keys_doc.py` · `tests/unit/u8_js_globals.py` · `tests/browser/b3_struct3.py` · `tests/browser/b4_oldcache.py` |
| 규칙표(JS 칸 채운 사본) | `cycle_3/stage1/README_5_규칙표_js_after.md` |
| 파일별 역할 표 | `cycle_3/stage1/README_2_파일별역할_js.md` |
| 스크린샷 | `~/ff_shots/st3/{before,after,oldcache}/` |
| 로그 | `cycle_3/stage1/logs/` |

---

## 11. 시각표 (서버 `date` 실측)

| 시각 | 무엇 |
|---|---|
| 00:39 | 시작 · 시작 관문 164/0 |
| 00:50 | `before/` 사본 · 모래상자 만들기 |
| 01:05 | **시뮬 로더 먼저** — 쪼개기 전 `app.js` 한 파일에서도 덩어리 로더로 50/31/9 확인 |
| 01:06 | 12파일로 쪼갬(스크립트) · 문법 통과 |
| 01:07 | `index.html` 새 목록 · 옛 `app.js` 다리 · `ui.js` 안내 |
| 01:08 | u5 42/0 · u7 69/0 · u8 42/0 |
| 01:19 | 브라우저 시나리오 **전**(sandbox_before) 14걸음 |
| 01:22 | 브라우저 시나리오 **후**(sandbox) 14걸음 · 다른 칸 0 · 스크린샷 13/14 바이트 동일 |
| 01:26 | 옛 캐시 다리 시험 11/0 |
| 01:27~01:35 | 모래상자 전체 관문 `--browser --check-baseline` — **1,053 단정 · 실패 0** (①② 0칸 · ⑤ 6칸 = 정적 지문) |
| 01:36:05 | 정본 `app/static/` 이 `before/` 사본과 **같은지** sha256 대조(5파일 전부 같음 = 그 사이 아무도 안 고침) |
| 01:36:16 | **정본 반영** — js 12파일 → 시험 도구 → `ui.js` 안내 → `app.js` 다리 → `index.html` (한 명령 · 1초 미만) |
| 01:37:34 | 정본에서 시나리오 재측정 29/0 · 다른 칸 0 |
| 01:38 | 정본에서 다리 시험 11/0 |
| 01:42 | 첫 정본 관문이 **사이클 2 관문과 겹쳐** 엉킴(5-8) |
| 01:42:57~01:51:19 | 정본 관문 다시 — **1,102 단정 · 실패 0** · ①② 0칸 · ③ 실패 0 · ⑤ 6칸(정적 지문) |
| 01:53 | `style.css` 주석 3줄의 옛 파일 이름 갱신 → 빠른 관문 **458/0** |


---

## 12. 2차에게 넘기는 «치울 것» 한 줄

제가 01:03 에 **경로를 잘못 쳐서** 빈 폴더 하나를 만들었습니다(툴 폴더가 아니라 이름이 한 글자 다릅니다).
삭제는 규칙상 제가 하지 않습니다 — 사람이 지워 주세요:

```
rmdir 후:  /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툍/
파일:      같은 폴더의 cycle3_tmp.txt (4바이트, 아무 뜻 없음)
```

그리고 모래상자에만 남은 것: `cycle_3/stage1/sandbox/app/static/index_oldcache_test.html`
(처음에 손으로 만든 시험용 옛 index — 지금은 `b4_oldcache.py` 가 **모래상자 안에서 스스로** 만들므로
필요 없습니다. **정본 `app/static/` 에는 없습니다** — 반영 목록에 넣지 않았습니다).
