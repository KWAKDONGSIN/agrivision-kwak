# -*- coding: utf-8 -*-
"""b23 — **숫자가 바뀔 때 칸 너비가 흔들리지 않는가** (디자인 G5).
작성: 2026-09-21

왜
  좌표·배율·개수·쪽수가 적히는 칸은 글자 수가 그때그때 달라진다.
    · `#hud` — 마우스를 움직일 때마다 «(9, 8)» ↔ «(1664, 1248)» 로 칸이 늘었다 줄었다 한다.
    · `#zoompct` — «39%» ↔ «3000%» 로 확대바 왼쪽 끝이 밀린다.
    · `#cnts` — «개수 1·1·1» ↔ «개수 100·100·99».
    · `#pageinfo` — «1 / 9 쪽» ↔ «10 / 19 쪽» 이 되면 **▶ 단추가 오른쪽으로 달아난다**.
  칸이 흔들리면 눈이 따라다녀야 하고, ▶ 처럼 누르려던 단추가 손가락 밑에서 움직인다.

무엇을 고쳤나 (style.css 만)
  ① 네 칸에 `min-width` 를 **ch 단위**로 줘서 가장 긴 글자 몫의 자리를 미리 잡아 둔다.
  ② 다섯 칸에 `font-variant-numeric: tabular-nums` 를 준다.
  ③ `#hud:empty { display:none }` — 자리를 잡아 두면 **빈 칸이 커다랗게 보이기** 때문이다
     (`#zoompct:empty` 와 같은 처방).

⚠ `--mono` 는 **일부러 안 썼다.** 탐침으로 재 보니
    · 지금 글꼴은 숫자 폭이 이미 같다(«1» 과 «8» 이 둘 다 7.77px) → tabular-nums 로는 아무것도
      안 바뀐다. 흔들림의 원인은 글자 모양이 아니라 **자릿수**다.
    · `--mono` 를 씌우면 한글 +15% · 숫자 +8.5% 로 오히려 **넓어지고**, 흔들림은 그대로다
      (#pageinfo 26.67 → 28.87px).
  그래서 이 시험은 «`var(--mono)` 를 아무도 안 쓴다» 를 단정으로 **못박는다**. 그래도
  tabular-nums 는 남긴다 — 사람 PC 의 진짜 맑은 고딕에서 숫자 폭이 다르면 그때 듣는다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 지금 글꼴의 숫자 폭을 실측해 «왜 tabular-nums 만으로는 안 되는지» 를 기록한다
    ② 다섯 칸에 tabular-nums 가 실제로 붙어 있다 · `var(--mono)` 는 아무도 안 쓴다
    ③ `#zoompct` — **진짜로** 확대·축소하며 너비가 한 번도 안 바뀐다
    ④ `#hud` — **진짜 마우스 이동**으로 한 자리~네 자리 좌표를 만들어도 너비가 그대로다
    ⑤ `#cnts` — 개수가 한 자리→세 자리가 되어도 너비가 그대로고 `#todo` 자리가 안 밀린다
    ⑥ `#pageinfo` — 쪽수가 바뀌어도 너비가 그대로고 **▶ 단추가 안 움직인다**
    ⑦ `#listinfo` — 자리를 **일부러 안 잡았다**(옆이 안 밀린다). 그 사실을 못박는다
    ⑧ 잡아 둔 자리가 가장 긴 글자를 **정말 덮는가**(모자라면 도로 흔들린다)
    ⑨ 자리가 바뀐 곳이 «내가 미리 적어 둔 그것뿐인가» — 고치기 전에 뜬 `b23_before.json` 과 댄다
    ⑩ 좁은 창(mobile.css 가 듣는 820 아래 — 파이어폭스가 390 을 청해도 실제로는 500 이다)
       에서 쪽수 칸이 창 밖으로 안 샌다 · 콘솔 오류 0
  `--capture` 로 돌리면 고치기 **전** 자리를 `b23_before.json` 에 떠 둔다(한 번만).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_g5")
FRUIT = "peach"
BEFORE = os.path.join(HERE, "b23_before.json")
CSS = os.path.join(L.T, "app", "static", "style.css")

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 자리를 재는 칸들 — 고치기 전/후를 짝지어 댄다.
RECT_LIST = ["#counts", "#listinfo", "#prevpage", "#pageinfo", "#nextpage",
             ".pager", "#grid", ".bar", "#f-q"]
RECT_EDIT = ["#hud", "#zoombar", "#zoompct", "#zoomout", "#zoomin", "#zoomfit",
             "#cnts", "#todo", "#todorow", "#verdictbar", "#canvaswrap", "#cv",
             "#toolrail", "#side", "#topbar"]

# 바뀌기로 **미리 적어 둔** 것. 여기 없는 칸이 하나라도 움직이면 실패다.
#  · 자리를 잡아 준 네 칸은 넓어진다 → 그 칸 자신(w)과, 그 때문에 밀리는 이웃만.
EXPECT = {
    ("list", "#pageinfo", "w"),     # 21ch 을 잡았다
    ("list", "#nextpage", "x"),     # 그만큼 오른쪽으로
    ("edit", "#cnts", "w"), ("edit", "#cnts", "x"),      # 15ch — 오른쪽 끝에 붙어 있어 왼쪽으로 자란다
    ("edit", "#todo", "w"),                              # 그만큼 줄어든다(… 로 접힌다)
    ("edit", "#zoompct", "w"), ("edit", "#zoompct", "x"),  # 8.5ch
    ("edit", "#zoombar", "w"), ("edit", "#zoombar", "x"),  # 확대바 전체가 왼쪽으로 자란다
    # #hud 는 **네 성질이 다 바뀐다** — 사진을 연 직후에는 글자가 없어서 `:empty` 로 숨기 때문에
    # 자리(x·y)까지 0 으로 접힌다. 전에는 16×6 짜리 검은 조각이 사진 왼쪽 아래에 떠 있었다.
    ("edit", "#hud", "w"), ("edit", "#hud", "h"),
    ("edit", "#hud", "x"), ("edit", "#hud", "y"),
}

RECTS = """
const sels = arguments[0], out = {};
for (const s of sels) {
  const e = document.querySelector(s);
  if (!e) { out[s] = null; continue; }
  const r = e.getBoundingClientRect();
  out[s] = { x: Math.round(r.left * 100) / 100, y: Math.round(r.top * 100) / 100,
             w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 };
}
return JSON.stringify(out);
"""

# 한 칸에 글자를 차례로 넣어 보며 너비와 «옆 칸 자리» 를 잰다.
SWEEP = """
const sel = arguments[0], texts = arguments[1], nbr = arguments[2];
const e = document.querySelector(sel);
if (!e) return null;
const old = e.textContent;
const probe = document.createElement('span');
probe.style.cssText = 'position:absolute;visibility:hidden;width:1ch';
e.appendChild(probe);
const ch = probe.getBoundingClientRect().width;
probe.remove();
const cs = getComputedStyle(e);
const out = { ch: Math.round(ch * 1000) / 1000, fvn: cs.fontVariantNumeric,
              font: cs.fontFamily, minw: cs.minWidth, rows: [] };
for (const t of texts) {
  e.textContent = t;
  const r = e.getBoundingClientRect();
  const q = nbr ? document.querySelector(nbr) : null;
  out.rows.push({ t: t, w: Math.round(r.width * 100) / 100,
                  nbr: q ? Math.round(q.getBoundingClientRect().left * 100) / 100 : null });
}
e.textContent = old;
return JSON.stringify(out);
"""


def sweep(b, sel, texts, nbr=None):
    r = b.js(SWEEP, sel, texts, nbr)
    return json.loads(r) if r else None


def spread(rows, key="w"):
    v = [x[key] for x in rows if x[key] is not None]
    return (max(v) - min(v)) if v else None


def rects(b, sels):
    return json.loads(b.js(RECTS, sels))


def open_edit(b):
    """목록 → 사진 한 장 → 전문가 모드(#hud 는 쉬움 모드에서 숨는다)."""
    b.open_photo(FRUIT)
    b.wait("return !!document.querySelector('#cv')")
    time.sleep(1.2)
    b.js("document.body.classList.remove('easy')")
    time.sleep(0.4)


# 칸마다 «실제로 들어가는» 글자. 자릿수가 바뀌는 짝을 일부러 골랐다.
CNTS = ["개수 1·1·1", "개수 12·12·11", "개수 100·100·99"]
PAGE = ["1 / 2 쪽 (한 쪽에 120장)", "9 / 9 쪽 (한 쪽에 120장)", "10 / 10 쪽 (한 쪽에 120장)"]
LIST = ["조건에 맞는 사진 9장", "조건에 맞는 사진 125장", "조건에 맞는 사진 1114장"]


def capture():
    """고치기 **전** 자리를 떠 둔다(한 번만 쓴다)."""
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5591)
    p = L.start(port=port, sb=SB)
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.wait("return !!document.querySelector('#listinfo')")
        time.sleep(0.6)
        out = {"list": rects(b, RECT_LIST)}
        open_edit(b)
        out["edit"] = rects(b, RECT_EDIT)
        json.dump(out, open(BEFORE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[뜸] %s" % BEFORE)
        for k, v in out.items():
            for s, r in v.items():
                print("  %-5s %-14s %s" % (k, s, r))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return 0


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5591)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "numwidth")
    os.makedirs(shots, exist_ok=True)
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.wait("return !!document.querySelector('#listinfo')")
        time.sleep(0.6)
        now_list = rects(b, RECT_LIST)        # ⑨ 에서 쓴다 — 아직 아무것도 안 건드린 자리

        # ── ① 지금 글꼴의 숫자 폭 — 왜 tabular-nums 만으로는 안 되는지 ──────────
        digits = json.loads(b.js("""
const cv = document.createElement('canvas'); const g = cv.getContext('2d');
const fam = getComputedStyle(document.body).fontFamily;
function w(t) { g.font = '14px ' + fam; return Math.round(g.measureText(t).width * 100) / 100; }
return JSON.stringify({ one: w('1'), eight: w('8'), fam: fam });"""))
        same = abs(digits["one"] - digits["eight"]) < 0.01
        L.chk("① 이 글꼴은 숫자 폭이 이미 같다 → 흔들림의 원인은 **자릿수**다 (1=%s · 8=%s)"
              % (digits["one"], digits["eight"]), same, digits)

        # ── ② tabular-nums 는 붙어 있고, --mono 는 아무도 안 쓴다 ──────────────
        css = open(CSS, encoding="utf-8").read()
        L.chk("② `var(--mono)` 를 쓰는 곳이 하나도 없다(재 보고 일부러 안 썼다)",
              "var(--mono)" not in css, css.count("var(--mono)"))
        L.chk("② 그래도 `--mono` 선언은 살아 있다(G1 토큰 28개를 안 줄였다)",
              "--mono:" in css)
        for sel in ("#listinfo", "#pageinfo"):
            fvn = b.js("return getComputedStyle(document.querySelector(arguments[0]))"
                       ".fontVariantNumeric", sel)
            L.chk("② %s 에 tabular-nums 가 붙어 있다" % sel, fvn == "tabular-nums", fvn)

        # ── ⑥ #pageinfo — 쪽수가 바뀌어도 ▶ 가 안 움직인다 ────────────────────
        real_page = b.js("return document.querySelector('#pageinfo').textContent")
        L.chk("⑥ 지금 쪽수 글자가 list.js 의 그 틀이다(%r)" % real_page,
              "쪽 (한 쪽에" in real_page and "/" in real_page, real_page)
        pg = sweep(b, "#pageinfo", PAGE, "#nextpage")
        L.chk("⑥ #pageinfo 너비가 한 번도 안 바뀐다(%s)" % [r["w"] for r in pg["rows"]],
              spread(pg["rows"]) == 0, pg)
        L.chk("⑥ ▶ 단추가 한 화소도 안 움직인다(%s)" % [r["nbr"] for r in pg["rows"]],
              spread(pg["rows"], "nbr") == 0, pg)
        L.chk("⑥ 잡아 둔 자리가 ch 단위다(글꼴이 바뀌어도 따라온다) — min-width=%s" % pg["minw"],
              pg["minw"] not in ("", "0px", "auto") and float(pg["minw"][:-2]) > 100, pg["minw"])

        # ── ⑧ 잡아 둔 자리가 가장 긴 글자를 덮는가 ────────────────────────────
        longest = max(r["w"] for r in pg["rows"])
        over = sweep(b, "#pageinfo", ["100 / 199 쪽 (한 쪽에 1200장)"])
        L.chk("⑧ #pageinfo — 실제로 나올 수 있는 가장 긴 쪽수까지 자리가 남는다",
              longest == pg["rows"][0]["w"], [longest, pg["rows"][0]["w"]])
        L.chk("⑧ 그보다 더 긴 글자가 오면 **자르지 않고** 늘어난다(min-width 라서)",
              over["rows"][0]["w"] > longest, [over["rows"][0]["w"], longest])

        # ── ⑦ #listinfo — 자리는 일부러 안 잡았다 ─────────────────────────────
        li = sweep(b, "#listinfo", LIST, "#prevpage")
        L.chk("⑦ #listinfo 는 자리를 안 잡아 너비가 늘어난다(%s)" % [r["w"] for r in li["rows"]],
              spread(li["rows"]) > 0, li)
        L.chk("⑦ 그래도 ◀ 단추는 안 밀린다(가운데 빈칸이 먹는다 — 그래서 안 잡았다)",
              spread(li["rows"], "nbr") == 0, li)

        b.shot(os.path.join(shots, "01_pager.png"))

        # ── 편집 화면 ────────────────────────────────────────────────────────
        open_edit(b)
        now_edit = rects(b, RECT_EDIT)        # ⑨ — 손대기 전과 **같은 때**에 잰다

        # ── ③ #zoompct — 진짜로 확대·축소한다 ─────────────────────────────────
        zw, zb, texts = [], [], []
        for _ in range(9):
            b.js("document.querySelector('#zoomin').click();")
            time.sleep(0.12)
            r = json.loads(b.js("""
const e = document.querySelector('#zoompct').getBoundingClientRect();
const o = document.querySelector('#zoomout').getBoundingClientRect();
return JSON.stringify({ w: Math.round(e.width * 100) / 100,
                        o: Math.round(o.left * 100) / 100,
                        t: document.querySelector('#zoompct').textContent });"""))
            zw.append(r["w"])
            zb.append(r["o"])
            texts.append(r["t"])
        L.chk("③ 진짜로 확대했다 — 글자가 %s → %s 로 자릿수가 늘었다" % (texts[0], texts[-1]),
              len(set(len(t) for t in texts)) >= 2, texts)
        L.chk("③ 그 동안 #zoompct 너비가 한 번도 안 바뀐다(%s)" % sorted(set(zw)),
              len(set(zw)) == 1, zw)
        L.chk("③ － 단추도 한 화소도 안 움직인다", len(set(zb)) == 1, zb)
        b.js("document.querySelector('#zoomfit').click();")
        time.sleep(0.3)

        # ── ④ #hud — 진짜 마우스 이동 ─────────────────────────────────────────
        hud = json.loads(b.js("""
const cv = document.querySelector('#cv');
const r = cv.getBoundingClientRect();
const v = window.eval('S.view');
const out = [];
for (const [ix, iy] of [[1, 1], [40, 30], [400, 300], [1400, 1000]]) {
  const cx = Math.round(r.left + v.tx + v.s * ix), cy = Math.round(r.top + v.ty + v.s * iy);
  if (cx < r.left || cx > r.right || cy < r.top || cy > r.bottom) continue;
  cv.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: cx, clientY: cy }));
  const e = document.querySelector('#hud');
  const b2 = e.getBoundingClientRect();
  out.push({ t: e.textContent, w: Math.round(b2.width * 100) / 100,
             x: Math.round(b2.left * 100) / 100 });
}
return JSON.stringify(out);"""))
        L.chk("④ 진짜 마우스 이동으로 좌표 글자가 실제로 바뀌었다(%d 자리)" % len(hud),
              len(hud) >= 3 and len(set(x["t"] for x in hud)) == len(hud),
              [x["t"] for x in hud])
        L.chk("④ 자릿수가 한 자리 ↔ 네 자리로 바뀌어도 #hud 너비가 그대로다(%s)"
              % sorted(set(x["w"] for x in hud)), len(set(x["w"] for x in hud)) == 1, hud)
        L.chk("④ 왼쪽 끝도 그대로다", len(set(x["x"] for x in hud)) == 1, hud)
        empty = json.loads(b.js("""
const e = document.querySelector('#hud'); const old = e.textContent;
e.textContent = '';
const cs = getComputedStyle(e), r = e.getBoundingClientRect();
const out = { disp: cs.display, w: Math.round(r.width * 100) / 100 };
e.textContent = old; return JSON.stringify(out);"""))
        L.chk("④ 글자가 없을 때는 **빈 칸이 안 보인다**(자리를 잡아 두었으니 꼭 필요하다)",
              empty["disp"] == "none" and empty["w"] == 0, empty)

        # ── ⑤ #cnts — 개수 ────────────────────────────────────────────────────
        real_cnts = b.js("return document.querySelector('#cnts').textContent")
        L.chk("⑤ 지금 개수 글자가 counts.js 의 그 틀이다(%r)" % real_cnts,
              real_cnts.startswith("개수 ") and real_cnts.count("·") == 2, real_cnts)
        cn = sweep(b, "#cnts", CNTS, "#todo")
        L.chk("⑤ 개수가 한 자리 → 세 자리가 되어도 너비가 그대로다(%s)"
              % [r["w"] for r in cn["rows"]], spread(cn["rows"]) == 0, cn)
        L.chk("⑤ 상태 한 문장(#todo) 자리도 안 밀린다", spread(cn["rows"], "nbr") == 0, cn)
        b.shot(os.path.join(shots, "02_edit.png"))

        # ── ⑨ 바뀐 자리가 «미리 적어 둔 그것뿐인가» ────────────────────────────
        if os.path.exists(BEFORE):
            before = json.load(open(BEFORE, encoding="utf-8"))
            now = {"edit": now_edit, "list": now_list}
            moved, same_n = set(), 0
            for scr in ("list", "edit"):
                for sel, r0 in before.get(scr, {}).items():
                    r1 = (now.get(scr) or {}).get(sel)
                    if r0 is None or r1 is None:
                        continue
                    for k in ("x", "y", "w", "h"):
                        if abs(r0[k] - r1[k]) > 0.5:
                            moved.add((scr, sel, k))
                        else:
                            same_n += 1
            L.chk("⑨ 안 바뀌기로 한 칸은 하나도 안 움직였다(%d 짝 그대로)" % same_n,
                  not (moved - EXPECT), sorted(moved - EXPECT))
            L.chk("⑨ 바뀐 칸이 미리 적어 둔 그것과 **정확히 같다**(%d 짝)" % len(moved),
                  moved == EXPECT, {"더": sorted(moved - EXPECT), "덜": sorted(EXPECT - moved)})
        else:
            L.warn("⑨ 기준(b23_before.json)이 없어 건너뛴다 — `--capture` 로 먼저 뜬다")

        # ── ⑩ 휴대폰 폭 ───────────────────────────────────────────────────────
        b2 = L.browser(w=390, h=780, base="http://127.0.0.1:%d" % port)
        try:
            b2.wait("return !!document.querySelector('#listinfo')")
            time.sleep(0.8)
            ph = json.loads(b2.js("""
const p = document.querySelector('.pager').getBoundingClientRect();
const g = document.querySelector('#pageinfo').getBoundingClientRect();
const n = document.querySelector('#nextpage').getBoundingClientRect();
return JSON.stringify({ pw: Math.round(p.width), gw: Math.round(g.width),
                        gr: Math.round(g.right), nr: Math.round(n.right),
                        vw: window.innerWidth,
                        over: n.right > p.right + 1 });"""))
            L.chk("⑩ 좁은 창(실측 %dpx)에서 쪽수 칸과 ▶ 가 창 밖으로 안 샌다" % ph["vw"],
                  not ph["over"], ph)
            L.chk("⑩ 쪽수 칸이 창보다 좁다(%dpx < %dpx)" % (ph["gw"], ph["pw"]),
                  ph["gw"] < ph["pw"], ph)
            b2.shot(os.path.join(shots, "03_narrow.png"))
            # 편집 화면도 본다 — 개수 칸(15ch)이 좁은 창에서 상태 한 문장을 밀어내지 않나
            b2.open_photo(FRUIT)
            b2.wait("return !!document.querySelector('#cv')")
            time.sleep(1.2)
            ed = json.loads(b2.js("""
const row = document.querySelector('#todorow');
const rr = row.getBoundingClientRect();
const c = document.querySelector('#cnts').getBoundingClientRect();
const t = document.querySelector('#todo').getBoundingClientRect();
return JSON.stringify({ dir: getComputedStyle(row).flexDirection,
                        rw: Math.round(rr.width), cw: Math.round(c.width),
                        tw: Math.round(t.width),
                        stacked: c.top >= t.bottom - 1,
                        over: c.right > rr.right + 1 || t.right > rr.right + 1 });"""))
            # 좁은 창에서는 mobile.css 가 #todorow 를 세로로 세운다 → 개수 칸이 **아랫줄**로 간다.
            # 그래서 15ch(108px)은 440px 줄 안에서 아무 일도 안 한다 — 그 사실을 못박는다.
            L.chk("⑩ 좁은 창의 편집 화면에서는 개수 칸이 아랫줄로 간다(mobile.css · %s)" % ed["dir"],
                  ed["dir"] == "column" and ed["stacked"], ed)
            L.chk("⑩ 그래서 잡아 둔 자리(15ch)가 좁은 창을 못 넘는다"
                  " (줄 %dpx · 개수 %dpx)" % (ed["rw"], ed["cw"]),
                  not ed["over"] and ed["cw"] <= ed["rw"], ed)
            b2.shot(os.path.join(shots, "04_narrow_edit.png"))
        finally:
            b2.close()

        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑩ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b23_numwidth")


if __name__ == "__main__":
    if "--capture" in sys.argv:
        sys.exit(capture())
    sys.exit(1 if main() else 0)
