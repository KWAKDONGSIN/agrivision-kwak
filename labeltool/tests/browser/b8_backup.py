# -*- coding: utf-8 -*-
"""b8 — **브라우저가 죽어도 저장 전 작업이 살아 있는가** (편의·안정성 S5).
작성: 2026-09-21

왜
  S4 의 «창 닫기 경고» 는 *사람이 닫을 때* 만 뜬다. 배터리가 나가거나 파이어폭스가 탭을 떨어뜨리면
  저장 전 붓질이 아무 흔적 없이 사라진다(서버는 저장 전 상태를 모른다). → 1분마다 브라우저에
  한 벌 적어 두고, 같은 사진을 다시 열면 «되돌릴까요» 를 묻는다.

  `tests/sim/backupsim.js` 가 백업 코드 자체(접기·자리 없음·거절)를 전수로 재고, 이 시험은
  **진짜 파이어폭스에서 정말 되돌아오는가** 를 잰다 — 붓질 → 백업 → 새로 읽어들이기(=죽은 흉내)
  → 사진 다시 열기 → 겹창 → 칠한 것이 그대로 돌아오는지.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다). 저장 단추는
  누르지 않는다 — 되돌리기까지만 보고, 화면에만 남긴다.
    ⓪ 아무것도 안 했으면 백업을 적지 않는다
    ① 붓질하면 적는다(어느 과일·어느 사진·어떤 크기인지 함께)
    ② 새로 읽어들인 뒤 같은 사진을 열면 겹창이 뜨고, «확인» 이면 칠한 것이 **한 화소까지** 돌아온다
    ③ 되돌린 것은 «저장 안 됨» 이고, «되돌리기»(Ctrl+Z) 로 서버 값으로 되돌아간다
    ④ «취소» 면 서버 값을 그대로 쓰고, 백업을 지워 **다시 묻지 않는다**
    ⑤ 끝까지 콘솔 오류 0

  ⚠ 겹창이 떠 있는 동안에는 `b.js()` 를 부르지 않는다 — geckodriver 는 기본값이 «몰래 닫고
    알려 주기» 라서, 그 사이 스크립트를 보내면 우리가 시험하려는 겹창을 자기가 닫아 버린다.
    그래서 카드를 직접 누르고 `alert_text()` 만으로 기다린다(open_photo 를 안 쓴다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_backup")
FRUIT = "peach"
STEM = "210629-t1-01"
KEY = "backup_260921"

HOOK = ("window.__errs = window.__errs || [];"
        "if (!window.__hooked) { window.__hooked = 1;"
        " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
        " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
        "return window.__errs.length;")

PICK = ("const c=[...document.querySelectorAll('#grid .card')]"
        ".find(c=>c.querySelector('.cap').firstChild.textContent.trim()===arguments[0]);")


def painted(b):
    """칠한 화소 수 — «한 화소까지 같은가» 를 이 숫자 하나로 본다."""
    return L.ev(b, "S.ed ? S.ed.reduce((a, v) => a + v, 0) : -1")


def to_list(b):
    """목록 화면으로 가서 그 사진 카드가 뜰 때까지 기다린다(누르지는 않는다)."""
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
         "s.dispatchEvent(new Event('change'))", FRUIT)
    b.js("const q=document.querySelector('#f-q');q.value=arguments[0];"
         "q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))", STEM)
    b.wait_js(PICK + "return !!c", STEM, timeout=60)


def click_card(b):
    b.js(PICK + "c.click()", STEM)


def wait_alert(b, secs):
    """겹창이 뜰 때까지 기다린다 — 글자를 돌려준다(안 뜨면 None)."""
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            return b.alert_text()
        except Exception:
            time.sleep(0.4)
    return None


def reload_as_crash(b):
    """«브라우저가 죽었다» 흉내 — 깃발을 내리고 새로 읽어들인다.
       (깃발을 내리는 것은 S4 의 창 닫기 경고를 피하기 위한 것이다. 화면 상태는 어차피 다 사라지고,
        서버에는 저장하지 않았으므로 정말 죽은 것과 같은 자리에서 다시 시작한다.)"""
    L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false")
    b.go("/")
    b.wait("return !!document.querySelector('#fruit option')", 60)
    L.close_tour(b)
    b.js(HOOK)


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5561)
    p = L.start(port=port, sb=SB)
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(HOOK)
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        srv = painted(b)
        L.chk("서버에서 읽은 칠한 영역이 있다", srv > 0, "%d화소" % srv)

        # ── ⓪ 아무것도 안 했으면 적지 않는다
        L.chk("⓪ 저장 안 한 것이 없으면 백업을 적지 않는다", L.ev(b, "UI.backupNow()") == 0)
        L.chk("⓪ 그러면 localStorage 에 아무것도 없다",
              L.ev(b, "localStorage.getItem('%s')" % KEY) is None)

        # ── ① 붓질 → 백업
        L.run(b, "UI.setTool('brush')")           # 사진에 AI 제안이 있으면 기본이 «자동채움» 이다
        b.drag("#cv", 700, 380, 760, 420)
        time.sleep(0.6)
        mine = painted(b)
        L.chk("① 붓질로 칠한 영역이 바뀌었다", mine != srv and mine > 0, "%d → %d화소" % (srv, mine))
        L.chk("① «저장 안 됨» 딱지가 올라갔다", L.ev(b, "!!S.edDirty") is True)
        n1 = L.ev(b, "UI.backupNow()")
        L.chk("① 백업을 적었다", n1 > 0, "%s글자" % n1)
        info = L.ev(b, "(function(){const o=JSON.parse(localStorage.getItem('%s'));"
                       "return {fruit:o.fruit, stem:o.stem, W:o.W, H:o.H,"
                       " keys:Object.keys(o).join(','), edlen:(o.ed||'').length};})()" % KEY)
        L.chk("① 어느 과일·어느 사진·어떤 크기인지 함께 적었다",
              info.get("fruit") == FRUIT and info.get("stem") == STEM
              and info.get("W") == L.ev(b, "S.W") and info.get("H") == L.ev(b, "S.H"), info)
        L.chk("① 저장 안 한 것(칠한 영역)만 적었다",
              "ed" in info.get("keys", "") and "inst" not in info.get("keys", "")
              and "boxes" not in info.get("keys", ""), info.get("keys"))

        # ── ② 죽은 흉내 → 같은 사진을 다시 연다
        reload_as_crash(b)
        L.chk("② 새로 읽어들인 뒤에도 백업은 남아 있다",
              L.ev(b, "!!localStorage.getItem('%s')" % KEY) is True)
        to_list(b)
        click_card(b)
        txt = wait_alert(b, 40)
        L.chk("② 같은 사진을 열면 «되돌릴까요» 를 묻는다", txt is not None,
              (txt or "").replace("\n", " / ")[:80])
        L.chk("② 무엇이 남아 있는지 말한다",
              txt is not None and "저장하지 않은 작업" in txt and "칠한 영역" in txt,
              (txt or "").split("\n")[0])
        b.alert_ok()
        time.sleep(1.5)
        back = painted(b)
        L.chk("② «확인» 을 누르면 칠한 것이 **한 화소까지** 돌아온다", back == mine,
              "되돌린 %d화소 / 칠했던 %d화소 / 서버 %d화소" % (back, mine, srv))
        L.chk("② 사진은 그 사진이 맞다", L.ev(b, "S.stem") == STEM)

        # ── ③ 되돌린 것은 «저장 안 됨» 이고, 되돌리기로 서버 값으로 간다
        L.chk("③ 되돌린 것은 «저장 안 됨» 이다(사람이 Ctrl+S 를 눌러야 한다)",
              L.ev(b, "!!S.edDirty") is True)
        L.chk("③ 되돌리기 단계가 하나 쌓였다", L.ev(b, "S.undo.length") == 1,
              L.ev(b, "S.undo.length"))
        os.makedirs(os.path.join(L.SHOTS, "backup"), exist_ok=True)
        b.shot(os.path.join(L.SHOTS, "backup", "restored.png"))
        b.click("#undo")
        time.sleep(0.8)
        L.chk("③ «되돌리기» 를 누르면 서버 값으로 되돌아간다", painted(b) == srv,
              "%d화소" % painted(b))

        # ── ④ 거절하면 지운다
        L.run(b, "UI.setTool('brush')")
        b.drag("#cv", 620, 300, 690, 350)
        time.sleep(0.6)
        mine2 = painted(b)
        L.chk("④ 다시 칠했다", mine2 != srv, "%d화소" % mine2)
        L.chk("④ 백업을 다시 적었다", L.ev(b, "UI.backupNow()") > 0)
        reload_as_crash(b)
        to_list(b)
        click_card(b)
        txt2 = wait_alert(b, 40)
        L.chk("④ 또 묻는다", txt2 is not None, (txt2 or "").split("\n")[0])
        b.alert_cancel()
        time.sleep(1.5)
        L.chk("④ «취소» 면 서버 값을 그대로 쓴다", painted(b) == srv,
              "%d화소 (서버 %d · 백업 %d)" % (painted(b), srv, mine2))
        L.chk("④ «저장 안 됨» 딱지도 안 올라간다", L.ev(b, "!!S.edDirty") is False)
        L.chk("④ 백업을 지웠다", L.ev(b, "localStorage.getItem('%s')" % KEY) is None)
        to_list(b)
        click_card(b)
        L.chk("④ 같은 사진을 또 열어도 **다시 묻지 않는다**", wait_alert(b, 12) is None)
        time.sleep(1.0)
        L.chk("④ 그 사진이 정상으로 열린다",
              L.ev(b, "S.stem") == STEM and painted(b) == srv, L.ev(b, "S.stem"))

        # ── ⑤ 콘솔
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑤ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b8_backup")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
