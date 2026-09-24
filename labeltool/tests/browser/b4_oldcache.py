# -*- coding: utf-8 -*-
"""b4 — «옛 index.html 을 캐시에서 쓰는 브라우저» 가 깨지지 않는가 (Ctrl+F5 전 실측).
작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» 1차)

왜
  정적 파일은 **서버를 다시 켜지 않아도 그 자리에서 바로 나간다.** 그래서 새 `index.html` 을
  올리는 순간, 이미 툴을 열어 둔 사람의 브라우저는 아직 **옛 index.html** 을 들고 있을 수 있다.
  옛 index.html 은 `/static/app.js` 와 `/static/ui.js` 두 개만 부른다 — 그 둘을 비워 두면
  그 사람 화면은 **새로고침(Ctrl+F5) 전까지 통째로 죽는다.**
  그래서 옛 `app.js` 를 «새 파일 12개를 대신 불러 주는 다리» 로 남겼다. 이 시험이 그 다리를 잰다.

어떻게
  **모래상자 안에서** 지금 `index.html` 의 `<script>` 칸만 옛 두 줄(`app.js`·`ui.js`)로 바꾼 쪽을
  `index_oldcache_test.html` 로 만들고(정본 `app/static/` 에는 아무것도 남기지 않는다),
  진짜 파이어폭스로 그 쪽을 연다. = «캐시에 옛 index.html 이 있는 사람» 과 같은 상황이다.
  ① 화면이 뜨고(과일 칸·카드) ② 콘솔 오류 0 ③ 사진 한 장이 열리고 단축키가 듣는다.
"""
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_oldcache")
FRUIT = "peach"
STEM = "210629-t1-01"
HOOK = ("window.__errs = window.__errs || [];"
        "if (!window.__hooked) { window.__hooked = 1;"
        " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
        " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
        "return window.__errs.length;")


def make_old_index(sb):
    """모래상자 안에서만 «옛 index.html» 을 만든다 — 지금 index 의 <script> 칸만 옛 두 줄로."""
    src = io.open(os.path.join(sb, "app", "static", "index.html"), encoding="utf-8").read()
    i = src.find("<!-- 화면(JS)")
    j = src.find("</body>")
    if i < 0 or j < 0 or j < i:
        return None
    old = (src[:i] + '<script src="/static/app.js"></script>\n'
                     '<script src="/static/ui.js"></script>\n' + src[j:])
    p = os.path.join(sb, "app", "static", "index_oldcache_test.html")
    io.open(p, "w", encoding="utf-8").write(old)
    return p


def main():
    static = os.path.join(L.T, "app", "static")
    if not os.path.isdir(os.path.join(static, "js")):
        L.warn("쪼개기 전 판이라 건너뜁니다(다리가 필요 없다)")
        return L.summary("b4_oldcache")
    L.sync(SB)
    L.reset_status(SB)
    old = make_old_index(SB)
    L.chk("모래상자에 «옛 index.html» 을 만들었다(정본에는 남기지 않는다)", bool(old), old)
    if not old:
        return L.summary("b4_oldcache")
    port = L.free_port(5521)
    p = L.start(port=port, sb=SB)
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.go("/static/index_oldcache_test.html")
        time.sleep(2.0)
        b.js(HOOK)
        ev = lambda e: b.js("return window.eval(arguments[0])", e)
        L.chk("옛 index.html 로 들어와도 화면이 산다(과일 칸이 채워진다)",
              b.js("return document.querySelectorAll('#fruit option').length") > 0)
        L.chk("전역 셋이 다 있다(다리가 12파일을 순서대로 불렀다)",
              ev("(function(){try{return [typeof S, typeof API, typeof UI].join(',')}"
                 "catch(e){return 'ReferenceError'}})()") == "object,object,object")
        for fn, expr in [("mask.js", "UI.setTool"), ("boxes.js", "UI.saveBoxes"),
                         ("instances.js", "UI.numKey"), ("keys.js", "UI.KEYS")]:
            got = ev("(function(){try{return typeof (%s)}catch(e){return 'ReferenceError'}})()" % expr)
            L.chk("다리가 부른 파일이 살아 있다: %s" % fn, got in ("function", "object"), got)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("사진이 열린다", ev("S.stem") == STEM, ev("S.stem"))
        b.key("x")
        time.sleep(0.8)
        L.chk("단축키가 듣는다(X = 상자 모드)", ev("!!S.boxMode") is True)
        b.key("x")
        time.sleep(0.5)
        os.makedirs(os.path.join(L.SHOTS, "oldcache"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "oldcache", "old_index_bridge.png"))
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("콘솔 오류 0", not errs, errs)
        # 새 index.html 로 들어오면 다리는 아예 불리지 않는다(두 번 실리지 않는다)
        b.go("/old")  # 0923: 옛 툴은 /old
        time.sleep(2.0)
        n = b.js("return document.querySelectorAll('script[src*=\"/static/app.js\"]').length")
        L.chk("새 index.html 은 옛 app.js 를 부르지 않는다(두 번 실릴 일이 없다)", n == 0, n)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b4_oldcache")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
