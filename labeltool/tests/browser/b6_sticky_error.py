# -*- coding: utf-8 -*-
"""b6 — **실패 알림이 저절로 사라지지 않는가** (편의·안정성 S2).
작성: 2026-09-21

왜
  전에는 성공이든 실패든 알림이 3초 뒤에 지워졌다. 저장이 실패하는 순간 사람은 보통 캔버스를
  보고 있어서, 상단 바 구석에 3초 떴다 사라지는 붉은 글씨를 **놓친다.** 그러고는 저장된 줄 알고
  다음 장으로 넘어간다 — S1 이 «조용히 씹히는» 것을 막았어도, 말해 준 것을 못 보면 결과가 같다.

어떻게
  모래상자 서버를 띄워 사진 한 장을 연 뒤 **내가 띄운 그 서버만** 끄고(남의 것은 건드리지 않는다)
  저장을 눌러 **진짜 실패**를 만든다. 그 다음
    ① 4초(옛 3초보다 길게) 뒤에도 실패 알림이 그대로 있는가
    ② «확인» 단추가 붙었고, 상단 바에 **잘리지 않아** 실제로 눌리는가
    ③ 누르면 알림과 붉은 띠가 함께 사라지는가
    ④ **성공** 알림은 전처럼 3초 뒤 저절로 사라지는가(잘 되는 일까지 손으로 지우게 하지 않는다)
    ⑤ 1초짜리 안내(`flashBrief` — «사진 밖입니다» 자리)는 전처럼 스스로 사라지고
       «확인» 단추가 붙지 않는가
  를 잰다. 서버를 끄는 시험이라 `run_all.sh --browser` 묶음과 따로 돌려도 된다(b5 와 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_sticky")
FRUIT = "peach"
STEM = "210629-t1-01"
HOOK = ("window.__errs = window.__errs || [];"
        "if (!window.__hooked) { window.__hooked = 1;"
        " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
        " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
        "return window.__errs.length;")

# 알림 칸의 지금 상태를 한 번에 읽는다 — 글자 · 붉은 띠 여부 · «확인» 단추 여부
STATE = ("const e = document.querySelector('#saveflash');"
         "if (!e) return null;"
         "const b = e.querySelector('.flashok');"
         "return { text: e.textContent, bad: e.classList.contains('flashbad'),"
         "         ok: !!b, color: getComputedStyle(e).color };")


def state(b):
    return b.js(STATE)


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5541)
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

        # ① 진짜 실패를 만든다 — «저장» 을 누른다
        b.click("#btn-save")
        time.sleep(1.5)
        dlg = L.eat_alert(b)                     # 첫 저장 때 한 번 묻는 «내 이름» 겹창(기존 장치)
        print("  (겹창) %r" % (dlg,), flush=True)
        st = None
        for _ in range(60):
            st = state(b)
            if st and st["text"] and "저장 중" not in st["text"]:
                break
            time.sleep(0.5)
        L.chk("① 저장 실패 알림이 떴다", bool(st and st["text"]) and "저장 중" not in (st or {}).get("text", ""),
              st and st.get("text"))
        first = (st or {}).get("text", "")

        # ① 4초를 기다린다 — 옛 규칙(3초)이라면 여기서 사라져 있다
        time.sleep(4.0)
        st = state(b)
        L.chk("① 4초 뒤에도 실패 알림이 그대로 남아 있다(3초에 안 사라진다)",
              st and st["text"].startswith(first[:12]) and bool(st["text"]), st and st.get("text"))
        L.chk("① 실패 알림이 붉은색이다", "255, 179, 179" in (st or {}).get("color", ""), st and st.get("color"))
        L.chk("② 붉은 띠(.flashbad)가 붙었다", bool(st and st["bad"]), st)
        L.chk("② «확인» 단추가 붙었다", bool(st and st["ok"]), st)

        # ② 그 단추가 화면에서 **정말로** 눌리는 자리에 있다 — 상단 바(overflow:hidden)에 안 잘렸나
        top = b.js("const x=document.querySelector('#saveflash .flashok');"
                   "if(!x) return null; const r=x.getBoundingClientRect();"
                   "if(r.width<=0||r.height<=0) return {why:'크기 0', r:[r.x,r.y,r.width,r.height]};"
                   "const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);"
                   "return { hit: e===x, cls: e? e.className : null,"
                   "         r: [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height)] };")
        L.chk("② 그 자리를 찍으면 «확인» 단추가 잡힌다(가려지거나 잘리지 않았다)",
              bool(top and top.get("hit")), top)
        os.makedirs(os.path.join(L.SHOTS, "sticky"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "sticky", "error_stays_until_ok.png"))

        # ③ 눌러서 지운다
        b.click("#saveflash .flashok")
        time.sleep(0.5)
        st = state(b)
        L.chk("③ «확인» 을 누르면 알림이 지워진다", st and st["text"] == "", st)
        L.chk("③ 붉은 띠도 «확인» 단추도 함께 사라진다",
              st and not st["bad"] and not st["ok"], st)

        # ④ 성공 알림은 전처럼 3초 뒤 스스로 사라진다
        L.run(b, "UI.flash('저장했습니다')")
        time.sleep(1.0)
        st = state(b)
        L.chk("④ 성공 알림은 떠 있고 «확인» 단추가 안 붙는다",
              st and st["text"] == "저장했습니다" and not st["ok"] and not st["bad"], st)
        time.sleep(3.0)
        st = state(b)
        L.chk("④ 성공 알림은 3초쯤 뒤 저절로 사라진다", st and st["text"] == "", st)

        # ⑤ 1초짜리 안내(flashBrief)는 전처럼 스스로 사라진다 — «사진 밖입니다» 가 쓰는 길
        L.run(b, "UI.flashBrief('사진 밖입니다 — 격자 무늬 밖으로는 칠할 수 없습니다', true)")
        time.sleep(0.3)
        st = state(b)
        L.chk("⑤ 1초 안내는 붉은 글씨로 뜨되 띠도 «확인» 단추도 없다",
              st and "사진 밖" in st["text"] and not st["bad"] and not st["ok"]
              and "255, 179, 179" in st["color"], st)
        time.sleep(1.4)
        st = state(b)
        L.chk("⑤ 1초 안내는 저절로 사라진다", st and st["text"] == "", st)

        # 화면이 안 멈췄는지 · 콘솔이 깨끗한지
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.chk("보던 사진이 그대로다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b6_sticky_error")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
