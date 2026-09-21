# -*- coding: utf-8 -*-
"""b22 — **단추·입력칸의 테두리·반지름이 통일됐고, 키보드로 돌 때 지금 어디인지 보이나** (디자인 G4).
작성: 2026-09-21

왜
  ① 키보드만으로 쓰는 사람에게 지금 이 툴은 «어디에 있는지» 를 거의 안 알려 준다. 파이어폭스의
     기본 테두리는 밝은 바탕에서 가늘고 흐려서, 단추 여섯 개를 지나면 자리를 놓친다.
     그림판·윈도우 프로그램은 «점선 네모» 로 늘 알려 준다. 여기서는 에메랄드 2px 띠로 알린다.
  ② 단추·입력칸의 테두리가 아직 파랑회색(#b9c2cc)이고, 손이 닿은 모양(hover)도 파란빛
     (#f2f7fc · #7fa8d8)이다. 상단 바(G2)·도구상자와 패널(G3)은 이미 무채색으로 접혔는데
     단추만 파랗게 남아 있다. 반지름도 6px 과 7px 이 섞여 있다.

  여기서 조용히 망가지는 길이 셋이다 —
    ① 포커스 띠가 **마우스로 눌렀을 때도** 뜬다(그러면 아무도 안 본다 → `:focus-visible` 이어야 한다)
    ② 뜻이 묶인 색까지 같이 덮는다(판정 5칸 · 카드 상태 테두리 · 눌린 도구)
    ③ 색만 바꾼다고 했는데 자리가 밀린다
  그래서 이 시험은 «바뀐 것이 맞나» 가 아니라 **«바뀐 것이 그것뿐인가»** 를 함께 묻는다.

어떻게
  고치기 **전에** 떠 둔 `b22_before.json` 과 지금을 칸칸이 댄다(b21 과 같은 방법).
    · `EXPECT` 에 적은 (칸, 성질) 은 반드시 바뀌었고 값이 토큰과 정확히 같아야 한다
    · 거기 없는 나머지는 **한 글자도** 달라지면 안 된다
  덧붙여 —
    ① 소스에서 — `:focus-visible` 규칙이 있고 · `outline:none` 으로 도로 지우는 자리가 없고 ·
       단추·입력칸 규칙에 옛 파랑회색이 안 남았고 · `var()` 쓰는 자리가 G2∪G3∪G4 뿐이다
    ② **진짜 Tab 키**로 화면을 한 바퀴 돈다 — 멈추는 자리마다 에메랄드 2px 띠가 있는가
    ③ 화면 사진의 **화소**로 — 띠가 정말 그려졌나 · 놓으면 사라지나 · 바탕과 얼마나 다른가
    ④ **마우스로 누르면 띠가 안 뜬다**(`:focus-visible` 의 값어치가 여기 있다)
    ⑤ 회귀 — 눌린 도구(U6)·판정 5칸·카드 상태 테두리가 그대로 · 자리가 한 화소도 안 밀린다
    ⑥ 좁은 창 1200 · 휴대폰 폭 · 콘솔 오류 0

쓰는 법
    python3 tests/browser/b22_focus.py --capture   # 고치기 **전에** 한 번 (기준을 뜬다)
    python3 tests/browser/b22_focus.py             # 시험

지키는 것
  모래상자 서버에만 붙는다(빈 포트를 스스로 찾는다). 실서버 5111 · 교수님 5100·5101·5105 에는
  붙지도 끄지도 않는다. 원본 데이터는 읽기만 한다.
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

SB = os.path.join(L.SB_ROOT, "sb_focus")
FRUIT = "peach"
STEM = "210629-t1-01"
CSS = os.path.join(L.T, "app", "static", "style.css")
REF = os.path.join(HERE, "b22_before.json")

TAB = ""                                           # WebDriver 의 Tab

# G4 가 꺼내 쓰는 토큰과 그 값 (style.css 의 :root)
CANVAS = (255, 255, 255)          # --canvas
SUNKEN = (244, 244, 244)          # --canvas-sunken
HAIR_S = (199, 199, 199)          # --hairline-strong
INK_FAINT = (178, 178, 178)       # --ink-faint
ACCENT_DEEP = (36, 180, 126)      # --accent-deep  (포커스 띠)
R_SM = "6px"                      # --r-sm

# G4 가 접는 옛 파랑회색 — 단추·입력칸의 테두리와 hover
OLD4 = ("#b9c2cc", "#f2f7fc", "#7fa8d8")
# `var()` 를 써도 되는 선택자 — 상단 바(G2) ∪ 패널(G3) ∪ 단추·입력칸(G4).
# 여기 없는 자리에서 쓰면 실패다. G5·G6 가 여기에 또 한 줄을 더하게 된다.
G2SEL = re.compile(r"#topbar|#navphoto|^\.who\b")
G3SEL = re.compile(r"^(body|#toolrail|#toolrail button|#side|\.railgrp|\.sbox|\.bar|\.vsep"
                   r"|\.card|\.card img|\.pager|\.dupstrip \.dupt|\.dupstrip \.dupt img)$")
G4SEL = re.compile(r"^(button|button:hover|button:disabled:hover|select, input|:focus-visible"
                   r"|#toolrail button|#toolrail button:hover"
                   # ↓ 0921 G6(그림자 줄이기)이 더한 둘. 푸는 것이 아니라 **이름으로 넓힌다**.
                   r"|\.tourcard|#saveflash\.flashbad"
                   r"|#vbrow button\.big, #vbrow #taskbtns button\.big)$")

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# ── 재는 칸 ────────────────────────────────────────────────────────────────
# 화면 상태에 기대지 않으려고 조각을 **직접 만들어** 끼우고 잰다 (b21 과 같은 방법)
BODY_PROBES = [
    # G4 가 **바꾸는** 칸 — 맨 밑바닥 단추·입력칸
    ("btn", "<button>가</button>", "button"),
    ("btn_dis", "<button disabled>가</button>", "button"),
    ("inp", "<input>", "input"),
    ("sel", "<select></select>", "select"),
    # 뜻이 묶인 색 — 절대 안 바뀐다 (판정 5칸)
    ("vb_ok", "<button class='big ok'>가</button>", "button"),
    ("vb_ai", "<button class='big ai'>가</button>", "button"),
    ("vb_save", "<button class='big save'>가</button>", "button"),
    ("vb_save_unsaved", "<button class='big save unsaved'>가</button>", "button"),
    ("vb_flag", "<button class='big flag'>가</button>", "button"),
    ("vb_exc", "<button class='big exc'>가</button>", "button"),
    # 목록 거르개 — 파랑·빨강은 뜻이다
    ("qf", "<button class='qf'>가</button>", "button"),
    ("qf_on", "<button class='qf on'>가</button>", "button"),
    ("qf_fq", "<button class='qf fq'>가</button>", "button"),
    ("qf_fq_on", "<button class='qf fq on'>가</button>", "button"),
    # 카드 상태 테두리·딱지 — 뜻이 묶인 색
    ("card", "<div class='card'></div>", ".card"),
    ("card_s_ok", "<div class='card s-ok'></div>", ".card"),
    ("card_s_fixed", "<div class='card s-fixed'></div>", ".card"),
    ("card_s_flag", "<div class='card s-flag'></div>", ".card"),
    ("card_s_exclude", "<div class='card s-exclude'></div>", ".card"),
    ("tag_st_ok", "<span class='tag st ok'>가</span>", ".tag"),
    ("tag_st_exclude", "<span class='tag st exclude'>가</span>", ".tag"),
    ("pill_ok", "<span class='pill'>1</span>", ".pill"),
    # 안 건드리는 이웃 — «다 고쳤다» 는 착각을 막는다 (G6 몫)
    ("dtable_td", "<table class='d'><tr><td>가</td></tr></table>", "td"),
    ("tourft", "<div class='tourcard'><div class='tourft'>가</div></div>", ".tourft"),
    ("keyhelp_kbd", "<div class='keyhelp-body'><kbd>가</kbd></div>", "kbd"),
    ("todobtn", "<div class='todo'><button class='todobtn'>가</button></div>", ".todobtn"),
]

# 도구상자 **안**에 끼워야 `#toolrail button` 규칙이 닿는다
RAIL_PROBES = [
    ("tool", "<button class='tool'><span class='ti'>◉</span><span class='tw'>가</span>"
             "<span class='tk'>b</span></button>", "button"),
    ("tool_on", "<button class='tool on'><span class='ti'>◉</span><span class='tw'>가</span>"
                "<span class='tk'>b</span></button>", "button"),
    ("tool_dis", "<button class='tool' disabled><span class='tw'>가</span></button>", "button"),
]

# 진짜로 화면에 있는 칸
#   ⚠ `#toolrail button` 을 그냥 집으면 **맨 앞의 작업 단추**(`#taskbar button.task.on`)가 잡힌다
#     (실측 — 둘의 값이 똑같이 나왔다). 진짜 도구 타일은 눌리지 않은 것으로 따로 집는다.
REAL_EDIT = ["#fruit", "#prev", "#sidetgl", "#note", "#toolrail button", "#toolrail .tool:not(.on)",
             "#vbrow button.big", "#zoombar button", "#taskbar button.task.on", "#who"]
REAL_LIST = ["#prevpage", "#f-q", "#f-status", "#f-sort", '.qf[data-qf="all"]']
# 자리 — 색·테두리만 바꿨다면 한 화소도 안 밀려야 한다
RECTS_EDIT = ["#topbar", "#toolrail", "#maincol", "#canvaswrap", "#cv", "#side",
              "#verdictbar", "#vbrow", "#todorow", "#toolrail button", "#vbrow button.big"]
RECTS_LIST = [".bar", "#grid", "#grid .card", ".pager", "#f-q", "#prevpage"]
# 마우스를 올려 재는 칸 (hover)
#   `#prevpage` 는 첫 쪽에서 **잠겨 있다**(실측) → 여기서 재는 것은 `button:disabled:hover` 다.
#   잠긴 단추가 손이 닿았다고 밝아지면 안 되므로 그것도 못박을 값어치가 있다.
HOVERS_LIST = ['.qf[data-qf="all"]', "#prevpage"]
HOVERS_EDIT = ["#toolrail .tool:not(.on)", "#sidetgl"]


def four(key, val):
    return {(key, p): val for p in ("bt", "br", "bb", "bl")}


# **바뀌어야 하는 칸** — 여기 적힌 것만 바뀌고, 값은 토큰과 정확히 같아야 한다
EXPECT = {}
for _k in ("btn", "btn_dis", "inp", "sel",
           "edit #fruit", "edit #sidetgl", "edit #note", "edit #who",
           "list #prevpage", "list #f-q", "list #f-status", "list #f-sort",
           "hover list #prevpage"):        # 잠긴 단추 — 테두리만 바뀌고 바탕은 흰색 그대로다
    EXPECT.update(four(_k, HAIR_S))
# 반지름 통일 — 7px 이던 다섯 자리를 --r-sm(6px) 으로
for _k in ("edit #toolrail button", "edit #toolrail .tool:not(.on)",
           "edit #taskbar button.task.on", "edit #vbrow button.big",
           "tool", "tool_on", "tool_dis", "hover edit #toolrail .tool:not(.on)"):
    EXPECT[(_k, "rad")] = R_SM
# 손이 닿은 모양(hover) — 파란빛에서 무채색 한 계단으로
for _k in ('hover list .qf[data-qf="all"]', "hover edit #sidetgl",
           "hover edit #toolrail .tool:not(.on)"):
    EXPECT[(_k, "bg")] = SUNKEN
    EXPECT.update(four(_k, INK_FAINT))

PROBE = """return (function (a) {
  const host = document.querySelector(a.host);
  if (!host) return null;
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;left:-10000px;top:0;width:420px;height:600px;';
  host.appendChild(box);
  const out = {};
  a.specs.forEach(function (sp) {
    const w = document.createElement('div');
    w.innerHTML = sp[1];
    box.appendChild(w);
    const e = w.querySelector(sp[2]);
    out[sp[0]] = e ? skin(e) : null;
  });
  box.remove();
  return out;
  function skin(e) { const c = getComputedStyle(e);
    return { bg: c.backgroundColor, col: c.color, sh: c.boxShadow, rad: c.borderRadius,
             bw: c.borderTopWidth,
             bt: c.borderTopColor, br: c.borderRightColor,
             bb: c.borderBottomColor, bl: c.borderLeftColor }; }
})(arguments[0])"""

REALJS = """return (function (sels) {
  const out = {};
  sels.forEach(function (s) {
    const e = document.querySelector(s);
    if (!e) { out[s] = null; return; }
    const c = getComputedStyle(e);
    out[s] = { bg: c.backgroundColor, col: c.color, sh: c.boxShadow, rad: c.borderRadius,
               bw: c.borderTopWidth,
               bt: c.borderTopColor, br: c.borderRightColor,
               bb: c.borderBottomColor, bl: c.borderLeftColor };
  });
  return out;
})(arguments[0])"""

RECTJS = """return (function (sels) {
  const out = {};
  sels.forEach(function (s) {
    const e = document.querySelector(s);
    if (!e) { out[s] = null; return; }
    const r = e.getBoundingClientRect();
    out[s] = [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
              Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100];
  });
  return out;
})(arguments[0])"""

# 지금 포커스가 놓인 칸 — 무엇이고, 띠가 어떻게 그려졌나
FOCUSJS = """return (function () {
  const e = document.activeElement;
  if (!e || e === document.body || e === document.documentElement) return { d: 'body' };
  const c = getComputedStyle(e), r = e.getBoundingClientRect();
  let d = e.tagName.toLowerCase();
  if (e.id) d += '#' + e.id;
  else if (typeof e.className === 'string' && e.className.trim())
    d += '.' + e.className.trim().split(/\\s+/).join('.');
  return { d: d, fv: e.matches(':focus-visible'), has: document.hasFocus(),
           st: c.outlineStyle, col: c.outlineColor, w: c.outlineWidth, off: c.outlineOffset,
           rect: [Math.round(r.left * 100) / 100, Math.round(r.top * 100) / 100,
                  Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100] };
})()"""


def rgb(s):
    """'rgb(199, 199, 199)' → (199,199,199)"""
    return tuple(int(v) for v in s[s.index("(") + 1:s.index(")")].replace("%", "").split(",")[:3])


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


def hover(b, sel):
    """마우스를 그 칸 가운데로 **옮기기만** 한다(누르지 않는다) — :hover 를 켜려고. (b20 과 같다)"""
    r = b.js("const e=document.querySelector(arguments[0]); if(!e) return null;"
             "const r=e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]", sel)
    if not r:
        return False
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"},
         "actions": [{"type": "pointerMove", "duration": 30, "x": int(r[0]), "y": int(r[1])}]}]})
    time.sleep(0.4)
    return True


def unhover(b):
    """마우스를 아무것도 없는 구석으로 치운다 — 다음에 재는 값에 hover 가 안 섞이게."""
    b._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m",
         "parameters": {"pointerType": "mouse"},
         "actions": [{"type": "pointerMove", "duration": 30, "x": 2, "y": 2}]}]})
    time.sleep(0.3)


def blur(b):
    b.js("document.activeElement && document.activeElement.blur();")
    time.sleep(0.2)


def restart_tab_point(b):
    """Tab 차례의 **출발점을 문서 맨 앞으로** 돌린다.

    사진을 열면 카드를 누른 자리에서 차례가 이어져 상단 바를 아예 안 지나간다(실측 — 첫 판의
    편집 화면 21군데에 `#prev` 가 없었다). 맨 앞 칸에 포커스를 잠깐 줬다 놓으면 그 다음부터 돈다.
    """
    b.js("const e=document.querySelector('#fruit'); if (e) { e.focus(); e.blur(); }")
    time.sleep(0.2)


def walk(b, n=40, shots=None, tag="", wanted=()):
    """**진짜 Tab 키**로 문서를 한 바퀴 돈다. 멈추는 자리를 차례대로 적는다.

    ⚠ **문서 끝을 넘기면 안 된다.** 넘기면 포커스가 브라우저 칸(주소창)으로 나가고,
      그 뒤로는 `document.hasFocus()` 가 거짓이라 `:focus-visible` 이 **영영 안 켜진다**
      (마우스로 눌러도 안 돌아온다 — `tests/_sandbox/_g4_probe2.py` 로 실측했다).
      첫 판에서 이것 때문에 «편집 화면은 21군데가 전부 포커스 띠가 없다» 는 거짓 실패가 났다.
      그래서 `body` 가 나오면 **바로 멈춘다**.
    `wanted` 에 적은 id 에 닿으면 그 자리에서 화면을 한 장 찍는다(되돌아가지 않으려고).
    """
    blur(b)
    stops, seen, shot = [], set(), {}
    for _ in range(n):
        b.key(TAB)
        s = b.js(FOCUSJS)
        if not s or s.get("d") == "body":
            break                           # 문서 끝 — 더 밀지 않는다
        key = (s["d"], tuple(s["rect"]))
        if key in seen:                     # 한 바퀴 돌아 처음으로 되돌아왔다
            break
        seen.add(key)
        stops.append(s)
        for w in wanted:
            if s["d"].endswith("#" + w) and w not in shot:
                p = os.path.join(shots, "%s_%s_on.png" % (tag, w))
                b.shot(p)
                shot[w] = (s, p)
    return stops, shot


def measure(b):
    """지금 화면에서 잴 수 있는 것을 다 잰다 — 목록 한 번, 사진을 연 뒤 한 번."""
    out = {"style": {}, "rect": {}}
    out["rect"].update({"list " + k: v for k, v in b.js(RECTJS, RECTS_LIST).items()})
    out["style"].update({"list " + k: v for k, v in b.js(REALJS, REAL_LIST).items()})
    for sel in HOVERS_LIST:
        if hover(b, sel):
            out["style"]["hover list " + sel] = b.js(REALJS, [sel])[sel]
    unhover(b)

    b.open_photo(FRUIT, STEM)
    time.sleep(1.2)
    out["style"].update(b.js(PROBE, {"host": "body", "specs": BODY_PROBES}) or {})
    out["style"].update(b.js(PROBE, {"host": "#toolrail", "specs": RAIL_PROBES}) or {})
    out["style"].update({"edit " + k: v for k, v in b.js(REALJS, REAL_EDIT).items()})
    out["rect"].update({"edit " + k: v for k, v in b.js(RECTJS, RECTS_EDIT).items()})
    for sel in HOVERS_EDIT:
        if hover(b, sel):
            out["style"]["hover edit " + sel] = b.js(REALJS, [sel])[sel]
    unhover(b)
    return out


def open_list(b):
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
         "s.dispatchEvent(new Event('change'))", FRUIT)
    b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
    L.close_tour(b)
    time.sleep(1.2)


def with_server(fn):
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5691)
    p = L.start(port=port, sb=SB)
    try:
        return fn(port)
    finally:
        L.stop(p)


def capture():
    """고치기 **전에** 부른다 — 지금의 테두리·반지름·hover·자리를 통째로 적어 둔다."""
    def go(port):
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        try:
            open_list(b)
            snap = measure(b)
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        finally:
            b.close()
        io.open(REF, "w", encoding="utf-8").write(
            json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True))
        n = sum(1 for k, v in snap["style"].items() if v)
        print("기준을 적었다 — %s\n  칸 %d개 · 자리 %d개" % (REF, n, len(snap["rect"])))
        miss = [k for k, v in snap["style"].items() if not v]
        if miss:
            print("  ⚠ 못 잰 칸: %s" % miss)
        return 0 if not miss else 1
    return with_server(go)


def source_checks():
    """① 소스에서 — 포커스 규칙 · 되돌려 지우는 자리 · 남은 옛 색 · var() 쓰는 자리."""
    raw = io.open(CSS, encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)          # 주석을 걷어낸다(색 이름이 적혀 있다)
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    body_of = {}
    for sel, body in rules:
        body_of.setdefault(sel.strip().splitlines()[-1].strip(), "")
        body_of[sel.strip().splitlines()[-1].strip()] += body

    fv = body_of.get(":focus-visible", "")
    L.chk("① `:focus-visible` 규칙이 있다", bool(fv), sorted(body_of)[:3])
    L.chk("① 포커스 띠가 토큰에서 나온다 — outline 에 var(--accent…)",
          "var(--accent" in fv, fv.strip())
    L.chk("① 띠 굵기 2px · 한 칸 띄움(outline-offset)",
          "2px" in fv and "outline-offset" in fv, fv.strip())

    # `outline: none/0` 으로 도로 지우는 자리가 있으면 이 기능은 **조용히** 죽는다
    killed = [s for s, bdy in body_of.items()
              if re.search(r"outline\s*:\s*(none|0)\b", bdy)]
    L.chk("① `outline:none` 으로 도로 지우는 자리가 없다", not killed, killed)

    # 단추·입력칸 규칙에 옛 파랑회색이 안 남았다
    left = []
    for s, bdy in body_of.items():
        if not G4SEL.match(s):
            continue
        for o in OLD4:
            if o in bdy:
                left.append(s + " → " + o)
    L.chk("① 단추·입력칸 규칙에 옛 파랑회색이 하나도 안 남았다", not left, left)
    rest = {o: css.count(o) for o in OLD4 if css.count(o)}
    L.chk("① 단추·입력칸 **밖**에는 아직 %d군데 남아 있다(G6 몫) — %s"
          % (sum(rest.values()), rest), True, rest)

    # var() 를 쓰는 자리가 G2 ∪ G3 ∪ G4 뿐인가 (b20·b21 과 같은 단정을 여기서도 지킨다)
    bad, g4 = [], []
    for sel, bdy in rules:
        if "var(--" not in bdy:
            continue
        s = sel.strip().splitlines()[-1].strip()
        if G2SEL.search(s) or G3SEL.match(s):
            continue
        if G4SEL.match(s):
            g4.append(s)
        else:
            bad.append(s)
    L.chk("① `var()` 를 쓰는 규칙은 상단 바(G2) ∪ 패널(G3) ∪ 단추·입력칸(G4) 뿐이다", not bad, bad)
    L.chk("① G4 가 꺼내 쓰는 규칙 %d개 — %s" % (len(g4), " · ".join(g4)), len(g4) >= 5, g4)


def compare(snap, old):
    """② «바뀐 것이 내가 적은 그것뿐인가» — 칸칸이 댄다."""
    keys = sorted(set(old["style"]) | set(snap["style"]))
    L.chk("② 재는 칸 수가 전과 같다 (%d개)" % len(keys),
          len(keys) == len(old["style"]) == len(snap["style"]),
          [len(old["style"]), len(snap["style"])])
    missing = [k for k in keys if not snap["style"].get(k)]
    L.chk("② 못 잰 칸이 없다", not missing, missing)

    changed, kept = {}, 0
    for k in keys:
        a, c = old["style"].get(k) or {}, snap["style"].get(k) or {}
        for prop in sorted(set(a) | set(c)):
            if a.get(prop) == c.get(prop):
                kept += 1
            else:
                changed[(k, prop)] = (a.get(prop), c.get(prop))

    extra = sorted(k for k in changed if k not in EXPECT)
    missed = sorted(k for k in EXPECT if k not in changed)
    L.chk("② 안 바뀌어야 할 %d짝이 **한 글자도** 안 달라졌다 (뜻이 묶인 색이 여기 다 있다)" % kept,
          not extra, [(k, changed[k]) for k in extra[:8]])
    L.chk("② 바꾸기로 적은 %d짝이 **다 바뀌었다**" % len(EXPECT), not missed, missed)
    for k in sorted(EXPECT):
        if k not in changed:
            continue
        got, was = changed[k][1], changed[k][0]
        want = EXPECT[k]
        ok = (got == want) if isinstance(want, str) else (rgb(got) == want)
        L.chk("② %s·%s = %s (전 %s)" % (k[0], k[1], got, was), ok, [got, want])

    moved = [(k, old["rect"].get(k), snap["rect"].get(k))
             for k in sorted(set(old["rect"]) | set(snap["rect"]))
             if old["rect"].get(k) != snap["rect"].get(k)]
    L.chk("⑤ 잰 자리 %d곳이 한 화소도 안 밀렸다" % len(snap["rect"]), not moved, moved[:5])
    L.chk("⑤ 잰 자리가 열 곳 이상이고 비어 있지 않다",
          len(snap["rect"]) >= 10 and all(snap["rect"].values()), snap["rect"])

    # 반지름이 한 값으로 모였나 — 단추·입력칸을 통틀어 6px 뿐이다
    rads = {}
    for k in ("btn", "inp", "sel", "edit #toolrail button", "edit #toolrail .tool:not(.on)",
              "edit #vbrow button.big", "edit #taskbar button.task.on",
              "edit #sidetgl", "list #prevpage", "list #f-q", "edit #zoombar button"):
        v = (snap["style"].get(k) or {}).get("rad")
        if v:
            rads.setdefault(v, []).append(k)
    L.chk("② 단추·입력칸 열한 자리의 반지름이 **한 값(%s)** 으로 모였다 — %s"
          % (R_SM, {k: len(v) for k, v in rads.items()}),
          list(rads) == [R_SM], rads)


def ring_px(im, rect, d, want, tol=48, band=5):
    """칸 둘레 **바깥** 띠에서 want 색에 가까운 화소를 센다(칸 안쪽은 안 센다)."""
    x0, y0 = int(round(rect[0] * d)), int(round(rect[1] * d))
    x1, y1 = int(round((rect[0] + rect[2]) * d)), int(round((rect[1] + rect[3]) * d))
    bw = int(round(band * d))
    n = 0
    for x in range(max(0, x0 - bw), min(im.size[0], x1 + bw)):
        for y in range(max(0, y0 - bw), min(im.size[1], y1 + bw)):
            if x0 <= x < x1 and y0 <= y < y1:
                continue
            px = im.getpixel((x, y))
            if all(abs(px[i] - want[i]) <= tol for i in range(3)):
                n += 1
    return n


def focus_walk(b, where, shots, tag, wanted, surround):
    """②③ 진짜 Tab 으로 한 바퀴 — 멈추는 자리마다 에메랄드 2px 띠가 있는가 · 화소로도 보이나.

    ⚠ «아무 데도 포커스가 없는» 화면은 **돌기 전에** 찍는다. 한 바퀴를 다 돌면 마지막 칸 다음
      Tab 에서 포커스가 창 밖으로 나가 돌아오지 않으므로(_g4_probe2), 돌고 난 뒤의 «띠 없음»은
      깨끗한 비교가 못 된다. 그래서 이 함수는 **브라우저 한 벌에 한 번만** 불러야 한다.
    """
    blur(b)
    off = os.path.join(shots, tag + "_off.png")
    b.shot(off)
    imoff = Image.open(off).convert("RGB")
    restart_tab_point(b)
    stops, shot = walk(b, shots=shots, tag=tag, wanted=wanted)
    L.chk("② %s — Tab 으로 %d군데에 멈춘다(10군데 이상)" % (where, len(stops)),
          len(stops) >= 10, [s["d"] for s in stops])
    lost = [s["d"] for s in stops if s.get("has") is not True]
    L.chk("② %s — 도는 동안 문서가 창의 포커스를 안 놓쳤다" % where, not lost, lost)
    bad_st = [s["d"] for s in stops if s.get("st") != "solid"]
    L.chk("② %s — 멈춘 %d군데가 전부 **실선** 띠다" % (where, len(stops)), not bad_st, bad_st)
    bad_col = [(s["d"], s.get("col")) for s in stops
               if not s.get("col") or rgb(s["col"]) != ACCENT_DEEP]
    L.chk("② %s — 띠 색이 전부 --accent-deep %s 다" % (where, ACCENT_DEEP), not bad_col, bad_col)
    bad_w = [(s["d"], s.get("w"), s.get("off")) for s in stops
             if s.get("w") != "2px" or s.get("off") != "1px"]
    L.chk("② %s — 띠가 전부 2px · 한 칸(1px) 띄움" % where, not bad_w, bad_w)
    bad_fv = [s["d"] for s in stops if s.get("fv") is not True]
    L.chk("② %s — 멈춘 자리가 전부 `:focus-visible` 이다" % where, not bad_fv, bad_fv)

    # ③ 화면 사진의 **화소**로 — 띠가 정말 그려졌나 · 아무 데도 없을 때는 없나
    d = float(b.js("return window.devicePixelRatio || 1"))
    for w in wanted:
        L.chk("③ %s — Tab 으로 %s 에 닿았다" % (where, w), w in shot, sorted(shot))
        if w not in shot:
            continue
        s, path = shot[w]
        n_on = ring_px(Image.open(path).convert("RGB"), s["rect"], d, ACCENT_DEEP)
        peri = 2 * (s["rect"][2] + s["rect"][3]) * d
        L.chk("③ %s — 띠 화소 %d개 ≥ 둘레의 1.2배(%d) (2px 짜리 띠다)"
              % (w, n_on, int(peri * 1.2)), n_on >= peri * 1.2, [n_on, int(peri)])
        n_off = ring_px(imoff, s["rect"], d, ACCENT_DEEP)
        L.chk("③ %s — 아무 데도 포커스가 없을 때 그 자리 띠 화소는 **0개**다 (%d개)" % (w, n_off),
              n_off == 0, n_off)
        bg = surround.get(w)
        if bg:
            r = ratio(ACCENT_DEEP, bg)
            L.chk("③ %s — 띠와 그 둘레 바탕 %s 의 밝기 차 %.2f:1" % (w, bg, r), r > 1.5, r)
    return stops, shot


def main():
    shots = os.path.join(L.SHOTS, "focus")
    os.makedirs(shots, exist_ok=True)
    old = json.load(io.open(REF, encoding="utf-8"))

    def go(port):
        base = "http://127.0.0.1:%d" % port
        # ── ① 목록 화면 한 바퀴 (브라우저 한 벌) ────────────────────────────
        #   ⚠ 한 바퀴를 다 돌면 포커스가 창 밖으로 나가 돌아오지 않는다(_g4_probe2) →
        #     **도는 일 하나에 브라우저 한 벌**을 쓴다. 그러지 않으면 뒤따르는 잰 값이 전부 거짓이다.
        b = L.browser(w=1366, h=768, base=base)
        try:
            b.js(ERRHOOK)
            open_list(b)
            # 쪽수 «▶» 와 검색칸은 흰 바탕 위다 («◀» 는 첫 쪽에서 잠겨 Tab 이 안 선다 — 실측)
            focus_walk(b, "목록 화면", shots, "01_list", ["nextpage", "f-q"],
                       {"nextpage": CANVAS, "f-q": CANVAS})
            errs = b.js("return (window.__errs || []).slice()")
            L.chk("⑥ 목록 화면 — 콘솔 오류 0", not errs, errs)
        finally:
            b.close()

        # ── ② 편집 화면 한 바퀴 (브라우저 한 벌) ────────────────────────────
        b = L.browser(w=1366, h=768, base=base)
        try:
            b.js(ERRHOOK)
            open_list(b)
            b.open_photo(FRUIT, STEM)
            time.sleep(1.2)
            # «◀» 는 검은 상단 바 위, «▸»(패널 접기)는 흰 패널 위다
            focus_walk(b, "편집 화면", shots, "02_edit", ["prev", "sidetgl"],
                       {"prev": (28, 28, 28), "sidetgl": CANVAS})
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        finally:
            b.close()

        # ── ③ 잰 값·마우스 클릭·회귀 (돌지 않는 브라우저 한 벌) ─────────────
        b = L.browser(w=1366, h=768, base=base)
        try:
            b.js(ERRHOOK)
            open_list(b)
            snap = measure(b)          # 여기서 사진이 열린다
            compare(snap, old)
            unhover(b)

            # ④ **마우스로 누르면 띠가 안 뜬다** — `:focus-visible` 의 값어치가 여기 있다
            d = float(b.js("return window.devicePixelRatio || 1"))
            r = b.js(RECTJS, ["#sidetgl"])["#sidetgl"]
            blur(b)
            b.click("#sidetgl")
            time.sleep(0.5)
            s = b.js(FOCUSJS)
            click_png = os.path.join(shots, "03_mouseclick.png")
            b.shot(click_png)
            n = ring_px(Image.open(click_png).convert("RGB"), r, d, ACCENT_DEEP)
            L.chk("④ 마우스로 누른 뒤에는 `:focus-visible` 이 아니다 (%s)" % (s and s.get("d")),
                  s.get("fv") is not True, s)
            L.chk("④ 그래서 그 단추 둘레에 띠 화소가 **0개**다 (%d개)" % n, n == 0, n)
            b.click("#sidetgl")        # 접었다 폈으니 되돌린다
            time.sleep(0.5)
            blur(b)

            # ⑤ 회귀 — 눌린 도구(U6)의 명암과 판정 5칸은 그대로다
            face = b.js(REALJS, ["#toolrail .tool.on", "#vbrow button.ok", "#vbrow button.save"])
            L.chk("⑤ 눌린 도구가 U6 의 짙은 파랑·그림자 그대로다 (%s)" % face["#toolrail .tool.on"]["bg"],
                  rgb(face["#toolrail .tool.on"]["bg"]) == (23, 100, 173)
                  and "inset" in face["#toolrail .tool.on"]["sh"], face["#toolrail .tool.on"])
            L.chk("⑤ 판정 «원본 OK» 초록 테두리 그대로 (%s)" % face["#vbrow button.ok"]["bt"],
                  rgb(face["#vbrow button.ok"]["bt"]) == (99, 189, 121), face["#vbrow button.ok"])
            L.chk("⑤ 판정 «저장» 진회색 그대로 (%s)" % face["#vbrow button.save"]["bg"],
                  rgb(face["#vbrow button.save"]["bg"]) == (34, 48, 63), face["#vbrow button.save"])

            errs = b.js("return (window.__errs || []).slice()")
            L.chk("⑥ 잰 값·클릭을 보는 동안 콘솔 오류 0", not errs, errs)
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        finally:
            b.close()

        # ⑥ 좁은 창 1200 · 휴대폰 폭 — ⚠ 이 파이어폭스는 500 아래로 안 줄어든다(shots12 실측)
        for w, tag in [(1200, "04_narrow_1200"), (390, "05_phone")]:
            b = L.browser(w=w, h=780, base=base)
            try:
                b.js(ERRHOOK)
                open_list(b)
                real = b.js("return window.innerWidth")
                stops, _ = walk(b, 24)
                bad = [(s["d"], s.get("col"), s.get("st")) for s in stops
                       if s.get("st") != "solid" or rgb(s["col"]) != ACCENT_DEEP]
                L.chk("⑥ 폭 %d(청한 값 %d) — 멈춘 %d군데가 전부 에메랄드 실선 띠다"
                      % (real, w, len(stops)), stops and not bad, bad)
                st = b.js(REALJS, ["#prevpage", "#f-q"])
                L.chk("⑥ 폭 %d — 쪽수 단추·검색칸 테두리가 --hairline-strong 이다" % real,
                      rgb(st["#prevpage"]["bt"]) == HAIR_S and rgb(st["#f-q"]["bt"]) == HAIR_S,
                      [st["#prevpage"]["bt"], st["#f-q"]["bt"]])
                b.shot(os.path.join(shots, tag + ".png"))
                errs = b.js("return (window.__errs || []).slice()")
                L.chk("⑥ 폭 %d — 콘솔 오류 0" % real, not errs, errs)
            finally:
                b.close()

        png = sorted(x for x in os.listdir(shots) if x.endswith(".png") and not x.startswith("_"))
        L.chk("화면 %d장을 남겼다 — %s" % (len(png), shots), len(png) >= 6, png)
        return 0

    source_checks()
    with_server(go)
    return L.summary("b22_focus")


if __name__ == "__main__":
    if "--capture" in sys.argv:
        sys.exit(capture())
    sys.exit(1 if main() else 0)
