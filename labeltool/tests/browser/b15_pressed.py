# -*- coding: utf-8 -*-
"""b15 — **고른 도구가 «눌려 들어간» 모양인가** (편의 U6).
작성: 2026-09-21

왜
  «지금 무슨 도구를 쥐고 있나» 를 알리는 표시가 **짙은 파랑 바탕 하나**뿐이었다. 구형 그림판이
  쓰는 «눌림» 세 가지는 이름만 있고 화면에는 없었다 —
    · 테두리(#2f6fe0)가 바탕(#1764ad)보다 **밝아서** 파인 것이 아니라 떠 보였고
    · 위 안쪽 그림자 rgba(24,62,110,.22) 는 짙은 바탕에 묻혀 **보이지 않았다**
      (고치기 전 실측 — «① 칠한 영역» 칸 위 안쪽 (32,51,70) 이 가운데 (34,48,63) 보다 오히려 밝다)
    · 얼굴이 내려앉지 않아 «누르기 전» 과 «누른 뒤» 가 같은 자리에 있었다.
  색 하나에만 기대면 색맹인 사람이나 밝은 햇빛 아래 노트북에서는 아무 표시도 없는 셈이 된다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 연다
    ② 고른 칸과 안 고른 칸이 바탕·테두리·그림자가 다르다
    ③ 눌린 칸의 **위 안쪽이 바탕보다 어둡다** — 진짜 화면 사진의 화소로 잰다
    ④ **아래 안쪽에 옅은 밝은 줄** 이 있다 (파인 자리의 앞턱)
    ⑤ **테두리가 바탕보다 어둡다** (밝으면 눌린 것이 아니라 빛나 보인다)
    ⑥ 얼굴(아이콘·글자·글쇠)이 **딱 1화소** 내려앉고 **칸 자리는 한 화소도 안 밀린다**
    ⑦ 흰 글자와 바탕의 대비가 WCAG AA(4.5:1) 아래로 안 떨어진다
    ⑧ 도구를 바꾸면 눌림이 **따라 옮겨 간다** (JS 는 한 줄도 안 고쳤다 — 이미 `.on` 을 옮긴다)
    ⑨ 세 작업 전부 — 상자 도구·번호 도구도 같은 규칙
    ⑩ 전문가 모드의 «보기 전환» 3단 스위치도 같이 눌린다
    ⑪ 번호 편집에서 **잠긴** 도구가 지금 그대로다 (회귀 — 잠금 규칙과 눌림 규칙이 겹치는 자리)
    ⑫ 좁은 창(1200)·휴대폰 폭(390) 에서 글자가 칸 밖으로 안 새어 나간다
    ⑬ 콘솔 오류 0 · 붓질 회귀
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b14 와 같다).

⚠ `S` 는 쪽의 전역이라 `b.js()` 안에서는 안 보인다 → `L.ev()`(window.eval) 로 부른다(b13·b14).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402
from PIL import Image                                    # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_pressed")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 한 칸의 «옷» 을 통째로 — 계산된 값과 화면 자리
FACE = """return (function (sel) {
  const e = document.querySelector(sel); if (!e) return null;
  const c = getComputedStyle(e), r = e.getBoundingClientRect();
  const kid = function (q) { const k = e.querySelector(q); if (!k) return null;
    const b = k.getBoundingClientRect(); return [Math.round(b.left * 100) / 100, Math.round(b.top * 100) / 100]; };
  return { on: e.classList.contains('on'), bg: c.backgroundColor, bc: c.borderTopColor,
           col: c.color, sh: c.boxShadow, pt: c.paddingTop, pb: c.paddingBottom,
           bw: Math.round(parseFloat(c.borderTopWidth)),
           rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
           ti: kid('.ti'), tw: kid('.tw'), tk: kid('.tk'),
           dis: !!e.disabled, lock: e.classList.contains('locked') };
})(arguments[0])"""

# 글자가 칸 밖으로 새어 나갔나 (좁은 창·휴대폰)
SPILL = """return (function (sel) {
  const e = document.querySelector(sel); if (!e) return null;
  const r = e.getBoundingClientRect(); let worst = 0;
  e.querySelectorAll('.ti, .tw').forEach(function (k) {
    const b = k.getBoundingClientRect();
    worst = Math.max(worst, r.top - b.top, b.bottom - r.bottom, r.left - b.left, b.right - r.right);
  });
  return Math.round(worst * 100) / 100;
})(arguments[0])"""


def rgb(s):
    """'rgb(23, 100, 173)' → (23,100,173)"""
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


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5631)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "pressed")
    os.makedirs(shots, exist_ok=True)
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        time.sleep(1.0)
        L.chk("① 기본은 쉬움 모드다", b.js("return document.body.classList.contains('easy')") is True)

        BRUSH = '.tool[data-tool="brush"]'
        TASK = '#taskbar .task[data-task="mask"]'

        # ── ② 고른 칸과 안 고른 칸이 다르다 ──────────────────────────────────
        b.key("b")
        time.sleep(0.4)
        on = b.js(FACE, BRUSH)
        off = b.js(FACE, '.tool[data-tool="erase"]')
        L.chk("② B 키로 붓을 골랐다", on["on"] is True and L.ev(b, "S.tool") == "brush",
              [on["on"], L.ev(b, "S.tool")])
        L.chk("② 고른 칸과 안 고른 칸의 **바탕**이 다르다 (%s ↔ %s)" % (on["bg"], off["bg"]),
              on["bg"] != off["bg"], [on["bg"], off["bg"]])
        L.chk("② 고른 칸과 안 고른 칸의 **테두리**가 다르다 (%s ↔ %s)" % (on["bc"], off["bc"]),
              on["bc"] != off["bc"], [on["bc"], off["bc"]])
        L.chk("② 안 고른 칸에는 안쪽 그림자가 아예 없다 (%s)" % off["sh"], off["sh"] == "none", off["sh"])
        L.chk("② 고른 칸에는 안쪽 그림자가 **두 겹** 있다(위 그늘 + 아래 밝은 줄)",
              on["sh"].count("inset") == 2, on["sh"])

        # ── ③④ 진짜 화면 사진으로 «파였나» 를 잰다 ──────────────────────────
        #   세 점 다 **칸 가운데 세로줄**에서 잰다. 안쪽 그림자는 폭 전체가 고르고, 이 줄의
        #   위 세 칸과 아래 네 칸에는 아이콘·글자가 닿지 않는다(실측).
        #   ⚠ 왼쪽 끝(x0+4)에서 재면 안 된다 — `border-radius:7px` 라 거기는 모서리가 휘어
        #     맨 아랫줄이 칸 **밖**이고, 그림자도 모서리를 감아 돌아 어둡게 나온다
        #     (첫 실행이 여기서 ④ 를 놓쳤다. 실측 x0+4 (19,77,136) ↔ 가운데 (65,123,178)).
        for name, sel in [("붓 도구", BRUSH), ("작업 ① 칠한 영역", TASK)]:
            f = b.js(FACE, sel)
            x0, y0, w, h = f["rect"]
            bw = f["bw"]
            pts = [(x0 + w / 2, y0 + bw + 1),          # 위 안쪽 (그늘)
                   (x0 + w / 2, y0 + h - bw - 1),      # 아래 안쪽 (밝은 줄)
                   (x0 + w / 2, y0 + h - bw - 4)]      # 글자 밑 맨바탕
            (top, bot, flat), _ = shot_px(b, os.path.join(shots, "_px.png"), pts)
            fill = rgb(f["bg"])
            L.chk("③ %s — 위 안쪽 %s 이 바탕 %s 보다 **어둡다**" % (name, top, fill),
                  lum(top) < lum(fill) * 0.85, [top, fill, round(lum(top), 4), round(lum(fill), 4)])
            L.chk("④ %s — 아래 안쪽 %s 이 바탕 %s 보다 **밝다**" % (name, bot, fill),
                  lum(bot) > lum(fill) * 1.15, [bot, fill, round(lum(bot), 4), round(lum(fill), 4)])
            L.chk("⑤ %s — 테두리 %s 가 바탕 %s 보다 어둡다" % (name, rgb(f["bc"]), fill),
                  lum(rgb(f["bc"])) <= lum(fill), [f["bc"], f["bg"]])
            # ⑦ 흰 글자가 앉는 맨바탕의 대비
            L.chk("⑦ %s — 흰 글자와 바탕 %s 의 대비 %.2f:1 ≥ 4.5 (WCAG AA)"
                  % (name, flat, ratio((255, 255, 255), flat)),
                  ratio((255, 255, 255), flat) >= 4.5, [flat, ratio((255, 255, 255), flat)])

        # ── ⑥ 얼굴은 1화소 내려앉고 칸 자리는 그대로 ────────────────────────
        b.key("e")                                        # 붓을 놓는다(지우개로)
        time.sleep(0.4)
        was = b.js(FACE, BRUSH)
        b.key("b")
        time.sleep(0.4)
        now = b.js(FACE, BRUSH)
        L.chk("⑥ 칸 자리가 한 화소도 안 밀렸다 %s" % (now["rect"],),
              now["rect"] == was["rect"], [was["rect"], now["rect"]])
        for part in ("ti", "tw"):
            d = round(now[part][1] - was[part][1], 2)
            L.chk("⑥ 눌리면 %s 가 정확히 1화소 내려앉는다 (%s → %s)"
                  % (part, was[part][1], now[part][1]), d == 1.0, d)
            # 좌우는 **반 화소 아래**로 못박는다. 0 이 아닌 까닭은 눌린 칸이 굵은 글씨
            # (`font-weight:700`, 내가 더한 것이 아니라 전부터 있던 줄)라 글자 폭이 조금
            # 달라지고, 가운데 맞춤이 그만큼 옮겨 앉기 때문이다. 내가 고친 여백은 위아래뿐이다.
            dx = round(now[part][0] - was[part][0], 2)
            L.chk("⑥ 좌우로는 반 화소도 안 움직인다 (%s · %s화소)" % (part, dx), abs(dx) < 0.5,
                  [was[part][0], now[part][0]])
        if now["tk"] and was["tk"]:
            d = round(now["tk"][1] - was["tk"][1], 2)
            L.chk("⑥ 글쇠 힌트(B)도 같이 1화소 내려앉는다 (%s → %s)" % (was["tk"][1], now["tk"][1]),
                  d == 1.0, d)
        L.chk("⑥ 위아래 여백의 **합** 은 그대로 4화소다 (%s + %s)" % (now["pt"], now["pb"]),
              (float(now["pt"][:-2]) + float(now["pb"][:-2])
               == float(was["pt"][:-2]) + float(was["pb"][:-2])), [was, now])
        b.shot(os.path.join(shots, "01_easy_mask.png"))

        # ── ⑧ 눌림이 도구를 따라 옮겨 간다 ──────────────────────────────────
        b.key("f")
        time.sleep(0.4)
        sm = b.js(FACE, '.tool[data-tool="smartadd"]')
        br = b.js(FACE, BRUSH)
        L.chk("⑧ F 로 자동채움을 고르니 눌림이 그쪽으로 옮겨 갔다",
              sm["on"] is True and br["on"] is False, [sm["on"], br["on"]])
        L.chk("⑧ 옮겨 간 칸도 같은 그림자를 입는다", sm["sh"] == on["sh"], [sm["sh"], on["sh"]])
        L.chk("⑧ 놓인 칸은 그림자가 없다", br["sh"] == "none", br["sh"])
        L.chk("⑧ 한 번에 **하나만** 눌려 있다 (도구 칸)",
              b.js("return document.querySelectorAll('#toolbox .tool.on').length") == 1,
              b.js("return document.querySelectorAll('#toolbox .tool.on').length"))
        b.key("b")
        time.sleep(0.3)
        b.shot(os.path.join(shots, "02_easy_brush_on.png"))

        # 눌린 칸 · 안 눌린 칸을 나란히 4배로 오려 둔다(사람 눈으로 대조하라고)
        f1, f2 = b.js(FACE, BRUSH), b.js(FACE, '.tool[data-tool="erase"]')
        im = Image.open(os.path.join(shots, "02_easy_brush_on.png")).convert("RGB")
        d = float(b.js("return window.devicePixelRatio || 1"))
        box = (int((f1["rect"][0] - 2) * d), int((f1["rect"][1] - 2) * d),
               int((f2["rect"][0] + f2["rect"][2] + 2) * d), int((f1["rect"][1] + f1["rect"][3] + 2) * d))
        im.crop(box).resize(((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.NEAREST) \
          .save(os.path.join(shots, "03_easy_tile_zoom.png"))

        # ── ⑨ 세 작업 전부 ──────────────────────────────────────────────────
        b.key("x")
        time.sleep(0.6)
        L.chk("⑨ 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        bd = b.js(FACE, '.btool[data-btool="draw"]')
        bp = b.js(FACE, '.btool[data-btool="pick"]')
        L.chk("⑨ 상자 «그리기» 가 눌려 있고 «고르기» 는 안 눌렸다",
              bd["on"] is True and bd["sh"] == on["sh"] and bp["sh"] == "none",
              [bd["on"], bd["sh"], bp["sh"]])
        b.shot(os.path.join(shots, "07_box_draw.png"))
        b.key("v")
        time.sleep(0.4)
        bd2 = b.js(FACE, '.btool[data-btool="draw"]')
        bp2 = b.js(FACE, '.btool[data-btool="pick"]')
        L.chk("⑨ V 를 누르면 눌림이 «고르기» 로 옮겨 간다",
              bp2["on"] is True and bp2["sh"] == on["sh"] and bd2["sh"] == "none",
              [bp2["on"], bp2["sh"], bd2["sh"]])
        L.chk("⑨ 상자 칸도 얼굴이 1화소 내려앉는다 (%s → %s)" % (bp["tw"][1], bp2["tw"][1]),
              round(bp2["tw"][1] - bp["tw"][1], 2) == 1.0, [bp["tw"][1], bp2["tw"][1]])
        b.shot(os.path.join(shots, "08_box_pick.png"))
        b.shot(os.path.join(shots, "10_easy_box.png"))
        b.key("x")
        time.sleep(0.5)
        L.chk("⑨ 상자 모드를 껐다", L.ev(b, "!!S.boxMode") is False)

        # ── ⑩ 전문가 모드의 «보기 전환» 3단 스위치 ──────────────────────────
        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.6)
        L.chk("⑩ 전문가 모드로 바꿨다",
              b.js("return document.body.classList.contains('easy')") is False)
        b.shot(os.path.join(shots, "04_adv_mask.png"))
        vs = b.js(FACE, '#viewsw .vsw[data-vm="over"]')
        L.chk("⑩ «겹쳐» 가 눌려 있다(기본)", vs["on"] is True and vs["rect"][2] > 0, vs["rect"])
        L.chk("⑩ 3단 스위치도 그림자 두 겹을 입는다", vs["sh"].count("inset") == 2, vs["sh"])
        x0, y0, w, h = vs["rect"]
        bw = vs["bw"]
        # 가로 줄이라 «가운데» 에는 글자가 있다. 오른쪽 끝에서 20화소 안쪽 — 글자(왼쪽에
        # 모여 있다)와 둥근 모서리(7화소) 둘 다 피한 자리다.
        pts = [(x0 + w - 20, y0 + bw + 1), (x0 + w - 20, y0 + h - bw - 1)]
        (vtop, vbot), _ = shot_px(b, os.path.join(shots, "_px.png"), pts)
        vfill = rgb(vs["bg"])
        L.chk("⑩ 3단 스위치 — 위 안쪽 %s 이 바탕 %s 보다 어둡다" % (vtop, vfill),
              lum(vtop) < lum(vfill) * 0.85, [vtop, vfill])
        L.chk("⑩ 3단 스위치 — 아래 안쪽 %s 이 바탕 %s 보다 밝다" % (vbot, vfill),
              lum(vbot) > lum(vfill) * 1.15, [vbot, vfill])
        was_v = b.js(FACE, '#viewsw .vsw[data-vm="photo"]')
        b.click('#viewsw .vsw[data-vm="photo"]')
        time.sleep(0.5)
        now_v = b.js(FACE, '#viewsw .vsw[data-vm="photo"]')
        L.chk("⑩ «원본만» 을 누르니 눌림이 옮겨 갔다", now_v["on"] is True, now_v["on"])
        L.chk("⑩ 3단 스위치 칸 자리도 한 화소도 안 밀린다 %s" % (now_v["rect"],),
              now_v["rect"] == was_v["rect"], [was_v["rect"], now_v["rect"]])
        L.chk("⑩ 3단 스위치 얼굴도 1화소 내려앉는다 (%s → %s)" % (was_v["tw"][1], now_v["tw"][1]),
              round(now_v["tw"][1] - was_v["tw"][1], 2) == 1.0,
              [was_v["tw"][1], now_v["tw"][1]])
        dxv = round(now_v["tw"][0] - was_v["tw"][0], 2)
        L.chk("⑩ 좌우 여백은 그대로다 — «원본만» 글자가 반 화소도 안 밀렸다 (%s화소)" % dxv,
              abs(dxv) < 0.5, [was_v["tw"][0], now_v["tw"][0]])
        b.shot(os.path.join(shots, "05_adv_viewsw_photo.png"))
        im = Image.open(os.path.join(shots, "05_adv_viewsw_photo.png")).convert("RGB")
        d = float(b.js("return window.devicePixelRatio || 1"))
        vr = b.js("const e=document.querySelector('#viewsw');const r=e.getBoundingClientRect();"
                  "return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)]")
        box = (int((vr[0] - 2) * d), int((vr[1] - 2) * d),
               int((vr[0] + vr[2] + 2) * d), int((vr[1] + vr[3] + 2) * d))
        im.crop(box).resize(((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.NEAREST) \
          .save(os.path.join(shots, "06_adv_viewsw_zoom.png"))
        b.click('#viewsw .vsw[data-vm="over"]')
        time.sleep(0.4)

        # ── ⑪ 번호 편집에서 잠긴 도구 (회귀) ────────────────────────────────
        #   잠금 규칙(`button:disabled`)과 눌림 규칙이 **같은 힘**이라 순서가 뒤집히면
        #   눌린 도구가 회색으로 바뀐다. 지금 그대로 짙은 파랑인지 못박는다.
        if L.ev(b, "!!S.inst"):
            b.key("k")
            time.sleep(0.7)
            L.chk("⑪ 번호 편집이 켜졌다", L.ev(b, "!!S.numMode") is True)
            lk = b.js(FACE, BRUSH)
            L.chk("⑪ 붓이 잠겼다(disabled · locked)", lk["dis"] is True and lk["lock"] is True,
                  [lk["dis"], lk["lock"]])
            L.chk("⑪ 잠겨도 눌린 칸의 바탕은 지금 그대로 짙은 파랑이다 (%s)" % lk["bg"],
                  rgb(lk["bg"]) == rgb(on["bg"]), [lk["bg"], on["bg"]])
            ne = b.js(FACE, '.ntool[data-ntool="erase"]')
            L.chk("⑪ 번호 도구 «지우기» 가 눌려 있고 같은 그림자를 입는다",
                  ne["on"] is True and ne["sh"] == on["sh"], [ne["on"], ne["sh"]])
            nm = b.js(FACE, '.ntool[data-ntool="merge"]')
            b.click('.ntool[data-ntool="merge"]')
            time.sleep(0.4)
            nm2 = b.js(FACE, '.ntool[data-ntool="merge"]')
            L.chk("⑪ 번호 도구도 눌리면 1화소 내려앉는다 (%s → %s)" % (nm["tw"][1], nm2["tw"][1]),
                  nm2["on"] is True and round(nm2["tw"][1] - nm["tw"][1], 2) == 1.0,
                  [nm["tw"][1], nm2["tw"][1]])
            b.shot(os.path.join(shots, "09_num_locked.png"))
            b.click('.ntool[data-ntool="erase"]')
            time.sleep(0.3)
            b.key("k")
            time.sleep(0.5)
            L.chk("⑪ 번호 편집을 껐다", L.ev(b, "!!S.numMode") is False)
        else:
            L.warn("⑪ 이 사진에는 번호본이 없어 잠긴 도구는 못 쟀다")
        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.5)

        # ── ⑬ 콘솔 · 붓질 회귀 ──────────────────────────────────────────────
        b.key("b")
        time.sleep(0.3)
        L.run(b, "S.undo.length = 0")
        pix0 = L.ev(b, "(function(){let n=0;const e=S.ed;for(let i=0;i<e.length;i++)if(e[i])n++;return n;})()")
        b.drag("#cv", 320, 250, 400, 300)
        time.sleep(0.4)
        pix1 = L.ev(b, "(function(){let n=0;const e=S.ed;for(let i=0;i<e.length;i++)if(e[i])n++;return n;})()")
        L.chk("⑬ 도구를 다 돌린 뒤에도 붓질이 그대로 칠해진다 (%d → %d 화소)" % (pix0, pix1),
              pix1 > pix0, [pix0, pix1])
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑬ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        b.close()
        b = None

        # ── ⑫ 좁은 창(1200) · 휴대폰 폭(390) ────────────────────────────────
        #   휴대폰에서는 도구 칸(#toolbox)이 통째로 숨는다(mobile.css) — 거기서는 «작업» 타일
        #   셋이 눌리는 칸이다. 숨은 칸을 재면 «안 새어 나갔다» 가 거저 통과하므로 칸마다
        #   **폭이 0 이 아닌지** 를 먼저 묻는다. 휴대폰 타일은 글자가 두 줄로 접힐 수 있어
        #   (`white-space:normal`) 위 여백을 1화소 늘린 것이 잘림으로 번지는지 여기서 본다.
        for w, tag, name, SEL in [(1200, "11_narrow_1200", "좁은 창 1200", BRUSH),
                                  (390, "12_phone_390", "휴대폰 폭 390", TASK)]:
            b = L.browser(w=w, h=780, base="http://127.0.0.1:%d" % port)
            b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
                 "s.dispatchEvent(new Event('change'))", FRUIT)
            b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
            L.close_tour(b)
            b.open_photo(FRUIT, STEM)
            time.sleep(1.2)
            b.key("b")
            time.sleep(0.5)
            f = b.js(FACE, SEL)
            sp = b.js(SPILL, SEL)
            L.chk("⑫ %s — 눌린 칸이 화면에 실제로 보인다 (%s)" % (name, f["rect"]),
                  f["on"] is True and f["rect"][2] > 0 and f["rect"][3] > 0, f)
            L.chk("⑫ %s — 글자·아이콘이 칸 밖으로 안 새어 나간다 (최대 %s화소)" % (name, sp),
                  sp <= 0, sp)
            L.chk("⑫ %s — 위아래 여백의 합이 그대로 4화소다 (%s + %s)" % (name, f["pt"], f["pb"]),
                  float(f["pt"][:-2]) + float(f["pb"][:-2]) == 4.0, [f["pt"], f["pb"]])
            b.shot(os.path.join(shots, tag + ".png"))
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
            b.close()
            b = None

        png = sorted(x for x in os.listdir(shots) if x.endswith(".png") and not x.startswith("_"))
        L.chk("화면 %d장을 남겼다 — %s" % (len(png), shots), len(png) == 12, png)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b15_pressed")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
