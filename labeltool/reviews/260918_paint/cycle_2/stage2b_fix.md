작성: 2026-09-18

# 라벨링 툴 «사람 확정 + 검수 큐» — 사이클 2/5 · **3차 판정 전 소수정**(Opus 5)

2차 검수(`stage2_review.md`)가 «서버를 고치는 일이라 제가 하지 않았습니다» 라며 3차로 넘긴 것 가운데,
총괄(Fable)이 **고치라고 결정한 네 건만** 고쳤습니다. 툴의 다른 코드는 **한 글자도** 건드리지 않았고,
1차·2차의 보고서·로그·시험 파일도 그대로입니다(회귀가 남긴 부수 효과 하나는 §3 끝에 적었습니다).

| 시각(실측) | 한 일 |
|---|---|
| 15:08 | 시작 — `작업기록.md` 읽기 · 2차 보고서 §3·§5·§13 읽기 |
| 15:14 | 내 모래상자 만들기(`stage2b/sandbox` ← `T/app`·`T/data`·`T/export` 실복사, 링크수 1) |
| 15:17~15:25 | **고치기 전** 시험 `t_fix4.py BEFORE` → 통과 16 / **실패 13** |
| 15:26:03 | 고침 적용(`fix_260918_c2c.py`) — `app/server.py` · `app/static/ui.js` 두 파일 |
| 15:26~15:28 | **고친 뒤** 같은 시험 `t_fix4.py AFTER` → **통과 29 / 실패 0** |
| 15:29~15:48 | 회귀(2차 s1~s8 · 1차 묶음 · 앞 사이클 시뮬레이션) |
| 15:50~15:54 | 회귀 하나 더 — 사이클1 2차의 `s5_fix.py after`(N1) **9 / 0** · 내 모래상자·브라우저 정리 |

- 고친 파일 **2개**(서버 1 · 화면 1) · 고친 자리 **8곳** · 주석을 뺀 코드로 **더한 줄 20 · 지운 줄 13**
  (server.py +10/-6 · ui.js +10/-7). **뜻이 바뀌는 자리는 다섯 곳**(keep_prev 2 · confirm_status 건너뛰기 · repv · `if (!j) return;`)
- 백업 `app/_backup_260918_c2c_server.py` · `app/static/_backup_260918_c2c_ui.js`
- 실서버(5111)는 **켜지도 끄지도 않았고**, 공용 `T/data/` 에 **한 바이트도 쓰지 않았습니다**
  (`find T/data -newermt '2026-09-18 15:00' -type f` → 0건).

---

## 0. 네 건 — 전 / 후 한 줄 요약

| # | 무엇 | 고치기 전 (실측) | 고친 뒤 (실측) |
|---|---|---|---|
| **N1** | «1~4»(판정 단추)가 AI 3회 검수의 판정·검수자·메모를 **되살릴 수 없게** 지움 | AI 제외 사진에 «1» → `status=ok` · `by=사람` · **`prev` 없음** → 「수정본 되돌리기」는 «아직 안 봄 + 메모 «수정본 되돌림»» | `prev={exclude · AI 3회 검수(…) · «중복: …»}` 가 남고, 「수정본 되돌리기」가 **AI 제외·검수자·메모를 그대로 되살림** |
| **N3** | 묶음째 확정이 «사람이 이미 확정한 구성원» 을 «제외» 로 덮음(서버) | API 로 직접 보내면 `ok(먼저본사람)` → **`exclude(묶음확정사람)`** | 그 장은 **건드리지 않고** 응답 `skipped:["…image6"]` 로 알려 줌 |
| **N5** | 묶음 대표에서 `Enter` 가 AI 의 `flag` 를 **«원본 OK» 로 바꿔** 확정 | 대표(AI=flag) → 확정 **`ok`** · 확인창 «이 사진(대표) = 쓴다(원본 그대로 OK)» | 대표 → 확정 **`flag`** · 확인창 «**대표: 문제 있음 으로 확정 · 나머지 6장: 제외로 확정**» |
| **가드** | «서버가 아직 확정을 모릅니다» 가드가 떠도 **다음 사진으로 넘어감** | `image101` → **`image106`** (확정 0인데 사람은 «했다» 고 오해) | `image101` → **`image101`** (그 자리에 머무름 · 확정 0) |

---

## 1. 고친 것 — diff 전문

### 1-1. `app/server.py` (백업 `_backup_260918_c2c_server.py`, 원본 시각 13:16:07)

```diff
--- _backup_260918_c2c_server.py	2026-09-18 13:16:07
+++ server.py	2026-09-18 15:26:03
@@ -448,19 +448,29 @@ def confirm_status(fruit, pairs, by, note):
     pairs = [(stem, status), ...] (묶음째 확정이면 여러 장). `status:<과일>` 자물쇠 안에서
     한 번에 읽고 한 번에 쓰므로, 묶음 안에서 일부만 저장되는 일이 없다(N-A 와 같은 층).
     `status`·`note`·`prev` 는 건드리지 않는다.
+
+    0918 «3차 판정 전 소수정»(N3): **구성원(pairs[1:]) 중 사람이 이미 확정한 장은 건너뛴다.**
+    기존 「묶음 제외」 단추(api_exclude_group)의 «사람이 판정한 사진은 건너뛴다» 와 같은 규칙이다.
+    화면(ui.js enterConfirm)이 이미 걸러 보내지만, **두 사람이 동시에** 같은 묶음을 확정하면
+    화면만으로는 못 막는다 — 여기가 마지막 방어선이다(실측 stage2/s1_api [마]-2).
+    반환: (확정한 것, 건너뛴 stem 목록). 대표(pairs[0])는 사람이 **지금 누른** 장이라 건너뛰지 않는다.
     """
     out = {}
+    skipped = []
     with lock_for("status:" + fruit):
         d = read_status(fruit)
         at = now_str()
-        for stem, v in pairs:
+        for i, (stem, v) in enumerate(pairs):
             rec = d.get(stem) or {}
+            if i and confirmed_of(rec):
+                skipped.append(stem)       # 남의 확정(또는 내 옛 확정)을 덮지 않는다
+                continue
             # `src` 는 적지 않는다 — 위 주석대로 그 칸은 이미 «어느 단추가 제외했나» 표식이다.
             rec["confirmed"] = {"status": v, "by": by, "at": at, "note": note}
             d[stem] = rec
             out[stem] = rec["confirmed"]
         write_status(fruit, d)
-    return out
+    return out, skipped
@@ -1076,13 +1086,19 @@ def api_save():
     with lock_for("mask:%s:%s" % (fruit, stem)):
         if action == "ok":
-            st = update_status(fruit, stem, "ok", by, note)
+            # 0918 사이클2 «3차 판정 전 소수정»(N1): 사람이 «1~4» 를 누르면 AI 3회 검수의
+            # 판정·검수자·메모가 **되살릴 수 없게** 지워졌다(실측 stage2/s5_live_guard [C]).
+            # keep_prev=True 로 «AI 제안이던 것» 을 한 벌만 prev 에 적어 둔다 — 마스크 저장
+            # 길(_save_verdict)이 이미 쓰는 것과 **같은 장치**이고, 「수정본 되돌리기」
+            # (/api/revert)가 그 prev 로 되살린다. 사람이 이미 prev 를 가졌으면 덮지 않는다.
+            st = update_status(fruit, stem, "ok", by, note, keep_prev=True)
             # 내보내기는 masks_fixed 가 있으면 그것을 쓴다 → «원본 그대로» 와 어긋날 수 있어 알려 준다
             return jsonify({"ok": True, "status": st, "wrote_mask": False,
                             "has_fixed": os.path.exists(fixed_path(fruit, stem))})
 
         if action in ("flag", "exclude"):
-            st = update_status(fruit, stem, action, by, note)
+            # 같은 이유(N1) — «3 문제 있음»·«4 제외» 도 옛 판정을 prev 에 남긴다
+            st = update_status(fruit, stem, action, by, note, keep_prev=True)
             return jsonify({"ok": True, "status": st, "wrote_mask": False})
@@ -1171,8 +1187,10 @@ def api_status():
             pairs.append((s2, v2))
-        return jsonify({"ok": True, "confirmed": confirm_status(fruit, pairs, by, note),
-                        "n": len(pairs)})
+        conf, skipped = confirm_status(fruit, pairs, by, note)
+        # `n` 의 뜻은 그대로 둔다(= 이 묶음이 몇 장짜리였나). 0918 소수정(N3)으로 **건너뛴 장**은
+        # `skipped` 한 칸으로 따로 알려 준다 — 옛 화면·옛 시험은 `n` 만 보므로 영향이 없다.
+        return jsonify({"ok": True, "confirmed": conf, "n": len(pairs), "skipped": skipped})
     st = update_status(fruit, stem, s, by, note)
     return jsonify({"ok": True, "status": st})
```

주석을 뺀 코드: **더한 줄 10 · 지운 줄 6**
(`skipped = []` · `for i, (stem, v) in enumerate(...)` · `if i and confirmed_of(rec)` 세 줄 ·
`return out, skipped` · `keep_prev=True` 두 곳 · `conf, skipped = …` · `jsonify` 한 줄).

### 1-2. `app/static/ui.js` (백업 `_backup_260918_c2c_ui.js`, 원본 시각 14:24:17)

```diff
--- _backup_260918_c2c_ui.js	2026-09-18 14:24:17
+++ ui.js	2026-09-18 15:26:03
@@ -741,9 +741,13 @@ async function enterConfirm() {
   if (m.dup_rep === m.stem && others.length) {
-    // 묶음째 확정 — 확인창 **한 번**. 대표는 «쓴다(원본 OK)», 나머지는 «제외» 로 확정한다.
-    // 대표는 «쓴다». 사람이 방금 고쳐 저장한 사진이면 «수정함» 을 지켜 준다(고친 사실이 지워지지 않게).
-    const repv = (m.ai_status === "fixed") ? "fixed" : "ok";
+    // 묶음째 확정 — 확인창 **한 번**. 대표는 «자기 AI 제안 그대로», 나머지는 «제외» 로 확정한다.
+    // 0918 «3차 판정 전 소수정»(N5): 전에는 AI 가 «문제 있음»(flag) 이라고 한 대표까지 «원본 OK» 로
+    // 확정해 버려(실측 s3_guards 가드9), 사람이 보지도 않은 «문제 없음» 이 찍혔다. 한 장짜리 길
+    // (아래 else)에서 Enter 는 «AI 제안 그대로» 이므로 묶음 길도 같은 뜻이어야 한다 —
+    // flag 면 flag 로 확정하고(그 사진은 큐에 «고칠 것» 으로 남는다), 사람이 방금 고쳐 저장한
+    // 사진이면 «수정함» 을 지켜 준다. 판정이 없는 사진(아직 안 봄)만 «쓴다(원본 OK)» 로 본다.
+    const repv = ["ok", "fixed", "flag", "exclude"].indexOf(m.ai_status) >= 0 ? m.ai_status : "ok";
@@ -753,20 +757,26 @@
     if (!confirm("거의 같은 사진 묶음 " + mem.length + "장을 한 번에 확정합니다.\n\n"
-        + "· 이 사진(대표) = 쓴다(" + statusKo(repv) + ")\n"
-        + "· 나머지 " + todo.length + "장 = 제외\n"
+        + "· 대표: " + statusKo(repv) + " 으로 확정\n"
+        + "· 나머지 " + todo.length + "장: 제외로 확정\n"
         + (keep.length ? "· 그중 " + keep.length + "장은 사람이 이미 확정해서 그대로 둡니다\n" : "")
         + "\n원본 파일은 지워지지 않습니다. 계속할까요?")) return;
     const j = await confirmVerdict(repv, todo.map((x) => ({ stem: x, status: "exclude" })));
-    if (j) flash("묶음 " + mem.length + "장을 확정했습니다 (대표 1장 쓰기 · " + todo.length + "장 제외"
-                 + (keep.length ? " · 이미 확정된 " + keep.length + "장은 그대로" : "") + ")");
+    if (!j) return;            // 0918 소수정(가드): 확정이 안 됐으면 **다음 사진으로 넘어가지 않는다**
+    flash("묶음 " + mem.length + "장을 확정했습니다 (대표 1장 " + statusKo(repv) + " · "
+          + todo.length + "장 제외"
+          + (keep.length ? " · 이미 확정된 " + keep.length + "장은 그대로" : "") + ")");
   } else {
     const ai = m.ai_status || m.status || "unreviewed";
     if (ai === "unreviewed") { flash("이 사진에는 아직 판정이 없습니다 — 1~4 로 직접 고르세요", true); return; }
     const j = await confirmVerdict(ai);
-    if (j) flash("확정: " + statusKo(ai) + " (" + who() + ")");
+    // 0918 «3차 판정 전 소수정»(가드): 전에는 확정이 **안 됐어도** 아래 nextItem() 이 돌아
+    // 다음 사진으로 넘어갔다 — 옛 서버에서 Enter 를 열 번 누르면 열 장이 넘어가는데 확정은 0 이라
+    // 사람이 «다 했다» 고 오해했다(실측 stage2/s8_guard_advance.py). 그 자리에 머문다.
+    if (!j) return;
+    flash("확정: " + statusKo(ai) + " (" + who() + ")");
   }
-  nextItem(true);            // 다음 장이 자동으로 뜬다(확정은 붓질을 버리지 않으므로 다시 안 묻는다)
+  nextItem(true);            // 확정이 **된** 때만 다음 장이 자동으로 뜬다(붓질을 버리지 않으므로 안 묻는다)
 }
```

주석을 뺀 코드: **더한 줄 10 · 지운 줄 7**
(`repv` 한 줄 교체 · `if (!j) return;` **두 곳** · 확인창 문구 두 줄 · 알림 문구 · `nextItem` 주석).
**뜻이 바뀌는 자리는 세 곳뿐입니다**: `repv` 계산 · 묶음 길의 `if (!j) return;` · 한 장 길의 `if (!j) return;`.

---

## 2. 전 / 후 시험 — `stage2b/t_fix4.py` (같은 스크립트를 두 번)

보안 관련 값·설정 세부는 공개본에서 생략했습니다.
①③④ 는 **진짜 파이어폭스**, ② 는 서버 API 직접(화면을 거치지 않는 방어선).

| | 고치기 전 `t_fix4_BEFORE.log` | 고친 뒤 `t_fix4_AFTER.log` |
|---|---|---|
| 합계 | 통과 16 / **실패 13** | **통과 29 / 실패 0** |

### ① N1 — «1» 을 누른 뒤 AI 3회 검수가 되살아나는가 (새 서버 5201 · 진짜 브라우저)

사진 `20150919_174151_image101` · 전 `status=exclude` · `by=AI 3회 검수(Opus5→Opus5→Fable5.1)` ·
`note=중복: 20150919_174151_image96`

| 시험 | 전 | 후 |
|---|---|---|
| 1-a «1» 로 사람 확정이 찍힌다 | ok | ok |
| 1-b `status` 는 `ok` 로 바뀐다(지금 동작 유지) | ok | ok |
| 1-c `prev` 에 AI 판정 «제외» | **FAIL**(`prev` 없음) | **ok** |
| 1-d `prev` 에 AI 검수자 이름 | **FAIL** | **ok** |
| 1-e `prev` 에 AI 메모 | **FAIL** | **ok** |
| 1-f 두 번째 판정(«3»)이 `prev` 를 덮지 않는다 | ok | ok |
| 1-f′ 그래도 확정은 새 판정(flag)으로 바뀐다 | ok | ok |
| 1-g 화면에 «수정본 되돌리기» 단추가 있다 | ok | ok |
| 1-h 「수정본 되돌리기」가 **AI 제외를 되살린다** | **FAIL**(`unreviewed`) | **ok**(`exclude`) |
| 1-i AI 검수자 이름도 되살아난다 | **FAIL**(`소수정사람`) | **ok** |
| 1-j AI 메모도 되살아난다 | **FAIL**(«수정본 되돌림») | **ok**(«중복: …image96») |
| 1-k 되돌린 뒤 `prev` 는 치워진다(기존 규칙) | ok | ok |

- **되살리는 길은 새로 만들지 않았습니다.** 화면의 「수정본 되돌리기」 → `POST /api/revert` →
  «`prev` 가 있으면 그것으로 되돌리고 `prev` 를 치운다» 는 **0918 UI사이클4 2차가 넣어 둔 기존 길**
  그대로입니다(`server.py` 1116~1149행, 한 글자도 안 고쳤습니다).
- ⚠ 그 단추는 **접힌 오른쪽 칸**(`#side.fold` → `#sidebody` `display:none`) 안의 «더 보기»(`#sec-more`)
  칸에 있습니다 — 사람이 오른쪽 칸을 펴고 그 칸을 열어야 보입니다. **제가 만든 문제가 아니고**
  배치도 안 건드렸지만, N1 의 되살리는 길이 «두 번 접힌 곳» 에 있다는 것은 3차가 알아야 합니다.
- `prev` 는 «AI 제안이던 것» **한 벌만** 적습니다(기존 `keep_prev` 규칙 그대로):
  이미 `prev` 가 있으면 덮지 않고, 지금 판정이 `flag`·`exclude` 일 때만 생깁니다.

### ② N3 — 서버가 «이미 확정한 구성원» 을 건너뛰는가 (API 직접)

묶음 5장 · 대표 `…image1` · 구성원 `…image6`(먼저 «원본 OK» 로 확정) ·`image11`·`image16`·`image26`

| 시험 | 전 | 후 |
|---|---|---|
| 2-a 묶음째 확정 200 | ok | ok |
| 2-b 이미 확정한 구성원이 그대로다 | **FAIL** `ok(먼저본사람)` → `exclude(묶음확정사람)` | **ok** 그대로 |
| 2-c 응답 `skipped` 에 그 장이 담긴다 | **FAIL**(칸 없음) | **ok** `["20150919_174151_image6"]` |
| 2-d 나머지 구성원은 «제외» 로 확정 | ok | ok |
| 2-e 대표는 확정된다 | ok | ok |
| 2-f AI 제안(`status`)은 안 바뀐다 | ok | ok |
| 2-g 아무도 확정 안 해 둔 묶음은 `skipped` 가 빈다 | ok | ok(`[]`) |

- 응답의 `n` **뜻은 안 바꿨습니다**(= 이 묶음이 몇 장짜리였나). 결정문이 «응답에 `skipped` 목록» 이라
  했고, `n` 을 바꾸면 1차 시험 `t1_api ⑤`·2차 시험 `s1_api 마-1`(«n = 묶음 크기»)이 **뜻 없이** 깨집니다.
  건너뛴 장수는 `skipped.length` 로 셉니다.
- 화면 쪽(2차의 F2)은 그대로 둡니다 — 화면이 먼저 걸러 보내고, 서버가 마지막에 한 번 더 막습니다.

### ③ N5 — flag 대표 묶음에서 Enter (새 서버 5201 · 진짜 브라우저)

묶음 7장 · 대표 `20150919_174151_image201`(AI=flag) · 나머지 6장(AI=exclude)

| 시험 | 전 | 후 |
|---|---|---|
| 3-a 대표는 자기 AI 제안(flag) 그대로 확정 | **FAIL** 확정 `ok` | **ok** 확정 `flag` |
| 3-b 구성원은 «제외» 로 확정 | ok | ok |
| 3-c 확인창 «대표: 문제 있음 으로 확정» | **FAIL**(«이 사진(대표) = 쓴다(원본 그대로 OK)») | **ok** |
| 3-d 확인창 «나머지 6장: 제외로 확정» | **FAIL**(«나머지 6장 = 제외») | **ok** |
| 3-e AI 제안(`status`)은 안 바뀐다 | ok | ok |
| 3-f 그 사진은 큐에 «고칠 것»(flag)으로 남는다 | **FAIL** | **ok** |

고친 뒤 확인창 전문(실측):

```
거의 같은 사진 묶음 7장을 한 번에 확정합니다.

· 대표: 문제 있음 으로 확정
· 나머지 6장: 제외로 확정

원본 파일은 지워지지 않습니다. 계속할까요?
```

### ④ 가드 — 옛 서버(백업 서버 트리) + 새 화면 (5202 · 진짜 브라우저)

| 시험 | 전 | 후 |
|---|---|---|
| 4-a 가드 문장이 뜬다 | ok | ok |
| 4-b 확정은 0 이다 | ok (0 → 0) | ok (0 → 0) |
| 4-c 가드가 떴으면 **그 자리에 머문다** | **FAIL** `image101` → `image106` | **ok** `image101` → `image101` |

가드 문장(실측): «서버가 아직 «확정» 을 모릅니다 — 담당자가 서버를 다시 켠 뒤에 쓰세요(아무것도
저장하지 않았습니다)»

---

## 3. 회귀 — 시험 코드는 **한 글자도 안 고치고**

1차(`cycle_2/stage1`)와 2차(`cycle_2/stage2`)의 시험을 `stage2b/reg_s1`·`reg_s2` 로 **실복사**해
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
1차·2차의 로그·json 은 **한 개도 덮지 않았습니다**. 한 줄 재현: `bash stage2b/runall_c2c.sh`.

### 3-1. 2차 검수의 s1~s8 (기준 = 2차의 `*_AFTER.log`)

| 시험 | 2차가 적은 값 | 내 결과 | 판정 |
|---|---|---|---|
| `s1_api.py` | 71 / 5 | **72 / 4** | **마-2(N3 서버 쪽)가 실패 → 통과**. 남은 4개는 2차가 «안 고침» 으로 넘긴 것 그대로(검증-8·9 = N7 500 · 검증-10 = N8 · 바-6 = N6). **마-1 «n = 묶음 크기» 는 계속 통과**(`n` 뜻을 안 바꿨으므로) |
| `s2_scenario.py` | 20 / 0 | 20 / 0 | 같음 |
| `s3_guards.py` | 17 / 1 | **18 / 0** | **가드9(N5)가 실패 → 통과**(대표 확정 = `flag`). 가드1~8·10 은 전과 같이 통과 |
| `s4_paint8.py` | 21 / 1 | 21 / 1 | 같음(남은 1 = N10 «확정 딱지 12.5px», 3차 몫) |
| `s5_live_guard.py` (part_a+part_c) | 9 / 4 | 9 / 4 | 같음. **C-3(AI 메모가 남는가)은 이제 `prev` 로 통과**하고, C-2·C-4 는 설계 (나) 몫이라 그대로 실패(§4-3). A-2·A-6 실패도 2차와 같은 그 두 개 |
| `s6_layout.py` | 7 / 0 | 7 / 0 | 같음 |
| `s7_clip.py` | 2 / 0 | 2 / 0 | 같음(도구 이름 잘림 0곳) |
| `s8_guard_advance.py` | 2 / 1 | **3 / 0** | **가드-C 가 실패 → 통과**(그 자리에 머문다) |

### 3-2. 1차의 묶음 + 앞 사이클 회귀

| 시험 | 1차·2차가 적은 값 | 내 결과 | 판정 |
|---|---|---|---|
| `t1_api.py` (A·B·보호 장치 · **P1·P2·N-A·N-C** 포함) | 79 / 0 | **79 / 0** | 같음 — `keep_prev` 를 넣어도 «N-A 되돌리기가 `prev` 로 제외·메모를 되살린다»·«확정이 AI 제안을 안 건드린다» 가 전부 그대로 |
| `t2_queue.py` (10장 시나리오·가드) | 43 / 0 | **35 / 8** | ❗ **실패 8개가 전부 같은 한 줄** — «묶음째: 대표는 «쓴다» 로 확정(원본 OK 또는 수정함)» · 값은 여덟 번 다 `flag`. **N5 결정이 바로 이 동작을 바꾸라는 것**이므로 시험의 기대값이 낡은 것입니다(1차 시험이라 고치지 않았습니다). 나머지 35칸은 전과 같이 통과 |
| `t3_conc.py` (동시 100건) | 8 / 0 | 8 / 0 | 같음 |
| `t4_paint8.py` (8건 전/후) | 22 / 0 | 22 / 0 | 같음 |
| `runall_stage1/t1_measure.py` (배치 25벌) | 155 / 0 | 155 / 0 | 같음 |
| `runall_stage1/t6_view.py` (보기 전환) | 126 / 4 | 126 / 4 | 같음(3차가 «시험의 사진 고르기 문제» 로 판정한 그 4개) |
| `runall_stage1/t3_matrix.py` (네 과일 × 세 작업) | 84 / 0 | 84 / 0 | 같음 |
| `runall_stage1/t4_keys.py` (단축키 25) | 25 / 0 | 25 / 0 | 같음 |
| `runall_stage1/t2_reg.py` (11칸 회귀 · **py_compile 서버 5파일** 포함) | 11 / 0 | 11 / 0 | 같음 |
| `runall_stage1/t5_shots.py` | 0 FAIL | **안 돌림** | 실서비스 폴더에 그림을 덮어씀 → §4-4 |
| `260918_paint/stage2/s5_fix.py after` (N1 · 사이클1 2차) | 9 / 0 | **9 / 0** | 같음(F1~F5 전부) |
| `modesim.js` | 31 / 31 | **31 / 31** | 같음 |
| `boxsim.js` | 50 / 50 | **50 / 50** | 같음 |
| `sim.js` (좌표 역변환) | 오차 1e-11 | 동일 | 같음 |
| `app/boxes.py` 자체 점검 | 통과 | 통과 | 같음 |
| `node --check app.js·ui.js` · `py_compile` 서버 5파일 | 통과 | **통과** | `server.py`·`instances.py`·`boxes.py`·`dupes.py`·`maskio.py`(+`export_dataset.py`) |

**바뀐 칸은 정확히 네 군데뿐입니다**: `s1_api` 마-2 · `s3_guards` 가드9 · `s8_guard_advance` 가드-C
(셋 다 실패 → 통과) 와 `t2_queue` 의 «대표는 «쓴다»» 여덟 줄(통과 → 실패, **N5 결정 그 자체**).
그 밖의 모든 칸은 숫자까지 전과 같습니다.

⚠ **정직하게 적어 둘 부수 효과 하나**: 1차의 `t2_reg.py` 는 «옛 스크립트가 지금도 도는가» 를 보려고
`cycles/260917_신기능/` 의 스크립트를 **다시 돌립니다**. 그래서 그 스크립트들의 **시험 산출물 json 3개**가
새로 써졌습니다 — `cycle_3/stage1/seed_after_sbx6.json`(차이는 측정 밀리초뿐) ·
`cycle_6_n6/stage1/n1_cut.json` · `n6_save.json`. 1차(13:2x)·2차(14:5x) 회귀 때도 같은 일이 있었고
(그래서 파일 이름에 `_sbx6` 가 붙어 있습니다), **문서·판정서(.md)와 `T/inspect/` 는 손대지 않았습니다.**

---

## 4. 제가 고른 것(결정문에 안 적혀 있던 갈림길) — 3차가 볼 곳

1. **응답 `n` 의 뜻을 안 바꿨다**(N3). 위 §2-② 참조. 건너뛴 장수는 `skipped` 로 셉니다.
   `S.confDone += j.n`(app.js)은 그대로라 **동시에 겹친 드문 경우에만** 진행률이 1~2장 많게 셉니다.
   (화면이 이미 걸러 보내므로 평소에는 `n` = 실제로 쓴 장수입니다. app.js 는 안 고쳤습니다.)
2. **«AI 제안 그대로» 의 범위**(N5). `ok`·`fixed`·`flag`·`exclude` 는 **그대로**, `unreviewed` 만
   «쓴다(원본 OK)» 로 봅니다(전과 같음). 결정문 본문이 «대표는 자기 AI 제안 그대로» 라서 `exclude` 도
   포함했습니다 — 대표가 `exclude` 인 경우는 `pick_representative` 규칙상 **묶음 전원이 exclude 일 때뿐**
   이고(dupes.py 70~73행), 그때는 확인창이 «대표: 제외 으로 확정 · 나머지 N장: 제외로 확정» 이라고
   **먼저 보여 줍니다**. 원본 파일은 지워지지 않습니다. 3차가 «그 경우 대표는 살려야 한다» 고 보면
   `repv` 한 줄에서 `"exclude"` 만 빼면 됩니다.
3. **N1 은 (가) «한 글자 고침» 만 넣었습니다.** 2차가 말한 (나)««1~4» 는 `confirmed` 만 쓰고 `status` 는
   건드리지 않는다» 는 **사이클 4** 몫입니다. 그래서 2차 시험 `s5_live_guard` 의 **C-2·C-4 는 지금도
   FAIL 입니다**(`status`·`by` 는 여전히 사람 것으로 바뀜) — 고쳐진 것은 «되살릴 수 있게 되었다» 뿐입니다.
4. **시험을 돌리지 않은 것 둘**(이유를 적습니다):
   `runall_stage1/t5_shots.py` — 사용법 그림을 **실서비스 폴더 `app/static/help/` 에 덮어씁니다.**
   제 수정과 무관하고 «정적 파일 최소 변경» 이라 안 돌렸습니다(2차가 이미 0 FAIL).
   `s5_live_guard.py part_b` — **실서버 5111** 에 붙습니다(GET 뿐이지만 안 건드립니다) → `part_a`·`part_c` 만.

---

## 5. 3차가 «켜기» 전에 — 바뀐 것만

🔴 **정적 파일(`ui.js`)은 재시작 없이 이미 5111 에 나가 있습니다.** 2차의 F1·F2·F5·F6 과 같은 성질입니다
(서버가 `static/` 을 **디스크에서 그때그때** 읽어 줍니다 — 2차가 §13-1 에서 실측으로 확인해 둔 것).
저는 실서버에 **로그인조차 하지 않았습니다**: 확인은 `curl http://127.0.0.1:5111/static/ui.js` 한 번뿐이고
로그인 화면으로 넘기는 **302** 만 받았습니다(쓰기 0건 · 판정 0건).
이번에 나간 것은 **N5(대표 확정값·확인창 문구)** 와 **가드(안 넘어감)** 두 개이고, 둘 다 **화면을 더
안전하게** 만드는 쪽입니다. 지금 5111 은 서버가 옛 판이라 `Enter` 는 가드에 막히는데, 이제 **그 자리에
머물러** 사람이 «확정됐다» 고 오해하지 않습니다. 보는 사람은 **Ctrl+F5** 한 번.

🔴 **`server.py`(N1·N3)는 서버 코드라 켠 뒤에 효과가 납니다.** 실서버 PID **313878** 은
`2026-09-18 04:49:41` 기동이고 `server.py` 수정은 **15:26:03** — 기동보다 뒤라 **지금 도는 코드는 옛 판**
입니다(2차 §13 규칙 8 그대로 유지).

### 켜기 (2차 §13-2 순서 + 이번 것)

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
tail -20 $T/app/logs/server.log        # ① 최근 1분에 POST /api/save·/api/status·/api/save_instances 가 없나
ps -o pid,lstart,cmd -p 313878         # ② 지금 도는 서버가 그 PID 인가 (남의 프로세스면 멈춘다)
kill 313878                            # ③ 사람이 결정한 뒤에만
cd $T/app && nohup ./run.sh > logs/start_$(date +%y%m%d_%H%M).log 2>&1 &
```

### 켠 뒤 확인 GET (이 순서로, 쓰기는 하나도 없음)

```bash
B=http://127.0.0.1:5111
curl -s $B/api/fruits                                   # n_confirmed 칸이 **생겼는지**(옛 판엔 없음)
curl -s "$B/api/list?fruit=apple&page_size=20"          # items[0] 에 ai_status·confirmed·src 가 있는지
curl -s "$B/api/list?fruit=apple&page_size=20&sort=queue"   # 큐 순서(flag → 묶음 대표 → 나머지)
curl -s "$B/api/item?fruit=apple&stem=20150919_174151_image201"  # dup_member_confirmed 칸이 오는지
curl -s "$B/api/counts?fruit=apple"                     # 확정 0 · by_person {}
```

기대값(제 실측 기준, 2차와 같음): `peach 125 · grape 2406 · apple 1001 · blueberry 1195` ·
**확정 0 · `by_person {}`** · `/api/list` 에 `ai_status` 있음.

### 되돌리는 법 (한 줄씩)

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
cp $T/app/_backup_260918_c2c_server.py        $T/app/server.py
cp $T/app/static/_backup_260918_c2c_ui.js     $T/app/static/ui.js
```

---

## 6. 파일 위치

```
T/cycles/260918_paint/cycle_2/
  stage2b_fix.md                  ← 이 문서
  stage2b/
    fix_260918_c2c.py             고친 것 네 건(백업 뜨고 고치는 스크립트 · 다시 돌리면 SKIP 만 찍고 아무것도 안 바꿈)
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    t_fix4.py                     네 건 전/후 시험 · t_fix4_BEFORE.log / t_fix4_AFTER.log / *.json
    probe_revert.py               «수정본 되돌리기» 단추가 어디 있나(읽기만)
    runall_c2c.sh                 회귀 한 줄 재현 · runall_c2c.log
    reg_s0/                       사이클1 2차의 s5_fix.py 실복사(포트 5209) · s5_fix_after.log
    reg_s1/                       1차 시험 실복사(포트 5203) — t1_api·t2_queue·t3_conc·t4_paint8·runall_stage1
    reg_s2/                       2차 시험 실복사(포트 5205~5208) — s1_api ~ s8_guard_advance
    sandbox/                      app+data+export 실복사 · app_before = 사이클2 **전** 판
~/ff_shots/c2/stage2b/            스크린샷(c2c_1_n1_* · c2c_3_n5_* · c2c_4_guard_*)
```

고친 원본 파일 2개: `T/app/server.py` · `T/app/static/ui.js`
백업 2개: `T/app/_backup_260918_c2c_server.py` · `T/app/static/_backup_260918_c2c_ui.js`
