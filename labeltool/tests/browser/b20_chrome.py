# -*- coding: utf-8 -*-
"""b20 — **상단 한 줄이 무채색 `--chrome*` 계단 하나로 접혔나** (디자인 G2).
작성: 2026-09-21

왜
  이 한 줄에만 파랑회색이 **넷**(#22303f 바탕 · #cfd8e3 글씨 · #46596e 테두리·구분선 ·
  #3a4a5c hover) 들어 있었다. 손으로 하나씩 고르다 쌓인 것이라 옆 칸과 미묘하게 안 맞는다.
  G1 에서 선언만 해 둔 토큰을 여기서 **처음으로 꺼내 쓴다**.

  색을 바꾸는 일에서 조용히 망가지는 길이 셋이다 —
    ① `var(--없는이름)` 이면 CSS 는 **말없이** 그 선언을 버린다 → 글씨가 검게 남아도 아무도 모른다
    ② 대비가 떨어져 글씨가 안 읽힌다(특히 흐린 글씨 #9a9a9a)
    ③ 색만 바꾼다고 했는데 자리가 밀린다
  그래서 «계산된 색이 토큰과 **정확히** 같은가 · 대비가 AA 인가 · 옛 색으로 되돌려도 자리가
  **한 화소도** 안 달라지는가» 를 전부 숫자로 잰다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① `style.css` 를 읽어 — 토큰이 브라우저에서 다 살아 있고, `var()` 를 쓰는 자리가
       **상단 바 규칙 안뿐**이며, 그 안에 옛 파랑회색이 하나도 안 남았다
    ② 상단 바와 그 안 일곱 자리의 계산된 색이 토큰 값과 **정확히** 같다 (옛 색이 아니다)
    ③ 계단이 어두운 쪽부터 밝은 쪽으로 **한 방향**이다 (--chrome < soft < hi < line < mute < ink)
    ④ 대비 — 글씨·흐린 글씨·고른 탭·노랑·초록이 전부 WCAG AA(4.5:1) 위다
    ⑤ 진짜 화면 사진의 **화소**로 잰다 — 빈 자리 · 고른 탭 · 구분선 1px
    ⑥ hover — ◀ 에 마우스를 올리면 바탕이 --chrome-hi 로 바뀐다(화소로 확인)
    ⑦ 옛 색으로 되돌려 봐도 상단 바와 그 안 열네 자리가 **한 화소도** 안 움직인다
    ⑧ 좁은 창(1200)·휴대폰 폭에서 — 글자가 바 밖으로 안 새고 탭 4개가 다 눌린다
    ⑨ 뜻이 묶인 색 회귀 — «저장 안 됨» 노랑 · 저장됨 초록 · 실패 띠 붉은색
    ⑩ 탭 이동 회귀 · 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b19 와 같다).
"""
import io
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402
from PIL import Image                                    # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_chrome")
FRUIT = "peach"
STEM = "210629-t1-01"
CSS = os.path.join(L.T, "app", "static", "style.css")

# G2 가 쓰는 토큰과 그 값 (design_final.md + style.css 의 :root)
TOK = {"--chrome": (28, 28, 28), "--chrome-soft": (32, 32, 32), "--chrome-hi": (52, 52, 52),
       "--chrome-line": (61, 61, 61), "--chrome-mute": (154, 154, 154),
       "--chrome-ink": (237, 237, 237), "--canvas": (255, 255, 255)}
OLD = ("#22303f", "#cfd8e3", "#46596e", "#3a4a5c")       # 접기 전 파랑회색 넷
# 🔴 2026-09-21 G3 — 이 시험은 «`var()` 를 쓰는 규칙은 상단 바 것뿐이다» 를 못박아 두었다.
#   G3(도구상자·패널·카드)이 토큰을 꺼내 쓰기 시작하면 그 단정이 거짓 실패가 된다. 느슨하게
#   풀지 않고 **다음 단계의 선택자를 이름으로 적어** 넓힌다 — 여기 없는 자리에서 `var()` 를
#   쓰면 여전히 실패한다(그게 이 단정의 값어치다). G4 는 여기에 또 한 줄을 더하게 된다.
G3SEL = re.compile(r"^(body|#toolrail|#toolrail button|#side|\.railgrp|\.sbox|\.bar|\.vsep"
                   r"|\.card|\.card img|\.pager|\.dupstrip \.dupt|\.dupstrip \.dupt img"
                   # ↓ 0921 G4(단추·입력칸·포커스)가 더한 줄. 푸는 것이 아니라 **이름으로 넓힌다** —
                   #   여기 없는 자리에서 var() 를 쓰면 여전히 실패한다. G5·G6 가 또 더하게 된다.
                   r"|button|button:hover|button:disabled:hover|select, input|:focus-visible"
                   r"|#toolrail button:hover"
                   # ↓ 0921 G6(그림자 줄이기)이 더한 둘. 밖으로 띄우는 그림자는 이 툴에 이 둘뿐이다.
                   r"|\.tourcard|#saveflash\.flashbad"
                   r"|#vbrow button\.big, #vbrow #taskbtns button\.big)$")

# 옛 색을 그대로 되돌리는 덧쓰기 — ⑦ «색만 바뀌었나» 를 재는 자
OLDCSS = """#topbar{background:#22303f;color:#fff}
#topbar button.tab{color:#cfd8e3;border-color:#46596e}
#topbar button.tab.on{background:#fff;color:#22303f;border-color:#fff}
#navphoto::before{border-left-color:#46596e}
#topbar #prev,#topbar #next{color:#cfd8e3;border-color:#46596e}
.who{color:#cfd8e3}"""

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 한 자리의 계산된 색 + 화면 자리
SKIN = """return (function (sel) {
  const e = document.querySelector(sel); if (!e) return null;
  const c = getComputedStyle(e), r = e.getBoundingClientRect();
  return { bg: c.backgroundColor, col: c.color, bc: c.borderTopColor,
           rect: [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
                  Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100] };
})(arguments[0])"""

# 상단 바 안에서 «보이는» 칸의 자리를 통째로 (⑦⑧)
KIDS = """return (function () {
  const bar = document.querySelector('#topbar');
  const out = { bar: null, kids: {} };
  const R = function (e) { const r = e.getBoundingClientRect();
    return [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
            Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100]; };
  out.bar = R(bar);
  bar.querySelectorAll('*').forEach(function (e, i) {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;             // 숨은 칸(휴대폰에서 여럿 숨는다)
    const key = (e.id || e.className || e.tagName) + '#' + i;
    out.kids[key] = R(e);
  });
  return out;
})()"""


def rgb(s):
    """'rgb(28, 28, 28)' → (28,28,28)"""
    return tuple(int(v) for v in s[s.index("(") + 1:s.index(")")].replace("%", "").split(",")[:3])


def lum(c):
    """WCAG 상대 밝기."""
    v = []
    for k in c[:3]:
        k = k / 255.0
        v.append(k / 12.92 if k <= 0.04045 else ((k + 0.055) / 1.055) ** 2.4)
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    if la < lb:
        la, lb = lb, la
    return round((la + 0.05) / (lb + 0.05), 2)


def shot_px(b, path, points):
    """화면을 찍고 (x, y) 여럿의 진짜 화소색을 돌려준다."""
    b.shot(path)
    im = Image.open(path).convert("RGB")
    d = float(b.js("return window.devicePixelRatio || 1"))
    return [im.getpixel((int(x * d), int(y * d))) for (x, y) in points], im


def hover(b, sel):
    """마우스를 그 칸 가운데로 **옮기기만** 한다(누르지 않는다) — :hover 를 켜려고."""
    r = b.js("const r=document.querySelector(arguments[0]).getBoundingClientRect();"
             "return [r.left + r.width / 2, r.top + r.height / 2]", sel)
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"},
         "actions": [{"type": "pointerMove", "duration": 30, "x": int(r[0]), "y": int(r[1])}]}]})
    time.sleep(0.4)


def source_checks():
    """① 소스에서 — 토큰 이름 · `var()` 가 쓰인 자리 · 남은 옛 색."""
    raw = io.open(CSS, encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)          # 주석을 걷어낸다(색 이름이 적혀 있다)
    i = css.index(":root")
    root = css[i:css.index("}", i)]
    names = re.findall(r"(--[a-z0-9-]+)\s*:", root)
    used = sorted(set(re.findall(r"var\((--[a-z0-9-]+)\)", css)))
    L.chk("① :root 토큰이 %d개 선언돼 있다" % len(names), len(names) >= 30, len(names))
    L.chk("① 쓰이는 토큰 이름이 전부 :root 에 있다(오타 0)",
          all(u in names for u in used), [u for u in used if u not in names])

    # `var()` 를 쓰는 규칙의 선택자가 상단 바(G2) ∪ 그다음 단계(G3) 것뿐인가.
    # 상단 바 안에서 쓰는 **이름**은 G2 가 고른 그 일곱 개 그대로여야 한다(늘지도 줄지도 않는다).
    bad, topnames = [], set()
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if "var(--" not in body:
            continue
        s = sel.strip().splitlines()[-1].strip()
        if re.search(r"#topbar|#navphoto|^\.who\b", s):
            topnames |= set(re.findall(r"var\((--[a-z0-9-]+)\)", body))
        elif not G3SEL.match(s):
            bad.append(s)
    L.chk("① `var()` 를 쓰는 규칙은 상단 바(G2) ∪ G3 목록뿐이다", not bad, bad)
    L.chk("① 상단 바가 쓰는 이름 %d개 — %s" % (len(topnames), " ".join(sorted(topnames))),
          topnames == set(TOK) - {"--chrome-soft"}, sorted(topnames))

    # 상단 바 규칙 안에 옛 파랑회색이 하나도 안 남았다
    left = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        s = sel.strip().splitlines()[-1].strip()
        if not re.search(r"#topbar|#navphoto|^\.who\b", s):
            continue
        for o in OLD:
            if o in body:
                left.append(s + " → " + o)
    L.chk("① 상단 바 규칙에 옛 파랑회색이 하나도 안 남았다", not left, left)
    # 밖에는 아직 남아 있다 — G3·G4 가 할 일이라는 것을 여기서 못박는다(다 지웠다고 착각 금지)
    rest = sum(css.count(o) for o in OLD)
    L.chk("① 상단 바 **밖**에는 아직 %d군데 남아 있다(G3·G4 몫)" % rest, rest > 0, rest)
    return names


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5671)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "chrome")
    os.makedirs(shots, exist_ok=True)
    try:
        names = source_checks()

        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        # ⚠ 사진을 **먼저** 연다 — 목록 화면에서는 `#navphoto`(파일 이름·◀▶·구분선)가
        #   자리를 안 차지한다(실측 rect [0,0,0,0]). 거기서 재면 «구분선이 없다 · hover 가
        #   안 붙는다» 로 헛되이 실패한다(첫 실행이 여기서 걸렸다).
        b.open_photo(FRUIT, STEM)
        time.sleep(1.2)
        L.chk("① 사진이 열렸다(상단 바가 다 펴진 상태에서 잰다)", L.ev(b, "S.stem") == STEM,
              L.ev(b, "S.stem"))

        # ── ① 브라우저가 토큰을 다 읽나 (조용히 버려진 선언 0) ──────────────
        got = b.js("return arguments[0].map(function(n){"
                   "return [n, getComputedStyle(document.documentElement).getPropertyValue(n).trim()];})",
                   names)
        empty = [n for n, v in got if not v]
        L.chk("① 브라우저가 토큰 %d개를 **다 읽는다**(못 읽은 것 %d개)" % (len(got), len(empty)),
              not empty, empty)

        # ── ② 계산된 색이 토큰과 정확히 같다 ────────────────────────────────
        bar = b.js(SKIN, "#topbar")
        L.chk("② 상단 바 바탕 = --chrome %s" % (rgb(bar["bg"]),),
              rgb(bar["bg"]) == TOK["--chrome"], bar["bg"])
        L.chk("② 상단 바 글씨 = --chrome-ink %s" % (rgb(bar["col"]),),
              rgb(bar["col"]) == TOK["--chrome-ink"], bar["col"])
        L.chk("② 상단 바가 전보다 **어둡다** (#22303f → %s)" % (rgb(bar["bg"]),),
              lum(rgb(bar["bg"])) < lum((34, 48, 63)), [lum(rgb(bar["bg"])), lum((34, 48, 63))])

        # ⚠ 어느 탭이 켜져 있는지를 **손으로 적지 않는다** — 사진을 열면 «편집» 으로 넘어가므로
        #   `data-view` 로 집으면 뒤바뀐다(첫 실행이 여기서 걸렸다). `.on` 으로 집는다.
        tab_off = b.js(SKIN, "#topbar .tab:not(.on)")
        tab_on = b.js(SKIN, "#topbar .tab.on")
        L.chk("② 켜진 탭 하나 · 꺼진 탭 셋이다",
              b.js("return [document.querySelectorAll('#topbar .tab.on').length,"
                   "document.querySelectorAll('#topbar .tab:not(.on)').length]") == [1, 3],
              b.js("return [...document.querySelectorAll('#topbar .tab')]"
                   ".map(t=>[t.dataset.view, t.classList.contains('on')])"))
        prev = b.js(SKIN, "#topbar #prev")
        who = b.js(SKIN, "#topbar .who")
        for nm, v, want in [("안 고른 탭 글씨 = --chrome-mute", tab_off["col"], TOK["--chrome-mute"]),
                            ("안 고른 탭 테두리 = --chrome-line", tab_off["bc"], TOK["--chrome-line"]),
                            ("고른 탭 바탕 = --canvas", tab_on["bg"], TOK["--canvas"]),
                            ("고른 탭 글씨 = --chrome", tab_on["col"], TOK["--chrome"]),
                            ("◀ 글씨 = --chrome-ink", prev["col"], TOK["--chrome-ink"]),
                            ("◀ 테두리 = --chrome-line", prev["bc"], TOK["--chrome-line"]),
                            ("«내 이름» = --chrome-mute", who["col"], TOK["--chrome-mute"])]:
            L.chk("② %s %s" % (nm, rgb(v)), rgb(v) == want, [v, want])
        for nm, v in [("상단 바", bar["bg"]), ("탭 글씨", tab_off["col"]),
                      ("탭 테두리", tab_off["bc"]), ("◀ 글씨", prev["col"])]:
            L.chk("② %s 가 옛 파랑회색이 **아니다** (%s)" % (nm, rgb(v)),
                  rgb(v) not in [(34, 48, 63), (207, 216, 227), (70, 89, 110), (58, 74, 92)], v)

        # ── ③ 계단이 한 방향인가 ────────────────────────────────────────────
        lad = ["--chrome", "--chrome-soft", "--chrome-hi", "--chrome-line", "--chrome-mute", "--chrome-ink"]
        ls = [round(lum(TOK[n]), 4) for n in lad]
        L.chk("③ 계단이 어두운 쪽 → 밝은 쪽 한 방향이다 %s" % (ls,),
              all(ls[i] < ls[i + 1] for i in range(len(ls) - 1)), ls)

        # ── ④ 대비 (WCAG AA 4.5:1) ──────────────────────────────────────────
        base = TOK["--chrome"]
        for nm, fg, bg in [("상단 바 글씨(--chrome-ink)", TOK["--chrome-ink"], base),
                           ("흐린 글씨(--chrome-mute)", TOK["--chrome-mute"], base),
                           ("고른 탭 글씨", TOK["--chrome"], TOK["--canvas"]),
                           ("노랑 «사용법·?»", (255, 212, 0), base),
                           ("초록 «저장됨»", (126, 226, 168), base)]:
            r = ratio(fg, bg)
            L.chk("④ %s 대비 %.2f:1 ≥ 4.5" % (nm, r), r >= 4.5, [fg, bg, r])
        # 선·hover 는 글씨가 아니다 — «보이되 시끄럽지 않은가» 를 지금 세기로 못박는다
        rl = ratio(TOK["--chrome-line"], base)
        rh = ratio(TOK["--chrome-hi"], base)
        L.chk("④ 1px 선 세기 %.2f:1 — 보이되(>1.2) 안 시끄럽다(<2.0)" % rl, 1.2 < rl < 2.0, rl)
        L.chk("④ hover 세기 %.2f:1 — 보이되(>1.2) 안 시끄럽다(<2.0)" % rh, 1.2 < rh < 2.0, rh)

        # ── ⑤ 진짜 화면 화소 ────────────────────────────────────────────────
        sp = b.js(SKIN, "#topbar .spacer")
        nav = b.js(SKIN, "#navphoto")
        pts = [(sp["rect"][0] + sp["rect"][2] / 2, sp["rect"][1] + sp["rect"][3] / 2),   # 빈 자리
               (tab_on["rect"][0] + 3, tab_on["rect"][1] + tab_on["rect"][3] / 2)]       # 고른 탭 바탕
        (empty_px, tabon_px), im = shot_px(b, os.path.join(shots, "01_bar.png"), pts)
        L.chk("⑤ 상단 바 빈 자리 화소가 %s = --chrome" % (empty_px,), empty_px == TOK["--chrome"], empty_px)
        L.chk("⑤ 고른 탭 바탕 화소가 %s = --canvas" % (tabon_px,), tabon_px == TOK["--canvas"], tabon_px)
        # 구분선 1px — #navphoto 왼쪽 끝 언저리를 훑어 «바 색이 아닌 화소» 를 찾는다
        d = float(b.js("return window.devicePixelRatio || 1"))
        y = int((nav["rect"][1] + nav["rect"][3] / 2) * d)
        found = None
        for x in range(int((nav["rect"][0] - 2) * d), int((nav["rect"][0] + 3) * d)):
            c = im.getpixel((x, y))
            if c != TOK["--chrome"]:
                found = (x, c)
                break
        L.chk("⑤ 구분선 1px 이 %s = --chrome-line (x=%s)" % (found and found[1], found and found[0]),
              bool(found) and found[1] == TOK["--chrome-line"], found)

        # ── ⑥ hover ─────────────────────────────────────────────────────────
        hover(b, "#topbar #prev")
        hv = b.js(SKIN, "#topbar #prev")
        L.chk("⑥ ◀ 에 마우스를 올리면 바탕이 --chrome-hi %s" % (rgb(hv["bg"]),),
              rgb(hv["bg"]) == TOK["--chrome-hi"], hv["bg"])
        (hv_px,), _ = shot_px(b, os.path.join(shots, "02_hover_prev.png"),
                              [(hv["rect"][0] + 3, hv["rect"][1] + hv["rect"][3] / 2)])
        L.chk("⑥ 그 화소도 실제로 %s 다" % (hv_px,), hv_px == TOK["--chrome-hi"], hv_px)
        hover(b, "#topbar .brand")                      # 마우스를 치운다(아무 일도 안 하는 칸)
        back = b.js(SKIN, "#topbar #prev")
        L.chk("⑥ 마우스를 치우면 되돌아온다 (%s)" % back["bg"],
              rgb(back["bg"]) != TOK["--chrome-hi"], back["bg"])

        # ── ⑦ 옛 색으로 되돌려도 자리가 한 화소도 안 움직인다 ────────────────
        now = b.js(KIDS)
        b.js("const s=document.createElement('style');s.id='__oldchrome';"
             "s.textContent=arguments[0];document.head.appendChild(s);", OLDCSS)
        time.sleep(0.5)
        old = b.js(KIDS)
        oldbar = b.js(SKIN, "#topbar")
        b.js("const s=document.querySelector('#__oldchrome'); if(s) s.remove();")
        time.sleep(0.4)
        L.chk("⑦ 되돌리는 자가 진짜로 들었다(옛 바탕 %s)" % (rgb(oldbar["bg"]),),
              rgb(oldbar["bg"]) == (34, 48, 63), oldbar["bg"])
        L.chk("⑦ 상단 바 자리가 옛 색일 때와 **똑같다** %s" % (now["bar"],),
              now["bar"] == old["bar"], [old["bar"], now["bar"]])
        moved = [k for k in now["kids"] if old["kids"].get(k) != now["kids"][k]]
        L.chk("⑦ 바 안 %d자리가 한 화소도 안 움직였다" % len(now["kids"]),
              not moved and len(now["kids"]) >= 12,
              [len(now["kids"]), [(k, old["kids"].get(k), now["kids"][k]) for k in moved[:5]]])
        after = b.js(SKIN, "#topbar")
        L.chk("⑦ 자를 치우니 새 색으로 돌아왔다 (%s)" % (rgb(after["bg"]),),
              rgb(after["bg"]) == TOK["--chrome"], after["bg"])

        # ── ⑨ 뜻이 묶인 색 회귀 ─────────────────────────────────────────────
        #   «*» 는 처음 더러워질 때 만들어진다(dirtymark.js) — 깨끗한 채로 찾으면 없다.
        L.run(b, "S.edDirty = true;")
        time.sleep(0.5)
        star = b.js(SKIN, "#dirtystar")
        L.run(b, "S.edDirty = false;")
        flash = b.js(SKIN, "#saveflash")
        L.chk("⑨ «저장 안 됨» 별이 노랑 그대로다 %s" % (rgb(star["col"]),),
              rgb(star["col"]) == (255, 212, 0), star["col"])
        L.chk("⑨ 저장됨 알림이 초록 그대로다 %s" % (rgb(flash["col"]),),
              rgb(flash["col"]) == (126, 226, 168), flash["col"])
        b.js("document.querySelector('#saveflash').classList.add('flashbad');")
        time.sleep(0.3)
        fb = b.js(SKIN, "#saveflash")
        b.js("document.querySelector('#saveflash').classList.remove('flashbad');")
        L.chk("⑨ 실패 띠가 붉은색 그대로다 %s" % (rgb(fb["bg"]),),
              rgb(fb["bg"]) == (74, 35, 40), fb["bg"])
        tl = b.js(SKIN, "#topbar .toplink")
        L.chk("⑨ «사용법» 글자가 노랑 그대로다 %s" % (rgb(tl["col"]),),
              rgb(tl["col"]) == (255, 212, 0), tl["col"])

        # ── ⑩ 탭 이동 회귀 ──────────────────────────────────────────────────
        b.shot(os.path.join(shots, "03_edit_easy.png"))
        b.js("document.querySelector('.tab[data-view=\"dash\"]').click();")
        b.wait("return document.querySelector('#dash').textContent.length>100", 30)
        L.chk("⑩ 현황 탭으로 옮겨 간다",
              b.js("return document.querySelector('.tab[data-view=\"dash\"]').classList.contains('on')") is True)
        dash_on = b.js(SKIN, '#topbar .tab[data-view="dash"]')
        L.chk("⑩ 옮겨 간 탭이 흰 바탕·--chrome 글씨를 입는다 (%s · %s)"
              % (rgb(dash_on["bg"]), rgb(dash_on["col"])),
              rgb(dash_on["bg"]) == TOK["--canvas"] and rgb(dash_on["col"]) == TOK["--chrome"],
              [dash_on["bg"], dash_on["col"]])
        b.js("document.querySelector('.tab[data-view=\"list\"]').click();")
        time.sleep(0.6)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑩ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        b.close()
        b = None

        # ── ⑧ 좁은 창 1200 · 휴대폰 폭 ──────────────────────────────────────
        #   ⚠ 390 을 청해도 이 파이어폭스는 **500** 아래로 안 줄어든다(shots12 가 실측했다).
        #     실제 폭을 재서 그대로 적는다. 진짜 휴대폰 한 바퀴는 사람 몫이다(plan.md).
        for w, tag in [(1200, "04_narrow_1200"), (390, "05_phone")]:
            b = L.browser(w=w, h=780, base="http://127.0.0.1:%d" % port)
            b.js(ERRHOOK)
            b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
                 "s.dispatchEvent(new Event('change'))", FRUIT)
            b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
            L.close_tour(b)
            b.open_photo(FRUIT, STEM)             # 목록 화면에서는 #navphoto 가 안 보인다
            time.sleep(1.2)
            real = b.js("return window.innerWidth")
            k = b.js(KIDS)
            sk = b.js(SKIN, "#topbar")
            L.chk("⑧ 폭 %d(청한 값 %d) — 바탕이 그대로 --chrome %s" % (real, w, rgb(sk["bg"])),
                  rgb(sk["bg"]) == TOK["--chrome"], sk["bg"])
            bx = k["bar"]
            worst = 0
            for key, r in k["kids"].items():
                worst = max(worst, bx[0] - r[0], (r[0] + r[2]) - (bx[0] + bx[2]),
                            bx[1] - r[1], (r[1] + r[3]) - (bx[1] + bx[3]))
            L.chk("⑧ 폭 %d — 바 안 %d자리가 바 밖으로 안 샌다 (최대 %.2f화소)"
                  % (real, len(k["kids"]), worst), worst <= 0.5, [worst, bx])
            hit = b.js("return [...document.querySelectorAll('#topbar .tab')].map(function(t){"
                       "const r=t.getBoundingClientRect();"
                       "const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);"
                       "return [t.dataset.view, r.width>0 && r.height>0, e===t||t.contains(e)];})")
            L.chk("⑧ 폭 %d — 탭 4개가 다 보이고 가운데가 안 가렸다" % real,
                  len(hit) == 4 and all(v and c for _, v, c in hit), hit)
            L.chk("⑧ 폭 %d — 바 높이 %.2f (그 폭의 자리 그대로)" % (real, bx[3]), bx[3] > 0, bx)
            b.shot(os.path.join(shots, tag + ".png"))
            errs = b.js("return (window.__errs || []).slice()")
            L.chk("⑧ 폭 %d — 콘솔 오류 0" % real, not errs, errs)
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
            b.close()
            b = None

        png = sorted(x for x in os.listdir(shots) if x.endswith(".png") and not x.startswith("_"))
        L.chk("화면 %d장을 남겼다 — %s" % (len(png), shots), len(png) == 5, png)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b20_chrome")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
