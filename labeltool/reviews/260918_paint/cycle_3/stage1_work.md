작성: 2026-09-18

# 라벨링 툴 «데이터 정리 탭(백엔드 + 프런트 · 서버 저장)» — 사이클 3/5 · **1차 작업** (Opus 5)

근거 문서: 방향 `문서/260918_툴_방향_녹취기준.md` §4 사이클3 · §5 ·
설계 `cycle_2/stage2_review.md` **§12-2** · 정책 `cycle_2/stage3_final.md` **§4** · `cycle_2/stage2b_fix.md` §5

작업 시각(실측 `date`): 2026-09-18 **16:02 ~ 16:58** (모래상자 5211/5212 · 회귀 5241~5269 · 전부 127.0.0.1)

---

## 0. 한 장 요약

- 만든 것: **서버 4개 주소**(`export_start`·`export_status`·`export_list`·`export_plan`) +
  **화면 탭 1개**(«데이터 정리») + **사용법 1절**(그림 1장) + README §15.
- 나가는 곳: **툴 폴더 안** `exports/<YYMMDD_HHMMSS>_<과일>/` 하나뿐. 팀 데이터셋 폴더·공용 `data/` 무변경.
- 실제로 내보내는 코드는 **명령줄과 같은 함수**다 — `export_one()`(콜백 한 개만 더함)과
  새로 뺀 `export_boxes_to()`. 규칙이 두 군데로 갈라지지 않게.
- 🔴 **실서버(5111)는 켜지도 붙지도 않았다.** 재시작·로그인·쓰기 0건. 다만 **정적 파일 4개는
  재시작 없이 이미 5111 에 나가 있다**(규칙 §8-10 그대로) → 그래서 **가드**를 넣었다:
  서버가 `/api/export_list` 를 모르면(404) 탭 안에 «서버가 아직 이 기능을 모릅니다 — 관리자가
  켜야 합니다» 만 보이고 **누를 것이 하나도 없다**(옛 서버에서 실측: 쓰기 요청 0건).
- 시험: **t1_api 79/0 · t2_ui 24/0 · t3_helpfig 2/0**(새로 짠 105항목, 실패 0).
  회귀 22묶음은 **`s1_api` 하나만 72/4 → 68/8** 로 바뀌었고 그 8개의 내역은 §8 에 한 줄씩 적었다
  (전에 실패하던 «manifest 에 확정 칸» 이 통과로 바뀌고, 5개는 **3차 결정 2 때문에 낡은 기대값**).
  나머지는 **숫자까지 전과 같다**.

---

## 1. 무엇을 어디에 고쳤나 (백업은 전부 `_backup_260918_c3_<파일명>`)

| 파일 | 늘어난 줄 | 지운 줄 | 지금 줄 수 | 무엇 |
|---|---|---|---|---|
| `app/server.py` | **+181** | 0 | 1,725 | 새 주소 4개 · 작업 딕셔너리 · 과일별 «무슨 자료가 있나» |
| `app/boxes.py` | +53 | −33 | 285 | `export_boxes_to()` 를 모듈 함수로 빼냄(동작 불변) |
| `export/export_dataset.py` | +44 | −7 | 237 | `on_step` · manifest 4칸 · flag 기본 제외 · CLI 덮어쓰기 멈춤 · 결과 반환 |
| `app/static/index.html` | +23 | 0 | 343 | 탭 1개 + `#view-exp` 화면(뼈대만) |
| `app/static/app.js` | **+5** | 0 | 2,348 | `showView()` 에 탭 한 칸(옛 화면에서도 안 깨지게 `?` 처리) |
| `app/static/ui.js` | +175 | 0 | 989 | 탭 안 화면·가드·1초 폴링·표 |
| `app/static/style.css` | +13 | 0 | 343 | 탭 모양 |
| `app/static/help.html` | +45 | −1 | 454 | «데이터 정리» 절 + 목차 한 칸 |
| `app/README.md` | +26 | 0 | 687 | §6 에 한 줄 + §15(API 요약) |
| `app/static/help/ui_export_260918c3.png` | (새 파일 107KB) | | | 사용법 그림 1장 |

합계 **+565 / −41 줄**. 새 파이썬·JS 파일 0개.
고친 자리는 전부 `cycle_3/stage1/fix_260918_c3.py`(20자리) · `fix_260918_c3_docs.py`(4자리) 에 적혀 있고,
**앵커를 하나라도 못 찾으면 아무것도 쓰지 않고 멈춘다**(반쯤 고쳐 놓는 일이 없게).

---

## 2. 서버 — 새 주소 4개 (`app/server.py`)

```
POST /api/export_start   {fruit, kinds:["mask","instances","boxes"], confirmed_only:true, by}
      → 검사(FRUITS · kinds · 번호는 마스크와 함께) → out = ROOT/exports/<YYMMDD_HHMMSS>_<fruit>/
      → with lock_for("export:"+fruit):  같은 과일이 running 이면 409
                                         os.makedirs(out, exist_ok=False)   ← 덮어쓰기 금지는 이 한 줄
      → threading.Thread(daemon=True) 로 export_one() · export_boxes_to() 를 부르고 바로 응답
      ← {ok, job:"260918_162919_peach", out:"exports/260918_162919_peach"}
GET  /api/export_status?job=…  ← {state running|done|error, done, total, msg, out, n_images, n_dropped, …}
                                  _jobs 에 없으면 <out>/job.json 으로 답한다(서버를 껐다 켜도 살아 있다)
GET  /api/export_list          ← 끝난 폴더 목록(각 job.json) + running + 과일마다
                                  {has_mask, has_instances, n_box_images, confirmed_counts, n_confirmed_out}
GET  /api/export_plan?fruit=&confirmed_only=  ← «지금 누르면 몇 장 나가나»(파일 0개 씀)
```

- **자물쇠는 `_jobs` 를 보는 동안만** 잡는다(설계 §12-2 그대로). 오래 걸리는 일은 자물쇠 밖 스레드.
  딕셔너리를 통째로 볼 때는 `dict(_jobs)`(C 층에서 한 번에 복사) 로만 읽는다.
- `export_plan` 을 하나 더 만든 이유: **확인창에 적는 숫자와 실제로 나가는 숫자가 같은 코드에서
  나와야** 하기 때문이다. `export_one(..., dry_run=True)` 과 **같은 길**로 세고 파일은 쓰지 않는다
  (번호 출처는 보지 않는다 — 장마다 파일을 열면 사과 1,001장에 100초가 걸린다).
- `export_list` 가 «과일마다 무슨 자료가 있나» 까지 같이 준다 → 화면은 탭을 열 때 **한 번만** 부른다.
  이 주소가 **404 인지**가 곧 «서버가 이 기능을 아는가» 의 판정이다(가드).

## 3. 내보내기 규칙 (`export/export_dataset.py`)

1. `export_one(fruit, out, args, **on_step=None**)` — 사진 한 장마다 `on_step(i, n)`. 끝에 결과
   딕셔너리(`n_total·n_out·n_dropped·n_instances·…`)를 돌려준다. **부르는 쪽이 없으면 예전과 똑같다**
   (기본값 None · 반환값을 안 받으면 그만).
2. manifest 에 칸 **4개** 추가 — `confirmed_status` · `confirmed_by` · `confirmed_at` · `source`.
   **앞의 9칸은 한 칸도 바뀌지 않았다**(검출 팀이 읽는 표라서). `source` = `human`(사람 확정이 있다) /
   `ai`(AI 제안뿐).
3. **사람이 «문제 있음(flag)» 으로 확정한 사진은 «사람 확정만» 에서 빠진다**(3차 결정 2).
4. CLI 에서 `--out` 폴더에 **파일이 이미 있으면 멈춘다**(전에는 말없이 덮어썼다 — 2차 실측 «바-8»).
   **빈 폴더는 통과시킨다** — 옛 시험들이 `mkdtemp()` 로 빈 폴더를 만들어 넘기기 때문이다.

## 4. 상자 — 같은 함수를 두 길이 쓴다 (`app/boxes.py`)

`api_boxes_export()` 안에만 있던 몸통(옛 185~205행)을 **글자 그대로** `export_boxes_to(data_dir, fruit,
out_dir, all_json, at)` 로 빼고, 기존 단추는 그 함수를 부르게 했다. 답의 칸 이름·순서·값은 그대로다
(실측: 리팩터 전/후 응답이 같고 YOLO txt 4개의 md5 가 같다 — §7 F).

## 5. 화면 (`index.html` · `ui.js` · `style.css` · `app.js`)

상단 탭 «데이터 정리» 하나. 탭 안은 **한 줄에 하나씩**:
과일 라디오 4 · 종류 체크 3(없는 자료는 «(없음)» 회색 + 풍선말에 이유) ·
«사람 확정만 / AI 제안 포함» 라디오(기본 앞) · **확정 장수 줄(상시)** · «서버에 저장» ·
진행 막대(1초 폴링) · 끝나면 **폴더 경로 한 줄 + 사진 장수 + 제외 장수** · «지금까지 내보낸 것» 표(최근 10개).

- 확정 장수 줄(3차 결정 1 문구 그대로):
  «**지금 확정된 사진 5장 — 0장이면 아무것도 나가지 않습니다. AI 제안까지 포함하려면 위에서 고르세요.
  · 지금 조건으로 나갈 사진 5장**»
- 확인창은 **한 번**: «복숭아 · 세그 마스크 / 조건: 사람 확정만 / 나갈 사진: 5장 / 서버 폴더(exports/)에 저장할까요?»
- 이름 칸이 비어 있으면 **이름부터** 묻는다(기존 `ensureWho()` 를 그대로 씀).
- `app.js` 는 **5줄만** 고쳤다(`showView` 에 한 칸 + `window.expOpen` 호출). 회귀 시험
  `modesim.js`·`boxsim.js` 가 떼어 가는 함수(`setTool`·`setNumMode`·`numKey`·keydown·`#box-mode`)는 건드리지 않았다.

### 가드 (규칙 §8-10)
```
탭을 열면 GET /api/export_list  →  404(또는 ok 가 아님)이면
   #expbody 를 통째로 감추고  #expguard 만 보여 준다:
   «서버가 아직 이 기능을 모릅니다 — 관리자가 켜야 합니다»
```
옛 서버(백업 서버 트리 5212) + **새 정적 파일**로 실측: 문구만 뜨고, 보이는 단추·입력칸 **0개**,
억지로 `#exp-go` 를 눌러도 나가는 쓰기 요청 **0건**.

---

## 6. 내가 정한 것 (2차·3차가 뒤집을 수 있게 이유까지)

| # | 정한 것 | 왜 |
|---|---|---|
| 1 | **빈 폴더 정책 — 화면은 안 만들고, API 는 만든다** | 화면에서 «확정 0장 + 사람 확정만» 이면 **서버를 부르지 않고** «0장 — 나갈 것이 없습니다» 만 보여 준다(폴더 0개, 실측 가-17·18). 그러나 `POST /api/export_start` 를 직접 부르면 폴더는 생기고 **`manifest.csv`(1,195줄 전부 «제외 · not_confirmed») + `job.json`** 만 남는다 — 왜 0장인지 나중에 설명할 수 있어야 하고, 스레드가 이미 떠 있는데 폴더를 지우면 «누가 지웠나» 가 더 헷갈리기 때문. `images/`·`masks/` 는 **만들지 않는다**(export_one 이 장마다 늦게 만든다) |
| 2 | manifest 는 **칸 이름을 안 바꾸고 뒤에 4칸만 붙였다** | 지시서의 «`action=dropped · reason=flag`» 는 지금 표에서 **`포함여부`=«제외» · `excluded_reason`=`confirmed_flag`** 에 해당한다. 앞 9칸 이름을 바꾸면 검출 팀이 읽는 표와 옛 시험이 깨진다. 값 이름을 `flag` 가 아니라 `confirmed_flag` 로 한 것은 옛 `--drop-flag` 의 `status_flag`(= AI 제안 flag)와 **구별**하려는 것 |
| 3 | «열매 번호» 는 **세그 마스크와 함께만** 나간다(혼자 고르면 400) | `export_one()` 이 번호를 쓸 때 마스크도 같이 쓴다. 화면은 번호를 켜면 마스크를 자동으로 켠다 |
| 4 | «AI 제안 포함» 은 **옛 기본값 그대로**(`keep_duplicates=False`·`drop_flag=False`·`copy_images=False`) | 2차가 «옛 export_one 과 같은 파일 집합» 을 md5 로 대조할 수 있게. 실측 D-2·D-3·D-4 동일 |
| 5 | 미리 세기(`export_plan`)를 주소 하나로 따로 뒀다 | 확인창 숫자 = 실제 나가는 숫자. 라디오를 바꿀 때마다 서버 로그에 dry-run 3줄이 찍히는 것은 감수(작음) |
| 6 | 브라우저 내려받기 없음 · 여러 과일 동시 실행 없음(과일마다 하나) | 설계 §12-2 «안 할 것» 그대로 |

---

## 7. 시험 표 — 내가 새로 짠 것 (모래상자 5211 새 판 / 5212 옛 판)

| 묶음 | 무엇을 봤나 | 결과 |
|---|---|---|
| **A** 발견 | `export_list` 200 · `dir`=exports · 과일 4 · 복숭아(마스크 O·번호 X·상자 1장) · 사과(번호 O·상자 X) · 미리 세기 0장/125장 · 미리 세기는 **파일 0개** | 10/10 |
| **B** 빈 폴더 | 블루베리 확정 0장 → `done · 사진 0 · 제외 1,195` · 폴더에 `manifest.csv`+`job.json` 만(`images/`·`masks/` 없음) · manifest 전부 `not_confirmed` · job.json 에 시작·끝·조건·장수·누가 | 6/6 |
| **C** 확정 10장 | 복숭아 ok3·fixed2·flag2·exclude3 → **나간 것은 ok3+fixed2 = 5장 정확히** · manifest 13칸 · `confirmed_flag` 2 · `confirmed_exclude` 3 · `not_confirmed` 115 · 확정 10장은 `confirmed_*` 3칸 + `source=human` · 나머지는 빈칸 + `source=ai` · **«수정함» 2장은 masks_fixed 사본이 나갔다(픽셀 md5 일치, 원본과는 불일치)** · 이미지는 심볼릭 링크 | 16/16 |
| **D** AI 제안 포함 | 리팩터 **전** 코드(백업 트리)로 돌린 CLI 결과와 **masks/ 125장 md5 전부 동일** · images/ 링크 대상 동일 · manifest **앞 9칸 줄 하나까지 동일** · 새 칸은 확정 10장만 `human` | 6/6 |
| **E** 열매 번호 | 사과 2장 → `instances/` uint16 · 최대 번호·번호 개수가 `load_inst()` 와 일치(95·102) · manifest `instances_source` 채워짐 | 4/4 |
| **F** 상자 | 상자 4개짜리 3장을 저장 → **리팩터 전/후 응답 동일 · YOLO txt 4개 md5 동일 · `boxes_all.json`(시각 칸 제외) 동일 · 새 길 `exports/…/boxes/` 도 같은 md5** · 상자만 고르면 `images/` 안 만듦 | 9/9 |
| **G** 동시성 | 포도 내보내는 중 **같은 과일 두 번째 = 409** · 다른 과일(사과)은 200 · `running` 에 둘 다 보임 · 둘 다 done(2,403 · 2) · 409 는 **폴더를 만들지 않았다** | 6/6 |
| **H** 덮어쓰기 금지 | 앞으로 4초치 폴더를 미리 만들어 두고 요청 → **409**(500 아님) + 사람 말 · **미리 있던 폴더 내용 그대로** | 2/2 |
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| **J** 껐다 켜기 | 서버를 껐다 켜도 목록 7개 그대로(job.json 복원) · `running` 비어 있음 · 옛 작업의 상태도 job.json 으로 답함 · 최신 것부터 | 4/4 |
| **K** 공용 폴더 | `T/data` 안에 바뀐 파일 **0개** · `T/exports` 는 **아예 없음**(진짜 산출물 0개) | 2/2 |
| **가** 화면(파이어폭스 1366×768) | 탭 1개 · 라디오 4·체크 3·라디오 2 · 기본 «사람 확정만»+«세그 마스크» · 없는 자료는 비활성+이유 · **스크롤 없음**(642 ≤ 642) · 확인창 한 번(과일·종류·조건·장수) · 진행 막대 100% · **경로 줄 `exports/260918_163803_peach` + 사진 5장 · 제외 120장** · 표에 쌓임 · 0장이면 확인창도 안 뜨고 폴더도 안 생김 · 이름 칸이 비면 이름부터 물음 | 20/20 |
| **나** 옛 서버 + 새 화면 | 가드 문구만 · 내용 통째로 숨음 · **보이는 단추 0개** · 억지로 눌러도 **쓰기 0건** | 4/4 |
| **t3** 사용법 그림 | `app/static/help/ui_export_260918c3.png` 새로 만듦(기존 help 그림은 하나도 안 건드림) | 2/2 |

합계 **t1_api 79 / 0 · t2_ui 24 / 0 · t3_helpfig 2 / 0** (실패 0).

---

## 8. 회귀 — 사이클 1·2 시험을 **한 글자도 안 고치고** (`cycle_3/stage1/reg_c3/`)

돌린 시각(실측): **2026-09-18 16:39 ~ 16:58** (19분). 시험 코드는 사이클2 3차 소수정의 것을 그대로 복사하고
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
그래야 사이클2 의 로그·json(= 2차·3차의 근거)을 덮어쓰지 않는다.

| 시험 | 전 (cycle_2/stage2b) | 후 (지금) | 판정 |
|---|---|---|---|
| `py_compile` 6파일 · `node --check` 2파일 | OK | **OK** | 같음 |
| `boxes.py` 자체 점검 | 통과 | **통과** | 같음 (리팩터 뒤에도) |
| `modesim.js` | 31/31 | **31/31** | 같음 |
| `boxsim.js` | 50/50 | **50/50** | 같음 |
| 1차 `t1_api` | 79 / 0 | **79 / 0** | 같음 |
| 1차 `t2_queue` | 35 / 8 | **35 / 8** | 같음(그 8개는 사이클2 N5 결정으로 **낡은 기대값** — 3차 판정 §1) |
| 1차 `t3_conc` | 8 / 0 | **8 / 0** | 같음 |
| 1차 `t4_paint8` | 22 / 0 | **22 / 0** | 같음 |
| 2차 `s1_api` | 72 / 4 | **68 / 8** | ⚠ 아래 설명 |
| 2차 `s2_scenario` | 20 / 0 | **20 / 0** | 같음 |
| 2차 `s3_guards` | 18 / 0 | **18 / 0** | 같음 |
| 2차 `s4_paint8` | 21 / 1 | **21 / 1** | 같음(그 1개는 12.5px 딱지 = N10, 사이클4 몫) |
| 2차 `s5_live_guard`(part_a+c) | 9 / 4 | **9 / 4** | 같음 |
| 2차 `s6_layout` | 7 / 0 | **7 / 0** | 같음 — **숫자까지 한 자리도 안 다르다**(캔버스 82.7~88.1% · 편집화면 글자 155/171/226자, `diff` 로 대조) |
| 2차 `s7_clip` | 2 / 0 | **2 / 0** | 같음 |
| 2차 `s8_guard_advance` | 3 / 0 | **3 / 0** | 같음 |
| 사이클1 `t1_measure`(배치·글자) | FAIL 0 | **155 / 0** | 같음 |
| 사이클1 `t6_view`(보기 전환) | 126 / 4 | **126 / 4** | 같음 |
| 사이클1 `t3_matrix`(네 과일×세 작업 12칸) | FAIL 0 | **84 / 0** | 같음 |
| 사이클1 `t4_keys`(단축키 25) | FAIL 0 | **25 / 0** | 같음 |
| 사이클1 `t2_reg` | FAIL 0 | **FAIL 0** | 같음 |
| 사이클1 2차 `s5_fix`(여백 붓질) | 9 / 0 | **9 / 0** | 같음 |

### `s1_api` 72/4 → 68/8 — 다섯 개는 «시험이 낡은 것», 하나는 **고쳐진 것**

| 항목 | 전 | 후 | 왜 |
|---|---|---|---|
| **바-6** «manifest 에 사람이 확정한 판정 칸이 있나» | ❗FAIL | **통과** | 이번 사이클이 고친 것(N6 · 확정 4칸) |
| 바-1 dry-run 포함 장수 | 통과 | FAIL `6 vs 7` | 그 시험은 «확정 8장 − 확정제외 1장 = 7» 을 기대한다. **3차 결정 2**(사람 확정 flag 는 기본 제외)로 그중 flag 1장이 더 빠져 **6장**이 맞다 |
| 바-2 실제 파일 장수 | 통과 | FAIL `(6, 6)` | 위와 같은 한 가지 이유 |
| 바-3 manifest 포함 줄 수 | 통과 | FAIL `6` | 위와 같은 한 가지 이유 |
| 바-5 «빠진 이유가 not_confirmed/confirmed_exclude 뿐» | 통과 | FAIL `confirmed_flag: 1` | 이유가 하나 늘었다(의도한 것) |
| 바-7 «AI 가 제외한 것도 사람이 ok 로 확정하면 나간다» | 통과 | FAIL `7` | 기대값이 `7+1=8`. 실제 `6+1=7` — 규칙대로면 맞는 값 |
| 검증-8·9·10 | FAIL | FAIL | 전과 같음(N7·N8 = 사이클4 몫) |
| 바-8 «같은 out 으로 두 번 돌려도 안 막는다» | 통과(`rc=0`) | 통과(`rc=1`) | 시험 자체가 «무조건 통과» 로 적혀 있고 **기록만** 바뀐다 — 이제 CLI 가 막는다(E1) |

→ 실패 8개 중 **3개는 전부터 있던 것**(검증-8·9·10), **5개는 낡은 기대값**(전부 한 가지 원인:
사람 확정 flag 제외), 그리고 **전에 실패하던 바-6 이 통과**로 바뀌었다. 시험 코드는 한 글자도 안 고쳤으므로
**사이클 4 회귀 때 기대값을 갱신**해야 한다(사이클2 가 `t2_queue` 8칸을 그렇게 남겨 둔 것과 같은 성질).

---

## 9. 글자 예산 («그림판» 규칙)

| 잰 곳 | 전 | 후 |
|---|---|---|
| **편집 화면 `#view-edit`** (사이클1 판정의 138자) | 138 | **건드리지 않음** — 이 사이클은 `#view-edit` 안의 HTML·CSS 를 한 줄도 바꾸지 않았다(회귀 `s4_paint8`·`s6_layout` 으로 재측정, §8) |
| 상단 바 `#topbar` | 16자 | **22자** (+6 = 탭 이름 «데이터 정리») |
| 새 탭 `#view-exp` | — | **495자** (실측, 내보낸 목록 7줄이 있는 상태) |

새 탭 495자의 속내: **고정 문구·딱지 ≈ 150자**(과일 4 + 종류 3 + 조건 2 + 단추 + 표 머리말)
+ **3차가 지시한 확정 장수 줄 77자** + 나머지 **≈ 270자는 «지금까지 내보낸 것» 표의 데이터**
(폴더 이름 27자 × 7줄). 설명·이유는 한 글자도 화면에 두지 않고 전부 풍선말(title)과 사용법 페이지로 보냈다.
표는 **최근 10개만** 보여 주고 그 아래에 «전체 N개» 한 줄만 적는다.

---

## 10. 스크린샷 (진짜 파이어폭스 · 1366×768 · `~/ff_shots/c3/stage1/`)

| 파일 | 무엇 |
|---|---|
| `c3_01_tab_default.png` | 탭을 연 처음 모습(복숭아가 기본으로 잡힘) |
| `c3_02_peach_kinds.png` | 복숭아 — «열매 번호 (없음)» 회색 · 상자는 켤 수 있음 (01 과 같은 화면) |
| `c3_03_saved.png` | 저장이 끝난 뒤 — 경로 줄 + 장수 + 표 |
| `c3_04_zero.png` | 확정 0장(블루베리) + «사람 확정만» → «0장 — 나갈 것이 없습니다» |
| `c3_05_old_guard.png` | **옛 서버 + 새 화면** → 가드 문구만 |
| `c3_helpfig.png` | 사용법 페이지에 넣은 그림(= `app/static/help/ui_export_260918c3.png`) |

---

## 11. 🔴 켜기 순서 (3차가 직접 · 나는 5111 에 손대지 않았다)

1. `tail -20 $T/app/logs/server.log` — 최근 1분에 `POST /api/save`·`/api/status`·`/api/save_instances` 가 없나
2. `ps -o pid,lstart,cmd -p <지금 PID>` — **내 계정 프로세스인지** 확인(남의 것이면 멈춘다)
3. `cd $T/app && bash run.sh restart` (사이클2 3차가 15:58 에 쓴 것과 같은 명령)
4. 켠 뒤 확인 GET(쓰기 0건):
   ```bash
   B=http://127.0.0.1:5111
   curl -s "$B/api/export_list"                  # ok:true · dir:"exports" · fruits 4개 (옛 판이면 404)
   curl -s "$B/api/export_plan?fruit=peach"      # n_out = 지금 확정된 장수
   curl -s "$B/api/fruits" | head -c 300         # 사이클2 기대값 그대로(peach 125 · grape 2406 · apple 1001 · blueberry 1195)
   ```
5. 브라우저에서 **Ctrl+F5** 한 번 → «데이터 정리» 탭이 가드 없이 열리면 켜진 것.
6. 되돌리는 법(한 줄씩):
   ```bash
   T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
   cp $T/app/_backup_260918_c3_server.py            $T/app/server.py
   cp $T/app/_backup_260918_c3_boxes.py             $T/app/boxes.py
   cp $T/export/_backup_260918_c3_export_dataset.py $T/export/export_dataset.py
   cp $T/app/static/_backup_260918_c3_index.html    $T/app/static/index.html
   cp $T/app/static/_backup_260918_c3_app.js        $T/app/static/app.js
   cp $T/app/static/_backup_260918_c3_ui.js         $T/app/static/ui.js
   cp $T/app/static/_backup_260918_c3_style.css     $T/app/static/style.css
   cp $T/app/static/_backup_260918_c3_help.html     $T/app/static/help.html
   cp $T/app/_backup_260918_c3_README.md            $T/app/README.md
   ```

> ⚠ **지금 5111 에 이미 나가 있는 것**: 정적 파일 4개(`index.html`·`app.js`·`ui.js`·`style.css`)와
> 사용법 페이지·그림. 서버가 옛 판이므로 탭을 눌러도 **가드 문구만** 보이고 아무것도 못 누른다
> (옛 서버로 실측). 서버 파이썬 3개(`server.py`·`boxes.py`·`export_dataset.py`)는 **재시작 전까지 옛 판**이다.

---

## 12. 2차 검수가 그대로 재현할 명령

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
PY=/home/kds0206/.conda/envs/kwak/bin/python
cd $T/cycles/260918_paint/cycle_3/stage1

bash runall.sh                      # 전부 한 번에 (약 35분)
# 또는 하나씩 — t2_ui 는 t1_api 가 만든 «확정 5장» 을 그대로 본다(순서대로)
$PY -u t1_api.py     > t1_api.log     2>&1    # 서버 쪽 79항목   (약 4분)
$PY -u t2_ui.py      > t2_ui.log      2>&1    # 진짜 브라우저 24항목 (약 2분)
$PY -u t3_helpfig.py > t3_helpfig.log 2>&1    # 사용법 그림 1장
$PY mk_reg_c3.py && bash reg_c3/runall_c3.sh > reg_c3/runall_c3.log 2>&1   # 회귀 (약 25분)

# 고친 자리를 다시 보고 싶으면 (아무것도 쓰지 않음)
$PY fix_260918_c3.py --dry ; $PY fix_260918_c3_docs.py --dry
diff -u $T/app/_backup_260918_c3_server.py $T/app/server.py | less
```

⛔ **`t5_shots.py` 와 실서버(5111) 접속 시험은 돌리지 마세요** — 앞의 것은 실서비스 폴더
`app/static/help/` 의 그림을 덮어쓰고, 뒤의 것은 사람이 쓰는 서버에 붙습니다.

---

## 13. 파일 위치

```
T/cycles/260918_paint/cycle_3/
  stage1_work.md              ← 이 문서
  stage1/
    fix_260918_c3.py          코드 20자리를 고치는 스크립트(백업 뜨고 고침 · --dry 로 미리보기)
    fix_260918_c3_docs.py     사용법·README 4자리
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    lib_c3.py                 내 모래상자 도구(5211 새 판 / 5212 옛 판 · md5 · 진짜 브라우저)
    t1_api.py  t1_api.log  t1_api.json        서버 쪽 79항목
    t2_ui.py   t2_ui.log   t2_ui.json         진짜 파이어폭스 24항목
    t3_helpfig.py  t3_helpfig.log             사용법 그림 1장
    runall.sh                 위 §12 를 한 번에
    sandbox/                  app+export+data 실복사(**새 코드**) · 안에 exports/ 가 생긴다
    sandbox_old/              같은 사본인데 서버 파이썬만 _backup_260918_c3_*(**옛 판**) · 정적 파일은 새 판
    reg_c3/                   사이클1·2 회귀 묶음 사본(reg_s0·reg_s1·reg_s2 + sandbox) · runall_c3.sh
~/ff_shots/c3/stage1/         스크린샷 6장
```

---

## 13-2. 끄고 치운 것 · 남은 것 (끝내기 점검, 16:58 실측)

- 내가 띄운 모래상자 서버는 **전부 내 PID 로만** 껐다 — `ss -ltn` 에 5211·5212·5241~5269 **하나도 없음**.
- 아직 떠 있는 `geckodriver` 3개(**871735 · 1025718 · 1026914**, 12:00·13:13 기동)와 그 파이어폭스 3개는
  **내 것이 아니다**(사이클1 2차·사이클2 가 남긴 것 — 사이클2 §13-2-7 에도 같은 목록이 있다). **끄지 않았다.**
- 실서버 5111 은 **PID 1458190 · 15:58:22 기동 그대로**(사이클2 3차가 켠 것). 붙지도, 재시작하지도 않았다.
- 공용 `T/data` 는 16:00 이후 바뀐 파일 **0개**, `T/exports` 는 **아직 없음**(진짜 산출물 0개).
- 지워도 되는 모래상자(다 쓰면): `cycle_3/stage1/sandbox`(105MB) · `sandbox_old`(105MB) · `reg_c3`(117MB).

## 14. 2차(공격적 리뷰)에게 미리 말해 두는 약한 곳

1. **서버가 내보내는 중에 죽으면** 그 폴더에는 `job.json` 이 없어 목록에 안 나온다(반쯤 만든 폴더가
   조용히 남는다). 지우지 않는 쪽을 골랐다 — 사람이 보고 지우게.
2. `_jobs` 는 **끝난 작업도 계속 들고 있다**(서버를 껐다 켜면 사라진다). 한 번에 몇십 개면 무시할 크기지만
   상한은 없다.
3. `export_plan` 을 라디오마다 부른다 → 서버 로그에 dry-run 3줄씩 쌓인다(파일은 안 쓴다).
4. 가드는 «404 가 아닌 다른 오류»(예: 500)일 때도 **같은 문구**로 탭을 잠근다. 안전한 쪽으로 틀렸지만
   문구가 상황과 다를 수 있다.
5. «AI 제안 포함» 에는 `--keep-duplicates`·`--copy-images` 를 화면에 두지 않았다(CLI 기본값 고정).
6. 확정 장수(`n_confirmed_out`)는 **ok+fixed** 만 센다. 화면의 «나갈 사진 N장» 은 `export_plan` 이
   따로 세므로 두 숫자가 같아야 한다 — 다르면 그 자체가 버그다.
