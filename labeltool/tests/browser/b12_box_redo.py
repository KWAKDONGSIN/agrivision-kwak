# -*- coding: utf-8 -*-
"""b12 — **상자 다시하기(Ctrl+Y)가 진짜 브라우저에서 되는가** (편의 U3).
작성: 2026-09-21

왜
  되돌리기(Ctrl+Z)는 칠한 영역·상자·번호 셋 다 있는데 **다시하기(Ctrl+Y)만 상자에 없었다**
  (`keys.js` 가 «상자에는 다시 실행이 없습니다» 라고 거절했다). 한 번 더 누른 사람은 방금 친
  네모를 손으로 다시 칠 수밖에 없었다 — 그림판·포토샵·워드 어디에도 없는 일이다.

  `tests/sim/boxsim.js` 5절이 함수 단위로 19가지를 전수로 보지만, 시뮬은 «키가 정말 그 함수로
  가는가» 를 모른다. 여기서는 **진짜 파이어폭스에서 진짜 Ctrl 을 눌러** 잰다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 상자 모드에서 마우스로 **정말** 네모를 그린다
    ② Ctrl+Z 로 사라지고 ③ Ctrl+Y 로 «좌표 글자까지» 그대로 돌아온다
    ④ 세 개를 그려 세 번 되돌리고 세 번 다시 실행해도 한 칸씩 정확히 오간다
    ⑤ 다시할 것이 없으면 안내만 뜨고 상자를 건드리지 않는다
    ⑥ 되돌린 뒤 새로 그리면 옛 갈래가 되살아나지 않는다
    ⑦ 상자 모드에서 Ctrl+Y 가 «칠한 영역» 다시하기(#redo)를 누르지 않는다(사이클3 수정 회귀)
    ⑧ 상자 모드를 끄면 Ctrl+Y 는 예전대로 #redo 로 간다(회귀)
    ⑨ 단축키 표가 «상자» 를 포함하도록 바뀌었다 · 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b11 과 같다).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_boxredo")
FRUIT = "peach"
STEM = "210629-t1-01"

CTRL = ""                                          # WebDriver 가 정한 Ctrl 키 코드

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# «칠한 영역» 다시하기 단추가 눌린 횟수 — 상자 모드에서 0 이어야 한다(사이클3 수정)
REDOHOOK = ("window.__redoClicks = 0;"
            "const r = document.querySelector('#redo');"
            "if (!window.__redohooked) { window.__redohooked = 1;"
            " r.addEventListener('click', function () { window.__redoClicks++; }); }"
            "return window.__redoClicks;")


def chord(b, k):
    """진짜 Ctrl+<키>. ff.py 의 key() 는 키 하나만 보내므로 여기서 조합을 만든다
       (ff.py 는 다른 시험도 같이 쓰는 공용 파일이라 건드리지 않는다)."""
    b._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb", "actions": [
        {"type": "keyDown", "value": CTRL},
        {"type": "keyDown", "value": k},
        {"type": "keyUp", "value": k},
        {"type": "keyUp", "value": CTRL}]}]})
    time.sleep(0.12)


def boxes(b):
    """지금 화면이 들고 있는 상자를 «글자 그대로» — 개수가 아니라 좌표까지 견준다."""
    return json.loads(L.ev(b, "JSON.stringify(S.boxes.map(function(x){return x.xyxy.join(',');}))"))


def flashtext(b):
    return b.js("const e = document.querySelector('#saveflash');"
                "return e ? { text: e.textContent, bad: e.classList.contains('flashbad') } : null")


def clear_flash(b):
    """S2 의 «실패 알림은 사라지지 않는다» 때문에 안내를 눌러 치워야 다음 항목이 깨끗하다."""
    b.js("const k = document.querySelector('#saveflash .flashok'); if (k) k.click();")
    time.sleep(0.1)


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5581)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "boxredo")
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(ERRHOOK)
        os.makedirs(shots, exist_ok=True)

        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        L.close_tour(b)
        b.open_photo(FRUIT, STEM)
        L.chk("① 사진이 열렸다", L.ev(b, "S.stem") == STEM, L.ev(b, "S.stem"))
        time.sleep(1.2)                                   # loadBoxes()·초벌까지 가라앉기를 기다린다
        b.js(REDOHOOK)

        # ── ① 상자 모드 + 진짜 드래그 ─────────────────────────────────────
        b.key("x")
        time.sleep(0.3)
        L.chk("① 상자 모드가 켜졌다", L.ev(b, "!!S.boxMode") is True)
        L.chk("① 그리기 도구다", L.ev(b, "S.btool") == "draw", L.ev(b, "S.btool"))
        base = boxes(b)
        L.chk("① 다시하기 칸이 처음엔 비어 있다", L.ev(b, "S.bredo.length") == 0,
              L.ev(b, "S.bredo.length"))

        b.drag("#cv", 520, 300, 640, 420)                 # 마우스로 정말 네모를 친다
        time.sleep(0.3)
        one = boxes(b)
        L.chk("① 네모가 하나 늘었다(%d → %d)" % (len(base), len(one)),
              len(one) == len(base) + 1, one[-1:] if one else None)
        made = one[-1]
        L.chk("① 그린 순간에는 다시할 것이 없다", L.ev(b, "S.bredo.length") == 0)
        b.shot(os.path.join(shots, "1_drawn.png"))

        # ── ② Ctrl+Z ────────────────────────────────────────────────────
        chord(b, "z")
        back = boxes(b)
        L.chk("② Ctrl+Z 로 그 네모가 사라졌다", back == base, [base, back])
        L.chk("② 다시하기 칸에 한 칸이 생겼다", L.ev(b, "S.bredo.length") == 1,
              L.ev(b, "S.bredo.length"))
        L.chk("② 화면도 다시 그려졌다(#boxinfo 가 줄어든 개수를 말한다)",
              ("상자 %d개" % len(base)) in b.js("return document.querySelector('#boxinfo').textContent"),
              b.js("return document.querySelector('#boxinfo').textContent"))

        # ── ③ Ctrl+Y — 체크리스트에 적힌 바로 그 검증 ──────────────────────
        t0 = time.time()
        chord(b, "y")
        again = boxes(b)
        took = round(time.time() - t0, 2)
        L.chk("③ Ctrl+Y 로 네모가 돌아왔다", len(again) == len(base) + 1, again[-1:] if again else None)
        L.chk("③ 좌표가 «글자까지» 그렸던 그대로다(%s)" % made,
              again and again[-1] == made and again == one, [one, again])
        L.chk("③ 다시하기 칸을 썼다(1 → 0)", L.ev(b, "S.bredo.length") == 0)
        L.chk("③ 되돌리기 칸이 도로 채워졌다(또 Ctrl+Z 할 수 있다)",
              L.ev(b, "S.bundo.length") >= 1, L.ev(b, "S.bundo.length"))
        print("   실측 — Ctrl+Y 한 번에 %s초" % took)
        b.shot(os.path.join(shots, "2_redone.png"))

        # ── ④ 세 칸 왕복 ─────────────────────────────────────────────────
        snaps = [boxes(b)]
        for x in (700, 760, 820):
            b.drag("#cv", x, 480, x + 60, 540)
            time.sleep(0.25)
            snaps.append(boxes(b))
        L.chk("④ 세 개를 더 그렸다", len(snaps[-1]) == len(snaps[0]) + 3, len(snaps[-1]))
        good = True
        for k in range(2, -1, -1):
            chord(b, "z")
            if boxes(b) != snaps[k]:
                good = False
        L.chk("④ 세 번 되돌리면 한 칸씩 정확히 뒤로 간다", good, boxes(b))
        L.chk("④ 다시하기 칸이 세 칸이다", L.ev(b, "S.bredo.length") == 3,
              L.ev(b, "S.bredo.length"))
        good = True
        for k in range(1, 4):
            chord(b, "y")
            if boxes(b) != snaps[k]:
                good = False
        L.chk("④ 세 번 다시 실행하면 한 칸씩 정확히 앞으로 간다", good, boxes(b))
        L.chk("④ 마지막이 되돌리기 전과 «글자까지» 같다", boxes(b) == snaps[3], [snaps[3], boxes(b)])
        L.chk("④ 다시하기 칸을 다 썼다", L.ev(b, "S.bredo.length") == 0)

        # ── ⑤ 다시할 것이 없을 때 ─────────────────────────────────────────
        keep = boxes(b)
        chord(b, "y")
        f = flashtext(b)
        L.chk("⑤ 상자를 건드리지 않는다", boxes(b) == keep, boxes(b))
        L.chk("⑤ «다시 실행할 상자 작업이 없습니다» 라고 알린다",
              f and "다시 실행할 상자 작업이 없습니다" in f["text"], f)
        L.chk("⑤ 경고색이다(S2 규칙대로 «확인» 을 눌러야 지워진다)", f and f["bad"] is True, f)
        clear_flash(b)

        # ── ⑥ 되돌린 뒤 새로 그리면 옛 갈래는 버린다 ────────────────────────
        chord(b, "z")
        L.chk("⑥ 한 번 되돌려 다시하기 1칸", L.ev(b, "S.bredo.length") == 1)
        b.drag("#cv", 300, 470, 380, 540)                 # 다른 자리에 새로 그렸다
                                                          # (y 는 600 을 넘기지 않는다 — 캔버스 위 64px
                                                          #  + 화면 높이 682 라 그 아래는 창 밖이다)
        time.sleep(0.3)
        L.chk("⑥ 새로 그리면 다시하기 갈래를 버린다", L.ev(b, "S.bredo.length") == 0,
              L.ev(b, "S.bredo.length"))
        now = boxes(b)
        chord(b, "y")
        f = flashtext(b)
        L.chk("⑥ 그 뒤 Ctrl+Y 는 아무 상자도 되살리지 않는다", boxes(b) == now, [now, boxes(b)])
        L.chk("⑥ 안내만 뜬다", f and "다시 실행할 상자 작업이 없습니다" in f["text"], f)
        clear_flash(b)

        # ── ⑦ «칠한 영역» 다시하기를 누르지 않는다 ──────────────────────────
        L.chk("⑦ 상자 모드에서 Ctrl+Y 가 #redo 를 0회 눌렀다",
              b.js("return window.__redoClicks") == 0, b.js("return window.__redoClicks"))
        L.chk("⑦ 칠한 영역은 손대지 않았다", L.ev(b, "!!S.edDirty") is False, L.ev(b, "!!S.edDirty"))
        b.shot(os.path.join(shots, "3_after.png"))

        # ── ⑧ 상자 모드를 끄면 예전 갈래 그대로 ────────────────────────────
        b.key("x")
        time.sleep(0.3)
        L.chk("⑧ 상자 모드가 꺼졌다", L.ev(b, "!!S.boxMode") is False)
        chord(b, "y")
        L.chk("⑧ 그때 Ctrl+Y 는 예전대로 #redo 로 간다(회귀)",
              b.js("return window.__redoClicks") == 1, b.js("return window.__redoClicks"))
        clear_flash(b)

        # ── ⑨ 단축키 표 · 콘솔 ────────────────────────────────────────────
        row = b.js("""
          const t = document.querySelector('[data-key-table]');
          if (!t) return null;
          const tr = [...t.querySelectorAll('tr')].find(r => /Ctrl/.test(r.textContent) && /Y/.test(r.textContent)
                                                            && /다시 실행/.test(r.textContent));
          return tr ? tr.textContent : null;
        """)
        L.chk("⑨ 화면의 단축키 표에 Ctrl+Y 줄이 있다", row is not None, row)
        L.chk("⑨ 그 줄이 «상자» 도 말한다", row and "상자" in row, row)
        L.chk("⑨ «상자에는 없다» 는 옛말이 사라졌다", row and "상자에는" not in row, row)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑨ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b12_box_redo")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
