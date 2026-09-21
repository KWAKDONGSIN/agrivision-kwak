# -*- coding: utf-8 -*-
"""b17 — **붓 굵기를 도구마다 따로 기억하는가** (편의 U8).
작성: 2026-09-21

왜
  굵기 칸이 하나뿐이라 붓과 지우개가 그것을 나눠 썼다. 알을 12 로 다듬다가 지우개로 크게
  쓸어내고 붓으로 돌아오면 12 가 아니라 44 라, [ ] 를 여덟 번 두드려 되돌려야 했다.
  포토샵·그림판은 도구마다 제 굵기를 기억한다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 열고 굵기 기억을 비운 채로 시작한다(브라우저를 처음 쓰는 사람)
    ② 처음 지우개를 고르면 **쓰던 붓 굵기를 물려받는다**(없는 값을 지어내지 않는다)
    ③ 지우개를 44 로 바꾸고 붓으로 돌아오면 12 — 화면 숫자·슬라이더까지 함께
    ④ 다섯 번 왕복해도 각자 제 값
    ⑤ [ ] 키는 **지금 도구** 칸만 바꾼다
    ⑥ 브라우저에 적힌 칸 이름은 둘 — `brush:<과일>` · `brush:<과일>:erase`
    ⑦ ❗**진짜로 그어 본다** — 붓 자국 두께와 지우개 자국 두께를 화소로 잰다(보이기만 하는
       숫자가 아니라 정말 그 굵기로 칠하고 지우는가)
    ⑧ 새로고침해도 도구별로 남는다
    ⑨ 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b16 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_brushsize")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 한 열(column)에서 칠해진(또는 지워진) 화소가 몇 개인가 = 가로로 그은 자국의 **두께**
THICK = """(function (cx, want) {
  const W = S.W, H = S.H; let n = 0;
  for (let y = 0; y < H; y++) if ((S.ed[y * W + cx] ? 1 : 0) === want) n++;
  return n;
})(%d, %d)"""


def size(b):
    """지금 화면이 말하는 굵기 셋 — [S.brush, 슬라이더, 옆 숫자]."""
    return L.ev(b, "[S.brush, +document.querySelector('#brush').value,"
                   " +document.querySelector('#brushv').textContent]")


def slide(b, n):
    """슬라이더를 n 으로 옮긴다(사람이 끄는 것과 같은 input 사건)."""
    b.js("const e=document.querySelector('#brush'); e.value=String(arguments[0]);"
         "e.dispatchEvent(new Event('input',{bubbles:true}));", int(n))
    time.sleep(0.25)


def tool(b, k, want):
    b.key(k)
    time.sleep(0.3)
    return L.ev(b, "S.tool") == want


def brush_keys(b):
    return L.ev(b, "Object.keys(localStorage).filter(k=>k.indexOf('brush:')===0).sort()")


def imgx(b, sx):
    """화면 x → 사진 x (열 하나를 집어 두께를 재려고)."""
    return int(L.ev(b, "Math.round((%d - S.view.tx) / S.view.s)" % sx))


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5651)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "brushsize")
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

        # 기억을 비우고 «브라우저를 처음 쓰는 사람» 자리에서 시작한다
        L.run(b, "Object.keys(localStorage).filter(k=>k.indexOf('brush:')===0)"
                 ".forEach(k=>localStorage.removeItem(k))")
        L.chk("① 굵기 기억을 비웠다", brush_keys(b) == [], brush_keys(b))
        L.chk("① 붓으로 시작한다", tool(b, "b", "brush"), L.ev(b, "S.tool"))

        # ── ② 처음 지우개는 붓 굵기를 물려받는다 ────────────────────────────
        slide(b, 12)
        L.chk("② 붓을 12 로 놓았다 %s" % size(b), size(b) == [12, 12, 12], size(b))
        L.chk("② E 로 지우개", tool(b, "e", "erase"), L.ev(b, "S.tool"))
        L.chk("② 처음 지우개는 쓰던 12 그대로다(없는 기본값을 지어내지 않는다) %s" % size(b),
              size(b) == [12, 12, 12], size(b))

        # ── ③ 지우개 44 · 붓으로 돌아오면 12 ────────────────────────────────
        slide(b, 44)
        L.chk("③ 지우개를 44 로 놓았다 %s" % size(b), size(b) == [44, 44, 44], size(b))
        t0 = time.time()
        L.chk("③ B 로 붓", tool(b, "b", "brush"), L.ev(b, "S.tool"))
        back = size(b)
        L.chk("③ ❗붓으로 돌아오면 **12** — 화면 숫자·슬라이더까지 함께 (%.2f초) %s"
              % (time.time() - t0, back), back == [12, 12, 12], back)
        L.chk("③ E 로 지우개", tool(b, "e", "erase"), L.ev(b, "S.tool"))
        L.chk("③ 지우개로 가면 다시 44 %s" % size(b), size(b) == [44, 44, 44], size(b))
        b.shot(os.path.join(shots, "1_erase44.png"))

        # ── ④ 다섯 번 왕복 ─────────────────────────────────────────────────
        seq = []
        for i in range(5):
            b.key("b"); time.sleep(0.2); seq.append(L.ev(b, "S.brush"))
            b.key("e"); time.sleep(0.2); seq.append(L.ev(b, "S.brush"))
        L.chk("④ 다섯 번 왕복해도 12·44 가 번갈아 나온다 %s" % seq,
              seq == [12, 44] * 5, seq)

        # ── ⑤ [ ] 키는 지금 도구 칸만 ──────────────────────────────────────
        L.chk("⑤ 지금은 지우개다", L.ev(b, "S.tool") == "erase", L.ev(b, "S.tool"))
        b.key("]"); time.sleep(0.2)
        b.key("]"); time.sleep(0.25)
        L.chk("⑤ 지우개에서 ] 두 번 → 52 %s" % size(b), size(b) == [52, 52, 52], size(b))
        b.key("b"); time.sleep(0.3)
        L.chk("⑤ 붓은 12 그대로다([ ] 가 남의 칸을 안 건드렸다) %s" % size(b),
              size(b) == [12, 12, 12], size(b))
        b.key("["); time.sleep(0.25)
        L.chk("⑤ 붓에서 [ 한 번 → 8 %s" % size(b), size(b) == [8, 8, 8], size(b))
        b.key("e"); time.sleep(0.3)
        L.chk("⑤ 지우개는 52 그대로 %s" % size(b), size(b) == [52, 52, 52], size(b))

        # ── ⑥ 브라우저에 적힌 칸 이름 ──────────────────────────────────────
        keys = brush_keys(b)
        L.chk("⑥ 칸은 둘뿐이다 — `brush:%s` · `brush:%s:erase` %s" % (FRUIT, FRUIT, keys),
              keys == ["brush:%s" % FRUIT, "brush:%s:erase" % FRUIT], keys)
        vals = L.ev(b, "[localStorage.getItem('brush:%s'), localStorage.getItem('brush:%s:erase')]"
                       % (FRUIT, FRUIT))
        L.chk("⑥ 적힌 값도 8 · 52 %s" % vals, vals == ["8", "52"], vals)

        # ── ⑦ ❗진짜로 그어 본다 — 자국 두께를 화소로 잰다 ───────────────────
        # 붓 8 로 가로줄 하나. 가운데 열에서 **칠해진** 화소를 세면 그것이 굵기다.
        b.key("b"); time.sleep(0.3)
        L.run(b, "UI.applyBits(new Uint8Array(S.W*S.H)); S.undo.length=0")
        time.sleep(0.3)
        b.drag("#cv", 300, 300, 620, 300)
        time.sleep(0.5)
        cx = imgx(b, 460)                                  # 그은 줄의 한가운데 열
        t_brush = L.ev(b, THICK % (cx, 1))
        L.chk("⑦ 붓 8 로 그은 자국의 두께가 8화소다 (실측 %d · 열 %d)" % (t_brush, cx),
              abs(t_brush - 8) <= 2, [t_brush, 8])
        painted = L.ev(b, "(function(){let n=0;for(let i=0;i<S.ed.length;i++)if(S.ed[i])n++;return n;})()")
        L.chk("⑦ 붓질이 진짜로 칠해졌다 (%d화소)" % painted, painted > 0, painted)
        b.shot(os.path.join(shots, "2_brush8.png"))

        # 지우개 52 로 같은 자리를 지운다 — 다 칠해 놓고 그어야 두께가 보인다
        b.key("e"); time.sleep(0.3)
        L.chk("⑦ 지우개는 52 다", L.ev(b, "S.brush") == 52, L.ev(b, "S.brush"))
        L.run(b, "const a=new Uint8Array(S.W*S.H); a.fill(1); UI.applyBits(a); S.undo.length=0")
        time.sleep(0.4)
        b.drag("#cv", 300, 300, 620, 300)
        time.sleep(0.5)
        t_erase = L.ev(b, THICK % (cx, 0))
        L.chk("⑦ ❗지우개 52 로 지운 자국은 52화소다 — 같은 자리를 그었는데 %d배 넓다 (실측 %d)"
              % (round(t_erase / max(1, t_brush)), t_erase),
              abs(t_erase - 52) <= 3, [t_erase, 52])
        L.chk("⑦ 붓 자국(%d)과 지우개 자국(%d)이 정말 다르다" % (t_brush, t_erase),
              t_erase > t_brush * 4, [t_brush, t_erase])
        b.shot(os.path.join(shots, "3_erase52.png"))

        # ── ⑧ 새로고침해도 도구별로 남는다 ──────────────────────────────────
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        b.go("/")
        b.wait("return !!document.querySelector('#fruit option')", 60)
        time.sleep(1.2)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        time.sleep(0.8)
        b.js(ERRHOOK)
        b.key("b"); time.sleep(0.3)
        L.chk("⑧ 새로고침한 뒤에도 붓은 8 %s" % size(b), size(b) == [8, 8, 8], size(b))
        b.key("e"); time.sleep(0.3)
        L.chk("⑧ ❗지우개도 52 그대로 살아 있다 %s" % size(b), size(b) == [52, 52, 52], size(b))

        # ── ⑨ 콘솔 ─────────────────────────────────────────────────────────
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑨ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b17_brushsize")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
