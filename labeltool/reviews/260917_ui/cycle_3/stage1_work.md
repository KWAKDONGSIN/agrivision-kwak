작성: 2026-09-17

# UI 개선 사이클 3 · 1차 작업 (Opus 5)

대상 `T = /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴`
과제 정의 `T/cycles/260917_ui/cycle_2/stage3_final.md` ③ 1~7 · 근거 `cycle_2/stage2_review.md` §6
**추가 지시(총괄 Fable)**: 데이터 사이클2 1단계 `T/cycles/260917_ab/cycle_2/stage1_report.md` 의 **P1~P4** 를 같은 사이클에서 고칠 것.

이번 사이클은 **서버 수정 허용**. 백업은 전부 `_backup_260917_ui5_<파일명>`.
개발·시험은 **모래상자 5133**(앞 사이클의 `cycle_1/stage2/sandbox/` 재사용, `app/` 는 현재 `T/app` 을 다시 복사,
보안 관련 값·설정 세부는 공개본에서 생략했습니다.

**단정 합계: 150개 전부 통과** (`t_api` 34 · `t_ab` 35 · `t_counts` 19 · `t_ui` 35 · `t_layout` 12 · `t_live` 15)
\+ 회귀 6종(31/31 · 50/50 포함) + 브라우저 스크린샷 32장.

---

## 1. 항목별 한 줄 (①~⑦ + P1~P4)

| # | 한 일 | 결과 |
|---|---|---|
| ① 중복 묶음을 한 번에 | `/api/item` 에 `dup_rep`·`dup_member_status` 추가 · 편집 화면 오른쪽에 **구성원 썸네일 줄**(대표 «남김» · 지금 사진 강조 · 눌러서 이동) · **«이 묶음: 대표만 남기고 제외»** + **«방금 제외한 것 되돌리기»**(새 API 2개) | ✅ 전부 |
| ② 의심 종류별 빠른 단추 | `/api/list?flag=<종류>` + 응답의 `flag_counts` · 목록 둘째 줄에 **한국어 이름 + 장수** 단추(그 과일에 있는 종류만) | ✅ 전부 |
| ③ 카운팅 개수 화면 | `/api/instance_stats` + **디스크 캐시**(`app/cache/instance_counts/`) · 진행 현황 탭 표(합계·평균·최대·«지금 세기» + 진행) · 목록 카드 «N개» 딱지 | ✅ 전부 |
| ④ 목록의 «제외» 가 안 보임 | 카드에 상태 딱지(제외·문제 있음·수정함·OK) 추가 | ✅ |
| ⑤ M2 1100×700 두 겹 | 좁은 창에서 판정 줄 한 겹 · 위 두 줄은 한 줄로 자르고 풍선말 · **캔버스 47.1% → 57.5%**(합격선 55%) | ✅ 합격 |
| ⑥ M3·M4·M5·M6·M7 | 문서 3문장·옛 단추 이름 4곳·`@media` 1400→1180·`isComposing`·`TH_ASOF`+콘솔 경고 | ✅ 전부 |
| ⑦ 사용성 | 범례를 눌러 레이어 껐다 켜기 ✅ / **세로 사진 검은 벌판은 손대지 않음**(이미 캔버스 높이의 97% 를 씀 — §7) | ✅ / 의도적 보류 |
| P1 되돌리기가 3차 판정을 지움 | `pick_representative` 가 **flag 를 건너뛰지 않음**(exclude 만) · 일괄 제외에 `src` 표식 · 되돌리기는 **그 표식만** · 일괄 제외가 사람 판정을 덮어쓰지 않음 | ✅ 35/35 |
| P2 번호 저장이 판정·메모를 덮어씀 | 저장이 `exclude`·`flag` 를 지키고 메모를 앞에 붙이며 `prev` 보관 · 되돌리기가 `prev` 로 복원 | ✅ |
| P3 정리된 묶음의 대표에게 «4 제외» | 대표에게는 «이 묶음의 대표(남길 장)입니다 — 나머지 N장은 이미 제외됐습니다» (경고색 아님) | ✅ |
| P4 flag 메모의 후보 좌표가 안 보임 | 메모에서 좌표를 읽어 **노란 점선 상자** + 할 일 줄에 «노란 점선 = 라벨 안 된 열매 후보 N곳» + flag 사유 앞부분 | ✅ |

---

## 2. 새 API 명세 (요청·응답 예)

### 2-1. `GET /api/list` — 인자 `flag` 추가 · 응답 칸 3개 추가 (②③)
```
GET /api/list?fruit=apple&flag=filled_blob&page_size=5
→ {"fruit":"apple","total":117, ...,
   "flag":"filled_blob",
   "flag_counts":{"merged_blob":833,"filled_blob":117,"fg_too_high":10,"fg_too_low":10,"single_convex_blob":6},
   "items":[{"stem":"...", "status":"exclude", ..., "dup_group":12, "has_fixed":false, "n_inst":40}]}
```
- `flag` 를 안 주면 **예전과 완전히 같다**(실측: 사과 1,001장 그대로).
- `flag_counts` 는 그 과일의 **데이터셋 안 사진만** 센다(진행 현황 표와 같은 규칙). 없는 종류는 안 나온다.
- `n_inst` 는 **캐시에 있을 때만** 숫자, 없으면 `null`(새로 세지 않는다 → 목록이 느려지지 않는다).

### 2-2. `GET /api/item` — 칸 2개 추가 (①)
```
GET /api/item?fruit=apple&stem=20150919_174730_image241
→ { ...전과 같은 칸 전부...,
    "dup_group":37, "dup_members":["...241","...236","...246","...251"],
    "dup_rep":"20150919_174730_image241",
    "dup_member_status":["unreviewed","exclude","exclude","exclude"] }
```
`dup_rep` 은 `dupes.representative_map` 과 **같은 함수**(`pick_representative`)로 고른다 — 화면·내보내기가 다른 대표를 볼 수 없다.

### 2-3. `POST /api/exclude_group` (①, 새 API)
```
{"fruit":"apple","stem":"<이 묶음 안의 아무 사진>","by":"곽동신"}
→ {"ok":true,"group":37,"rep":"...241","members":[...4장...],
   "changed":["...246","...251"],
   "skipped":[{"stem":"...236","why":"ok"}]}          # 사람이 이미 판정한 장·데이터셋 밖 장
```
- 대표는 절대 제외하지 않는다. **`unreviewed` 인 장만** 바꾼다(ok·fixed·flag·exclude 는 `skipped`).
- 메모는 기존 3차 판정과 **같은 형식** «중복: \<대표stem\>», 표식 `src:"dup_group"`.
- 묶음이 아닌 사진 → `400` + 한국어 안내, 없는 stem → `404`.

### 2-4. `POST /api/undo_exclude_group` (①, 새 API)
```
{"fruit":"apple","stems":["...246","...251"],"by":"곽동신"}
→ {"ok":true,"changed":["...246","...251"],"kept":[]}
```
네 가지가 **모두** 맞는 것만 되돌린다: ① 지금 `exclude` ② 메모가 «중복: » ③ `src=="dup_group"` ④ `by` 가 같다.
→ **3차 판정(by «AI 3회 검수…», 표식 없음)이 넣은 제외는 이 단추로 지워지지 않는다.**

### 2-5. `GET /api/instance_stats` (③, 새 API)
```
GET /api/instance_stats                      # 캐시만 읽는다(실측 0.19~0.22초)
→ {"ok":true,"at":"2026-09-17 23:47:20","started":false,
   "stats":{"apple":{"n_images":1001,"n_counted":1001,"n_cached":1001,
                     "n_instances":40468,"avg":40.4,"max":123,"stale":0}, ...},
   "running":{}}

GET /api/instance_stats?fruit=apple&start=1   # 낡은 장만 뒤에서 다시 센다
→ {..., "started":true, "running":{"apple":{"done":18,"total":100,"sec":3.2}}}
```
- `/api/boxes_stats` 와 같은 모양(`{과일: {...}}`)이다.
- 개수는 `instances.load_inst()` 로 센다 → 편집 화면의 «번호 N개» 와 **같은 숫자**(실측으로 확인, §4).

### 2-6. `GET /api/duplicate_preview` — 칸 4개 추가 (P1)
`kept_human`(사람이 이미 판정해 안 건드릴 장수) · `n_will_change`(정말 바뀔 장수) ·
`n_undoable`(이 단추가 넣은 제외 = 되돌릴 수 있는 장수) · `n_other_excludes`(다른 출처의 제외).
확인창이 «314장 중 **0장**을 제외합니다 / 되돌릴 것 0장, 다른 출처 314장은 그대로» 라고 정확히 말하게 하려는 값이다.

### 2-7. `status.json` 에 늘어난 칸 (형식은 그대로, **추가만**)
| 칸 | 뜻 | 지우는 때 |
|---|---|---|
| `src` | 이 «제외» 를 어느 단추가 넣었나 — `dup_bulk`(진행 현황 일괄) · `dup_group`(편집 화면 묶음) | 그 단추의 되돌리기가 되돌릴 때 |
| `prev` | 번호 편집 «전» 의 `{status, note, by}` | «번호 되돌리기» 가 복원한 뒤 |

---

## 3. 파일별 줄 수 (+추가 / −삭제)

| 파일 | 전 → 후 | + | − | 무엇 |
|---|---|---|---|---|
| `app/server.py` | 1,117 → 1,269 | 167 | 15 | `flag` 거르기·`flag_counts`·`n_inst`·`dup_rep`·묶음 제외/되돌리기 2개·일괄 제외 P1 수정 |
| `app/instances.py` | 297 → 508 | 216 | 5 | 개수 집계 캐시(모듈 함수 12개)·`/api/instance_stats`·P2 저장/되돌리기 |
| `app/dupes.py` | 107 → 113 | 10 | 4 | P1 `pick_representative`(flag 를 건너뛰지 않음) |
| `app/static/app.js` | 2,019 → 2,197 | 182 | 4 | 묶음 썸네일 줄·묶음 제외/되돌리기·상태/개수 딱지·개수 표·P4 점선 상자·확인창 문구 |
| `app/static/ui.js` | 349 → 451 | 125 | 23 | 종류별 단추·P3 대표 문구·P4 안내·할 일 줄 줄이기·`isComposing`·`TH_ASOF`·범례 누르기 |
| `app/static/index.html` | 274 → 286 | 12 | 0 | 종류 단추 자리·묶음 칸 |
| `app/static/style.css` | 233 → 281 | 50 | 2 | `@media` 1180 새 블록·썸네일 줄·딱지 색·범례 누르기 |
| `app/static/help.html` | 240 → 271 | 35 | 4 | M3 문장 2곳 정정·새 기능 3절·1100px 하한 |
| `app/README.md` | 399 → 446 | 56 | 9 | M3·M4 정정·다섯 창/하한·P1 규칙·12절(카운팅)·13절(새 API) |

합계 **+853 / −66**. 외부 라이브러리 0개, 새 파이썬 패키지 0개.

---

## 4. 실측

### 4-1. 열매 개수 집계(③)
| 무엇 | 값 |
|---|---|
| **첫 계산 — 사과 1,001장** | **188.6초** (장당 0.188초) · 열매 **40,468개** · 장당 평균 **40.4** · 최대 **123** |
| **첫 계산 — 블루베리 1,195장** | **209.5초** (장당 0.175초) · 열매 **45,124개** · 장당 평균 **37.8** · 최대 **204** |
| 캐시 적중(한 과일) | **0.085 ~ 0.099초** (3회) |
| 캐시 적중(네 과일 한꺼번에) | **0.187 ~ 0.223초** · 실서버 **0.196초** |
| 1장만 다시 셀 때 | **0.1초** |
| 100장 다시 셀 때 | **17.7초** (장당 0.177초) |
| 캐시 파일 크기 | 사과 62KB · 블루베리 75KB (`app/cache/instance_counts/*.json`, 합계 144KB) |

**딴 데서 온 숫자와 대조**: 사과 1,001장의 개수가 `data/apple/inspection.csv` 의 `gt_instances` 칸과
**1,001장 전부 일치**(작업자 B 가 따로 만든 파일이다). 블루베리는 대조할 칸이 없다.

**캐시 무효화 증명**(`t_counts.py`, 모래상자):
- 번호 파일(`instances_fixed/`)에 번호 하나를 지운 판을 쓰면 → `stale` 이 **딱 1장**, 다시 센 뒤 그 장만 95→94,
  **다른 1,000장의 캐시 줄은 한 글자도 안 바뀜**, 과일 합계도 딱 1 줄어듦(40,468→40,467). 파일을 지우면 95로 복귀.
- 이진 마스크(`masks_fixed/`)만 바꿔도 → `stale` 1장, 잘린 번호만큼 95→94, 그 값이 `/api/instance_info` 의
  «번호 N개» 와 **같다**(화면 94 · 집계 94). 되돌리면 95.
- 캐시에서 100장을 빼고 «지금 세기» → `running {done:18, total:100, sec:3.2}` 가 실제로 보이고,
  끝난 뒤 캐시가 **처음과 완전히 동일**.

### 4-2. 1100×700 배치(⑤ M2) — 같은 스크립트로 전/후
`t_layout.py` (모래상자에 «고치기 전» 판 정적 파일을 잠깐 넣고 한 번, 고친 판으로 한 번)

| 창 | 작업 | 판정 단추 | 판정 줄 | 캔버스 % (전 → 후) |
|---|---|---|---|---|
| **1100×700** | ① 마스크 | 5/5 → 5/5 | **2겹 103px → 1겹 65px** | **56.6% → 62.7%** |
| **1100×700** | ② 상자 | 5/5 → 5/5 | 2겹 → 1겹 | **52.3% → 62.7%** |
| **1100×700** | ③ 번호 | 5/5 → 5/5 | 2겹 → 1겹 | **47.1% → 57.5%** ✅(합격선 55%) |
| 1280×720 | 세 작업 | 5/5 | 1겹 | 63.6% → 60.8% (단추 설명이 살아나 4px 낮아짐) |
| 1366×768 | 세 작업 | 5/5 | 1겹 | 66.2% → 63.5% (〃) |
| 1920×1080 | 세 작업 | 5/5 | 1겹 | 76.7% → 76.7% |

가로 넘침 0 · 판정 줄이 캔버스를 덮는 넓이 0 — 12벌 전부. **실서버(5111)에서도 12/12 같은 값**(`t_layout_live.log`).
M5 확인: 단추 «한 줄 설명» 이 1280·1366 에서 **보이게** 됐고(전에는 1920 에서만), 1100 에서만 접힌다.

### 4-3. 묶음 제외 왕복(①)
| 무엇 | 값 |
|---|---|
| `/api/item`(대표·구성원 상태 포함) | **0.004초** |
| `POST /api/exclude_group` 3장 | **0.014초** |
| `POST /api/undo_exclude_group` 3장 | **0.023초** |
| 브라우저에서 «누르고 → 썸네일이 바뀔 때까지» | 1초 안(확인창 포함, 눈으로 확인) |

### 4-4. 그 밖
- 한글 검색(M6): 조합 중 `/api/list` **0회**(전에는 자모마다 1회, 최대 7회), 조합이 끝나면 **1회**.
- 실서버 재시작 뒤 `/api/list?fruit=apple` 첫 응답에 `flag_counts`·`n_inst` 가 실려 온다(§9).

---

## 5. 시험한 조작 / 안 한 조작

### 시험한 것 (전부 모래상자 5133, 표시된 것만 실서버 읽기)
| 조작 | 스크립트 | 단정 |
|---|---|---|
| `flag` 거르기 5종 × (장수·내용 대조) · 없는 종류 · 인자 없음 | `t_api.py` | 15 |
| `dup_rep`·`dup_member_status` 모양 | `t_api.py` | 3 |
| 묶음 제외/되돌리기(대표 보호·사람 판정 보호·메모 형식·남의 제외 보호·400/404) | `t_api.py` | 16 |
| P1 대표 고르기 — **고치기 전 판(`_backup_260917_ui5_dupes.py`)과 나란히** | `t_ab.py` | 5 |
| P1 일괄 제외 → 되돌리기 → 다시 일괄 제외 · **status.json 전후 diff 0** | `t_ab.py` | 7 |
| P1 이 단추가 넣은 것만 되돌아옴(2장 넣고 2장만) | `t_ab.py` | 4 |
| P2 번호 저장/되돌리기 × (flag·exclude) — 판정·메모·`prev`·내보내기 포함 여부 | `t_ab.py` | 19 |
| 캐시 적중·무효화(번호 파일/이진 마스크)·진행 표시 | `t_counts.py` | 19 |
| 목록 상태 딱지·개수 딱지 | `t_ui.py`(브라우저) | 3 |
| 종류 단추(한국어·장수 일치·켜짐/풀림) | `t_ui.py` | 6 |
| P4 노란 점선 안내·flag 사유 | `t_ui.py` | 2 |
| P3 대표 문구·경고색 아님·썸네일 흐림 | `t_ui.py` | 4 |
| 묶음 썸네일(대표 표시·강조·눌러 이동) + **확인창 글자 읽고 확인 누르기** + 되돌리기 | `t_ui.py` | 10 |
| 범례 눌러 레이어 껐다 켜기(꺼진 줄 유지·다른 레이어 불변) | `t_ui.py` | 5 |
| M6 한글 조합(가짜 IME 이벤트 + `fetch` 세기) | `t_ui.py` | 3 |
| 진행 현황 탭 개수 표 | `t_ui.py` | 2 |
| 다섯 창 × 세 작업 배치(전/후) | `t_layout.py` | 12+12 |
| **실서버 읽기 전용 확인**(네 과일·게이트·새 API·캐시) | `t_live.py` | 15 |
| 회귀 6종 | 아래 §6 | — |

### 안 한 것 (그리고 왜)
| 안 한 것 | 이유 |
|---|---|
| **실서버에서 판정·저장·묶음 제외 단추 누르기** | 지시. 공용 `data/` 가 바뀐다. 지문으로 안 건드렸음을 보였다(§8) |
| 포도·복숭아 열매 개수 세기 | 번호가 없어 전부 «번호 없음» 이다(표에 0으로 나오고 «세기» 단추는 보인다). 2,531장 × 0.2초를 쓸 이유가 없다 |
| 실서버 캐시를 «세기» 단추로 채우기 | 재시작 전에 **오프라인으로 미리 채웠다**(`warm_counts.py`, `app/cache/` 에만 씀) → 사람이 첫날부터 바로 본다 |
| 크롬·엣지·모바일 | 서버에 파이어폭스뿐. 사이클 5 사람 체크리스트로 |
| 여러 사람이 동시에 같은 묶음을 제외할 때 | `status:<과일>` 자물쇠 안에서 읽고 쓰지만 **동시 시험은 안 했다** |
| 세로 사진 «검은 벌판» 줄이기 | §7 — 이미 꽉 맞춰 그리고 있어 손대지 말라는 지시를 따랐다 |
| `scripts/ff.py` 고치기 | 금지. 확인창 세션은 내 시험에서 `Browser` 를 상속해 해결했다(ab사이클2 P7 도 그대로 둠) |

---

## 6. 회귀 (전과 같이 통과)

```
node --check app/static/app.js                                   ✅
node --check app/static/ui.js                                    ✅
node cycles/260917_신기능/cycle_1/stage1/sim.js                   ✅ (같은 숫자)
node cycles/260917_신기능/cycle_2/stage2/modesim.js               ✅ 31/31
node cycles/260917_신기능/cycle_2/stage1_client/boxsim.js          ✅ 50/50
python app/boxes.py                                              ✅ 자체 점검 통과
python cycles/260917_신기능/cycle_5/stage1/live_c5.py (실서버 읽기)  ✅ 실패 0개 (16항목)
```
node `v22.23.2`(`/home/kds0206/.local/node22/bin`) · 파이썬 `/home/kds0206/.conda/envs/kwak/bin/python`.
**시험 파일은 한 줄도 고치지 않았습니다.**

---

## 7. 가정 (갈림길에서 고른 것)

1. **P1 의 고칠 안은 «②+③»** — 총괄 지시대로 `duplicates.json` 을 **안 고치고**(P5) 코드로만 해결했다.
   ② `pick_representative` 가 flag 를 건너뛰지 않게 · ③ 되돌리기는 자기가 넣은 것만.
   ①(파일에 `rep` 칸 명시)은 공용 데이터 파일을 고쳐야 해서 **안 했다** — 총괄의 데이터 v2 몫으로 남긴다.
2. **«누가 넣었나» 는 `by` 가 아니라 `src` 표식으로 구분**했다. 메모 형식이 3차 판정과 같고(«중복: …»),
   `by` 는 사람이 아무 이름이나 적을 수 있어 «AI 3회 검수» 와 우연히 같아질 수 있기 때문이다.
   표식이 없는 옛 항목은 **어떤 되돌리기도 건드리지 않는다**(가장 안전한 쪽으로 기울였다).
3. **번호 저장이 `exclude`·`flag` 를 지킨다**(`ok`·`fixed`·`unreviewed` 는 전처럼 `fixed` 가 된다).
   «이 사진을 쓸지 말지» 는 판정이고 번호 편집은 내용 수정이라, 내용 수정이 판정을 뒤집지 않는 쪽으로 봤다.
4. **집계는 «지금 세기» 를 눌러야 시작**한다(화면을 열자마자 7분짜리 일이 돌지 않게). 대신 실서버 캐시는
   내가 미리 채워 두었으므로 사람은 «다 셌습니다» 만 본다.
5. **범례는 꺼진 줄도 회색으로 남긴다.** 꺼지면서 줄이 사라지면 다시 켤 자리가 없어진다.
   대신 범례 칸이 늘 4~5줄이 된다(1100px 에서 사진의 3.8% 를 덮던 것이 조금 늘어난다 — §10 흠).
6. **⑦ «세로 사진 양옆 검은 벌판» 은 손대지 않았다.** `app.js fitView()` 가
   `min(캔버스폭/W, 캔버스높이/H) × 0.97` 로 이미 **캔버스 높이의 97%** 를 쓴다 — 세로 사진은 이미 꽉 찼고,
   검은 벌판은 «세로 사진 : 가로로 넓은 칸» 이라는 비율 차이 그 자체다(1366px·1080×1920 사진 기준
   그림 폭은 칸의 약 22% — **계산값, 실측 아님**). 옆 패널 폭을 그대로 두라는 조건에서 이것을 줄이려면
   캔버스를 세로로 더 키우는 수밖에 없는데, 그건 ⑤ 에서 이미 한 일이다(1100px 에서 +10%p).
7. 종류 이름의 한국어는 내가 지었다(`merged_blob` = «알끼리 붙음» 등 6가지). 영어 원래 이름은 **풍선말**에 남겼다.

---

## 8. 공용 데이터·원본을 안 건드렸다는 증거

- 공용 `T/data/` : 파일 **7,395개**, `data/apple/status.json` **22:22** · `data/blueberry/status.json` **22:24**
  (3차 판정이 쓴 시각 그대로 — 내 작업 전후 안 바뀜). 「경로+크기」 목록 md5 `b788254ef41938146be05e2964f2ce78`.
- 실서버에서 누른 것: **GET 뿐**(`/api/health`·`/api/fruits`·`/api/list`·`/api/item`·`/api/instance_stats`·
  `/api/duplicate_preview`·`/login` 화면·브라우저로 목록·사진 열기). 판정·저장·묶음 제외·내보내기는 **한 번도 안 눌렀다**.
- 쓴 곳: **모래상자 `cycles/260917_ui/cycle_1/stage2/sandbox/`** 와 **`T/app/cache/instance_counts/`**(캐시 2파일) 뿐.
- 모래상자 `data/apple/status.json` 은 시험이 끝난 뒤 **exclude 314 · flag 68 · `src` 0 · `prev` 0** 으로
  3차 판정 상태 그대로다(시험이 만든 흔적을 스스로 되돌린다).
- 원본 데이터셋(`datasets_resized_2mp`·`datasets_reviewed_260916`)은 **읽기만** 했다.
- `T/inspect/` · `T/cycles/260917_ab/` 는 **읽기만** 했다(보고서 1개).

---

## 9. 실서버 반영

1. `app/logs/server.log` 끝 확인 — 최근 저장(POST) **0건**(마지막 활동은 23:42 의 내 읽기 전용 시험).
2. `bash app/run.sh restart` → **2026-09-17 23:47:00 · 옛 PID 3326081 종료 · 새 PID 3847740** (포트 5111).
3. 재시작 뒤 확인(`t_live.py`, 읽기 전용) **15/15**:
   - 네 과일 그대로 열림 — 복숭아 125 · 포도 2,406 · 사과 1,001 · 블루베리 1,195
   - 사과 제외 314 · 문제 있음 68 / 블루베리 제외 71 · 문제 있음 6 **(3차 판정 그대로)**
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
   - 새 API 전부 응답: `flag_counts` · `flag=` 거르기 117장 · `n_inst` · `dup_rep`+구성원 상태 ·
     `/api/instance_stats`(사과 40,468 · 블루베리 45,124 · 다시 셀 것 0)
   - `duplicate_preview` 가 «되돌릴 것 0장 · 다른 출처 314장» 이라고 답함(P1 보호가 살아 있음)
4. 실서버 배치 재측정 12/12(§4-2) · 스크린샷 `~/ff_shots/ui3/live/`.
5. 실서버 화면 눈 확인(브라우저, 읽기만 — 단추는 목록 필터와 사진 열기만 눌렀습니다):
   종류 단추 5개(«알끼리 붙음 833» …) · 카드 120장에 **개수 딱지 120개 · 상태 딱지 59개** ·
   사진을 열면 묶음 썸네일 4장 + «이 묶음의 대표(남길 장)입니다 — 나머지 3장은 이미 제외됐습니다» ·
   범례에 누를 수 있는 줄 4개 · **자바스크립트 오류 0건**.
   사진 `~/ff_shots/ui3/live/LIVE_{edit,list}_apple.png`

> **정적 파일은 재시작 없이 바로 나갑니다**(`send_from_directory`). 그래서 이번 작업 중에는 잠깐
> «새 화면 + 옛 서버» 상태가 있었습니다(23:08~23:47). 다음 사람은 화면과 서버를 같이 고칠 때
> **서버 재시작을 먼저 잡아 두는 편**이 낫습니다.

---

## 10. 남은 흠 · 2차가 봐 줬으면 하는 것

1. **범례를 누를 수 있게 되면서 사진 왼쪽 위 작은 칩 위에서는 붓질이 시작되지 않습니다.**
   (칩만 `pointer-events:auto` 라 칩 사이 빈틈으로는 그대로 통과합니다.) 왼쪽 위 모서리를 칠해야 할 때는
   바깥에서 끌고 들어오거나 레이어를 잠깐 꺼야 합니다 — 받아들일 만한지 판정 바랍니다.
2. **묶음 썸네일을 눌러 연 사진은 «이 쪽 목록» 끝에 붙습니다.** 그래서 그 뒤의 `,`·`.`(이전/다음)이
   목록 순서가 아니라 «붙인 순서» 로 움직입니다. 자주 쓰면 헷갈릴 수 있습니다.
3. **P2 의 `prev` 는 한 겹만 보관합니다.** 번호를 두 번 저장하면 «맨 처음» 것을 지킵니다(일부러).
   되돌리기는 그 «맨 처음» 으로 갑니다 — 중간 상태로는 못 돌아갑니다.
4. **일괄 제외가 이제 flag 사진을 건너뜁니다.** 지금 데이터에서는 바뀌는 게 없지만(사과 kept_human 0),
   앞으로 «중복인데 flag» 인 사진은 사람이 직접 제외해야 합니다. 이 규칙이 맞는지 판정 바랍니다.
5. **`/api/list` 가 매번 `flag_counts` 를 셉니다**(포도 2,406장에서도 1ms 대지만 «필요할 때만» 은 아닙니다).
6. 포도·복숭아 «세기» 단추를 누르면 2,531장을 0.2초씩 셉니다(약 8분). 번호가 없어 결과는 전부 0입니다 —
   단추를 아예 숨길지 판정 바랍니다.
7. 크롬·엣지·모바일 미확인(사이클 2 와 같음).

---

## 11. 2차가 그대로 재현할 명령

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
PY=/home/kds0206/.conda/envs/kwak/bin/python
export PATH=/home/kds0206/.local/node22/bin:$PATH

# 0) 회귀
cd $T && node --check app/static/app.js && node --check app/static/ui.js
node cycles/260917_신기능/cycle_1/stage1/sim.js
node cycles/260917_신기능/cycle_2/stage2/modesim.js          # 31/31
node cycles/260917_신기능/cycle_2/stage1_client/boxsim.js     # 50/50
$PY app/boxes.py
cd $T/cycles/260917_신기능/cycle_5/stage1 && $PY live_c5.py   # 실서버 읽기 전용

# 1) 모래상자 켜기 (포트는 비어 있는지 먼저 보세요 — 5131 은 다른 에이전트 것)
SB=$T/cycles/260917_ui/cycle_1/stage2/sandbox
cp -p $T/app/{server.py,instances.py,dupes.py,boxes.py,maskio.py} $SB/app/
cp -p $T/app/static/{index.html,ui.js,style.css,app.js,help.html} $SB/app/static/
cp -p $T/data/{apple,blueberry}/status.json $SB/data/…     # 3차 판정 상태로 맞추고 시작하세요
mkdir -p $SB/app/cache/instance_counts && cp -p $T/app/cache/instance_counts/*.json $SB/app/cache/instance_counts/
cd $SB/app && PORT=5133 LABELTOOL_DATA_ROOT=/data/project/2026summer/kds0206/datasets_reviewed_260916 \
보안 관련 값·설정 세부는 공개본에서 생략했습니다.

# 2) 새 API·P1·P2·캐시 (전부 모래상자)
cd $T/cycles/260917_ui/cycle_3/stage1
$PY t_api.py        # 34/34
LABELTOOL_DATA_ROOT=/data/project/2026summer/kds0206/datasets_reviewed_260916 $PY t_ab.py     # 35/35
LABELTOOL_DATA_ROOT=… $PY t_counts.py                                                        # 19/19

# 3) 진짜 브라우저 (모래상자에서만 — 저장이 일어납니다)
$PY t_ui.py         # 35/35 · 사진 ~/ff_shots/ui3/after/
$PY t_layout.py     # 12/12 (1100×700 캔버스 57.5% 이상)

#    «고치기 전» 을 다시 보려면 백업 정적 파일을 잠깐 넣고 같은 스크립트를 돌리세요
for f in app.js ui.js index.html style.css help.html; do cp -p $T/app/static/_backup_260917_ui5_$f $SB/app/static/$f; done
SB_TAG=before $PY t_layout.py     # 3/12 실패(1100×700 두 겹 · 캔버스 47.1%)
for f in app.js ui.js index.html style.css help.html; do cp -p $T/app/static/$f $SB/app/static/$f; done

# 4) 실서버(읽기 전용)
$PY t_live.py       # 15/15

# 5) 캐시를 다시 채우려면(오프라인, app/cache 에만 씀)
cd $T/app && $PY ../cycles/260917_ui/cycle_3/stage1/warm_counts.py apple blueberry

# 6) 모래상자 끄기 — **PID 로** 끄세요(남의 5131 을 죽이지 않게)
ss -ltnp | grep 5133      # PID 확인 뒤 kill <PID>

# 7) 되돌리려면 (이번 사이클 전체)
cd $T/app && for f in server.py instances.py dupes.py README.md; do cp _backup_260917_ui5_$f $f; done
cd $T/app/static && for f in app.js ui.js index.html style.css help.html; do cp _backup_260917_ui5_$f $f; done
cd $T && bash app/run.sh restart
```

---

## 12. 남긴 자취 (지울목록에 적을 것)

| 무엇 | 어디 | 크기 | 처리 |
|---|---|---|---|
| 내 스크립트 8개 | `T/cycles/260917_ui/cycle_3/stage1/{sb3,t_api,t_ab,t_counts,t_ui,t_layout,t_live,warm_counts}.py` | 약 60KB | 남깁니다(재현용) |
| 시험 기록 3개 | 같은 폴더 `warm_counts.log`(첫 계산 시간) · `t_layout_live.log`(실서버 배치) · `t_ui.log` | 12KB | 남깁니다 |
| ⚠️ `t_ui.log` 주의 | **첫(실패한) 실행 기록**입니다 — 시험 스크립트 자체의 버그(`indexOf`·WebDriver 에서 `S` 가 안 보임) 때문이고, 고친 뒤 마지막 실행은 35/35 입니다. 최신 결과는 `$PY t_ui.py` 를 다시 돌려 보세요 | — | — |
| 스크린샷 32장 | `~/ff_shots/ui3/{before,after,live}/` | **19MB** | 남깁니다(증거) |
| 백업 9개 | `app/_backup_260917_ui5_{server,instances,dupes,boxes}.py` · `app/_backup_260917_ui5_README.md` · `app/static/_backup_260917_ui5_{app.js,ui.js,index.html,style.css,help.html}` | 약 210KB | 남깁니다 |
| **열매 개수 캐시** | `app/cache/instance_counts/{apple,blueberry}.json` | 144KB | **남깁니다 — 지우면 다시 7분** (공용 data/ 아님) |
| 모래상자 | `T/cycles/260917_ui/cycle_1/stage2/sandbox/` | 98MB | 재사용했습니다(이미 지울목록에 있음). 안에 시험이 만든 `_status_backup_260917_23*.json` 5개 — **복사본**입니다 |
| 모래상자 서버(5133) | — | — | **껐습니다**(PID 로만 종료 · 남의 5131·5111 은 안 건드림). 2차는 §11 의 명령으로 다시 켜세요 |
