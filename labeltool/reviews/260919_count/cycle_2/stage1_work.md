작성: 2026-09-19

# 사이클 2 (보통) 1차 작업 — 논문 근거 대조표 1판 + 어긋난 것 수정 1차

작업 시각: **14:02:52 시작 ~ 14:33 1판 · 14:34~14:38 자체 정정 2건 · 14:39~14:50 3-c 신설 · 15:19~15:22 3-c 를 «부분 해결» 로 갱신** (`date` 실측. 14:1x 사용자 지시로 15:20 보고 시한·18:00 마감 해제 → 항목을 줄이지 않고 7항목 전부 대조)
작업자: Opus 5 · 지시서 `kds0206/문서/260919_상자카운팅_논문근거_5사이클_지시.md` §2
산출물: **`kds0206/문서/260919_논문근거_대조표.md`** (표 27칸 + 부록 A~E)

---

## 1. 무엇을 했나

`platform/01_references/pdf/` **143편 전부**를 `pdftotext -layout` 로 뽑아(143/143 성공, 그 중 2편은
텍스트층이 없어 17·13바이트만 나옴) 지시서 §2 의 **7개 항목 전부**를 대조했습니다.
항목마다 관련 논문을 제목·본문 전수 `grep` 으로 폭넓게 찾았고, 인용문은 **쪽 번호까지 찍어** 확인했습니다
(`pg.py` — 대조표 부록 A 에 그대로 있음). 근거를 못 찾은 것은 «근거 없음», PDF 가 없는 것은
«PDF 없음» 으로 적었고 **지어낸 인용문은 없습니다.**

대조표 머리에 `260813_사진처리_전과정과_논문근거.md` 의 «사후 정당화» 경고 문장을 **원문 그대로** 옮겼습니다.

읽은 우리 쪽 구현:
`app/boxes.py`(`boxes_of`·`boxes_seed`·`clean`·`human_count`·`CLASSES`·`TEAM_CLS`) ·
`app/instances.py` · `app/server.py:1123 labeled()` ·
박성문 `semantic-segmentation/tools/instance_split.py`·`fruit_bbox.py`·`bbox_outputs/README.md` ·
`kds0206/semantic-segmentation/tools/build_merged_dataset.py`(session·split_group·2MP 규격 절) ·
`tools/resize_datasets_to_common_pixels.py` · `문서/260918_사과블루베리_5회검수_최종판정.md` ·
`문서/260918_툴_방향_녹취기준.md`.

---

## 2. 대조표 요약 — 항목별 판정 집계

표는 **28칸**입니다(항목 1:6 · 2:6 · 3:**3** · 4:3 · 5:5 · 6:4 · 7:1).

> 🔴 **15:21 갱신 — 3-c 는 «부분 해결» 입니다.** 제가 14:48 에 «가장 급함» 으로 올린 뒤
> **다른 사이클이 14:51~14:52 에 세 스크립트를 다 고쳤습니다**(제 권고 문구와 거의 같게, `seo2024peach` p.5 까지).
> `make_fig_crop_overlay.py:208` 은 이제 «원칙적으로 라벨 대상이 아니지만 … 사과 일부(42장 중 5장)에 라벨이 남아
> 규칙 미정» 입니다. 형제 그림 2·3(`make_fig_samples_annotated.py:211-213`·`make_fig_objects_per_image.py:226-227`)은
> **원래부터 정확했습니다** — 제가 14:48 에 «논문·발표에 그대로 들어갑니다» 라고 쓴 것은 **과했습니다.**
> 🔴 **남은 것 둘**: ① **그림 파일 재생성** — 스크립트 mtime 09-19 14:51~52 vs 그림 08-11 10:26·08-11 10:26·08-12 15:33
> (스크립트만 고쳐도 `reports/figures/` 의 pdf·png 는 옛 그림 그대로입니다) ② `tools/make_evidence_workflow_pdf.py`
> (08-12) L126·L282~283 이 여전히 «땅에 떨어진 과실은 라벨 없음»(단정) · «미라벨 … **유지**합니다» 라고 적어 둔 것.
> ⚠️ **제가 확인 못 한 것**: 옛 그림 파일 **안에** 옛 단정문이 박혀 있는지 — 폰트 서브셋 때문에 `pdftotext` 가
> 한글을 복원하지 못합니다(균일 시프트도 실패). 사람이 열어 보거나 재생성해 비교해야 합니다.
>
> 🔴🔴 **14:48 원래 기록 — 3-c 신설(당시 «가장 급한 것» 으로 판단).** 배경 grep 의 마지막 파일을 따라가 보니
> **우리 그림 2-1 캡션이 우리 데이터와 다른 말을 하고 있었습니다.** `tools/make_fig_crop_overlay.py:208`
> 이 그림에 단정문으로 *"※ 땅에 떨어진 과실은 라벨에 포함되지 않습니다. 따라서 위 개수는 «나무에 달린
> 과실»만 센 것입니다."* 를 찍는데, 실제로는 **사과 5장에 낙과가 라벨돼 있습니다**(교수님확인 10번).
> 논문 근거의 문제가 아니라 **사실관계 오류**이고, 이 그림은 `reports/figures/` 로 생성돼 논문·발표에
> 들어갑니다. → **M12**(가장 급함). 캡션을 고치기 전에는 **그림 2-1 을 발표에 쓰지 마십시오.**
>
> 🔴 **14:38 자체 정정** — 14:33 에 낸 1판에서 **2칸(2-f·3-a)을 제가 너무 후하게 줬습니다.**
> 배경 grep 이 늦게 끝나 «땅에 떨어진 과실» 규칙과 amodal 규칙이 **우리 쪽에서는 아직 «규칙 미정»**
> 이라는 사실(`문서/260917_교수님확인_7건.md` 2·9·10번)을 1판 집필 시점에 못 봤습니다. 아래는 정정 후입니다.

| 판정 | 칸 수 | 어느 칸 |
|---|---:|---|
| **일치** | **14** | 1-a·1-b·1-c·1-e · 2-a·2-b·2-c·2-d · 4-a·4-b · 5-a·5-b·5-c · 7 |
| **부분** | 5 | 3-b · 4-c · 5-d · 6-b · 6-c |
| **어긋남** | **5** | **1-d**(복숭아 초벌이 워터셰드 아닌 CC) · **1-f**(4-연결 ↔ 8-연결) · **2-f**(modal/amodal — **사과 안에서도** 섞임) · 🆕 **3-a**(라벨 범위 «규칙 미정» — 낙과 42장 중 5장만 라벨, 남은 사진 17장) · 🔴 🆕 **3-c**(그림 캡션 — **부분 해결**: 스크립트는 14:51~52 에 고쳐졌고 **그림 재생성 · 근거 PDF 스크립트**가 남음) |
| **근거 없음** | 2(+1) | 2-e(`other` 클래스) · 6-a(2,073,600 화소 = 교수님 지시) · 🆕 **2-f 의 사과 쪽**(MinneApple 원문에 **폴리곤 범위 명문이 없다**) |
| **오지정 정정** | 1 | 5-e(`demsar2006` 은 누수 근거가 **아니다**) |
| **PDF 없음/미대조** | 1 | 6-d(`singh2018snip`·`amarnath2026resolution`·`ullah2025camus`) |

항목 단위로:

| 항목 | 내용 | 판정 |
|---|---|---|
| 1 | 카운팅 = 마스크 → 거리변환 + 워터셰드 → 개체 → 개수 | **일치** (박성문 `instance_split.py` 는 `bargoti2017image` p.17 과 문장 단위로 같다) — 단 **툴 쪽 2건 어긋남** |
| 2 | 상자 = 개체별 tight box, 클래스 0/1/2 | **일치** (`lin2014coco` p.11 «tight-fitting bounding boxes from the annotated segmentation masks») — 단 **modal/amodal 1건 어긋남**, `other` 클래스 **근거 없음** |
| 3 | 라벨 범위 = 전경 나무의 과실만, 땅·배경 제외 | **논문 쪽 일치 · 우리 쪽 어긋남**(14:38 정정) — 두 원논문은 규칙이 명확한데(MinneApple p.4 · seo2024peach p.5) **우리는 규칙 미정**이고 데이터가 섞여 있다 |
| 4 | 개수 평가 지표 = MAE/RMSE/R² | **일치**(`farjon2023countingreview` p.16 식 (1)~(4)) — 단 **`counts.csv` 에 정답 칸이 없어 계산 불가** |
| 5 | 중복·근접 프레임 제거 + 촬영 단위 분할 | **일치**(`lin2014coco` p.11 · `hani2020minneapple` p.3 · `kapoor2023leakage` p.5 L1.4·L3.2) — 단 `demsar2006` 은 **주제가 다르다** |
| 6 | 2MP 비율 유지 리사이즈 · 마스크 NEAREST | **부분·근거 없음 섞임** + 핵심 논문 3편 **PDF 없음** |
| 7 | «AI 초벌 → 사람 확정» | 🔴 **일치** — 지시서는 «없으면 근거 없음» 으로 적으라고 했는데 **근거가 5편 있었다**(그 중 2편이 과수·블루베리 같은 분야) |

### 이번에 가장 중요한 세 가지

1. 🔴 **항목 7 은 «근거 없음» 이 아니었습니다.** `oh2025fruittreereview` p.23 이
   *"…use human-in-the-loop labeling, where a model is initially trained with a small number of labeled
   samples, and then unlabeled samples are segmented, and a human corrects the results."* 로
   우리 툴을 문장 그대로 적어 뒀고, **`ni2020blueberry`**(블루베리 논문)는 p.5 에서
   *"using generated annotation with manual correction could be as accurate as manual annotation"* 를
   **실측으로 보였습니다.** 툴의 존재 이유를 방어할 가장 좋은 인용입니다.
2. 🔴 **modal/amodal — 14:38 정정. 1판에서 제가 틀리게 적었습니다.**
   `hani2020minneapple` p.4 *"only provide annotations for fully or partially visible fruits"* 는
   «**어느 개체를** 라벨하나»(완전히 가려진 열매는 라벨 안 함) 이지 «**폴리곤이 가려진 데까지 덮나**»
   가 **아닙니다.** MinneApple 원문에 폴리곤 범위를 적은 문장은 **없습니다.**
   명문이 있는 것은 **복숭아뿐** — `seo2024peach` p.11 *"annotated at the pixel level, including
   obscured regions, referred to as 'amodal masks'"* = **amodal**.
   그리고 우리 실측(`문서/260917_교수님확인_7건.md` **9번**)은 오히려 **MinneApple 사진이 amodal**
   (가려진 데까지 원으로 통째 — 의심 상위 150개체 중 **92개**), **dataset1~3 은 modal** 이라
   **사과 한 과일 안에서 두 규칙이 섞여** 있습니다. 어쨌든 «지금은 modal» 한 줄은 **쓸 수 없습니다.**
3. 🔴 **`counts.csv` 로는 MAE/RMSE/R² 를 못 냅니다.** `farjon` p.16 식 (1) 이 `ei = yi − ŷi` 인데
   정답 `y` 칸이 없습니다. 정답은 박성문 `bbox_outputs/<과일>/gt_boxes/csv/detections.csv` 에 따로 있습니다.
4. 🔴 **라벨 범위도 우리 규칙이 아직 없습니다(14:38 추가).** 논문 두 편은 «땅에 떨어진 과실을 뺀다» 로
   명확한데(`hani2020minneapple` p.4 · `seo2024peach` p.5 *"except for dropped fruits"*),
   우리는 `260917_교수님확인_7건.md` **10번** 그대로 *"낙과가 보이는 42장 중 5장만 라벨돼 있습니다"* ·
   *"«규칙 미정» 으로 표시만 해 뒀습니다(폴더에 남은 사진 17장)"* 입니다.
   **좋은 소식**: 두 원저자가 모두 뺐다는 것이 확인됐으므로, 교수님께 질문만 던지던 것을
   **«빼는 것이 두 원논문의 규칙입니다» 라는 근거 있는 권고**로 바꿀 수 있습니다(M11).
5. 🔴 **그림 캡션 — 14:48 발견, 15:21 «부분 해결» 로 정정.**
   `tools/make_fig_crop_overlay.py:208` 캡션: *"※ 땅에 떨어진 과실은 라벨에 포함되지 않습니다.
   따라서 위 개수는 «나무에 달린 과실»만 센 것입니다."* — 단정문입니다.
   실제로는 사과 5장에 낙과가 라벨돼 있으므로 **위 개수는 «나무에 달린 과실»만 센 것이 아닙니다.**
   → **14:51~52 에 다른 사이클이 세 스크립트를 다 고쳤습니다.** 남은 것은 **그림 파일 재생성**과
   `make_evidence_workflow_pdf.py` 의 옛 문구뿐입니다(M12). 형제 그림 2·3 은 원래부터 정확했으므로
   제가 «논문·발표에 그대로 들어갑니다» 라고 쓴 것은 과했습니다.

---

## 3. 이번에 **고친 것** (문서만. 백업 남김)

| 파일 | 무엇을 | 백업 |
|---|---|---|
| `kds0206/문서/260918_툴_방향_녹취기준.md` | **§6 «논문 근거» 절 신설** — «AI 초벌 → 사람 확정» 이 교수님 지시뿐이 아님을 5편 인용문(쪽 포함)으로. 머리에 `최종 수정: 2026-09-19` | `kds0206/문서/_backup_260919_cnt2_260918_툴_방향_녹취기준.md` |
| `platform/05_ai_dialogues/근거문서/260812_디텍션논문_근거조사.md` | **§5 미결 2건을 닫음** — ① 포도 송이 단위 근거(`blekos2023grape` p.5 = CERTH 원논문 · `santos2020grapetracking` p.1·p.2) ② 워터셰드 한계 근거(`kornilov2022review` p.3 · `bargoti2017image` p.17) | `…/_backup_260919_cnt2_260812_디텍션논문_근거조사.md` |
| `platform/05_ai_dialogues/근거문서/260813_사진처리_전과정과_논문근거.md` | ① §3 «마스크 NEAREST = 공학 표준·인용 불필요» → **`isensee2021nnunet` p.17 인용**으로 교체 + 우리 순수 NEAREST 와 nnU-Net one-hot+argmax 의 차이를 명시 ② §5 «비율 유지» 에 `xie2021segformer` p.6 · `he2019resnetd` p.3 보조 근거 ③ §4 에 **«핵심 3편 PDF 없음» 경고** 신설(+ `huang2018tiling` p.1 재확인, `reina2020tiling` 도 PDF 있음) | `…/_backup_260919_cnt2_260813_사진처리_전과정과_논문근거.md` |

| 🆕 `kds0206/문서/260813_내가_한_일과_이론_출처.md` **(14:48)** | L88~89 의 «캡션에 «땅에 떨어진 과실은 라벨 없음» 명시 … ✅» 를 **«관행은 ✅ 이지만 우리 캡션의 «사실» 은 ❌»** 로 고침 + `seo2024peach` p.5 근거 추가 + «캡션을 고치기 전에는 이 그림을 발표에 쓰지 마십시오» | `kds0206/문서/_backup_260919_cnt2_260813_내가_한_일과_이론_출처.md` |

**고치지 않은 것(일부러)**

- 툴 코드 `app/boxes.py`·`app.js`·`ui.js`·`server.py`·`export_dataset.py`,
  `tools/build_merged_dataset.py` — **사이클 1 이 지금 쓰는 중**(14:06 `boxes.py`, 14:12 `server.py` mtime).
  지시서 규칙대로 손대지 않고 §4 로 넘겼습니다.
- `app/README.md` — 사이클 1 이 §1-5(상자 정의)를 쓸 예정이라 **충돌을 피해** §4 M4·M5·M6 로 넘겼습니다
  (11:59 이후 아직 안 건드려졌지만, 곧 쓰일 파일입니다).
- 데이터셋 파일(`datasets_*`) — 하나도 건드리지 않았습니다. 6-c(one-hot+argmax)는 **0920 재빌드 결정 목록**.
- 원본·검수판·`datasets_merged_*`·팀원 폴더·`01_references` — **읽기만** 했습니다. 실서버 접속·삭제·GPU·새 패키지 없음.

---

## 4. 수정 필요 목록 — 사이클 3·4 로 넘김

| # | 무엇 | 어디 | 대조표 칸 | 급함 |
|---|---|---|---|---|
| **M1** | 🔴 `boxes_seed` 가 번호 마스크 없는 과일(**복숭아**)에서 CC 대신 **워터셰드**(`distance_transform_edt` → `peak_local_max(min_distance=round(r*1.1))` → `watershed(-dist, markers, mask=binary)`, `RADIUS_PCT=90`·`MIN_AREA=10`)를 쓰게. **포도는 CC 유지**(송이 단위) | `app/boxes.py api_boxes_seed()` · `app/server.py labeled()` | 1-d | **높음** — CC 는 사과 정답 대비 −18.2% 과소계수(실측) |
| **M2** | 연결성분 이웃 규칙을 박성문과 맞춤(**8-연결** 권장). 사과 정답으로 4↔8 차이를 실측해 근거를 남긴다 | `app/server.py:1135 ndimage.label(arr)` | 1-f | 중간 |
| **M3** | 🔴 `counts.csv` 에 **`n_gt`·`gt_source`** 추가(사과·복숭아·포도는 `bbox_outputs/<과일>/gt_boxes/csv/detections.csv` 에서, 블루베리는 빈칸 — 정답이 없다) | 사이클 1 의 counts.csv · `build_merged_dataset.py` manifest | 4-c | **높음** — 없으면 지시서 §2 «계산 가능한가» 를 못 채운다 |
| **M4** | 🔴 **(14:38 정정)** «지금은 modal» **한 줄로 쓰지 않는다.** 사실은 «**복숭아 = amodal**(명문 p.11) / **사과 = 출처마다 섞임 — 규칙 미정**(교수님확인 9번) / 포도·블루베리 = 판정 불가». MinneApple 원문에 폴리곤 범위 명문 **없음** | `app/README.md` · 편집 화면 help | 2-f | **높음** |
| **M5** | 클래스 `2 other` → `trunk` 로 바꾸거나, 남기고 «논문 선례 없음 — 학습에 쓰지 않음» 을 README 에 명시. **교수님 질문**으로도 올린다 | `app/boxes.py:23 CLASSES` · README | 2-e | 중간 |
| **M6** | README·help 에 «포도 송이 상자는 알에 맞지 않는다(`santos2020grapetracking` p.2)» 한 줄 | `app/README.md` | 2-b | 낮음 |
| **M7** | **(14:38 정정)** 땅에 떨어진 과실은 **우리 규칙이 아직 없다** → 안내문보다 **교수님 결정이 먼저**. 그때까지 help 에 «낙과·뒷줄 나무는 규칙 미정 — 손대지 말고 그대로» 를 적고, 결정 뒤 **17장 재작업** | 편집 화면 help | 3-a · 3-b | 중간 |
| **M8** | `singh2018snip`·`amarnath2026resolution`·`ullah2025camus` **PDF 재확보** → 인용문 글자 대조. SNIP 은 ④ 겉보기 크기 통일의 **유일한 강한 근거** | `platform/01_references/` | 6-d | 중간(사이클 5 또는 사람) |
| **M9** | 마스크 크기 변경을 순수 NEAREST 로 둘지 nnU-Net 식 one-hot+argmax 로 바꿀지 결정 → **0920 재빌드 목록** | `resize_datasets_to_common_pixels.py` · `build_merged_dataset.py` | 6-c | 낮음 |
| **M10** | 논문·발표에서 `demsar2006statistical` 을 **누수 근거로 쓰지 않는다**(Friedman 검정 근거로만) | 모든 문서·Codex 질문 | 5-e | 중간 |
| **M12** | 🔴 **(15:21 범위 축소)** ~~캡션 문구~~ → **14:51~52 에 다른 사이클이 이미 고쳤습니다.** 남은 것 둘: ① **세 그림 재생성**(`fig_crop_overlay_4fruits` 08-11 · `fig_samples_annotated_4fruits` 08-11 · `fig_objects_per_image_4fruits` 08-12 — 전부 스크립트보다 오래됐다) ② `tools/make_evidence_workflow_pdf.py` **L126·L282~283** 의 옛 문구 수정 + 산출 PDF 재생성 | `reports/figures/` · `tools/make_evidence_workflow_pdf.py` | 3-c | 중간 |
| **M11** | 🆕 **(14:38)** 교수님확인 **2·9·10번**에 이번에 찾은 **원논문 근거**를 붙여 다시 올린다 — «MinneApple p.4 과 seo2024peach p.5 **두 원저자가 모두 낙과를 뺐습니다**» / «복숭아 원논문은 **amodal 이라고 명시**(p.11), MinneApple 은 폴리곤 범위를 **아예 적지 않았습니다**». 질문 → **근거 있는 권고**로 | `문서/260917_교수님확인_7건.md` | 2-f · 3-a | **높음** |

**교수님 질문에 추가할 것(사이클 5)**

1. amodal / modal — **(14:38 정정)** 복숭아 원논문은 **amodal 이라고 명시**하고, 사과는 **출처마다 섞여**(MinneApple 사진 amodal · dataset1~3 modal) 있으며 MinneApple 원문은 폴리곤 범위를 **아예 적지 않았습니다**. 이미 교수님확인 **9번**으로 올라가 있으니 **근거를 붙여 다시** 올립니다.
2. 포도 «송이 개수» 의 정의 — 알 몇 개 이상을 한 송이로 보나. 143편에 정의가 없습니다(WGISD·CERTH 도 정의 없이 씁니다).
3. 상자 클래스 `2 other` 를 `trunk`(MinneApple 관례)로 바꿀까요, 없앨까요?

---

## 5. 대조 못 한 것 (정직하게)

| 무엇 | 왜 |
|---|---|
| `singh2018snip` · `amarnath2026resolution` · `ullah2025camus` 인용문 | **PDF 없음** — INDEX 143편 미등재. `find /data/project/2026summer -iname "*snip*" -o -iname "*amarnath*"` → **0건** |
| `joshi2022agml` · `ma2021lossodyssey` 본문 | `pdftotext` 가 **17바이트 · 13바이트**만 뽑음(텍스트층 없음). 이번 항목과 직접 관계가 없어 OCR 안 함 |
| ~~툴 `counts.csv` **실제 헤더**~~ | ✅ **14:31 확인 완료** — 사이클 1 이 `app/README.md` **§19-3·§19-4** 에 적어 뒀고, 칸 10개(+manifest 5칸)에 **정답(`n_gt`) 칸이 정말 없습니다.** 4-c 는 추정이 아니라 구현 확인입니다 |
| 포도 «송이 개수» 의 정의 | 143편에 없음 → 교수님 질문 |
| 🆕 **낙과·amodal 규칙을 우리가 어떻게 정할지** | **논문 근거는 다 찾았지만**(두 원저자 모두 낙과 제외 · 복숭아 amodal 명문) **결정은 교수님 몫**입니다(교수님확인 2·9·10번, 사과 17장 대기). AI 가 정할 수 없습니다 |
| 🆕 **그림 2-1 을 실제로 다시 생성해 캡션이 바뀌는지** | 캡션 문구를 고치는 것은 **코드 수정**이라 사이클 3·4 몫입니다(M12). 저는 **발견하고 문서에 표시**만 했습니다 |
| 🆕 «MinneApple 폴리곤이 amodal 인가» 를 **원문으로** | 원문에 **명문이 없어** 우리 실측(상위 150개체 중 92개)으로만 말할 수 있습니다. 원문 근거는 **존재하지 않습니다** |
| «조각난 번호를 얼마나 멀리까지 한 상자로 묶나» | `bargoti2017image` p.17 이 «이어야 한다» 고만 하고 기준 거리를 안 적음 |
| 4-연결 vs 8-연결 중 어느 쪽이 옳은가 | 논문 근거 없음(구현 세부). **실측 비교 필요**(M2) |

---

## 6. 검수자(2차)가 재확인할 명령

```bash
# ① 쪽 번호까지 찍는 도구를 다시 만든다 (대조표 부록 A 와 같은 것)
cat > /tmp/pg.py <<'EOF'
import sys, re, subprocess
k, pat = sys.argv[1], sys.argv[2]
p = "/data/project/2026summer/platform/01_references/pdf/%s.pdf" % k
txt = subprocess.run(["pdftotext","-layout",p,"-"],capture_output=True,text=True).stdout
for i, pg in enumerate(txt.split("\f"), 1):
    for ln in pg.split("\n"):
        if re.search(pat, ln, re.I):
            print("p.%d | %s" % (i, ln.strip()))
EOF

# ② 어긋남 3건의 근거를 직접 본다
python3 /tmp/pg.py hani2020minneapple "fully or partially visible"        # 2-f 사과 = modal
python3 /tmp/pg.py seo2024peach     "amodal|including occluded areas"     # 2-f 복숭아 = amodal
python3 /tmp/pg.py bargoti2017image "computing distances of individual fruit pixels"   # 1-d
sed -n '46,54p' /data/project/2026summer/platform/work/park_seongmoon/semantic-segmentation/tools/instance_split.py   # FALLBACK peach=watershed, _S8
sed -n '1123,1143p' /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/app/server.py                 # labeled() = ndimage.label (4-연결)

# ③ 항목 7 이 정말 근거가 있는지
python3 /tmp/pg.py oh2025fruittreereview "human-in-the-loop"
python3 /tmp/pg.py ni2020blueberry "manual correction could be as accurate|iterative annotation strategy"

# ④ 오지정 정정이 맞는지 (demsar 는 누수 논문이 아니다)
python3 /tmp/pg.py demsar2006statistical "Multiple Data Sets|Friedman test"
python3 /tmp/pg.py kapoor2023leakage "Duplicates in datasets|Nonindependence between training"

# ⑤ PDF 가 정말 없는지
ls /data/project/2026summer/platform/01_references/pdf/ | grep -iE "snip|singh|amarnath|ullah"   # 0줄이어야 한다
find /data/project/2026summer -maxdepth 5 -iname "*snip*" -o -maxdepth 5 -iname "*amarnath*"     # 0줄이어야 한다

# ⑥ 내가 고친 문서의 백업이 남아 있는지 + 무엇이 달라졌는지
diff /data/project/2026summer/kds0206/문서/_backup_260919_cnt2_260918_툴_방향_녹취기준.md \
     /data/project/2026summer/kds0206/문서/260918_툴_방향_녹취기준.md
D=/data/project/2026summer/platform/05_ai_dialogues/근거문서
diff "$D/_backup_260919_cnt2_260812_디텍션논문_근거조사.md" "$D/260812_디텍션논문_근거조사.md"
diff "$D/_backup_260919_cnt2_260813_사진처리_전과정과_논문근거.md" "$D/260813_사진처리_전과정과_논문근거.md"
```

**2차 검수가 공격해야 할 곳** (내가 스스로 약하다고 보는 곳)

1. **2-b·6-b 처럼 «관행 근거»** 를 «일치/부분» 으로 적은 것 — 심사자 기준으로 충분한가?
2. **1-e(포도 CC)를 «일치» 로 준 것** — `blekos2023grape` 는 «송이로 라벨했다» 만 말하고
   «그러니 CC 로 세라» 고는 하지 않는다. 논리 한 칸이 우리 실측(+53.6%)으로 채워져 있다.
3. **4-b 의 MinneApple 수치** — Table IV 를 표 본문으로 읽지 않고 본문 문장(*"achieve between 95.5
   and 97.8% accuracy"*)만 인용했다. 표 안의 지표 이름을 안 봤다.
4. **부록 C 의 «조각난 번호» 칸** — `boxes_of()` 가 옳다고 적었지만 실제로 사과에서
   조각 병합이 정답과 맞는지 **숫자로 재지 않았다.**
