# -*- coding: utf-8 -*-
"""b11 — **지금 배율이 늘 보이는가** (편의 U2).
작성: 2026-09-21

왜
  배율 %가 적히는 자리는 `#hud`(왼쪽 아래) 하나뿐이었는데 그 칸은
    · 쉬움 모드에서 **아예 숨고**(style.css `body.easy #hud`),
    · 마우스를 움직여야 갱신된다(main.js mousemove).
  그래서 ＋/－/맞춤 단추만 눌러 본 사람은 «내가 얼마나 당겼는지» 를 알 길이 없다.
  → 그림판 상태줄처럼, 확대 단추 바로 옆에 지금 배율을 늘 띄운다(`#zoompct`).

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 열기 전에는 자리도 차지하지 않는다
    ② 사진을 열면 숫자가 뜨고, 그 숫자가 `S.view.s` 와 맞는다
    ③ 확대 단추와 안 겹치고, 단추를 **가리지 않는다**(글자일 뿐이다)
    ④ ＋ 는 1.25배 · － 는 되돌아온다 — 숫자가 실제로 그만큼 바뀐다
    ⑤ 휠로 당겨도 숫자가 따라온다(몇 초 만에 따라오는지 실측)
    ⑥ «맞춤»·0 키 뒤 숫자가 fitView 값과 같다
    ⑦ **쉬움 모드에서도 보인다**(`#hud` 는 숨는데 이 칸은 남는다)
    ⑧ 전문가 모드에서 `#hud` 가 말하는 배율과 **같은 수**다(두 자리가 다른 말을 하면 안 된다)
    ⑨ 끝까지 당기고 끝까지 밀어도(30배·0.03배) 숫자가 어긋나지 않는다 · 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b10 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_zoompct")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 배율 칸이 지금 **화면에 어떻게 그려져 있나** — 있음/없음이 아니라 자리와 글자로 본다.
PCT = """
const e = document.querySelector('#zoompct');
if (!e) return null;
const r = e.getBoundingClientRect();
const cs = getComputedStyle(e);
return { text: e.textContent, disp: cs.display, color: cs.color, pe: cs.pointerEvents,
         x: Math.round(r.left), y: Math.round(r.top),
         w: Math.round(r.width), h: Math.round(r.height), title: e.title };
"""

# 화면이 말하는 글자 · 코드가 들고 있는 배율로 만든 글자 — 둘이 같아야 한다.
# `S` 는 페이지의 전역이라 webdriver 의 execute 에서는 안 보인다 → L.ev(window.eval) 로 읽는다.
SAYS = ("{ shown: document.querySelector('#zoompct').textContent,"
        "  want: (S.view.s * 100).toFixed(0) + '%', s: S.view.s }")


def pct(b):
    return b.js(PCT)


def says(b):
    return L.ev(b, SAYS)


def num(t):
    """«125%» → 125 (숫자가 아니면 None)"""
    try:
        return int((t or "").replace("%", ""))
    except ValueError:
        return None


def wait_match(b, secs=3.0):
    """화면 글자가 지금 배율과 맞을 때까지 — 걸린 초(안 맞으면 None)."""
    t0 = time.time()
    while time.time() - t0 < secs:
        d = says(b)
        if d["shown"] == d["want"]:
            return round(time.time() - t0, 2)
        time.sleep(0.02)
    return None


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5571)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "zoompct")
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        os.makedirs(shots, exist_ok=True)

        # ── ① 사진을 열기 전 ────────────────────────────────────────────
        p0 = pct(b)
        L.chk("① 배율 칸이 화면에 있다(id 는 index.html 것)", p0 is not None, p0)
        L.chk("① 사진을 열기 전에는 글자가 없다", p0 and p0["text"] == "", p0)

        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))

        # ── ② 열면 숫자가 뜬다 ──────────────────────────────────────────
        took = wait_match(b)
        d = says(b)
        L.chk("② 숫자가 떴다", num(d["shown"]) is not None, d)
        L.chk("② 그 숫자가 지금 배율과 같다(%s)" % d["want"], took is not None, d)
        p1 = pct(b)
        L.chk("② 진짜로 그려져 있다(넓이·높이가 0 이 아니다)",
              p1 and p1["w"] > 0 and p1["h"] > 0 and p1["disp"] != "none", p1)
        L.chk("② 풍선말에 이 칸이 무엇인지 적혀 있다", "배율" in (p1.get("title") or ""), p1.get("title"))

        # ── ③ 자리 — 확대 단추 옆 · 단추를 안 가린다 ──────────────────────
        pos = b.js("""
          const pc = document.querySelector('#zoompct').getBoundingClientRect();
          const zo = document.querySelector('#zoomout').getBoundingClientRect();
          const zf = document.querySelector('#zoomfit').getBoundingClientRect();
          const cw = document.querySelector('#canvaswrap').getBoundingClientRect();
          const hitOut = document.elementFromPoint(zo.left + zo.width / 2, zo.top + zo.height / 2);
          const hitFit = document.elementFromPoint(zf.left + zf.width / 2, zf.top + zf.height / 2);
          const over = !(pc.right <= zo.left || pc.left >= zo.right);
          return { gap: Math.round(zo.left - pc.right), over: over,
                   inwrap: pc.left >= cw.left && pc.right <= cw.right
                           && pc.top >= cw.top && pc.bottom <= cw.bottom,
                   mid: Math.round(Math.abs((pc.top + pc.bottom) / 2 - (zo.top + zo.bottom) / 2)),
                   hitOut: hitOut ? hitOut.id : null, hitFit: hitFit ? hitFit.id : null };
        """)
        L.chk("③ 확대 단추 바로 왼쪽이다(10px 안)", 0 <= pos.get("gap", 999) <= 10, pos)
        L.chk("③ 단추와 겹치지 않는다", pos.get("over") is False, pos)
        L.chk("③ 단추와 세로 가운데가 맞는다(2px 안)", pos.get("mid", 99) <= 2, pos)
        L.chk("③ 사진 칸 안에 들어 있다", pos.get("inwrap") is True, pos)
        L.chk("③ － 단추를 가리지 않는다(글자일 뿐이다)", pos.get("hitOut") == "zoomout", pos)
        L.chk("③ «맞춤» 단추도 가리지 않는다", pos.get("hitFit") == "zoomfit", pos)
        L.chk("③ 눌리지 않는 글자다(pointer-events: none)", p1.get("pe") == "none", p1)

        # ── ④ ＋ 1.25배 · － 되돌아오기 ──────────────────────────────────
        before = says(b)
        b.js("document.querySelector('#zoomin').click();")
        L.chk("④ ＋ 뒤에도 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        after = says(b)
        L.chk("④ ＋ 가 1.25배다(%s → %s)" % (before["shown"], after["shown"]),
              abs(after["s"] / before["s"] - 1.25) < 1e-6, [before, after])
        L.chk("④ 숫자가 실제로 커졌다", num(after["shown"]) > num(before["shown"]), [before, after])
        b.js("document.querySelector('#zoomout').click();")
        L.chk("④ － 뒤에도 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        L.chk("④ － 로 아까 숫자로 돌아왔다", says(b)["shown"] == before["shown"], [before, says(b)])
        b.shot(os.path.join(shots, "zoompct_easy.png"))

        # ── ⑤ 휠 ────────────────────────────────────────────────────────
        prev = says(b)
        b.js("""
          const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
          cv.dispatchEvent(new WheelEvent('wheel', { deltaY: -200, bubbles: true, cancelable: true,
            clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 }));
        """)
        wtook = wait_match(b)
        L.chk("⑤ 휠로 당기면 숫자가 따라온다", wtook is not None and wtook <= 1.0, wtook)
        L.chk("⑤ 실제로 더 커졌다(%s → %s)" % (prev["shown"], says(b)["shown"]),
              says(b)["s"] > prev["s"], [prev, says(b)])

        # ── ⑥ 맞춤 · 0 키 ───────────────────────────────────────────────
        b.js("document.querySelector('#zoomfit').click();")
        L.chk("⑥ «맞춤» 뒤 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        fit = says(b)
        b.js("document.querySelector('#zoomin').click();")
        wait_match(b)
        b.key("0")
        L.chk("⑥ 0 키 뒤 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        L.chk("⑥ 0 키가 «맞춤» 과 같은 숫자로 돌아온다(%s)" % fit["shown"],
              says(b)["shown"] == fit["shown"], [fit, says(b)])

        # ── ⑦ 쉬움 모드 — #hud 는 숨는데 이 칸은 남는다 ────────────────────
        easy = b.js("return document.body.classList.contains('easy')")
        L.chk("⑦ 지금은 쉬움 모드다(기본값)", easy is True, easy)
        hud = b.js("return getComputedStyle(document.querySelector('#hud')).display")
        L.chk("⑦ 쉬움 모드에서 #hud 는 숨어 있다(그래서 이 칸이 필요하다)", hud == "none", hud)
        pe = pct(b)
        L.chk("⑦ 그래도 배율 칸은 보인다", pe and pe["disp"] != "none" and pe["w"] > 0, pe)
        L.chk("⑦ 쉬움 모드에서도 숫자가 배율과 같다", wait_match(b) is not None, says(b))

        # ── ⑧ 전문가 모드 — #hud 와 같은 수인가 ──────────────────────────
        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.6)
        L.chk("⑧ 전문가 모드로 바뀌었다",
              b.js("return document.body.classList.contains('easy')") is False)
        # #hud 는 마우스를 움직여야 갱신된다 — 붓질이 되지 않게 단추 없이 mousemove 만 보낸다
        b.js("""
          const r = document.querySelector('#cv').getBoundingClientRect();
          window.dispatchEvent(new MouseEvent('mousemove', { bubbles: true,
            clientX: Math.round(r.left + r.width / 2), clientY: Math.round(r.top + r.height / 2) }));
        """)
        time.sleep(0.3)
        both = b.js("""
          const h = document.querySelector('#hud').textContent;
          const m = h.match(/배율\\s*(\\d+)%/);
          return { hud: h, hudpct: m ? m[1] + '%' : null,
                   pct: document.querySelector('#zoompct').textContent };
        """)
        L.chk("⑧ #hud 가 배율을 말한다", both.get("hudpct") is not None, both)
        L.chk("⑧ 두 자리가 **같은 수**를 말한다", both.get("hudpct") == both.get("pct"), both)
        L.chk("⑧ 전문가 모드에서도 배율 칸이 보인다",
              (pct(b) or {}).get("disp") != "none", pct(b))
        L.chk("⑧ 붓질이 되지 않았다(마우스만 움직였다)", L.ev(b, "!!S.edDirty") is False)
        b.shot(os.path.join(shots, "zoompct_adv.png"))

        # ── ⑨ 끝까지 당기고 끝까지 밀기 ──────────────────────────────────
        for _ in range(30):
            b.js("document.querySelector('#zoomin').click();")
        L.chk("⑨ 최대(30배)까지 당겨도 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        L.chk("⑨ 최대는 3000% 다", says(b)["shown"] == "3000%", says(b))
        for _ in range(60):
            b.js("document.querySelector('#zoomout').click();")
        L.chk("⑨ 최소(0.03배)까지 밀어도 숫자가 배율과 같다", wait_match(b) is not None, says(b))
        L.chk("⑨ 최소는 3% 다", says(b)["shown"] == "3%", says(b))
        BTN = ("const r = document.querySelector('#zoomout').getBoundingClientRect();"
               "return { x: Math.round(r.left), y: Math.round(r.top) };")
        wide, wbtn = pct(b), b.js(BTN)                    # 글자가 제일 긴 «3%» 직전 상태
        b.js("document.querySelector('#zoomfit').click();")
        wait_match(b)
        narrow, nbtn = pct(b), b.js(BTN)
        L.chk("⑨ 숫자 길이가 바뀌어도 확대 단추 자리가 안 밀린다(%s → %s)"
              % (wide["text"], narrow["text"]), wbtn == nbtn, [wbtn, nbtn])
        L.chk("⑨ 칸은 사진 칸 안에 그대로 있다",
              narrow["x"] + narrow["w"] <= wide["x"] + wide["w"] + 1, [wide, narrow])
        # 쉬움 모드로 되돌려 둔다(다음 사람이 쓰던 대로)
        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.4)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑨ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        b.shot(os.path.join(shots, "zoompct_fit.png"))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b11_zoompct")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
