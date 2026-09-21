# -*- coding: utf-8 -*-
"""b21 — **도구상자·오른쪽 패널·목록 카드의 «바탕과 1px 선»이 무채색 토큰으로 접혔나** (디자인 G3).
작성: 2026-09-21

왜
  G2 는 상단 한 줄만 접었다. 그 아래는 아직 파랑회색이다 — 도구상자 #e4e9ef · 그 테두리 #ccd4dd ·
  칸 나눔 #b7c1cc · 도구 타일 테두리 #c3cbd4 · 패널 테두리 #ccd4dd · 작은 상자 #e3e8ee ·
  목록 줄·카드·쪽수 줄 #dde3ea · 사진 자리 #e9edf1 · 화면 바탕 #eef1f5. 아홉 가지가 «거의 같지만
  조금씩 다른 회색»이라, 어디를 고쳐도 옆 칸과 안 맞는다. 이것을 `--canvas*`·`--hairline*` 로 접는다.

  여기서 조용히 망가지는 길은 하나다 — **뜻이 묶인 색까지 같이 덮는 것**.
  레이어 4겹(빨강·파랑·초록·노랑분홍) · 판정 5칸 · 목록 카드의 상태 딱지와 테두리는 «예쁘게»
  맞추면 안 된다. 그래서 이 시험은 «바뀐 것이 맞나»가 아니라 **«바뀐 것이 그것뿐인가»** 를 묻는다.

어떻게
  고치기 **전에** 한 번 떠 둔 `b21_before.json` 과 지금을 칸칸이 댄다. 재는 칸은 106개이고
  칸마다 여덟 가지(바탕·바탕그림·글씨·테두리 넷·그림자)를 본다.
    · `EXPECT` 에 적은 (칸, 성질) 은 **반드시 바뀌었고 그 값이 토큰과 정확히 같아야** 한다
    · 거기 없는 나머지는 **한 글자도 달라지면 안 된다** (데이터 색이 여기 다 들어 있다)
  이 두 가지가 같이 통과해야 «색만, 그것도 내가 적은 칸만 바뀌었다» 를 말할 수 있다.

  덧붙여 —
    ① 소스에서 — `var()` 이름에 오타가 없고, 쓰는 자리가 상단 바 ∪ G3 목록뿐이며,
       G3 규칙에 옛 회색이 하나도 안 남았고, **밖에는 아직 남아 있다**(G4·G6 몫)
    ② 계단이 밝은 쪽 → 어두운 쪽 한 방향이다
    ③ 대비 — 도구상자 글씨가 새 바탕 위에서 AA(4.5:1) 위다
    ④ 1px 선 세기가 «보이되 시끄럽지 않다»(1.1~2.0) + 도구상자 가장자리는 전과 비슷하다
    ⑤ 자리 — 도구상자·패널·판정 줄·캔버스·카드가 **한 화소도** 안 밀렸다
    ⑥ 진짜 화면 사진의 화소로 — 도구상자 빈 자리 · 패널 빈 자리 · 목록 바탕 · 카드 바탕
    ⑦ 좁은 창 1200 · 휴대폰 폭 — 색이 그대로이고 카드가 안 깨진다 · 콘솔 오류 0

쓰는 법
    python3 tests/browser/b21_panels.py --capture   # 고치기 **전에** 한 번 (기준을 뜬다)
    python3 tests/browser/b21_panels.py             # 시험

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

SB = os.path.join(L.SB_ROOT, "sb_panels")
FRUIT = "peach"
STEM = "210629-t1-01"
CSS = os.path.join(L.T, "app", "static", "style.css")
REF = os.path.join(HERE, "b21_before.json")

# G3 가 꺼내 쓰는 토큰과 그 값 (style.css 의 :root · design_final.md 의 표)
CANVAS = (255, 255, 255)          # --canvas
SOFT = (250, 250, 250)            # --canvas-soft
SUNKEN = (244, 244, 244)          # --canvas-sunken
HAIR = (223, 223, 223)            # --hairline
HAIR_S = (199, 199, 199)          # --hairline-strong
HAIR_C = (237, 237, 237)          # --hairline-cool

# G3 가 접는 옛 회색 아홉 가지
OLD9 = ("#eef1f5", "#e4e9ef", "#ccd4dd", "#b7c1cc", "#c3cbd4", "#e3e8ee", "#dde3ea", "#e9edf1")
# `var()` 를 써도 되는 선택자 — 상단 바(G2) ∪ 아래 목록(G3). 여기 없는 자리에서 쓰면 실패다.
G2SEL = re.compile(r"#topbar|#navphoto|^\.who\b")
G3SEL = re.compile(r"^(body|#toolrail|#toolrail button|#side|\.railgrp|\.sbox|\.bar|\.vsep"
                   r"|\.card|\.card img|\.pager|\.dupstrip \.dupt|\.dupstrip \.dupt img)$")
# 0921 G4(단추·입력칸·포커스)가 더한 줄 — b20 과 같은 방식으로 **이름을 적어** 넓힌다.
# 0921 G6(그림자)이 `.tourcard`·`#saveflash.flashbad` 둘을 더했다(그림자는 이 둘뿐이다).
G4SEL = re.compile(r"^(button|button:hover|button:disabled:hover|select, input|:focus-visible"
                   r"|#toolrail button:hover|\.tourcard|#saveflash\.flashbad"
                   r"|#vbrow button\.big, #vbrow #taskbtns button\.big)$")

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# ── 재는 칸 ────────────────────────────────────────────────────────────────
# (이름, 끼워 넣을 조각, 그 안에서 집을 것) — 화면 상태에 기대지 않으려고 **직접 만들어** 잰다.
#   («칠한 영역 딱지가 마침 안 떠 있어서» 같은 이유로 못 재는 칸이 없게)
BODY_PROBES = [
    # 레이어 4겹 — 절대 안 바뀌는 데이터 색
    ("sw_red", "<span class='sw red'></span>", ".sw"),
    ("sw_blue", "<span class='sw blue'></span>", ".sw"),
    ("sw_green", "<span class='sw green'></span>", ".sw"),
    ("sw_diff", "<span class='sw diff'></span>", ".sw"),
    ("sw_inst", "<span class='sw inst'></span>", ".sw"),
    ("sw_num", "<span class='sw num'></span>", ".sw"),
    # 판정 5칸 — 절대 안 바뀌는 데이터 색
    ("vb_ok", "<button class='big ok'>가</button>", "button"),
    ("vb_ai", "<button class='big ai'>가</button>", "button"),
    ("vb_save", "<button class='big save'>가</button>", "button"),
    ("vb_save_unsaved", "<button class='big save unsaved'>가</button>", "button"),
    ("vb_flag", "<button class='big flag'>가</button>", "button"),
    ("vb_exc", "<button class='big exc'>가</button>", "button"),
    # 목록 카드의 상태 딱지 — 절대 안 바뀌는 데이터 색
    ("tag", "<span class='tag'>가</span>", ".tag"),
    ("tag_dup", "<span class='tag dup'>가</span>", ".tag"),
    ("tag_sus", "<span class='tag sus'>가</span>", ".tag"),
    ("tag_dice", "<span class='tag dice'>가</span>", ".tag"),
    ("tag_insterr", "<span class='tag insterr'>가</span>", ".tag"),
    ("tag_ninst", "<span class='tag ninst'>가</span>", ".tag"),
    ("tag_st_ok", "<span class='tag st ok'>가</span>", ".tag"),
    ("tag_st_fixed", "<span class='tag st fixed'>가</span>", ".tag"),
    ("tag_st_flag", "<span class='tag st flag'>가</span>", ".tag"),
    ("tag_st_exclude", "<span class='tag st exclude'>가</span>", ".tag"),
    ("tag_conf", "<span class='tag conf'>가</span>", ".tag"),
    ("tag_unconf", "<span class='tag unconf'>가</span>", ".tag"),
    # 목록 카드의 **상태 테두리** — 절대 안 바뀌는 데이터 색
    ("card_s_ok", "<div class='card s-ok'></div>", ".card"),
    ("card_s_fixed", "<div class='card s-fixed'></div>", ".card"),
    ("card_s_flag", "<div class='card s-flag'></div>", ".card"),
    ("card_s_exclude", "<div class='card s-exclude'></div>", ".card"),
    # 진행률 알약 — «확정 초록 / 미확정 회색» 한 쌍도 뜻이다
    ("pill", "<span class='pill'>1</span>", ".pill"),
    ("pill_unreviewed", "<span class='pill unreviewed'>1</span>", ".pill"),
    ("pill_ok", "<span class='pill ok'>1</span>", ".pill"),
    ("pill_fixed", "<span class='pill fixed'>1</span>", ".pill"),
    ("pill_flag", "<span class='pill flag'>1</span>", ".pill"),
    ("pill_exclude", "<span class='pill exclude'>1</span>", ".pill"),
    ("pill_conf", "<span class='pill conf'>1</span>", ".pill"),
    ("barbg", "<span class='barbg'></span>", ".barbg"),
    ("barfill", "<span class='barbg'><i class='barfill'></i></span>", ".barfill"),
    ("prog", "<span class='prog'>가</span>", ".prog"),
    ("chk", "<span class='chk'>가</span>", ".chk"),
    # 목록 거르개 단추 — 파랑·빨강은 뜻이다
    ("qf", "<button class='qf'>가</button>", "button"),
    ("qf_on", "<button class='qf on'>가</button>", "button"),
    ("qf_fq", "<button class='qf fq'>가</button>", "button"),
    ("qf_fq_on", "<button class='qf fq on'>가</button>", "button"),
    # 하단 상태 한 문장·개수 칸 — 뜻이 묶인 색
    ("todo", "<div class='todo'>가</div>", ".todo"),
    ("todo_go", "<div class='todo go'>가</div>", ".todo"),
    ("todo_warn", "<div class='todo warn'>가</div>", ".todo"),
    ("todo_done", "<div class='todo done'>가</div>", ".todo"),
    ("todo_cf", "<div class='todo'><span class='cf'>가</span></div>", ".cf"),
    ("todo_cf_on", "<div class='todo'><span class='cf on'>가</span></div>", ".cf"),
    ("cnts", "<span class='cnts'>1</span>", ".cnts"),
    ("cnts_hum", "<span class='cnts hum'>1</span>", ".cnts"),
    ("cnts_ne", "<span class='cnts ne'>1</span>", ".cnts"),
    # ── G3 가 **바꾸는** 칸 ──
    ("bar", "<div class='bar'></div>", ".bar"),
    ("vsep", "<div class='vsep'></div>", ".vsep"),
    ("card", "<div class='card'></div>", ".card"),
    ("card_img", "<div class='card'><img alt=''></div>", ".card img"),
    ("pager", "<div class='pager'></div>", ".pager"),
    ("sbox", "<details class='sbox'></details>", ".sbox"),
    ("numlock", "<details class='sbox numlock'></details>", ".sbox"),
    ("dupt", "<div class='dupstrip'><a class='dupt'></a></div>", ".dupt"),
    ("dupt_img", "<div class='dupstrip'><a class='dupt'><img alt=''></a></div>", ".dupt img"),
    ("dupt_me", "<div class='dupstrip'><a class='dupt me'></a></div>", ".dupt"),
    # ── 일부러 **안 건드린** 이웃들 — «다 지웠다» 는 착각을 막는다 (G4·G6 몫) ──
    ("dtable_th", "<table class='d'><tr><th>가</th></tr></table>", "th"),
    ("dtable_td", "<table class='d'><tr><td>가</td></tr></table>", "td"),
    ("tourhd", "<div class='tourcard'><div class='tourhd'>가</div></div>", ".tourhd"),
    ("tourft", "<div class='tourcard'><div class='tourft'>가</div></div>", ".tourft"),
    ("keyhelp_td", "<div class='keyhelp-body'><table><tr><td>가</td></tr></table></div>", "td"),
    ("numerr_er", "<div class='numerr'><div class='er'>가</div></div>", ".er"),
    ("btn", "<button>가</button>", "button"),
    ("inp", "<input>", "input"),
]

# 도구상자 **안**에 끼워야 `#toolrail button` 규칙이 닿는다
RAIL_PROBES = [
    ("tool", "<button class='tool'><span class='ti'>◉</span><span class='tw'>가</span>"
             "<span class='tk'>b</span></button>", "button"),
    ("tool_on", "<button class='tool on'><span class='ti'>◉</span><span class='tw'>가</span>"
                "<span class='tk'>b</span></button>", "button"),
    ("tool_dis", "<button class='tool' disabled><span class='tw'>가</span></button>", "button"),
    ("railgrp", "<div class='railgrp'></div>", ".railgrp"),
    ("railhint", "<div class='railhint'>가</div>", ".railhint"),
    ("railrange", "<div class='railrange'>가</div>", ".railrange"),
    ("railinfo", "<div class='railinfo'>가</div>", ".railinfo"),
]

# 진짜로 화면에 있는 칸 (조각이 아니라 그 자체를 잰다)
REAL = ["body", "#topbar", "#toolrail", "#side", "#sidebody", "#verdictbar", "#canvaswrap",
        "#cv", "#hud", "#taskbadge", "#easyguide", "#dupbox", "#toolrail .railhint",
        "#taskbar button.task.on", "#zoombar #zoompct", "#legend span.i"]
# 자리 — 색만 바꿨다면 한 화소도 안 밀려야 한다
RECTS_EDIT = ["#topbar", "#toolrail", "#maincol", "#canvaswrap", "#cv", "#side", "#sidebody",
              "#verdictbar", "#vbrow", "#todorow"]
RECTS_LIST = [".bar", "#grid", "#grid .card", ".pager", "#f-q"]


def four(key, val):
    return {(key, p): val for p in ("bt", "br", "bb", "bl")}


# **바뀌어야 하는 칸** — 여기 적힌 것만 바뀌고, 값은 토큰과 정확히 같아야 한다
EXPECT = {("body", "bg"): SOFT,
          ("#toolrail", "bg"): SUNKEN, ("#toolrail", "br"): HAIR,
          ("#side", "bl"): HAIR,
          ("railgrp", "bt"): HAIR_S,
          ("bar", "bb"): HAIR,
          ("vsep", "bl"): HAIR,
          ("card_img", "bg"): SUNKEN,
          ("pager", "bt"): HAIR,
          ("dupt_img", "bg"): SUNKEN}
EXPECT.update(four("card", HAIR))
EXPECT.update(four("sbox", HAIR_C))
EXPECT.update(four("numlock", HAIR_C))
EXPECT.update(four("dupt", HAIR))
EXPECT.update(four("tool", HAIR_S))
# 🔴 0921 G4 — 맨 밑바닥 단추·입력칸의 테두리가 #b9c2cc → --hairline-strong 으로 접혔다.
#   G3 때는 «일부러 안 건드린 이웃» 이라 «안 바뀌어야 할 칸» 쪽에 있었다. 단정을 푸는 것이
#   아니라 **바뀐 두 칸을 이름으로 옮긴다** — 나머지 91칸은 여전히 한 글자도 달라지면 안 된다.
EXPECT.update(four("btn", HAIR_S))
EXPECT.update(four("inp", HAIR_S))

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
    return { bg: c.backgroundColor, bi: c.backgroundImage, col: c.color, sh: c.boxShadow,
             bt: c.borderTopColor, br: c.borderRightColor,
             bb: c.borderBottomColor, bl: c.borderLeftColor }; }
})(arguments[0])"""

REALJS = """return (function (sels) {
  const out = {};
  sels.forEach(function (s) {
    const e = document.querySelector(s);
    if (!e) { out[s] = null; return; }
    const c = getComputedStyle(e);
    out[s] = { bg: c.backgroundColor, bi: c.backgroundImage, col: c.color, sh: c.boxShadow,
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


def rgb(s):
    """'rgb(223, 223, 223)' → (223,223,223)"""
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


def measure(b):
    """지금 화면에서 잴 수 있는 것을 다 잰다 — 목록 한 번, 사진을 연 뒤 한 번."""
    out = {"style": {}, "rect": {}}
    out["rect"].update({"list " + k: v for k, v in b.js(RECTJS, RECTS_LIST).items()})
    b.open_photo(FRUIT, STEM)
    time.sleep(1.2)
    out["style"].update(b.js(PROBE, {"host": "body", "specs": BODY_PROBES}) or {})
    out["style"].update(b.js(PROBE, {"host": "#toolrail", "specs": RAIL_PROBES}) or {})
    out["style"].update(b.js(REALJS, REAL))
    out["rect"].update({"edit " + k: v for k, v in b.js(RECTJS, RECTS_EDIT).items()})
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
    port = L.free_port(5681)
    p = L.start(port=port, sb=SB)
    try:
        return fn(port)
    finally:
        L.stop(p)


def capture():
    """고치기 **전에** 부른다 — 지금의 색과 자리를 통째로 적어 둔다."""
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
    """① 소스에서 — 오타 · var() 를 쓰는 자리 · 남은 옛 색."""
    raw = io.open(CSS, encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)          # 주석을 걷어낸다(색 이름이 적혀 있다)
    i = css.index(":root")
    root = css[i:css.index("}", i)]
    names = re.findall(r"(--[a-z0-9-]+)\s*:", root)
    used = sorted(set(re.findall(r"var\((--[a-z0-9-]+)\)", css)))
    L.chk("① 쓰이는 토큰 이름이 전부 :root 에 있다(오타 0)",
          all(u in names for u in used), [u for u in used if u not in names])

    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", css)
    bad, g3 = [], []
    for sel, body in rules:
        if "var(--" not in body:
            continue
        s = sel.strip().splitlines()[-1].strip()
        if G2SEL.search(s) or G4SEL.match(s):
            continue
        if G3SEL.match(s):
            g3.append(s)
        else:
            bad.append(s)
    L.chk("① `var()` 를 쓰는 규칙은 상단 바(G2) ∪ G3 ∪ G4 목록뿐이다", not bad, bad)
    L.chk("① G3 가 꺼내 쓰는 규칙 %d개 — %s" % (len(g3), " · ".join(g3)), len(g3) >= 12, g3)
    L.chk("① G3 가 꺼내 쓰는 토큰 이름이 여섯 계단 안에 있다",
          {"--canvas", "--canvas-soft", "--canvas-sunken", "--hairline",
           "--hairline-strong", "--hairline-cool"} <= set(used),
          [u for u in used if u.startswith(("--canvas", "--hairline"))])

    left = []
    for sel, body in rules:
        s = sel.strip().splitlines()[-1].strip()
        if not G3SEL.match(s):
            continue
        for o in OLD9:
            if o in body:
                left.append(s + " → " + o)
    L.chk("① G3 규칙에 옛 회색이 하나도 안 남았다", not left, left)
    rest = {o: css.count(o) for o in OLD9 if css.count(o)}
    L.chk("① G3 **밖**에는 아직 %d군데 남아 있다(G4·G6 몫) — %s"
          % (sum(rest.values()), rest), sum(rest.values()) > 0, rest)


def compare(snap, old):
    """②  «바뀐 것이 내가 적은 그것뿐인가» — 칸칸이 댄다."""
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
    L.chk("② 안 바뀌어야 할 %d칸이 **한 글자도** 안 달라졌다 (데이터 색이 여기 다 있다)" % kept,
          not extra, [(k, changed[k]) for k in extra[:8]])
    L.chk("② 바꾸기로 적은 %d칸이 **다 바뀌었다**" % len(EXPECT), not missed, missed)
    for k in sorted(EXPECT):
        if k in changed:
            got = changed[k][1]
            L.chk("② %s·%s = %s (전 %s)" % (k[0], k[1], got, changed[k][0]),
                  rgb(got) == EXPECT[k], [got, EXPECT[k]])

    # ⑤ 자리 — 색만 바꿨으면 한 화소도 안 밀린다
    moved = [(k, old["rect"].get(k), snap["rect"].get(k))
             for k in sorted(set(old["rect"]) | set(snap["rect"]))
             if old["rect"].get(k) != snap["rect"].get(k)]
    L.chk("⑤ 잰 자리 %d곳이 한 화소도 안 밀렸다" % len(snap["rect"]), not moved, moved[:5])
    L.chk("⑤ 잰 자리가 %d곳 이상이고 비어 있지 않다" % 10,
          len(snap["rect"]) >= 10 and all(snap["rect"].values()), snap["rect"])


def ladder_and_contrast(snap, old):
    """②③④ 계단·대비·선 세기."""
    lad = [("--canvas", CANVAS), ("--canvas-soft", SOFT), ("--canvas-sunken", SUNKEN),
           ("--hairline-cool", HAIR_C), ("--hairline", HAIR), ("--hairline-strong", HAIR_S)]
    ls = [round(lum(v), 4) for _, v in lad]
    L.chk("③ 계단이 밝은 쪽 → 어두운 쪽 한 방향이다 %s" % (ls,),
          all(ls[i] > ls[i + 1] for i in range(len(ls) - 1)), ls)

    rail = rgb(snap["style"]["#toolrail"]["bg"])
    body = rgb(snap["style"]["body"]["bg"])
    for nm, fg, bg in [("도구상자 아래 안내 글씨", rgb(snap["style"]["railhint"]["col"]), rail),
                       ("붓 굵기 줄 글씨", rgb(snap["style"]["railrange"]["col"]), rail),
                       ("도구 이름", rgb(snap["style"]["tool"]["col"]),
                        rgb(snap["style"]["tool"]["bg"])),
                       ("본문 글씨(목록 바탕 위)", rgb(snap["style"]["chk"]["col"]), body)]:
        r = ratio(fg, bg)
        L.chk("③ %s 대비 %.2f:1 ≥ 4.5 (%s / %s)" % (nm, r, fg, bg), r >= 4.5, [fg, bg, r])

    # ⚠ «전» 은 손으로 적지 않는다 — 고치기 전에 떠 둔 b21_before.json 에서 그대로 꺼내 센다.
    #   (선 색과 그 선이 놓인 바탕색 둘 다 전 값으로 재야 «세기» 를 견줄 수 있다)
    for nm, sel, prop, bgsel, fg, bg in [
            ("도구상자 가장자리", "#toolrail", "br", "#toolrail", HAIR, SUNKEN),
            ("도구상자 칸 나눔", "railgrp", "bt", "#toolrail", HAIR_S, SUNKEN),
            ("도구 타일 테두리", "tool", "bt", "tool", HAIR_S, CANVAS),
            ("목록 줄·쪽수 줄 밑선", "bar", "bb", "bar", HAIR, CANVAS),
            ("작은 상자 테두리", "sbox", "bt", "#side", HAIR_C, CANVAS)]:
        was = ratio(rgb(old["style"][sel][prop]), rgb(old["style"][bgsel]["bg"]))
        r = ratio(fg, bg)
        L.chk("④ %s 세기 %.2f:1 — 보이되(>1.1) 안 시끄럽다(<2.0)" % (nm, r), 1.1 < r < 2.0, r)
        L.chk("④ %s 세기가 전(%.2f)과 비슷하다 (차 %.2f ≤ 0.35)" % (nm, was, abs(r - was)),
              abs(r - was) <= 0.35, [was, r])


def main():
    shots = os.path.join(L.SHOTS, "panels")
    os.makedirs(shots, exist_ok=True)
    old = json.load(io.open(REF, encoding="utf-8"))

    def go(port):
        base = "http://127.0.0.1:%d" % port
        b = L.browser(w=1366, h=768, base=base)
        try:
            b.js(ERRHOOK)
            open_list(b)
            # ⑥ 목록 화면의 진짜 화소 — 카드 사이 빈 자리(= 화면 바탕)와 카드 바탕
            g = b.js(RECTJS, ["#grid", "#grid .card"])
            d = float(b.js("return window.devicePixelRatio || 1"))
            b.shot(os.path.join(shots, "01_list.png"))
            im = Image.open(os.path.join(shots, "01_list.png")).convert("RGB")
            c = g["#grid .card"]
            gap = im.getpixel((int((c[0] + c[2] + 4) * d), int((c[1] + c[3] / 2) * d)))
            cap = im.getpixel((int((c[0] + c[2] / 2) * d), int((c[1] + c[3] - 4) * d)))
            L.chk("⑥ 카드 사이 빈 자리 화소가 %s = --canvas-soft" % (gap,), gap == SOFT, gap)
            L.chk("⑥ 카드 바탕 화소가 %s = --canvas" % (cap,), cap == CANVAS, cap)

            snap = measure(b)          # 여기서 사진이 열린다
            compare(snap, old)
            ladder_and_contrast(snap, old)

            # ⑥ 편집 화면의 진짜 화소 — 도구상자 빈 자리 · 오른쪽 패널 빈 자리
            #   ⚠ `#sidebody` 가 아니라 `#side` 를 쓴다 — 오른쪽 패널은 **기본이 접힘**이라
            #     `#side.fold #sidebody{display:none}` 로 자리가 [0,0,0,0] 이다(실측).
            b.shot(os.path.join(shots, "02_edit.png"))
            im = Image.open(os.path.join(shots, "02_edit.png")).convert("RGB")
            r = snap["rect"]["edit #toolrail"]
            s = snap["rect"]["edit #side"]
            railpx = im.getpixel((int((r[0] + 2) * d), int((r[1] + r[3] - 3) * d)))
            sidepx = im.getpixel((int((s[0] + 2) * d), int((s[1] + s[3] - 6) * d)))
            L.chk("⑥ 도구상자 빈 자리 화소가 %s = --canvas-sunken" % (railpx,),
                  railpx == SUNKEN, railpx)
            L.chk("⑥ 오른쪽 패널 빈 자리 화소가 %s = --canvas" % (sidepx,), sidepx == CANVAS, sidepx)
            # 도구상자 오른쪽 가장자리 1px 선
            line = None
            y = int((r[1] + r[3] / 2) * d)
            for x in range(int((r[0] + r[2] - 3) * d), int((r[0] + r[2] + 2) * d)):
                px = im.getpixel((x, y))
                if px == HAIR:
                    line = (x, px)
                    break
            L.chk("⑥ 도구상자 가장자리 1px 선이 %s = --hairline" % (line and line[1],),
                  bool(line), line)

            errs = b.js("return (window.__errs || []).slice()")
            L.chk("⑦ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        finally:
            b.close()

        # ⑦ 좁은 창 1200 · 휴대폰 폭 — ⚠ 이 파이어폭스는 500 아래로 안 줄어든다(shots12 실측)
        for w, tag in [(1200, "03_narrow_1200"), (390, "04_phone")]:
            b = L.browser(w=w, h=780, base=base)
            try:
                b.js(ERRHOOK)
                open_list(b)
                real = b.js("return window.innerWidth")
                st = b.js(REALJS, ["body", "#toolrail", "#side"])
                L.chk("⑦ 폭 %d(청한 값 %d) — 화면 바탕이 --canvas-soft %s"
                      % (real, w, rgb(st["body"]["bg"])), rgb(st["body"]["bg"]) == SOFT,
                      st["body"]["bg"])
                n = b.js("return document.querySelectorAll('#grid .card').length")
                fit = b.js("return (function(){const g=document.querySelector('#grid');"
                           "const gr=g.getBoundingClientRect();let worst=0;"
                           "g.querySelectorAll('.card').forEach(function(c){const r="
                           "c.getBoundingClientRect();worst=Math.max(worst,gr.left-r.left,"
                           "(r.left+r.width)-(gr.left+gr.width));});"
                           "return Math.round(worst*100)/100;})()")
                L.chk("⑦ 폭 %d — 카드 %d장이 목록 밖으로 안 샌다 (최대 %s화소)" % (real, n, fit),
                      n > 0 and fit <= 0.5, [n, fit])
                b.open_photo(FRUIT, STEM)
                time.sleep(1.2)
                st = b.js(REALJS, ["#toolrail", "#side"])
                L.chk("⑦ 폭 %d — 도구상자 바탕이 --canvas-sunken %s"
                      % (real, rgb(st["#toolrail"]["bg"])),
                      rgb(st["#toolrail"]["bg"]) == SUNKEN, st["#toolrail"]["bg"])
                b.shot(os.path.join(shots, tag + ".png"))
                errs = b.js("return (window.__errs || []).slice()")
                L.chk("⑦ 폭 %d — 콘솔 오류 0" % real, not errs, errs)
                L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
            finally:
                b.close()

        png = sorted(x for x in os.listdir(shots) if x.endswith(".png") and not x.startswith("_"))
        L.chk("화면 %d장을 남겼다 — %s" % (len(png), shots), len(png) == 4, png)
        return 0

    source_checks()
    with_server(go)
    return L.summary("b21_panels")


if __name__ == "__main__":
    if "--capture" in sys.argv:
        sys.exit(capture())
    sys.exit(1 if main() else 0)
