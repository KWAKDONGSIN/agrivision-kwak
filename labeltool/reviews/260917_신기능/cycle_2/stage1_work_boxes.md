작성: 2026-09-17

# 0917 새 기능 5회 검수 — 사이클 2 · 1차 작업(나) «상자 저장 응답 + boxes.py 깎기» (Opus 5)

담당 범위: **`app/boxes.py` 한 파일만.** 사이클 1 3차 판정(`cycle_1/stage3_final.md`)의 **D3 서버 절반**과 **⑤ ponytail 중 `boxes.py` 항목**.
증거 폴더: `cycles/260917_신기능/cycle_2/stage1_boxes/`
근거 표기: 📄 실측(경로·값 명시) · ❌ 내 판단

---

## ① 합격 기준 (먼저 적고 그다음 실행했습니다)

| # | 기준 | 판정 |
|---|---|---|
| A1 | `POST /api/boxes` 응답에 저장된 상자 목록 `boxes` 가 실려 온다 | ✅ |
| A2 | 기존 응답 필드 `ok`·`n_boxes`·`dropped`·`over`·`at` 가 **그대로** 남는다(이름·값·꼴) | ✅ |
| A3 | 늘어난 열쇠는 `boxes` 하나뿐, 없어진 열쇠 없음 | ✅ |
| A4 | 저장 응답의 `boxes` 가 **되읽기(`GET /api/boxes`) 결과와 완전히 같다** | ✅ |
| B1 | 안 쓰는 `import time` 이 없다 | ✅ |
| B2 | `clean()` 이 `register()` 밖 모듈 최상위에 있다 | ✅ |
| B3 | `python3 app/boxes.py` 자체 점검이 **실제 `clean()`** 을 불러 통과한다(규칙을 손으로 다시 적지 않는다) | ✅ |
| C1 | 저장·되읽기 **동작이 이전과 같다**(작은 상자 버림 `dropped`, 뒤집힌 좌표 정렬, 사진 밖 자르기) | ✅ |
| C2 | 3,000개 초과 때 `over` 가 이전과 같이 온다 | ✅ |
| C3 | **YOLO 내보내기 값이 이전과 바이트까지 같다** | ✅ |
| C4 | 시험에 쓴 상자를 빈 목록으로 되돌리고, 파일은 지우지 않는다 | ✅ |
| D1 | `app/boxes.py` 외의 파일을 건드리지 않는다(ruflo 불변조건) | ✅ |

**24개 검사 전부 통과** — 📄 `stage1_boxes/verify_c2b.out` (종료코드 0).

## ② 한 줄 결론

D3 의 서버 절반(`"boxes": boxes` 를 저장 응답에 실기)과 ponytail 3건(`import time` 삭제·`clean()` 최상위로·`demo()` 가 실제 `clean()` 을 시험)을 넣었고, **저장·되읽기·`over`·YOLO 내보내기 값은 이전과 완전히 동일**함을 예전 코드/새 코드로 **같은 시험을 두 번 돌려** 확인했습니다. 화면 쪽 4줄은 다음 갈래 몫입니다.

## ③ 바꾼 것과 줄 수 변화

파일: `app/boxes.py` (백업 `app/_backup_260917_c2b_boxes.py`) 📄 **212줄 → 212줄** (47줄 추가 / 47줄 삭제, net 0)

| 무엇 | 자리 | 줄 변화 |
|---|---|---|
| **D3**: 저장 응답에 `"boxes": boxes` 추가 (왜 그러는지 주석 2줄) | `api_boxes_save()` 끝 `jsonify` | +3 |
| `import time` 삭제 (📄 `time.` 호출 0건) | 모듈 머리 | −1 |
| `clean()` 을 `register()` 안에서 **모듈 최상위**로 올림 (23줄 블록 이동, 상수 `CLASSES`·`MAX_BOXES`·`MIN_SIDE` 만 쓰므로 안전) | `L22` 부근 | +1 |
| `demo()` 가 규칙을 손으로 다시 적지 않고 **실제 `clean()`** 을 부르게 바꿈. 죽은 줄 `class C: pass`·`got, dropped = None, None` 삭제. 검사도 늘렸음(클래스 이름 보정·`id` 다시 붙이기·`src`·`dropped`·`over`·3,000개 상한) | `demo()` | −3 |
| `api_boxes()` 의 `(d or {})` 세 번 → 한 번 (3차 ⑤ 항목) | `api_boxes()` | ±0 |

`net: 0 lines.` 기능 코드는 줄었고(−4), 늘어난 3줄은 D3 필드와 그 주석, 나머지는 자체 점검이 **실제로 검증하게** 된 대가입니다. ❌ 줄 수가 안 줄어든 이유를 숨기지 않으려고 표로 나눴습니다.

### ③-1 일부러 **안** 건드린 것 — 3차 판정서 안의 모순 1건 (사람/3차 판단 필요)

3차 판정서가 `boxes.py:L157`(`CLASSES.index(b.get("cls","fruit")) if b.get("cls") in CLASSES else 0` → `CLASSES.index(b["cls"])`) 을 두 군데서 **서로 반대로** 지시합니다.

- ⑤·⑥-4: 「ponytail 중 `boxes.py` 항목만 깎기(… `L157`)」 → 깎아라
- 같은 문서 맨 끝줄: 「사람 결정 대기: **D1 클래스 번호** … 결정 전에는 `boxes.py:L18 CLASSES`·**`L157`** 을 손대지 않습니다」 → 손대지 마라

❌ **금지 쪽을 따랐습니다**(그 줄이 D1 (다)안에서 «대응표» 가 될 자리이고, 지금 깎으면 D1 결정 때 두 번 고쳐야 함). 동작에는 영향 없으니 D1 결정 뒤 사이클 4·5 에서 함께 처리하면 됩니다. → **3차가 어느 쪽인지 한 줄로 확정해 주세요.**

### ③-2 3차 제안을 «그대로» 쓰지 않은 곳 1건 (동작이 바뀌어서)

3차 ⑤ 는 `api_boxes()` 의 `saved` 를 `os.path.exists(box_path(...))` 로 바꾸라고 했습니다. ❌ 그러면 **동작이 바뀝니다**: `read_boxes()` 는 파일이 없을 때와 **JSON 이 깨졌을 때** 모두 `None` 을 주므로(📄 `boxes.py` `read_boxes()` 의 `except: return None`), 깨진 파일에서 지금은 `saved:false` 인데 `os.path.exists` 로는 `saved:true` + `boxes:[]` 가 됩니다 — 화면이 «저장된 빈 상자» 로 착각할 수 있습니다. 그래서 동작이 똑같은 꼴로만 줄였습니다: `saved, d = d is not None, d or {}` 한 줄 뒤 `d.get(...)` 세 번.

## ④ 실행 증거 (전부 실제로 돌린 것)

**방법**: 똑같은 시험을 ⑴ **고치기 전 돌고 있던 예전 코드**로 한 번(`before`), ⑵ 고치고 재시작한 뒤 한 번(`after`) 돌려 **응답·파일을 서로 비교**했습니다. 📄 스크립트 `stage1_boxes/probe.sh`, 비교 `stage1_boxes/verify_c2b.py`.

```
python3 app/boxes.py            -> "boxes.py 자체 점검 통과 (실제 clean() 을 시험했습니다)"  종료코드 0
python -m py_compile boxes.py   -> OK
bash app/run.sh restart         -> PID 2888468 -> 2898501, 원본 폴더 그대로
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
bash probe.sh before / after    -> 모든 요청 HTTP 200 (login 302)
python3 verify_c2b.py           -> 검사 24개 전부 [통과], 종료코드 0
```

시험 대상: `peach/210629-t4-17` (1248×1664). 이 stem 은 앞 갈래가 이미 «빈 목록» 으로 돌려 둔 시험용이라 남의 라벨을 덮어쓰지 않습니다. 📄 `stage1_boxes/_pristine/` 에 시작 상태를 떠 놓았습니다.

**⑴ 저장 응답 (5개 보냄: 정상 3 + 1픽셀 1 + 좌우 뒤집힘 1)**

| | 예전 코드 | 새 코드 |
|---|---|---|
| 응답 | `{ok, n_boxes:4, dropped:1, over:0, at}` | `{ok, n_boxes:4, dropped:1, over:0, at, **boxes:[4개]**}` |
| `boxes` 열쇠 | 없음 | 있음 (길이 4 = `n_boxes`) |
| 크기 | 📄 72 바이트 | 📄 330 바이트 |

- 📄 `dropped:1` — 1픽셀 상자 `[500,500,501,501]` 가 `MIN_SIDE` 로 버려짐(예전과 같음).
- 📄 뒤집어 보낸 `[700,900,650,850]` → `[650,850,700,900]` 로 정렬(예전과 같음).
- 📄 사진 밖 `[1200,1600,1260,1700]` → `[1200,1600,1248,1664]` 로 잘림(예전과 같음).

**⑵ A4 — 응답 `boxes` 와 되읽기가 같은가** (D3 의 핵심: 화면이 이걸로 덮어써도 파일과 안 갈림)

📄 `resp_save_after.json["boxes"] == resp_get_after.json["boxes"]` **완전 일치**. 값:
`[{id:1,cls:fruit,src:human,xyxy:[100,200,300,400]}, {id:2,cls:bunch,…[10,10,60,80]}, {id:3,cls:other,…[1200,1600,1248,1664]}, {id:4,cls:fruit,…[650,850,700,900]}]`
그리고 되읽기 결과 자체가 **예전 코드와 동일**(`boxes`·`width`·`height`·`saved`·`classes` 전부).

**⑶ C2 — 3,000개 초과**

📄 3,005개 보냄 → 예전 `{n_boxes:3000, dropped:0, over:5}` / 새 코드 `{n_boxes:3000, dropped:0, over:5}` + `boxes` 3,000개(`id` 1…3000).
📄 이때 응답 크기 **195,977 바이트(191KB)** — 3차 판정서의 «3,000개여도 200KB 정도» 추정이 실측과 맞습니다.

**⑷ C3 — YOLO 내보내기 값** (가장 중요한 «안 바뀜» 증거)

📄 `yolo_before.txt` 와 `yolo_after.txt` **바이트까지 동일**:
```
0 0.160256 0.180288 0.160256 0.120192
1 0.028045 0.027043 0.040064 0.042067
2 0.980769 0.980769 0.038462 0.038462
0 0.540865 0.525841 0.040064 0.030048
```
📄 내보내기 응답도 동일(`n_images:1, n_boxes:4`), `boxes_all.json` 도 `at`·`by`(시험 흔적) 빼고 동일.

**⑸ C4 — 되돌리기**

📄 빈 목록 저장 → `{n_boxes:0, boxes:[]}` → 다시 내보내기 → `boxes_yolo/210629-t4-17.txt` 0바이트, `boxes_all.json` `n_boxes:0, n_images:1`(시작 상태와 같음). 파일은 **지우지 않았습니다**. 시작 파일과 `stem`·`fruit`·`width`·`height`·`boxes` 가 같고 `by`·`at` 만 시험 흔적으로 남습니다. 📄 `grape` 쪽은 md5 그대로(건드리지 않음).

**⑹ 시험한 것 / 안 한 것** (3차 ⑥-5 의 의무 표, 서버 쪽)

| 시험한 것 | 안 한 것 (다음 갈래·다음 사이클) |
|---|---|
| 저장(5개·3,005개·빈 목록), 되읽기, YOLO 내보내기, 1픽셀 버림, 좌우 뒤집힘 정렬, 사진 밖 자르기, 모르는 클래스 보정, `id` 다시 붙이기, `over` 세기, 3,000개 응답 크기 | **실제 브라우저 화면**(`saveBoxes` 반영·Ctrl+Z·flash 문구) — 내 파일이 아님. `/api/boxes_seed`(초벌) 은 손대지 않아 시험 안 함. 동시에 두 사람이 같은 stem 을 저장하는 경합. D2(`dpr` 불일치) 브라우저 실측. |

⚠️ 정직하게 남기는 주의 1건: 내가 `bash app/run.sh restart` 를 한 14:39 시점에 📄 `app/instances.py` 의 mtime 도 14:39 였습니다(다른 작업자가 그 순간 편집 중). 서버는 정상 기동(health 200)했지만, **열매 번호 담당은 자기 변경이 반영됐는지 스스로 다시 확인**해 주세요. 서버는 켜 둔 채 넘깁니다(PID 2898501).

## ⑤ 화면 쪽(다음 갈래)이 해야 할 일 — 넘기는 지시

서버는 이제 저장 응답에 **정리된 최종 목록**을 줍니다. `app/static/app.js` `saveBoxes()` 를 3차 판정 ③ 대로 고쳐 주세요(내 파일이 아니라 손대지 않았습니다):

1. 보내기 **전에** `const stem = S.stem` 을 붙잡고, 응답이 온 뒤 `S.stem !== stem` 이면(저장 중 사진을 바꿨을 때) 화면을 **건드리지 말고** flash 만 띄운다.
2. `j.dropped || j.over` 일 때**만** `bpush()` — 사라진 것을 Ctrl+Z 로 볼 수 있게.
3. 그다음 순서대로: `S.boxes = j.boxes; S.bsel = -1; S.bDirty = false;` — `bpush()` 가 `bDirty` 를 올리므로 **반드시 그 뒤에** 내린다.
4. `boxInfo` 문구를 「저장됨 … · 너무 작아 버린 것 N — 화면에서도 지웠음(Ctrl+Z 로 되돌려 볼 수 있음)」, `dropped||over` 면 `flash(..., true)` 경고색.
5. `S.dirty = true` 로 다시 그린다.
6. ❌ 실측 참고: `j.boxes` 는 상자 3,000개일 때 **191KB**(4개면 330바이트)입니다. 그대로 대입하면 되고 따로 아낄 필요 없습니다. `j.boxes` 의 각 항목은 `{id, cls, xyxy, src}` 이고 `id` 는 **1부터 다시 붙습니다** — 화면이 들고 있던 `id` 와 달라질 수 있으니 `S.bsel` 은 위처럼 `-1` 로 초기화하는 것이 맞습니다.
7. ⚠️ 방어적으로 `if (Array.isArray(j.boxes))` 로 감싸 주세요 — 예전 서버(재시작 전)는 `boxes` 를 주지 않으므로 `undefined` 대입 사고를 막습니다.

**내가 못 한 숙제 2건**(내 파일이 아니라서 — 3차 ③ 이 요구한 것):
- `cycles/260917_신기능/cycle_1/stage1/test_clean.py` 에 「2픽셀 미만 2개 섞은 5개 POST → 응답 `boxes` 길이 3」 한 줄 추가 → ❌ 내 담당 파일(`boxes.py`)이 아니어서 안 했습니다. 다만 같은 내용을 **살아 있는 서버로** 확인해 뒀습니다(④⑴, 5개 중 1픽셀 1개 → 응답 `boxes` 길이 4).
- `saveBoxes` 를 `new Function` 으로 떼어 내 «저장 뒤 `S.boxes.length===3`, `S.bDirty===false`, `S.bundo.length===1`» 확인 → 화면 갈래가 해 주세요.

## ⑥ 2차 검수가 재현할 절차

```bash
cd /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
D=cycles/260917_신기능/cycle_2/stage1_boxes

# 1) 내가 바꾼 것 전부 보기 (212줄 -> 212줄)
diff -u app/_backup_260917_c2b_boxes.py app/boxes.py

# 2) 자체 점검이 «실제 clean()» 을 시험하는지 (일부러 틀리게 고쳐 보면 터집니다)
cd app && python3 boxes.py; cd ..          # -> 자체 점검 통과, 종료코드 0
grep -n "^def clean" app/boxes.py          # -> 최상위에 있음
grep -n "import time" app/boxes.py         # -> 없음
grep -n '"boxes": boxes' app/boxes.py      # -> 저장 응답에 있음

# 3) 살아 있는 서버로 다시 시험 (재시작은 필요할 때만!)
bash $D/probe.sh after                     # 응답·YOLO 를 $D 에 다시 씀
python3 $D/verify_c2b.py $D                # -> 검사 24개 전부 [통과], 종료코드 0

# 4) 예전 코드와 비교하고 싶으면
#    app/_backup_260917_c2b_boxes.py 를 app/boxes.py 로 되돌리고 restart 뒤
#    bash $D/probe.sh before  --> yolo_before.txt / yolo_after.txt 가 같아야 함
diff $D/yolo_before.txt $D/yolo_after.txt  # -> 차이 없음
```

- 남긴 증거: `verify_c2b.out`(검사 24개 결과), `resp_save_{before,after}.json`, `resp_get_{before,after}.json`, `resp_big_{before,after}.json`, `yolo_{before,after}.txt`, `all_{before,after}.json`, `restart_after.log`, `_pristine/`(시작 상태).
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
- 확인해 주면 좋을 것: ③-1 의 `L157` 모순(깎을까 / D1 결정까지 둘까), ③-2 의 `saved` 판단(깨진 파일에서 `saved:false` 를 지킨 것).
