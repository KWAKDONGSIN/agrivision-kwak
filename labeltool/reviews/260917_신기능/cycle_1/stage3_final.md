작성: 2026-09-17

# 0917 새 기능 5회 검수 — 사이클 1 · 3차 최종 판정 (Fable 5.1)

주제: **좌표·저장 정확성**
읽은 것: `cycles/260917_신기능/cycle_1/stage1_work.md`(1차 Opus 5), `stage2_review_work.md`(2차 Opus 5), 계획서, 참고저장소 적용기록,
`app/boxes.py`, `app/static/app.js` 상자 블록(L895–1079)·`resizeCanvas`·`draw`·`toImg`, `app/instances.py`, `export/export_dataset.py`, `~/.claude/skills/ponytail-review/SKILL.md`
코드는 **읽기만** 했고 고치지 않았습니다(다른 에이전트가 `app.js`·`index.html`·`style.css` 를 쓰는 중).

근거 표기: ✅ 논문 근거(이번엔 없음) · 📄 코드·파일 실측(경로 명시) · ❌ AI 판단

내가 직접 다시 돌린 것 📄
```
node --check app/static/app.js                          → OK
node cycles/cycle_1/stage2/verify_resize_real.js        → A~E 전부 통과 (C1 고침·B1 회귀 확인)
python3 app/boxes.py                                    → 자체 점검 통과
python3 -c "cx,bw=0.999199,0.001603; print(cx+bw/2)"    → 1.0000004999999998  (2차 R1 반례 재현)
```

---

## ① 한 줄 결론

1차가 고친 B1(옮기기 누적 반올림)·B2(3,000개 초과 조용히 사라짐)와 2차가 고친 C1(크기조절 뒤집기 붕괴)은 **모두 실제로 고쳐졌고 재현 확인됐습니다**. 갈린 항목은 2차 쪽이 맞지만(YOLO 값이 1.0 을 5e-7 넘음) **고칠 문제가 아니라 그대로 둡니다**. 남은 실질 문제는 D3(서버가 버린 상자가 화면에 남음) 하나이며, **저장 응답으로 화면 목록을 덮어쓰는 방식(가)** 으로 결정합니다 — 사이클 2 의 1차가 구현합니다.

## ② 갈린 항목 판정

| 항목 | 1차 | 2차 | 판정 | 근거 |
|---|---|---|---|---|
| YOLO `중심±반폭` 이 1.0 을 넘는가 (1차 ②-4 vs 2차 R1) | 「우리는 절대 안 넘는다」 | 「넘는다, 1.0000005·-5e-07」 | **2차 맞음. 그러나 고치지 않음 — 그대로 둔다.** | 📄 재현: `0.999199+0.001603/2 = 1.0000004999999998`. 원인은 좌표 범위가 아니라 `boxes.py:L156-158` 이 중심과 너비를 **각각** `%.6f` 로 반올림하는 것 — 어떤 6자리 형식이든 생기는 성질. 📄 검출 팀 파일 1,752개도 331줄이 같은 성질(1차 실측). 📄 ultralytics 8.4.115 `data/utils.py:L294-295` (`/data/project/AIhwasung2026/.../site-packages/ultralytics/data/utils.py`) 는 각 열 값이 `≤1.01`·`≥-0.01` 인지만 검사하고 `중심±반폭` 은 계산하지 않음 → 우리 값 최대 `1.000000`, 최소 `0.000601` 이라 통과. ❌ 자릿수를 늘리거나 값을 깎으면 오히려 팀 형식과 달라져 손해. **단 1차의 「절대 안 넘는다」 문장은 최종 판정서에 옮기지 않는다.** 사이클 4 «되돌아 읽어도 같은 상자» 시험은 `round(cx·W ± bw·W/2)` 픽셀 되돌림 기준으로 한다(2차 C3 가 이미 7개 전부 일치 확인). |
| 「좌표 변환은 정확했다」 결론의 범위 (2차 R2) | 옮기기·휠·역변환만 시험하고 전체를 정확하다고 결론 | 크기조절을 안 시험했고 거기 더 큰 버그(C1)가 있었다 | **2차 맞음.** C1 고침은 내가 `verify_resize_real.js` 로 재확인(전부 통과). | 📄 고친 `app.js:L966-971`(고정점 `ax/ay`), `L1000`. ❌ 이후 사이클은 «시험한 조작 / 안 한 조작» 표를 보고서에 의무로 남긴다. |
| 반올림 규칙이 둘 (파이썬 `round` 짝수, JS `Math.round` 올림) (2차 R3) | 「파이썬 round 통과」 | 「통과지만 규칙이 둘」 | **실효 없음 — 그대로.** | 📄 화면은 항상 정수를 보냄(`app.js:L1000, L1011, L995-996`). 사이클 5 에서 `boxes.py clean()` 주석 한 줄만. |
| B2 가 살아 있는 서버에 반영됐나 | 「아직 미반영(재시작 필요)」 | 「반영됨(PID 2835094)」 | 시점 차이, 둘 다 맞음. **지금은 반영.** | 📄 2차가 살아 있는 서버에 3,005개 POST → `over:5`. |
| D3 처리 방식 | «사용성 결정»으로 넘김 | 의견 (나): 버려질 상자만 빨갛게 남기고 `bDirty` 유지 | **(가) 저장 응답으로 화면 목록 덮어쓰기.** ③ 참조 | ❌ (나)는 «버려질 표시» 상태·색·`bDirty` 예외 규칙을 새로 만들어야 하고, 사람이 그 상자를 직접 지우기 전엔 «저장 안 됨» 이 영원히 남음. (가)는 서버 1줄 + 화면 4줄로 «화면 = 파일» 불변조건이 서고, 사라진 것은 Ctrl+Z 로 볼 수 있어 2차의 우려(«왜 사라졌는지 본다»)도 충족. |
| 크기조절에 최소 크기를 걸 것인가 (2차 ⑤-2) | — | 막지 말자 | **막지 않는다.** D3 (가) 로 흡수. | ❌ 화면 규칙을 하나 더 두면 서버 `MIN_SIDE` 와 두 벌이 됨. 저장 때 서버가 정리하고 화면이 그 결과를 따르면 충분. |
| 손잡이 반경이 배율에 반비례 (2차 ⑤-4) | — | 사이클 2 로 | 사이클 2 (좌표 정확성 아님). | 📄 `app.js:L905 HANDLE=7`, `L959 r = HANDLE / S.view.s`. |
| 보고서 파일 이름 충돌 (2차 ⑤-5) | — | 사람이 정리 | **해결됨.** | 📄 `cycles/260917_신기능/` 폴더 분리 + `README.md`. 0916 것은 그대로. |

## ③ D3 구현 지시 (사이클 2 · 1차가 할 것)

**결정: 저장 응답의 상자 목록으로 화면을 덮어쓴다.** `app/boxes.py` `api_boxes_save()` 의 `jsonify(...)` 에 `"boxes": boxes` 를 넣는다(정리된 목록은 이미 손에 있으므로 1줄, 3,000개여도 응답 200KB 정도). `app/static/app.js` `saveBoxes()` 는 ①보내기 전에 `const stem = S.stem` 을 붙잡고, 응답이 온 뒤 `S.stem !== stem` 이면(저장 중에 사진을 바꾼 경우) 화면을 건드리지 않고 flash 만 띄운다 ②`j.dropped || j.over` 일 때만 `bpush()` 하고(되돌리기로 «무엇이 사라졌는지» 볼 수 있게) ③`S.boxes = j.boxes; S.bsel = -1; S.bDirty = false;` 순서로 쓴다 — `bpush()` 가 `bDirty` 를 true 로 올리므로 **반드시 그 뒤에** false 로 내린다 ④`boxInfo` 문구를 「저장됨 … · 너무 작아 버린 것 N — 화면에서도 지웠음(Ctrl+Z 로 되돌려 볼 수 있음)」 으로, `dropped||over` 가 있으면 `flash(..., true)` 경고색으로 띄운다 ⑤`S.dirty = true` 로 다시 그린다. 확인 방법: `cycles/260917_신기능/cycle_1/stage1/test_clean.py` 에 «2픽셀 미만 2개 섞은 5개 POST → 응답 `boxes` 길이 3」 검사를 한 줄 추가하고, 2차의 `verify_resize_real.js` 방식(`new Function` 으로 `saveBoxes` 를 떼어 내 가짜 `post` 로 실행)으로 «저장 뒤 `S.boxes.length === 3`, `S.bDirty === false`, `S.bundo.length === 1`» 을 확인한다. 2차 ⑤-2(크기조절 최소 크기)는 이 결정으로 함께 끝난다 — 화면에서 따로 막지 않는다.

## ④ 1차 «판단 필요» 7건 + 2차 추가 항목 분류

| # | 내용 | 분류 | 비고 |
|---|---|---|---|
| D1 | 클래스 번호가 검출 팀 `grape.yaml`(`0: bunch`)와 어긋남 (우리 `fruit=0, bunch=1, other=2`) | **사람 결정** | 📄 `work/park_seongmoon/yolo_grape/cv1/grape.yaml` 실측 `names: 0: bunch` 하나뿐. 선택지는 계획서 그대로 (가)우리 번호를 맞춤 (나)과일별 표 (다)내보낼 때 대응표. ❌ 코드 변경량은 (다)가 가장 작음(`boxes.py:L157` 한 식) — 결정 전엔 손대지 않는다. 사이클 4 주제. |
| D2 | `resizeCanvas` 의 `round(w*dpr)` 와 `draw` 의 `setTransform(dpr)` 불일치 (최대 ≈0.3 CSS px) | **미해결(보류)** | 📄 `app.js:L387-389, L413`. 상자만이 아니라 붓에도 해당, 브라우저 실측 필요. 고친다면 `resizeCanvas` 에서 `cv._sx = cv.width / w; cv._sy = cv.height / h` 를 저장하고 `draw`·`fitView`·`toImg` 가 `dpr` 대신 그것을 쓰는 것(3곳). 사이클 2 에서 실제 브라우저를 쓸 수 있으면 그때, 아니면 사이클 5 «보류 목록» 에. |
| D3 | 서버가 버린 상자가 화면에 남음 | **해결(결정함)** | ③ 대로 사이클 2 1차가 구현. |
| D4 | 단순 고르기 클릭에도 `bDirty=true`, 고르기·손잡이 잡기마다 `bpush()` 로 되돌리기 30칸이 참 | **미해결(사이클 2)** | 📄 `app.js:L908 bpush`, `L968, L977`(mousedown 에서 push), `L1015`(mouseup 에서 무조건 `bDirty=true`). 고칠 것: mousedown 에서는 `S.drag.before = JSON.stringify(S.boxes)` 만 저장하고, `boxMouseUp` 에서 `JSON.stringify(S.boxes) !== S.drag.before` 일 때만 `bundo.push(before)`·`bDirty=true`. `S.bsel` 바꾸는 것은 `bDirty` 를 올리지 않는다. 확인: 고르기만 100회 → `bundo.length 0`, `bDirty false`. |
| D5 | `clean()` 상한이 `x1≤w-1`, `x2≤w` 로 다름 | **해결(그대로 둠)** | 📄 2차 검산 동의: `x1=w-1` 이면 폭 ≤1 이라 `MIN_SIDE` 가 버림. ❌ 사이클 5 정리 때 `w-1`→`w` 로 네 줄을 같은 꼴로 만들어도 동작 동일(선택). |
| D6 | `/api/boxes_export` 가 `rec["stem"]` 을 검증 없이 파일명으로 씀 | **해결(안 고침)** | 📄 그 json 은 `api_boxes_save` 만 쓰고 저장 전 `check(fruit, stem)` 을 지남(`boxes.py:L90`). 지금 경로로 도달 불가. |
| D7 | 3,000개 초과 시 «앞 3,000개» 를 남기는 규칙이 문서에 없음 | **미해결(사이클 5 문서)** | ❌ 사람이 손으로 3,000개를 그릴 일은 없고 초벌도 3,000에서 끊음(`boxes.py:L130`). README §10 에 「그린 순서대로 앞 3,000개」 한 줄이면 끝. |
| 2차 ⑤-4 | 손잡이 반경 `HANDLE/s` 가 0.03배에서 233 이미지px | **미해결(사이클 2)** | ❌ `hitHandle` 의 `r` 을 `Math.min(HANDLE / S.view.s, 짧은 변 / 3)` 정도로 상한. 겹친 상자 고르기와 같은 주제. |
| 2차 R3 | 반올림 규칙 둘 | **해결(그대로 둠)** | ② 표 참조. |

## ⑤ ponytail — 상자·번호 코드에서 지울 수 있는 것

형식 `파일:함수 — 자를 것 — 대체물`. 정확성 문제는 여기 넣지 않았습니다(위 ②④).

- `boxes.py:L12 (모듈) — delete: import time 미사용 — 없음.` (📄 `time.` 호출 0건)
- `boxes.py:L190-208 demo() — shrink: clean() 규칙 19줄을 손으로 다시 씀(`class C`·`got, dropped` 는 죽은 줄). 이 점검은 **실제 clean() 을 시험하지 않는다** — clean() 은 상수만 쓰므로 `register` 밖 모듈 최상위로 올리고 demo 가 `clean(raw, 40, 40)` 을 직접 부른다. 약 -12줄, 규칙이 두 벌로 갈릴 위험 제거.`
- `boxes.py:L157 api_boxes_export — shrink: `CLASSES.index(b.get("cls","fruit")) if b.get("cls") in CLASSES else 0` — clean() 이 이미 `cls∈CLASSES` 를 보장(`L69`)하므로 `CLASSES.index(b["cls"])`. (D1 결정이 (다)면 이 자리가 대응표가 됨.)`
- `boxes.py:L80-84 api_boxes — shrink: `(d or {}).get` 세 번 — `d = read_boxes(fruit, stem) or {}` 한 줄 뒤 `d.get`; `saved` 는 `os.path.exists(box_path(...))`.`
- `export_dataset.py:L60-103 instance_source()·copy_instances() — yagni/중복: `instances.py` 의 `source_of()`(L59-75)·`_read_u16()`·`_png_u16_bytes()` 와 같은 논리를 다시 씀. `PARK`·`SEED_DIRS` 상수도 두 파일에 따로(`instances.py:L20-21`, `export_dataset.py:L60-61`) — 한쪽 경로만 바뀌면 조용히 갈림. `instances.py` 의 `source_of` 를 `register` 밖으로 올리고(`gt_path` 를 인자로) export 가 `from instances import ...`. 약 -30줄.` ⚠️ **번호 편집 화면을 만드는 에이전트가 끝난 뒤에** 손댈 것.
- `instances.py:L84-92 serve_instances — shrink: `layer=="gt"` 분기가 `source_of` 를 부른 뒤 결과를 다시 뒤집음. `source_of(fruit, stem, allow_fixed=(layer!="gt"))` 처럼 인자 하나로 4줄.` (같은 ⚠️)

`net: -50 lines possible.` (`boxes.py` 만 따지면 -16.) 자체 점검 `demo()` 자체는 ponytail 최소치이므로 지우지 않습니다.

## ⑥ 사이클 2 · 1차가 할 일 (우선순위)

1. **D3 구현** — ③ 그대로(`boxes.py` 1줄 + `saveBoxes` 4줄) + `test_clean.py`·JS 검사 추가. 서버 재시작은 남의 작업 없을 때만(`bash app/run.sh restart`).
2. **D4** — `bDirty`·`bundo` 를 «실제 변화» 때만(④ D4 의 방법). 고르기만으로 «저장 안 됨» 이 뜨지 않게.
3. **손잡이 반경 상한 + 겹친 상자 고르기**(사이클 2 주제) — `hitHandle` 의 `r` 상한, 작은 상자가 큰 상자 안에 있을 때 고르기.
4. **ponytail 중 `boxes.py` 항목만** 깎기(`import time`, `clean()` 최상위 + `demo()` 호출, L157). `instances.py`·`export/` 는 번호 편집 에이전트가 끝난 뒤.
5. 보고서에 «시험한 조작 / 안 한 조작» 표를 넣고, `index.html:L119` 「상자 그리기 (X)」 라벨 정정(X 는 모드 토글이지 그리기 도구 키가 아님 — `app.js:L776`).

사람 결정 대기: **D1 클래스 번호**(계획서 «사람이 정해야 하는 것» 1번). 결정 전에는 `boxes.py:L18 CLASSES`·`L157` 을 손대지 않습니다.
