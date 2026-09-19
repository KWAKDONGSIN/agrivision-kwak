작성: 2026-09-18

# 사이클 4 — **3차 판정 전 소수정**(2차 판정자 본인 · Opus 5)

대상: 2차 `cycle_4/stage2_review.md` §4(즉시 수정 3 · 3차로 넘긴 8) · 1차 `cycle_4/stage1_work.md` ·
총괄(Fable) 결정 6항목. **총괄이 채택한 것만** 최소로 고쳤습니다.

작업 시각(실측 `date`): **2026-09-18 21:55 ~ 23:05**(회귀 22:12~22:55 · 다시 돌린 것 22:56~23:01) · 내 모래상자 **7011**(새 시험) ·
보안 관련 값·설정 세부는 공개본에서 생략했습니다.

🔴 **실서버 5111(PID 1908658)** 에는 **접속 0건**입니다 — `/api/health` 조차 부르지 않았고, 재시작·로그인·쓰기
모두 하지 않았습니다. 공용 `T/data`·`T/exports` **무변경**(쓰기는 모래상자 안 `sandbox/data`·`sandbox/exports` 만) ·
`t5_shots.py`·`t3_helpfig.py`·`s5_live_guard part_b` **안 돌림** · 삭제·GPU·새 패키지 **없음** ·
남의 프로세스(5100·5101·5105) **손대지 않음** · `작업기록.md` **갱신하지 않음**(지시대로).

---

## 0. 한 장 요약

| 총괄 결정 | 무엇을 했나 | 고치기 전 → 고친 뒤 |
|---|---|---|
| **1. 되돌리기와 확정** | 되돌리기가 성공하면 **그 종류의 `confirmed_<kind>` 를 지운다**. 세 종류가 **함수 하나**(`server.clear_confirm`)를 쓴다. 응답에 `confirmed_cleared` · 화면은 «확정이 풀렸습니다 — 다시 확정하세요» 를 **1초 힌트**로 | `c1_revert` **16/7 → 23/0** |
| **2. 상자 파일 없어도 «나갈 상자»** | `n_confirmed_boxes_out` 을 **`box_set(fruit)` 과 교집합**으로. 화면 숫자 = 실제 txt 수 | `c2_boxout` **8/5 → 13/0** |
| **3. N8 주석 근거** | 주석 문장만 실측에 맞게 고침(**코드 무변경**) | 동작 그대로 |
| **4. `runall.sh` 위생** | `t3_chars` 호출 추가 · `mk_reg_c4*.py` 가 `cp -a` 뒤 옛 `*.log`·`*_AFTER*.json` 을 사본 안에서만 지움 | 사본에 남의 로그 0 |
| **5. `t2_queue` 두 번 돌리기** | 시험 시작 때 앞 판이 남긴 `masks_fixed/` 잔재를 치우는 `setup`(시험 코드·모래상자 안) | **42/1 → 43/0** (두 번 돌려도) |
| **6. 사이클 5 로 넘긴 것** | «목록에 지금 무슨 작업인지»·«확정 뒤 카드 옛 그림»·«빈 날짜 폴더» — **손대지 않았습니다** | — |

**회귀: 새로 깨진 것 0개.** 다만 결정 1 이 «되돌려도 확정은 남는다» 는 옛 약속을 뒤집었으므로
**옛 시험 3자리의 기대값을 갱신**했습니다(§7-2 · 갱신 뒤 옛 숫자 그대로 79/0 · 77/0 · 9/0).

**고친 파일 13개**(서버 파이썬 2 · 정적 1 · 시험·도구 5 · 기대값 갱신 5). 백업은 모두 같은 폴더에 `_backup_260918_c4c_<파일명>`.

---

## 1. 결정 1 — 되돌리면 그 종류의 확정을 지운다

### 1-1. 왜 (다)가 아니라 «지우기» 인가 — 실측한 거짓말

고치기 전, 복숭아 `210629-t1-02` 를 «AI 로 교체»(수정본 생성) → «수정함» 으로 확정 → 되돌리기 한 뒤
같은 조건(«사람 확정만»)으로 **실제로 내보낸** manifest 한 줄입니다.

| 언제 | 포함여부 | status | mask_source | confirmed_status | source |
|---|---|---|---|---|---|
| 확정 직후 | 포함 | fixed | `masks_fixed` | fixed | human |
| **되돌린 뒤 (고치기 전)** | **포함** | unreviewed | **원본** | **fixed** | **human** |
| 되돌린 뒤 (고친 뒤) | 제외 | unreviewed | (없음) | (없음) | ai |

가운데 줄이 문제입니다 — manifest 는 «사람이 고쳐 확정한 것»(`human` · `fixed`)이라고 적는데 실제로 나간
파일은 **원본**입니다. 2차 권고 (다)(`note` 에 «되돌림» 덧붙이기)는 그 줄을 **그대로 두기** 때문에,
나중에 «사람이 손댄 장» 을 세면 여전히 틀립니다. 그래서 총괄 결정대로 확정을 **지웁니다.**

### 1-2. diff — `app/server.py`

새 함수 하나(`confirm_status()` 바로 아래 · **쓰는 곳은 여기 한 곳**):

```python
+def clear_confirm(fruit, stem, kind):
+    """**되돌리기가 성공하면 그 종류의 사람 확정을 지운다** — 쓰는 곳은 여기 하나뿐이다.
+    …(왜 «note 덧붙이기» 가 아니라 «지우기» 인가 · 사람은 Enter 로 다시 확정 · 화면 1초 힌트)…
+    돌려주는 것: (지운 종류 or None, 지금 status 항목)"""
+    key = CONFIRM_KINDS.get(kind)
+    with lock_for("status:" + fruit):
+        d = read_status(fruit)
+        rec = d.get(stem) or {}
+        if not key or key not in rec:
+            return None, rec                   # 원래 확정이 없었다 → 아무것도 바꾸지 않는다
+        rec.pop(key, None)
+        d[stem] = rec
+        write_status(fruit, d)
+        return kind, rec
```

`/api/revert`(마스크) — 자물쇠 안, **두 번의 status 쓰기 뒤**에:

```python
         if prev:
             st = write_status_entry(fruit, stem, {k: v for k, v in st.items() if k != "prev"})
+        cleared, st = clear_confirm(fruit, stem, "mask")
-    return jsonify({"ok": True, "removed": removed, "restored": bool(prev), "status": st})
+    return jsonify({"ok": True, "removed": removed, "restored": bool(prev), "status": st,
+                    "confirmed_cleared": cleared})
```

`_instances.register(app, {…})` 의 ctx 에 한 줄:

```python
+    "clear_confirm": clear_confirm,
```

### 1-3. diff — `app/instances.py` (`/api/revert_instances`)

```python
             st.pop("prev", None)
             st = ctx["write_status_entry"](fruit, stem, st)
+            cleared, st = ctx["clear_confirm"](fruit, stem, "instances")
         return jsonify({"ok": True, "removed": removed, "changed": True,
-                        "restored": bool(prev), "status": st})
+                        "restored": bool(prev), "status": st, "confirmed_cleared": cleared})
```

«되돌릴 것이 아무것도 없으면» 먼저 `changed: False` 로 돌아가는 옛 갈래는 **건드리지 않았습니다** —
되돌리기가 «성공» 한 것이 아니므로 확정을 지울 이유가 없습니다.

### 1-4. diff — `app/static/app.js` (화면 · 1초 힌트)

```js
+function clearTaskConfirmed(kind) {
+  const ik = kind === "boxes" ? "confirmed_boxes"
+           : kind === "instances" ? "confirmed_instances" : "confirmed";
+  if (S.item && S.item.stem === S.stem) S.item[ik] = null;
+  const it = S.items.find((x) => x.stem === S.stem);
+  if (it) it[ik] = null;
+  flash("확정이 풀렸습니다 — 다시 확정하세요");
+  clearTimeout(flash._t); flash._t = setTimeout(() => { $("#saveflash").textContent = ""; }, 1000);
+}
```

`#btn-revert`(마스크)와 `revertInstances()`(번호) 에 각각 한 줄:

```js
+  if (j.confirmed_cleared) clearTaskConfirmed(j.confirmed_cleared);   // 총괄 결정 1
```

- **1초 힌트는 이미 있는 장치를 그대로 씁니다** — `#saveflash` + `flash._t` 를 1000ms 로 줄이는 방식은
  `app.js` 가 «사진 밖입니다» 힌트에 쓰는 것과 **같은 두 줄**입니다(새 DOM·CSS 0).
- 목록 카드의 칸(`confirmed`·`confirmed_boxes`·`confirmed_instances`)도 같이 비웁니다 —
  2차가 고친 `renderGrid()` 가 그 칸으로 테두리 색·판정 딱지를 그리기 때문입니다. 비우지 않으면
  화면이 서버와 어긋나 «확정» 이라고 계속 적혀 있습니다.
- `ui.js` 는 **한 글자도 고치지 않았습니다**(2차의 교훈: `app.js` 에서 `ui.js` 함수를 부르지 않는다).

### 1-5. 시험 — `cycle_4/stage2c/c1_revert.py` (**16/7 → 23/0**)

| 항목 | 고치기 전 | 고친 뒤 |
|---|---|---|
| [가]-6 `/api/revert` 응답에 `confirmed_cleared="mask"` | **FAIL** (칸 없음) | **ok** `"mask"` |
| [가]-8 마스크 확정이 지워졌다 | **FAIL** `{"status":"fixed","by":"곽동신"}` | **ok** `None` |
| [가]-9 «사람 확정만» 내보내기에서 빠진다 | **FAIL** 나감(`['210629-t1-02']`) | **ok** 안 나감(`[]` · n_images 1 → 0) |
| [나]-5 `/api/revert_instances` 응답에 `confirmed_cleared="instances"` | **FAIL** | **ok** `"instances"` |
| [나]-7 번호 확정이 지워졌다 | **FAIL** `fixed` 그대로 | **ok** `None` |
| [나]-8 **마스크 확정은 그대로**(칸이 서로 독립) | ok | **ok** (`{"status":"ok"}` 남음) |
| [다]-3 같은 함수를 `kind="boxes"` 로 부르면 `"boxes"` | **FAIL** (`clear_confirm` 없음) | **ok** |
| [다]-4 상자 확정이 지워졌다 | **FAIL** | **ok** |
| 묶음 전체 | **통과 16 / 실패 7** | **통과 23 / 실패 0** |

- **상자 되돌리기 주소는 없습니다** — `/api/revert_boxes` 는 **404**(실측 [다]-1). `boxes.py` 에도
  되돌리기 경로가 없습니다(라우트 5개 전수 확인). 그래서 «상자를 되돌렸는데 확정이 남는» 길은 **지금 없고**,
  함수는 `kind="boxes"` 를 이미 받습니다(위 [다]-3 은 `server.clear_confirm(…, "boxes")` 를 직접 불러 확인).
  나중에 상자 되돌리기가 생기면 **그 한 줄만** 부르면 됩니다.
- 되돌리기가 원래 하던 일(파일 삭제 · `prev` 로 판정·메모 되살리기)은 그대로입니다 —
  [나]-4 응답 `restored: true` · `removed: ["instances_fixed","masks_fixed"]`.

---

## 2. 결정 2 — 상자 파일이 없으면 «나갈 상자» 로 세지 않는다

### 2-1. diff — `app/server.py` `export_caps()`

```python
+    bset = box_set(fruit)
+    n_box_out = 0
     for s in stems:
         …
         vb = confirmed_of(st.get(s), "boxes")
         cb[vb["status"] if vb else "unreviewed"] += 1
+        if vb and vb["status"] in ("ok", "fixed") and s in bset:
+            n_box_out += 1
…
-            "n_confirmed_boxes_out": cb["ok"] + cb["fixed"],
+            "n_confirmed_boxes_out": n_box_out,
```

- `box_set(fruit)` 은 **이미 있는 함수**(0918 사이클4 · 폴더를 한 번 훑어 상자 파일이 있는 stem 집합).
  장마다 `stat` 하지 않으므로 목록 성능 규칙(2차 §3-3)을 깨지 않습니다.
- 바꾼 것은 **«나갈» 쪽 칸 하나**(`n_confirmed_boxes_out`)입니다. 사람이 누른 확정 자체를 세는
  `n_confirmed_boxes`(`/api/fruits` 의 «확정 장수»)는 **그대로** 둡니다 — 사람이 누른 판정을 코드가
  지우지 않는다는 방향 문서 §5 와 어긋나지 않게.
- 화면·확인창·목록이 전부 이 한 숫자를 씁니다(`ui.js` 996·1008·1060행) → **정적 파일 수정 0**.
  그래서 화면의 «지금 확정된 사진 … 상자 N장» 줄도 같이 진실해집니다 — 그 줄은 세그·번호도
  이미 `_out`(ok·fixed 만)을 쓰므로 «실제로 나갈 수 있는 것» 이라는 뜻이 세 종류에서 같아집니다.

### 2-2. 시험 — `cycle_4/stage2c/c2_boxout.py` (**8/5 → 13/0**)

복숭아에는 상자 파일이 **한 장**(`210629-t4-17.json`)뿐입니다.

| 상황 | 항목 | 고치기 전 | 고친 뒤 | 실제 txt |
|---|---|---|---|---|
| 상자 **파일이 없는** 사진만 확정 | «나갈 상자» | **1** (FAIL) | **0** | **0** |
| 〃 | 화면 숫자 = txt 수 | **FAIL** (화면 1 · txt 0) | **ok** (0 = 0) | — |
| 파일 있는 사진까지 확정(2장) | «나갈 상자» | **2** (FAIL) | **1** | **1** |
| 〃 | 화면 숫자 = txt 수 | **FAIL** (화면 2 · txt 1) | **ok** (1 = 1) | — |
| 〃 | «지금 확정된 사진»(안 바뀌어야 함) | 2 | **2** | — |
| 〃 | `n_box_images`(저장된 전부) | 1 | **1** | — |
| `/api/export_list` 의 같은 숫자 | | **2** (FAIL) | **1** | — |
| 묶음 전체 | | **통과 8 / 실패 5** | **통과 13 / 실패 0** | |

---

## 3. 결정 3 — N8 주석의 근거 문장 (코드 무변경)

`app/server.py` `api_status()` 의 «⚠ 여기에서만 막는다» 문단만 고쳤습니다. 동작·기대값·시험 **무변경**.

- 지운 문장: «/api/save·/api/save_instances 는 AI 검수 스크립트가 **실제로** «AI 3회 검수» 라는 이름으로
  판정을 써 넣는 길이라, 거기서 막으면 그 도구가 죽는다» — **실측과 다릅니다.**
- 새로 적은 근거: `status.json` 의 «AI 3회 검수(…)» **990행**(사과 623·포도 180·복숭아 102·블루베리 85)은
  **HTTP 가 아니라 파일로 직접** 쓰인 것이고(`T/scripts`·`inspect`·`ai_pass`·`export`·`final` 어디에도
  `/api/save` 호출이 없음), 그 이름으로 `/api/save` 를 부르는 것은 **우리 시험 스크립트뿐**입니다.
  그래도 여기만 막는 이유 둘 — ① 사람이 그 길로 갈 수 있는 자리는 «이름 칸» 하나뿐이고 그것이 이 주소다
  ② 두 주소까지 막으면 **우리 회귀 시험 10여 개가 죽는데 동작 이득은 0** 이다.

---

## 4. 결정 4 — `runall.sh` 위생

### 4-1. `cycle_4/stage1/runall.sh` — `t3_chars` 호출 추가

```bash
 $PY -u regress_all.py > regress_all.log 2>&1; echo "regress_all rc=$?"
+$PY -u t3_chars.py    > t3_chars.log    2>&1; echo "t3_chars rc=$?"
…
-for f in t1_api t2_ui regress_all; do
+for f in t1_api t2_ui regress_all t3_chars; do
```

이제 «1차 명령을 그대로» 따라 해도 **글자 예산이 다시 재집니다**(전에는 `final_check.sh` 에만 있었습니다).

### 4-2. `mk_reg_c4.py`·`mk_reg_c4b.py` — `cp -a` 뒤 옛 로그 치우기 (**사본 안에서만**)

```python
     for d, dirs, fns in os.walk(DST):          # DST = 내가 방금 만든 사본 폴더
         …
         for fn in fns:
-            if fn.endswith(".pid"):
+            if fn.endswith(".pid") or fn.endswith(".log") or \
+                    (fn.endswith(".json") and "_AFTER" in fn):
                 os.remove(os.path.join(d, fn))
+                n_old += 1
+    print("옛 로그·산출물 지움(사본 안에서만): %d개" % n_old)
```

- 지우는 것은 **`DST`(사본) 안**뿐입니다 — 원본 폴더(`cycle_2/stage2b`·`cycle_3/stage2c/rep2`)와
  공용 폴더는 손대지 않습니다.
- `.json` 은 **`*_AFTER*.json` 만** 지웁니다(총괄 결정). 기대값·결과 json(`t1_api.json` 등)은 이름이
  달라 남습니다 — 통째로 지우면 시험이 읽는 기대값이 사라질 수 있습니다.

---

## 5. 결정 5 — `t2_queue` 를 두 번 돌려도 같은 숫자

`t2_queue.py` 의 `main()` 에서 `L.reset_status()` 바로 뒤에 `setup` 을 넣었습니다(**시험 코드** ·
쓰는 곳은 **모래상자 안**뿐). 하드코딩한 사진 이름을 쓰지 않고 «공용 `T/data` 에 **없는** 수정본만» 지웁니다 —
`T/data/apple/masks_fixed` 는 실측 **0개**이므로, 앞 판이 만든 잔재만 정확히 없어집니다.

```python
     L.reset_status()
+    _fx, _src = L.SB + "/data/apple/masks_fixed", L.T + "/data/apple/masks_fixed"
+    _keep = set(os.listdir(_src)) if os.path.isdir(_src) else set()
+    for _n in sorted((set(os.listdir(_fx)) - _keep) if os.path.isdir(_fx) else ()):
+        os.remove(os.path.join(_fx, _n))
+        print("[setup] 앞 판 잔재 지움: masks_fixed/" + _n, flush=True)
     p = L.start()
```

고친 파일 **둘**(내용이 한 글자도 다르지 않게 유지): `cycle_2/stage1/t2_queue.py`(원본) ·
`cycle_2/stage2b/reg_s1/t2_queue.py`(회귀 사본들이 이것을 복사해 갑니다 — 그래서 여기를 고쳐야
사이클 4·5 의 사본이 낫습니다).

---

## 6. 결정 6 — 손대지 않은 것

2차가 3차로 넘긴 8개 중 **3개는 사이클 5 로** 넘어갔고, 저는 **한 글자도 고치지 않았습니다**:
③ «목록 화면에 지금 무슨 작업인지가 없다» · ④ «확정한 사진은 목록에 돌아와도 카드가 옛 그림» ·
⑦ «상자만·확정만·0장에서 저장하면 빈 날짜 폴더». ⑦ 의 가드는 2차가 한 번 넣었다가 사이클 3 2차의
결정(`a5b_ui` 화면-4-A «상자만 골라도 저장이 된다»)을 깨서 되돌린 자리입니다 — 그대로 둡니다.

---

## 7. 회귀

1차·2차의 로그는 **한 글자도 덮어쓰지 않았습니다** — 포트·모래상자·스크린샷 폴더만 바꾼 사본으로
돌렸습니다(`mk_rep_c.py` → `rep/`(73xx·77xx~79xx) · `mk_rep2_c.py` → `rep2/`(74xx)).
한 번에 돌리는 것은 `runall_c4c.sh`(22:12~22:55) · 다시 돌린 것은 `rerun_c4c.sh`(22:56~23:01).

### 7-1. 숫자 — 전부 전과 같습니다(기대값을 바꾼 3자리 제외)

| 묶음 | 1차·2차가 적은 것 | 내 판 | 판정 |
|---|---|---|---|
| 사이클4 `t1_api` | 34 / 0 | **34 / 0** | 같음 |
| 사이클4 `t2_ui`(진짜 파이어폭스) | 27 / 0 (경고 1) | **27 / 0** (경고 1) | 같음 |
| 사이클4 `regress_all`(네 과일 × 세 작업 × 아홉 조작) | 99 / 0 (해당없음 9) | **99 / 0** (해당없음 9) | 같음 |
| 사이클4 `t3_chars`(글자 예산) | 2 / 0 | **2 / 0** | 같음 (이제 `runall.sh` 가 부른다) |
| 시뮬 `sim.js`·`modesim.js`·`boxsim.js`·`boxes.py` | 통과 · 31/31 · 50/50 · 통과 | **같음** | 같음 |
| 문법 `py_compile` 6 · `node --check` 2 | OK | **OK** | 같음 |
| 사이클2 1차 `t1_api` | 79 / 0 | 78/1 → **79 / 0** | **기대값 1칸 갱신**(§7-2) |
| 사이클2 1차 `t2_queue` | 43/0 (**2판은 42/1**) | **43/0 · 2판 43/0 · 3판 43/0** | **좋아짐**(결정 5) |
| 사이클2 1차 `t3_conc` · `t4_paint8` | 8/0 · 22/0 | **8/0 · 22/0** | 같음 |
| 사이클1 `t1_measure`(after) · `t3_matrix` · `t4_keys` | 155/0 · 84/0 · 25/0 | **155/0 · 84/0 · 25/0** | 같음 |
| 사이클1 `t6_view` | 126 / 4 | **126 / 4** | 같음(전부터) |
| 사이클1 `t2_reg` | 11 / 0 | 10/1 → **11 / 0** | **속도 흔들림**(§7-3) |
| 사이클2 2차 `s1_api` | 77 / 0 | 76/1 → **77 / 0** | **기대값 1칸 갱신**(§7-2) |
| 사이클2 2차 `s2_scenario` · `s3_guards` | 20/0 · 18/0 | **20/0 · 18/0** | 같음 |
| 사이클2 2차 `s4_paint8` · `s5_live_guard`(a+c) | 21/1 · 12/1 | **21/1 · 12/1** | 같음(전부터) |
| 사이클2 2차 `s6_layout` · `s7_clip` · `s8_guard_advance` | 7/0 · 2/0 · 3/0 | **7/0 · 2/0 · 3/0** | 같음 |
| 사이클1 2차 `s5_fix`(after) | 9 / 0 | **9 / 0** | 같음 |
| 사이클3 2차 `a1_sem`·`a2b_loss`·`a3_conc`·`a4_input`·`a5b_ui`·`a5c_errrow`·`a6_reg`·`a7_equiv` | 16/0 · 7/0 · 17/0 · 62/0 · 7/0 · 3/0 · 9/2 · 11/0 | **전부 같음** | 같음(`a6_reg` 2는 전부터) |
| 사이클3 2차 `a5_ui` | (1차도 `getBoundingClientRect ... null` 로 죽음) | **같은 자리·같은 오류** | 같음(전부터) |
| 사이클3 1차 `t1_api` · `t2_ui` | 79/0 · 24/0 | **79/0 · 24/0** | 같음 |
| 2차 `s1_flow` | 26 / 0 (경고 1) | **26 / 0** (경고 1) | 같음 |
| 2차 `s2_rest c`(다) | 9 / 0 | 8/1 → **9 / 0** | **기대값 1칸 갱신**(§7-2) |
| 2차 `s2_rest d`(라) | 표는 5/0(경고2) · **2차 자신의 로그는 5/1** | **5 / 1** (경고 2) | 2차 로그와 같음(§7-4) |
| 2차 `s2_rest e`(마) · `s5_card` · `s6_drag` | 1/0 · 2/0 · 2/0 | **1/0 · 2/0 · 2/0** | 같음 |
| **새로 만든** `c1_revert` | — | **16/7 → 23/0** | 결정 1 |
| **새로 만든** `c2_boxout` | — | **8/5 → 13/0** | 결정 2 |

**새로 깨진 것 0개.** 남아 있는 실패 칸(`t6_view` 4 · `s4_paint8` 1 · `s5_live_guard` 1 · `a6_reg` 2 ·
`a5_ui` 죽음 · `s2_rest d` 1)은 전부 이 소수정 **전부터** 있던 것이고 1차·2차 로그와 숫자가 같습니다.

### 7-2. 🔴 기대값을 바꾼 3자리 — 총괄 결정 1 이 **옛 약속을 뒤집었기 때문**입니다

세 시험이 «되돌려도 사람 확정은 **남는다**» 를 못박아 두고 있었습니다. 총괄 결정 1 이 바로 그것을
뒤집었으므로, 기대값을 고치지 않으면 «고친 것이 실패로 보이는» 상태가 됩니다. 사이클 3 2차가
`a5b_ui` 에서 했던 것과 같은 방식으로, **무엇을 왜 바꿨는지 시험 코드 안에 주석으로 남겼습니다.**

| 시험 | 옛 기대값 | 새 기대값 | 갱신한 파일 |
|---|---|---|---|
| 사이클2 1차 `t1_api` N-A | «`confirmed` 칸이 되돌리기로 바뀌지 않는다» | «되돌리기가 마스크 확정을 지운다» + `confirmed_cleared` 확인 | `cycle_2/stage1/t1_api.py` · `cycle_2/stage2b/reg_s1/t1_api.py` |
| 사이클2 2차 `s1_api` 가-N-A | «confirmed 그대로» | «되돌리기가 마스크 확정을 지운다» | `cycle_2/stage2/s1_api.py` · `cycle_2/stage2b/reg_s2/s1_api.py` |
| 2차 `s2_rest` 다-8 | «되돌려도 사람 확정은 남는다(제외 그대로)» | «되돌리면 사람 확정이 풀린다» | `cycle_4/stage2/s2_rest.py` |

- 두 벌씩 고친 이유: `cycle_2/stage1`(원본)과 `cycle_2/stage2b/reg_s1`·`reg_s2`(**회귀 사본들이
  복사해 가는 자리** — `mk_reg_c4.py` 의 `SRC`)를 같이 맞춰야 다음 사이클 사본도 낫습니다.
  두 벌은 포트 말고는 한 글자도 다르지 않음을 `diff` 로 확인했습니다.
- `cycle_2/stage2/reg_c2s1/t1_api.py` 는 사이클2 가 남긴 **실행 사본**(아무도 복사해 가지 않음)이라
  근거 보존용으로 **그대로 두었습니다.**
- 갱신 뒤 숫자: `t1_api` **79/0** · `s1_api` **77/0** · `s2_rest c` **9/0** — 셋 다 옛 숫자로 돌아왔습니다.

### 7-3. `t2_reg` 10/1 은 **속도 흔들림**이었습니다

실패한 칸은 `live_c5.py` 의 «블루베리 (144)\_121 초벌 5회 전부 **0.5초 미만**» — 순전히 시간 재기입니다.
제 코드는 초벌·마스크 읽기를 한 글자도 고치지 않았고, 그때 같은 기계에서 파이어폭스 묶음이 동시에
돌고 있었습니다. **부하가 없을 때 다시 재니 11 / 0** 입니다(`t2_run_rerun.log`).

### 7-4. `s2_rest d` 1 실패는 **2차 자신의 로그에도 있습니다**

2차 보고서 §2 표는 «`s2_rest d` 5 / 0(경고 2)» 라고 적었지만, 2차가 남긴 로그
`stage2/s2_rest_d_AFTER.log` 는 **«통과 5 / 실패 1 / 경고 2»** 이고 실패 칸은
«라-3 과일을 바꾸면 그 과일의 붓 크기다 | 포도 55 · 사과 55» 입니다. 제 판도 **같은 칸·같은 값**입니다.
이것은 2차가 §3-6 에서 «결함으로 보지 않는다» 고 판정한 바로 그 동작(값이 없는 과일은 마지막 값을
물려받는다)이라 손대지 않았습니다 — **2차 보고서 표의 오기**로 보시면 됩니다(3차가 표를 고칠 자리).

---

## 8. 고친 파일 · 만든 파일

### 8-1. 고친 파일 8개 (백업은 모두 같은 폴더 `_backup_260918_c4c_<파일명>`)

| 파일 | 늘어난 줄 | 줄어든 줄 | 지금 줄 수 | 무엇 |
|---|---|---|---|---|
| `app/server.py` | +52 | −4 | 1,959 | 결정 1(새 함수·revert·ctx) · 2(export_caps) · 3(주석) |
| `app/instances.py` | +5 | −1 | 563 | 결정 1(번호 되돌리기) |
| `app/static/app.js` | +16 | −0 | 2,481 | 결정 1(화면 칸 비우기 · 1초 힌트) |
| `cycles/260918_paint/cycle_4/stage1/runall.sh` | +4 | −1 | 65 | 결정 4-1 |
| 〃 `stage1/mk_reg_c4.py` | +9 | −1 | 84 | 결정 4-2 |
| 〃 `stage1/mk_reg_c4b.py` | +9 | −0 | 68 | 결정 4-2 |
| `cycles/260918_paint/cycle_2/stage1/t2_queue.py` | +9 | −0 | 321 | 결정 5 |
| 〃 `cycle_2/stage2b/reg_s1/t2_queue.py` | +9 | −0 | 321 | 결정 5 (위와 동일 내용) |

**기대값을 갱신한 시험 5개**(§7-2 · 결정 1 이 옛 약속을 뒤집었기 때문 · 백업 규칙 같음):

| 파일 | 늘어난 줄 | 줄어든 줄 | 지금 줄 수 |
|---|---|---|---|
| `cycle_2/stage1/t1_api.py` | +9 | −3 | 392 |
| `cycle_2/stage2b/reg_s1/t1_api.py` | +9 | −3 | 392 |
| `cycle_2/stage2/s1_api.py` | +5 | −1 | 603 |
| `cycle_2/stage2b/reg_s2/s1_api.py` | +5 | −1 | 603 |
| `cycle_4/stage2/s2_rest.py` | +5 | −2 | 300 |

`app/static/ui.js` · `app/boxes.py` · `export/export_dataset.py` · `app/README.md` · `help.html` 은
**한 글자도 고치지 않았습니다.**

### 8-2. 만든 파일 (전부 `cycles/260918_paint/cycle_4/stage2c/`)

| 파일 | 무엇 |
|---|---|
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
| `c1_revert.py` · `c1_revert.json` | 결정 1 시험(마스크·번호·상자 · 실제 내보내기 manifest 까지) |
| `c2_boxout.py` · `c2_boxout.json` | 결정 2 시험(«나갈 상자» = 실제 txt 수) |
| `c1_revert_BEFORE.log` · `c1_revert_AFTER.log` | 같은 시험의 고치기 전/뒤 |
| `c2_boxout_BEFORE.log` · `c2_boxout_AFTER.log` | 〃 |
| `mk_rep_c.py` · `rep/` | 1차 묶음을 포트·경로만 바꿔 복사(회귀) + 그 로그 |
| `mk_rep2_c.py` · `rep2/` | 2차 묶음(`s1_flow`·`s2_rest`·`s5_card`·`s6_drag`) 사본 + 그 로그 |
| `runall_c4c.sh` · `runall_c4c_outer.log` | 위 전부를 한 번에(다시 돌릴 때 이 한 줄) |
| 모래상자 `stage2c/sandbox` · `rep/sandbox*` · `rep2/sandbox*` | **지울 목록에 넣어 주세요** |

---

## 9. 3차(총괄)가 켜기 전에 알아야 할 것

1. **정적 파일은 이미 나가 있습니다**(재시작 없이) — 오늘 제가 고친 것은 `app/static/app.js` 하나입니다.
   보는 사람은 **Ctrl+F5** 한 번. `ui.js` 는 2차 판 그대로입니다.
2. **서버 파이썬을 고쳤으므로 이번에는 재시작이 필요합니다**(`server.py`·`instances.py`).
   재시작하지 않으면 «되돌리면 확정이 풀린다»·«나갈 상자» 두 가지가 **옛 동작 그대로**입니다.
3. 되돌리려면 백업 3개를 제자리로 복사하면 됩니다 —
   `app/_backup_260918_c4c_server.py` · `app/_backup_260918_c4c_instances.py` ·
   `app/static/_backup_260918_c4c_app.js` (정적 파일은 재시작 불필요).

### 켜기 순서 (담당자만)

```bash
ps -o pid,etime,cmd -p 1908658          # 내 것이 맞는지 먼저 확인 · 남의 5100·5101·5105 는 손대지 않는다
cd /data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
./app/run.sh restart
```

### 켠 뒤 확인 — 전부 GET · 쓰기 0건 (실제로 있는 주소만)

```bash
curl -s 'http://127.0.0.1:5111/api/health'                     # 로그인 없이 열림
# 아래는 로그인 쿠키가 있어야 200 (없으면 401 이 정상)
curl -s 'http://127.0.0.1:5111/api/fruits'
curl -s 'http://127.0.0.1:5111/api/export_list'                # n_confirmed_boxes_out ← 결정 2 가 바꾼 칸
curl -s 'http://127.0.0.1:5111/api/export_plan?fruit=peach&confirmed_only=1'   # caps.n_confirmed_boxes_out
curl -s 'http://127.0.0.1:5111/api/list?fruit=apple&sort=queue&mode=boxes&confirmed=0&page_size=5'
curl -s 'http://127.0.0.1:5111/api/item?fruit=apple&stem=20150919_174151_image201'
```

### 화면으로 볼 것 (사람 눈 · 시험 도구로 못 재는 것)

1. 마스크를 붓으로 고쳐 저장(Ctrl+S) → Enter 로 확정 → «수정본 되돌리기» →
   하단에 **«확정이 풀렸습니다 — 다시 확정하세요»** 가 약 1초 뜨고, 목록 카드가 **«미확정»** 으로 바뀌는지.
2. 붓 크기를 바꾼 뒤 **창을 완전히 닫았다 다시 열어** 그 값이 남는지(2차가 못 잰 유일한 항목 · 그대로 남음).
