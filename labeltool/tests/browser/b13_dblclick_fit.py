# -*- coding: utf-8 -*-
"""b13 — **캔버스 더블클릭이 화면 맞춤으로 가는가** (편의 U4).
작성: 2026-09-21

왜
  휠로 당겨 놓고 **되돌아오는 길**(0 키·«맞춤» 단추)을 모르는 사람이 많다. 윈도우 사진 뷰어처럼
  «두 번 누르면 처음 크기» 를 얹었다. 다만 이 툴의 캔버스는 **그림을 그리는 자리**라서, 아무 데서나
  맞춤을 걸면 자동채움을 두 번 누른 사람·붓으로 점을 두 개 찍은 사람의 확대가 말없이 풀린다.
  그래서 «지금 그리는 중이 아님» 이 보장되는 두 자리에서만 듣게 했다 —
  ① 사진 밖 회색 여백(어느 도구에서나) ② ✋이동 도구나 Space(보기만 하는 손짓).

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 열고 «맞춤» 배율(0 키)을 자로 잰다
    ② 확대한 뒤 ✋ 도구로 사진 한가운데를 **진짜 더블클릭** → 맞춤값으로 돌아온다
    ③ 붓 도구로 **사진 위**를 더블클릭하면 배율이 꿈쩍도 안 한다(그리기가 먼저다)
    ④ 같은 붓 도구라도 **사진 밖 회색 여백**을 더블클릭하면 맞춤으로 돌아온다
    ⑤ 다각형을 찍는 중에는 건드리지 않는다
    ⑥ Space 를 누른 채 사진 위를 더블클릭하면 맞춤
    ⑦ 상자 모드에서도 여백 더블클릭은 맞춤이고, 상자가 생기거나 «저장 안 됨» 이 켜지지 않는다
    ⑧ 1초 안내·배율 %(U2)·콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b12 와 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_dblfit")
FRUIT = "peach"
STEM = "210629-t1-01"

SPACE = " "                                              # WebDriver 가 code "Space" 로 바꿔 준다
ESC = ""

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 사진 **밖** 회색 여백 한 점(캔버스 왼쪽 위 기준 CSS 화소). 네 쪽 여백 중 가장 넓은 쪽을 고르고,
# 창 밖으로 나가지 않게 세로를 잘라 준다(b12 가 «out of bounds of viewport» 로 죽었던 그 함정).
# ⚠ `S` 는 쪽의 전역이라 `b.js()` 안에서는 안 보인다 → `L.ev()`(window.eval) 로 부른다.
GRAYPT = """(function () {
window.scrollTo(0, 0);                       // Space 키가 쪽을 내렸을 수 있다 — 재기 전에 맨 위로
const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
const W = r.width, H = r.height, s = S.view.s;
const m = [
  { v: S.view.tx,                        x: S.view.tx / 2,                        y: H / 2 },
  { v: W - (S.view.tx + S.W * s),        x: (W + S.view.tx + S.W * s) / 2,        y: H / 2 },
  { v: S.view.ty,                        x: W / 2,                                y: S.view.ty / 2 },
  { v: H - (S.view.ty + S.H * s),        x: W / 2,                                y: (H + S.view.ty + S.H * s) / 2 }
].sort((a, b) => b.v - a.v)[0];
const maxY = Math.min(H, window.innerHeight - r.top) - 8;
const y = Math.max(8, Math.min(maxY, Math.round(m.y)));
const x = Math.max(4, Math.min(W - 4, Math.round(m.x)));
// 정말 사진 밖인지 여기서 한 번 더 재서 같이 돌려준다(시험이 짐작하지 않게)
const ix = (x - S.view.tx) / s, iy = (y - S.view.ty) / s;
return { x: x, y: y, margin: Math.round(m.v),
         outside: (ix < 0 || iy < 0 || ix >= S.W || iy >= S.H) };
})()"""

# 지금 칠해져 있는 화소 수 — «여백을 눌렀으니 한 화소도 안 바뀌었다» 를 자로 재는 데 쓴다
PIXSUM = "(function(){let n=0;const e=S.ed;for(let i=0;i<e.length;i++)if(e[i])n++;return n;})()"

# 캔버스 한가운데가 사진 **위**인지 (④·⑥ 에서 «그리기 자리» 임을 못박는다)
CENTERPT = """(function () {
window.scrollTo(0, 0);
const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
const maxY = Math.min(r.height, window.innerHeight - r.top) - 8;
const x = Math.round(r.width / 2), y = Math.round(Math.min(r.height / 2, maxY));
const ix = (x - S.view.tx) / S.view.s, iy = (y - S.view.ty) / S.view.s;
return { x: x, y: y, onphoto: (ix >= 0 && iy >= 0 && ix < S.W && iy < S.H) };
})()"""


def dbl(b, x, y):
    """#cv 위 (x,y) 를 **진짜 두 번** 누른다(브라우저가 dblclick 을 만들어 주게).
       ff.py 에는 더블클릭이 없고, 공용 파일이라 건드리지 않는다(b12 의 chord() 와 같은 판단)."""
    r = b.js("const r=document.querySelector('#cv').getBoundingClientRect();return [r.left,r.top]")
    X, Y = int(r[0] + x), int(r[1] + y)
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"}, "actions": [
             {"type": "pointerMove", "duration": 0, "x": X, "y": Y},
             {"type": "pointerDown", "button": 0}, {"type": "pointerUp", "button": 0},
             {"type": "pause", "duration": 40},
             {"type": "pointerDown", "button": 0}, {"type": "pointerUp", "button": 0}]}]})
    time.sleep(0.25)


def hold(b, k, down=True):
    b._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb", "actions": [
        {"type": "keyDown" if down else "keyUp", "value": k}]}]})
    time.sleep(0.1)


def view(b):
    """지금 보고 있는 자리 — 배율과 밀린 양까지. 소수 넷째 자리에서 끊어 견준다."""
    v = L.ev(b, "[S.view.s, S.view.tx, S.view.ty]")
    return [round(x, 4) for x in v]


def zoom(b, sel, n):
    for _ in range(n):
        b.click(sel)
        time.sleep(0.15)


def flashtext(b):
    return b.js("const e = document.querySelector('#saveflash');"
                "return e ? { text: e.textContent, bad: e.classList.contains('flashbad') } : null")


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5591)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "dblfit")
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        os.makedirs(shots, exist_ok=True)

        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        time.sleep(1.0)

        # ── ① 맞춤 배율을 0 키로 자로 잰다 ────────────────────────────────
        b.key("0")
        time.sleep(0.3)
        FIT = view(b)
        L.chk("① 0 키가 잡아 준 «맞춤» 배율을 쟀다 (%s%%)" % round(FIT[0] * 100),
              FIT[0] > 0, FIT)

        # ── ② 확대한 뒤 ✋ 도구로 사진 한가운데 더블클릭 ────────────────────
        zoom(b, "#zoomin", 3)
        big = view(b)
        L.chk("② ＋ 를 세 번 눌러 확대됐다 (%s%% → %s%%)"
              % (round(FIT[0] * 100), round(big[0] * 100)), big[0] > FIT[0] * 1.5, [FIT, big])
        L.run(b, "UI.setTool('pan')")
        time.sleep(0.2)
        L.chk("② ✋ 이동 도구가 켜졌다", L.ev(b, "!!S.panTool") is True)
        c = L.ev(b, CENTERPT)
        L.chk("② 누를 자리는 사진 **위**다(그리기 자리)", c and c["onphoto"] is True, c)
        b.shot(os.path.join(shots, "1_zoomed.png"))
        t0 = time.time()
        dbl(b, c["x"], c["y"])
        took = round(time.time() - t0, 2)
        now = view(b)
        L.chk("② 더블클릭 한 번에 배율이 맞춤값으로 돌아왔다", now[0] == FIT[0], [FIT, now])
        L.chk("② 밀린 자리까지 0 키와 «숫자 그대로» 같다", now == FIT, [FIT, now])
        f = flashtext(b)
        L.chk("② «화면에 맞췄습니다» 라고 알린다",
              f and "화면에 맞췄습니다" in f["text"], f)
        L.chk("② 경고색이 아니다(1초 안내다)", f and f["bad"] is False, f)
        pct = b.js("const e=document.querySelector('#zoompct');return e?e.textContent:null")
        L.chk("② 확대바의 배율 %% 도 같은 수를 말한다(U2 회귀)",
              pct == "%d%%" % int(FIT[0] * 100 + 0.5), [pct, FIT[0]])
        print("   실측 — 더블클릭에서 맞춤까지 %s초" % took)
        b.shot(os.path.join(shots, "2_fitted.png"))
        time.sleep(1.1)                                   # 1초 안내가 스스로 사라지기를 기다린다
        # clearFlash() 는 칸을 지우는 것이 아니라 **글자를 비운다**(api.js paintFlash("")) →
        # 요소가 없어지기를 기다리면 안 된다. 글자가 비었고 «확인» 단추가 없는 것을 본다.
        f = flashtext(b)
        L.chk("② 안내는 1초 뒤 스스로 사라진다(«확인» 을 눌러야 하는 실패 띠가 아니다)",
              f is not None and f["text"] == "", f)
        L.chk("② 1초 안내에는 «확인» 단추가 붙지 않았다(S2 회귀)",
              b.js("return !document.querySelector('#saveflash .flashok')") is True)

        # ── ③ 붓 도구 · 사진 **위** — 그리기가 먼저다 ───────────────────────
        L.run(b, "UI.setTool('brush')")
        zoom(b, "#zoomin", 3)
        keep = view(b)
        c = L.ev(b, CENTERPT)
        L.chk("③ 누를 자리는 사진 위다", c and c["onphoto"] is True, c)
        L.run(b, "S.undo.length = 0")                     # 20칸 한도에 걸려 «늘었나» 를 못 세는 일이 없게
        dbl(b, c["x"], c["y"])
        L.chk("③ 붓으로 사진 위를 두 번 눌러도 배율이 꿈쩍 않는다", view(b) == keep, [keep, view(b)])
        L.chk("③ 그 두 번은 붓 손잡이까지 그대로 갔다(되돌리기에 두 칸)",
              L.ev(b, "S.undo.length") == 2, L.ev(b, "S.undo.length"))

        # ── ④ 같은 붓 도구 · 사진 **밖** 회색 여백 ──────────────────────────
        b.key("0")
        time.sleep(0.3)
        zoom(b, "#zoomout", 2)
        small = view(b)
        g = L.ev(b, GRAYPT)
        L.chk("④ 회색 여백이 넉넉하다(%s화소)" % (g and g["margin"]), g and g["margin"] >= 20, g)
        L.chk("④ 그 자리는 정말 사진 밖이다", g and g["outside"] is True, g)
        pix = L.ev(b, PIXSUM)
        dbl(b, g["x"], g["y"])
        L.chk("④ 붓을 쥐고도 여백 더블클릭이면 맞춤으로 돌아온다 (%s%% → %s%%)"
              % (round(small[0] * 100), round(view(b)[0] * 100)), view(b) == FIT, [small, view(b)])
        L.chk("④ 여백을 눌렀으니 한 화소도 안 칠해졌다 (%s개 그대로)" % pix,
              L.ev(b, PIXSUM) == pix, [pix, L.ev(b, PIXSUM)])
        b.shot(os.path.join(shots, "3_gray.png"))

        # ── ⑤ 다각형을 찍는 중이면 건드리지 않는다 ──────────────────────────
        L.run(b, "UI.setTool('polyadd')")
        zoom(b, "#zoomout", 2)
        keep = view(b)
        g = L.ev(b, GRAYPT)
        dbl(b, g["x"], g["y"])
        L.chk("⑤ 다각형 점 두 개가 찍혔다", L.ev(b, "S.poly.length") == 2, L.ev(b, "S.poly.length"))
        L.chk("⑤ 찍는 중에는 화면이 움직이지 않는다", view(b) == keep, [keep, view(b)])
        b.key(ESC)
        time.sleep(0.2)
        L.chk("⑤ Esc 로 다각형을 치웠다", L.ev(b, "S.poly.length") == 0)
        L.run(b, "UI.setTool('brush')")

        # ── ⑥ Space 를 누른 채 사진 위 더블클릭 ─────────────────────────────
        b.key("0")
        time.sleep(0.3)
        zoom(b, "#zoomin", 3)
        hold(b, SPACE, True)                              # Space 를 먼저 잡고 **그다음에** 잰다
        L.chk("⑥ Space 를 잡고 있다", L.ev(b, "!!S.spaceDown") is True)
        c = L.ev(b, CENTERPT)                                # (쪽이 내려갔으면 여기서 맨 위로 되돌린다)
        L.chk("⑥ 누를 자리는 사진 위다", c and c["onphoto"] is True, c)
        dbl(b, c["x"], c["y"])
        got = view(b)
        hold(b, SPACE, False)
        L.chk("⑥ Space + 더블클릭도 맞춤이다", got == FIT, [FIT, got])
        L.chk("⑥ Space 를 놓았다", L.ev(b, "!!S.spaceDown") is False)

        # ── ⑦ 상자 모드 — 여백 더블클릭이 상자를 만들지 않는다 ───────────────
        b.key("x")
        time.sleep(0.4)
        L.chk("⑦ 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        nb = L.ev(b, "S.boxes.length")
        bd = L.ev(b, "!!S.bDirty")
        zoom(b, "#zoomout", 2)
        g = L.ev(b, GRAYPT)
        L.chk("⑦ 그 자리는 사진 밖이다", g and g["outside"] is True, g)
        dbl(b, g["x"], g["y"])
        L.chk("⑦ 상자 모드에서도 여백 더블클릭은 맞춤이다", view(b) == FIT, [FIT, view(b)])
        L.chk("⑦ 상자가 생기지 않았다 (%d개 그대로)" % nb,
              L.ev(b, "S.boxes.length") == nb, L.ev(b, "S.boxes.length"))
        L.chk("⑦ «저장 안 됨» 이 켜지지 않았다",
              L.ev(b, "!!S.bDirty") is bd, L.ev(b, "!!S.bDirty"))
        b.key("x")
        time.sleep(0.3)
        L.chk("⑦ 상자 모드를 도로 껐다", L.ev(b, "!!S.boxMode") is False)

        # ── ⑧ 콘솔 ────────────────────────────────────────────────────────
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑧ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        b.shot(os.path.join(shots, "4_end.png"))
        # 저장 안 한 것을 남긴 채 창을 닫으면 beforeunload 가 붙잡는다(③ 에서 두 점을 칠했다)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b13_dblclick_fit")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
