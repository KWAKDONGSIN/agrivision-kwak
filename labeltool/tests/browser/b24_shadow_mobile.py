# -*- coding: utf-8 -*-
"""b24 — **그림자를 줄이고 `mobile.css` 를 토큰으로** (디자인 G6).
작성: 2026-09-21

왜
  supabase 체계의 원칙은 «깊이는 1px 실선» 이다. 지금 이 툴에는 **띄우는** 그림자가 둘 있는데
  둘 다 짙다 — 겹창(안내 창·단축키 표) `0 18px 50px rgba(0,0,0,.35)` 와 저장 실패 띠
  `0 4px 12px rgba(0,0,0,.35)`. G1 이 선언해 둔 `--shadow-1`·`--shadow-3` 으로 바꿔 옅게 한다.
  그리고 `mobile.css` 에 혼자 남아 있던 옛 파랑회색 `#22303f` 둘을 `--chrome` 으로 접는다 —
  G2 가 상단 바를 #1c1c1c 로 바꾼 뒤로 **휴대폰에서만** 알림 띠와 아래 단추 줄이 옛 색이라
  같은 화면 안에서 두 검정이 어긋나 보였다.

  조용히 망가지는 길이 넷이다 —
    ① `mobile.css` 는 `:root` 가 **없는 파일**이다. 토큰은 `style.css` 에서 온다 → 그 문서가
       style.css 를 같이 안 부르면 `var(--chrome)` 이 비어 **배경이 통째로 사라진다**
    ② 그림자를 줄이다가 **안쪽** 그림자(U6 눌린 도구)나 노란 테두리(U1 «저장 안 됨»)까지
       건드리면 b15·b10 이 화소로 못박아 둔 «파여 보임» 과 «저장 안 됨» 이 깨진다
    ③ 실패 띠의 **붉은 바탕**(#4a2328)은 뜻이 묶인 색이다 — 휴대폰 규칙이 이것을 덮으면 안 된다
    ④ 색·그림자만 바꾼다 했는데 자리가 밀린다
  그래서 «고치기 전» 값을 먼저 떠 두고(`b24_before.json`), 고친 뒤와 대어
  **바뀐 짝이 내가 미리 적어 둔 그것뿐인가** 를 숫자로 말한다(b21·b22·b23 과 같은 방식).

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 소스에서 — style.css 의 «띄우는» 그림자 둘이 `var(--shadow-*)` 이고, 안쪽 그림자 둘과
       노란 테두리는 **글자 그대로** 남아 있으며, mobile.css 에 `#22303f` 가 하나도 없다
    ② mobile.css 를 부르는 문서는 style.css 도 부른다(①의 첫째 길을 막는다)
    ③ 브라우저에서 — 겹창 둘과 실패 띠의 계산된 그림자가 토큰 값과 **정확히** 같다
    ④ 전보다 **옅고 작다** (알파 .35 → .12/.06)
    ⑤ 안쪽 그림자(U6)·노란 테두리(U1)는 **한 글자도** 안 바뀌었다
    ⑥ 화소로 — 겹창 바깥 그늘이 실제로 밝아졌고, 겹창 **안**은 한 화소도 안 바뀌었다
    ⑦ 휴대폰 폭(360·390 을 청한다) — 아래 단추 줄·알림 띠가 상단 바와 **같은 색**이다
    ⑧ 실패 띠의 붉은 바탕은 휴대폰에서도 그대로고 «확인» 이 눌린다(S2 회귀)
    ⑨ 「바뀐 짝이 그것뿐인가」 — before.json 과 대어 나머지는 한 글자도 안 달라졌다
    ⑩ 자리가 한 화소도 안 밀렸다 · 콘솔 오류 0 · F1 겹창 회귀(U7)

  쓰는 법
      python3 tests/browser/b24_shadow_mobile.py --capture   # 고치기 **전**에 한 번
      python3 tests/browser/b24_shadow_mobile.py             # 고친 **뒤**
"""
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402
from PIL import Image                                    # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_g6")
FRUIT = "peach"
STEM = "210629-t1-01"
CSS = os.path.join(L.T, "app", "static", "style.css")
MCSS = os.path.join(L.T, "app", "static", "mobile.css")
HTML = os.path.join(L.T, "app", "static", "index.html")
BEFORE = os.path.join(HERE, "b24_before.json")
F1 = ""                                            # WebDriver 의 F1 · Esc (b16 과 같은 값)
ESC = ""

# G6 이 쓰는 토큰 값 (style.css 의 :root · design_final.md)
SH1 = (0, 1, 3, 0.06)                                    # --shadow-1  y·blur·알파
SH3 = (0, 16, 48, 0.12)                                  # --shadow-3
CHROME = (28, 28, 28)                                    # --chrome
OLD_CHROME = (34, 48, 63)                                # #22303f — 접기 전
BAD_BG = (74, 35, 40)                                    # #4a2328 실패 띠 — 뜻이 묶인 색

# ⑨ 「바뀌기로 적은 짝」. 여기 없는 짝이 달라지면 실패다.
EXPECT = {
    ("desk", "#tour .tourcard", "sh"),
    ("desk", "#keyhelp .tourcard", "sh"),
    ("desk", "#saveflash.flashbad", "sh"),
    ("phone", "#saveflash.flashbad", "sh"),
    ("phone", "#mobile-bar", "bg"),
    ("phone", "#saveflash", "bg"),
}

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

SKIN = """return (function (sel) {
  const e = document.querySelector(sel); if (!e) return null;
  const c = getComputedStyle(e), r = e.getBoundingClientRect();
  return { bg: c.backgroundColor, col: c.color, bc: c.borderTopColor, sh: c.boxShadow,
           rad: c.borderTopLeftRadius,
           rect: [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
                  Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100] };
})(arguments[0])"""

# 화면에 **보이는** 칸의 자리를 통째로 (⑩ — 한 화소도 안 밀렸나)
RECTS = """return (function (root) {
  const out = {};
  const R = function (e) { const r = e.getBoundingClientRect();
    return [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
            Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100]; };
  document.querySelectorAll(root).forEach(function (e, i) {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    out[(e.id || e.className || e.tagName) + '#' + i] = R(e);
  });
  return out;
})(arguments[0])"""


def rgb(s):
    """'rgb(28, 28, 28)' · 'rgba(0, 0, 0, 0.12)' → (28,28,28)"""
    if not s or "(" not in s:
        return None
    return tuple(int(float(v)) for v in s[s.index("(") + 1:s.index(")")].split(",")[:3])


def shadow(s):
    """계산된 box-shadow 한 줄 → (알파, x, y, blur). 파이어폭스는
       'rgba(0, 0, 0, 0.12) 0px 16px 48px 0px' 꼴로 돌려준다."""
    if not s or s == "none":
        return None
    a = re.search(r"rgba?\(([^)]*)\)", s)
    parts = [x.strip() for x in a.group(1).split(",")] if a else []
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    nums = [float(x) for x in re.findall(r"(-?[\d.]+)px", s)]
    while len(nums) < 3:
        nums.append(0.0)
    return (alpha, nums[0], nums[1], nums[2])


def lum(c):
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


# ───────────────────────── 재는 자리 ─────────────────────────
def desk_probe(b):
    """넓은 창(1366)에서 — 겹창 둘 · 실패 띠 · 눌린 도구 · «저장 안 됨» 단추."""
    out = {}
    # 첫 방문 안내 창을 잠깐 다시 펴서 카드를 잰다(닫는 것은 아래에서)
    L.run(b, "document.querySelector('#tour').classList.remove('hidden')")
    time.sleep(0.4)
    out["#tour .tourcard"] = b.js(SKIN, "#tour .tourcard")
    L.run(b, "document.querySelector('#tour').classList.add('hidden')")
    time.sleep(0.3)

    b.key(F1)                                            # 단축키 겹창 (U7)
    time.sleep(0.6)
    out["#keyhelp .tourcard"] = b.js(SKIN, "#keyhelp .tourcard")
    rects = b.js(RECTS, "#keyhelp, #keyhelp *")
    b.key(ESC)
    time.sleep(0.4)

    L.run(b, "UI.flash('시험 — 저장에 실패했습니다', true)")
    time.sleep(0.5)
    out["#saveflash.flashbad"] = b.js(SKIN, "#saveflash.flashbad")
    out[".flashok"] = b.js(SKIN, ".flashok")
    L.run(b, "document.querySelector('.flashok').click()")
    time.sleep(0.3)

    out["#toolrail button.on"] = b.js(SKIN, "#toolrail button.on")          # U6 안쪽 그림자
    out["#taskbar button.task.on"] = b.js(SKIN, "#taskbar button.task.on")
    out["#toolrail #viewsw button.on"] = b.js(SKIN, "#toolrail #viewsw button.on")

    L.run(b, "S.edDirty = true")                          # U1 «저장 안 됨» 노란 테두리
    time.sleep(0.5)
    out["button.save.unsaved"] = b.js(SKIN, "#btn-save.unsaved")
    L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false")
    time.sleep(0.4)

    out["#topbar"] = b.js(SKIN, "#topbar")
    out["#verdictbar"] = b.js(SKIN, "#verdictbar")
    out["#toolrail"] = b.js(SKIN, "#toolrail")
    out["#canvaswrap"] = b.js(SKIN, "#canvaswrap")
    return out, rects


def phone_probe(b):
    """휴대폰 폭에서 — 아래 단추 줄 · 알림 띠(성공/실패) · 상단 바."""
    out = {}
    out["#mobile-bar"] = b.js(SKIN, "#mobile-bar")
    out["#topbar"] = b.js(SKIN, "#topbar")

    L.run(b, "UI.flash('저장했습니다')")
    time.sleep(0.5)
    out["#saveflash"] = b.js(SKIN, "#saveflash")
    time.sleep(2.8)                                       # 성공 알림은 3초 뒤 스스로 사라진다

    L.run(b, "UI.flash('시험 — 저장에 실패했습니다', true)")
    time.sleep(0.5)
    out["#saveflash.flashbad"] = b.js(SKIN, "#saveflash.flashbad")
    out[".flashok"] = b.js(SKIN, ".flashok")
    L.run(b, "document.querySelector('.flashok').click()")
    time.sleep(0.3)

    out["#verdictbar"] = b.js(SKIN, "#verdictbar")
    out["#canvaswrap"] = b.js(SKIN, "#canvaswrap")
    rects = b.js(RECTS, "#view-edit, #view-edit > *, #mobile-bar, #topbar")
    return out, rects


def _open(b):
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
         "s.dispatchEvent(new Event('change'))", FRUIT)
    b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
    L.close_tour(b)
    time.sleep(0.8)
    b.open_photo(FRUIT, STEM)
    time.sleep(1.4)


def collect(port):
    """넓은 창·휴대폰 폭 두 벌을 한 번에 뜬다(capture 와 본 시험이 **같은 함수**를 쓴다)."""
    base = "http://127.0.0.1:%d" % port
    got = {}
    b = L.browser(w=1366, h=768, base=base)
    try:
        b.js(ERRHOOK)
        _open(b)
        got["desk"], got["deskrects"] = desk_probe(b)
        got["errs"] = b.js("return (window.__errs || []).slice()")
    finally:
        b.close()
    b = L.browser(w=390, h=780, base=base)
    try:
        b.js(ERRHOOK)
        _open(b)
        got["innerw"] = b.js("return window.innerWidth")
        got["phone"], got["phonerects"] = phone_probe(b)
        got["errs2"] = b.js("return (window.__errs || []).slice()")
    finally:
        b.close()
    return got


def capture():
    """고치기 **전** 값을 떠서 b24_before.json 에 적는다."""
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5691)
    p = L.start(port=port, sb=SB)
    try:
        got = collect(port)
    finally:
        L.stop(p)
    io.open(BEFORE, "w", encoding="utf-8").write(json.dumps(got, ensure_ascii=False, indent=1))
    n = len(got["desk"]) + len(got["phone"])
    print("고치기 전 %d칸 · 휴대폰 실제 폭 %s · %s" % (n, got["innerw"], BEFORE))
    for side in ("desk", "phone"):
        for k, v in got[side].items():
            print("  %-6s %-28s bg=%-22s sh=%s" % (side, k, (v or {}).get("bg"), (v or {}).get("sh")))
    return 0


# ───────────────────────── ① 소스 ─────────────────────────
def source_checks():
    raw = io.open(CSS, encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)       # 주석을 걷어낸다(옛 색이 적혀 있다)
    mraw = io.open(MCSS, encoding="utf-8").read()
    mcss = re.sub(r"/\*.*?\*/", "", mraw, flags=re.S)
    html = io.open(HTML, encoding="utf-8").read()

    # 띄우는 그림자 둘이 토큰이 됐나
    for sel, tok in [(r"\.tourcard", "--shadow-3"), (r"#saveflash\.flashbad", "--shadow-1")]:
        m = re.search(sel + r"\s*\{([^{}]*)\}", css)
        body = m.group(1) if m else ""
        L.chk("① %s 의 그림자가 var(%s) 다" % (sel.replace("\\", ""), tok),
              ("var(%s)" % tok) in body, body.strip()[:120])

    # 안쪽 그림자(U6)·노란 테두리(U1)는 글자 그대로 남아 있다
    keep = [("U6 타일", "inset 0 2px 4px rgba(0, 0, 0, .42)"),
            ("U6 보기전환", "inset 0 2px 3px rgba(0, 0, 0, .38)"),
            ("U1 «저장 안 됨»", "box-shadow: 0 0 0 2px #ffd400")]
    for nm, s in keep:
        L.chk("① %s 은 글자 그대로 남아 있다(토큰으로 안 접었다)" % nm, s in raw, s)

    # style.css 에 남은 «짙은» 그림자 0 — rgba(0,0,0,.2) 위는 안쪽(inset)뿐이어야 한다
    dark = [x for x in re.findall(r"box-shadow:[^;}]+", css)
            if (not x.strip().startswith("box-shadow: inset")) and "inset" not in x
            and re.search(r"rgba\(0,\s*0,\s*0,\s*\.[2-9]", x)]
    L.chk("① 밖으로 띄우는 짙은 그림자가 하나도 안 남았다", not dark, dark)

    # mobile.css — 옛 색 0 · 토큰 셋 · 오타 0
    L.chk("① mobile.css 에 #22303f 가 하나도 없다", "22303f" not in mcss, mcss.count("22303f"))
    used = re.findall(r"var\((--[a-z0-9-]+)\)", mcss)
    L.chk("① mobile.css 가 토큰을 %d군데 쓴다(--chrome 둘 · --r-sm 하나)" % len(used),
          sorted(used) == ["--chrome", "--chrome", "--r-sm"], sorted(used))
    root = css[css.index(":root"):css.index("}", css.index(":root"))]
    names = re.findall(r"(--[a-z0-9-]+)\s*:", root)
    L.chk("① mobile.css 가 쓰는 이름이 전부 style.css `:root` 에 있다(오타 0)",
          all(u in names for u in used), [u for u in used if u not in names])

    # ② mobile.css 를 부르는 문서는 style.css 도 부른다 — :root 가 없는 파일이라 이게 생명줄이다
    L.chk("② index.html 이 style.css 와 mobile.css 를 **둘 다** 부른다",
          "/static/style.css" in html and "/static/mobile.css" in html,
          [x for x in re.findall(r'href="([^"]*\.css)"', html)])
    L.chk("② style.css 를 mobile.css **보다 먼저** 부른다",
          html.index("/static/style.css") < html.index("/static/mobile.css"), None)
    return names


# ───────────────────────── 본 시험 ─────────────────────────
def main():
    if not os.path.exists(BEFORE):
        print("‼ %s 가 없습니다 — 고치기 **전**에 `--capture` 를 먼저 돌려야 합니다." % BEFORE)
        return False
    old = json.loads(io.open(BEFORE, encoding="utf-8").read())

    source_checks()

    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5691)
    p = L.start(port=port, sb=SB)
    shots = os.path.join(L.SHOTS, "g6")
    os.makedirs(shots, exist_ok=True)
    try:
        now = collect(port)

        # ── ③ 계산된 그림자가 토큰 값과 정확히 같다 ──────────────────────
        for side, sel, want, nm in [("desk", "#tour .tourcard", SH3, "안내 창"),
                                    ("desk", "#keyhelp .tourcard", SH3, "단축키 겹창"),
                                    ("desk", "#saveflash.flashbad", SH1, "실패 띠"),
                                    ("phone", "#saveflash.flashbad", SH1, "실패 띠(휴대폰)")]:
            got = shadow((now[side][sel] or {}).get("sh"))
            L.chk("③ %s 그림자 = %s %s" % (nm, "--shadow-3" if want is SH3 else "--shadow-1", got),
                  got is not None and abs(got[0] - want[3]) < 0.005
                  and (got[1], got[2], got[3]) == (want[0], want[1], want[2]),
                  [got, want])

        # ── ④ 전보다 옅고 작다 ────────────────────────────────────────────
        for side, sel, nm in [("desk", "#tour .tourcard", "안내 창"),
                              ("desk", "#keyhelp .tourcard", "단축키 겹창"),
                              ("desk", "#saveflash.flashbad", "실패 띠")]:
            a, b_ = shadow(old[side][sel]["sh"]), shadow(now[side][sel]["sh"])
            L.chk("④ %s 그림자가 전보다 **옅다** (알파 %.2f → %.2f)" % (nm, a[0], b_[0]),
                  b_[0] < a[0], [a, b_])
            L.chk("④ %s 그림자가 전보다 **작다** (번짐 %gpx → %gpx)" % (nm, a[3], b_[3]),
                  b_[3] <= a[3] and b_[2] <= a[2], [a, b_])

        # ── ⑤ 안쪽 그림자(U6)·노란 테두리(U1)는 한 글자도 안 바뀌었다 ─────
        for sel in ["#toolrail button.on", "#taskbar button.task.on",
                    "#toolrail #viewsw button.on", "button.save.unsaved"]:
            L.chk("⑤ %s 의 그림자가 전과 **글자까지 같다**" % sel,
                  (now["desk"][sel] or {}).get("sh") == (old["desk"][sel] or {}).get("sh"),
                  [(old["desk"][sel] or {}).get("sh"), (now["desk"][sel] or {}).get("sh")])

        # ── ⑦ 휴대폰 — 아래 단추 줄·알림 띠가 상단 바와 같은 색 ───────────
        L.chk("⑦ 휴대폰 폭에서 잰다(청한 390 · 실제 %s · mobile.css 가 듣는 820 아래)" % now["innerw"],
              now["innerw"] < 820, now["innerw"])
        top = rgb(now["phone"]["#topbar"]["bg"])
        mb = rgb(now["phone"]["#mobile-bar"]["bg"])
        sf = rgb(now["phone"]["#saveflash"]["bg"])
        L.chk("⑦ 아래 단추 줄 = --chrome %s" % (mb,), mb == CHROME, mb)
        L.chk("⑦ 알림 띠(성공) = --chrome %s" % (sf,), sf == CHROME, sf)
        L.chk("⑦ 상단 바와 **같은 색**이다 %s" % (top,), top == mb == sf, [top, mb, sf])
        L.chk("⑦ 옛 파랑회색 #22303f 가 **아니다**", OLD_CHROME not in (mb, sf), [mb, sf])
        L.chk("⑦ 전에는 상단 바와 **달랐다** (%s ↔ %s)" %
              (rgb(old["phone"]["#topbar"]["bg"]), rgb(old["phone"]["#mobile-bar"]["bg"])),
              rgb(old["phone"]["#topbar"]["bg"]) != rgb(old["phone"]["#mobile-bar"]["bg"]),
              [old["phone"]["#topbar"]["bg"], old["phone"]["#mobile-bar"]["bg"]])
        fg = rgb(now["phone"]["#saveflash"]["col"])
        L.chk("⑦ 알림 띠 글씨 대비 %s:1 ≥ 4.5 (AA)" % ratio(fg, sf), ratio(fg, sf) >= 4.5, [fg, sf])

        # ── ⑧ 실패 띠의 붉은 바탕은 그대로 · «확인» 이 눌린다 ─────────────
        for side in ("desk", "phone"):
            bad = rgb(now[side]["#saveflash.flashbad"]["bg"])
            L.chk("⑧ 실패 띠 바탕이 붉은색 그대로다(%s · %s)" % (side, bad), bad == BAD_BG, bad)
        ok = now["phone"][".flashok"]
        L.chk("⑧ 휴대폰에서 «확인» 이 화면 안에 있다 %s" % (ok["rect"],),
              ok["rect"][2] >= 20 and ok["rect"][3] >= 20 and ok["rect"][0] >= 0, ok["rect"])

        # ── ⑨ 바뀐 짝이 미리 적어 둔 그것뿐인가 ──────────────────────────
        changed, same = [], 0
        for side in ("desk", "phone"):
            for sel, v in now[side].items():
                ov = old[side].get(sel)
                if v is None or ov is None:
                    changed.append((side, sel, "없음"))
                    continue
                for k in ("bg", "col", "bc", "sh", "rad"):
                    if v.get(k) != ov.get(k):
                        changed.append((side, sel, k))
                    else:
                        same += 1
        extra = [c for c in changed if tuple(c) not in EXPECT]
        missing = [e for e in EXPECT if tuple(e) not in {tuple(c) for c in changed}]
        L.chk("⑨ 안 바뀌기로 한 %d짝이 한 글자도 안 달라졌다" % same, not extra, extra)
        L.chk("⑨ 바뀐 %d짝이 미리 적어 둔 그것과 정확히 같다" % len(changed), not missing, missing)

        # ── ⑩ 자리가 한 화소도 안 밀렸다 ─────────────────────────────────
        for side in ("deskrects", "phonerects"):
            moved = {k: [old[side][k], v] for k, v in now[side].items()
                     if k in old[side] and old[side][k] != v}
            L.chk("⑩ %s — 잰 자리 %d곳이 한 화소도 안 밀렸다" % (side, len(now[side])),
                  not moved, list(moved.items())[:6])
        for sel in ("#topbar", "#verdictbar", "#toolrail", "#canvaswrap"):
            L.chk("⑩ %s 자리 그대로 %s" % (sel, now["desk"][sel]["rect"]),
                  now["desk"][sel]["rect"] == old["desk"][sel]["rect"],
                  [old["desk"][sel]["rect"], now["desk"][sel]["rect"]])
        L.chk("⑩ 넓은 창 콘솔 오류 0", not now["errs"], now["errs"])
        L.chk("⑩ 휴대폰 폭 콘솔 오류 0", not now["errs2"], now["errs2"])

        # ── ⑥ 화소로 — 겹창 바깥 그늘이 밝아지고 안쪽은 그대로 ────────────
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        try:
            _open(b)
            b.key(F1)
            time.sleep(0.8)
            r = b.js("const e=document.querySelector('#keyhelp .tourcard');"
                     "const q=e.getBoundingClientRect();"
                     "return [q.left,q.top,q.width,q.height]")
            d = float(b.js("return window.devicePixelRatio || 1"))
            # 그늘을 **껐다 켜서** 잰다(U10 의 십자 안내선과 같은 방법). 같은 화면의 «먼 곳» 과
            # 대면 바탕이 다른 UI 라 못 읽는다 — 첫 판이 그렇게 헛되이 실패했다.
            pics = {}
            for tag, css in [("off", "none"), ("new", ""), ("old", "0 18px 50px rgba(0,0,0,.35)")]:
                L.run(b, "(function(v){var s=document.getElementById('__g6')||"
                         "document.head.appendChild(Object.assign(document.createElement('style'),"
                         "{id:'__g6'}));s.textContent=v?'.tourcard{box-shadow:'+v+'}':'';})"
                         "(%s)" % json.dumps(css))
                time.sleep(0.4)
                pth = os.path.join(shots, "01_keyhelp_%s.png" % tag)
                b.shot(pth)
                pics[tag] = Image.open(pth).convert("RGB")
            L.run(b, "var s=document.getElementById('__g6'); if(s) s.remove()")
            # 카드 둘레만 잘라 본다(카드 칸 + 80px). 그늘이 닿을 수 있는 자리는 여기뿐이다.
            W, H = pics["off"].size
            bx = (max(0, int((r[0] - 80) * d)), max(0, int((r[1] - 80) * d)),
                  min(W, int((r[0] + r[2] + 80) * d)), min(H, int((r[1] + r[3] + 80) * d)))
            card = (int(r[0] * d), int(r[1] * d), int((r[0] + r[2]) * d), int((r[1] + r[3]) * d))

            def foot(tag):
                """그늘이 «덮은 자리 수» 와 «어둡게 만든 양», 그리고 카드 속을 침범했나."""
                a = list(pics["off"].crop(bx).getdata())
                c = list(pics[tag].crop(bx).getdata())
                w = bx[2] - bx[0]
                n, dark, inside = 0, 0, 0
                for i, (u, v) in enumerate(zip(a, c)):
                    if u == v:
                        continue
                    n += 1
                    dark += (sum(u) - sum(v)) / 3.0
                    x, y = bx[0] + i % w, bx[1] + i // w
                    if card[0] + 14 * d < x < card[2] - 14 * d and card[1] + 14 * d < y < card[3] - 14 * d:
                        inside += 1
                return n, round(dark / max(n, 1), 2), inside
            # 카드 **바로 바깥**(그늘이 제일 짙은 자리) ↔ **먼 곳**(그늘이 안 닿는 덮개).
            #   그림자가 옅어지면 이 둘의 차가 없어진다. 첫 판에서는 «안쪽이 흰 바탕인가» 를
            #   물었는데 그건 **내 자의 거짓 실패**였다 — 겹창 안은 흰 바탕이 아니라 남색
            #   머리말(.tourhd rgb(34,48,63))과 회색 표줄이 섞여 있다. 게다가 밖으로 띄우는
            #   box-shadow 는 원래 테두리 **안**을 칠하지 않으므로 물어야 할 질문도 아니었다.
            #   «겹창 안이 안 바뀌었나» 는 화면 12장의 08_keyhelp 로 따로 쟀다
            #   (`tests/_sandbox/_g6_shadow.py`) — 바뀐 화소 104,171개가 전부 카드 **밖**이고
            #   그중 **어두워진 것은 0개**(전부 밝아졌다 = 그늘이 옅어졌다), 카드 칸 안으로
            #   센 141개는 전부 **둥근 네 모서리 14px** 안이며 카드 **속**은 0개다.
            #   전 → 후 실측 — 아래 6px (87,92,99) → (105,111,120) · 왼쪽 6px (23,29,35) →
            #   (26,32,38) · 그늘이 원래 안 닿던 먼 곳(200px)은 ±0 이다.
            nn, nd, nin = foot("new")
            on, od, oin = foot("old")
            b.key(ESC)
            time.sleep(0.4)
            L.chk("⑥ 지금 그늘이 덮는 자리 %d화소 · 평균 %.2f채널 어둡게 (옛것은 %d화소 · %.2f채널)"
                  % (nn, nd, on, od), nn > 0 and on > 0, [nn, nd, on, od])
            L.chk("⑥ 지금 그늘이 **덮는 자리가 더 좁다** (%d < %d)" % (nn, on), nn < on, [nn, on])
            L.chk("⑥ 지금 그늘이 **더 옅다** (평균 %.2f < %.2f 채널)" % (nd, od), nd < od, [nd, od])
            L.chk("⑥ 그늘이 카드 **속**을 침범하지 않는다 (지금 %d · 옛것 %d)" % (nin, oin),
                  nin == 0 and oin == 0, [nin, oin])
            L.chk("⑥ F1 회귀 — 겹창이 Esc 로 닫힌다(U7)",
                  b.js("return document.querySelector('#keyhelp').classList.contains('hidden')"), None)
        finally:
            b.close()
    finally:
        L.stop(p)
    return L.summary("b24_shadow_mobile")


if __name__ == "__main__":
    if "--capture" in sys.argv:
        sys.exit(capture())
    # 🔴 2026-09-21 Z2: 여기가 `0 if main() else 1` 로 **뒤집혀 있었다**. `main()` 은
    #   `L.summary()` 가 돌려주는 **실패 개수**라 0 이 «다 통과» 다 → 50/50 으로 통과해도
    #   rc=1(실패)로, 반대로 정말 깨지면 rc=0(통과)으로 말하고 있었다. 나머지 브라우저 시험
    #   스물셋은 전부 `1 if main() else 0` 이다(실측) → 같은 모양으로 맞춘다.
    sys.exit(1 if main() else 0)
