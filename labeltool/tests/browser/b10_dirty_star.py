# -*- coding: utf-8 -*-
"""b10 — **저장 안 한 작업이 눈에 보이는가** (편의 U1).
작성: 2026-09-21

왜
  지금까지 «저장 안 됨» 이 적히는 자리는 도구 상자의 접힌 «작업 정보» 칸뿐이었고(상자·번호),
  칠한 영역에는 그 표시조차 없었다. 사람은 캔버스를 보고 있으므로 셋 다 눈에 안 들어온다.
  → 메모장·포토샵처럼 파일 이름 옆에 «*» 를 세우고, 그 작업의 «저장» 단추를 노랗게 두른다.

  `tests/sim/dirtysim.js` 가 깃발 여덟 조합을 전수로 재고, 이 시험은 **진짜 파이어폭스에서
  정말 보이는가** 를 잰다 — 붓질·상자 그리기를 실제로 해서 «*» 가 뜨는지, 저장하면 사라지는지,
  그 «*» 가 상단 바 안에서 **가려지지 않고** 실제로 그려지는지(화소 자리로 실측).

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 막 열었을 때는 «*» 요소가 아예 없다(깨끗할 때 화면에 한 칸도 안 는다)
    ② 붓질하면 «*» 가 뜨고 «저장» 에 노란 테두리가 그려진다(실측 · 0.2초 안)
    ③ 그 «*» 가 파일 이름 바로 옆에 있고, 무엇에도 안 가려진다
    ④ Ctrl+S 로 저장하면 둘 다 사라진다
    ⑤ 상자를 그리면 «상자 저장» 쪽에만 뜨고, 저장하면 사라진다
    ⑥ 번호도 같다(그 사진에 번호가 있을 때만)
    ⑦ 다른 사진으로 넘어가면 «*» 가 남지 않는다 · 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b9 와 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_star")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# «*» 가 지금 **화면에 그려져 있나** — 있음/없음이 아니라 실제 자리와 색으로 본다.
STAR = """
const e = document.querySelector('#dirtystar');
if (!e) return null;
const r = e.getBoundingClientRect();
const cs = getComputedStyle(e);
return { on: e.classList.contains('on'), disp: cs.display, color: cs.color,
         x: Math.round(r.left), y: Math.round(r.top),
         w: Math.round(r.width), h: Math.round(r.height), title: e.title };
"""

RING = """
const e = document.querySelector(arguments[0]);
if (!e) return null;
return { unsaved: e.classList.contains('unsaved'), shadow: getComputedStyle(e).boxShadow };
"""


def star(b):
    return b.js(STAR)


def ring(b, sel):
    return b.js(RING, sel)


def wait_star(b, want, secs=4.0):
    """«*» 가 want(True/False) 가 될 때까지 기다린다 — 걸린 초를 돌려준다(안 되면 None)."""
    t0 = time.time()
    while time.time() - t0 < secs:
        s = star(b)
        now = bool(s and s.get("on"))
        if now == want:
            return round(time.time() - t0, 2)
        time.sleep(0.05)
    return None


def wait_clean(b, flag, secs=20):
    """저장이 끝나 그 깃발이 내려갈 때까지."""
    t0 = time.time()
    while time.time() - t0 < secs:
        if L.ev(b, "!!S.%s" % flag) is False:
            return round(time.time() - t0, 1)
        time.sleep(0.2)
    return None


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5561)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "star")
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        # 첫 저장 때 한 번 묻는 «내 이름» 겹창은 이 시험이 보는 것이 아니다 — 미리 채워 비켜 간다
        b.js("document.querySelector('#who').value = '별표시험';")
        os.makedirs(shots, exist_ok=True)

        # ── ① 깨끗할 때 ─────────────────────────────────────────────────
        time.sleep(0.6)                                  # 0.2초 시계가 몇 번 돌 시간
        L.chk("① 저장할 것이 없으면 «*» 요소가 아예 없다", star(b) is None, star(b))
        r0 = ring(b, "#btn-save")
        L.chk("① «저장» 단추에도 테두리가 없다", r0 and r0.get("unsaved") is False, r0)

        # ── ② 붓질 → «*» ────────────────────────────────────────────────
        L.run(b, "UI.setTool('brush')")                  # AI 제안이 있으면 기본이 «자동채움» 이다
        b.drag("#cv", 700, 380, 760, 420)
        took = wait_star(b, True)
        L.chk("② 붓질로 «저장 안 됨» 깃발이 올라갔다", L.ev(b, "!!S.edDirty") is True)
        L.chk("② «*» 가 떴다(0.2초 시계 안)", took is not None and took <= 1.0, took)
        s = star(b)
        L.chk("② 진짜로 그려져 있다(넓이·높이가 0 이 아니다)",
              s and s.get("w", 0) > 0 and s.get("h", 0) > 0 and s.get("disp") != "none", s)
        L.chk("② 노란색이다(«저장» 테두리와 같은 색)", s and s.get("color") == "rgb(255, 212, 0)", s)
        L.chk("② 풍선말에 무엇이 저장 안 됐는지 적혀 있다",
              "칠한 영역" in (s.get("title") or ""), s.get("title"))
        r1 = ring(b, "#btn-save")
        L.chk("② «저장» 단추에 노란 테두리가 그려졌다",
              r1 and r1.get("unsaved") is True and "255, 212, 0" in (r1.get("shadow") or ""), r1)
        L.chk("② 상자·번호 저장 단추는 그대로다(그 일은 안 건드렸다)",
              (ring(b, "#boxsave") or {}).get("unsaved") is False
              and (ring(b, "#numsave") or {}).get("unsaved") is False,
              [ring(b, "#boxsave"), ring(b, "#numsave")])
        b.shot(os.path.join(shots, "star_on.png"))

        # ── ③ 자리 — 파일 이름 바로 옆 · 안 가려짐 ────────────────────────
        pos = b.js("""
          const nm = document.querySelector('#stemname').getBoundingClientRect();
          const st = document.querySelector('#dirtystar').getBoundingClientRect();
          const tb = document.querySelector('#topbar').getBoundingClientRect();
          const hit = document.elementFromPoint(st.left + st.width / 2, st.top + st.height / 2);
          return { gap: Math.round(st.left - nm.right), inbar: st.top >= tb.top && st.bottom <= tb.bottom,
                   hit: hit ? (hit.id || hit.className || hit.tagName) : null };
        """)
        L.chk("③ 파일 이름 바로 오른쪽이다(20px 안)",
              0 <= pos.get("gap", 999) <= 20, pos)
        L.chk("③ 상단 바 안에 들어 있다(잘려 나가지 않았다)", pos.get("inbar") is True, pos)
        L.chk("③ 무엇에도 안 가려진다", pos.get("hit") == "dirtystar", pos)

        # ── ④ 저장하면 사라진다 ──────────────────────────────────────────
        b.js("window.dispatchEvent(new KeyboardEvent('keydown',{key:'s',ctrlKey:true,bubbles:true}));")
        L.chk("④ 저장이 끝났다", wait_clean(b, "edDirty") is not None,
              b.js("return document.querySelector('#saveflash').textContent"))
        gone = wait_star(b, False)
        L.chk("④ «*» 가 사라졌다", gone is not None, gone)
        r2 = ring(b, "#btn-save")
        L.chk("④ «저장» 단추 테두리도 없어졌다",
              r2 and r2.get("unsaved") is False and "255, 212, 0" not in (r2.get("shadow") or ""), r2)
        b.shot(os.path.join(shots, "star_off.png"))

        # ── ⑤ 상자 ──────────────────────────────────────────────────────
        b.key("x")
        time.sleep(0.6)
        L.chk("⑤ 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        b.drag("#cv", 520, 300, 640, 420)                 # 진짜로 네모 하나를 그린다
        time.sleep(0.4)
        L.chk("⑤ 상자가 하나 그려졌다", L.ev(b, "S.boxes.length") >= 1, L.ev(b, "S.boxes.length"))
        L.chk("⑤ 상자 쪽 «*» 가 떴다", wait_star(b, True) is not None, star(b))
        L.chk("⑤ 풍선말이 «상자» 라고 말한다", "상자" in ((star(b) or {}).get("title") or ""),
              (star(b) or {}).get("title"))
        L.chk("⑤ «상자 저장» 단추에만 테두리가 붙었다",
              (ring(b, "#boxsave") or {}).get("unsaved") is True
              and (ring(b, "#btn-save") or {}).get("unsaved") is False,
              [ring(b, "#boxsave"), ring(b, "#btn-save")])
        b.js("document.querySelector('#boxsave').click();")
        L.chk("⑤ 상자 저장이 끝났다", wait_clean(b, "bDirty") is not None,
              b.js("return document.querySelector('#saveflash').textContent"))
        L.chk("⑤ 저장하면 «*» 가 사라진다", wait_star(b, False) is not None, star(b))
        L.chk("⑤ 상자 저장 단추 테두리도 없어졌다",
              (ring(b, "#boxsave") or {}).get("unsaved") is False, ring(b, "#boxsave"))
        b.key("x")
        time.sleep(0.5)

        # ── ⑥ 번호 — 그 사진에 번호가 있을 때만 ───────────────────────────
        if L.ev(b, "!!S.inst"):
            L.run(b, "UI.setNumMode(true, true)")
            time.sleep(0.5)
            # 번호 한 알을 진짜로 고치는 길은 «고른 뒤 D» 라 좌표에 기댄다 — 여기서 보는 것은
            # «깃발이 올라가면 표시가 따라오는가» 이므로 깃발만 올린다(무엇이 깃발을 올리는지는
            # instances.js 의 일이고 sim/dirtysim.js 가 여덟 조합을 따로 잰다).
            L.run(b, "S.numDirty = true")
            L.chk("⑥ 번호 쪽 «*» 가 떴다", wait_star(b, True) is not None, star(b))
            L.chk("⑥ 풍선말이 «번호» 라고 말한다", "번호" in ((star(b) or {}).get("title") or ""),
                  (star(b) or {}).get("title"))
            L.chk("⑥ «번호 저장» 단추에만 테두리가 붙었다",
                  (ring(b, "#numsave") or {}).get("unsaved") is True
                  and (ring(b, "#btn-save") or {}).get("unsaved") is False,
                  [ring(b, "#numsave"), ring(b, "#btn-save")])
            b.js("document.querySelector('#numsave').click();")
            L.chk("⑥ 번호 저장이 끝났다", wait_clean(b, "numDirty") is not None,
                  b.js("return document.querySelector('#saveflash').textContent"))
            L.chk("⑥ 저장하면 «*» 가 사라진다", wait_star(b, False) is not None, star(b))
            L.run(b, "UI.setNumMode(false, true)")
            time.sleep(0.4)
        else:
            L.warn("⑥ 번호", "이 사진(%s)에는 열매 번호가 없어 건너뜀 — 시뮬 dirtysim 이 대신 잰다" % STEM)

        # ── ⑦ 다음 사진 · 콘솔 ───────────────────────────────────────────
        L.run(b, "UI.setTool('brush')")
        b.drag("#cv", 700, 380, 720, 400)
        L.chk("⑦ 다시 칠하면 «*» 가 또 뜬다", wait_star(b, True) is not None, star(b))
        L.run(b, "S.edDirty = false")                     # 다음 사진으로 넘어갈 때 겹창을 안 띄우려고
        # `.`(다음 사진) 을 쓸 수 없다 — open_photo 가 이름으로 걸러 목록에 이 한 장뿐이라
        #   «이 쪽의 마지막 사진입니다» 로 끝난다(2026-09-21 실측). 걸러 놓은 것을 지우고
        #   **다른 이름의 카드**를 직접 누른다.
        b.js("document.querySelector('#topbar .tab[data-view=\"list\"]').click();")
        b.js("const q=document.querySelector('#f-q');q.value='';"
             "q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))")
        b.wait_js("return [...document.querySelectorAll('#grid .card')]"
                  ".some(c=>c.querySelector('.cap').firstChild.textContent.trim()!==arguments[0])",
                  STEM, timeout=60)
        b.js("const c=[...document.querySelectorAll('#grid .card')]"
             ".find(c=>c.querySelector('.cap').firstChild.textContent.trim()!==arguments[0]); c.click();", STEM)
        time.sleep(2.0)
        L.chk("⑦ 다른 사진으로 넘어갔다", L.ev(b, "S.stem") != STEM, L.ev(b, "S.stem"))
        L.chk("⑦ 깨끗한 새 사진에는 «*» 가 안 남아 있다", wait_star(b, False) is not None, star(b))
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑦ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        b.shot(os.path.join(shots, "after_all.png"))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b10_dirty_star")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
