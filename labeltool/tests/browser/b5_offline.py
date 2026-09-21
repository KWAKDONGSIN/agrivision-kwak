# -*- coding: utf-8 -*-
"""b5 — **서버가 없어졌을 때** 저장이 조용히 씹히지 않는가 (편의·안정성 S1).
작성: 2026-09-21

왜
  `api.js` 의 `fetch` 에는 `.catch` 가 없었다. 감시자가 서버를 다시 켜거나 와이파이가 끊긴
  그 순간에 «저장» 을 누르면 약속(Promise)이 깨지고 `await` 가 거기서 멈춘다 —
  화면에는 «저장 중…» 만 남고 **아무 말도 없다**. 사람은 저장된 줄 알고 다음 장으로 넘어간다.

어떻게
  모래상자 서버를 띄워 사진 한 장을 연 뒤 **내가 띄운 그 서버만** 끄고(남의 것은 건드리지 않는다)
    ① `API.get` 이 깨지지 않고 `{ok:false, error:…}` 로 **돌아오는가**
    ② «저장»(#btn-save)을 누르면 `#saveflash` 에 **붉은** 글씨가 뜨는가
    ③ 콘솔에 unhandled rejection 이 **없는가**
    ④ 화면이 안 멈추는가(사진·작업이 그대로 남아 있다)
  를 잰다. 서버를 끄는 시험이라 `run_all.sh --browser` 묶음과 따로 돌려도 된다.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_offline")
FRUIT = "peach"
STEM = "210629-t1-01"
HOOK = ("window.__errs = window.__errs || [];"
        "if (!window.__hooked) { window.__hooked = 1;"
        " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
        " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
        "return window.__errs.length;")


def flash_now(b):
    return b.js("const e=document.querySelector('#saveflash');"
                "return e ? [e.textContent, getComputedStyle(e).color] : null;")


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5531)
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
        b.js("document.querySelector('#saveflash').textContent='';")

        # ── 여기서부터 «서버가 사라진» 상황. 내가 띄운 PID 만 끈다.
        L.stop(p)
        p = None
        time.sleep(1.0)

        # ① API.get 이 깨지지 않고 돌아온다
        b.js("window.__r='(아직)';"
             "window.eval(\"API.get('/api/health').then(j=>{window.__r=j},e=>{window.__r='깨짐:'+e})\")")
        for _ in range(60):
            r = b.js("return window.__r")
            if r != "(아직)":
                break
            time.sleep(0.5)
        r = b.js("return window.__r")
        L.chk("① 서버가 없어도 API.get 이 답을 돌려준다(약속이 깨지지 않는다)", isinstance(r, dict), r)
        L.chk("① 그 답이 {ok:false, error:…} 모양이다",
              isinstance(r, dict) and r.get("ok") is False and bool(r.get("error")), r)

        # ② «저장» 을 누르면 붉은 알림
        b.click("#btn-save")
        time.sleep(1.5)
        # 저장 단추를 처음 누르면 «내 이름» 을 한 번 묻는다(main.js 의 가로채기 → ensureWho).
        # 이 시험이 보는 것과 상관없는 기존 장치이므로 치우고 지나간다.
        dlg = L.eat_alert(b)
        print("  (겹창) %r" % (dlg,), flush=True)
        txt, color = "", ""
        for _ in range(60):
            f = flash_now(b)
            txt, color = (f or ["", ""])[0], (f or ["", ""])[1]
            if txt and "저장 중" not in txt:
                break
            time.sleep(0.5)
        L.chk("② 저장을 눌렀을 때 알림이 뜬다(조용히 씹히지 않는다)", bool(txt) and "저장 중" not in txt, txt)
        L.chk("② 그 알림이 «서버에 닿지 못했습니다» 다", "닿지 못했" in (txt or ""), txt)
        # flash(…, true) 의 붉은색 #ffb3b3 = rgb(255, 179, 179)
        L.chk("② 알림이 붉은색이다(실패로 보인다)", "255, 179, 179" in (color or ""), color)

        # ③ 콘솔에 깨진 약속이 없다
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("③ unhandled rejection 이 없다", not [e for e in errs if str(e).startswith("reject:")], errs)

        # ④ 화면이 멈추지 않는다 — 사진·작업이 그대로고 단축키도 듣는다
        L.chk("④ 보던 사진이 그대로다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        b.key("x")
        time.sleep(0.8)
        L.chk("④ 화면이 안 멈췄다(X 로 상자 모드가 켜진다)", L.ev(b, "!!S.boxMode") is True)
        b.key("x")
        time.sleep(0.4)
        os.makedirs(os.path.join(L.SHOTS, "offline"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "offline", "save_when_server_down.png"))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b5_offline")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
