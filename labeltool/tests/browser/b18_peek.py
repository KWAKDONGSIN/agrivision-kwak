# -*- coding: utf-8 -*-
"""b18 — **`~` 를 누르고 있는 동안만 «원본만»** (편의 U9).
작성: 2026-09-21

왜
  «내가 칠한 것 밑에 열매가 정말 있나» 는 검수 내내 가장 자주 하는 확인이다. 지금은 Q 를 눌러
  «원본만» 으로 갔다가 «칠한 영역만» 을 지나 «겹쳐» 로 돌아와야 한다(세 번). 포토샵은 레이어
  눈을 누르고 있는 동안만 끄고, 놓으면 저절로 돌아온다 — 손이 기억할 것이 없다.

어떻게
  모래상자 서버에만 붙는다(실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다).
    ① 사진을 열고 «겹쳐» 로 시작한다
    ② 누르고 있는 동안 — 겹이 전부 꺼지고 상자·점선도 쉬고, 3단 스위치가 «원본만» 이 된다
    ③ 놓으면 — 체크·스위치가 원래대로 돌아오고 **캔버스 화소가 한 점도 안 다르다**
    ④ 사람이 꺼 두었던 겹은 **꺼진 채로** 돌아온다(내 마음대로 켜 주지 않는다)
    ⑤ 누르고 있으면 keydown 이 되풀이된다 — 여러 번 와도 한 번만 적는다
    ⑥ «칠한 영역만» 에서 눌렀다 놓으면 «겹쳐» 가 아니라 **«칠한 영역만»** 으로 돌아온다
    ⑦ 글자 칸(«내 이름»)에 커서가 있으면 안 듣고 «~» 가 글자로 찍힌다
    ⑧ Ctrl+~ 는 안 듣는다(다른 프로그램의 단축키다)
    ⑨ 키를 쥔 채 창을 떠나면(알트탭) keyup 이 안 온다 — blur 에서도 풀린다
    ⑩ ② 상자 그리기에서도 상자가 감췄다 돌아오고 «저장 안 됨»(bDirty)은 안 건드린다
    ⑪ 저장 안 한 붓질이 그대로 살아 있다(보기만 바꾸지 그림을 안 건드린다)
    ⑫ 콘솔 오류 0
  `run_all.sh --browser` 묶음(b1·t2)과 따로 돌린다(b5~b17 과 같다).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_peek")
FRUIT = "peach"
STEM = "210629-t1-01"

ERRHOOK = ("window.__errs = window.__errs || [];"
           "if (!window.__ehooked) { window.__ehooked = 1;"
           " window.addEventListener('error', function (e) { window.__errs.push(String(e.message || e)); });"
           " window.addEventListener('unhandledrejection', function (e) { window.__errs.push('reject: ' + String(e.reason)); }); }"
           "return window.__errs.length;")

# 캔버스 화소를 그대로 떠 두고(SNAP) 나중에 몇 점이 다른지 센다(DIFF)
SNAP = ("(function(){const c=document.querySelector('#cv');"
        "window.__snap=c.getContext('2d').getImageData(0,0,c.width,c.height).data.slice();"
        "return window.__snap.length/4;})()")
DIFF = ("(function(){const c=document.querySelector('#cv');"
        "const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data, s=window.__snap;"
        "let n=0;for(let i=0;i<d.length;i+=4)"
        "if(d[i]!==s[i]||d[i+1]!==s[i+1]||d[i+2]!==s[i+2])n++;return n;})()")

TILDE = "~"
CTRL = ""


def down(b, k):
    """키를 **누르기만** 한다(놓지 않는다) — b.key() 는 눌렀다 바로 놓아서 이 시험에 못 쓴다."""
    b._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb",
         "actions": [{"type": "keyDown", "value": k}]}]})


def up(b, k):
    b._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb",
         "actions": [{"type": "keyUp", "value": k}]}]})


def checks(b):
    """여섯 겹의 체크 상태를 한 줄로 — 사람이 켜 둔 대로 돌아오는지 보는 자다."""
    return L.ev(b, "['l-gt','l-ai','l-ed','l-diff','l-num','l-numtext']"
                   ".map(function(i){var e=document.querySelector('#'+i);"
                   "return e&&e.checked?1:0;}).join('')")


def vsw(b):
    """3단 스위치에서 지금 «눌린» 칸."""
    return L.ev(b, "[].slice.call(document.querySelectorAll('.vsw'))"
                   ".filter(function(b){return b.classList.contains('on');})"
                   ".map(function(b){return b.dataset.vm;}).join(',')")


def hidden(b):
    return L.ev(b, "[S.hideBox ? 1 : 0, S.dim]")


def painted(b):
    return L.ev(b, "(function(){let n=0;for(let i=0;i<S.ed.length;i++)if(S.ed[i])n++;return n;})()")


def main():
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5661)
    p = L.start(port=port, sb=SB)
    b = None
    shots = os.path.join(L.SHOTS, "peek")
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
        time.sleep(1.0)
        b.key("0")
        time.sleep(0.5)

        base_chk, base_vsw = checks(b), vsw(b)
        L.chk("① «겹쳐» 로 시작하고 겹이 켜져 있다 (%s · 스위치 %s)" % (base_chk, base_vsw),
              base_vsw == "over" and base_chk[0] == "1", [base_chk, base_vsw])
        L.chk("① 원본 라벨(l-gt)이 켜져 있다", L.ev(b, "document.querySelector('#l-gt').checked"), base_chk)
        b.shot(os.path.join(shots, "1_over.png"))

        # ── ② 누르고 있는 동안 ─────────────────────────────────────────────
        npx = L.ev(b, SNAP)
        L.chk("② 캔버스 화소를 떠 두었다 (%d화소)" % npx, npx > 100000, npx)
        t0 = time.time()
        down(b, TILDE)
        time.sleep(0.4)
        dt = time.time() - t0
        on_chk, on_vsw, on_hid = checks(b), vsw(b), hidden(b)
        L.chk("② 누르는 동안 겹이 **전부** 꺼진다 (%s · %.2f초)" % (on_chk, dt),
              on_chk == "000000", on_chk)
        L.chk("② 스위치가 «원본만» 으로 간다 (%s)" % on_vsw, on_vsw == "photo", on_vsw)
        L.chk("② 상자·점선도 쉰다 (hideBox %s · dim %s)" % (on_hid[0], on_hid[1]),
              on_hid == [1, 0], on_hid)
        d_on = L.ev(b, DIFF)
        L.chk("② 화면이 **정말** 바뀌었다 — %d화소가 달라졌다" % d_on, d_on > 1000, d_on)
        b.shot(os.path.join(shots, "2_peek.png"))

        # ── ③ 놓으면 화소까지 그대로 ───────────────────────────────────────
        t0 = time.time()
        up(b, TILDE)
        time.sleep(0.5)
        d_off = L.ev(b, DIFF)
        L.chk("③ ❗놓으면 캔버스가 **한 화소도 안 다르다** (실측 %d화소 · %.2f초)"
              % (d_off, time.time() - t0), d_off == 0, d_off)
        L.chk("③ 체크도 원래대로 (%s → %s)" % (on_chk, checks(b)), checks(b) == base_chk,
              [checks(b), base_chk])
        L.chk("③ 스위치도 «겹쳐» 로 (%s)" % vsw(b), vsw(b) == "over", vsw(b))
        L.chk("③ hideBox·dim 도 원래대로 %s" % hidden(b), hidden(b) == [0, 0], hidden(b))

        # ── ④ 사람이 꺼 두었던 겹은 꺼진 채로 ──────────────────────────────
        L.run(b, "const e=document.querySelector('#l-ai'); if(e.checked){e.checked=false;"
                 "if(e.onchange)e.onchange(); S.dirty=true;}")
        time.sleep(0.4)
        off_chk = checks(b)
        L.chk("④ AI 겹을 꺼 두었다 (%s)" % off_chk, off_chk[1] == "0", off_chk)
        L.ev(b, SNAP)
        down(b, TILDE)
        time.sleep(0.35)
        L.chk("④ 누르는 동안은 전부 꺼진다 (%s)" % checks(b), checks(b) == "000000", checks(b))
        up(b, TILDE)
        time.sleep(0.45)
        L.chk("④ ❗놓아도 AI 겹은 **꺼진 채로** 돌아온다 (%s) — 내 마음대로 켜 주지 않는다"
              % checks(b), checks(b) == off_chk, [checks(b), off_chk])
        L.chk("④ 그때도 화소가 한 점도 안 다르다 (%d)" % L.ev(b, DIFF), L.ev(b, DIFF) == 0, L.ev(b, DIFF))
        L.run(b, "const e=document.querySelector('#l-ai'); if(!e.checked){e.checked=true;"
                 "if(e.onchange)e.onchange(); S.dirty=true;}")
        time.sleep(0.4)

        # ── ⑤ keydown 이 되풀이돼도 한 번만 적는다 ─────────────────────────
        L.ev(b, SNAP)
        for _ in range(3):
            down(b, TILDE)
            time.sleep(0.15)
        L.chk("⑤ 세 번 눌러도 «원본만» 하나 (%s)" % vsw(b), vsw(b) == "photo", vsw(b))
        up(b, TILDE)
        time.sleep(0.45)
        L.chk("⑤ 한 번 놓으면 제대로 돌아온다 (%s · 화소 차 %d)" % (vsw(b), L.ev(b, DIFF)),
              vsw(b) == "over" and L.ev(b, DIFF) == 0, [vsw(b), L.ev(b, DIFF)])

        # ── ⑥ «칠한 영역만» 에서 눌렀다 놓으면 거기로 돌아온다 ──────────────
        b.key("q"); time.sleep(0.3)            # over → photo
        b.key("q"); time.sleep(0.4)            # photo → mask(«칠한 영역만»)
        L.chk("⑥ Q 두 번으로 «칠한 영역만» (%s)" % vsw(b), vsw(b) == "mask", vsw(b))
        mask_chk = checks(b)
        L.ev(b, SNAP)
        down(b, TILDE)
        time.sleep(0.4)
        L.chk("⑥ 누르는 동안 «원본만» (%s · 겹 %s)" % (vsw(b), checks(b)),
              vsw(b) == "photo" and checks(b) == "000000", [vsw(b), checks(b)])
        up(b, TILDE)
        time.sleep(0.5)
        L.chk("⑥ ❗놓으면 «겹쳐» 가 아니라 **«칠한 영역만»** 으로 (%s)" % vsw(b), vsw(b) == "mask", vsw(b))
        L.chk("⑥ 그 상태의 겹·화소도 그대로 (%s · 차 %d)" % (checks(b), L.ev(b, DIFF)),
              checks(b) == mask_chk and L.ev(b, DIFF) == 0, [checks(b), mask_chk, L.ev(b, DIFF)])
        b.shot(os.path.join(shots, "3_maskonly.png"))
        b.key("q"); time.sleep(0.5)            # mask → over (원래 자리로)
        L.chk("⑥ Q 한 번 더로 «겹쳐» 로 돌아왔다 (%s)" % vsw(b), vsw(b) == "over", vsw(b))

        # ── ⑦ 글자 칸에서는 안 듣는다 ───────────────────────────────────────
        L.run(b, "document.querySelector('#who').value='';document.querySelector('#who').focus()")
        time.sleep(0.2)
        down(b, TILDE); time.sleep(0.3); up(b, TILDE); time.sleep(0.3)
        who = L.ev(b, "document.querySelector('#who').value")
        L.chk("⑦ 이름 칸에 커서가 있으면 보기가 안 바뀐다 (%s)" % vsw(b), vsw(b) == "over", vsw(b))
        L.chk("⑦ 그 «~» 는 글자로 칸에 찍힌다 (%r)" % who, who == "~", who)
        L.run(b, "document.querySelector('#who').value='';document.querySelector('#who').blur()")
        time.sleep(0.2)

        # ── ⑧ Ctrl+~ 는 안 듣는다 ──────────────────────────────────────────
        down(b, CTRL); down(b, TILDE)
        time.sleep(0.35)
        ctrl_vsw = vsw(b)
        up(b, TILDE); up(b, CTRL)
        time.sleep(0.35)
        L.chk("⑧ Ctrl+~ 는 안 듣는다 (누르는 동안 %s)" % ctrl_vsw, ctrl_vsw == "over", ctrl_vsw)

        # ── ⑨ 키를 쥔 채 창을 떠나면(알트탭) 풀린다 ─────────────────────────
        #     진짜 알트탭은 헤드리스에서 못 만든다 → 브라우저가 그때 보내는 blur 만 보낸다.
        L.ev(b, SNAP)
        down(b, TILDE)
        time.sleep(0.35)
        L.chk("⑨ 쥐고 있다 (%s)" % vsw(b), vsw(b) == "photo", vsw(b))
        L.run(b, "window.dispatchEvent(new Event('blur'))")
        time.sleep(0.45)
        L.chk("⑨ ❗창을 떠나면 keyup 없이도 풀린다 (%s · 화소 차 %d)" % (vsw(b), L.ev(b, DIFF)),
              vsw(b) == "over" and L.ev(b, DIFF) == 0, [vsw(b), L.ev(b, DIFF)])
        up(b, TILDE)
        time.sleep(0.35)
        L.chk("⑨ 뒤늦게 온 keyup 이 아무것도 안 뒤집는다 (%s · 차 %d)" % (vsw(b), L.ev(b, DIFF)),
              vsw(b) == "over" and L.ev(b, DIFF) == 0, [vsw(b), L.ev(b, DIFF)])

        # ── ⑩ ② 상자 그리기에서도 ──────────────────────────────────────────
        b.key("x"); time.sleep(0.6)
        L.chk("⑩ 상자 모드로 들어왔다", L.ev(b, "S.boxMode") is True, L.ev(b, "S.boxMode"))
        b.drag("#cv", 380, 300, 520, 420)
        time.sleep(0.6)
        nbox, bdirty = L.ev(b, "(S.boxes||[]).length"), L.ev(b, "S.bDirty ? 1 : 0")
        L.chk("⑩ 네모를 하나 더 그렸다 (이 사진의 상자 %d개 · 저장 안 됨 %d)" % (nbox, bdirty),
              nbox > 0 and bdirty == 1,
              [nbox, bdirty])
        L.ev(b, SNAP)
        down(b, TILDE)
        time.sleep(0.4)
        L.chk("⑩ 누르는 동안 상자·흰 필름이 쉰다 (hideBox %s)" % hidden(b)[0], hidden(b)[0] == 1, hidden(b))
        d_box = L.ev(b, DIFF)
        L.chk("⑩ 화면이 정말 바뀌었다 (%d화소)" % d_box, d_box > 1000, d_box)
        b.shot(os.path.join(shots, "4_box_peek.png"))
        up(b, TILDE)
        time.sleep(0.5)
        L.chk("⑩ 놓으면 상자가 화소까지 그대로 돌아온다 (차 %d)" % L.ev(b, DIFF), L.ev(b, DIFF) == 0,
              L.ev(b, DIFF))
        L.chk("⑩ 상자 개수·«저장 안 됨» 은 안 건드렸다 (%d개 · %d)"
              % (L.ev(b, "(S.boxes||[]).length"), L.ev(b, "S.bDirty ? 1 : 0")),
              L.ev(b, "(S.boxes||[]).length") == nbox and L.ev(b, "S.bDirty ? 1 : 0") == 1,
              [L.ev(b, "(S.boxes||[]).length"), nbox])
        L.run(b, "S.bDirty=false; S.boxes.length=0; S.dirty=true")
        b.key("x"); time.sleep(0.6)
        L.chk("⑩ 상자 모드를 껐다", L.ev(b, "S.boxMode") is False, L.ev(b, "S.boxMode"))

        # ── ⑪ 저장 안 한 붓질이 그대로 ──────────────────────────────────────
        b.key("b"); time.sleep(0.3)
        b.drag("#cv", 300, 300, 620, 340)
        time.sleep(0.6)
        px0, dirty0 = painted(b), L.ev(b, "S.edDirty ? 1 : 0")
        L.chk("⑪ 붓질을 했다 (%d화소 · 저장 안 됨 %d)" % (px0, dirty0), px0 > 0 and dirty0 == 1,
              [px0, dirty0])
        L.ev(b, SNAP)
        down(b, TILDE); time.sleep(0.4)
        L.chk("⑪ 누르는 동안 내 수정본도 안 보인다 (%s)" % checks(b), checks(b) == "000000", checks(b))
        up(b, TILDE); time.sleep(0.5)
        L.chk("⑪ ❗놓으면 칠한 화소가 **그대로** (%d → %d)" % (px0, painted(b)), painted(b) == px0,
              [px0, painted(b)])
        L.chk("⑪ «저장 안 됨» 도 그대로 (%d)" % L.ev(b, "S.edDirty ? 1 : 0"),
              L.ev(b, "S.edDirty ? 1 : 0") == 1, L.ev(b, "S.edDirty ? 1 : 0"))
        L.chk("⑪ 화면도 화소까지 그대로 (차 %d)" % L.ev(b, DIFF), L.ev(b, DIFF) == 0, L.ev(b, DIFF))
        b.shot(os.path.join(shots, "5_after.png"))

        # ── ⑫ 콘솔 ─────────────────────────────────────────────────────────
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("⑫ 콘솔에 깨진 약속·오류가 없다", not errs, errs)
        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    return L.summary("b18_peek")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
