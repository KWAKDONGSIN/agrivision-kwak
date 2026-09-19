# 네 과일 통합 데이터셋 — datasets_merged_260918_v3

작성: 2026-09-18
만든 것: `semantic-segmentation/tools/build_merged_dataset.py` (자동 생성 폴더입니다)

## 이 폴더가 무엇인가

검수판 데이터셋(사람·AI 가 눈으로 본 결과)에 **라벨링 툴에서 사람이 누른 확정**을 덮어서
네 과일을 한 곳에 모은 것입니다. 원본(`datasets_resized_2mp`)·검수판·툴 `data/` 는
**한 글자도 바꾸지 않았습니다.** 전부 실제 파일 복사입니다(심볼릭 링크 아님).

## 구조

```
datasets_merged_260918_v3/
├── apple      images/ (429)  masks/ (429)  instances/ (429)  boxes/ (429 + YOLO txt)  manifest.csv
├── grape      images/ (2403)  masks/ (2403)  boxes/ (2403 + YOLO txt)  manifest.csv
├── peach      images/ (125)  masks/ (125)  boxes/ (125 + YOLO txt)  manifest.csv
├── blueberry  images/ (1114)  masks/ (1114)  instances/ (1114)  boxes/ (1114 + YOLO txt)  manifest.csv
├── manifest.csv        ← 네 과일 전부(제외한 사진 행도 들어 있음)
├── build_summary.json  ← 입력 지문·장수·소요 시간
└── README.md
```

## 장수

| | 검수판 manifest 행 | 남긴 사진 | 제외 | 열매 번호 | 상자 | 촬영 단위 | 분할 묶음 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 사과 | 1001 | **429** | 572 | 429 | 429 | 17 | 99 |
| 포도 | 2502 | **2403** | 99 | 0 | 2403 | 2403 | 2403 |
| 복숭아 | 125 | **125** | 0 | 0 | 125 | 4 | 4 |
| 블루베리 | 1195 | **1114** | 81 | 1114 | 1114 | 288 | 1055 |
| **합계** | 4823 | **4071** | 752 | 1543 | 4071 | | |

**사람이 되살린 중복** 0장 — 검수판이 «거의 같은 사진» 이라고 뺐던 것을 사람이 되살려 **묶음 대표와 함께** 남은 사진입니다. 사람 판정이 코드 규칙보다 위이므로 대표를 자동으로 빼지 않습니다(2026-09-18 결정 D1).

## 제외 사유

| 과일 | 사유 | 장수 | 뜻 |
|---|---|---:|---|
| 사과 | `reviewed_duplicate` | 572 | 검수판: 거의 같은 사진(대표만 남김) |
| 포도 | `reviewed_duplicate` | 98 | 검수판: 거의 같은 사진(대표만 남김) |
| 포도 | `reviewed_not_grape` | 1 | 검수판: 포도 사진이 아님 |
| 블루베리 | `reviewed_duplicate` | 81 | 검수판: 거의 같은 사진(대표만 남김) |

## 판정이 어디서 왔나 (`manifest.csv` 의 `source` 칸)

| 값 | 뜻 |
|---|---|
| `human_confirmed` | 툴에서 사람이 **확정**(status.json 의 `confirmed` 칸) |
| `human_unconfirmed` | **확정 칸 없이 사람이 누른 판정**(`confirmed` 칸은 없고 `by` 가 «AI» 로 시작하지 않는 것). 사이클 2 이전 저장분뿐 아니라 **오늘 사람이 마스크만 고쳐 저장한 것**도 여기 들어옵니다(2026-09-18 이전 이름 `human_legacy`) |
| `ai` | 툴에 AI 판정만 있고 사람은 아직 안 누름 → 검수판 판정을 그대로 씀 |
| `reviewed` | 툴에 아무 기록도 없음 → 검수판 판정 그대로 |

남긴 사진의 출처별 장수: 사과(ai=53, reviewed=376) · 포도(ai=84, reviewed=2319) · 복숭아(ai=125) · 블루베리(ai=6, reviewed=1108)

사람 판정을 어떻게 반영하는가: `ok`=남김(원본 마스크) · `fixed`=툴 `masks_fixed/` 마스크 사용 ·
`exclude`=제외(`human_exclude`) · `flag`=제외(`confirmed_flag`, 아직 고칠 것이라 «확실한 데이터» 가 아님).
**사람이 `ok` 로 확정하면 검수판에서 뺐던 사진도 되살아납니다**(`note` 에 «검수판 제외를 사람이 되살림»).

## `session`(촬영 단위)과 `split_group`(분할 묶음)

**분할(폴드 나누기)은 `session` 단위 GroupKFold 를 권고합니다.** 같은 촬영에서 나온 사진이
학습과 시험으로 갈라지면 점수가 부풀기 때문입니다. `split_group` 은 «그보다 잘게 나눌 때
지켜야 하는 최소 조건» 입니다.

| 과일 | `session` 을 무엇으로 정했나 | 근거 |
|---|---|---|
| 사과 | 검수판 manifest 의 `session` 칸 그대로(파일명에서 끝 번호를 뗀 것) | `datasets_reviewed_260917/README.md` |
| 블루베리 | 검수판 manifest 의 `session` 칸 그대로(«Camera N Video (X)») | 같은 곳 |
| 복숭아 | 파일명 `210629-t1-01` → **`210629-t1`**(날짜 + 나무 번호). `t2-of10`~`of18` 은 t2 의 곁가지라 t2 에 넣음 | 파일명 규칙(125장 전부가 `YYMMDD-t번호[-of번호]-장번호`) |
| 포도 | **미확인** — 사진 한 장을 한 촬영으로 둠 | 아래 |

🔴 **포도의 촬영 단위는 확인하지 못했습니다(미확인).** 근거:
원본 CERTH COCO 주석(`share_grape_certh/CERTH_annotations.zip`)의 `file_name` 이 `0.png`…`2501.png`
번호뿐이고 폴더 구분이 없으며 `date_captured` 가 전부 빈 문자열입니다. 툴 `data/grape/duplicates.json`
의 `sequence_stats` 도 `n_sequences`=1 이고 이웃 번호 2,501쌍의 상관계수 중앙값이 0.110 이라
**번호 순서가 촬영 순서가 아닙니다.** 그래서 포도는 `session` 을 만들지 않고 사진마다 하나로 두었습니다.

🔴 **그래서 포도는 `session` 으로 GroupKFold 를 돌려도 사실상 무작위 분할입니다**(2026-09-18 2차 검수 실측: 남긴 포도 2403장의 `session` 이 2403개 = 장마다 하나, `split_group` 도 2403개로 **전부 한 장짜리**입니다). 즉 포도에는 **지금 누수를 막는 장치가 없습니다** — 검수판이 «거의 같은 사진» 을 미리 빼 둔 것이 유일한 방어입니다. 포도 점수를 다른 과일과 나란히 놓을 때는 이 차이를 각주로 남기십시오.

`split_group` 은 복숭아·포도의 경우 **툴 `duplicates.json` 의 근접 중복 묶음 ∪ 같은 `session`** 으로
만들었습니다(사과·블루베리는 검수판 manifest 의 값을 그대로 씁니다).

## `manifest.csv` 의 칸

`fruit` · `stem` · `image_source` · `mask_source` · `action` · `reason` · `note` · `source` · `confirmed_by` · `confirmed_at` · `session` · `split_group` · `has_instances` · `has_boxes` · `rule_pending` · `overlap_neighbors` · `instances_source` · `boxes_source` · `apple_check_verdict` · `verdict_source` · `peach_dup_candidate` · `mask_audit_reason`

`action` = `keep`·`mask_fixed`·`image_replaced`·`needs_human`(여기까지 남긴 사진) ·
`excluded_duplicate`·`excluded_not_grape`·`excluded_human`·`excluded_flag`(뺀 사진).
`needs_human` 은 «마스크에 문제가 있다고 AI 가 표시한 것» 이고 검수판과 마찬가지로 **남겨 두었습니다**.
마지막 세 칸(`rule_pending`·`overlap_neighbors`·`instances_source`)은 검수판의 정보를 잃지 않으려고
덧붙인 것입니다. `rule_pending` 은 오류가 아니라 **규칙이 정해지지 않은 사진**입니다(남긴 사진 기준 사과 17 · 포도 0 · 복숭아 0 · 블루베리 218).

## 팀원 산출물을 어디에 반영했나

| 칸 | 값 | 어디서 왔나 |
|---|---|---|
| `boxes_source` | `tool` | 라벨링 툴에서 **사람이 그린** 상자 (`data/<과일>/boxes/`) |
| | `psm_gt` | 박성문 `bbox_outputs/<과일>/gt_boxes/` — **정답 마스크에서 뽑은** 상자. YOLO txt 도 그쪽 것을 그대로 복사 |
| | `lsh` | 임성후 `bbox_outputs/<과일>/all/` — watershed **추정** 상자(**미검증**). 박성문 gt 가 없는 과일에서만 |
| | `none` | 상자 없음 |
| `apple_check_verdict` | 예: `ok_one_apple=2 duplicate_polygon=1 · 확정오류 1` | 박성문 `apple_check/review_list.csv`(사람 눈 판정) + `confirmed_errors.csv` |
| `verdict_source` | `psm_review_list` / `psm_review_list+confirmed_errors` / `psm_confirmed_errors` / `none` | 같은 곳 |
| `peach_dup_candidate` | `burst_ofNN` / `pair_NN` / 빈칸 | 최인훈 `dup_audit_260917/peach/` — **제외하지 않습니다**(교수님 결정 항목) |
| `mask_audit_reason` | 예: `bottom_5pct_ratio` | 최인훈 `mask_audit_260908/suspects.csv` — 전경 비율이 아래 5% 인 마스크 |
| `instances_source` | `instances_fixed`/`detect_seed`/`reviewed_number_mask`/`none` | 아래 «값 사전» |

### `instances_source` 값 사전 (열매 번호가 어디서 왔나)

| 값 | 뜻 |
|---|---|
| `instances_fixed` | 라벨링 툴에서 **사람이 고친** 번호 마스크(`data/<과일>/instances_fixed/`) |
| `detect_seed` | 검출 팀 watershed **자동 초벌**(블루베리만). 사람이 검수한 것이 아닙니다 |
| `reviewed_number_mask` | 검수판 **원본 마스크 자체가 번호 마스크**인 경우(사과). 2026-09-18 이전 판에서는 한글 `원본번호` 였습니다 |
| `none` | 열매 번호 없음 |

상자 우선순위는 **툴(사람) > 박성문 gt > 임성후 > 없음** 입니다.
남긴 사진의 상자 출처: 사과(psm_gt=429) · 포도(psm_gt=2403) · 복숭아(psm_gt=125) · 블루베리(lsh=1114)

🔴 **교수님 결정 항목**

- **복숭아 중복 후보** — 최인훈 검수에서 `210629-t2-ofNN` 9그룹 45장이 «같은 복숭아를 5각도로 찍은 버스트»
  로 확인됐습니다. 우리 검수판은 복숭아를 **한 장도 빼지 않았으므로** 이 판에도 전부 들어 있습니다.
  얼마나 솎을지는 교수님이 정하실 일이라 `peach_dup_candidate` 칸에 **표시만** 했습니다(이 판 55장 · 13그룹).
- **의심 마스크** — `mask_audit_reason` 이 붙은 사진(이 판 205장)은 전경이 아주 작습니다. 빼지 않았습니다.
- **사과 번호 오류** — `apple_check_verdict` 가 붙은 사진(이 판 122장)은 박성문·사람 눈 판정입니다.
  `duplicate_polygon`·`one_apple_two_ids` 등은 **번호(instances) 쪽 문제**라 세그 마스크는 그대로 씁니다.

## 직전 빌드와 견준 «바뀐 입력»

읽지 못한 입력 **7개** — 그 칸은 비어 나갔습니다: `psm:blueberry:gt_boxes.json` · `psm:blueberry:gt_boxes.summary` · `psm:blueberry:gt_boxes.yolo` · `tool:apple:boxes` · `tool:blueberry:boxes` · `tool:grape:instances_fixed` · `tool:peach:instances_fixed`

견준 곳: `/data/project/2026summer/kds0206/datasets_merged_260918_v2/build_summary.json` — **바뀐 입력 없음**.

## 주의

- 마스크는 **전부 L 모드 0/255** 로 통일했습니다(사과 원본은 열매 번호, 블루베리 원본은 RGB 였습니다).
- 사과의 `instances/` 는 **원본 마스크의 열매 번호**이고, 블루베리의 `instances/` 는
  검출 팀이 만든 **자동 초벌**(watershed)입니다 — 사람이 검수한 것이 아닙니다.
- 번호는 «이진 마스크가 번호 마스크를 자른다» 규칙으로 잘라 저장했습니다(마스크 밖 번호 0개).
- 🔴 **`mask_source=masks_fixed` 경로는 아직 실자료로 검증되지 않았습니다.** 지금까지의 빌드에서는 해당 행이 0건이었습니다(사람이 툴에서 «수정함» 으로 확정한 사진이 아직 없기 때문). 이 판에 그 행이 생겼다면 **그중 한 장을 눈으로 열어** 툴에서 고친 마스크가 맞는지 확인하십시오(2026-09-18 결정 D5).
- 사과는 출처마다 라벨 규칙이 다릅니다(MinneApple = 가려진 부분까지 · dataset1~4 = 보이는 것만).
  **성능은 출처별로 나눠 보고하십시오.**

## 다시 만들려면

```bash
PY=/home/kds0206/.conda/envs/kwak/bin/python
cd /data/project/2026summer/kds0206/semantic-segmentation
$PY tools/build_merged_dataset.py --dry-run     # 무엇이 들어갈지만 본다
$PY tools/build_merged_dataset.py               # 오늘 날짜 폴더를 새로 만든다
```

같은 날 두 번 만들려면 `--suffix <이름>` 을 주십시오(폴더가 있으면 **덮어쓰지 않고 멈춥니다**).
자세한 절차는 `문서/260918_통합데이터셋_갱신법.md` 를 보십시오.
