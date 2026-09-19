작성: 2026-09-19

# «상자 + 개수 세기» 사이클 1 — 1차 작업 (Opus 5)

지시서: `kds0206/문서/260919_상자카운팅_논문근거_5사이클_지시.md` §1(만들 것 1~5)·§4
작업 시각(실측 `date`): 시작 **14:02** · 코드 끝 **14:44** · 회귀 완료는 §7.
도중 지시 변경 셋을 받아 반영했다(아래 §0).

## 0. 도중에 받은 지시 변경 (전부 반영)

| 받은 것 | 무엇 | 어디에 반영 |
|---|---|---|
| 14:1x 사용자 | «6시 전에 못 끝내도 좋다» → 15:10 시한·18:00 마감 없어짐. 범위를 줄이지 말고 다섯 가지 전부 + 회귀 전체 | 범위 축소 0. 사이클4 `runall.sh` 전체 + 통합 시험 전부 돌렸다(§7) |
| 사이클2 1판 | ①상자 정의를 과일별로 ②`counts.csv` 에 정답 칸 `n_gt`·`gt_source`, 통합에 `n_gt` ③툴 4-연결 vs 팀 8-연결은 **고치지 말고 적기만** | ②③ 그대로 반영(§3·§5). ①은 아래 2판으로 다시 씀 |
| 사이클2 정정 | ① 을 뒤집음 — MinneApple p.4 는 «어느 열매를 라벨하나» 이지 폴리곤 범위가 아니다 → **사과 modal 근거 없음**. «지금은 modal» 이라고 쓰지 말 것 | README §10·help 문장을 2판으로 다시 씀(§5). «modal» 단정 문구 0 |

## 1. 만든 것 — 한눈에

| # | 지시서 §1 | 상태 | 어디에 |
|---|---|---|---|
| 1 | 개수 칸 (상시 표시) | **완료** | `app/static/{index.html,style.css,ui.js,app.js}` · `app/server.py counts_of()` |
| 2 | 사람 확정 개수 = 상자/번호에서 유도 (별도 입력 칸 없음) | **완료** | `app/boxes.py human_count()` — 규칙이 있는 **한 군데** |
| 3 | `counts.csv` 내보내기 | **완료** | `export/export_dataset.py counts_rows()·write_counts_csv()` · `app/server.py`(kind `counts`) · `ui.js`(체크칸) |
| 4 | 통합 manifest 개수 칸 | **완료** | `semantic-segmentation/tools/build_merged_dataset.py` — `n_boxes, n_instances, n_count_human, count_source, count_conflict, n_gt` |
| 5 | 상자 정의 문서화 | **완료** | `app/README.md` §10 · `app/static/help.html` `#box` |

**못 한 것: 없음.** 다만 «고치지 말라고 지시받아 남겨 둔 것» 이 §8 에 둘 있다.

## 2. 규칙 — 개수를 어떻게 정하나 (이 사이클의 핵심 결정)

### 2-1. 개수만 치는 입력 칸은 **두지 않았다** (지시서 §1-2 의 yagni 판단)

이유 셋 — 보고서에 남기라고 한 것:

1. 숫자 칸을 두면 상자·번호와 어긋나는 **세 번째 진실**이 생긴다. 사람이 «17» 이라고 쳤는데
   상자 16·번호 15 이면 무엇이 맞는지 아무도 모른다(지금은 두 개뿐이라 `≠` 로 보여 주고 끝난다).
2. 확정·되돌리기 규칙을 **네 번째 종류**(`confirmed_counts`)로 또 나눠야 한다. 사이클 4·5 판정서가
   확정 세 칸을 독립으로 만드는 데 두 사이클을 썼다(되돌리기 = 그 종류 확정 삭제 · 상자 0개 저장 =
   삭제 + 확정 비움). 네 번째 칸은 그 규칙을 통째로 한 벌 더 만들고, «개수만 확정하고 상자는
   미확정» 같은 말이 안 되는 상태를 새로 만든다.
3. 녹취 0908 의 «AI 초벌 + 사람이 맞다/틀리다» 흐름에 **없는 작업**이다. 사람은 이미 상자나 번호를
   보고 Enter 를 누른다. 그 Enter 가 곧 «이 사진은 N개가 맞다» 이다.

### 2-2. 유도 우선순위 — `app/boxes.py human_count(n_boxes, n_instances, conf_boxes, conf_instances)`

```
① 번호 확정(confirmed_instances 가 ok·fixed)이 있고 번호 수를 알면  → 번호 수  source="instances"
② 아니면 상자 확정(confirmed_boxes 가 ok·fixed)이 있고 상자 수를 알면 → 상자 수  source="boxes"
③ 둘 다 없으면                                                      → 없음     source=""
둘 다 확정됐는데 수가 다르면 ①을 쓰되 conflict=True 로 표시한다(고르지 않는다 — 사람이 본다)
```

- **`flag`·`exclude` 는 «확정» 으로 세지 않는다.** 내보내기가 이미 그 둘을 뺀다(사이클3 결정 2).
- **번호가 먼저인 까닭**: 번호는 알 하나하나에 붙은 라벨이고, 상자는 그 번호에서 만든 것이다
  (`/api/boxes_seed` 는 번호 마스크가 있으면 번호마다 상자 하나). 사람이 상자를 합치거나 나눌 수
  있으므로 상자는 «개수의 원본» 이 아니다.
- **`0` 과 «없음» 은 다르다.** 상자 0개 저장은 파일을 지우는 것이므로(사이클5 2차 결정) `n_boxes=None`
  이고, 상자가 정말 0개로 저장돼 있으면 `0` 이다. 표에서도 빈칸 ≠ `0`.
- **확정은 있는데 셀 수가 없으면 «없음»** 이다(예: 번호를 확정했는데 번호 파일이 사라짐).
  세지 못한 것을 다른 종류의 수로 메우지 않는다.

같은 규칙이 세 곳에 있다. **일부러** 그렇게 했다(지시서 §1-4: 통합 스크립트는 툴 `app/` 을
import 하지 않는다 — 다른 파이썬 환경에서도 돌아야 한다). 갈라지지 않는지는 새 시험이 대조한다(§6).

| 어디 | 함수 | 쓰는 곳 |
|---|---|---|
| 툴 화면 | `app/boxes.py human_count()` ← `app/server.py counts_of()` | 하단 «개수» 칸 |
| 툴 내보내기 | `export/export_dataset.py counts_rows()`(위 함수를 **그대로 import**) | `counts.csv` |
| 통합 | `tools/build_merged_dataset.py count_cells()`(**다시 구현**) | `manifest.csv` |

## 3. 무엇을 어디에 — diff 요지

백업은 전부 `_backup_260919_cnt1_<파일명>` 으로 같은 폴더에 남겼다.

| 파일 | 늘어남/지움 | 무엇 |
|---|---:|---|
| `app/boxes.py` | +57 / −1 | `team_count()`(팀원 상자 개수만 · 사진을 열지 않는다) · **`human_count()`**(규칙 한 군데) · `demo()` 에 자체 점검 7개 |
| `app/server.py` | +45 / −4 | `counts_of()` · `api_item` 에 `counts` 칸 **추가만** · `EXPORT_KINDS` 에 `counts` · `export_args(counts=)` · `JOB_FIELDS`·job 에 `n_counts` · `export_worker` 에 «개수만» 갈래 |
| `app/static/index.html` | +6 / −1 | `#todo` 를 `#todorow` 로 감싸고 `#cnts` 한 칸 추가 |
| `app/static/style.css` | +9 / −0 | `#todorow`(flex) · `.cnts`·`.cnts.hum`·`.cnts.ne` |
| `app/static/ui.js` | +73 / −4 | `renderCntChip()`·`cntTip()` · `renderTodo()` 맨 앞에서 부름 · `EXPK.counts` 체크칸·풍선말·확정 장수 줄·결과 표 |
| `app/static/app.js` | +13 / −0 | `cntSet()` — 상자/번호 저장 직후 그 숫자만 고침(`/api/item` 을 다시 부르지 않는다) |
| `export/export_dataset.py` | +124 / −0 | `--counts` · `COUNTS_COLS`(12칸) · `gt_counts()` · `counts_rows()` · `write_counts_csv()` · `export_one` 끝에서 **같은 job 으로** 호출 |
| `tools/build_merged_dataset.py` | +133 / −2 | `MANIFEST_COLS` +6칸 · `count_cells()` · `n_box_in()` · `gt_counts()` · `write_fruit` 에서 **나간 파일**을 세고 그 뒤에 `count_cells` · 등록표에 `psm:<과일>:gt_boxes.csv` · README 생성부에 «개수 칸» 절 |
| `app/README.md` | +138 / −0 | §10 «상자의 정의»(2판) · **§19 개수 확정과 counts.csv**(19-1~19-4) |
| `app/static/help.html` | +39 / −2 | `#box` 에 «상자를 어디까지 치는가» 카드 · **`#cnt` 개수 세기 절**(새) · 목차 링크 · 내보내기 종류에 «개수» |
| 새 파일 | 315줄 | `semantic-segmentation/tools/tests_merged_260918/counts/test_counts.py` |
| 새 파일 | 114줄 | `cycles/260919_count/cycle_1/stage1/t3_chars_cnt1.py`(이 사이클만의 글자 예산 측정) |
| 새 파일 | 110줄 | `cycles/260919_count/cycle_1/stage1/ab_revert.py`(실패 자리 A/B — 되돌리기·종류 개수) |
| 새 파일 | 64줄 | `cycles/260919_count/cycle_1/stage1/ab_layout.py`(실패 자리 A/B — 캔버스가 움직였나) |

코드만(문서·시험 빼고) **+460줄**.

### 3-1. 화면 «개수» 칸

- 자리: 하단 상태 한 줄 **오른쪽**. `#todo` 는 길면 «…» 로 줄지만 이 칸은 flex 로 자리를 지켜
  **어느 작업(마스크·상자·번호)에서도 늘 보인다.**
- 글자: `개수 16·15·20` — 상자 · 번호 · 검출 팀 초벌(박성문, 없으면 임성후). 없는 것은 `-`.
  상자와 번호가 다르면 가운뎃점이 **`≠`** 로 바뀌고 칸이 노래진다. 사람 확정 개수가 있으면 초록.
- **실측 글자 수 10자**(사과 첫 사진 `개수 -·-·95`), 편집 화면 전체 증가 **+9자**(예산 12자) — §7.
- 나머지는 전부 풍선말(**352자**): 네 숫자가 각각 무엇인가 · 사람 확정 개수와 그 출처 ·
  어긋남 안내 · «초벌이 센 개수는 4-연결 기준» 경고(§8-1).
- **가드**: 서버가 `counts` 를 모르면(정적 파일이 서버보다 먼저 나가는 규칙 §8-10) 조용히
  `개수 -·-·-` 로 두고 풍선말로만 알린다. 화면이 없는 숫자를 지어내지 않는다.
- 보이는 숫자는 **저장·확정된 값**이다. 지금 그리는 중인 상자는 저장 뒤에 센다(풍선말에 명시).
  저장하면 `cntSet()` 이 그 숫자만 고친다 — **사람 확정 개수는 화면에서 계산하지 않는다**
  (규칙을 화면에도 또 적으면 네 번째 구현이 된다).

### 3-2. `counts.csv` — 칸 12개

`stem, n_boxes, n_instances, n_team_park, n_team_im, n_gt, gt_source, n_human, human_source,
count_conflict, confirmed_by, confirmed_at`

- `n_gt`·`gt_source` 는 **사이클2 지시 ②** 로 더한 것. 박성문
  `bbox_outputs/<과일>/gt_boxes/csv/detections.csv` 의 그 사진 줄 수이고 출처는 `psm_gt_boxes`,
  없으면 빈칸과 `-`. **블루베리는 정답 상자가 없다**(`all/` 은 watershed 자동 추정이라 정답이 아니다).
  정답이 없으면 MAE·RMSE·R²(`farjon2023countingreview` p.16 식 (1)~(4))를 셀 수 없다.
- `confirmed_by`·`confirmed_at` 은 **그 개수를 낳은 확정**(번호 또는 상자)의 이름·시각이다.
- 기본 «사람 확정만» = `n_human` 이 있는 줄만. «AI 제안 포함» 이면 전부(빈칸 허용).
- 「데이터 정리」 탭 종류에 **«개수(counts.csv)»** 가 늘었고, 세그 마스크·번호와 **같은 job**
  (`export_one` 이 쓴다)이다. **개수만 골라도 된다**(상자 YOLO 만 고를 수 있는 것과 같은 자리).
  그래서 `instances` 처럼 «마스크와 함께» 강제하는 규칙은 두지 않았다.
- 번호를 확정했는데 개수 캐시에 없는 사진은 **그 한 장만** 그 자리에서 센다(`instances.count_one`).
  세지 않으면 «번호로 확정했는데 표에는 상자 수» 라는 조용한 거짓말이 된다.

### 3-3. 통합 manifest — 칸 6개

`n_boxes, n_instances, n_count_human, count_source, count_conflict, n_gt` (전부 **맨 뒤에** 붙였다 —
앞 칸 순서를 한 칸도 건드리지 않았다. 검출 팀이 읽는 표이기 때문).

- `n_boxes`·`n_instances` 는 **그 폴더에 실제로 나간 파일**을 센 값이다(툴 저장분이 아니라).
  규격을 맞추다 번호가 사라질 수 있어(`spec_warn`) 계획 단계의 수는 결과와 다를 수 있다.
  그래서 `write_fruit` 가 파일을 다 쓴 **뒤에** `count_cells()` 를 부른다(순서가 중요하다).
- 뺀 사진은 앞 다섯 칸이 `-`. `0` 이라고 적으면 «열매가 없는 사진» 으로 읽혀 MAE·R² 에 섞인다.
  **`n_gt` 는 덮지 않는다** — 정답은 이 폴더에 무엇이 나갔나와 무관하고, 뺀 사진의 정답 수는
  «왜 뺐나» 를 볼 때 쓰인다.
- 새 입력 `psm:<과일>:gt_boxes.csv` 를 등록표(`input_registry`)에 넣었다 — 그 칸이 말없이
  비어 나가는 것을 «있다 → 없다» 검사가 잡게 하려는 것이다.

## 4. 시험 — 표

| 무엇 | 결과 |
|---|---|
| `node --check app.js` · `ui.js` | 통과 |
| `py_compile` server·instances·boxes·dupes·maskio·export_dataset | 통과 |
| `python app/boxes.py`(자체 점검 — `clean`·`boxes_of`·**`human_count`**) | 통과 |
| c4 `t1_api.py` | rc=0 |
| c4 `t2_ui.py` (진짜 브라우저) | rc=0 |
| c4 `regress_all.py` (전 조작 회귀) | rc=0 |
| `sim.js` · `modesim.js` · `boxsim.js` | **31/31 · 50/50** 통과 |
| c4 `t3_chars.py`(기준 = 사이클4 직전) | rc=1 — **내 것이 아니다**(§7-1) |
| **`t3_chars_cnt1.py`(기준 = 이 사이클 직전)** | **6/6 통과 · 최대 증가 +9자(예산 12)** |
| c4 `reg_c4`(사이클1·2 회귀) · `reg_c4b`(a1~a7) · `reg_c4c` · `rerun_fixed.sh` | **전 묶음 완료** — 사이클4 값과 견준 표가 §7-2. **새로 깨진 것 1칸**(낡은 기대값 · 결함 아님) |
| 실패 네 자리 A/B(옛 판 vs 새 판 · `ab_revert.py`·`ab_layout.py`) | **셋은 옛 판에서도 같은 값** · 하나는 내 것이고 지시서가 시킨 칸 추가 — §7-3 |
| **새 `tests_merged_260918/counts/test_counts.py`** | **61항목 · 실패 0** |
| `tests_merged_260918/test_build_merged.py` | **68항목 · 실패 0** |
| `stage4/test_confirm_kinds.py` | **200항목 · 실패 0** |
| `stage5/test_spec.py` | **106항목 · 실패 0** |
| `stage5/test_fix_m5c.py` | **67항목 · 실패 0** |
| 통합 시험 합계 | **441항목 · 실패 0** |
| `build_merged_dataset.py --dry-run`(`-W error::DeprecationWarning`) | **exit 0** |
| dry-run 장수 | 사과 429 · 포도 2,403 · 복숭아 125 · 블루베리 1,114 — **v3 와 한 장도 다르지 않음** |
| 복숭아 부분 빌드 md5 vs `datasets_merged_260918_v3` | `images` `dc036154…` · `masks` `14e28b7d…` · `boxes` `768e1143…` — **셋 다 바이트 동일** |

### 4-1. 새 시험이 보는 것 (`counts/test_counts.py` 61항목)

| 부분 | 무엇 |
|---|---|
| [가] | (상자 수 6 × 번호 수 6 × 상자 확정 6 × 번호 확정 6) = **1,296 조합 전수**를 툴 `human_count()` 와 통합 `count_cells()` 에 넣어 대조 + 규칙 못 박기 7개 |
| [나] | **진짜 자료** — 툴 `counts_rows()` 를 네 과일(125·2,502·1,001·1,195 = 4,823줄)에 돌려 그 줄을 통합 구현에 넣어 대조 |
| [나2] | **모래상자** — 확정이 있는 자료 9가지(둘 다 같음 / 둘 다 다름 / 상자만 / 번호만 / 확정 없음 / flag·exclude / 상자 0개 / 확정은 있는데 파일 없음 / 캐시에 없음)로 `ok`·`fixed`·어긋남 갈래를 **실제 `counts_rows()` 로** 돌린다 |
| [다] | `counts.csv` 칸 이름·«사람 확정만» 걸러내기·빈칸과 0 의 구별·**복숭아 정답 합계 977알**(박성문 표와 같음)·블루베리 정답 없음 |
| [라] | 통합 `MANIFEST_COLS` 여섯 칸이 맨 뒤·README 설명·뺀 사진 `-` 규칙·`count_cells` 호출 순서·두 `gt_counts()` 가 같은 결과 |

**[나] 가 지금 약한 곳을 [나2] 가 메운다**: 2026-09-19 현재 진짜 `status.json` 에 상자·번호
확정이 **한 장도 없다**(네 과일 실측 0장). 그래서 [나] 만으로는 «없음» 갈래만 돈다.

### 4-2. 실측으로 얻은 교차 검증

복숭아 부분 빌드 manifest 125행에서 **`n_boxes` 와 `n_gt` 가 완전히 같고 합계가 977** 이다
(박성문 `260907_과실bbox_간단설명.md` 의 «복숭아 977알» 과 일치). 복숭아 상자는 `psm_gt` 에서
오므로 당연한 결과지만, 두 경로(상자 json 세기 ↔ detections.csv 줄 세기)가 같은 수를 낸다는
독립 확인이다.

## 5. 상자 정의 문서화 (지시서 §1-5 · 사이클2 정정 2판)

`app/README.md` §10 과 `app/static/help.html` `#box` 에 넣은 문장:

> **상자 = 마스크(또는 번호)를 꼭 감싸는 축정렬 최소 상자**(COCO 관례, `lin2014coco` p.11).
> **마스크가 가려진 부분까지 포함하는지(amodal)는 과일마다 다르다** —
> 복숭아 amodal(원논문 명문 `seo2024peach` p.11) / 사과 출처별로 섞여 **규칙 미정**(교수님 질문 #1·#9) /
> 포도·블루베리 **판정 불가**. **상자는 마스크를 그대로 따른다.**

«지금은 modal» 이라는 단정은 **쓰지 않았다**(사이클2 정정). MinneApple p.4 의
«only provide annotations for fully or partially visible fruits» 는 «어느 열매를 라벨하나» 를
말한 문장이지 폴리곤이 어디까지 덮나를 정한 문장이 아니다.

### 5-1. «정말 min/max 로 계산하나» — 실측 한 줄씩

| 어디 | 코드 | 결과 |
|---|---|---|
| 툴 «✨ 초벌» | `app/boxes.py boxes_of()` | ✅ `ndimage.find_objects()` 슬라이스 안에서 `lab[s]==i` 화소의 `xs.min()/ys.min()`·`xs.max()/ys.max()` — **그 번호 화소의 min/max 그대로** |
| 검출 팀 정답 상자 | 박성문 `tools/draw_gt_boxes.py:54` | ✅ 같은 `find_objects()` 의 슬라이스 경계 `start`~`stop-1` = 그 번호 화소의 min/max |
| 검출 팀 블루베리 초벌 | 박성문 `tools/fruit_bbox_lib/instances.py:349` | ✅ `regionprops` 의 `bbox`(배타)를 포함 좌표로. **`bbox_padding` 이 0** — 실측 `bbox_outputs/blueberry/all/json/*.json` 의 `params.bbox_padding == 0` |

### 5-2. 🟡 새로 찾은 것 — 좌표 관례가 한 화소 다르다 (고치지 않았다)

`boxes_of()` 의 `x2·y2` 는 **배타적**(`max+1` = 슬라이스의 `stop`)이고 박성문 `bbox_xyxy` 는
**포함적**(`stop-1`)이다. YOLO 로 나가는 **넓이는 두 쪽 다 `max-min+1` 화소로 같지만**,
`read_team_boxes()` 가 팀원 좌표를 그대로 읽으므로 **팀원 초벌 상자가 화면에서 오른쪽·아래로
1화소 좁게** 보인다. 상자 하나가 보통 수십~수백 화소라 라벨 품질 영향은 무시할 수준이고,
고치면(읽을 때 +1) 이미 확정한 상자의 좌표가 바뀌므로 **사이클 2 이후 결정**으로 남겼다.
README §10 에 그대로 적어 두었다.

## 6. 켜기 순서 (실서버 5111 은 이 사이클이 건드리지 않았다)

지시서 §4·§8-10 대로 **만들기와 켜기를 나눴다**. 이 사이클은 파일만 고쳤고 5111(PID 3915126)에
붙지도, 재시작하지도, 로그인하지도 않았다.

1. 정적 파일(`app/static/*`)은 **다시 켜지 않아도 즉시** 나간다 → 그 사이에는 서버가 `counts` 를
   모르므로 화면이 조용히 `개수 -·-·-` 로 뜬다(가드 확인 완료).
2. 서버를 켤 때: `cd <툴>/app && bash run.sh restart`(데이터 루트 유지). `pkill -f` 금지 — PID 로.
3. 켠 뒤 눈으로 볼 것 셋:
   - 사진을 열면 하단 오른쪽에 `개수 …` 가 뜨는가(`-·-·-` 가 아니어야 한다)
   - 「데이터 정리」 탭 종류에 «개수(counts.csv)» 가 보이고, 그것만 골라도 «서버에 저장» 이 되는가
   - `/box` 전용 화면에서도 개수 칸이 보이는가
4. 통합 스크립트는 **0920·0921 재빌드 때** 새 칸이 저절로 들어간다. 지금 다시 빌드할 필요 없다.

## 7. 회귀 — 무엇을 어떻게 돌렸나

사이클4 `cycles/260918_paint/cycle_4/stage1/` 을 **통째로 복사**해
`cycles/260919_count/cycle_1/stage1/c4reg/` 에서 돌렸다(로그가 사이클4 결과를 덮지 않게).

    cd <툴>/cycles/260919_count/cycle_1/stage1/c4reg && bash runall.sh > runall_cnt1.log 2>&1

### 7-1. `t3_chars` rc=1 은 이 사이클의 잘못이 아니다

c4 판 `t3_chars.py` 의 «전» 기준은 `_backup_260918_c4_*`(= 사이클4 **직전**)이라
**사이클4·5 가 늘린 글자까지 함께** 센다: 마스크 +9 · 상자 **+84** · 번호 +1.
상자 +84 는 0919 사이클5 의 «초벌 출처» 칸·«팀원 상자 …» 줄이고 이 사이클 것이 아니다.

그래서 **같은 방법·같은 창 크기·같은 사진**으로 «전» 만 `_backup_260919_cnt1_*` 로 바꾼
`t3_chars_cnt1.py`(새 114줄, 포트 5321·5322, 모래상자는 **내 폴더 안**)를 만들어 다시 쟀다:

```
  [전] 마스크 153 · 상자 244 · 번호 216자 · 개수칸 없음
  [후] 마스크 162 · 상자 253 · 번호 225자 · 개수칸 '개수 -·-·95'(10자, 풍선말 352자)
  차이: 마스크 +9 · 상자 +9 · 번호 +9자        ← 지시서 기준 ≤12자
```

6항목 전부 통과. 스크린샷 `~/ff_shots/cnt1/edit_후_{mask,box,num}.png`(1920×1080).

### 7-2. 전 묶음 결과 — 사이클4 1차가 적어 둔 값과 나란히

`runall.sh` 전체(**C4_ALLDONE**) + `rerun_fixed.sh`(모래상자를 미리 띄워야 하는 넷)를 다 돌렸다.
«사이클4» 칸은 `cycles/260918_paint/cycle_4/stage1_work.md` 의 표에 적힌 값이다.

| 묶음 | 사이클4 1차 | 이번 | 판정 |
|---|---|---|---|
| `modesim.js` · `boxsim.js` · `sim.js` · `boxes.py` | 31/0 · 50/0 · 통과 | **31/0 · 50/0 · 통과** | 같음 |
| `py_compile` 6파일 · `node --check` 2파일 | OK | **OK** | 같음 |
| 사이클2 1차 `t1_api` | 79 / 0 | **78 / 1** | 🟡 **내 것 아님** — A/B 로 증명(§7-3 ①) |
| 사이클2 1차 `t2_queue` | 43 / 0 | **42 / 1** | 🟡 **내 것 아님** — 배치 A/B 로 증명(§7-3 ②) |
| 사이클2 1차 `t3_conc` | 8 / 0 | **8 / 0** | 같음 |
| 사이클2 1차 `t4_paint8` | 22 / 0 | **22 / 0** | 같음 |
| 사이클2 1차 `t1_after`·`t2_reg` | 0 FAIL | **0 FAIL** | 같음 |
| 사이클2 1차 `t3_matrix` | 84 / 0 | **FAIL 4** | 🟡 **0919 사이클5 가 만든 낡은 기대값**(§7-3 ③) |
| 사이클2 1차 `t4_keys` | 25 / 0 | **25 / 0** | 같음 |
| 사이클2 1차 `t6_view` | 126 / 4 | **126 / 4** | 같음(사이클1부터 있던 4칸) |
| 사이클2 2차 `s1_api` | 77 / 0 | **76 / 1** | 🟡 **내 것 아님** — `t1_api` 와 **같은 원인**(§7-3 ①) |
| 사이클2 2차 `s2_scenario`·`s3_guards` | 20/0 · 18/0 | **20/0 · 18/0** | 같음 |
| 사이클2 2차 `s4_paint8` | 21 / 1 | **21 / 1** | 같음(전부터) |
| 사이클2 2차 `s5_live_guard`(a+c) | 12 / 1 | **12 / 1** | 같음(전부터) |
| 사이클2 2차 `s6_layout`·`s7_clip`·`s8_guard_advance` | 7/0 · 2/0 · 3/0 | **7/0 · 2/0 · 3/0** | 같음 |
| 사이클3 2차 `a1_sem`·`a2b_loss`·`a3_conc`·`a4_input` | 16/0 · 7/0 · 17/0 · 62/0 | **같은 값** | 같음 |
| 사이클3 2차 `a5b_ui`·`a5c_errrow`·`a7_equiv` | 7/0 · 3/0 · 11/0 | **같은 값** | 같음 |
| 사이클3 2차 `a6_reg` | 9 / 2 | **9 / 2** | 같음(전부터) |
| 사이클3 2차 `a5_ui` | (도중 오류) | **(같은 오류)** | 같음 — `a5b_ui` 가 대신하는 시험 |
| 사이클3 1차 `t1_api` | 79 / 0 | **79 / 0** | 같음 |
| 사이클3 1차 `t2_ui` | 24 / 0 | **23 / 1** | 🟠 **내 것 · 낡은 기대값**(§7-3 ④) |
| 사이클4 1차 `t1_api`·`t2_ui`·`regress_all` | 34/0 · 27/0(경고1) · 99/0(경고9) | **같은 값** | 같음 |
| 사이클4 1차 `t3_chars` | 1 / 1 | **1 / 1** | 기준이 사이클4 직전 — §7-1 |

**새로 깨진 것: `t2_ui 가-4` 한 칸뿐이고 그것은 «종류 체크가 3개» 라는 낡은 기대값이다.**

### 7-3. 실패 네 자리를 하나씩 — 말이 아니라 실측으로

말로 «내 것이 아니다» 라고 하지 않고 **옛 판·새 판에 같은 것을 물어** 갈랐다.
스크립트 둘(`stage1/ab_revert.py` · `stage1/ab_layout.py`)과 결과
`ab_revert.json`·`ab_layout.json` 을 남겼다. 모래상자는 `stage1/sb_ab_{before,after}`,
포트 5331~5334, «전» 은 `_backup_260919_cnt1_*`(서버 2 + 정적 5 + export 1)로만 바꾼 같은 사본이다.

**① `t1_api` «N-A(확정된 사진): confirmed 칸이 되돌리기로 바뀌지 않는다» · `s1_api` «가-N-A confirmed 그대로»**

```
  ① /api/revert 가 마스크 confirmed 를 지우는가 : 전 True · 후 True
```

**옛 판에서도 똑같이 지운다** → 이 사이클 것이 아니다. 지우는 것은 **사이클4 stage2c 총괄 결정 1**
(`clear_confirm` — «되돌리기가 성공하면 그 종류의 사람 확정을 지운다»)이고, 사이클2 가 적어 둔
기대값이 그 결정으로 낡았는데 아무도 갱신하지 않은 것이다. 사이클4 1차 표가 79/0 인 까닭은
그때는 `clear_confirm` 이 **stage1 뒤(stage2c)에** 들어왔기 때문이다.
👉 **고칠 자리**: `cycle_2/stage1/t1_api.py` 와 `cycle_2/stage2/s1_api.py` 의 그 두 칸을
«되돌리기는 그 종류의 확정을 **지운다**» 로 갱신(사이클4 `fix_expect_c4.py` 와 같은 방식).
이 사이클은 남의 사이클 시험을 건드리지 않았다.

**② `t2_queue` «붓질로 «저장 안 한 수정» 딱지가 켜진다»**

`#cv` 위 **고정 좌표**(420,330 → 470,372)를 드래그하는 검사라 캔버스가 조금만 움직여도 헛나간다.
내가 `#todo` 를 `#todorow` 로 감쌌으므로 그것부터 쟀다(1366×768 · 사과 첫 사진):

```
  #cv        전 [164, 40, 1172, 564] · 후 [164, 40, 1172, 564] → 같음
  #verdictbar 전 [164, 604, 1172, 78] · 후 [164, 604, 1172, 78] → 같음
  #todo      전 [172, 610, 1156, 23] · 후 [172, 610, 1078, 23]  (개수 칸 72px + 간격 6px 만큼만 좁아짐)
```

**캔버스와 하단 줄이 한 픽셀도 안 움직였다.** `#todo` 만 78px 좁아지는데 그 줄은 원래
`text-overflow: ellipsis` 로 줄어드는 칸이다. → 이 실패는 내 배치 변경으로 설명되지 않는다
(붓 드래그 흔들림 계열 · `s4_paint8`·`t6_view` 와 같은 자리).

**③ `t3_matrix` FAIL 4 — «② 전부 지우고 저장하면 0개»(복숭아·포도·사과)**

**0919 사이클5 2차가 바꾼 규칙** 때문이다: «전부 지움 → 상자 저장»(= 상자 0개 저장)은 이제
«저장» 이 아니라 **파일을 지우고 상자 확정을 비우는 것**이다(사이클5 열린 문제 7). `boxes.py`
`api_boxes_save` 의 그 갈래는 **내가 한 글자도 건드리지 않았다**(내 `boxes.py` diff 에서 지운 줄은
`demo()` 의 print 한 줄뿐이다 — `diff` 로 확인). 네 번째 FAIL «apple ③ 번호 저장이 기록됨 |
수정본 되돌림» 과 끝의 `Unexpected confirm dialog` 도 그 뒤에 이어진 것이다.
👉 **고칠 자리**: `cycle_2/stage1/runall_stage1/t3_matrix.py` 의 «전부 지우고 저장하면 0개» 를
«전부 지우고 저장하면 **파일이 없어지고 확정이 풀린다**» 로 갱신 — **사이클5 가 남긴 숙제**다.

**④ `t2_ui`(사이클3 1차) «가-4 과일 라디오 4개 · 종류 체크 3개 · 조건 라디오 2개» → (4, **4**, 2)**

**이것만 내 것이다. 그리고 지시서가 시킨 것이다** — 「데이터 정리」 종류에 «개수(counts.csv)»
한 칸을 더했으므로 3 → 4 가 맞다. A/B 로도 그대로 나온다:

```
  ② 「데이터 정리」 종류 체크 개수 : 전 3 · 후 4
```

결함이 아니라 **낡은 기대값**이다.
👉 **고칠 자리**: `cycle_3/stage1/t2_ui.py` 의 `(n_f, n_k, n_m) == (4, 3, 2)` 를 `(4, 4, 2)` 로.
남의 사이클 시험 파일이라 **이 사이클은 고치지 않았다** — 2차가 판단할 자리다.

### 7-4. 요약

- **새로 깨진 것 1칸**(`t2_ui 가-4`) — 지시서가 시킨 칸 추가에 따른 **기대값 낡음**, 결함 아님.
- 나머지 3자리(`t1_api`·`s1_api` 1칸씩 · `t2_queue` 1칸 · `t3_matrix` 4칸)는 **사이클4·5 의 결정으로
  낡은 기대값**이거나 **전부터 있던 흔들림**이고, 옛 판에서도 같은 값이 나온다(실측).
- 전부터 설명돼 있던 실패 7칸(`t6_view` 4 · `s4_paint8` 1 · `s5_live_guard` 1 · `a6_reg` 2)과
  `a5_ui` 의 도중 오류는 **사이클4 값과 똑같다.**

## 8. 고치지 않고 남긴 것 (지시받은 것 + 내가 찾은 것)

### 8-1. 🔴 연결 덩어리 세는 법이 팀과 다르다 — **사이클2 가 «고치지 말라»** (사이클3·4 몫)

툴 `app/server.py:1135` 의 `ndimage.label()` 은 **기본 4-연결**이고 박성문
`instance_split.py:55` 는 **8-연결**(`_S8 = np.ones((3,3))`). 같은 이진 마스크에서 개수가 다르게
나온다(대각선으로만 닿은 두 덩어리를 툴은 2개, 팀 도구는 1개). 번호가 있는 과일(사과·블루베리)은
번호 수를 쓰므로 영향이 없고, **번호가 없는 복숭아·포도의 «✨ 초벌» 상자 개수**에만 걸린다.

🆕 **덧붙여 찾은 것**: 툴은 scipy 가 없을 때 `skimage.measure.label`(기본 2-connectivity =
**8-연결**)로 되넘긴다(`server.py:1137`). 즉 **툴 안에서도 두 값이 갈린다.**

지시대로 **코드는 손대지 않고**, 개수 칸 풍선말과 README §19-3-B 에 사실만 적었다:
«초벌이 센 개수는 4-연결 덩어리 기준 — 검출 팀 도구(8-연결)와 다를 수 있습니다».

### 8-2. 🟡 팀원 상자 좌표가 1화소 좁게 읽힌다 — §5-2. 사이클 2 이후 결정.

### 8-3. 🟡 `team_count()` 와 화면 상자 수가 1~2개 다를 수 있다

`team_count()` 는 `bbox_xyxy` 가 4개 이상인 `detections` 를 세고, 화면은 그 뒤 `clean()` 이
**2픽셀 미만 상자를 버린 것**을 그린다. 팀원 초벌은 «참고 값» 이고 사람 확정 개수로는 쓰지 않으므로
그대로 두었다(`boxes.py` 주석에 명시).

## 9. 2차가 재현할 명령

```bash
PY=/home/kds0206/.conda/envs/kwak/bin/python
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
S=/data/project/2026summer/kds0206/semantic-segmentation

# ① 문법·자체 점검
/home/kds0206/.local/node22/bin/node --check $T/app/static/ui.js
/home/kds0206/.local/node22/bin/node --check $T/app/static/app.js
$PY -m py_compile $T/app/server.py $T/app/boxes.py $T/export/export_dataset.py
$PY $T/app/boxes.py                       # human_count() 자체 점검 7개

# ② 이 사이클만의 글자 예산(진짜 브라우저 · 포트 5321·5322 · 모래상자는 내 폴더)
cd $T/cycles/260919_count/cycle_1/stage1 && $PY -u t3_chars_cnt1.py

# ③ 사이클4 회귀 전체 (내 사본에서 — 사이클4 로그를 덮지 않는다)
cd $T/cycles/260919_count/cycle_1/stage1/c4reg && bash runall.sh > runall_cnt1.log 2>&1
grep -E '^###|C4_ALLDONE' runall_cnt1.log

# ④ 통합 — 대조시험 + 기존 시험 전부
cd $S
$PY tools/tests_merged_260918/counts/test_counts.py            # 61항목
$PY tools/tests_merged_260918/test_build_merged.py             # 68
$PY tools/tests_merged_260918/stage4/test_confirm_kinds.py     # 200
$PY tools/tests_merged_260918/stage5/test_spec.py              # 106
$PY tools/tests_merged_260918/stage5/test_fix_m5c.py           # 67

# ⑤ dry-run 장수 불변 (exit 0 · 429 / 2,403 / 125 / 1,114)
$PY -W error::DeprecationWarning tools/build_merged_dataset.py --dry-run

# ⑥ 복숭아 부분 빌드 md5 가 v3 와 같은가 (모래상자에만 만든다 · 15초)
OUT=$(mktemp -d)
$PY tools/build_merged_dataset.py --fruits peach --out-root $OUT \
    --date 260919 --suffix cnt1repro --no-prev
A=/data/project/2026summer/kds0206/datasets_merged_260918_v3/peach
B=$OUT/datasets_merged_260919_cnt1repro/peach
for sub in images masks boxes; do
  a=$(cd $A/$sub && find . -type f | sort | xargs md5sum | md5sum)
  b=$(cd $B/$sub && find . -type f | sort | xargs md5sum | md5sum)
  [ "$a" = "$b" ] && echo "$sub 바이트 동일" || echo "$sub 다름"
done

# ⑦ counts.csv 를 눈으로 (모래상자로만)
$PY $T/export/export_dataset.py --fruit peach --counts --dry-run

# ⑧ 모래상자를 미리 띄워야 하는 넷 (사이클4 가 쓰던 것 그대로)
cd $T/cycles/260919_count/cycle_1/stage1/c4reg && bash rerun_fixed.sh > rerun_fixed_cnt1.log 2>&1

# ⑨ 실패 네 자리가 내 것인가 — 옛 판·새 판 A/B (포트 5331~5334)
cd $T/cycles/260919_count/cycle_1/stage1
$PY -u ab_revert.py      # ① /api/revert 가 confirmed 를 지우는가 · ② 종류 체크 개수
$PY -u ab_layout.py      # ③ #todorow 가 캔버스를 움직였는가
```

## 10. 만지지 않은 것

- **실서버 5111(PID 3915126)** — 재시작·로그인·붙기 **0회**. 교수님 5100·5101·5105 도 0회.
- 원본 · 검수판(`datasets_reviewed_260916`·`_260917`) · `datasets_resized_2mp` ·
  `datasets_merged_260918`·`_v2`·`_v3` · 팀원 폴더(박성문·최인훈·임성후) — **읽기만**.
- 공용 `T/data`·`T/exports` — **한 글자도 쓰지 않았다**.
- 삭제 0 · GPU 0 · 새 패키지 0 · `pkill -f` 0 · 남의 프로세스 kill 0 · `작업기록.md` 갱신 0.

⚠ **한 가지 밝힐 것**: `c4reg/lib_c4.py` 의 `HERE` 가 `cycles/260918_paint/cycle_4/stage1` 로
**하드코딩**돼 있어, 복사본에서 돌려도 회귀 묶음의 **모래상자**(`sandbox`·`sandbox_old`·
`sandbox_chars_*`·`reg_c4/`)는 사이클4 폴더 아래에 만들어진다. 그 폴더들은 매 실행마다
`rmtree` 후 다시 만드는 **임시 작업 공간**이고 판정서·로그·`*.json` 결과는 전부 내 폴더에
남았다. 그래도 «남의 사이클 폴더에 쓴 것» 이므로 적어 둔다. 내가 새로 만든
`t3_chars_cnt1.py` 는 `L.HERE` 를 **내 폴더로 덮어써서** 이 문제가 없다.
