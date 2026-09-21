# -*- coding: utf-8 -*-
"""b7 — **서버가 죽으면 말해 주는가 · 살아나면 저절로 지워지는가** (편의·안정성 S3).
작성: 2026-09-21

왜
  S1·S2 는 «사람이 무엇을 눌렀을 때» 만 말해 준다. 사람이 아무것도 안 누르고 30분을 칠하는
  동안 서버가 죽어 있으면 그 30분은 아무도 알려 주지 않는다 — «저장» 을 누르는 순간에야
  붉은 띠를 보고, 그때는 이미 늦다. → 30초마다 `/api/health` 를 두드려 화면 맨 위에 알린다.

어떻게
  모래상자 서버를 띄워 사진 한 장을 연 뒤 **내가 띄운 그 서버만** 껐다 켠다(남의 것은 건드리지
  않는다). 재시작은 **같은 포트**에 다시 띄운다 — 로그인 쿠키가 비밀번호로 서명돼 있어
  (`core/auth.py`) 서버를 다시 켜도 그대로 살아 있다.
    ⓪ 잘 도는 동안에는 배너가 화면에 **아예 없다**(DOM 에 요소가 늘지 않는다)
    ① 서버를 끄고 **아무것도 누르지 않아도** 35초 안에 붉은 배너가 뜬다 (= 30초 감시)
    ② 그 배너가 상단 바를 **덮지 않고 밀어 내린다**(과일 고르개가 그대로 눌린다)
    ③ 서버를 다시 켜면 **아무것도 누르지 않아도** 20초 안에 배너가 저절로 사라진다
    ④ 사라진 뒤 `body.netdown` 도 빠지고 상단 바가 제자리로 돌아온다
    ⑤ 배너와 S2 의 실패 띠가 **겹치지 않는다** — 둘 다 떠 있을 때 «확인» 단추가 눌린다
    ⑥ 배너가 떠 있어도 화면이 안 멈추고 콘솔에 오류가 없다
  를 잰다. 서버를 껐다 켜는 시험이라 `run_all.sh --browser` 묶음과 따로 돌린다(b5·b6 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_health")
FRUIT = "peach"
STEM = "210629-t1-01"
HOOK = ("window.__errs = window.__errs || [];"
        "if (!window.__hooked) { window.__hooked = 1;"
        " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
        " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
        "return window.__errs.length;")

# 배너의 지금 상태를 한 번에 읽는다 — 있나 · 보이나 · 글자 · 색 · 높이 · body 딱지
STATE = ("const e = document.querySelector('#netdown');"
         "if (!e) return { exists: false, on: false, body: document.body.classList.contains('netdown') };"
         "const cs = getComputedStyle(e); const r = e.getBoundingClientRect();"
         "return { exists: true, on: e.classList.contains('on'),"
         "         shown: cs.display !== 'none' && r.height > 0,"
         "         text: e.textContent, bg: cs.backgroundColor, h: Math.round(r.height),"
         "         body: document.body.classList.contains('netdown') };")

TOPBAR_TOP = "const r=document.querySelector('#topbar').getBoundingClientRect(); return Math.round(r.top);"


def state(b):
    return b.js(STATE)


def wait_banner(b, want, secs):
    """배너가 보이는/안 보이는 상태가 될 때까지 기다린다. 걸린 초를 돌려준다(못 되면 None)."""
    t0 = time.time()
    while time.time() - t0 < secs:
        st = state(b)
        if bool(st.get("shown")) is want:
            return round(time.time() - t0, 1)
        time.sleep(0.5)
    return None


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5551)
    p = L.start(port=port, sb=SB)
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("사진이 열렸다(서버가 살아 있는 동안)", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        b.js(HOOK)

        # ⓪ 잘 도는 동안에는 배너 요소가 아예 없다
        st = state(b)
        top0 = b.js(TOPBAR_TOP)
        L.chk("⓪ 서버가 멀쩡할 때는 배너 요소가 화면에 없다", st.get("exists") is False, st)
        L.chk("⓪ body 에 netdown 딱지도 없다", st.get("body") is False, st)
        L.chk("⓪ 상단 바는 맨 위(0px)에 있다", top0 == 0, top0)

        # ── ① 서버를 끄고 **아무것도 누르지 않는다**. 30초 감시가 스스로 알아채야 한다.
        #    끄기 직전에 한 번 확인시켜 30초 시계를 새로 맞춘다 — 그래야 «끈 뒤 30초» 를 잰다.
        L.run(b, "UI.netProbe()")                # 화면 전역은 window.eval 로만 보인다(L.run)
        time.sleep(1.0)
        L.stop(p)
        p = None
        took = wait_banner(b, True, 45)
        L.chk("① 아무것도 안 눌러도 배너가 뜬다(30초 감시)", took is not None, took)
        L.chk("① 그 시각이 30초 감시와 맞는다(25~40초)",
              took is not None and 25 <= took <= 40, took)
        st = state(b)
        L.chk("① 배너가 붉은색이다", "179, 38, 30" in (st.get("bg") or ""), st.get("bg"))
        L.chk("① 배너에 «연결되지 않습니다» 가 적혀 있다", "연결되지 않습니다" in (st.get("text") or ""),
              st.get("text"))
        L.chk("① body 에 netdown 딱지가 붙었다", st.get("body") is True, st)

        # ② 상단 바를 덮지 않고 밀어 내린다 — 과일 고르개가 여전히 눌린다
        top1 = b.js(TOPBAR_TOP)
        L.chk("② 상단 바가 배너 높이(32px)만큼 내려갔다(덮이지 않았다)",
              top1 == st.get("h") and top1 > 0, [top1, st.get("h")])
        hit = b.js("const x=document.querySelector('#fruit'); const r=x.getBoundingClientRect();"
                   "const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);"
                   "return { hit: e===x, got: e ? (e.id || e.tagName) : null };")
        L.chk("② 배너가 떠 있어도 과일 고르개가 그대로 눌린다", bool(hit.get("hit")), hit)
        os.makedirs(os.path.join(L.SHOTS, "health"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "health", "banner_server_down.png"))

        # ── ③ 서버를 **같은 포트**에 다시 켠다. 역시 아무것도 누르지 않는다.
        p = L.start(port=port, sb=SB)
        back = wait_banner(b, False, 20)
        L.chk("③ 서버가 살아나면 아무것도 안 눌러도 배너가 사라진다", back is not None, back)
        st = state(b)
        top2 = b.js(TOPBAR_TOP)
        L.chk("④ body 의 netdown 딱지도 함께 빠진다", st.get("body") is False, st)
        L.chk("④ 상단 바가 제자리(0px)로 돌아온다", top2 == 0, top2)

        # ── ⑤ 배너와 S2 의 실패 띠가 겹치지 않는가 — 다시 끄고 «저장» 을 눌러 둘 다 띄운다
        L.stop(p)
        p = None
        time.sleep(1.0)
        b.click("#btn-save")
        time.sleep(1.5)
        dlg = L.eat_alert(b)                     # 첫 저장 때 한 번 묻는 «내 이름» 겹창(기존 장치)
        print("  (겹창) %r" % (dlg,), flush=True)
        took2 = wait_banner(b, True, 20)
        L.chk("⑤ 저장이 실패하면 배너가 곧바로 뜬다(30초를 안 기다린다)",
              took2 is not None and took2 <= 10, took2)
        two = b.js("const n=document.querySelector('#netdown');"
                   "const f=document.querySelector('#saveflash');"
                   "const k=f && f.querySelector('.flashok');"
                   "if (!n || !k) return { why: '둘 중 하나가 없다', n: !!n, k: !!k };"
                   "const nr=n.getBoundingClientRect(), kr=k.getBoundingClientRect();"
                   "const e=document.elementFromPoint(kr.left+kr.width/2, kr.top+kr.height/2);"
                   "return { hit: e===k, got: e ? (e.className || e.tagName) : null,"
                   "         nbot: Math.round(nr.bottom), ktop: Math.round(kr.top) };")
        L.chk("⑤ 둘 다 떠 있어도 «확인» 단추가 가려지지 않고 눌린다", bool(two.get("hit")), two)
        L.chk("⑤ 실패 띠가 배너 아래에 있다(겹치지 않는다)",
              two.get("ktop") is not None and two.get("nbot") is not None
              and two["ktop"] >= two["nbot"], two)
        b.shot(os.path.join(L.SHOTS, "health", "banner_with_save_error.png"))

        # ⑥ 화면이 안 멈추고 콘솔이 깨끗하다
        L.chk("⑥ 보던 사진이 그대로다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        b.key("x")
        time.sleep(0.8)
        L.chk("⑥ 화면이 안 멈췄다(X 로 상자 모드가 켜진다)", L.ev(b, "!!S.boxMode") is True)
        b.key("x")
        time.sleep(0.4)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑥ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b7_health")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
