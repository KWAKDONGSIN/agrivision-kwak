작성: 2026-09-19

# 상자+개수 세기 5사이클 — 사이클 3 (공격적) 1차 작업: 논문 근거 대조표 **공격 검수**

작업 시각(`date` 실측): **16:42:59 시작** · 16:44~17:00 PDF 145편을 세 모드로 다시 뽑고 측정 5건 띄움 ·
17:00~17:14 인용 재대조·쪽번호 전수·순환 튜닝 실측 · 17:06~17:14 문서 3개 정정 · **17:18:56 포도 2,502장 전수 실측 끝** · 17:15~17:24 보고서·대조표 마무리(`date` 실측).
대상: `문서/260919_논문근거_대조표.md`(28칸, 2차 정정판) · 사이클 2 1차/2차/3차 기록 · 박성문 `instance_split.py`·`fruit_bbox.py` ·
툴 `app/boxes.py`·`app/server.py` · `build_merged_dataset.py`.
모래상자: `cycles/260919_count/cycle_3/stage1/`(내가 짠 도구 7개 + 측정 JSON). **툴 코드·데이터셋·팀원 폴더·`01_references` 는 한 글자도 쓰지 않았습니다.**

## §0. 한눈에 — 공격 10개의 결과

| # | 공격 | 결과 | 심각도 |
|---|---|---|---|
| 1 | 인용 위조·오독 재수색(51건) | **위조 0건 · 글자 불일치 0건**(내 도구로 세 모드 재대조). 그러나 **쪽 번호는 6편 22건이 논문에 옮길 수 없는 값**이고 1편은 **쪽이 한 칸 틀렸다**(kapoor p.5→**인쇄 p.4**), 1편은 **PDF 가 심사용 판과 섞여 있다**(seo2024peach) | 🔴 큼(인용 신뢰도) |
| 1b | 문맥 이탈 | **4건** — 4-b MinneApple 95.5~97.8%(Table IV 아님 = **Table V 수확량**) · 1-e zabawa «CC 로 센다»(**알 단위 + 경계 클래스 전제**) · 7 caicedo·santos(**반자동 보조 도구**) · 5-c MinneApple stride(**촬영 단계**, 누수 장치 아님) | 🔴 큼 |
| 2 | 코드 ↔ Bargoti 2017 줄 단위 | 4단계는 같고 **다른 단계 5개**(우리만의 숫자 4개 · 논문에 있는 형태학 전처리 없음 · CHT 없음 · 정답·매칭 규칙 다름 · **우리 숫자는 정답 마스크 입력**) | 🔴 큼 |
| 2b | 순환 튜닝 의심 | **절차는 순환이 맞다**(사과 전수로 고르고 같은 전수로 «+0.7%» 보고, 분리 없음). **그러나 무작위 절반으로 다시 재니 숫자는 그대로**(안 쓴 절반 편향 중앙 **+0.62%**) → **과대평가는 아니다.** 진짜 문제는 **값이 안 옮겨진다**(복숭아 최적 `peak_frac`=**0.9**, 1.1 은 −4.71%)와 **`radius_pct`=90 은 훑어 본 적도 없는데 민감하다**(사과 80→+5.82%, 95→−3.41%) | 🟠 중간(결론 유지, 문장 수정) |
| 3 | 포도 CC 조건(`maierhein` p.204) | **조건 둘 다 안 맞는다** — 닿아 있는 송이 쌍 있고, 송이의 **대부분이 조각나 있다**(§3-1) → 1-e 의 «일치» 는 **어긋남**으로 내려야 한다 | 🔴 큼 |
| 4 | 조각난 번호 숫자 | 사과는 **문제가 작다** — 조각난 개체 4-연결 **1.06%** · 8-연결 0.07%. CC 오차는 **거의 전부 «합쳐짐»**(merge 3,385 · fragment 0) | 🟢 작음(대조표 문장 보강만) |
| 5 | 2-f solidity 방법 | **타당하지 않다** — 현(직선)으로 50% 가려도 solidity 0.99(볼록). **높은 solidity 는 amodal 의 증거가 못 된다.** 2차의 «전수 분포로 재현 안 됨» 은 0.8% 소수 주장에 대한 반증이 아니다. 다만 **모든 크기 구간에서 두 출처 차이가 한 방향**(0.03~0.04)으로 남는다 | 🟠 중간 |
| 6 | 4-b 지표 이름 + 우리 지표 계산 | Table IV = *"Fruit cluster counting benchmark results"* = **패치 분류 counting accuracy(%)**. MinneApple 에 **MAE·RMSE·R² 없음**. 우리 지표는 지금 계산했다(§3-4) | 🔴 큼 |
| 7 | 누수 근거 | L1.4·L3.2 **인용 타당**(쪽만 정정). «시퀀스 프레임» 은 kapoor 에 **없는 말**(확장 적용). **L3.1 은 우리 경우 아님.** 덤: 같은 문단의 *"block cross-validation"* 이 **5-d 의 빈칸을 메운다**. 5-a 는 **부분**으로 내렸다(우리 `session` 이 논문보다 느슨 · 포도는 장치 없음). demsar 제거는 **표에서 확인**(5-e 오지정 정정 유지) | 🟠 중간 |
| 8 | 리사이즈·SNIP | 대조표는 정직했지만 **`260813` 문서의 표 행이 아직 «✅ 강함»** 이었다 → **고쳤다**. nnU-Net p.17 은 **전처리 절 = 우리와 같은 단계**(방법만 다름), zhao2019rmi 는 **손실 계산 문맥 = 단계가 다름** → 근거로 쓰지 말 것 | 🟠 중간 |
| 9 | HITL 5편 | **3편만 우리 흐름**(oh2025 · ni2020 · wu2026). caicedo·santos 는 **반자동 보조** → 대조표 수정 | 🟠 중간 |
| 10 | 표 형식 | 28칸 전부 **6칸·빈칸 0** ✅. 쪽 규약 절은 **4편만 다뤄 18편이 비어 있었다** → 21편 전수 표로 교체 | 🟢 |

**뒤집은 판정 3개**: 1-e 일치 → **어긋남** · 5-a 일치 → **부분** · 7 «5편 일치» → **3편 일치·2편 불일치**.
**뒤집지 못한 것**: 1-d(CC→워터셰드)·1-f·2-f·3-a 의 방향은 2차가 맞다. 2차의 인용 정정 3건도 전부 옳았다(재확인).

---
## §1. 인용 재대조 — 51건을 내 도구로 다시 뽑아 통짜 대조

### 1-1. 방법(2차 것을 쓰지 않고 새로 짬)

1. `01_references/pdf/*.pdf` **145편 전부**를 `-layout` · 기본 · `-raw` **세 모드**로 다시 뽑았다(`txt3/{layout,plain,raw}`, 각 145개).
2. **대조표 본문에서 인용을 기계로 긁었다**(`a1_extract.py`) — 2차가 손으로 옮긴 `quotes.tsv`(49건)를 믿지 않고
   표 행에서 «백틱 citekey → **p.N** → *"인용문"*» 순서를 훑어 **59건**을 뽑았다(그 중 8건은 우리 문서 인용 = 한글).
   → **PDF 대조 대상 51건**(2차가 센 49건보다 2건 많다).
3. 쪽별 텍스트를 한 줄로 눌러 합자(ﬁﬂ)·굽은 따옴표·줄끝 붙임표를 표준화하고 **인용문 전체가 그 쪽에 있는지** 봤다.
   줄임표(`…`)로 이은 인용은 **조각마다** 대조하고 «모든 조각이 같은 쪽에» 있어야 통과로 셌다(`a1_verify.py`).
4. 그 쪽에 없으면 **PDF 전체에서** 찾아 «쪽 틀림» 인지 «없음» 인지 갈랐다.

### 1-2. 결과 — 글자: 51건 전부 통과 · 지어낸 인용 0건

| 판정 | 건수 | 비고 |
|---|---:|---|
| **OK**(표가 적은 쪽에 통짜로 있다) | **50** | 세 모드 중 하나 이상에서 확인. **`-layout` 만으로는 18건이 안 잡힌다**(2단 조판이 좌우 단을 섞어 놓기 때문) — 기본 모드로 16건, `-raw` 로 나머지 2건(`seo2024peach` p.5)이 잡혔다. **세 모드를 다 뽑아야 하는 이유가 숫자로 확인된다** |
| OK(쪽 표기가 «(p.1 제목)» 형태라 내 정규식이 못 읽은 것) | 1 | `demsar2006statistical` 제목 — **p.1 에 있다**(확인). 대조표에서 demsar 가 나오는 곳은 5-e·집계·M10 뿐이고 **누수 근거 문맥에는 남아 있지 않다**(전문 `grep` 확인 = 지시서 7번의 «demsar 제거 확인» 통과) |
| 글자 불일치·MISSING | **0** | |
| 우리 문서 인용(한글, PDF 대조 대상 아님) | 8 | 교수님확인 7건·260917 실측 문장 등 |

**2차가 «정정» 한 3건은 전부 옳았다**(내가 다시 확인):
`he2019resnetd` 는 **p.2 에만** 있다(p.3 에는 없다 — 2차의 p.3→p.2 정정 맞음) ·
`zabawa2020counting` p.9 의 두 부분 캡션과 p.11 의 문장형 인용 **모두 그 쪽에 있다** ·
`seo2024peach` p.11 의 큰따옴표 표기도 원문대로다.

### 1-3. 🔴 그러나 쪽 번호는 2차가 절반만 잡았다 (21편 전수 재실측)

전수 표는 **대조표 머리말의 규약 절로 옮겨 넣었다**(이번에 교체). 요점만:

| 문제 | 편 수 | 인용 건수 | 무엇 |
|---|---:|---:|---|
| **PDF 쪽을 논문에 옮길 수 없다**(프리프린트·긴 부록판인데 `bib` 은 학술지 쪽을 가리킴) | **6** | **22** | `bargoti2017image`(JFR 34:1039–1060) · `hani2020minneapple`(RA-L 5:852–858) · `zabawa2020counting`(ISPRS 164:73–83) · `isensee2021nnunet`(Nat.Methods 18:203–211인데 **PDF 는 56쪽 프리프린트이고 제목까지 다르다** — *"Automated Design of Deep Learning Methods for Biomedical Image Segmentation"*, arXiv:1904.08128) · `maierhein2024metrics`(Nat.Methods 21:195–212인데 **PDF 는 210쪽 arXiv:2206.01653v8**, p.204 는 그 프리프린트의 쪽 — 출판판에도 204쪽이 있지만 **내용이 다르다**) · `caicedo2019dsb`(**PDF p.8 = 인쇄 p.1254** = 논문 범위 1247–1253 **밖** = 온라인 Methods) |
| **쪽이 한 칸 틀렸다** | 1 | 2 | `kapoor2023leakage` — 바닥글 «4 Patterns 4, 100804» → **PDF p.5 = 인쇄 p.4**. 2차는 이 논문을 «쪽번호 없음» 으로 분류했다 |
| **PDF 가 두 판이 섞여 있다** | 1 | (p.5 인용 2건) | `seo2024peach` — 4·5·7쪽 머리글이 «**x FOR PEER REVIEW**»(«4 of 15»·«5 of 15»)이고 1~3·8~14쪽은 출판판(«of 14»). **«except for dropped fruits» 인용이 심사용 판 쪽에 있다**(글자는 맞다). p.11(amodal 명문)은 출판판 쪽이라 안전 |
| 2차 분류가 반대로 된 것(효과는 없음) | 4 | — | `blekos2023grape`·`kornilov2022review`·`oh2025fruittreereview` 는 MDPI 바닥글 «N of M» 이 있어 **PDF쪽 = 인쇄쪽**(2차는 «쪽번호 없음» 이라 했다) · `he2019resnetd` 는 **쪽번호가 아예 없다**(2차는 «PDF쪽=인쇄쪽» 이라 했다) |
| 2차가 맞게 잡은 것 | 4 | — | `lin2014coco`(750·752 ✅) · `farjon2023countingreview`(1698 ✅ — 실은 그 쪽 머리글에 **직접 찍혀 있다**) · `wu2026agrimamba`(p.4 ✅) · `caicedo2019dsb`(«확인 필요» → 이번에 **1254** 로 닫음) |

### 1-4. 🔴 문맥 이탈 4건 (문장은 맞는데 뜻이 다르다)

| # | 칸 | 인용 | 원문의 문맥 | 우리가 쓴 뜻 | 조치 |
|---|---|---|---|---|---|
| ① | **4-b** | *"achieve between 95.5 and 97.8% accuracy with respect to the"* | **«C. Yield estimation» 절 + Table V** — 프레임을 **추적해 중복을 없애고 나무줄 양쪽을 합친** 뒤 **수확한 실제 열매 수**와 비교한 값. 문장 끝이 잘려 있어(«…with respect to the **harvested ground truth**») 이 사실이 감춰졌다 | «Table IV — MinneApple 은 정확도(%)로 보고» = **사진 단위 개수 정확도**처럼 읽힌다 | 🔴 대조표 4-b **고쳤다**(Table IV 원문·지표 이름·«MAE/RMSE/R² 없음» 명시) |
| ② | **1-e** | `zabawa2020counting` p.1 *"Each berry is then counted with a connected component algorithm."* | 초록. 세는 단위는 **알(berry)** 이고, 같은 논문 p.2 가 *"three classes, 'berry', 'edge' and 'background' so that every single berry is separated … by an edge"* 로 **경계 클래스를 둔 뒤에야** CC 를 쓴다 | «**송이**를 CC 로 세는 것의 근거» | 🔴 **1-e 판정을 내렸다.** 같은 논문을 1-d 에서는 «경계 없이 CC 면 합쳐진다» 는 근거로 쓰고 1-e 에서는 «CC 로 세도 된다» 는 근거로 쓰는 것은 **표 안에서 서로 어긋난다** |
| ③ | **7** | caicedo2019dsb «assisted annotation tool» · santos2020 «interactive image segmentation» | caicedo: *"expert biologists who manually delineated each object"*, 보조 도구는 **초분할로 고르기 쉽게** 한 것 / santos: *"the user can freely mark the image using **scribbles**"* | «AI 초벌 → 사람 수정» 5편 중 2편 | 🔴 대조표 7 **고쳤다** — 일치 3편·불일치 2편 |
| ④ | **5-c** | *"We then extracted every fifth image … every 30th image."* | «III. Image Collection» 절 — **영상에서 사진을 뽑는 단계**. 누수 방어는 따로 «different tree rows and different years» 로 했다 | «우리 stride 솎기 = 누수 장치의 직접 선례» | 🔴 대조표 5-c **고쳤다**(«솎기 자체의 선례» 로만) |

그 밖에 **문맥은 다르지만 표가 이미 밝혀 둔 것**: 6-c `zhao2019rmi`(손실 계산 중 다운샘플링 — 표에 적혀 있음. §4-2 에서 «근거로 쓰지 말 것» 으로 강화),
1-b `kornilov2022review` p.18(자기들 실험이 **3D 마이크로CT 사암 공극**이다 — 기법 문장이라 문제없지만, 인용은 **정의가 있는 p.3** 쪽이 안전).

---
## §2. 코드 ↔ 논문 절차 — 줄 단위로 나란히

### 2-1. 박성문 `instance_split.py` `split_instances()` ↔ Bargoti 2017 p.17(+ Zabawa 2020)

| 단계 | 우리 코드(줄) | Bargoti 2017 p.17 서술 | 판정 |
|---|---|---|---|
| ① 이진화 | `binary = raw > 0` (`label_instances:118`) | *"CHT on the **binary segmentation output**"* | 같다 |
| ②′ **형태학 전처리** | **없다** (`instance prompt.md` 4절: «opening / closing 은 기본 꺼 둔다») | *"For both detection operations, the segmentation output is **pre-processed with morphological erosion and dilation** to enforce local consistency."* | 🔴 **논문에 있고 우리에겐 없다** |
| ③ 거리변환 | `ndimage.distance_transform_edt(binary)` (`:72`) | *"this contour is evaluated by computing **distances of individual fruit pixels to the nearest background pixel**"* | 같다 |
| ④ 봉우리 = 중심 | `peak_local_max(dist, min_distance=md, labels=binary)` (`:76`) | *"resulting in a **local maximum** that is typically situated around the centre of each fruit"* | 같다 |
| ⑤ **봉우리 간격 기준** | `r = percentile(dist[binary], RADIUS_PCT=90)` → `md = max(2, round(r × PEAK_FRAC=1.1))` (`:73-74`) | **없다** — 논문은 간격·반지름 추정 기준을 한 줄도 적지 않았다 | 🔴 **논문에 없음 — 우리 선택** |
| ⑥ 마커 워터셰드 | `watershed(-dist, markers, mask=binary)` (`:81`) | *"The WS algorithm is used for separating connected objects…"* (마커 방식 자체는 `kornilov2022review` p.3 이 근거) | 같다 |
| ⑦ 잡티 버림 | `MIN_AREA=10` 화소 미만 버림 (`:34`, `:84-85`) | **없다** | 🔴 **논문에 없음 — 우리 선택** |
| ⑧ 이웃 규칙 | `_S8 = ones((3,3))` = **8-연결**(`:54`) ↔ 툴은 `ndimage.label` 기본 **4-연결** | **없다**(8-연결 선례는 `boatswainjacques2021shallot` p.5 — 단 **봉우리를 묶을 때**) | 🔴 **논문에 없음 — 우리 선택** + 도구 사이 불일치(1-f) |
| ⑨ 조각 잇기 | **없다** | *"the algorithm cannot merge fragments … To overcome this, we also tested **CHT**"* | 🔴 **논문에 있고 우리에겐 없다**(다만 논문도 최고 F1 은 WS) |
| ⑩ 정답·매칭 | 인스턴스 마스크 · 헝가리안 **IoU≥0.5**(박성문 `fruit_bbox.py` eval) | *"labelling them with a **circular marker with variable radius**"* + *"greedy **1-nearest neighbour**, one-to-one matching … within the annotated fruit region"* | 🔴 **다르다 — F1 0.858 을 우리 F1 과 나란히 놓으면 안 된다** |
| ⑪ 입력 마스크 | **정답 마스크**(`run.log`: `mask_source=gt`) | **CNN 이 예측한 마스크** | 🔴 **다르다 — 우리 «+0.7%» 는 «세는 알고리즘의 상한»** |

**Zabawa 2020 과의 차이**(1-e 관련): Zabawa 는 «berry/**edge**/background» **3클래스**를 학습해 알 사이에 경계를 만들고 나서 CC 를 쓴다.
우리 팀 표준 마스크는 **2클래스(열매/배경)** 다 → CC 로는 붙은 것을 못 나눈다(사과 −18.2% 의 이유). 즉 **Zabawa 를 따라 하려면 학습 쪽에 경계 클래스를 넣어야** 하고, 우리는 그 대신 워터셰드로 **후처리**한다. 대조표에 이 한 줄이 없다 → §5 에서 넣었다.

**내 재구현 검증**: 나는 `split_instances` 를 보고 **다시 적어**(`a2_tune.py split_mine`) 사과 1,001장에서 대조했다 —
**다른 장 0장, 합계 40,732 ↔ 40,732**. 즉 대조표의 «어디에 구현» 칸 설명은 **코드와 정확히 같다**(2차 판정 유지).

### 2-2. 🔴 순환 튜닝 의심 — 절차는 순환이 맞지만, 다시 재 보니 숫자는 견딘다

**(가) 순환은 사실이다.** 근거 3곳:
- `instance_split.py:35` 주석 *"PEAK_FRAC = 1.1 # … (**사과 정답으로 튜닝**)"* · 파일 머리 *"PEAK_FRAC 값은 그 검증으로 골랐다"*
- `validate_instance_split.py` — **사과 마스크 전수**(`datasets_resized_2mp/apple/masks` 1,001장)로 `--fracs` 를 훑는다. **학습/시험 분리가 없다.**
- 그 산출물 `semantic-segmentation/output/instance_split_validation.json`(08-10 17:54): `images 1001`, `fracs 1.0/1.1/1.2`, GT 40,464,
  1.1 의 `total_bias_pct` **+0.662%**. `instance prompt.md` §5.2 가 이 표를 그대로 싣고 *"1.1 은 총량 편향이 가장 작아서 기본값으로 쓴다"* 로 고른다.
  → **고른 근거와 발표하는 «+0.7%» 가 같은 1,001장이다.**

**(나) 그런데 분리해서 재 보면 숫자가 그대로다**(`a2_tune.py` + `a2_report.py`, 사과 1,001장 · `peak_frac` 5값 · 200회 무작위 절반).

| 무엇 | 값 |
|---|---|
| A(고른 반쪽)에서 본 편향 — 지금 발표 중인 «+0.7%» 와 **같은 성격** | 중앙 **+0.62%** (−0.99 ~ +1.00) |
| **B(고르는 데 안 쓴 반쪽)** 에서 본 편향 — **정직한 값** | 중앙 **+0.62%** (−1.82 ~ +1.32) · MAE 중앙 **2.05** |
| A 에서 «총량편향» 으로 고른 값 | 1.1 이 **172/200**회, 1.2 가 28회 |
| A 에서 «MAE» 로 고른 값 | 1.1 이 134/200, 1.2 가 66회 |

→ **과대평가가 아니다.** 5개 값 중 하나를 1,001장으로 고르는 정도의 «자유도» 는 편향을 부풀리지 않는다.
**그러므로 «+0.7%» 를 논문에서 내리라고 할 근거는 없다.** 다만 다음 세 가지를 반드시 적어야 한다.

**(다) 진짜 문제 세 가지**

1. **기준을 바꾸면 최적이 바뀐다** — 사과 전수에서 «총량편향»·«MAE» 는 1.1 이 최적이지만 **«20% 이내 이미지 비율» 은 1.2 가 최적**(96.6% ↔ 95.5%). 어느 기준으로 골랐는지 밝혀야 한다.
2. 🔴 **값이 다른 과일로 옮겨지지 않는다** — **복숭아 977알**(튜닝에 쓰지 않은 정답)에서:

   | `peak_frac` | 0.9 | 1.0 | **1.1(현재)** | 1.2 | 1.3 |
   |---|---:|---:|---:|---:|---:|
   | 총량 편향 | **−3.38%** | −3.79% | −4.71% | −5.42% | −6.45% |
   | MAE | **0.26** | 0.30 | 0.37 | 0.42 | 0.50 |

   **복숭아 최적은 0.9**(사과 값 1.1 은 MAE 가 **1.4배**). `instance prompt.md` §5.3 도 «peach 는 1.0 도 실험» 이라 적어 두었고 실제로 `bbox_outputs/peach/all_pf1.0/` 이 있는데, **통합에 쓰이는 `all/` 은 1.1** 이다. **블루베리는 정답이 없어 «사과 값을 빌려 쓴다»(§5.3) — 검증 불가.**
3. 🔴 **`radius_pct=90` 은 훑어 본 적이 없는데 민감하다**(§5.1 근거 칸이 «기존 코드» 뿐):

   | `radius_pct` | 80 | **90(현재)** | 95 |
   |---|---:|---:|---:|
   | 사과 총량 편향 | +5.82% | **+0.66%** | −3.41% |
   | 사과 MAE | 2.97 | **2.03** | 2.31 |
   | 복숭아 총량 편향 | **−2.66%** | −4.71% | −6.96% |
   | 복숭아 MAE | **0.21** | 0.37 | 0.54 |

   사과에서는 90 이 거의 최적이지만 **복숭아에서는 80 이 낫다.** 즉 «검증된 값» 이 아니라 **사과에 맞춰진 값**이다.

**(라) 판정** — «순환 튜닝이라 +0.7% 를 못 믿는다» 는 **틀렸다**(내가 분리해 재 봤다). 그러나
«사과 정답으로 고른 두 숫자를 네 과일에 그대로 쓴다» 는 **맞다**. 논문 문장은 이렇게 써야 한다:
«매개변수는 **사과 정답으로 골랐고**(peak_frac 1.1, radius_pct 90), 복숭아·블루베리에는 **그대로 옮겨 썼고**(포도는 워터셰드를 껐다).
복숭아 정답으로 확인하면 0.9 가 더 맞았으나(MAE 0.26 ↔ 0.37) 과일마다 다른 값을 쓰지 않기 위해 1.1 로 두었다.»
(이 문장은 사실이고, 고정 설정을 쓴 이유도 설명한다.)

---
## §3. 실측 — 포도 CC 조건 · 조각난 번호 · solidity · 지표

### 3-1. 포도: `maierhein2024metrics` p.204 의 조건을 실제로 만족하는가 → **둘 다 아니다**

인용문은 조건이 **둘**이다 — *"(in case of **purely non-touching** and **connected** instances)"*.
CERTH 정답 송이(COCO RLE)를 **원본 해상도에서 그대로 펴서** 직접 셌다(`a3_grape.py`, 내 코드. RLE 해독만 박성문 `grape_gt.py` 를 읽기 전용으로 씀).

| 조건 | 무엇을 셌나 | 포도 2,502장 · 정답 송이 9,832 |
|---|---|---|
| ① **non-touching**(닿지 않음) | 4-이웃에서 **서로 다른 송이 id 가 맞닿는 곳** | **닿아 있는 송이 쌍 1,932개** · 그런 송이 **3,087개 = 전체의 31.4%** · **사진 1,029장(41.1%)** 에 닿은 쌍이 있다 |
| ② **connected**(한 덩어리) | 송이마다 연결요소 수(10화소 이상 조각만) | **조각난 송이 43.5%**(4-연결) · 송이당 평균 **1.85조각** · 최대 **22조각** · 조각 합계 **18,202**(송이 9,832 → **+8,370조각**) |
| 결과 | 이진 마스크를 CC 로 세면 | **CC 4-연결 15,937(+62.1%)** · CC 8-연결 15,815(+60.9%) |
| 오차의 정체 | CC 하나에 든 서로 다른 송이 / 한 송이가 걸친 CC 수 | **합쳐짐 1,898** ↔ **쪼개짐이 압도적**(잡티까지 세면 58,853, 10화소 이상 조각만 세면 위의 +8,370) |

※ 참고 — 조각 수를 «10화소 미만 잡티까지» 세면 송이당 평균 52조각(200장 표본)까지 올라간다. 위 표는 **`MIN_AREA=10` 을 적용한 정직한 값**이다.


**판정**: 조건 ①(닿지 않음)도 ②(한 덩어리)도 **만족하지 않는다.** 특히 ② 가 심하다 — 포도 CC 오차는
«합쳐짐» 이 아니라 **«쪼개짐»** 이고, 그래서 **과대 계수**(+53.6%, 박성문 `bbox_outputs/grape/all/eval/summary.md`)가 난다.
같은 파일의 객체 단위 평가도 **P 0.506 · R 0.778 · F1 0.613 · split err 35.8%** 다.
참고로 포도에 **워터셰드를 켜면 더 나빠진다**(`grape/cv1_test_ws_on`: **+123.5%**, F1 0.534) — **어느 쪽으로도 못 센다.**

→ 그래서 1-e 의 «일치» 는 유지할 수 없다. 살아남는 것은 **«라벨을 송이 단위로 둔다»**(blekos p.5 · santos p.1)이고,
**«그래서 CC 로 세면 된다»** 는 근거가 아니다. `maierhein` p.204 는 오히려 **우리가 조건을 어겼다는 증거**다.

### 3-2. 「조각난 번호」 — 사과에서는 작다 (검수판 429장 · 개체 17,566)

| 이웃 규칙 | 조각 1개 | 2개 | 3개 이상 | 최대 | 조각난 개체 비율 | 조각 합계 |
|---|---:|---:|---:|---:|---:|---:|
| 4-연결 | 98.9% | 0.9% | 0.1% | 5 | **1.06%** | 17,787 (+221) |
| 8-연결 | 99.9% | 0.1% | 0.0% | 3 | **0.07%** | 17,579 (+13) |

세 가지에 주는 차이:

| 세는 방식 | 조각난 개체 하나를 몇으로 세나 | 사과 429장 합계 | 정답(17,566) 대비 |
|---|---|---:|---:|
| **상자**(`boxes_of`, 번호마다 `find_objects` 슬라이스) | **1개**(조각 전체를 한 상자로 감싼다) | 17,566 상자 | — (정답과 같음) |
| **개수**(번호 수) | **1개** | 17,566 | — |
| **CC 세기**(4-연결) | **조각마다 1개** | 14,377 | **−18.2%** |
| **CC 세기**(8-연결) | 조각마다 1개 | 14,182 | −19.3% |

**CC 오차의 분해(8-연결)**: 합쳐진 개체(merge) **3,385** · 쪼개진 조각(fragment) **0**.
즉 **사과에서 CC 의 병은 전부 «합쳐짐»** 이고, 조각남은 사실상 없다(4-연결에서도 +221개뿐).
→ 대조표 부록 C 의 숙제(«`boxes_of` 가 조각을 한 상자로 묶는 것이 옳은가»)는 **숫자로 닫힌다**:
사과에서 영향받는 개체가 **1.06%**, 8-연결로 보면 0.07% 다. 반대로 **포도는 조각남이 지배적**(§3-1)이므로
«조각을 한 상자로 묶는다» 는 규칙이 **포도에서 훨씬 중요**하다 — 대조표는 이 대비를 적지 않았다.

### 3-3. 2-f 의 solidity 방법 — 판정 도구가 될 수 없다

**(가) 이론값**(반지름 60화소 원반, `a5_solidity.py`)

| 모양 | solidity |
|---|---:|
| 완전한 원반 (= amodal 이상형) | **0.9895** |
| 현(직선)으로 10% 베어 냄 (modal) | 0.9917 |
| 현으로 30% 베어 냄 (modal) | 0.9907 |
| **현으로 50% 베어 냄** (modal) | **0.9896** |
| 가운데를 잎 띠 10 / 20 / 30화소가 지나감 | 0.887 / 0.784 / 0.684 |
| 한쪽만 잎 띠 10 / 20 / 30화소 | 0.938 / 0.886 / 0.836 |

→ **볼록하게 잘린 가림**(앞 열매·굵은 가지·사진 테두리)은 **절반이 가려져도 solidity 가 안 내려간다.**
그래서 «solidity 가 높다 → amodal» 은 **성립하지 않는다**(역방향 «낮다 → modal» 만 쓸 수 있다).

**(나) 2차의 지적 중 맞는 것과 틀린 것**

- ✅ 맞다 — 1차가 쓴 «의심 상위 150개체» 는 **일부러 치우치게 고른 표본**이다. 그렇게 뽑은 92/150 을 «실측» 으로 단정하면 안 된다.
- ❌ 틀렸다 — «전수 분포로 재현되지 않았다» 는 **반증이 아니다.** 92개는 MinneApple 계열 개체 11,885개의 **0.8%** 이고, 중앙값은 0.8% 를 볼 수 없다.
- ➕ 새로 — **크기 효과를 뺀 비교에서 차이가 한 방향으로 남는다**(중앙 solidity):

| 면적 구간(화소) | 100~300 | 300~600 | 600~1200 | 1200~2500 | 2500~5000 | 5000+ |
|---|---:|---:|---:|---:|---:|---:|
| MinneApple 계열 | 0.895 | 0.909 | 0.926 | 0.941 | 0.955 | 0.966 |
| dataset1~3 | 0.862 | 0.887 | 0.896 | 0.911 | 0.938 | 0.961 |

  개체 크기 중앙값은 오히려 dataset1~3 이 크다(1,357 ↔ 1,203화소)고, 테두리에 닿은 개체는 2.7%·3.4% 뿐이므로
  **크기·테두리로 설명되지 않는다.** 즉 «두 출처의 라벨 관행이 다르다» 는 **신호는 살아 있다.**

**판정**: 2-f 는 여전히 **어긋남(우리 데이터 안에서 섞임) + MinneApple 쪽 근거 없음** 이 맞다.
다만 어느 쪽으로도 **solidity 로 판정하지 말 것** — 사람이 그림을 보고 정하는 문제다(교수님 결정 9번).

### 3-4. 4-b 의 지표 이름과, 우리 지표 계산 (지금 낸 값)

**(가) MinneApple 이 실제로 보고한 것**(PDF p.6 원문 확인)

| 표 | 캡션 | 무엇을 보고했나 | 값 |
|---|---|---|---|
| **Table IV** | *"Fruit cluster counting benchmark results."* | 본문 *"Table IV shows the **counting accuracy**"* — 패치를 «열매 몇 개» 부류로 분류하는 방법(*"classify the fruits into k distinct classes"*, ResNet50, 6부류)의 **정확도(%)** | GMM 88.0·81.8·77.2·76.1 / CNN 88.8·92.68·95.1·88.5 (Dataset 1~4) |
| **Table V** | *"Yield estimation results in terms of fruit counts."* | **수확량** — 추적으로 중복 제거 + 나무줄 양쪽 합산 후 **수확한 실제 열매 수** 대비 | 여기서 나온 문장이 «95.5~97.8%» 다 |
| — | — | **MAE·RMSE·R² 는 논문에 없다**(전수 검색) | — |

**(나) 우리 지표**(`a6_metrics.py`. 사진 한 장 = 표본 하나. R² = 1−SSres/SStot)

| 과일 | 방법 | 합계 | 총량 편향 | MAE | RMSE | R² |
|---|---|---:|---:|---:|---:|---:|
| **사과 1,001장**(정답 40,464) | 툴 초벌 CC(4-연결, `min_px=4`) | 33,708 | −16.7% | 6.76 | 8.93 | 0.883 |
| | 박성문 8-연결 CC | 33,098 | −18.2% | 7.36 | 9.67 | 0.863 |
| | **박성문 워터셰드** | 40,732 | **+0.7%** | **2.03** | **2.97** | **0.987** |
| | 팀원 상자(박성문 = 임성후) | 40,833 | +0.9% | 2.00 | 2.93 | 0.987 |
| | (툴의 «번호» = 정답 파일 그대로) | 40,467 | +0.0% | 0.00 | 0.05 | 1.000 |
| **복숭아 125장**(정답 977) | 툴 초벌 CC(4-연결) | 890 | −8.9% | 0.70 | 1.23 | 0.960 |
| | 박성문 8-연결 CC | 888 | −9.1% | 0.71 | 1.26 | 0.958 |
| | **박성문 워터셰드** | 931 | −4.7% | 0.37 | 0.82 | 0.982 |
| | 팀원 상자(박성문 = 임성후) | 939 | −3.9% | 0.30 | 0.73 | 0.986 |
| | (툴의 «번호» — 복숭아는 이진 마스크라 **장당 1개**) | 125 | −87.2% | 6.82 | 9.17 | −1.24 |

읽는 법 세 가지(대조표에 없던 것):
1. **사과의 «번호» 줄은 성능이 아니다.** 툴이 읽는 번호 마스크가 **정답 파일 그 자체**라 MAE 0 이 당연하다. 논문에 실으면 안 된다.
2. **복숭아의 «번호» 줄은 툴의 현재 결함을 보여 준다**(이진 마스크에 번호가 없어 장당 1개) — 1-d 의 M1 이 필요한 이유.
3. 🔴 **`n_team_park` 와 `n_team_im` 은 독립 확인이 아니다** — 두 팀원의 `all/json` 개수가 **사과 1,001장·복숭아 125장 전부에서 한 장도 다르지 않다**(40,833·939). counts.csv 의 두 칸을 «서로 대조» 로 쓰면 안 된다.
4. 블루베리는 정답이 없어 표에서 뺀다(대조표 4-c 와 같은 결론). 포도는 **정답은 있으나 세는 단위가 미정**이라 빼야 한다(§3-1).
5. **박성문 파이프라인이 이미 MAE 를 내고 있다**(`bbox_outputs/<과일>/all/eval/{counting.csv,summary.md}` §7.2) — 4-a 의 «아직 계산 스크립트 없음» 은 사실과 다르다. 없는 것은 **RMSE·R²** 뿐이고, 위 표가 그것이다. 내 값은 박성문 summary 와 **일치**(사과 CC 33,098·−18.2%, 워터셰드 40,833·MAE 2.00).

---
## §4. 누수 · 리사이즈 · HITL 판정

### 4-1. 누수(5-a·5-b·5-c·5-d·5-e)

| 물음 | 실제로 원문에 무엇이 있나 | 판정 |
|---|---|---|
| `kapoor2023leakage` L1.4·L3.2 가 «시퀀스 프레임 분할 누수» 를 말하나 | **그런 말은 없다.** 전수 검색: `frame`·`sequence`·`adjacent`·`video` 가 이 뜻으로 **0건**. 있는 것은 L1.4 «중복», L3.2 «**the same people or units**» 다. 우리 «근접 프레임» 은 L3.2 의 **확장 적용** | **인용은 타당 · 문장은 «확장 적용» 으로 써야 함**. 쪽은 **인쇄 p.4**(PDF p.5) |
| L3.1 Temporal leakage 를 쓸 수 있나 | *"When an ML model is used to make predictions about a **future outcome**… the test set should not contain any data from a date before the training set"* — **미래 예측 문제 전용** | 🔴 **우리 경우가 아니다. 끌어오면 안 된다** |
| 덤 — `GroupKFold`(5-d) 의 근거 | 같은 L3.2 문단이 *"Methods such as \"**block cross-validation**\" can partition the dataset strategically so that the performance evaluation does not suffer from data leakage and overoptimism."* 로 **해법을 이름까지 들어 준다** | ✅ **5-d 의 «원리는 있고 함수 이름만 없다» 를 이 문장이 메운다** |
| Häni 2020 의 시퀀스 분할이 우리 `session` 과 같은 단위인가 | 🔴 **다르다.** 논문은 *"Data for the train/test splits are taken from **different tree rows and different years**"* / *"Acquiring datasets during different years guarantees the independence of the test set"* 다. 우리 `session` 은 ① 사과 = 파일명 앞부분(한 촬영) ② 블루베리 = «Camera N Video (X)» ③ 복숭아 = 날짜+나무 ④ **포도 = 사진 한 장**(`grape_session()` 이 `stem` 을 돌려준다). **같은 나무줄의 다른 촬영이 학습·시험으로 갈라질 수 있다** | **5-a 를 «부분» 으로 내렸다.** 생성 스크립트 자신이 이미 자백해 두었다: «포도는 `session` 으로 GroupKFold 를 돌려도 **사실상 무작위 분할**… 포도에는 지금 **누수를 막는 장치가 없습니다**»(`build_merged_dataset.py:2160`) |
| MinneApple 의 stride(5-c) | «III. Image Collection» 절 = **영상에서 사진 뽑는 단계**. 누수 방어는 나무줄·연도로 따로 했다 | **«솎기 자체» 의 선례로만** |
| `demsar2006statistical` 제거(5-e) | 표에 **«오지정 정정» 으로 남아 있다**(누수 근거 아님, Friedman 근거로만). 내가 대조표 전문을 다시 훑어 **누수 문맥에 demsar 가 남아 있지 않은 것**을 확인했다 | ✅ **확인** — 남은 일은 다른 문서·Codex 질문에서 빼는 것(M10) |

### 4-2. 리사이즈(6-a~6-d)

- **SNIP·Amarnath·Ullah 3편** — 대조표 6-d 는 «PDF 없음/미대조» 로 **정직했다.** 그런데 🔴 **`260813_사진처리_전과정과_논문근거.md` 의 §3·§4 표에는 아직 «✅ 강함»(SNIP)·«⚠️ 보조» 가 인용문까지 달려 있었다.** 경고는 표 아래 164~167행에만 있어서, 표만 옮겨 적는 사람은 «대조된 근거» 로 착각한다 → **표 행마다 «🔴 서버에 PDF 없음 — 글자 대조 못 함» 을 박아 넣었다.** `kds0206/문서/260813_내가_한_일과_이론_출처.md` L72 의 «SNIP / Huang 2018, **둘 다 arXiv 원문 확인**» 도 고쳤다(Huang 은 PDF 가 있어 대조됨, SNIP 은 없음).
- **nnU-Net p.17 의 문맥** — 원문은 *"Segmentation maps are resampled by converting them to one hot encodings. Each channel is then interpolated with linear interpolation and the segmentation mask is retrieved by an argmax operation."* 이고 이 절은 **데이터 전처리(resampling)** 다 → **우리와 같은 단계**다. 다른 것은 **방법**뿐(우리 = 순수 NEAREST, nnU-Net = one-hot+linear+argmax, nearest 는 비등방 축에만). 그러므로 **6-c 의 «부분» 판정은 정확하다.**
- **`zhao2019rmi` p.8 은 단계가 다르다** — Table 3 캡션이고 문맥은 *"reserves most information after downsampling"* = **손실 계산 중의 다운샘플링**이다. 표도 그렇게 적었지만, 3차 권고는 한 걸음 더: **논문·발표에서 zhao 를 근거로 들지 말 것**(«관행» 예시로만). 근거로는 **nnU-Net 을 쓰고 우리와의 차이를 밝히는** 것이 방어가 된다.

### 4-3. HITL 5편(7) — 3편만 우리 흐름

| # | 인용 | 원문이 말하는 것 | 우리 흐름(모델이 다 내놓고 사람이 확정)과 |
|---|---|---|---|
| ① | `oh2025fruittreereview` p.23 | *"**human-in-the-loop labeling**, where a model is initially trained with a small number of labeled samples, and then unlabeled samples are segmented, and **a human corrects the results**"* (반지도학습 문단 안의 서술) | ✅ **같다**(과수 분야) |
| ② | `ni2020blueberry` p.1·p.5 | *"An **iterative annotation strategy** was developed"* / *"using **generated annotation with manual correction** could be as accurate as manual annotation"* — 모델이 만든 마스크를 사람이 고쳐 학습에 썼고 mAP 가 맞먹었다(단 mIoU 는 0.004 낮았다) | ✅ **같다**(블루베리) |
| ③ | `wu2026agrimamba` p.5 | *"SAM … to generate initial **pre-annotations** … undergo **manual verification and refinement**"* | ✅ 같다(식물 병해) |
| ④ | `caicedo2019dsb` p.8 | 앞 문맥이 *"The annotations were created by expert biologists who **manually delineated each object**"* 이고, 보조 도구는 *"precomputed **superpixel** segmentations to facilitate the **selection** of regions"* = **사람이 고르기 쉽게** 한 초분할 | 🔴 **다르다 — 반자동 보조 도구**(AI 가 개체를 내놓지 않는다) |
| ⑤ | `santos2020grapetracking` p.2·p.4 | *"an annotation tool based on **interactive image segmentation** by graph matching"* + *"the user can freely mark the image using **scribbles**"* | 🔴 **다르다 — 사람이 지시하는 대화식 분할** |

→ 대조표 7 을 **«일치 3편 · 불일치 2편»** 으로 고쳤다. **툴의 존재 이유를 방어하는 가장 좋은 인용은 여전히 ②**(블루베리에서 «고친 자동 라벨 ≈ 수작업 라벨» 을 보였다)이고, ①은 **과수 리뷰 논문에 우리 흐름이 그대로 적혀 있다**는 점에서 값이 크다.

---
## §5. 지금 고친 것 (문서만. 코드·데이터셋은 손대지 않았다)

| 파일 | 무엇을 고쳤나 | 백업 |
|---|---|---|
| `kds0206/문서/260919_논문근거_대조표.md` | ① 머리말 **쪽 번호 규약 절을 21편 전수 표로 교체** ② **1-a** 일치→**부분**(다른 단계 5개) ③ **1-d** «정답 마스크 입력» 단서 + 툴에 이미 있는 워터셰드 초벌 경로 ④ **1-e** 일치→**어긋남**(포도 조건 실측 + zabawa 문맥) ⑤ **2-f** solidity 이론값·구간별 실측 ⑥ **4-a** «계산 스크립트 없음» 정정 ⑦ **4-b** Table IV↔V 정정·지표 이름 ⑧ **4-c** 정답 세 값·팀원 두 칸 동일 ⑨ **5-a** 일치→**부분** ⑩ **5-b** 인쇄 p.4·단서 4개 ⑪ **5-c** 문맥 ⑫ **6-c** 인용 두 편의 격 ⑬ **6-d** 260813 문서 문제 ⑭ **7** 5편→3편 ⑮ 판정 집계 갱신(일치 11·부분 7·어긋남 6) ⑯ 부록 C 숙제 2칸 닫음 ⑰ 부록 E **M13·M14·M15** 신설 ⑱ **부록 G 신설** | `문서/_backup_260919_cnt3_260919_논문근거_대조표.md` |
| `platform/05_ai_dialogues/근거문서/260813_사진처리_전과정과_논문근거.md` | §3·§4 표의 SNIP·Amarnath·Ullah 행에 «🔴 서버에 PDF 없음 — 글자 대조 못 함» · SNIP «✅ 강함» → «판정 보류» · 기호 설명 아래 경고 한 줄 · `최종 수정` 줄 | `…/_backup_260919_cnt3_260813_사진처리_전과정과_논문근거.md` |
| `kds0206/문서/260813_내가_한_일과_이론_출처.md` | «둘 다 arXiv 원문 확인» → Huang 은 대조, **SNIP 은 서버에 PDF 없음·미대조** · `최종 수정` 줄 | `문서/_backup_260919_cnt3_260813_내가_한_일과_이론_출처.md` |

**일부러 고치지 않은 것**: 툴 코드(`app/*`)·`build_merged_dataset.py`·`instance_split.py`·데이터셋·검수판·팀원 폴더·`01_references`.
`app/README.md`·편집 화면 help 는 사이클 1·4 가 쓰는 중이라 **§6 목록으로 넘겼다.**

---

## §6. 사이클 4 로 넘기는 «수정 필요» 목록 (3차가 새로 만든 것 + 기존 M 목록에 대한 3차 의견)

| # | 무엇 | 어디 | 근거 |
|---|---|---|---|
| **M1**(기존) | 번호 없는 과일(복숭아)의 초벌을 CC → 워터셰드로 | `app/boxes.py api_boxes_seed()` | 유지. 🆕 **3차 제안: 다시 구현하지 말고 `source=team:<이름>` 을 기본으로 돌려라** — 그 파일이 이미 박성문 워터셰드 출력이다(`params: peak_frac 1.1, radius_pct 90`). 복숭아 실측 MAE 0.30(팀원 상자) ↔ 0.70(툴 CC) |
| **M2**(기존) | 4↔8 연결 통일 | `app/server.py:1135` | 🆕 **3차 의견: 서둘 일이 아니다.** 사과에서 **4-연결이 더 정확**(MAE 6.76 ↔ 7.36)하고 조각남은 1.06% 뿐이다. M1 을 하면 CC 자체가 빠진다 |
| **M4·M7**(기존) | README·help 문장(modal/amodal · 낙과 규칙 미정) | `app/README.md`·help | 유지. 🆕 **3차: «solidity 로 판정» 같은 말은 쓰지 말 것**(§3-3) |
| **M12**(기존) | 그림 3종 재생성 + `make_evidence_workflow_pdf.py` 옛 문구 | `reports/figures/`·`tools/` | 유지(3차는 그림을 만들지 않았다 — 기존 산출물 덮어쓰기 금지 규칙) |
| 🆕 **M13** | 분할 단위가 논문보다 느슨하다는 각주(포도는 장치 없음) | 논문 Methods · README | §4-1 |
| 🆕 **M14** | **포도를 개수 지표에서 빼거나** «세는 방법 미정» 각주 + `FALLBACK["grape"]="cc"` 는 차선이라고 주석 | 문서(코드 주석은 사이클 4) | §3-1 |
| 🆕 **M15** | 매개변수 문장 고치기(«사과 정답으로 골랐고 다른 과일에 옮겨 썼다» + «정답 마스크 입력 = 상한») | 논문 Methods·`260812_카운팅방법_근거_확정본.md` | §2-2 |
| 🆕 **M16** | `counts.csv` 의 `n_team_park`·`n_team_im` 이 **같은 값**임을 README 에 적거나 한 칸으로 줄인다 | `app/README.md`·`export_dataset.py` | §3-4 |
| 🆕 **M17** | **RMSE·R² 계산을 어디에 둘지 정한다** — 박성문 eval 에 붙이거나(그쪽에 MAE 가 이미 있다) 우리 쪽 스크립트로. 3차 값은 `stage1/a6_metrics.py` 에 있다 | 학습·평가 쪽 | §3-4 |
| 🆕 **M18** | **예측 마스크로 세 본 값이 아직 없다** — 지금 모든 개수 숫자는 `mask_source=gt`(정답 마스크)다. 폴드 시험 마스크로 한 번 돌려 «파이프라인 개수 오차» 를 내야 논문 표가 완성된다 | 박성문 `fruit_bbox.py --mask-source pred` | §2-1 ⑪ |
| 🆕 **M19** | `seo2024peach.pdf` 를 **출판판으로 다시 받아** p.5 인용 쪽을 확정한다(지금 파일은 4·5·7쪽이 심사용 판) · `bargoti`·`hani`·`zabawa`·`isensee`·`maierhein` 은 **출판판 쪽을 확인**하거나 절·표 번호로 인용 | `01_references/`(사람이) | §1-3 |

---

## §7. 검수자가 그대로 다시 돌릴 명령

```bash
S=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/cycles/260919_count/cycle_3/stage1

# ① PDF 145편을 세 모드로 다시 뽑기 (약 4분)
mkdir -p $S/txt3/{layout,plain,raw}
for f in /data/project/2026summer/platform/01_references/pdf/*.pdf; do b=$(basename "$f" .pdf)
  pdftotext -layout "$f" "$S/txt3/layout/$b.txt"; pdftotext "$f" "$S/txt3/plain/$b.txt"; pdftotext -raw "$f" "$S/txt3/raw/$b.txt"; done

# ② 대조표에서 인용을 기계로 긁고, 세 모드로 통짜 대조 (51건)
python3 $S/a1_extract.py > $S/a1_quotes.json
python3 $S/a1_verify.py                    # OK 50 · 쪽표기를 못 읽은 1(demsar 제목, p.1 에 있다) · 우리문서 8 · 불일치 0

# ③ 인용문 앞뒤 문맥 보기 (문맥 이탈 찾기)
python3 $S/a1_ctx.py hani2020minneapple "achieve between 95.5 and 97.8" 1200
python3 $S/a1_ctx.py zabawa2020counting "Each berry is then counted with a connected component algorithm" 900
python3 $S/a1_ctx.py caicedo2019dsb "assisted annotation tool that precomputed superpixel" 800
python3 $S/a1_ctx.py santos2020grapetracking "interactive image segmentation" 700

# ④ 쪽 번호 전수 (PDF쪽 ↔ 인쇄쪽) + 인용한 쪽의 머리글·바닥글 그대로 보기
python3 $S/a1_pgnum2.py
python3 $S/a1_pghead.py                    # 필요하면 citekey 를 인수로
grep -nE "[0-9]+ of [0-9]+" $S/txt3/layout/seo2024peach.txt | head   # 심사용 판 섞임 확인

# ⑤ 순환 튜닝 (사과 1,001장 · peak_frac 5값 · radius_pct 2값 · 약 9분, 워커 12)
python3 $S/a2_tune.py && python3 $S/a2_report.py

# ⑥ 포도 CC 조건 (2,502장 · 약 25분, 워커 8)  / 200장만 보려면 인수 200
python3 $S/a3_grape.py

# ⑦ 조각난 번호 (검수판 사과 429장 · 약 1분)
python3 $S/a4_frag.py reviewed

# ⑧ solidity 이론값 + 구간별 실측
python3 $S/a5_solidity.py

# ⑨ MAE·RMSE·R² (사과 1,001 + 복숭아 125 · 약 7분)
python3 $S/a6_metrics.py

# ⑩ 참고 — 박성문이 이미 낸 개수 평가
sed -n '1,14p' /data/project/2026summer/platform/work/park_seongmoon/bbox_outputs/apple/all/eval/summary.md
sed -n '1,14p' /data/project/2026summer/platform/work/park_seongmoon/bbox_outputs/grape/all/eval/summary.md
grep -n "mask_source" /data/project/2026summer/platform/work/park_seongmoon/bbox_outputs/*/all/run.log
cat /data/project/2026summer/kds0206/semantic-segmentation/output/instance_split_validation.json
sed -n '230,250p' "/data/project/2026summer/platform/work/park_seongmoon/instance prompt.md"   # §5.2 튜닝 표
```

**내가 만든 파일**(전부 `cycle_3/stage1/`): `a1_extract.py` · `a1_verify.py` · `a1_ctx.py` · `a1_pgnum.py`(1판) ·
`a1_pgnum2.py` · `a1_pghead.py` · `a2_tune.py` · `a2_report.py` · `a3_grape.py` · `a4_frag.py` · `a5_solidity.py` · `a6_metrics.py` ·
측정값 `a1_quotes.json` · `a1_verify.json` · `a1_pgnum.json` · `a2_tune.json` · `a3_grape.json` · `a3_grape_200.json` ·
`a4_frag_reviewed.json` · `a6_metrics.json` · 로그 6개 · `txt3/`(435개 텍스트).

## §8. 내가 못 한 것 (정직하게)

1. **옛 그림 파일 안의 문구**(M12) — 3차도 확인하지 못했다. PDF 폰트가 서브셋이라 `pdftotext` 로 한글이 복원되지 않는다. **사람이 열어 보거나 재생성해야 한다.**
2. **SNIP·Amarnath·Ullah 원문** — 서버에 PDF 가 없어 이번에도 대조 불가(M19). 경고만 문서에 박았다.
3. **출판판 쪽 번호** — `bargoti`·`hani`·`zabawa`·`isensee`·`maierhein` 의 학술지 쪽은 **PDF 가 프리프린트라 알 수 없다.** 어느 쪽이라고 지어내지 않았다.
4. **블루베리** — 정답이 없어 개수 지표를 낼 수 없다(대조표와 같은 결론).
5. **예측 마스크 실험**(M18) — GPU·학습 결과가 필요해 이번 범위 밖.
6. **표 28칸의 «어디에 구현» 칸을 전부 열어 보지는 않았다** — 카운팅·상자·분할·리사이즈에 관한 칸(1-a~1-f·2-a·2-f·4-c·5-a·6-a·6-c)은 코드로 확인했고, 나머지는 2차의 확인을 그대로 받았다.
