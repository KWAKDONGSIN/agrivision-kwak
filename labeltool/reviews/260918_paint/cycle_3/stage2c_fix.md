작성: 2026-09-18

# 라벨링 툴 «데이터 정리 탭» — 사이클 3/5 · **3차 판정 전 소수정** (Opus 5)

대상: 2차 검수 `cycle_3/stage2_review.md` §4(3차에 넘긴 9건) · 1차 작업 `cycle_3/stage1_work.md` ·
총괄(Fable)의 채택 결정 · 방향 `문서/260918_툴_방향_녹취기준.md`

작업 시각(실측 `date`): 2026-09-18 **18:04 ~ 18:43** · 내 모래상자 **5431**(고치기 전/후 시험) ·
**5441·5442**(1차 시험 사본) · **5331~5335**(2차 스크립트 사본) · **5641~5669**(앞 사이클 회귀) — 전부 127.0.0.1.

🔴 실서버 **5111(PID 1458190 · 15:58:22 기동)** 에는 **한 번도 붙지 않았다**(GET 도 0건 · 재시작 0회).
공용 `T/data` 무변경(status.json 4개 mtime 그대로: apple 09-18 03:07 · blueberry 09-18 09:07 ·
grape 09-17 00:55 · peach 09-17 14:59) · `T/exports` 는 지금도 **없다**(진짜 산출물 0개).
실서비스 그림 `app/static/help/ui_export_260918c3.png` 은 **09-18 16:38 · 109,738바이트 그대로**다.

---

## 0. 한 장 요약

- 총괄이 채택한 **7건(2·3·4·5·6·7·8) + 9번 둘**을 고쳤다. **1번은 (다) 문구만**이라 손대지 않았고,
  2차의 **F1~F4 도 전부 채택**이라 손대지 않았다.
- 고친 파일은 **5개뿐**: `app/server.py`(+40줄) · `app/static/ui.js`(+11줄) · `app/static/help.html`(+1줄) ·
  시험 파일 `cycle_3/stage1/t1_api.py`(+22줄) · `cycle_3/stage1/t3_helpfig.py`(+8줄).
- 고치기 전 시험 **7통과 / 23실패** → 고친 뒤 **32통과 / 0실패**(`b1_fix.py`) · 화면 쪽 `b2_fruitko.js` **1/1 → 7/0**.
- 1차 `t1_api` 는 **빈 폴더에서 그대로 돌았고**(2차 §1-2 가 걸린 자리) 기대값 갱신 뒤 **79/0** ·
  `t2_ui` **24/0** · `t3_helpfig` 는 **가드가 막았다**(rc=1 · 실서비스 그림 0바이트 변화).
- 회귀 22묶음 + 2차 스크립트 9개: §4 표. **숫자가 달라진 것은 두 묶음뿐이고 둘 다 «2차가 옛 동작을
  기대값으로 적어 둔 자리»** 다 — `a4_input` 60/2 → **57/5**(500→400 둘은 통과로, `confirmed_only` 다섯은 400 으로) ·
  `a3_conc` 15/1 → **12/4**(`[동시-3]` 네 칸 = 총괄 결정 2 그 자체). 나머지는 **한 묶음도 숫자가 안 바뀌었다.**

---

## 1. 항목별 — 결정 · diff 전문 · 전/후 시험

번호는 2차 보고서 §4 의 번호다. 시험은 전부 `cycle_3/stage2c/b1_fix.py`(모래상자 5431) ·
`b2_fruitko.js`(node) 로 돌렸고, 로그는 `b1_fix_BEFORE.log` / `b1_fix_AFTER.log` 에 있다.

### 1-1. 항목 2 — 스레드 실패 → 영영 409 `app/server.py`

총괄 결정 **(가)**: `Thread(...).start()` 를 try/except · 실패하면 `job["state"]="error"`·`msg` 사람 말 ·
응답은 500 대신 `err_json(..., 503)`.

```diff
         _jobs[job_id] = job
-    threading.Thread(target=export_worker, args=(job,), daemon=True).start()
+        write_job_json(job)                                  # «running» 으로 먼저 써 둔다(2차 §4-4)
+    # 0918 사이클3 3차 전 소수정(2차 §4-2): 스레드를 못 띄우면 job 이 **running 인 채** 남아서
+    # 그 과일은 서버를 껐다 켜기 전에는 영영 409 였다(취소 주소가 없다). 지금은 error 로 바꾸고
+    # 500 대신 사람 말로 답한다 — 다음에 누르면 정상으로 시작한다.
+    try:
+        threading.Thread(target=export_worker, args=(job,), daemon=True).start()
+    except Exception as e:                                   # noqa: BLE001
+        job["state"] = "error"
+        job["msg"] = "시작하지 못했습니다(서버가 바쁩니다): %s" % e
+        job["finished"] = now_str()
+        write_job_json(job)
+        app.logger.exception("내보내기 스레드를 띄우지 못했습니다: %s", job_id)
+        return err_json("지금은 서버가 바빠 내보내기를 시작하지 못했습니다 — 잠시 뒤에 다시 눌러 주세요.", 503)
     return jsonify({"ok": True, "job": job_id, "out": short_path(out)})
```

시험 방법은 총괄이 말한 그대로 **monkeypatch** 다 — 앱 코드는 한 글자도 고치지 않는다.
`cycle_3/stage2c/threadfail/sitecustomize.py` 를 `PYTHONPATH` 로 끼워 넣고 `C3C_THREAD_FAIL=1` 을 주면
`export_worker` 를 돌리려는 `Thread.start()` 만 **처음 한 번** 실패한다(플라스크 자신의 스레드는 안 건드린다).

| 시험 | 고치기 전 | 고친 뒤 |
|---|---|---|
| A-1 첫 요청의 응답 | **500** «서버에서 문제가 생겼습니다…» | **503** |
| A-2 문구 | 일반 오류 문구 | «지금은 서버가 바빠 내보내기를 시작하지 못했습니다 — 잠시 뒤에 다시 눌러 주세요.» |
| A-3 그 폴더 | 목록에 **안 보임**(job.json 이 없다) | `state=error` · msg «시작하지 못했습니다(서버가 바쁩니다): can't start new thread» |
| A-4 `running` | **그 과일이 남아 있음** | **비어 있음** |
| A-5 **다음 요청** | **409** «지금 peach 를 내보내는 중입니다» | **200** · 정상 시작 |
| A-6 그 작업 | — | `done`(«끝났습니다 — 사진 0장 · 제외 125장») |

### 1-2. 항목 4 — 서버가 죽어 남은 반쪽 폴더 `app/server.py` · `app/static/ui.js`

총괄 결정 **(가)**: 시작할 때 `job.json` 을 `state:"running"` 으로 **먼저** 쓰고 끝나면 덮어쓴다.
`export_list` 는 running 인 채 남은 폴더를 «도는 중(중단됐을 수 있음)» 으로.

```diff
 def job_public(j):
     out = {k: j.get(k) for k in JOB_FIELDS}
     out["out"] = short_path(j.get("out"))
     return out
+
+
+def write_job_json(job):
+    """<out>/job.json — **시작할 때 «running» 으로 먼저 쓰고**, 끝나면 같은 자리에 덮어쓴다.
+    0918 사이클3 3차 전 소수정(2차 §4-4): 전에는 **끝날 때만** 썼다. 그래서 서버가 도중에 죽으면
+    job.json 이 없는 반쪽 폴더가 남고, 목록에도 안 보이고 상태를 물으면 404 였다.
+    지금은 «running» 인 채 남으므로 목록이 «도는 중(중단됐을 수 있음)» 이라고 말해 준다."""
+    try:
+        with open(os.path.join(job["out"], "job.json"), "w", encoding="utf-8") as f:
+            json.dump(job_public(job), f, ensure_ascii=False, indent=1)
+    except Exception:
+        app.logger.exception("job.json 을 쓰지 못했습니다: %s", job.get("out"))
```
```diff
     job["finished"] = now_str()
-    try:
-        with open(os.path.join(out, "job.json"), "w", encoding="utf-8") as f:
-            json.dump(job_public(job), f, ensure_ascii=False, indent=1)
-    except Exception:
-        app.logger.exception("job.json 을 쓰지 못했습니다: %s", out)
+    write_job_json(job)                                      # 시작할 때 쓴 «running» 을 덮어쓴다
```
```diff
             if not os.path.isfile(p):
-                continue                                     # 도는 중이거나 사람이 만든 폴더
+                continue                                     # job.json 이 없는 폴더(사람이 만든 것)
             try:
                 with open(p, encoding="utf-8") as f:
-                    items.append(json.load(f))
+                    it = json.load(f)
             except Exception:
                 continue
+            # 0918 사이클3 3차 전 소수정(2차 §4-4): 이제 job.json 은 **시작할 때** 도 쓴다.
+            # «running» 인데 지금 도는 것이 아니면 서버가 도중에 죽은 것이다 →
+            # 화면이 «도는 중(중단됐을 수 있음)» 이라고 적을 수 있게 표를 하나 붙인다.
+            if it.get("state") == "running" and it.get("job") not in _jobs:
+                it["stale"] = True
+            items.append(it)
```
화면(2차 F3 의 그 자리 한 줄만 늘렸다 — **끝난 줄에는 글자가 한 자도 안 는다**):
```diff
-  const bad = (it) => (it.state && it.state !== "done") ? (it.state === "running" ? "도는 중 " : "실패 ") : "";
+  /* 0918 사이클3 3차 전 소수정(2차 §4-4): 서버가 죽어 «도는 중» 인 채 남은 폴더는 stale 로 온다 */
+  const bad = (it) => (it.state && it.state !== "done")
+    ? (it.state === "running" ? (it.stale ? "도는 중(중단됐을 수 있음) " : "도는 중 ") : "실패 ") : "";
```

| 시험 | 고치기 전 | 고친 뒤 |
|---|---|---|
| B-1 시작 직후 `job.json` | **없다**(`masks`·`images` 뿐) | **있다** |
| B-2 그 state | — | **running** |
| B-3 목록에 보이나(도는 중) | **안 보임** | `running` · stale 아님 |
| B-4 내보내는 중 서버를 kill → 껐다 켠 뒤 | 목록에 **없음** | `state=running` · **`stale: true`** |
| B-5 그 작업의 상태를 물으면 | **404** | **200 · running** |
| B-6 정상으로 끝났을 때 | done(그때 처음 쓰임) | **done 으로 덮어씀**(사진 125장) |

### 1-3. 항목 5 — 몸통이 JSON dict 가 아니면 400 `app/server.py`

총괄 결정 **(나)**: 새 주소에만. 사이클 3 이 만든 새 주소 4개 중 **몸통을 받는 것은
`POST /api/export_start` 하나뿐**이다(`export_status`·`export_list`·`export_plan` 은 GET). 그 한 곳만 고쳤다.

```diff
     d = request.get_json(force=True, silent=True) or {}
+    # 0918 사이클3 3차 전 소수정(2차 §4-5): 몸통이 `[1,2,3]`·`"peach"` 면 `.get` 이 없어 **500** 이었다.
+    # 사이클3 이 만든 새 주소만 여기서 막는다(다른 옛 주소는 사이클4 «입력 검증» 묶음에서 한 번에).
+    if not isinstance(d, dict):
+        return err_json("보낸 내용이 «이름:값» 꾸러미가 아닙니다(JSON 객체여야 합니다).", 400)
     fruit = d.get("fruit", "")
```

| 몸통 | 고치기 전 | 고친 뒤 |
|---|---|---|
| `[1,2,3]` | 500 | **400** «보낸 내용이 «이름:값» 꾸러미가 아닙니다(JSON 객체여야 합니다).» |
| `"peach"` | 500 | **400** |
| `5` | 500 | **400** |
| 그때 생긴 폴더 | 0개 | **0개**(그대로) |

### 1-4. 항목 6 — `confirmed_only: null` `app/server.py`

총괄 결정 **(가)**: 없거나 None 이면 **True**(기본 = 사람 확정만) · bool 이 아닌 값은 **400**.

```diff
-    confirmed_only = bool(d.get("confirmed_only", True))     # 기본값 = 사람 확정만(3차 결정 1)
+    # 0918 사이클3 3차 전 소수정(2차 §4-6): 전에는 `bool()` 이라 `null`·`0`·`""`·`[]` 가 **False**
+    # (= AI 제안 포함, 더 헐거운 쪽)가 됐다. 값을 «비워» 보내는 쪽이 더 많이 내보내면 안 된다.
+    # 없거나 None 이면 **사람 확정만**(안전한 쪽) · 참/거짓이 아닌 값은 되묻는다.
+    confirmed_only = d.get("confirmed_only", True)           # 기본값 = 사람 확정만(3차 결정 1)
+    if confirmed_only is None:
+        confirmed_only = True
+    if not isinstance(confirmed_only, bool):
+        return err_json("조건(confirmed_only)은 참·거짓이어야 합니다.", 400)
```

| 보낸 값 | 고치기 전 | 고친 뒤 |
|---|---|---|
| 키가 아예 없다 | 200 · 사람 확정만 | 200 · **사람 확정만**(그대로) |
| `null` | 200 · **AI 제안 포함** | 200 · **사람 확정만** |
| `"false"`(글자) | 200 · 사람 확정만 | **400** «조건(confirmed_only)은 참·거짓이어야 합니다.» |
| `0` | 200 · **AI 제안 포함** | **400** |
| `""` | 200 · **AI 제안 포함** | **400** |
| `true` / `false`(참·거짓) | 200 · 사람 확정만 / AI 제안 포함 | **그대로**(화면이 늘 보내는 값 = 영향 0) |

### 1-5. 항목 7 — 409 문구의 «peach» `app/server.py` · `app/static/ui.js`

총괄 결정 **(나)**: 서버 문구는 그대로. 응답에 `fruit` 칸을 넣어 두고 **화면이 `FRUIT_KO` 로 조립**한다.

```diff
             if j["fruit"] == fruit and j["state"] == "running":
-                return err_json("지금 %s 를 내보내는 중입니다 — 끝난 뒤에 다시 누르세요." % fruit, 409)
+                # 0918 사이클3 3차 전 소수정(2차 §4-7): 문구는 그대로 두고 `fruit` 칸을 같이 준다 —
+                # 화면(ui.js)이 이미 가진 FRUIT_KO 로 «복숭아» 라고 바꿔 쓴다(이름표를 두 군데 두지 않는다).
+                msg = "지금 %s 를 내보내는 중입니다 — 끝난 뒤에 다시 누르세요." % fruit
+                return jsonify({"ok": False, "error": msg, "msg": msg, "fruit": fruit}), 409
```
```diff
+/* 0918 사이클3 3차 전 소수정(2차 §4-7): 409 문구가 과일을 영어로 말했다(«지금 peach 를 …»).
+   서버 문구는 그대로 두고, 서버가 같이 주는 fruit 칸을 화면이 FRUIT_KO 로 바꿔 쓴다. */
+function expErrMsg(j) {
+  let m = (j && (j.error || j.msg)) || "저장하지 못했습니다.";
+  const ko = j && j.fruit && FRUIT_KO[j.fruit];
+  if (ko) m = m.split(j.fruit).join(ko);
+  return m;
+}
+
 async function expGo() {
@@
-  if (!r.j || !r.j.ok) { $("#exp-msg").textContent = (r.j && (r.j.error || r.j.msg)) || "저장하지 못했습니다."; return; }
+  if (!r.j || !r.j.ok) { $("#exp-msg").textContent = expErrMsg(r.j); return; }
```

| 시험 | 고치기 전 | 고친 뒤 |
|---|---|---|
| E-1 같은 과일을 또 누르면 | 409 | **409**(그대로) |
| E-2 응답의 `fruit` 칸 | **없다** | **`"blueberry"`** |
| E-3 서버 문구 | «지금 blueberry 를 …» | **그대로**(한 글자도 안 바꿨다) |
| 화면이 만드는 문장(`b2_fruitko.js`) | 함수 자체가 없음 | «지금 **블루베리** 를 내보내는 중입니다 — …» |

`b2_fruitko.js` 는 **실제로 나가는 파일**에서 `app.js` 의 `FRUIT_KO` 표와 `ui.js` 의 `expErrMsg()` 를
글자 그대로 꺼내 돌린다(브라우저 없이 확인되는 부분만). 모르는 과일(`kiwi`)·`fruit` 칸이 없는 응답·
응답 자체가 없을 때 **문구를 망가뜨리지 않는 것**까지 본다 → **7/0**.

### 1-6. 항목 3·9 — 문서 둘 `app/static/help.html` · `cycle_3/stage1/t3_helpfig.py`

총괄 결정 **(나)**: help 에 스냅샷 한 줄 + «아래 표» · `t3_helpfig.py` 에 ⛔ 주석과 가드.
manifest 의 `source` 칸은 **그대로 두었다**(2차 권고 그대로).

```diff
   <li>«<b>서버에 저장</b>» 을 누르면 확인창이 <b>한 번</b> 뜹니다(과일·종류·조건·나갈 장수).
       확인하면 진행 막대가 돌고, 끝나면 <b>폴더 경로가 한 줄</b>로 나옵니다.
-      아래 «지금까지 내보낸 것» 표에도 쌓입니다.</li>
+      아래 표에도 쌓입니다.</li>
 </ol>
+<p><b>내보내기는 누른 순간의 판정 기준입니다.</b> 도는 중에 바꾼 판정은 다음 내보내기에 들어갑니다.</p>
```
```diff
 # -*- coding: utf-8 -*-
+# ⛔ 다시 돌리지 말 것(실서비스 그림을 덮어씀)
 """사용법 페이지에 넣을 «데이터 정리» 탭 그림 1장. 작성: 2026-09-18
@@
 DST = L.T + "/app/static/help/ui_export_260918c3.png"
+
+# ⛔ 이 스크립트는 «한 번 만들고 끝» 이다. 0918 사이클3 2차 검수 §1-3: DST 가 실서비스 정적 폴더라
+#    그대로 돌리면 사람이 보고 있는 사용법 그림을 다시 찍어 **덮어쓴다**(재시작 없이 5111 에 나간다).
+#    정말 다시 만들어야 할 때만:  HELPFIG_FORCE=1 python t3_helpfig.py
+if DST.startswith(L.T + "/app/static/") and os.environ.get("HELPFIG_FORCE") != "1":
+    raise SystemExit("⛔ 멈춥니다 — DST 가 실서비스 그림입니다(%s). 정말 다시 만들려면 "
+                     "HELPFIG_FORCE=1 을 주세요." % DST)
```

| 시험 | 고치기 전 | 고친 뒤 |
|---|---|---|
| F-1 스냅샷 한 줄 | 없음 | **있음**(문구는 총괄이 준 그대로) |
| F-2 «지금까지 내보낸 것» | help 405행에 있음(화면엔 없는 이름) | **없음** · «아래 표에도 쌓입니다» |
| F-3 ⛔ 주석(맨 위 둘째 줄) | 없음 | **있음** |
| F-4 가드 | 없음 | `HELPFIG_FORCE=1` 일 때만 통과 |
| F-5 실제로 돌려 보면 | (가드가 없어 **돌리지 않았다** — 돌리면 실서비스 그림을 덮어쓴다) | **rc=1 · ⛔ 문구만 찍고 즉시 멈춤** |
| F-6 실서비스 그림 | — | **109,738바이트 · mtime 09-18 16:38 그대로** |

### 1-7. 항목 8 — `t1_api.py` 가 빈 폴더에서 안 돌던 것 + 낡아진 기대값 4개

총괄 결정 **(가)**: `reset_status()` 를 `sync()` 뒤로(두 줄 순서) · **F1 로 낡아진 D-2·D-3·D-4·D-6 을
새 규칙(사람 확정이 두 모드에서 최종 · 사람 flag 는 두 모드 모두 제외)에 맞게 갱신**.

```diff
 def main():
     global SBX
-    L.reset_status()
+    # 0918 사이클3 3차 전 소수정(2차 §1-2 · §4-8): reset_status() 는 **모래상자 안** status.json 을
+    # 덮어쓰므로 모래상자를 만드는 sync() **뒤**여야 한다. 전에는 먼저 불려서 빈 폴더에서는
+    # FileNotFoundError 로 죽었다(1차는 모래상자가 이미 있던 뒤에 돌려 못 봤다). 두 줄 순서만 바꾼다.
     L.clear_exports()
     print("[준비] 모래상자를 지금 T/app·T/export·T/data 로 맞춥니다", flush=True)
     L.sync(L.SB)
     L.sync(L.SB_OLD, old=True)
+    L.reset_status()
```

기대값 갱신(근거: 방향 문서 §3-1 «사람이 확정하면 그것이 위에 선다» · 사이클 2 3차 §4-2 ·
2차 F1). part C 가 미리 **flag 2 + exclude 3 = 5장**을 사람 확정으로 만들어 두므로,
«AI 제안 포함» 결과 = **옛 판 결과 빼기 그 5장**이다.

```diff
+    # 0918 사이클3 3차 전 소수정(2차 F1 · §3-5 · §4-8): 아래 네 칸(D-2·D-3·D-4·D-6)은
+    # **옛 동작**(«AI 제안 포함» 이 사람 확정을 아예 보지 않던 것)을 기대값으로 박아 두었었다.
+    # 새 규칙 = «사람이 확정하면 그것이 위에 선다»(방향 문서 §3-1 · 사이클2 3차 §4-2):
+    #   · 사람 확정은 **두 모드에서 똑같이** 최종이다
+    #   · 사람이 flag(«문제 있음»)·exclude 로 확정한 장은 **두 모드 모두** 빠진다
+    # 그래서 «AI 제안 포함» 결과 = 옛 판 결과 **빼기 그 5장**(part C 가 flag 2 + exclude 3 을 확정해 둔다).
+    drop5 = sorted(s for s, v in (OUT.get("confirmed") or {}).get("plan", []) if v in ("flag", "exclude"))
+    stem_of = lambda k: os.path.basename(k).rsplit(".", 1)[0]          # noqa: E731
     a_new = L.md5_tree(d + "/masks")
     b_old = L.md5_tree(old_out + "/masks")
-    L.chk("D-2 masks/ 파일 이름과 md5 가 한 글자도 다르지 않다", a_new == b_old,
-          (len(a_new), len(b_old), [k for k in a_new if a_new.get(k) != b_old.get(k)][:3]))
+    b_exp = {k: v for k, v in b_old.items() if stem_of(k) not in drop5}
+    L.chk("D-2 masks/ 는 옛 판에서 «사람이 flag·exclude 로 확정한 5장» 만 빠지고 나머지는 md5 가 같다",
+          len(drop5) == 5 and a_new == b_exp,
+          (len(a_new), len(b_old), len(b_exp), [k for k in b_exp if a_new.get(k) != b_exp.get(k)][:3]))
     i_new = L.md5_tree(d + "/images")
     i_old = L.md5_tree(old_out + "/images")
-    L.chk("D-3 images/ 링크가 가리키는 곳도 같다", i_new == i_old,
-          (len(i_new), len(i_old), [k for k in i_new if i_new.get(k) != i_old.get(k)][:3]))
+    i_exp = {k: v for k, v in i_old.items() if stem_of(k) not in drop5}
+    L.chk("D-3 images/ 링크도 그 5장만 빠지고 가리키는 곳이 같다", i_new == i_exp,
+          (len(i_new), len(i_old), len(i_exp), [k for k in i_exp if i_new.get(k) != i_exp.get(k)][:3]))
     hd_n, rn = L.manifest(d)
     hd_o, ro = L.manifest(old_out)
-    L.chk("D-4 manifest 앞 9칸은 줄 하나까지 같다", [r2[:9] for r2 in rn] == ro,
-          (len(rn), len(ro)))
+    rn_by = {r2[0]: r2 for r2 in rn}
+    ro_by = {r2[0]: r2 for r2 in ro}
+    same = all(rn_by.get(s, [None])[:9] == ro_by[s][:9] for s in ro_by if s not in drop5)
+    flip = all(rn_by.get(s, ["", ""])[1] == "제외"
+               and rn_by.get(s, ["", "", "", "", "", "", ""])[6] in ("confirmed_flag", "confirmed_exclude")
+               for s in drop5)
+    L.chk("D-4 manifest 앞 9칸은 그 5장 말고는 줄 하나까지 같다(그 5장은 «제외 · confirmed_*»)",
+          len(rn) == len(ro) and same and flip,
+          (len(rn), len(ro), same, flip, [rn_by.get(s, [])[:2] + rn_by.get(s, ["", "", "", "", "", "", ""])[6:7]
+                                          for s in drop5]))
     L.chk("D-5 새 칸은 확정한 10장만 human", sum(1 for r2 in rn if r2[12] == "human") == 10,
           sum(1 for r2 in rn if r2[12] == "human"))
-    L.chk("D-6 «AI 제안 포함» 이면 사람이 flag 로 확정한 장도 나간다(옛 동작 그대로)",
-          st.get("n_images") == len([r2 for r2 in ro if r2[1] == "포함"]),
-          (st.get("n_images"), len([r2 for r2 in ro if r2[1] == "포함"])))
+    L.chk("D-6 사람이 flag 로 확정한 장은 «AI 제안 포함» 에서도 빠진다(사람 확정이 최종)",
+          st.get("n_images") == len([r2 for r2 in ro if r2[1] == "포함"]) - len(drop5),
+          (st.get("n_images"), len([r2 for r2 in ro if r2[1] == "포함"]), drop5))
```

- **D-6 은 이름과 단정을 통째로 뒤집었다** — 총괄이 말한 «사람이 flag 로 확정한 장은 AI 제안 포함에서도 빠진다» 그대로다.
- **D-2·D-3·D-4 는 «같다» 를 «그 5장만 빠지고 같다» 로** 좁혔을 뿐, 나머지 120장은 **md5 한 글자까지 옛 판과 같음**을 그대로 본다.
- 갱신 뒤 **`t1_api` 79 / 0**(§4). 시험 항목 수는 79개 그대로다(늘리지도 줄이지도 않았다).
- **빈 폴더에서 돌았다**: `cycle_3/stage2c/rep/` 에 모래상자를 **미리 만들지 않고** 돌렸고,
  `t1_api.py` 가 스스로 `sandbox`·`sandbox_old` 를 만들었다(2차가 `prep.py` 로 때워야 했던 자리).

---

## 2. 손대지 않은 것

| 것 | 왜 |
|---|---|
| **항목 1** — 상자 YOLO 가 사람 확정을 안 가린다 | 총괄 **(다)**: 지금은 문구만(2차 F4 유지) · 사이클 4 본 과제 |
| 2차 **F1**(export_dataset.py) · **F2**(app.js) · **F3**·**F4**(ui.js) | 전부 채택 — **한 글자도 건드리지 않았다**(F3 의 `bad()` 한 줄만 stale 표시를 위해 늘렸다, §1-2) |
| manifest 의 `source` 칸 | 2차 권고대로 **그대로**(그 칸의 뜻은 «확정이 있나» 다) |
| `app/boxes.py` · `export/export_dataset.py` · `app/instances.py` · `index.html`·`style.css` | 이번 소수정에서 **무변경**(md5 그대로) |

---

## 3. 전/후 시험 한눈에

| 묶음 | 고치기 전 | 고친 뒤 |
|---|---|---|
| `b1_fix.py` (항목 2·4·5·6·7·3·9 · 모래상자 5431) | **7 / 23** | **32 / 0** |
| `b2_fruitko.js` (화면이 만드는 409 문장) | **1 / 1** | **7 / 0** |
| 1차 `t1_api.py` (기대값 갱신 · **빈 폴더에서**) | (빈 폴더에서는 **아예 못 돌았다** — FileNotFoundError) | **79 / 0** |

로그: `stage2c/b1_fix_BEFORE.log` · `b1_fix_AFTER.log` · `b2_fruitko_BEFORE.log` · `b2_fruitko_AFTER.log` ·
`stage2c/rep/t1_api.log`.

---

## 4. 회귀 (실측)

보안 관련 값·설정 세부는 공개본에서 생략했습니다.
(1차·2차가 한 것과 같은 방식 · 내 사본은 `stage2c/rep`(1차 시험) · `stage2c/rep/reg_c3c`(앞 사이클 22묶음) ·
`stage2c/rep2`(2차 검수 스크립트)). **원래 폴더의 로그·json 은 한 줄도 덮지 않았다.**
실행 18:16 ~ 18:39(회귀 22묶음 18:21~18:39) · 2차 스크립트 18:24~18:35.

### 4-1. 전과 같은 것 (전부)

| 묶음 | 1차·2차가 적은 것 | 내가 돌린 것 | 판정 |
|---|---|---|---|
| **1차 `t1_api`**(기대값 갱신 · **빈 폴더에서**) | 79 / 0 (2차는 F1 뒤 75/4) | **79 / 0** | 같음(§1-7) |
| **1차 `t2_ui`**(진짜 파이어폭스 24) | 24 / 0 | **24 / 0** | 같음 |
| `py_compile` 6파일 · `node --check` 2파일 | OK | **OK** | 같음 |
| `boxes.py` 자체 점검 · `modesim.js` · `boxsim.js` | 통과 · 31/31 · 50/50 | **통과 · 31/31 · 50/50** | 같음 |
| 사이클2 1차 `t1_api` · `t2_queue` · `t3_conc` · `t4_paint8` | 79/0 · 35/8 · 8/0 · 22/0 | **79/0 · 35/8 · 8/0 · 22/0** | 같음 |
| 2차 `s1_api` · `s2_scenario` · `s3_guards` · `s4_paint8` | 68/8 · 20/0 · 18/0 · 21/1 | **68/8 · 20/0 · 18/0 · 21/1** | 같음 |
| 2차 `s5_live_guard`(part_a+c) · `s6_layout` · `s7_clip` · `s8_guard_advance` | 9/4 · 7/0 · 2/0 · 3/0 | **9/4 · 7/0 · 2/0 · 3/0** | 같음 |
| 사이클1 `t1_measure` · `t6_view` · `t3_matrix` · `t4_keys` · `t2_reg` · `s5_fix` | 155/0 · 126/4 · 84/0 · 25/0 · 11/0 · 9/0 | **155/0 · 126/4 · 84/0 · 25/0 · 11/0 · 9/0** | 같음 |
| 2차 `a1_sem`(의미) | 16 / 0 | **16 / 0** | 같음 |
| 2차 `a7_equiv`(F1 동등성) | 11 / 0 | **11 / 0** | 같음 |
| 2차 `a5c_errrow`(실패 줄) | 3 / 0 | **3 / 0** | 같음 |
| 2차 `a2b_loss`(스냅샷·권한) | 7 / 0 | **7 / 0** | 같음 |
| 2차 `a6_reg`(상자 회귀·옛 호출자) | 9 / 2 | **9 / 2** | 같음(그 2개는 2차 때부터 있던 것) |
| 2차 `a5b_ui`(진짜 브라우저 · Ctrl+S·확인창) | 7 / 0 | **7 / 0** | 같음 |
| 2차 `a5_ui`(진짜 브라우저 · 탐색용) | ok 12 · FAIL 5 · `[화면-8]` 에서 `ff.py` 오류로 **멈춤**(요약 줄 없음) | **ok 14 · FAIL 3 · 같은 `[화면-8]` 에서 같은 오류로 멈춤** | 같음(아래 설명) |
| 이번 `b1_fix.py` · `b2_fruitko.js` | — | **32 / 0 · 7 / 0**(두 번 돌려 같음) | 새로 만든 것 |

`s6_layout` 의 **숫자까지** 같다: 캔버스 81.3~88.1 % · 편집 화면 글자 마스크 155 · 상자 171 · 번호 226자
→ **편집 화면 글자는 이번에도 0자 늘었다.**

### 4-2. 달라진 것 — 둘뿐이고, 둘 다 «2차가 옛 동작을 기대값으로 적어 둔 자리» 다

| 묶음 | 2차 | 지금 | 왜 |
|---|---|---|---|
| 2차 `a4_input`(입력 62항목) | 60 / 2 | **57 / 5** | ① **좋아진 것 2개**: `입력-6-D`(목록을 보내면 400)·`입력-6-E`(글자를 보내면 400)가 **500 → 400** 으로 바뀌어 **통과**(총괄 결정 5). ② **새로 FAIL 5개**: `입력-3` 의 `'false'`·`''`·`0`·`[]`·`'0'` 가 이제 **400 으로 되묻는다**(총괄 결정 6 — «bool 이 아닌 값은 400»). 그 시험은 «무슨 값이 나오나» 를 적어 둔 것이라 400 이 되면 FAIL 로 센다. 같은 묶음의 `confirmed_only=None → True`(안전한 쪽)는 2차에서 **False 였다가 지금 통과**한다. |
| 2차 `a3_conc`(동시성 16항목) | 15 / 1 (경고 1) | **12 / 4** (경고 1) | 네 개 전부 `[동시-3]` = **총괄 결정 2 를 그대로 뒤집은 자리**다. `동시-3-A` «500 이 난다» → 지금 **503** · `동시-3-B` «그 뒤로 영영 409» → 지금 **409 가 아니다**(503, 다음 요청은 정상) · `동시-3-C` «목록에 도는 중으로 남는다» → 지금 **안 남는다**(error) · `동시-3-D` «그 작업이 running 이라고 답한다» → 지금 **그런 작업이 없다**. `동시-3-F`(껐다 켜면 사라진다)는 그대로 통과. 남은 12개(동시-1·2·4·5)는 **2차와 같은 숫자**다. |

> 2차의 주입 방식(`server.py` 의 `Thread(...).start()` 줄을 `raise RuntimeError` 로 바꿔치기)은
> 고친 뒤에도 **그대로 들어간다** — 바꿔치기된 `raise` 가 내가 만든 `try:` 안에 앉기 때문이다.
> 그래서 `a3_conc` 는 우연히도 **새 except 갈래를 그대로 시험한 셈**이 됐고, 결과가 §1-1 의 A-1~A-6 과 일치한다.

`a5_ui` 의 FAIL 3개는 전부 설명된다 — ① `화면-3-B` «표 머리말에 «상태» 칸이 있다»: 2차가 **일부러
칸을 안 늘리고**(그림판 규칙) 실패한 줄 앞에만 «실패 » 를 붙였다(F3) → 이 칸은 앞으로도 FAIL 로 남는다.
② `화면-2-A`·`화면-2-B` 폴링(2차 §2 낮음 11)은 **총괄이 채택한 9건에 없다** → 손대지 않았다.
2차보다 ok 가 2개 는 것은 F3 으로 `화면-3-A`(실패 줄에 «실패» 가 보인다)가 통과로 바뀐 몫이다.
멈추는 자리(`[화면-8]` 붓질하다 탭 바꾸기)와 오류 문장은 2차와 **글자까지 같다**
(`ff.py` — `TypeError: can't access property "getBoundingClientRect", document.querySelector(...) is null`).

---

## 5. 줄 수

| 파일 | 전 | 후 | 늘어난 것 |
|---|---|---|---|
| `app/server.py` | 1,725 | **1,765** | +40 (그중 주석·docstring 21줄) |
| `app/static/ui.js` | 999 | **1,010** | +11 |
| `app/static/help.html` | 454 | **455** | +1 |
| `cycles/260918_paint/cycle_3/stage1/t1_api.py` | 451 | **473** | +22 (시험 파일) |
| `cycles/260918_paint/cycle_3/stage1/t3_helpfig.py` | 48 | **56** | +8 (시험 파일) |

**화면에 나오는 글자**는 늘지 않았다 — 늘어난 문구는 ① 사용법 한 줄(help.html) ②
«도는 중(중단됐을 수 있음)» (서버가 죽었을 때만 나오는 줄) ③ 오류 문구 두 개(503·400)뿐이다.
정상으로 끝난 줄·확인창·상시 줄은 **한 자도 안 바뀌었다**.

---

## 6. 켜기 순서 · 켠 뒤 확인

### 6-1. 지금 5111 에 **이미 나가 있는 것** (재시작 없이)

| 파일 | 누가 |
|---|---|
| `app/static/index.html`·`app.js`·`style.css` | 1차 + 2차 F2 |
| `app/static/ui.js` | 1차 + 2차 F3·F4 + **내 것 둘**(stale 표시 · 409 문구 한국어) |
| `app/static/help.html` | 1차 + **내 것 둘**(스냅샷 한 줄 · «아래 표») |
| `app/static/help/ui_export_260918c3.png` | 1차(**16:38 · 109,738바이트 그대로**) |

서버 파이썬 3개(`server.py`·`boxes.py`·`export_dataset.py`)는 **재시작 전까지 옛 판**이다 →
지금 5111 에서 «데이터 정리» 탭을 눌러도 가드 문구만 뜬다. 보는 사람은 **Ctrl+F5** 한 번.

### 6-2. 켜기 순서 (1차 §11 · 2차 §6-2 와 같음)

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
PY=/home/kds0206/.conda/envs/kwak/bin/python
tail -20 $T/app/logs/server.log          # 1) 최근 1분에 POST /api/save·/api/status 가 없나
ps -o pid,lstart,cmd -p 1458190          # 2) 내 계정 프로세스인지(남의 것이면 멈춘다)
$PY -m py_compile $T/app/server.py $T/app/boxes.py $T/export/export_dataset.py   # 3) 통과 확인함
cd $T/app && bash run.sh restart         # 4)
```

### 6-3. 켠 뒤 확인 GET — **실제로 있는 주소만** (쓰기 0건)

```bash
B=http://127.0.0.1:5111
curl -s "$B/api/export_list"   | head -c 400   # ok:true · dir:"exports" · items:[] · running:[] · fruits 4개
curl -s "$B/api/export_plan?fruit=peach"       # ok:true · n_out(=지금 확정 장수) · caps.n_confirmed_out
curl -s "$B/api/fruits"        | head -c 300   # peach 125 · grape 2406 · apple 1001 · blueberry 1195
curl -s "$B/api/health"                        # ok · time · pid
curl -s "$B/api/stats"         | head -c 200   # 진행 현황 탭이 쓰는 곳
curl -s "$B/api/export_status?job=없는것"      # 404 «그런 작업이 없습니다.» ← 이렇게 나와야 정상
```
- `/api/export_list` 가 **404 면 서버가 아직 옛 판**이다.
- **`POST /api/export_start` 는 켜자마자 누르지 마세요** — 진짜 `exports/` 폴더가 생깁니다.
  먼저 `export_plan` 으로 «지금 누르면 몇 장» 만 보세요(파일 0개).

---

## 7. 되돌리는 법 · 파일 위치

```bash
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
C=$T/cycles/260918_paint/cycle_3
cp $T/app/_backup_260918_c3c_server.py         $T/app/server.py
cp $T/app/static/_backup_260918_c3c_ui.js      $T/app/static/ui.js
cp $T/app/static/_backup_260918_c3c_help.html  $T/app/static/help.html
cp $C/stage1/_backup_260918_c3c_t1_api.py      $C/stage1/t1_api.py
cp $C/stage1/_backup_260918_c3c_t3_helpfig.py  $C/stage1/t3_helpfig.py
```
(2차 것을 되돌리려면 `_backup_260918_c3b_*` — 2차 §6-4)

```
cycle_3/
  stage2c_fix.md                 ← 이 문서
  stage2c/
    fix_260918_c3c.py            항목 2·3·4·5·6·7·8·9 를 고친다(백업 뜨고 · --dry 로 미리 보기)
    fix_260918_c3c.apply.log     실제로 고친 기록
    lib_c3c.py                   내 모래상자 도구(5431/5432)
    b1_fix.py  b1_fix_BEFORE.log / _AFTER.log / .json     고치기 전 7/23 → 고친 뒤 32/0
    b2_fruitko.js  b2_fruitko_BEFORE.log / _AFTER.log     화면이 만드는 409 문장 1/1 → 7/0
    threadfail/sitecustomize.py  «스레드를 못 띄우는 서버» monkeypatch(앱 코드는 안 고친다)
    runall_c3c.sh                회귀 한 줄씩 · runall_c3c_outer.log
    rep/                         1차 시험의 사본(포트 5441·5442) — **모래상자를 미리 안 만든다**
      t1_api.log · t2_ui.log · t3_helpfig.log · mk_reg_c3c.py · reg_c3c/(앞 사이클 회귀 22묶음)
    rep2/                        2차 검수 스크립트의 사본(포트 5331~5335) + 로그
    sandbox/                     app·export·data 실복사(내 시험 전용)
```

지워도 되는 모래상자(약 350MB): `stage2c/sandbox` · `stage2c/rep/sandbox`·`rep/sandbox_old` ·
`stage2c/rep/reg_c3c/` · `stage2c/rep2/sandbox`·`rep2/sandbox_old`.
