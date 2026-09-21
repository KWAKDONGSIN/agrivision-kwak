# -*- coding: utf-8 -*-
"""b16 — **F1 단축키 한 장 겹창** (편의 U7).
작성: 2026-09-21

왜
  단축키 표는 있었지만 **가는 길이 하나뿐이고 깊었다** — «?» 로 첫 방문 안내 3장을 띄우고,
  그 맨 아래 접힌 칸(`.shortcut-panel`, `max-height:30vh`)을 펴야 나왔다. 윈도우 프로그램은
  거의 다 **F1 = 도움말**이라 사람이 먼저 누르는 키가 F1 인데, 여기서는 아무 일도 안 났다.
  그래서 F1 로 열고 Esc 로 닫는 겹창 한 장을 얹는다. 표 자체는 새로 안 만든다 —
  `keys.js` 의 KEYS **한 곳**에서 온다(`[data-key-table]`).

이 시험의 핵심은 ③ 이다 — «표에 적힌 키가 진짜 키와 어긋나지 않는가».
  글자 대조는 `tests/unit/u7_keys_doc.py` 가 **파일**에서 보고(표 ↔ 도움말 ↔ 손잡이 코드,
  그리고 0921 에 더한 반대 방향 «코드가 받는 키가 표에 다 있나»), 이 시험은 **진짜 화면에
  뜬 겹창**이 그 표와 한 줄도 다르지 않은지 본다. 둘이 같은 자리를 양쪽에서 조인다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 처음에는 겹창이 숨어 있다
    ② F1 로 열린다
    ③ 겹창의 표가 UI.KEYS 와 **한 줄도 안 어긋난다** (줄 수·키·뜻 전부)
    ④ 열려 있는 동안 **뒤의 단축키가 안 먹는다** (b·1·0·x 를 눌러도 아무 일이 없다)
    ⑤ Esc 로 닫히고, 그 Esc 가 그리던 다각형을 지우지 않는다
    ⑥ F1 을 다시 누르면 닫힌다 (토글)
    ⑦ ✕ 단추와 바깥 어두운 데 클릭으로도 닫힌다
    ⑧ 목록 화면에서도 F1 이 듣는다 (편집 화면 전용이 아니다)
    ⑨ 글자 칸(«내 이름»)에 커서가 있어도 F1 은 듣는다 — «?» 는 안 듣는 것이 맞다(회귀)
    ⑩ 안내 창이 떠 있으면 F1 이 겹창을 안 연다 (겹창 두 장을 포개지 않는다)
    ⑪ «?» 로 안내 창이 여전히 열리고 그 안의 단축키 칸도 그대로다 (회귀)
    ⑫ 겹창이 화면 안에 다 들어오고, 표의 **마지막 줄까지** 닿는다
    ⑬ 전문가 모드·좁은(휴대폰) 폭에서도 카드가 화면 밖으로 안 나간다 — 폭은 **재서** 적는다
    ⑭ 콘솔 오류 0 · 붓질 회귀
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b15 와 같다).

⚠ `S`·`UI` 는 쪽의 전역이라 `b.js()` 안에서는 안 보인다 → `L.ev()`(window.eval) 로 읽는다
  (b13·b14·b15 가 같은 함정을 밟았다). DOM 은 그대로 보이므로 `b.js()` 로 읽는다.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_keyhelp")
FRUIT = "peach"
STEM = "210629-t1-01"
F1 = ""                                            # WebDriver 의 F1
ESC = ""

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

OPEN = "return !document.querySelector('#keyhelp').classList.contains('hidden')"

# 겹창에 **진짜로 뜬** 표를 그대로 읽어 온다
SHOWN = """return (function () {
  const rows = [].slice.call(document.querySelectorAll('#keyhelp table tbody tr'));
  return rows.map(function (tr) {
    return { key: [].slice.call(tr.children[0].querySelectorAll('kbd'))
                    .map(function (k) { return k.textContent; }).join('+'),
             ko: tr.children[1].textContent };
  });
})()"""

# 카드가 화면 안에 다 들어왔나 · 표 끝까지 닿나
FIT = """return (function () {
  const card = document.querySelector('#keyhelp .tourcard');
  const body = document.querySelector('#keyhelp .keyhelp-body');
  const r = card.getBoundingClientRect();
  body.scrollTop = body.scrollHeight;                     // 끝까지 굴려 본다
  const rows = document.querySelectorAll('#keyhelp table tbody tr');
  const last = rows[rows.length - 1].getBoundingClientRect();
  const br = body.getBoundingClientRect();
  return { rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
           vw: window.innerWidth, vh: window.innerHeight,
           lastTop: Math.round(last.top), lastBottom: Math.round(last.bottom),
           bodyTop: Math.round(br.top), bodyBottom: Math.round(br.bottom),
           rows: rows.length };
})()"""


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5641)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "keyhelp")
    os.makedirs(shots, exist_ok=True)
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)

        # ── ⑧ 목록 화면에서도 듣는다 (편집 화면으로 가기 전에 먼저 본다) ──────────
        L.chk("⑧ 지금은 목록 화면이다",
              b.js("return !document.querySelector('#view-list').classList.contains('hidden')") is True)
        L.chk("① 처음에는 겹창이 숨어 있다", b.js(OPEN) is False)
        b.key(F1)
        time.sleep(0.4)
        L.chk("⑧ 목록 화면에서 F1 이 겹창을 연다", b.js(OPEN) is True)
        b.key(ESC)
        time.sleep(0.3)
        L.chk("⑧ 목록 화면에서 Esc 가 닫는다", b.js(OPEN) is False)

        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        time.sleep(1.0)
        L.chk("① 기본은 쉬움 모드다", b.js("return document.body.classList.contains('easy')") is True)

        # ── ② F1 로 열린다 ────────────────────────────────────────────────────
        t0 = time.time()
        b.key(F1)
        for _ in range(30):
            if b.js(OPEN):
                break
            time.sleep(0.05)
        dt = round(time.time() - t0, 2)
        L.chk("② F1 로 겹창이 열린다 (%s초)" % dt, b.js(OPEN) is True, dt)
        b.shot(os.path.join(shots, "01_f1_open.png"))

        # ── ③ 겹창의 표 ↔ UI.KEYS (한 줄도 어긋나면 안 된다) ────────────────────
        keys = L.ev(b, "UI.KEYS")
        shown = b.js(SHOWN)
        L.chk("③ 겹창의 표가 UI.KEYS 와 **줄 수**가 같다 (%d줄)" % len(shown),
              len(shown) == len(keys) and len(keys) >= 30, [len(shown), len(keys)])
        bad = []
        for i, (want, got) in enumerate(zip(keys, shown)):
            if want["key"] != got["key"] or want["ko"] != got["ko"]:
                bad.append([i, want["key"], got["key"], want["ko"], got["ko"]])
        L.chk("③ 겹창의 표가 UI.KEYS 와 **키·뜻 전부** 같다 (%d줄 대조)" % len(shown), not bad, bad)
        L.chk("③ 표에 F1 줄이 있다 — 겹창이 자기 여는 법을 스스로 적는다",
              any(r["key"] == "F1" for r in shown),
              [r["key"] for r in shown if r["key"].startswith("F")])
        L.chk("③ 키 칸은 <kbd> 로 그려진다 (%d개)" % len(shown),
              b.js("return document.querySelectorAll('#keyhelp table kbd').length") >= len(shown),
              b.js("return document.querySelectorAll('#keyhelp table kbd').length"))
        L.chk("③ 겹창이 화면 맨 앞이다 (가운데 점을 눌러도 뒤가 안 잡힌다)",
              b.js("const e=document.elementFromPoint(innerWidth/2, innerHeight/2);"
                   "return !!(e && e.closest('#keyhelp'))") is True)

        # ── ④ 열려 있는 동안 뒤의 단축키가 안 먹는다 ──────────────────────────
        was = dict(tool=L.ev(b, "S.tool"), s=L.ev(b, "S.view.s"), box=L.ev(b, "S.boxMode"),
                   act=L.ev(b, "(S.item && S.item.action) || ''"))
        for k in ("b", "e", "1", "3", "0", "x", "k", "q"):
            b.key(k)
            time.sleep(0.12)
        now = dict(tool=L.ev(b, "S.tool"), s=L.ev(b, "S.view.s"), box=L.ev(b, "S.boxMode"),
                   act=L.ev(b, "(S.item && S.item.action) || ''"))
        L.chk("④ 겹창이 떠 있는 동안 도구가 안 바뀐다 (%s)" % now["tool"],
              now["tool"] == was["tool"], [was["tool"], now["tool"]])
        L.chk("④ 배율도 안 바뀐다 (%s)" % now["s"], now["s"] == was["s"], [was["s"], now["s"]])
        L.chk("④ 상자 모드도 안 켜진다 (%s)" % now["box"], now["box"] == was["box"],
              [was["box"], now["box"]])
        L.chk("④ **판정이 나가지 않는다** (%r)" % now["act"], now["act"] == was["act"],
              [was["act"], now["act"]])
        L.chk("④ 겹창은 그대로 열려 있다", b.js(OPEN) is True)

        # ── ⑤ Esc 로 닫히고, 그 Esc 가 다각형을 지우지 않는다 ──────────────────
        #   Esc 는 원래 «그리던 다각형 취소» 다. 겹창을 닫는 Esc 가 그 일까지 하면,
        #   표를 잠깐 봤다는 이유로 찍어 둔 점이 통째로 날아간다.
        L.run(b, "S.poly = [[10,10],[60,10],[60,60]];")
        b.key(ESC)
        time.sleep(0.35)
        L.chk("⑤ Esc 로 겹창이 닫힌다", b.js(OPEN) is False)
        L.chk("⑤ 그 Esc 가 그리던 다각형을 안 지운다 (점 %s개)" % L.ev(b, "S.poly.length"),
              L.ev(b, "S.poly.length") == 3, L.ev(b, "S.poly"))
        b.key(ESC)                                        # 닫힌 뒤의 Esc 는 원래대로 다각형 취소
        time.sleep(0.3)
        L.chk("⑤ 닫힌 뒤의 Esc 는 전처럼 다각형을 취소한다 (점 %s개)" % L.ev(b, "S.poly.length"),
              L.ev(b, "S.poly.length") == 0, L.ev(b, "S.poly"))

        # ── ⑥ F1 토글 ────────────────────────────────────────────────────────
        b.key(F1)
        time.sleep(0.3)
        L.chk("⑥ F1 로 다시 열린다", b.js(OPEN) is True)
        b.key(F1)
        time.sleep(0.3)
        L.chk("⑥ F1 을 한 번 더 누르면 닫힌다 (토글)", b.js(OPEN) is False)

        # ── ⑦ ✕ 단추 · 바깥 클릭 ─────────────────────────────────────────────
        b.key(F1)
        time.sleep(0.3)
        b.click("#keyhelp-x")
        time.sleep(0.3)
        L.chk("⑦ ✕ 단추로 닫힌다", b.js(OPEN) is False)
        b.key(F1)
        time.sleep(0.3)
        b.js("const o=document.querySelector('#keyhelp');"
             "o.dispatchEvent(new MouseEvent('click',{bubbles:true}));")   # 바깥(어두운 데) 클릭
        time.sleep(0.3)
        L.chk("⑦ 바깥 어두운 데를 눌러도 닫힌다", b.js(OPEN) is False)

        # ── ⑨ 글자 칸에 커서가 있어도 F1 은 듣는다 · «?» 는 안 듣는다 ────────────
        b.js("document.querySelector('#who').focus()")
        time.sleep(0.2)
        b.key("?")
        time.sleep(0.4)
        L.chk("⑨ 글자 칸에서는 «?» 가 안 듣는다 (이름에 ? 를 적을 수 있어야 한다 · 회귀)",
              b.js("return document.querySelector('#tour').classList.contains('hidden')") is True)
        #   «?» 는 안 듣는 대신 **이름 칸에 글자로 들어간다** — 그게 맞다(사람 이름에 ? 를 쓸 일은
        #   없지만, 글자 칸은 글자를 받는 곳이다). F1 은 그 칸에 아무 자국도 남기면 안 된다.
        before = b.js("return document.querySelector('#who').value")
        b.key(F1)
        time.sleep(0.4)
        after = b.js("return document.querySelector('#who').value")
        L.chk("⑨ 글자 칸에 커서가 있어도 F1 은 듣는다 (F1 은 글자가 아니다)", b.js(OPEN) is True)
        L.chk("⑨ 그 F1 이 이름 칸을 한 글자도 안 건드렸다 (%r → %r)" % (before, after),
              after == before, [before, after])
        b.js("const w=document.querySelector('#who'); w.value=arguments[0]; w.blur();",
             (before or "").replace("?", ""))          # 시험이 찍은 «?» 를 치운다

        # ── ⑫ 화면 안에 다 들어오고 마지막 줄까지 닿는다 ───────────────────────
        f = b.js(FIT)
        L.chk("⑫ 카드가 화면 밖으로 안 나간다 %s (창 %d×%d)"
              % (f["rect"], f["vw"], f["vh"]),
              f["rect"][0] >= 0 and f["rect"][1] >= 0
              and f["rect"][0] + f["rect"][2] <= f["vw"]
              and f["rect"][1] + f["rect"][3] <= f["vh"], f)
        L.chk("⑫ 끝까지 굴리면 **마지막 줄**이 보이는 자리에 온다 (%d줄 · 밑 %d ≤ %d)"
              % (f["rows"], f["lastBottom"], f["bodyBottom"] + 1),
              f["lastTop"] >= f["bodyTop"] - 1 and f["lastBottom"] <= f["bodyBottom"] + 1, f)
        b.shot(os.path.join(shots, "02_scrolled_end.png"))
        b.key(ESC)
        time.sleep(0.3)

        # ── ⑩⑪ 안내 창과의 사이 ──────────────────────────────────────────────
        b.js("document.querySelector('#who').blur()")     # 글자 칸을 벗어나야 «?» 가 듣는다
        b.key("?")
        time.sleep(0.5)
        L.chk("⑪ «?» 로 안내 창이 열린다 (회귀)",
              b.js("return !document.querySelector('#tour').classList.contains('hidden')") is True)
        L.chk("⑪ 안내 창 아래 «단축키 한 장» 칸이 펴져 있다 (회귀)",
              b.js("return !!document.querySelector('.shortcut-panel').open") is True)
        L.chk("⑪ 그 칸의 표도 같은 줄 수다 (%d줄)" % len(keys),
              b.js("return document.querySelectorAll('.shortcut-panel table tbody tr').length") == len(keys),
              b.js("return document.querySelectorAll('.shortcut-panel table tbody tr').length"))
        b.key(F1)
        time.sleep(0.4)
        L.chk("⑩ 안내 창이 떠 있으면 F1 이 겹창을 안 연다 (두 장을 포개지 않는다)",
              b.js(OPEN) is False)
        L.chk("⑩ 그 F1 이 안내 창을 닫지도 않는다",
              b.js("return !document.querySelector('#tour').classList.contains('hidden')") is True)
        b.key(ESC)
        time.sleep(0.4)
        L.chk("⑩ Esc 는 전처럼 안내 창을 닫는다",
              b.js("return document.querySelector('#tour').classList.contains('hidden')") is True)
        b.key(F1)
        time.sleep(0.4)
        L.chk("⑩ 안내 창이 닫힌 뒤에는 F1 이 다시 연다", b.js(OPEN) is True)
        b.key(ESC)
        time.sleep(0.3)

        # ── ⑬ 전문가 모드 ────────────────────────────────────────────────────
        b.click("#easytgl")
        time.sleep(0.6)
        L.chk("⑬ 전문가 모드로 바뀌었다",
              b.js("return !document.body.classList.contains('easy')") is True)
        b.key(F1)
        time.sleep(0.4)
        f2 = b.js(FIT)
        L.chk("⑬ 전문가 모드에서도 F1 이 열리고 카드가 화면 안이다 %s" % (f2["rect"],),
              b.js(OPEN) is True
              and f2["rect"][1] >= 0 and f2["rect"][1] + f2["rect"][3] <= f2["vh"], f2)
        b.shot(os.path.join(shots, "03_pro_mode.png"))
        b.key(ESC)
        time.sleep(0.3)

        # ── ⑭ 붓질 회귀 + 콘솔 오류 ──────────────────────────────────────────
        b.key("b")
        time.sleep(0.3)
        L.chk("⑭ 겹창을 닫은 뒤에는 단축키가 다시 듣는다 (B → 붓)", L.ev(b, "S.tool") == "brush",
              L.ev(b, "S.tool"))
        before = L.ev(b, "S.undo.length")
        b.drag("#cv", 300, 300, 380, 360)
        time.sleep(0.6)
        L.chk("⑭ 붓질이 그대로 된다 (되돌리기 %s → %s칸)" % (before, L.ev(b, "S.undo.length")),
              L.ev(b, "S.undo.length") > before, [before, L.ev(b, "S.undo.length")])
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑭ 콘솔 오류 0개", not errs, errs)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        b.close()
        b = None

        # ── ⑬ 좁은(휴대폰) 폭 ────────────────────────────────────────────────
        #   ⚠ `L.browser(w=390)` 은 **390 이 되지 않는다.** 실측 innerWidth 500 —
        #     헤드리스 파이어폭스에 가장 좁은 창 크기가 있다. WebDriver 의 `window/rect` 로
        #     한 번 더 좁혀 보고, **잰 값을 그대로 이름에 적는다**(앞 라운드 b11·b15 는
        #     «휴대폰 폭 390» 이라고 적었지만 실제로는 500 이었다 — 재지 않고 적은 값이다).
        #     500 도 mobile.css 의 문턱(820px) 아래라 휴대폰 규칙은 전부 켜진다.
        b = L.browser(w=390, h=780, base="http://127.0.0.1:%d" % port)
        try:
            b._s("POST", "/window/rect", {"width": 390, "height": 780})
        except Exception:
            pass
        time.sleep(0.4)
        vw = b.js("return window.innerWidth")
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        L.chk("⑬ 좁은 창 — 실측 폭 %d (휴대폰 규칙 문턱 820 아래)" % vw, vw <= 820, vw)
        b.key(F1)
        time.sleep(0.5)
        L.chk("⑬ 좁은 창(%d)에서도 F1 이 연다" % vw, b.js(OPEN) is True)
        f3 = b.js(FIT)
        L.chk("⑬ 좁은 창(%d) — 카드가 좌우로 안 삐져 나간다 %s" % (f3["vw"], f3["rect"]),
              f3["rect"][0] >= 0 and f3["rect"][0] + f3["rect"][2] <= f3["vw"], f3)
        L.chk("⑬ 좁은 창(높이 %d) — 위아래도 화면 안이다" % f3["vh"],
              f3["rect"][1] >= 0 and f3["rect"][1] + f3["rect"][3] <= f3["vh"], f3)
        L.chk("⑬ 좁은 창 — 끝까지 굴리면 마지막 줄이 보인다 (밑 %d ≤ %d)"
              % (f3["lastBottom"], f3["bodyBottom"] + 1),
              f3["lastBottom"] <= f3["bodyBottom"] + 1, f3)
        b.shot(os.path.join(shots, "04_phone_narrow.png"))
        b.key(ESC)
        time.sleep(0.3)
        L.chk("⑬ 좁은 창에서도 Esc 로 닫힌다", b.js(OPEN) is False)
        b.close()
        b = None

        png = sorted(x for x in os.listdir(shots) if x.endswith(".png"))
        L.chk("화면 %d장을 남겼다 — %s" % (len(png), shots), len(png) == 4, png)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b16_f1_help")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
