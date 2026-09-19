작성: 2026-09-17

# 0917 새 기능 5회 검수 — 사이클 5 · 1차 작업 (Opus 5)

주제: **사이클 4 판정이 확정한 N1 수정(P0) → 문서·숫자 정정(P1) → 나머지는 문서화(P2)**. 마지막 사이클.
읽은 것: `cycle_4/stage3_final.md`(지시 본체) · `cycles/prompts/stage1_c5.md` · 사이클 1~4 전 보고서 · 계획서 · `참고저장소_적용기록.md` ·
`app/{instances,boxes,server,dupes,maskio}.py` · `app/static/app.js` · `export/export_dataset.py` · `scripts/make_grape_instances.py` · `app/README.md` ·
`kds0206/문서/{260917_교수님확인_7건,260917_툴_사람확인_체크리스트}.md` · `260917_지울목록_시험잔재.md`
근거 표기: 📄 내가 직접 실행·확인한 실측(경로·수치 명시) · ❌ AI 판단 · ✅ 논문 근거(이번엔 없음)

⛔ 지킨 것: **포도 번호를 켜지 않았습니다**(📄 살아 있는 서버 `instance_info?fruit=grape&stem=1439` → `has=False`, `1564` → `has=False`).
파일 삭제 0건 · GPU 0 · 새 패키지·외부 CDN 0 · `cycles/260917_0917신기능_5회검수_계획.md` 와 `kds0206/문서/` **손대지 않음**(고칠 문장은 ⑨).
고치기 전 `_backup_260917_c5_*` 사본 8개를 남겼습니다.

---

## ① 합격 기준 (먼저 쓰고 실행했습니다)

| # | 기준 | 결과 |
|---|---|---|
| **K1** | 판정서 ③-4 대로 `instances.py` 에 `mask_path_of`·`load_inst` 가 있고 **읽는 자리 넷**(`/instances`·`/api/instance_info`·`/api/boxes_seed`·`export_dataset`)이 그것을 쓴다 | ✅ 📄 ③-1 |
| **K2** | 내보내기 manifest 에 `instances_check` 열과 요약 한 줄이 있다 | ✅ 📄 ③-1 |
| **K3** | `api_revert`(마스크 되돌리기)가 번호 파일이 있으면 **거절**한다 | ✅ 📄 400 + 문장 |
| **K4** | 판정서 **검증 1**: `export_coherence.py` 실패 0 · 유령 번호 0 · manifest `cut=1034 lost_ids=1` | ✅ 📄 ③-2 |
| **K5** | 판정서 **검증 2**: `n5_brush_vs_number.py` A·C 통과 + B 를 «거절» 로 바꿔 통과, **실패 0** | ✅ 📄 실패 0 |
| **K6** | 판정서 **검증 3**(회귀): `masks_fixed` 가 없는 사진은 자르기가 **아무것도 바꾸지 않는다** · 블루베리 `(144)_121` 은 실패가 아니라 `hole=151` 로 **기록** · `api_seed`·`edge_seed`·`boxes.py`·`modesim`·`boxsim`·`sim`·`test_clean` 통과 | ⚠️ 📄 **하나만 부분 미달** — 자르기 회귀·기록은 참, 그러나 `export_inst.py` 의 단정 ③ 은 블루베리 1장에서 **여전히 실패**(고치기 전과 같은 1건). 이유는 ③-3 |
| **K7** | 판정서 **검증 4**: 재시작한 살아 있는 서버에서 `(144)_121` 응답 **0.5초 미만** | ✅ 📄 0.193~0.205초(5회) |
| **K8** | 순환 논증 금지 — «같다» 의 증거는 **서로 다른 코드 경로**에서 나오고 무엇이 독립인지 밝힌다 | ✅ ⑧ |
| **K9** | `node --check app/static/app.js` · `python3 app/boxes.py` · `test_clean.py` 통과 유지 | ✅ 📄 셋 다 |
| **K10** | 공용 `data/` 에 남는 자취를 전부 적고 삭제는 사람에게 넘긴다 | ✅ ⑧-4 |

## ② 한 줄 결론

판정서 ③-4 를 **그대로** 구현했습니다 — 규칙 하나(**«이진본이 번호본을 자른다»**)를 `instances.py` 의 `load_inst()` 한 함수로 세우고 읽는 자리 넷이 그것을 쓰게 했으며, 내보내기에 `instances_check` 열과 요약 줄을, 마스크 되돌리기에 거절 한 줄을 넣었습니다. **N1 세 갈래가 전부 닫혔습니다** 📄: 내보내기 어긋남 1,034화소 → **0**, 유령 번호 1 → **0**, 브러시로 지운 알이 번호 레이어에 되살아나던 1,034화소 → **0화소**, 마스크 되돌리기 → **400 거절**. 판정서가 요구한 검증 4종 중 셋은 그대로 통과했고, 하나(회귀)는 **블루베리 `(144)_121` 한 장의 단정 ③ 이 고치기 전과 똑같이 실패**합니다 — 이것은 수정 실패가 아니라 «전경인데 번호 없음»(`hole=151`)을 **채우지 않기로 확정**한 결과이며, 그 시험의 단정이 그 확정보다 오래된 것입니다(③-3, 2차가 판정할 유일한 갈림길). P1(문서·숫자·N4 경고)까지 끝냈고, P2 세 건은 판정서·지시대로 **문서화만** 했습니다. ponytail 은 `--dry-run` 제거로 −3줄(예상 −5줄과 다른 이유 ⑥). 포도는 **켜지 않았습니다**.

## ③ 🔴 N1 수정 (P0) 과 검증

### ③-1 무엇을 고쳤나 — 판정서 ③-4 (a)(b)(c) 대조

| 판정서가 지시한 것 | 한 것 | 파일:줄 | 줄 수 |
|---|---|---|---|
| (a) `mask_path_of` — 이진 마스크 우선순위를 한 곳에 | 그대로 | `app/instances.py:89-95` | +7 |
| (a) `load_inst` — 번호본을 이진본으로 자르고 `(arr, kind, chk)` 반환 | 그대로. `chk = {"cut", "lost_ids", "hole"}` 로 «자른 화소·사라진 번호·전경인데 번호 없는 화소» 를 함께 돌려줘 export 가 **파일을 다시 읽지 않게** 했습니다(판정서가 «1차가 더 짧은 쪽을 고를 것» 이라 한 자리) | `app/instances.py:98-123` | +26 |
| (a) `load_mask_bool` 을 `maskio` 에서 import | 그대로 | `app/instances.py:21` | +1 |
| (a) 크기가 다르면 자르지 말고 `ValueError` | 그대로. 읽는 자리 넷이 각각 **400** 또는 manifest `err:` 로 흘립니다 | 〃 `:114-116` | — |
| (b) `/instances` | `load_inst` 로 교체. `layer=="fixed"` 분기도 같은 함수를 지나므로 **그 자리도 잘립니다**(판정서가 «거기도 자를 것» 이라 한 것) | `app/instances.py:136-156` | 순 −1 |
| (b) `/api/instance_info` + `hole_px`(선택) | 교체 + `cut_px`·`hole_px` **둘 다** 실었습니다(화면이 «전경인데 번호 없음 N화소» 를 보여 줄 수 있게) | 〃 `:158-176` | +5 |
| (b) `/api/boxes_seed` | `INST.load_inst` 로 교체 + `ValueError` → 400 | `app/boxes.py:155-160` | +3 |
| (b) `export_one` — `mask_path_of` 사용 · `read_u16`→`load_inst` · manifest `instances_check` 열 · 요약 한 줄 | 그대로. `check_cell()` 로 칸 서식을 한 곳에 | `export/export_dataset.py:66-76,110-128,162-167,175-177` | +25 |
| (c) `api_revert` 거절 3줄 | 그대로(+ 함수 설명 4줄) | `app/server.py:889-901` | +7 |

**판정서가 시키지 않았는데 한 것 두 가지**(둘 다 정확성·죽은 코드):
1. `export_dataset.py` 의 `fixed_dir`·`src_msk` **죽은 줄 2개 제거** — `mask_path_of` 로 옮겨간 뒤 아무도 안 씀(📄 `grep src_msk read_u16` → 0건). `read_u16` import 도 뺐습니다.
2. `app.js` 의 «낡은 txt» 표시 1줄(N4 가 **화면까지** 닿게 — ④ P1).

⚠️ **파일 권한 자백**: 제 파일 목록에 `app/server.py` 와 `app/static/app.js` 는 없었습니다. 그러나 (c)(= P0)는 `/api/revert` 가 `server.py` 에만 있어 다른 길이 없고, `app.js` 2줄은 판정서 ⑦ P1(`app.js:1520` 문구)과 N4 경고가 요구한 것입니다. 다른 작업자가 없고(지시문) 백업을 남겼으며 `node --check` 를 통과시켰습니다. 두 파일의 변경은 **총 +8줄, 전문을 ⑧-1 에 실었습니다.**

### ③-2 검증 1·2 — 판정서가 만든 두 시험 (📄 전부 재실행)

```
python cycles/260917_신기능/cycle_4/stage2/export_coherence.py     → 실패 0
   내보낸 instances/>0 ↔ masks/ 다른 화소 1,034 → **0** · 유령 번호 1 → **0**
   manifest: mask_source=masks_fixed · instances_source=원본번호 · instances_check=**cut=1034 lost_ids=1**
   요약 줄: «번호본을 이진본으로 자른 장 1(사라진 번호 1개) · 전경인데 번호 없는 장 0»
python cycles/260917_신기능/cycle_4/stage3/n5_brush_vs_number.py   → 실패 5 → **실패 0**
   A) 브러시로 알 1 지움 → /instances 가 알 1 을 **0화소**로 준다(전에는 1,034화소) · 번호 저장 뒤 되살아난 화소 **0/1,034**
   B) /api/revert → **400 «이 사진은 열매 번호를 고친 사진입니다. 번호 패널의 «번호 되돌리기» 를 쓰세요.»**
      번호본·이진본 파일 둘 다 남고 status 편집 기록도 그대로(되돌린 적이 없으므로)
   C) 낡은 instances_fixed + 브러시 → 유령 번호 **0개**(전에는 1개, 664화소) · 그 자리는 hole=828 로 기록
```
`n5` 의 단정 갱신은 판정서 지시대로입니다 — **B 의 세 단정을 «거절» 로 뒤집고**, 덧붙여 **A 의 단정도 뒤집었습니다**(A 는 원래 «구멍이 있다» 를 재던 단정이라 고친 뒤에는 실패가 정상이 됩니다. 판정서가 «A·C 통과, 실패 0» 을 요구했으므로 A 를 «이제 주지 않는다» 로 바꾸는 것이 그 요구를 만족시키는 유일한 길입니다 ❌).

### ③-3 검증 3 (회귀) — ⚠️ 한 줄만 판정서 문장과 다릅니다

```
python cycle_4/stage1/export_inst.py apple blueberry   → 실패 **1**  (고치기 전과 **같은 1건**)
     - Camera 1 Video (144)_121 ③ 번호본의 >0 이 내보낸 이진본과 화소 단위로 같다  (다른 화소 151)
     ① 화소 배열 완전 일치 · ② 번호 집합·번호별 화소 수 일치 · ④ manifest 출처 · 16비트 → 전부 통과
     apple 310개 · blueberry 366개 (고치기 전 json 과 같은 수) · 자른 장 0 · hole 장 1
python cycle_4/stage1/export_inst.py grape --n 6       → 실패 0 · 26개 · 자른 장 0 · hole 장 0
python cycle_3/stage1/api_seed.py (살아 있는 서버 40장) → 기대와 다른 것 **0장** · 6.7초
python cycle_3/stage2/edge_seed.py (저장·되돌리기 왕복) → 실패 **0** (15개 단정)
python app/boxes.py · test_clean.py · node sim.js(31/31) · modesim.js(31/31) · boxsim.js(50/50) · node --check → 전부 통과
python cycle_4/stage1/grape_seed_api.py (포도를 프로세스 안에서만 켬) → 실패 0, 40장 좌표까지 일치
```
판정서는 «블루베리 `(144)_121` 은 **이제 실패가 아니라** manifest `hole=151` 로 기록» 이라고 썼습니다. 📄 실제로는 **`hole=151` 기록은 됐지만 그 시험의 단정 ③ 은 여전히 실패**합니다. 이유 ❌: 단정 ③ 은 «내보낸 `instances/>0` == 내보낸 `masks/`» 인데, 판정서 ④ 가 «블루베리의 번호 없는 전경은 **채우지 않는다**» 를 확정했으므로 그 두 파일은 **설계상 151화소 달라야 합니다.** 즉 단정 ③ 은 «채우기» 를 전제한 낡은 불변식입니다. 제가 고른 길(❌): **시험을 고치지 않고 그대로 실패시켜 남겼습니다.** 사이클 4 의 증거이고, 제가 제 편의로 단정을 낮추면 «내가 만든 시험을 내가 통과» 가 되기 때문입니다. **2차 검수가 정할 것**: (가) 단정 ③ 을 «`only_inst==0` 이고 `only_mask` 는 manifest `hole` 과 같다» 로 고친다 (나) 블루베리만 예외 목록에 둔다 (다) 그대로 둔다. ❌ 저는 (가)를 권합니다 — 불변식을 «유령 번호 0 + 구멍은 기록과 일치» 로 정확히 옮기는 것이라서.

### ③-4 검증 4 — 살아 있는 서버 (📄 재시작 뒤 실호출)

```
bash app/run.sh restart   → PID 3034388 → **3141139** (원본 폴더 datasets_reviewed_260916 그대로 이어받음)
재시작 뒤 로그 107줄 · **500 응답 0건 · traceback 0줄**
blueberry Camera 1 Video (144)_121  boxes_seed 204개  0.193 0.205 0.200 0.198 0.200 초 (5회, 전부 0.5초 미만)
   instance_info → n=204 source=seed **hole_px=151** cut_px=0     ← 2차 bb_quant.json 의 only_mask=151 과 같은 수
blueberry (99)_1 102개 0.195초 · apple image1 95개 0.223초 · apple image451 번호 62개·상자 **61개**
apple image1 instance_info → n=95 **cut_px=0 hole_px=0** (masks_fixed 가 없으니 자르기가 0)
grape 1439 → source=gt **9개** · source=ai **17개**  |  grape 1439·1564 · peach → **has=False (포도 안 켬)**
/instances?apple image1 → IHDR 를 직접 읽어 (1920, 1080, **16비트, 회색**) · X-Instance-Source: gt
```
판정서 예상(«마스크 한 장을 더 읽으므로 +0.02초») 📄 확인: 0.14~0.15초(사이클 4 실측) → 0.193~0.205초, **+0.05초 안쪽**. 사람이 누르는 단추 기준 영향 없음.

## ④ P1 · P2 처리

| 순위 | 항목 | 한 것 |
|---|---|---|
| **P1** | 문서 정정 (README) | §6 에 `--instances`·`instances_check` 3줄 · §10 포도 초벌 개수 정정(«AI 제안을 켰을 때 `1` 5송이→4개, `1439` 1송이→17개, **원본 GT 면 8개·9개**») · §10 «그린 순서대로 앞 3,000개»(사이클1 D7) · §10 낡은 txt 3줄 · §11 **«번호본과 이진본 — 이진본이 번호본을 자른다»** 절 신설(자르기·채우지 않음·`instances_check` 읽는 법·되돌리기 거절·`layer=gt` 404). 📄 306 → 328줄 |
| **P1** | **N4** 낡은 txt 경고 | `api_boxes_export` 응답에 `stale_txt`·`stale_txt_names`(최대 20개). **삭제 코드 없음.** 화면에도 «상자가 없어진 낡은 txt N개(사람이 지울 것)» 로 뜨게 `app.js` 2줄. 📄 시험 `cycle_5/stage1/n4_stale.py` 3/3 통과(상자 지운 뒤 `stale_txt=1`·`t2.txt`, 파일은 **그대로 남음**) |
| **P1** | `app.js:1520` 문구 | `seed: "검출팀 초벌(watershed)"` → `"검출팀 초벌(블루베리 watershed · 포도 CERTH 송이)"`. 포도 켜기 **전제 3번 충족** |
| **P1** | 사이클 1~4 보고서 옛 숫자 | `cycle_3/stage1_work.md`·`cycle_4/stage1_work.md` 끝에 «사이클 5 정정» 표를 덧붙였습니다(본문은 기록으로 보존). 4+4건 — ⑤ 표 |
| **P2** | **N3** `boxes.py:191 rec["stem"]` | **코드 안 고침, 문서화만**(지시문 «P2 는 문서화만»). 📄 도달 불가: 그 json 은 `api_boxes_save` 만 쓰고 저장 전 `check(fruit, stem)` 을 지납니다(`boxes.py:117`). 고치려면 `rec.get("stem", fn[:-5])` 0줄 변경 — **영구 보류** |
| **P2** | API 방어 (`layer=gt` 404) | **404 유지 확정, 코드 없음.** README §11 마지막 줄에 «번호가 없는 과일에 `layer=gt` 는 404» 기록 |
| **P2** | 화면 배율 반올림(`dpr`) | **영구 보류 확정.** ❌ 근거: 고치는 법(사이클1 ④ D2)은 `cv._sx`·`cv._sy` 저장 + `draw`·`fitView`·`toImg` 세 곳 교체로 **2줄을 넘고**(판정서 조건 «2줄 이하이고 `boxsim.js` 통과» 불충족), 최대 오차가 **0.3 CSS 픽셀**이며 브라우저 눈 확인이 아직 0입니다. 📄 `app.js:393-395,402-406,414-419,1777-1779` 네 자리가 `dpr` 를 씀 — 세 곳만 바꾸면 1777 자리와 규칙이 갈립니다 |
| **유지 확정 — 손대지 않음** | 손으로 쓴 PNG 해독기(−70줄) · `api_revert_instances` 두 번 쓰기 · `maskio` 이동 | 📄 세 자리 모두 백업과 **바이트 동일**(⑧-1 diff 에 없음) |
| **ponytail** | `make_grape_instances.py --dry-run` 제거 | 📄 162 → **159줄 (−3)**. 예상 −5줄과 다른 이유는 ⑥ |

## ⑤ 문서·숫자 대조표 (📄 전부 이번에 다시 셌습니다)

| 숫자 | 문서에 적힌 곳 | 📄 다시 센 값 | 판정 |
|---|---|---|---|
| 사과 `image1` 번호 95개 → 상자 95개 | README §10, 체크리스트 G | 번호 95 · 상자 95(살아 있는 서버) | 맞음 |
| 블루베리 `(1)_1` 초벌 55개 → 상자 55개 | README §10, 체크리스트 G | 55/55 (`edge_seed` 복귀 확인에서 n=55) | 맞음 |
| 사과 `image451` 번호 62개 → 상자 **61개** | README §10 | 62/61 (살아 있는 서버) | 맞음 |
| AI 제안 «복숭아 125 · 포도 2,502 · 사과 1,001 · 블루베리 1,195 = 4,823장» | README §10 | 125·2502·1001·1195, 합 **4823** (`ls data/*/proposals`) | 맞음 |
| 포도 CERTH 2,502장 9,832송이 | 여러 곳 | `grape_gt.totals()` = **(2502, 9832)** (검출 팀 코드로 직접) · `instances_seed` **2,502장** | 맞음 |
| 블루베리 총 번호 45,124 · 장당 최대 204 | 계획서·보고서 | 45,124 · 204 (`bb_quant.json` 1,195행 재집계) | 맞음 |
| 블루베리 어긋난 장 239 · 화소 61,620 · 최대 5,887 · 반대 방향 0 | 판정서 ④ | 239 · 61,620 · 5,887 · **0** | 맞음 |
| 추정 누락 알 25개 · 21장 · 최악 7.38% | 판정서 ④ | 25 · 21 · 7.3835% | 맞음 |
| `(144)_121` 어긋남 151화소 | 2차 json | **살아 있는 서버 `hole_px=151`** (다른 경로로 재확인) | 맞음 |
| 사과 `image1` 알 1 = 1,034화소 | 2차·3차 | 1,034 (원본 마스크에서 직접) | 맞음 |
| «초벌이 3~4초» | `cycle_3/stage1_work.md` 6곳 | 최악은 **7.55초**, 지금은 **0.193~0.205초** | ❌ 틀림 → 정정 표 덧붙임 |
| «ponytail 정확히 −7줄» | `cycle_3/stage1_work.md` 3곳 | 합계 −7 은 맞고 구성은 «−10 + 16» | ⚠️ 오해 소지 → 정정 |
| «검출 팀 YOLO 라벨을 포도 초벌로» | `cycle_3/stage1_work.md` 2곳 | CERTH **원본 인스턴스**를 씁니다 | ❌ 틀림 → 정정 |
| «어긋남은 초벌 데이터의 성질, 우리 버그 아님» | `cycle_4/stage1_work.md` 3곳 | **절반만.** N1 은 우리 구조 문제였고 이번에 고쳤습니다 | ❌ 틀림 → 정정 |
| «7.71초» ↔ «7.55초» | 4차 ↔ 3차 | 같은 사진을 두 번 재서 생긴 차이, 둘 다 «7초대» | 정정 표에 기록 |
| README §10·§11 이 지금 코드와 같은가 | — | §11 에 **자르기 규칙이 없었습니다**(코드가 바뀜) → 절 신설. §10 포도 개수 문장이 AI 제안 여부를 안 밝혔음 → 정정 | 고침 |
| `참고저장소_적용기록.md` 가 실제와 같은가 | — | 📄 맞습니다. ponytail 스킬 6개 `~/.claude/skills/` 존재 · `boxes.py demo()` 자체 점검 살아 있음(📄 실행) · `ponytail:` 주석 6개(⑥) · ruflo 설치 안 함(`.claude-flow` 없음) · «한 작업공간에 한 사람» 도 이번에 지킴 | 고칠 것 없음 |

## ⑥ 지름길 대장 (ponytail 주석 전수 — 📄 `grep -rn ponytail` 살아 있는 코드만)

| 파일:줄 | 남긴 지름길 | 한계 | 나중에 올릴 길 |
|---|---|---|---|
| `instances.py:60` | `DATA_DIR`·원본 폴더를 `dupes` 모듈 전역으로 믿는다 | 서버가 다른 `data` 폴더를 쓰게 되면 `mask_path_of`·`inst_fixed_path` 가 서버와 **다른 폴더**를 볼 수 있다(지금은 `ctx["DATA_DIR"]` 와 같은 값) | 두 함수가 `ctx` 를 받게 (약 +6줄). 시험 스크립트들이 `DUP.DATA_DIR` 를 덮어쓰는 방식도 같이 바뀜 |
| `instances.py:144` | `/instances` 의 `layer=gt` 는 «번호가 없으면 404» | 옛 판은 0/255 이진 마스크를 번호인 척 200 으로 줬다. 화면이 그 응답에 기대고 있지 않은지는 **브라우저 눈 확인 0** | 그대로 유지 확정(사이클4 ⑦ P2). README 에 문장으로 남겼다 |
| `instances.py:252` | `api_revert_instances` 가 status 항목을 **두 번** 쓴다 | 두 쓰기 사이(같은 `inst` 자물쇠 안, status 자물쇠는 놓음)에 다른 요청이 읽으면 편집 기록이 잠깐 보인다 | **유지 확정**(사이클4 ⑦ P3). `update_status(..., extra=...)` 처럼 한 번에 쓰게 바꾸려면 서버 공용 함수 서명 변경 |
| `boxes.py:153` | `/api/boxes_seed` 의 `source` 인자는 번호가 있으면 **무시**된다 | 화면이 `source=inst` 를 보내도 서버가 번호 유무로 다시 판단 — 둘이 갈리면 조용히 서버 쪽이 이긴다 | 응답 `source` 가 실제로 쓴 것을 말해 주므로 지금은 문제 없음. 고친다면 400 으로 거절(+3줄) |
| `boxes.py:231` | `demo()` 자체 점검이 **실제** `clean()`·`boxes_of()` 를 부른다 | 시험 대상이 아니라 «지키는 것» — 지우지 않는다 | — |
| `export_dataset.py:161` | `--dry-run` 은 파일을 읽지 않으므로 열매 «개수» 를 세지 않는다(장수만) | dry-run 숫자와 실제 내보낸 숫자가 다르게 보일 수 있다(장수는 같다). 이번 수정으로 dry-run 은 `source_of` 만 부르고 **자르기를 하지 않으므로** `instances_check` 도 비어 있다 | dry-run 도 `load_inst` 를 부르면 정확해지지만 전수에서 마스크를 두 장씩 더 읽는다(1,195장×2). **일부러 안 함** |

**이번 사이클 ponytail 수확**: `make_grape_instances.py --dry-run`·`convert(write=)` 제거 = 📄 **−3줄**(인자 1 · 분기 1 · 문자열 1). 판정서 예상은 −5줄이었는데, `--dry-run` 이 `if write:` 두 줄과 인자 3자리에 걸쳐 있어 실제로 사라진 «줄» 은 3개였습니다(❌ 판정서 예상이 분기 들여쓰기 복원을 세지 않았음). 덧붙여 `export_dataset.py` 의 죽은 줄 2개(`fixed_dir`·`src_msk`)와 안 쓰는 import 1개를 뺐습니다. `net: -6 lines` (정확성 수정 +42줄은 ponytail 범위 밖).

## ⑦ 다섯 사이클에서 «아직 아무도 확인하지 못한 것» (마지막 사이클이므로 한곳에)

### (가) 브라우저 눈으로 봐야 하는 것 — **다섯 사이클 전부 0**
사이클 1~5 의 1차·2차·3차 **아홉 단계 모두 브라우저가 없었습니다.** 지금까지 화면은 `app.js` 의 함수를 떼어 내 가짜 DOM 에서 돌린 시뮬레이션(`sim`·`modesim`·`boxsim` = 112개 단정)으로만 확인했습니다.
- 상자가 **알 위에** 제대로 놓이는지(초벌 95개·204개), 확대·이동 중 손잡이 잡기, `dpr` 0.3화소 오차
- 번호 레이어의 **색·번호 글자**가 보이는지, 16비트 PNG 해독기가 **실제 브라우저**에서 사과 번호 1~95 를 살려 내는지(사이클 2 가 «전부 0 이 된다» 를 발견해 손으로 쓴 해독기를 넣은 자리 — 그 해독기가 **진짜 브라우저에서** 도는 것을 본 사람이 없습니다 🔴 가장 위험)
- 이번에 넣은 것: 번호 모드에서 **브러시로 지운 알이 안 보이는지**, «수정본 되돌리기» 거절 문구, «낡은 txt N개» 경고
→ ⑨-5 의 체크리스트 문장으로 넘깁니다.

### (나) 사람 결정 대기 (코드로는 더 못 감)
| # | 결정할 사람 | 무엇 | 막혀 있는 것 |
|---|---|---|---|
| 1 | 교수님 (확인 5번) | 상자 클래스 번호(우리 송이=1 ↔ 검출 팀 송이=0) | 내보낸 txt 를 학습에 바로 쓰기 |
| 2 | 교수님 (확인 8번) | «전경 기준을 우리 마스크로» — 포도 번호 켜기 | 포도 카운팅 전부 |
| 3 | 교수님 (확인 6번) | 사과·블루베리 검수판 데이터셋 | 근접 중복 47그룹 131장 폴드 재구성 |
| 4 | 박성문 | 블루베리 초벌 재생성 여부(지금이 가장 싼 시점 — 📄 `instances_fixed` 0장) | 21장 25알의 번호 |
| 5 | 박성문 | 카운팅 벤치마크 100장에 그 21장을 넣을지 | 벤치마크 구성 |
| 6 | 박성문 | 복숭아 COCO 인스턴스 («포도와 같은 방식으로 가능, **미확인**») | 복숭아 카운팅 |
| 7 | 곽동신 | 사과 `image451` x397 의 2화소 조각(사이클 3 ⑨-C) | 없음(기록만) |

### (다) 코드에 있으나 한 번도 지나가 보지 않은 길
| 경로 | 왜 안 지났나 | 위험 |
|---|---|---|
| `load_inst` 의 `ValueError`(번호↔이진 **크기 불일치**) | 실제 데이터에 그런 짝이 없음 | 📄 이번에 **일부러 만들어** 지나가 봤습니다(`n1_cut.py` S5: 400·`err:` ·파일 안 만듦). 실데이터 발생은 여전히 0 |
| 여러 사람이 **동시에** 같은 사진을 번호·브러시로 저장 | 사람 하나로만 시험 | 자물쇠는 `inst:` 와 `mask:` 로 **다릅니다** — 번호 저장과 브러시 저장이 동시에 들어오면 `masks_fixed` 를 누가 마지막에 쓰는지 정해져 있지 않습니다 ❌ 사이클 2 가 «잠금 불필요» 로 판정했으나 그 판정은 «한 사람» 전제 |
| 3,000개 상한을 **사람이 손으로** 넘기기 | 초벌도 3,000에서 끊음 | 없음(문서화 완료) |
| `--fruit all --instances` 전수 내보내기(4,823장) | 시간·용량 | 📄 과일별로는 전부 돌려 봤습니다(사과·블루베리 4장씩, 포도 6장). 전수 1회는 안 돌림 |
| 사과 1,001장·블루베리 1,195장 **전수** 자르기 회귀 | 표본 4장씩만 | ❌ `masks_fixed` 가 0장이므로 자르기는 원리적으로 아무것도 바꾸지 않습니다(S3 에서 실증). 전수 확인은 2차가 원하면 `export_inst.py --n` 을 늘리면 됩니다 |
| 포도를 **켠 상태로** 살아 있는 서버 운영 | ⛔ 금지 | test_client 로는 전부 통과(40장·저장·내보내기·되돌리기). 살아 있는 서버 재시작 뒤 확인은 켠 다음 10분 |

## ⑧ 실행 증거 (독립성 명시)

### ⑧-1 새로 만든 시험 2개 — 무엇이 독립인가

**`cycles/260917_신기능/cycle_5/stage1/n1_cut.py` (실패 0, 시나리오 5개 20단정)**
🔴 **독립성 한 줄**: 내보낸 번호본은 **PIL 없이 손으로 쓴 zlib+struct PNG 해독기**로 읽고(독립1 — 우리 저장은 PIL `I;16` 인코더), 내보낸 이진본은 **PIL(maskio)** 로 읽고(독립2), 기대값은 **팀 표준 원본 마스크의 화소 수**(독립3 — 사과 마스크값이 곧 번호라 «알 1 = 1,034화소» 는 원본이 말해 주는 수)에서 나옵니다. 해시는 근거로 쓰지 않았습니다.
```
S1 브러시로 알 1 지움·번호 편집 없음 → manifest instances_check = «cut=1034 lost_ids=1» (독립3 의 수와 일치)
   손수 해독기(필터 종류 0·1·2·4 를 실제로 지남) ↔ PIL 배열 동일 · 이진본 밖 번호 **0화소** · 번호 95→94, 알 1 만 빠짐
S2 툴 API 세 곳: instance_info n=94 cut_px=1034 hole_px=0 · /instances 알1 **0화소** · boxes_seed **94개**
S3 masks_fixed 를 지우면 → instances_check **빈칸** · 손수 해독한 번호본이 원본과 **다른 화소 0** (자르기 무영향 회귀)
S4 브러시로 500화소 **넓힘** → «hole=500» · 그 500화소는 **번호 없이** 나감(엉뚱한 번호로 안 채움) · instance_info hole_px=500
S5 크기가 다른 masks_fixed → instance_info·/instances **400** · manifest «err:…» · 잘못된 번호본 파일 **안 만듦**
```
**`cycles/260917_신기능/cycle_5/stage1/n4_stale.py` (실패 0)** — 상자 2장 내보내기 → `stale_txt=0`; json 하나를 지우고 다시 → `stale_txt=1`·`t2.txt`, **그 txt 는 남아 있음**(삭제 코드 없음).
**`cycles/260917_신기능/cycle_5/stage1/live_c5.py` (실패 0, 15단정)** — ③-4. 독립성: 기대값(`hole_px=151`)은 2차가 **다른 스크립트**로 전수 계산한 `bb_quant.json` 의 `only_mask` 이고, `/instances` 의 16비트는 **IHDR 바이트를 직접 뜯어** 확인했습니다(PIL 판단에 기대지 않음).

### ⑧-2 고친 파일과 줄 수 (📄 `_backup_260917_c5_*` 대조)
```
app/instances.py                 239 → 282  (+43)   ← N1 본체
export/export_dataset.py         157 → 182  (+25)   ← 자르기·instances_check·죽은 줄 −2
app/boxes.py                     252 → 260  (+8)    ← load_inst 교체 +3, N4 +5
app/server.py                   1110 → 1117 (+7)    ← api_revert 거절 3 + 설명 4
app/static/app.js               2007 → 2008 (+1)    ← 문구 1줄, N4 표시 2↔1줄
app/README.md                    306 → 328  (+22)
scripts/make_grape_instances.py  162 → 159  (−3)    ← ponytail
cycle_4/stage3/n5_brush_vs_number.py 142 → 149 (+7) ← 단정 갱신(판정서 지시)
```
전체 diff 는 위 백업들과 `diff -u` 로 재현됩니다. **PNG 해독기·`api_revert_instances`·`maskio` 는 diff 에 없습니다**(유지 확정).

### ⑧-3 통과 상태 유지
📄 `python3 app/boxes.py` → «자체 점검 통과» · `test_clean.py` → «고친 boxes.py 확인 통과» · `node --check app/static/app.js` → 통과 · `sim.js` 31/31 · `modesim.js` 31/31 · `boxsim.js` 50/50.

### ⑧-4 남긴 자취 (⛔ 삭제는 사람 — CLAUDE.md 3항)
- 공용 `data/`: **파일은 하나도 늘지 않았습니다** 📄 `masks_fixed` 0·0·0·39(복숭아는 예전 것) · `instances_fixed` **전부 0** · `instances_seed` 2,502 그대로 · `boxes` 그대로.
  단 `data/apple/status.json`·`data/blueberry/status.json` 의 **두 항목이 갱신됐습니다**(판정서가 요구한 `edge_seed.py` 회귀가 저장·되돌리기를 하기 때문):
  `apple/20150919_174151_image361` 과 `blueberry/Camera 1 Video (1)_1` → `status=unreviewed · by="AI 사이클3 2차 경계시험" · note="번호 편집 되돌림" · at=17:53`.
  **항목 수는 2·1·183·125 로 그대로**이고 내용도 사이클 3 2차가 남긴 것과 같은 꼴(시각만 새것)입니다. 사람이 이 두 항목을 지우고 싶으면 목록에 올려 주세요.
- 서버: **재시작했습니다**(PID 3034388 → 3141139). 로그 107줄 늘었고 500·traceback 0.
  📄 **살아 있는 서버가 최종 코드를 돌고 있습니다**: 기동 17:53:18 ↔ `server.py` 17:45:47 · `instances.py` 17:44:56 · `boxes.py` 17:45:16 · `app.js` 17:46:41 (전부 기동보다 **앞**).
  기동 뒤에 고친 것은 `export/export_dataset.py`(17:56, 죽은 줄 2개) 하나뿐이고 그것은 서버가 import 하지 않는 CLI 스크립트입니다. 📄 18:01 `/api/health` → `ok:true`.
- 세션 임시 폴더: `/tmp/c4_expinst_*` 가 **3개 늘었습니다**(`export_inst.py` 는 스스로 지우지 않는 스크립트 — 📄 지금 5개: `3mw546wd`·`ntnk71px`(사이클 4) + `4ur84cso`·`ckpyfwdn`·`_0sx0089`(제 것)). 제가 새로 쓴 3개와 `n5`·`export_coherence` 는 스스로 지웁니다(📄 `/tmp/c5_*` 0개).
- 덮어쓴 json: `cycle_4/stage2/export_coherence.json` · `cycle_4/stage3/n5_brush_vs_number.json` · `cycle_4/stage1/export_inst_*.json` · `cycle_4/stage1/grape_seed_api.json` · `cycle_3/stage1/seed_after.json` (전부 재실행 결과, 결론은 «고쳐졌음» 으로 **바뀜** — 그것이 증거입니다).
- 새 파일 7개: `cycle_5/stage1/{n1_cut.py,n1_cut.json,n4_stale.py,live_c5.py,live_c5.json,data_fingerprint_before.json,data_fingerprint_after.json}` + 이 보고서 + 백업 8개.

## ⑨ 제 담당이 아닌 문서에서 고칠 문장 (⛔ 저는 손대지 않았습니다)

| 파일 | 지금 | 바꿀 것 |
|---|---|---|
| `계획서` «사이클 4 진행 상태» | «사이클 5 진행 중» | «사이클 5 · 1차 완료 — **N1 세 갈래를 고쳤습니다**(이진본이 번호본을 자른다). 내보내기 어긋남 1,034화소 → 0 · 유령 번호 1 → 0 · 브러시 편집 되살아남 → 0 · 마스크 되돌리기 400 거절. 검증 4종 중 3종 통과, 1종은 낡은 단정 1건이 남아 2차가 판정» |
| 〃 새 단락(사이클 5) | — | «사이클 5 · 1차: 문서 정정(README 306→328줄) · N4 낡은 txt 경고 · `app.js` 문구 1줄 · ponytail −6줄 · N3·`dpr`·API 방어는 **문서화만**(영구 보류 확정) · PNG 해독기·두 번 쓰기·`maskio` 는 **유지 확정**» |
| 〃 `:156` «ponytail: 즉시 7줄» | 당시 예측치 | «(실제: 사이클 3 −10줄+16줄=−7줄 · 사이클 5 −6줄)» |
| 〃 `:82` (사람이 정해야 하는 것 3) | 포도 켜기 설명 | 뒤에 «전제 세 개 중 **2·3 은 사이클 5 에서 충족**(N1 수정 + 화면 문구). 남은 것은 교수님 8번 답과 사이클 5 2차 재현뿐» |
| `kds0206/문서/260917_툴_사람확인_체크리스트.md` H 묶음 | «(사이클 5 고치기 전) 사과·블루베리에서 브러시 저장 금지» | 🔴 **이 금지를 풀어도 됩니다** — 문장을 «(사이클 5 에서 고쳤습니다) 브러시로 지운 알은 번호 레이어에서도 바로 사라지고, 번호 저장이 브러시 편집을 되살리지 않습니다» 로 바꾸고 아래 눈 확인 3줄을 **지금 바로** 살릴 것 |
| 〃 H 묶음 다음 줄 | «(사이클 5 고친 뒤) 사과 image1 … 거절된다» | 그대로 살리고 문구를 정확히: 거절 메시지는 «**이 사진은 열매 번호를 고친 사진입니다. 번호 패널의 «번호 되돌리기» 를 쓰세요.**» |
| 〃 G 묶음에 새 줄 | — | «블루베리 `Camera 1 Video (144)_121` 을 열면 «열매 번호» 패널이 **번호 204개**로 뜬다(지금은 화면에 안 보이지만 서버는 «전경인데 번호 없음 151화소» 를 함께 보냅니다 — 카운팅 정답에서 21장 25알이 빠지는 그 자리)» |
| 〃 G 묶음에 새 줄 | — | «상자를 **전부 지우고** «YOLO 로 내보내기» → «상자가 없어진 낡은 txt N개(사람이 지울 것)» 경고가 뜬다. 파일은 저절로 지워지지 않는다» |
| `260917_지울목록_시험잔재.md` | 덧붙임 5 까지 | «덧붙임 6»: `rm -rf /tmp/c4_expinst_*`(5개 — 사이클 4 2개 + 사이클 5 3개, `export_inst.py` 가 스스로 지우지 않음) · `/tmp/c4b_yolo_*` 2개 · `/tmp/c3_roundtrip_*` 1개. **`data/{apple,blueberry}/status.json` 의 두 항목**(`20150919_174151_image361`·`Camera 1 Video (1)_1`, note «번호 편집 되돌림») 은 `edge_seed.py` 회귀가 남긴 것이니 지울지 판단해 주세요 — 파일이 아니라 항목이라 제가 손대지 않았습니다 |
| `260917_교수님확인_7건.md` 8번 | 수정 없음 | 그대로. 다만 «답이 «예» 여도 켜는 시점은 **사이클 5 2차 재현 뒤**» 를 곽동신이 알고 있을 것 |
| `문서/260917_상자기능_5회검수_최종판정.md` (아직 없음) | — | 사이클 5 3차가 쓸 초안에 실을 것: ⑥ 순환 논증 규칙 한 문장 · 사람 결정 7건(⑦-나) · 포도 켜기 절차(전제 2·3 충족) · «이진본이 번호본을 자른다» 규칙 · 브라우저 눈 확인 0 이라는 사실 |
| 곽동신 → 박성문 | 사이클 4 판정서 ④ 의 전달 문장 | 그 문장 그대로 + 한 줄 추가: «툴 쪽 고침이 끝났습니다 — 내보낼 때 장마다 `instances_check` 칸에 `hole=<화소>` 가 적히고(`(144)_121` = 151), «없는 번호» 가 나가는 반대 방향 문제는 0 이 됐습니다» |

## ⑩ 2차 검수가 재현할 절차

```bash
cd /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
# 0) 내가 고친 것 보기 (백업 대조)
for f in app/instances.py app/boxes.py app/server.py export/export_dataset.py \
         app/static/app.js scripts/make_grape_instances.py app/README.md; do
  diff -u "$(dirname $f)/_backup_260917_c5_$(basename $f)" "$f"; done

# 1) 판정서 검증 1·2 (공용 data/ 안 건드림, 스스로 지움)
python3 cycles/260917_신기능/cycle_4/stage2/export_coherence.py      # 실패 0 · cut=1034 lost_ids=1
python3 cycles/260917_신기능/cycle_4/stage3/n5_brush_vs_number.py    # 실패 0 (A·B·C)
# 2) 내가 새로 쓴 독립 시험 (손수 쓴 PNG 해독기로 교차 확인)
python3 cycles/260917_신기능/cycle_5/stage1/n1_cut.py                # 실패 0 (S1~S5)
python3 cycles/260917_신기능/cycle_5/stage1/n4_stale.py              # 실패 0
# 3) 회귀 — ⚠️ 블루베리 1건은 **실패가 정상**입니다(③-3 의 갈림길을 판정해 주세요)
python3 cycles/260917_신기능/cycle_4/stage1/export_inst.py apple blueberry   # 실패 1 (144)_121 ③
python3 cycles/260917_신기능/cycle_4/stage1/export_inst.py grape --n 6       # 실패 0
python3 cycles/260917_신기능/cycle_4/stage1/grape_seed_api.py                # 실패 0 (포도는 프로세스 안에서만 켜짐)
python3 app/boxes.py && python3 cycles/260917_신기능/cycle_1/stage1/test_clean.py
node --check app/static/app.js
node cycles/260917_신기능/cycle_1/stage1/sim.js
node cycles/260917_신기능/cycle_2/stage2/modesim.js
node cycles/260917_신기능/cycle_2/stage1_client/boxsim.js
# 4) 살아 있는 서버 (재시작은 이미 했습니다 — PID 3141139)
python3 cycles/260917_신기능/cycle_5/stage1/live_c5.py               # 실패 0 (hole_px=151 · 0.5초 미만 · 포도 has=False)
python3 cycles/260917_신기능/cycle_3/stage1/api_seed.py              # 40장 다른 것 0
python3 cycles/260917_신기능/cycle_3/stage2/edge_seed.py             # 실패 0 (⚠️ 공용 status.json 두 항목을 또 갱신합니다)
# 5) 자취 확인
python3 -c "import json;print(json.load(open('cycles/260917_신기능/cycle_5/stage1/data_fingerprint_after.json')))"
ls -d /tmp/c4_expinst_* /tmp/c5_* 2>/dev/null
```
**2차가 꼭 판정할 것 3가지**: (1) ③-3 의 `export_inst.py` 단정 ③ 을 어떻게 할지((가)/(나)/(다)). (2) ③-1 의 «제 파일 목록에 없던 `server.py`·`app.js` 를 P0·P1 때문에 고친 것» 이 타당한지. (3) ⑦-다 의 «번호 저장 ↔ 브러시 저장 동시 요청» 이 새 시험거리인지(자물쇠 이름이 다름 — 제가 고치지 않은 자리).
**2차가 고치지 말 것**: 포도 `SEED_DIRS`(⛔ 교수님 8번 뒤) · PNG 해독기 · `api_revert_instances` 두 번 쓰기 · `maskio` 위치 · `dpr`(영구 보류 확정) · N3.
