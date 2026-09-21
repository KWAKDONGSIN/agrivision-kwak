# -*- coding: utf-8 -*-
"""b9 — **저장이 느릴 때 두 번 눌러도 한 번만 가는가** (편의·안정성 S6).
작성: 2026-09-21

왜
  1664×1248 마스크 한 장은 PNG 로 접어 올리는 데 1~2초가 걸린다. 그동안 화면에 바뀌는 것은
  «저장 중…» 한 줄뿐이라, 사람은 «안 눌렸나» 하고 한 번 더 누른다. 그러면 같은 것이 두 번
  올라가고, 판정 단추는 끝에 `nextItem()` 이 붙어 있어 **보지도 않은 사진을 한 장 건너뛴다.**
  Ctrl+S 를 누른 채 있으면 키 반복이 그대로 서버로 간다.

어떻게
  모래상자 서버에 진짜 파이어폭스로 붙어, 화면 안의 `fetch` 를 감싸 **POST 를 1.5초 늦춘다**
  (서버는 건드리지 않는다 — 느린 것은 «응답» 이지 서버가 아니다). 그리고
    ① 수정본 저장(#btn-save)을 잇달아 두 번 눌러 `/api/save` 가 **한 번만** 가는지
    ② 그동안 단추에 «.saving» 딱지가 붙고, 마우스로는 아예 안 닿는지(pointer-events)
    ③ 다 끝나면 딱지가 떨어지고 **다시 눌리는지**(영영 잠기지 않는다)
    ④ Ctrl+S 를 다섯 번 연타해도 한 번만 가는지
    ⑤ 상자 저장(#boxsave)도 같은지
    ⑥ 번호 저장(#numsave)도 같은지 — 그 사진에 번호가 있을 때만
    ⑦ 콘솔에 깨진 약속·오류가 없는지
  를 잰다. `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b8 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_double")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# POST 를 세고, **답을 `window.__delay` 밀리초만큼 늦게 넘겨준다**(느린 서버 흉내).
#   · 보내는 것은 곧바로 보낸다 — 그래야 서버가 실제로 저장하고, «한 번 간 그 요청이 제대로
#     들어갔는지» 까지 잴 수 있다. 늦추는 것은 «화면이 답을 보는 시각» 뿐이다.
#   · 세는 자리는 보내기 직전이라 «화면이 몇 번 보내려 했나» 를 그대로 잡는다(잠금이 들으면
#     두 번째는 여기까지 오지 않는다).
#   ⚠ `orig.apply(window, …)` — `this` 를 그대로 넘기면 안 된다. 화면 코드는 `fetch(url, opt)` 를
#     맨이름으로 부르므로 `this` 가 undefined 로 오고, 파이어폭스는 그때
#     «'fetch' called on an object that does not implement interface Window» 로 **거절**한다
#     (2026-09-21 실측 — 그 바람에 POST 가 한 건도 서버에 닿지 않았다).
FETCHHOOK = """
window.__posts = window.__posts || [];
window.__delay = 0;
if (!window.__fhooked) {
  window.__fhooked = 1;
  const orig = window.fetch;
  window.fetch = function (url, opt) {
    const isPost = !!(opt && String(opt.method).toUpperCase() === 'POST');
    if (isPost) window.__posts.push(String(url).replace(/^https?:\\/\\/[^/]+/, ''));
    const p = orig.apply(window, arguments);
    const d = isPost ? (window.__delay || 0) : 0;
    if (!d) return p;
    return p.then(function (r) {
      return new Promise(function (res) { setTimeout(function () { res(r); }, d); });
    });
  };
}
return true;
"""

SAVING = ("return [...document.querySelectorAll(arguments[0].join(','))]"
          ".map(e => [e.id, e.classList.contains('saving')]);")


def posts(b, url):
    return [u for u in b.js("return (window.__posts || []).slice()") if u == url]


def reset_posts(b, delay):
    b.js("window.__posts = []; window.__delay = arguments[0];", delay)


def wait_unlocked(b, sel, secs=20):
    """딱지가 떨어질 때까지 기다린다(= 저장이 끝났다). 걸린 초를 돌려준다."""
    t0 = time.time()
    while time.time() - t0 < secs:
        if not b.js("const e=document.querySelector(arguments[0]);"
                    "return !!e && e.classList.contains('saving');", sel):
            return round(time.time() - t0, 1)
        time.sleep(0.2)
    return None


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5561)
    p = L.start(port=port, sb=SB)
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        # 첫 저장 때 한 번 묻는 «내 이름» 겹창은 이 시험이 보는 것이 아니다 — 미리 채워 비켜 간다.
        b.js("document.querySelector('#who').value = '두번누르기시험';")
        b.js(ERRHOOK)
        b.js(FETCHHOOK)

        FIVE = ["#btn-ok", "#btn-ai", "#btn-save", "#btn-flag", "#btn-exc"]

        # ── ① 수정본 저장을 잇달아 두 번 ─────────────────────────────────
        reset_posts(b, 1500)
        b.js("const e=document.querySelector('#btn-save'); e.click(); e.click(); e.click();")
        time.sleep(0.3)
        n1 = posts(b, "/api/save")
        L.chk("① 세 번 눌러도 /api/save 는 한 번만 갔다", len(n1) == 1, n1)

        # ── ② 그동안 딱지가 붙고, 마우스로는 안 닿는다 ────────────────────
        marks = dict(b.js(SAVING, FIVE))
        L.chk("② 저장 중에는 «.saving» 딱지가 붙는다", marks.get("btn-save") is True, marks)
        L.chk("② 같은 길을 쓰는 판정 다섯 단추가 함께 잠긴다",
              all(marks.get(s.lstrip("#")) is True for s in FIVE), marks)
        hit = b.js("const x=document.querySelector('#btn-save'); const r=x.getBoundingClientRect();"
                   "const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);"
                   "return { self: e===x, got: e ? (e.id || e.className || e.tagName) : null };")
        L.chk("② 마우스가 그 단추에 아예 안 닿는다(pointer-events:none)",
              hit.get("self") is False, hit)
        os.makedirs(os.path.join(L.SHOTS, "double"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "double", "saving_locked.png"))

        # ── ③ 끝나면 풀리고 다시 눌린다 ──────────────────────────────────
        took = wait_unlocked(b, "#btn-save")
        said = b.js("return document.querySelector('#saveflash').textContent")
        L.chk("③ 저장이 끝나면 딱지가 떨어진다", took is not None, took)
        L.chk("③ 한 번 간 그 요청은 제대로 저장됐다(막기만 한 것이 아니다)",
              "수정본 저장 완료" in (said or ""), said)
        L.chk("③ 그 시각이 늦춘 1.5초와 맞는다(0.8~6초)",
              took is not None and 0.8 <= took <= 6.0, took)
        marks = dict(b.js(SAVING, FIVE))
        L.chk("③ 다섯 단추가 다 풀렸다", not any(marks.values()), marks)
        L.chk("③ `disabled` 는 안 건드렸다 — «AI로 교체» 는 이 사진의 AI 제안 유무 그대로",
              L.ev(b, 'document.querySelector("#btn-ai").disabled')
              == (not L.ev(b, "!!(S.item && S.item.has_proposal)")),
              [L.ev(b, 'document.querySelector("#btn-ai").disabled'),
               L.ev(b, "!!(S.item && S.item.has_proposal)")])
        b.js("document.querySelector('#btn-save').click();")
        time.sleep(0.4)
        L.chk("③ 다시 누르면 또 간다(영영 잠기지 않는다)", len(posts(b, "/api/save")) == 2,
              posts(b, "/api/save"))
        wait_unlocked(b, "#btn-save")

        # ── ④ Ctrl+S 다섯 번 연타(키를 누른 채 있는 흉내) ─────────────────
        reset_posts(b, 1500)
        b.js("for (let i=0;i<5;i++) window.dispatchEvent("
             "new KeyboardEvent('keydown',{key:'s',ctrlKey:true,bubbles:true}));")
        time.sleep(0.3)
        n2 = posts(b, "/api/save")
        L.chk("④ Ctrl+S 를 다섯 번 연타해도 한 번만 갔다", len(n2) == 1, n2)
        wait_unlocked(b, "#btn-save")

        # ── ⑤ 상자 저장 ────────────────────────────────────────────────
        b.key("x")                                   # 상자 모드
        time.sleep(0.6)
        L.chk("⑤ 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        L.run(b, "S.boxes=[{cls:'fruit',src:'human',xyxy:[20,20,140,140]}]; S.bsel=-1; S.bDirty=true;")
        reset_posts(b, 1500)
        b.js("const e=document.querySelector('#boxsave'); e.click(); e.click();")
        time.sleep(0.3)
        n3 = posts(b, "/api/boxes")
        L.chk("⑤ 상자 저장을 두 번 눌러도 /api/boxes 는 한 번만 갔다", len(n3) == 1, n3)
        L.chk("⑤ 그동안 상자 저장 단추에 딱지가 붙어 있다",
              b.js("return document.querySelector('#boxsave').classList.contains('saving')"))
        took3 = wait_unlocked(b, "#boxsave")
        L.chk("⑤ 끝나면 풀린다", took3 is not None, took3)
        say = b.js("return [document.querySelector('#saveflash').textContent,"
                   "        document.querySelector('#boxinfo').textContent];")
        L.chk("⑤ 상자는 제대로 저장됐다(한 번 간 그 요청으로)",
              L.ev(b, "S.bDirty") is False and L.ev(b, "S.boxes.length") == 1,
              [L.ev(b, "S.bDirty"), L.ev(b, "S.boxes.length"), say])
        b.key("x")
        time.sleep(0.5)

        # ── ⑥ 번호 저장 — 그 사진에 번호가 있을 때만 ──────────────────────
        if L.ev(b, "!!S.inst"):
            L.run(b, "UI.setNumMode(true, true)")
            time.sleep(0.5)
            reset_posts(b, 1500)
            b.js("const e=document.querySelector('#numsave'); e.click(); e.click();")
            time.sleep(0.3)
            n4 = posts(b, "/api/save_instances")
            L.chk("⑥ 번호 저장을 두 번 눌러도 /api/save_instances 는 한 번만 갔다", len(n4) == 1, n4)
            wait_unlocked(b, "#numsave")
            L.run(b, "UI.setNumMode(false, true)")
            time.sleep(0.4)
        else:
            L.warn("⑥ 번호 저장", "이 사진(%s)에는 열매 번호가 없어 건너뜀 — 시뮬 locksim 이 대신 잰다" % STEM)

        # ── ⑦ 콘솔이 깨끗하고 화면이 안 멈췄다 ───────────────────────────
        reset_posts(b, 0)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑦ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.chk("⑦ 보던 사진이 그대로다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        b.key("x")
        time.sleep(0.6)
        L.chk("⑦ 화면이 안 멈췄다(X 로 상자 모드가 켜진다)", L.ev(b, "!!S.boxMode") is True)
        b.key("x")
        time.sleep(0.3)
        b.shot(os.path.join(L.SHOTS, "double", "after_all.png"))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b9_double_save")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
