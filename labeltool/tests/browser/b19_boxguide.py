# -*- coding: utf-8 -*-
"""b19 — **상자 모드 십자 안내선이 진짜 브라우저에서 그려지는가** (편의 U10).
작성: 2026-09-21

왜
  상자 작업의 대부분은 «이 네모의 위 변을 옆 네모의 위 변과 맞추는» 일인데, 화면에 기준선이
  하나도 없었다. 커서가 어느 줄에 있는지는 오른쪽 `#hud` 의 «(x, y)» 숫자로만 알 수 있어
  눈이 사진과 숫자 사이를 오갔다. 그림판의 눈금·CAD 의 crosshair 처럼, 커서를 지나는 가로·세로
  한 줄을 사진 끝까지 그어 둔다.

  체크리스트의 검증은 둘이다 — **① 상자 모드에서«만» 그려지는가 · ② 그리기 성능이 눈에 띄게
  나빠지지 않는가.** 둘 다 «코드를 읽어서» 가 아니라 **캔버스 화소를 세어서** 잰다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 커서를 P1 → P2 로 옮기고 캔버스를 떠서 «어느 칸·어느 줄이 통째로 바뀌었나» 를 센다
       (옛 자리 줄이 지워지고 새 자리에 줄이 서야 «안내선이 커서를 따라온다» 가 증명된다)
    ② 그 줄이 **커서 자리**(사진 좌표를 반올림한 자리)에 ±2 장치화소 안으로 선다
    ③ 굵기가 배율과 상관없이 화면에서 한 줄이다(3배로 당겨도 띠가 되지 않는다)
    ④ «고르기·옮기기»(V) 에서는 안 그린다
    ⑤ 커서가 **사진 밖**(회색 여백)이면 안 그린다
    ⑥ ① 칠한 영역 작업에서는 안 그린다 · ⑦ ③ 번호 편집에서도 안 그린다
    ⑧ «원본만» 보기(Q)에서는 안 그린다
    ⑨ 성능 — `drawBoxes()` 300회를 안내선 있음/없음으로 재고, 프레임 간격도 잰다
    ⑩ 회귀 — 실제로 끌어 그린 네모의 변이 안내선이 가리킨 정수 자리와 같다 ·
       점선 설정이 뒤에 오는 그림으로 새지 않는다 · 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b18 과 같다).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_boxguide")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 캔버스를 통째로 떠 두고(__snapC), 나중에 «어느 칸·어느 줄이 몇 점 바뀌었나» 를 센다(__diffC).
# 안내선은 사진 끝까지 이어지는 한 줄이므로 «한 칸에 수백 점» 이라는 모양으로만 나타난다 —
# 붓 원형(지름 30여 점)이나 네모 테두리와 섞일 수 없는 자다.
MEASHOOK = """
window.__snapC = function () {
  const c = document.querySelector('#cv');
  window.__snap = c.getContext('2d').getImageData(0, 0, c.width, c.height).data.slice();
  return [c.width, c.height];
};
window.__diffC = function (gx, gy) {
  const c = document.querySelector('#cv'), W = c.width, H = c.height;
  const d = c.getContext('2d').getImageData(0, 0, W, H).data, s = window.__snap;
  const col = new Int32Array(W), row = new Int32Array(H);
  let n = 0;
  for (let y = 0; y < H; y++) { const o = y * W;
    for (let x = 0; x < W; x++) { const i = (o + x) * 4;
      if (d[i] !== s[i] || d[i + 1] !== s[i + 1] || d[i + 2] !== s[i + 2]) { n++; col[x]++; row[y]++; } } }
  let bx = 0, by = 0;
  for (let x = 1; x < W; x++) if (col[x] > col[bx]) bx = x;
  for (let y = 1; y < H; y++) if (row[y] > row[by]) by = y;
  const near = function (a, c2, w) { let m = 0;
    for (let k = Math.max(0, c2 - w); k <= Math.min(a.length - 1, c2 + w); k++) m = Math.max(m, a[k]);
    return m; };
  // 굵기 — 가장 굵은 칸의 절반을 넘는 이웃 칸이 몇 개인가(점선 겉줄의 번짐까지 센다)
  let thick = 0;
  for (let k = Math.max(0, bx - 4); k <= Math.min(W - 1, bx + 4); k++) if (col[k] * 2 > col[bx]) thick++;
  return { n: n, W: W, H: H, bx: bx, bxn: col[bx], by: by, byn: row[by], thick: thick,
           atx: gx == null ? null : near(col, gx, 2), aty: gy == null ? null : near(row, gy, 2) };
};
return 1;
"""

# 사진의 «몇 할 자리» → 캔버스 왼쪽 위 기준 CSS 화소. 사진 크기를 미리 몰라도 안쪽을 짚을 수 있다
# (b14 의 TOSCREEN 을 «사진 비율» 로 바꾼 것 — 창 밖으로 나가지 않게 잘라 주는 것은 그대로).
TOSCREEN = """(function (fx, fy) {
const cv = document.querySelector('#cv'), r = cv.getBoundingClientRect();
const ix = S.W * fx, iy = S.H * fy;
const x = ix * S.view.s + S.view.tx, y = iy * S.view.s + S.view.ty;
const maxY = Math.min(r.height, window.innerHeight - r.top) - 6;
return { ix: ix, iy: iy,
         x: Math.round(Math.max(4, Math.min(r.width - 4, x))),
         y: Math.round(Math.max(4, Math.min(maxY, y))),
         cut: (y > maxY || y < 4 || x < 4 || x > r.width - 4) };
})(%r, %r)"""

# 사진의 «몇 할 자리» 를 캔버스 한가운데에 두고 배율을 s 로 — 확대해서 볼 때를 만든다
ZOOMTO = """(function (fx, fy, s) {
const cv = document.querySelector('#cv'), dpr = cv._dpr || 1;
const W = cv.width / dpr, H = cv.height / dpr;
S.view.s = s; S.view.tx = W / 2 - S.W * fx * s; S.view.ty = H / 2 - S.H * fy * s;
S.dirty = true;
return { x: Math.round(W / 2), y: Math.round(H / 2) };
})(%r, %r, %r)"""

# 지금 커서(S.cursor) 가 그릴 안내선이 캔버스의 몇 번째 장치 화소에 서야 하는가.
# 코드와 **따로** 계산한다 — drawBoxGuide 가 쓰는 식을 시험에서 다시 적어 둘이 맞는지 본다.
GUIDEAT = """(function () {
const cv = document.querySelector('#cv'), dpr = cv._dpr || 1;
if (!S.cursor) return null;
return { gx: Math.round((Math.round(S.cursor[0]) * S.view.s + S.view.tx) * dpr),
         gy: Math.round((Math.round(S.cursor[1]) * S.view.s + S.view.ty) * dpr),
         ph: Math.min(cv.height, Math.round(S.H * S.view.s * dpr)),
         pw: Math.min(cv.width, Math.round(S.W * S.view.s * dpr)),
         cur: [S.cursor[0], S.cursor[1]], s: S.view.s };
})()"""

TIME = ("(function (n) { const t = performance.now();"
        " for (let i = 0; i < n; i++) UI.drawBoxes();"
        " return Math.round((performance.now() - t) / n * 1000) / 1000; })(300)")

# 매 프레임 다시 그리게 해 놓고 rAF 간격을 모은다.
# ⚠ 앞서 돌던 고리가 살아 있으면 두 고리가 **같은 배열**에 값을 밀어 넣어 간격이 0ms 로 나온다
#   (첫 판에서 실제로 겪었다). 판마다 번호(__gen)를 매겨 옛 고리는 스스로 멈추게 하고,
#   배열도 지역 이름(a)으로 붙잡아 옛 고리가 새 배열을 못 건드리게 한다.
FPS = ("(function (n) { window.__gen = (window.__gen || 0) + 1;"
       " const g = window.__gen, a = []; window.__ts = a;"
       " (function lp(t) { if (g !== window.__gen) return; a.push(t); S.dirty = true;"
       "   if (a.length < n) requestAnimationFrame(lp); })(performance.now());"
       " return 1; })(%d)")
FPSN = 60


def act(b, actions):
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"}, "actions": actions}]})


def move(b, x, y):
    """`#cv` 위 (x,y) CSS 화소로 마우스를 **진짜** 옮긴다 (ff.py 에는 이동만 하는 손잡이가 없다 —
       공용 파일이라 건드리지 않는다. b14 의 move() 와 같은 판단)."""
    r = b.js("const r=document.querySelector('#cv').getBoundingClientRect();return [r.left,r.top]")
    act(b, [{"type": "pointerMove", "duration": 0, "x": int(r[0] + x), "y": int(r[1] + y)}])
    time.sleep(0.25)                                     # 다음 그림 한 장에서 선이 따라온다


def spot(b, fx, fy):
    return L.ev(b, TOSCREEN % (float(fx), float(fy)))


def snap(b):
    return b.js("return window.__snapC()")


def diff(b, gx=None, gy=None):
    return b.js("return window.__diffC(arguments[0], arguments[1])", gx, gy)


def guide_at(b):
    return L.ev(b, GUIDEAT)


def gap_median(b, tool):
    """매 프레임 다시 그리게 해 놓고 프레임 간격 중앙값(ms)."""
    L.run(b, "S.btool = '%s'; S.dirty = true" % tool)
    L.ev(b, FPS % FPSN)
    b.wait("return (window.__ts || []).length >= %d" % FPSN, 30)
    t = json.loads(L.ev(b, "JSON.stringify(window.__ts)"))
    d = sorted(round(t[i + 1] - t[i], 2) for i in range(len(t) - 1))
    return d[len(d) // 2] if d else None


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5621)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "boxguide")
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.js(MEASHOOK)
        os.makedirs(shots, exist_ok=True)

        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        time.sleep(1.2)                                   # loadBoxes()·초벌까지 가라앉기를 기다린다

        b.key("x")
        time.sleep(0.4)
        L.chk("① 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        L.chk("① 그리기 도구다", L.ev(b, "S.btool") == "draw", L.ev(b, "S.btool"))

        p1, p2 = spot(b, 0.25, 0.30), spot(b, 0.70, 0.62)
        L.chk("① 잴 두 자리가 캔버스 안이다(사진 %dx%d)" % (L.ev(b, "S.W"), L.ev(b, "S.H")),
              not p1["cut"] and not p2["cut"], [p1, p2])

        # ── ① 안내선이 커서를 따라온다 ────────────────────────────────────
        move(b, p1["x"], p1["y"])
        g1 = guide_at(b)
        wh = snap(b)
        move(b, p2["x"], p2["y"])
        g2 = guide_at(b)
        d = diff(b, g1["gx"], g1["gy"])
        L.chk("① 캔버스를 떴다(%dx%d 장치화소)" % (wh[0], wh[1]), wh[0] > 100 and wh[1] > 100, wh)
        L.chk("① 커서를 옮기자 화소가 바뀌었다(%d점)" % d["n"], d["n"] > 0, d["n"])
        # 세로줄은 사진 높이만큼 이어진다 — 붓 원형(지름 30여 점)·네모 테두리로는 나올 수 없는 수다
        needv, needh = int(g1["ph"] * 0.8), int(g1["pw"] * 0.8)
        L.chk("① 옛 자리 세로줄이 통째로 지워졌다(그 칸 %d점 ≥ %d)" % (d["atx"], needv),
              d["atx"] >= needv, [d["atx"], needv, g1["ph"]])
        L.chk("① 옛 자리 가로줄도 통째로 지워졌다(그 줄 %d점 ≥ %d)" % (d["aty"], needh),
              d["aty"] >= needh, [d["aty"], needh, g1["pw"]])
        d2 = diff(b, g2["gx"], g2["gy"])
        L.chk("① 새 자리에 세로줄이 새로 섰다(%d점 ≥ %d)" % (d2["atx"], needv),
              d2["atx"] >= needv, [d2["atx"], needv])
        L.chk("① 새 자리에 가로줄도 섰다(%d점 ≥ %d)" % (d2["aty"], needh),
              d2["aty"] >= needh, [d2["aty"], needh])
        print("   실측 — 안내선 세로 %d점 · 가로 %d점 (사진이 화면에서 %dx%d 장치화소 · 배율 %.3f)"
              % (d2["atx"], d2["aty"], g2["pw"], g2["ph"], g2["s"]))
        b.shot(os.path.join(shots, "1_guide.png"))

        # ── ② 커서 «바로 그 자리» 에 선다 ─────────────────────────────────
        # ⚠ 위 d2 는 «옛 자리가 지워지고 새 자리가 그려진» 차이라 굵은 칸이 **둘**이다
        #   (첫 판에서 가장 굵은 칸이 옛 자리로 잡혀 이 항목이 헛되이 실패했다).
        #   여기서는 안내선만 껐다 켜서 **십자 하나만** 남는 차이를 본다.
        L.run(b, "S.btool = 'pick'; S.dirty = true")
        time.sleep(0.3)
        snap(b)
        L.run(b, "S.btool = 'draw'; S.dirty = true")
        time.sleep(0.3)
        d2b = diff(b, g2["gx"], g2["gy"])
        # 바뀐 점이 «십자 하나» 넓이와 딱 맞아야 한다 — 다른 곳은 한 점도 건드리지 않았다는 뜻이다.
        # 십자 넓이 = (세로 사진높이 + 가로 사진폭) × 굵기. 끝의 번짐 몫으로 40점을 봐 준다.
        cross = (g2["ph"] + g2["pw"]) * d2b["thick"]
        L.chk("② 안내선만 켜자 바뀐 곳이 십자 하나뿐이다(%d점 ≈ (세로 %d + 가로 %d) × 굵기 %d = %d)"
              % (d2b["n"], g2["ph"], g2["pw"], d2b["thick"], cross),
              cross - (g2["ph"] + g2["pw"]) < d2b["n"] <= cross + 40,
              [d2b["n"], cross, g2["ph"], g2["pw"], d2b["thick"]])
        L.chk("② 가장 굵은 칸이 커서 자리다(%d ↔ %d)" % (d2b["bx"], g2["gx"]),
              abs(d2b["bx"] - g2["gx"]) <= 2, [d2b["bx"], g2["gx"]])
        L.chk("② 가장 굵은 줄도 커서 자리다(%d ↔ %d)" % (d2b["by"], g2["gy"]),
              abs(d2b["by"] - g2["gy"]) <= 2, [d2b["by"], g2["gy"]])
        L.chk("② 맞춤 배율에서 두께가 %d 장치화소다(≤ 3)" % d2b["thick"], d2b["thick"] <= 3,
              d2b["thick"])

        # ── ③ 3배로 당겨도 화면에서 한 줄이다 ──────────────────────────────
        mid = L.ev(b, ZOOMTO % (0.4, 0.45, 3.0))
        time.sleep(0.3)
        move(b, mid["x"], mid["y"])
        g3 = guide_at(b)
        snap(b)
        L.run(b, "S.btool = 'pick'; S.dirty = true")      # 안내선만 끈다(다른 그림은 그대로)
        time.sleep(0.3)
        d3 = diff(b, g3["gx"], g3["gy"])
        L.chk("③ 3배로 당겨도 두께가 %d 장치화소다(≤ 3 — 사진 3화소짜리 띠가 되지 않는다)"
              % d3["thick"], d3["thick"] <= 3, d3["thick"])
        print("   실측 — 배율 %.2f 에서 안내선 두께 %d 장치화소(dpr 1.5 → 1~2 가 정상)"
              % (g3["s"], d3["thick"]))

        # ── ④ «고르기» 에서는 안 그린다 (③ 끝 상태가 이미 pick 이다) ──────
        L.chk("④ «고르기» 로 바꾸자 안내선이 사라졌다(그 칸 %d점 ≥ %d)"
              % (d3["atx"], int(g3["ph"] * 0.5)), d3["atx"] >= int(g3["ph"] * 0.5),
              [d3["atx"], g3["ph"]])
        snap(b)
        move(b, mid["x"] + 70, mid["y"] + 50)
        g4 = guide_at(b)
        d4 = diff(b, g4["gx"], g4["gy"])
        L.chk("④ «고르기» 에서 커서를 옮겨도 새 안내선이 안 선다(%d점 < %d)"
              % (d4["atx"], int(g4["ph"] * 0.3)), d4["atx"] < int(g4["ph"] * 0.3),
              [d4["atx"], g4["ph"]])
        L.run(b, "S.btool = 'draw'; S.dirty = true")
        b.key("0")                                        # 배율을 «맞춤» 으로 되돌린다
        time.sleep(0.4)

        # ── ⑤ 사진 밖(회색 여백)에서는 안 그린다 ──────────────────────────
        out = L.ev(b, "(function(){const r=document.querySelector('#cv').getBoundingClientRect();"
                      "return {x: Math.max(4, Math.round(S.view.tx/2)), y: Math.round(r.height/2),"
                      " margin: Math.round(S.view.tx)};})()")
        if out["margin"] < 60:
            L.warn("⑤ 이 사진은 왼쪽 여백이 %dpx 뿐이라 건너뛴다" % out["margin"])
        else:
            move(b, out["x"], out["y"])
            ix = L.ev(b, "S.cursor[0]")
            L.chk("⑤ 커서가 사진 밖이다(이미지 x=%.1f)" % ix, ix < 0, ix)
            snap(b)
            move(b, max(4, out["x"] - 20), out["y"] + 40)
            d5 = diff(b, None, None)
            L.chk("⑤ 여백에서 움직여도 새 안내선이 안 선다(가장 굵은 칸 %d점 < 40)" % d5["bxn"],
                  d5["bxn"] < 40, d5)

        # 사진 안으로 돌려 놓고 «있음» 을 다시 확인 — 뒤의 ⑥⑦⑧ 이 «없음» 만 보기 때문이다
        move(b, p1["x"], p1["y"])
        gin = guide_at(b)
        snap(b)
        move(b, p2["x"], p2["y"])
        din = diff(b, gin["gx"], gin["gy"])
        L.chk("⑤ 사진 안으로 돌아오면 안내선이 다시 선다(%d점 ≥ %d)"
              % (din["atx"], int(gin["ph"] * 0.8)), din["atx"] >= int(gin["ph"] * 0.8),
              [din["atx"], gin["ph"]])

        # ── ⑥ ① 칠한 영역 작업에서는 안 그린다 ────────────────────────────
        b.key("x")
        time.sleep(0.4)
        L.chk("⑥ 상자 모드가 꺼졌다", L.ev(b, "!!S.boxMode") is False)
        move(b, p1["x"], p1["y"])
        g6 = guide_at(b)
        snap(b)
        move(b, p2["x"], p2["y"])
        d6 = diff(b, g6["gx"], g6["gy"])
        L.chk("⑥ 칠한 영역 작업에서는 안내선이 없다(그 칸 %d점 < %d)"
              % (d6["atx"], int(g6["ph"] * 0.3)), d6["atx"] < int(g6["ph"] * 0.3),
              [d6["atx"], g6["ph"]])
        L.chk("⑥ 가로줄도 없다(%d점 < %d)" % (d6["aty"], int(g6["pw"] * 0.3)),
              d6["aty"] < int(g6["pw"] * 0.3), [d6["aty"], g6["pw"]])

        # ── ⑦ ③ 번호 편집에서도 안 그린다 ─────────────────────────────────
        if not L.ev(b, "!!S.inst"):
            L.warn("⑦ 이 사진에는 번호본이 없어 건너뛴다")
        else:
            b.key("k")
            time.sleep(0.6)
            L.chk("⑦ 번호 편집이 켜졌다", L.ev(b, "!!S.numMode") is True)
            move(b, p1["x"], p1["y"])
            g7 = guide_at(b)
            snap(b)
            move(b, p2["x"], p2["y"])
            d7 = diff(b, g7["gx"], g7["gy"])
            L.chk("⑦ 번호 편집에서는 안내선이 없다(그 칸 %d점 < %d)"
                  % (d7["atx"], int(g7["ph"] * 0.3)), d7["atx"] < int(g7["ph"] * 0.3),
                  [d7["atx"], g7["ph"]])
            b.key("k")
            time.sleep(0.5)
            L.chk("⑦ 번호 편집을 되돌렸다", L.ev(b, "!!S.numMode") is False)

        # ── ⑧ «원본만» 보기에서는 안 그린다 ───────────────────────────────
        b.key("x")
        time.sleep(0.4)
        L.chk("⑧ 상자 모드로 돌아왔다", L.ev(b, "!!S.boxMode") is True)
        b.key("q")
        time.sleep(0.4)
        L.chk("⑧ «원본만» 이 켜졌다(필름·상자가 쉰다)", L.ev(b, "!!S.hideBox") is True,
              L.ev(b, "!!S.hideBox"))
        move(b, p1["x"], p1["y"])
        g8 = guide_at(b)
        snap(b)
        move(b, p2["x"], p2["y"])
        d8 = diff(b, g8["gx"], g8["gy"])
        L.chk("⑧ «원본만» 에서는 안내선이 없다(그 칸 %d점 < %d)"
              % (d8["atx"], int(g8["ph"] * 0.3)), d8["atx"] < int(g8["ph"] * 0.3),
              [d8["atx"], g8["ph"]])
        b.shot(os.path.join(shots, "2_photoonly.png"))
        b.key("q"); time.sleep(0.3)
        b.key("q"); time.sleep(0.5)                       # 원본만 → 상자만 → 겹쳐
        L.chk("⑧ «겹쳐» 로 돌아왔다", L.ev(b, "!!S.hideBox") is False, L.ev(b, "!!S.hideBox"))

        # ── ⑨ 성능 — 안내선이 한 프레임에 얼마나 더 쓰나 ────────────────────
        move(b, p1["x"], p1["y"])
        nb = L.ev(b, "S.boxes.length")
        L.run(b, "S.btool = 'draw'")
        L.ev(b, TIME)                                     # 첫 회는 버린다(JIT 가 덥혀지기 전)
        on = min(L.ev(b, TIME) for _ in range(3))
        L.run(b, "S.btool = 'pick'")
        L.ev(b, TIME)
        off = min(L.ev(b, TIME) for _ in range(3))
        L.run(b, "S.btool = 'draw'; S.dirty = true")
        add = round(on - off, 3)
        print("   실측 — drawBoxes() 한 번: 안내선 있음 %.3f ms · 없음 %.3f ms · 차이 %+.3f ms "
              "(상자 %d개)" % (on, off, add, nb))
        L.chk("⑨ 안내선이 더하는 시간이 한 프레임에 0.5ms 미만이다(%+.3f ms)" % add,
              add < 0.5, [on, off])
        L.chk("⑨ 한 프레임이 60fps 예산(16.7ms)에 한참 못 미친다(%.3f ms)" % on, on < 5, on)

        gon, goff = gap_median(b, "draw"), gap_median(b, "pick")
        L.run(b, "S.btool = 'draw'; S.dirty = true")
        print("   실측 — 매 프레임 다시 그릴 때 프레임 간격 중앙값: 안내선 있음 %.2f ms · 없음 %.2f ms"
              % (gon, goff))
        # rAF 는 화면 새로고침 눈금(약 16.7ms)으로 끊겨 오므로 그 한 칸 안이면 «같다» 로 본다.
        # 진짜로 무거워졌다면 한 칸을 넘어 두 칸·세 칸으로 벌어진다.
        L.chk("⑨ 프레임 간격이 안내선 때문에 한 칸(16.7ms) 넘게 늘지 않았다(%.2f ↔ %.2f)"
              % (gon, goff), gon - goff <= 17, [gon, goff])

        # ── ⑩ 회귀 — 그린 네모의 변이 안내선이 가리킨 자리와 같다 ───────────
        q1, q2 = spot(b, 0.33, 0.38), spot(b, 0.55, 0.58)
        move(b, q1["x"], q1["y"])
        a = L.ev(b, "[Math.round(S.cursor[0]), Math.round(S.cursor[1])]")
        move(b, q2["x"], q2["y"])
        c = L.ev(b, "[Math.round(S.cursor[0]), Math.round(S.cursor[1])]")
        before = L.ev(b, "S.boxes.length")
        b.drag("#cv", q1["x"], q1["y"], q2["x"], q2["y"])
        time.sleep(0.4)
        after = L.ev(b, "S.boxes.length")
        xy = json.loads(L.ev(b, "JSON.stringify(S.boxes[S.boxes.length-1].xyxy)"))
        L.chk("⑩ 네모가 하나 늘었다(%d → %d)" % (before, after), after == before + 1, [before, after])
        L.chk("⑩ 네 변이 안내선이 가리킨 정수 자리와 같다 %s ↔ %s" % (xy, [a[0], a[1], c[0], c[1]]),
              abs(xy[0] - a[0]) <= 1 and abs(xy[1] - a[1]) <= 1
              and abs(xy[2] - c[0]) <= 1 and abs(xy[3] - c[1]) <= 1, [xy, a, c])
        L.chk("⑩ 점선 설정이 뒤로 새지 않는다(그림이 끝난 뒤 getLineDash 가 비어 있다)",
              L.ev(b, "UI.ctx.getLineDash().length") == 0,
              L.ev(b, "JSON.stringify(UI.ctx.getLineDash())"))
        L.chk("⑩ «저장 안 됨» 이 정상으로 켜졌다(회귀)", L.ev(b, "!!S.bDirty") is True)
        b.shot(os.path.join(shots, "3_drawn.png"))
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑩ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b19_boxguide")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
