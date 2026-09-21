# -*- coding: utf-8 -*-
"""b14 — **도구마다 커서가 달라지는가** (편의 U5).
작성: 2026-09-21

왜
  커서는 지금까지 세 가지뿐이었다 — ✋이동만 `grab`, 지우개만 `cell`, **나머지 전부** `crosshair`.
  붓·다각형·자동채움·상자를 오가도 손끝이 하나도 안 바뀌었다. 특히 상자 «고르기» 는 풍선말로만
  «모서리로 크기를 바꿉니다» 라고 할 뿐, 손잡이가 어디까지인지 화면에 아무 표시가 없었다
  (판정 반경 bHandleR 은 배율·상자 크기에 따라 변해서 눈으로는 가늠이 안 된다).

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 마스크 도구 일곱을 **단축키로** 돌며 `#cv` 의 커서를 자로 잰다(getComputedStyle)
    ② 붓·지우개·다각형·이동이 서로 **다른 값**인가
    ③ ✋ 로 **실제로 끄는 동안** 은 `grabbing` 이고 놓으면 `grab` 으로 돌아온다
    ④ Space 를 누르고 있으면 어느 도구에서나 `grab`
    ⑤ 상자 모드 — 그리기는 십자, 고르기는 빈 곳 `default`·상자 위 `move`·모서리 `↘↖`·`↗↙`
    ⑥ 끄는 중에는 잡은 대로(옮기기 `move` · 크기조절은 그 모서리)
    ⑦ 번호 편집은 지금 그대로 `crosshair` (회귀)
    ⑧ 값이 그대로면 DOM 을 한 글자도 안 건드린다(1초 동안 마우스를 흔들며 style 쓰기 횟수 0)
    ⑨ 콘솔 오류 0 · 도구를 돌린 뒤에도 붓질이 그대로 된다(회귀)
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b13 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_cursor")
FRUIT = "peach"
STEM = "210629-t1-01"

SPACE = ""                                         # WebDriver 가 code "Space" 로 바꿔 준다

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 사진(이미지) 좌표 → 캔버스 왼쪽 위 기준 CSS 화소. 창 밖으로 나가지 않게 잘라 준다
# (b12 가 «Move target is out of bounds of viewport» 로 죽었던 그 함정 — 캔버스 위쪽이 64px).
# ⚠ `S` 는 쪽의 전역이라 `b.js()` 안에서는 안 보인다 → `L.ev()`(window.eval) 로 부른다(b13 과 같다).
TOSCREEN = """(function (ix, iy) {
const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
const x = ix * S.view.s + S.view.tx, y = iy * S.view.s + S.view.ty;
const maxY = Math.min(r.height, window.innerHeight - r.top) - 6;
return { x: Math.round(Math.max(4, Math.min(r.width - 4, x))),
         y: Math.round(Math.max(4, Math.min(maxY, y))),
         cut: (y > maxY || y < 4 || x < 4 || x > r.width - 4) };
})(%r, %r)"""


def cur(b):
    """지금 `#cv` 에 실제로 그려지는 커서 한 낱말."""
    return b.js("return getComputedStyle(document.querySelector('#cv')).cursor")


def screen(b, ix, iy):
    return L.ev(b, TOSCREEN % (float(ix), float(iy)))


def act(b, actions):
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"}, "actions": actions}]})


def move(b, x, y):
    """#cv 위 (x,y) 로 마우스를 **진짜** 옮긴다 (ff.py 에는 이동만 하는 손잡이가 없다.
       공용 파일이라 건드리지 않는다 — b12 의 chord()·b13 의 dbl() 과 같은 판단)."""
    r = b.js("const r=document.querySelector('#cv').getBoundingClientRect();return [r.left,r.top]")
    act(b, [{"type": "pointerMove", "duration": 0, "x": int(r[0] + x), "y": int(r[1] + y)}])
    time.sleep(0.2)                                      # 다음 그림 한 장에서 커서가 따라온다


def press_move(b, x0, y0, x1, y1):
    """(x0,y0) 에서 누른 채 (x1,y1) 까지 끈다. **떼지 않는다** — 끄는 중의 커서를 재려고."""
    r = b.js("const r=document.querySelector('#cv').getBoundingClientRect();return [r.left,r.top]")
    act(b, [{"type": "pointerMove", "duration": 0, "x": int(r[0] + x0), "y": int(r[1] + y0)},
            {"type": "pointerDown", "button": 0},
            {"type": "pointerMove", "duration": 80, "x": int(r[0] + x1), "y": int(r[1] + y1)}])
    time.sleep(0.25)


def release(b):
    act(b, [{"type": "pointerUp", "button": 0}])
    time.sleep(0.25)


def hold(b, k, down=True):
    b._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb", "actions": [
        {"type": "keyDown" if down else "keyUp", "value": k}]}]})
    time.sleep(0.15)


def tool_by_key(b, k, want):
    b.key(k)
    time.sleep(0.25)
    return L.ev(b, "S.tool"), cur(b)


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5601)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "cursor")
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
        b.key("0")
        time.sleep(0.3)

        # ── ① 마스크 도구 일곱을 단축키로 돌며 커서를 잰다 ────────────────────
        WANT = [("b", "brush", "crosshair"), ("e", "erase", "cell"),
                ("p", "polyadd", "copy"), ("o", "polysub", "copy"),
                ("f", "smartadd", "pointer"), ("g", "smartsub", "pointer")]
        got = {}
        for k, tool, want in WANT:
            t, c = tool_by_key(b, k, want)
            got[tool] = c
            L.chk("① %s 키 → %s 도구 · 커서 «%s»" % (k.upper(), tool, c),
                  t == tool and c == want, [t, c, want])
        L.run(b, "UI.setTool('pan')")
        time.sleep(0.25)
        got["pan"] = cur(b)
        L.chk("① ✋ 이동 → 커서 «grab»",
              L.ev(b, "!!S.panTool") is True and got["pan"] == "grab", got["pan"])
        b.shot(os.path.join(shots, "1_pan.png"))

        # ── ② 붓·지우개·다각형·이동이 서로 다른가 ────────────────────────────
        four = [got["brush"], got["erase"], got["polyadd"], got["pan"]]
        L.chk("② 붓·지우개·다각형·이동이 서로 **다른** 커서다 (%s)" % " · ".join(four),
              len(set(four)) == 4, four)
        L.chk("② 자동채움도 붓과 다르다(같은 칸에 나란히 있는 도구다)",
              got["smartadd"] != got["brush"], [got["smartadd"], got["brush"]])

        # ── ③ 실제로 끄는 동안은 grabbing ────────────────────────────────────
        a = screen(b, L.ev(b, "S.W") * 0.4, L.ev(b, "S.H") * 0.4)
        c2 = screen(b, L.ev(b, "S.W") * 0.55, L.ev(b, "S.H") * 0.5)
        press_move(b, a["x"], a["y"], c2["x"], c2["y"])
        during = cur(b)
        L.chk("③ ✋ 로 끄는 **동안** 은 쥔 손 «grabbing»", during == "grabbing", during)
        L.chk("③ 정말 끌고 있었다(S.panning)", L.ev(b, "!!S.panning") is True)
        release(b)
        L.chk("③ 손을 떼면 다시 «grab»", cur(b) == "grab", cur(b))

        # ── ④ Space 를 잡고 있으면 어느 도구에서나 grab ──────────────────────
        b.key("b")
        time.sleep(0.25)
        L.chk("④ 붓으로 돌아왔다(«crosshair»)", cur(b) == "crosshair", cur(b))
        hold(b, SPACE, True)
        time.sleep(0.25)
        L.chk("④ Space 를 잡고 있다", L.ev(b, "!!S.spaceDown") is True)
        L.chk("④ 붓이어도 Space 중에는 «grab»", cur(b) == "grab", cur(b))
        hold(b, SPACE, False)
        time.sleep(0.3)
        L.chk("④ Space 를 놓으면 붓 커서로 돌아온다", cur(b) == "crosshair", cur(b))

        # ── ⑤ 상자 모드 ─────────────────────────────────────────────────────
        b.key("x")
        time.sleep(0.5)
        L.chk("⑤ 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        L.run(b, "S.boxes = []; S.bsel = -1; S.bundo = []; S.bredo = []; S.dirty = true")
        time.sleep(0.3)
        L.chk("⑤ 상자 «그리기» 는 십자다", cur(b) == "crosshair", [cur(b), L.ev(b, "S.btool")])
        # 네모 하나를 **진짜 끌어서** 그린다 (캔버스 위쪽 64px → 화면 y 는 618 까지만 쓴다)
        b.drag("#cv", 330, 200, 470, 330)
        time.sleep(0.4)
        nb = L.ev(b, "S.boxes.length")
        L.chk("⑤ 네모 하나를 진짜로 그렸다", nb == 1, nb)
        xy = L.ev(b, "S.boxes[0].xyxy")
        L.chk("⑤ 그린 네모가 고른 상태다(손잡이가 보인다)", L.ev(b, "S.bsel") == 0, L.ev(b, "S.bsel"))
        b.key("v")
        time.sleep(0.3)
        L.chk("⑤ V 로 «고르기·옮기기» 로 바꿨다", L.ev(b, "S.btool") == "pick", L.ev(b, "S.btool"))

        far = screen(b, max(4, xy[0] - 260), max(4, xy[1] - 120))
        move(b, far["x"], far["y"])
        L.chk("⑤ 상자 밖(빈 곳)에서는 화살표 «default»", cur(b) == "default",
              [cur(b), L.ev(b, "S.cursor")])
        mid = screen(b, (xy[0] + xy[2]) / 2, (xy[1] + xy[3]) / 2)
        move(b, mid["x"], mid["y"])
        L.chk("⑤ 상자 **안** 에서는 옮기기 «move»", cur(b) == "move", cur(b))
        nw = screen(b, xy[0], xy[1])
        move(b, nw["x"], nw["y"])
        L.chk("⑤ 왼쪽 위 모서리에서는 «nwse-resize»", cur(b) == "nwse-resize",
              [cur(b), L.ev(b, "UI.hitHandle(S.bsel, S.cursor[0], S.cursor[1])")])
        ne = screen(b, xy[2], xy[1])
        move(b, ne["x"], ne["y"])
        L.chk("⑤ 오른쪽 위 모서리에서는 «nesw-resize»", cur(b) == "nesw-resize",
              [cur(b), L.ev(b, "UI.hitHandle(S.bsel, S.cursor[0], S.cursor[1])")])
        b.shot(os.path.join(shots, "2_box_handle.png"))

        # ── ⑥ 끄는 중에는 잡은 대로 ─────────────────────────────────────────
        press_move(b, mid["x"], mid["y"], mid["x"] + 30, mid["y"] + 20)
        L.chk("⑥ 상자를 옮기는 중에는 «move»", cur(b) == "move",
              [cur(b), L.ev(b, "S.drag && S.drag.mode")])
        release(b)
        xy = L.ev(b, "S.boxes[0].xyxy")
        nw = screen(b, xy[0], xy[1])
        press_move(b, nw["x"], nw["y"], nw["x"] - 25, nw["y"] - 18)
        L.chk("⑥ 모서리를 끄는 중에는 그 모서리 커서 그대로 «nwse-resize»",
              cur(b) == "nwse-resize", [cur(b), L.ev(b, "S.drag && S.drag.corner")])
        release(b)
        L.chk("⑥ 끝나면 상자는 그대로 하나다", L.ev(b, "S.boxes.length") == 1,
              L.ev(b, "S.boxes.length"))

        # ── ⑦ 번호 편집은 지금 그대로 십자 (회귀) ────────────────────────────
        b.key("x")
        time.sleep(0.4)
        L.chk("⑦ 상자 모드를 껐다", L.ev(b, "!!S.boxMode") is False)
        if L.ev(b, "!!S.inst"):
            b.key("k")
            time.sleep(0.5)
            L.chk("⑦ 번호 편집이 켜졌다", L.ev(b, "!!S.numMode") is True)
            L.chk("⑦ 번호 편집 커서는 지금 그대로 십자다", cur(b) == "crosshair", cur(b))
            b.key("k")
            time.sleep(0.4)
            L.chk("⑦ 번호 편집을 껐다", L.ev(b, "!!S.numMode") is False)
        else:
            L.warn("⑦ 이 사진에는 번호본이 없어 번호 편집 커서는 못 쟀다")

        # ── ⑧ 값이 그대로면 DOM 을 한 글자도 안 건드린다 ──────────────────────
        b.key("b")
        time.sleep(0.3)
        b.js("window.__mut = 0;"
             "if (window.__mo) window.__mo.disconnect();"
             "window.__mo = new MutationObserver(function (rs) { window.__mut += rs.length; });"
             "window.__mo.observe(document.querySelector('#cv'), { attributes: true });"
             "return 1")
        for i in range(10):
            move(b, 300 + i * 12, 240 + (i % 3) * 9)
        mut = b.js("window.__mo.disconnect(); return window.__mut")
        L.chk("⑧ 붓을 쥔 채 열 번 움직여도 style 을 한 번도 안 고쳤다 (%s회)" % mut,
              mut == 0, mut)
        L.chk("⑧ 그래도 커서는 붓 그대로다", cur(b) == "crosshair", cur(b))

        # ── ⑨ 콘솔 · 붓질 회귀 ──────────────────────────────────────────────
        L.run(b, "S.undo.length = 0")
        pix0 = L.ev(b, "(function(){let n=0;const e=S.ed;for(let i=0;i<e.length;i++)if(e[i])n++;return n;})()")
        b.drag("#cv", 320, 250, 400, 300)
        time.sleep(0.4)
        pix1 = L.ev(b, "(function(){let n=0;const e=S.ed;for(let i=0;i<e.length;i++)if(e[i])n++;return n;})()")
        L.chk("⑨ 도구를 다 돌린 뒤에도 붓질이 그대로 칠해진다 (%d → %d 화소)" % (pix0, pix1),
              pix1 > pix0, [pix0, pix1])
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑨ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        b.shot(os.path.join(shots, "3_end.png"))
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b14_cursor")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
