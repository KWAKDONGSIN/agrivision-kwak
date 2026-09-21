# -*- coding: utf-8 -*-
"""사이클 4 1차 — **진짜 파이어폭스**(1366×768)로 ② 상자·③ 번호 확정과 마스킹 편의 3가지.
작성: 2026-09-18

  가) 새 서버(5311) — ② 상자 모드 Enter → 상자 확정 · 마스크 확정 불변 · 하단 한 줄 문구
  나) 새 서버 — ③ 번호 모드 Enter(사과) · 복숭아는 ③ 자체가 잠긴다
  다) 마스킹 편의 셋 — 붓 크기 기억(브라우저를 새로 열어도) · 자동 확대 · 기본 도구
  라) 옛 서버(5312, 백업 서버 + **새 정적 파일**) — 가드 + 사진이 안 넘어간다
  마) 글자 예산 — 편집 화면 글자 수(#view-edit) 재측정
스크린샷은 ~/ff_shots/c4/stage1/ 에만.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox as L                                  # tests/lib/sandbox.py

OUT = {}
FR = "apple"


def shot(b, name):
    p = os.path.join(L.SHOTS, name + ".png")
    b.shot(p)
    return p


def open_exact(b, fruit, stem):
    b.js("['#f-dup','#f-suspect','#f-prop'].forEach(s=>{const e=document.querySelector(s);"
         "if(e&&e.checked){e.checked=false;}});"
         "document.querySelector('#f-q').value='';"
         "document.querySelector('#f-status').value='all';"
         "document.querySelector('#f-sort').value='priority';")
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];s.dispatchEvent(new Event('change'))", fruit)
    b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
    b.js("const q=document.querySelector('#f-q');q.value=arguments[0];"
         "q.dispatchEvent(new Event('input',{bubbles:true}));"
         "q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))", stem)
    time.sleep(1.2)
    pick = ("const c=[...document.querySelectorAll('#grid .card')]"
            ".find(c=>c.querySelector('.cap').firstChild.textContent.trim()===arguments[0]);")
    b.wait_js(pick + "return !!c", stem, timeout=60)
    b.js(pick + "c.click()", stem)
    b.wait("return document.querySelector('#loading').classList.contains('hidden')"
           " && document.querySelector('#stemname').textContent.length>3", 90)
    time.sleep(1.0)


def unfocus(b):
    b.js("document.activeElement && document.activeElement.blur(); document.body.focus();")
    return b.js("return document.activeElement ? document.activeElement.tagName : '-'")


def task(b, t):
    # 🔴 2026-09-21: ③ 번호 단추는 `/instances` 그림이 다 실린 뒤에야 켜진다
    #   (view.js «b.disabled = !S.inst»). `open_exact()` 가 자는 1초로는 모자랄 때가 있다 —
    #   데이터를 갓 복사한 «차가운» 모래상자에서 실측 **2.17초**. 잠긴 단추를 누르면 아무 일도
    #   없이 지나가서 나-0~나-3 이 한꺼번에 진다(원인은 화면 코드가 아니라 이 기다림이었다).
    #   → 켜질 때까지 기다렸다 누른다. 번호본이 없는 사진이면 끝까지 잠겨 있고, 그것은
    #     부르는 쪽(나-4)이 `disabled` 를 직접 읽어 본다.
    if t == "num":
        try:
            b.wait_js("const x=[...document.querySelectorAll('.task')].find(e=>e.dataset.task==='num');"
                      "return !!x && !x.disabled;", timeout=20)
        except Exception:
            pass
    b.js("[...document.querySelectorAll('.task')].find(x=>x.dataset.task===arguments[0]).click()", t)
    time.sleep(0.8)


def conf_of(fruit, stem, kind):
    key = {"mask": "confirmed", "boxes": "confirmed_boxes",
           "instances": "confirmed_instances"}[kind]
    return ((L.status_of(fruit).get(stem) or {}).get(key) or {}).get("status")


ENTER = ""


# ═══════════════════════════ [가]+[나]+[다]+[마] 새 서버 ═══════════════════════════
def part_new():
    print("\n[가] 새 서버 — ② 상자 모드 Enter 가 «상자 확정» 이다", flush=True)
    L.reset_status()
    p = L.start()
    b = None
    try:
        b = L.browser(1366, 768)
        b.js("document.querySelector('#who').value='곽동신';")
        stems = [x["stem"] for x in L.Api().get("/api/list?fruit=%s&page_size=20" % FR)["items"]]
        s0, s1 = stems[0], stems[1]
        open_exact(b, FR, s0)
        # 먼저 마스크를 확정해 둔다 — 상자 확정이 그것을 건드리지 않는지 보려고
        unfocus(b)
        b.key("1")
        time.sleep(2.0)
        L.eat_alert(b)
        L.chk("가-0 «1» 로 마스크를 확정했다", conf_of(FR, s0, "mask") == "ok", conf_of(FR, s0, "mask"))
        # 0918 사이클4 (s5 C-2·C-4 설계안): «1» 은 이제 confirmed 만 쓴다 — AI 제안은 그대로
        rec = L.status_of(FR).get(s0) or {}
        OUT["key1_keeps_ai"] = {k: rec.get(k) for k in ("status", "by")}
        L.chk("가-0b ❗«1» 이 AI 제안(status·by)을 덮지 않는다 (C-2·C-4)",
              str(rec.get("by", "")).startswith("AI"), OUT["key1_keeps_ai"])
        # «1» 은 다음 사진으로 넘어간다 → 다시 s0 를 연다
        open_exact(b, FR, s0)
        task(b, "box")
        line0 = b.js("return document.querySelector('#todo').textContent").strip()
        OUT["box_line_before"] = line0
        print("      ② 하단 한 줄(확정 전): «%s»" % line0)
        L.chk("가-1 ② 하단 한 줄이 «AI 초벌 상자 … 맞으면 Enter» 라고 말한다",
              "초벌" in line0 and "상자" in line0 and "Enter" in line0, line0)
        # 초벌을 만든다(사람이 «초벌» 단추를 누르는 것과 같다)
        b.js("document.querySelector('#boxseed').click()")
        for _ in range(60):                       # S 는 webdriver 에서 안 보인다 → window.eval(L.ev)
            if L.ev(b, "S.boxes.length") > 0:
                break
            time.sleep(0.5)
        nbox = L.ev(b, "S.boxes.length")
        L.chk("가-1b «초벌» 단추가 상자를 만들었다", nbox > 0,
              "%s · %s" % (nbox, b.js("return document.querySelector('#boxinfo').textContent")))
        shot(b, "c4_01_box_seed")
        unfocus(b)
        b.key(ENTER)
        time.sleep(3.0)
        L.eat_alert(b)
        L.chk("가-2 ❗Enter → confirmed_boxes = ok (저장+확정)",
              conf_of(FR, s0, "boxes") == "ok", conf_of(FR, s0, "boxes"))
        L.chk("가-3 ❗마스크 확정은 그대로 ok (독립)", conf_of(FR, s0, "mask") == "ok",
              conf_of(FR, s0, "mask"))
        L.chk("가-4 상자 파일이 실제로 저장됐다",
              os.path.exists("%s/data/%s/boxes/%s.json" % (L.SB, FR, s0)))
        stem_now = b.js("return document.querySelector('#stemname').textContent")
        fl = b.js("return document.querySelector('#saveflash').textContent")
        # open_exact() 는 **검색으로 한 장만** 남긴 목록이라 «다음 장» 이 없다(그 말이 뜨면 통과다).
        L.chk("가-5 확정 뒤 다음 사진으로 간다(목록이 한 장이면 «마지막 사진» 이라고 말한다)",
              stem_now != s0 or "마지막 사진" in fl, "%s → %s · flash «%s»" % (s0, stem_now, fl))
        OUT["box_enter"] = {"n_boxes": nbox, "next": stem_now != s0}
        # 확정된 사진을 다시 열면 «✔ 상자 확정» 이라고 말한다
        open_exact(b, FR, s0)
        task(b, "box")
        line1 = b.js("return document.querySelector('#todo').textContent").strip()
        OUT["box_line_after"] = line1
        print("      ② 하단 한 줄(확정 뒤): «%s»" % line1)
        L.chk("가-6 확정 뒤에는 «✔ 상자 확정»", "상자 확정" in line1, line1)
        shot(b, "c4_02_box_confirmed")

        # ── 저장(Ctrl+S) = «수정함» 으로 확정
        open_exact(b, FR, s1)
        task(b, "box")
        # 🔴 0919 사이클5(총괄) 3차 소수정 — **좌표만** 고쳤습니다(기대값은 그대로).
        # 사이클5 1차의 «그림판 재배치» 뒤 캔버스가 1172×564 로 넓고 낮아져서, 세로 사진(1080×1920)은
        # 가운데 좁은 기둥(왼쪽 여백 432px)에만 그려집니다. 그래서 (300,200)→(420,320) 은 **회색 여백**이고
        # `clampX` 가 둘 다 0 으로 잘라 **상자가 하나도 만들어지지 않았습니다**(실측 `stage2c/rep/d1_box7.log`).
        # 그런데도 이 시험이 통과했던 이유는 옛 서버가 «상자 0개 저장» 도 `fixed` 로 찍어 줬기 때문입니다.
        # 2차 고침 1(«0개 저장 = 되돌리기»)이 그것을 드러내 가-7 이 26/1 로 떨어졌습니다.
        # → 사진이 **실제로 그려진 자리**(`S.view = {s, tx, ty}`)로 좌표를 계산해 끕니다.
        _v = L.ev(b, "({s:S.view.s, tx:S.view.tx, ty:S.view.ty, W:S.W, H:S.H})")
        _pt = lambda fx, fy: (_v["tx"] + _v["W"] * fx * _v["s"], _v["ty"] + _v["H"] * fy * _v["s"])
        _x0, _y0 = _pt(0.30, 0.30)
        _x1, _y1 = _pt(0.60, 0.60)
        b.drag("#cv", _x0, _y0, _x1, _y1)
        time.sleep(0.6)
        b.js("document.querySelector('#boxsave').click()")
        time.sleep(2.5)
        L.eat_alert(b)
        L.chk("가-7 상자 저장 → confirmed_boxes = fixed", conf_of(FR, s1, "boxes") == "fixed",
              conf_of(FR, s1, "boxes"))
        L.chk("가-7b 그 사진의 마스크 확정은 생기지 않았다", conf_of(FR, s1, "mask") is None,
              conf_of(FR, s1, "mask"))

        # ── ③ 번호
        print("\n[나] ③ 번호 모드 Enter — 사과는 되고 복숭아는 ③ 가 잠긴다", flush=True)
        s2 = stems[2]
        open_exact(b, FR, s2)
        task(b, "num")
        L.chk("나-0 사과에서는 ③ 이 켜진다", L.ev(b, "!!S.numMode"))
        line2 = b.js("return document.querySelector('#todo').textContent").strip()
        OUT["num_line"] = line2
        print("      ③ 하단 한 줄: «%s»" % line2)
        # 2026-09-19 tests/ 로 옮기며 고친 기대값(ORIGIN.md 에 적음): 0919 «개수 세기» 사이클이
        # «AI 초벌 번호» 라는 한 낱말을 **출처 이름**(원본 정답 번호 · 박성문 · CERTH 정답 송이 ·
        # 사람이 고친 번호 · 4-연결)으로 바꿨다. 그래서 «초벌» 이라는 글자를 요구하지 않고
        # «번호 + 출처 낱말 하나 + Enter» 를 요구한다(출처를 지어내지 않는지는 b1_browser 가 본다).
        SRC_WORDS = ("초벌", "정답", "박성문", "고친", "4-연결")
        L.chk("나-1 ③ 한 줄이 «<번호 출처> … 맞으면 Enter»",
              "번호" in line2 and "Enter" in line2
              and any(w in line2 for w in SRC_WORDS), line2)
        unfocus(b)
        b.key(ENTER)
        time.sleep(3.0)
        L.eat_alert(b)
        L.chk("나-2 ❗Enter → confirmed_instances = ok", conf_of(FR, s2, "instances") == "ok",
              conf_of(FR, s2, "instances"))
        L.chk("나-3 ❗마스크·상자 확정은 안 생긴다",
              conf_of(FR, s2, "mask") is None and conf_of(FR, s2, "boxes") is None,
              (conf_of(FR, s2, "mask"), conf_of(FR, s2, "boxes")))
        shot(b, "c4_03_num_confirmed")
        # 복숭아 — 번호가 없으므로 ③ 단추가 잠겨 있다
        b.js("const t=[...document.querySelectorAll('.tab')].find(x=>x.dataset.view==='list');"
             "if(t) t.click();")
        time.sleep(0.5)
        ps = [x["stem"] for x in L.Api().get("/api/list?fruit=peach&page_size=5")["items"]]
        open_exact(b, "peach", ps[0])
        time.sleep(1.0)
        dis = b.js("return document.querySelector('.task[data-task=num]').disabled")
        # 🔴 기대값이 바뀌었다 — 2026-09-19 «개수 세기» **사이클4 결정 M1**: `instances.SEED_DIRS` 에
        # 복숭아(박성문 워터셰드 `instance_maps`)·포도(CERTH 정답 송이)를 넣어 **네 과일 모두 번호본이
        # 있다.** 그래서 ③ 번호 단추가 켜진다. 전에는 복숭아·포도가 잠겨 있었다.
        L.chk("나-4 복숭아도 ③ 번호 단추가 켜져 있다(번호본이 생겼다 · 사이클4 M1)", dis is False, dis)
        task(b, "box")
        line3 = b.js("return document.querySelector('#todo').textContent").strip()
        L.chk("나-5 복숭아에서도 ② 상자 줄은 정상", "상자" in line3, line3)
        OUT["peach_box_line"] = line3

        # ── [다] 마스킹 편의 3가지
        print("\n[다] 마스킹 편의 — 붓 크기 기억 · 자동 확대 · 기본 도구", flush=True)
        open_exact(b, FR, stems[3])
        task(b, "mask")
        b.js("const e=document.querySelector('#brush'); e.value=77;"
             "e.dispatchEvent(new Event('input',{bubbles:true}));")
        time.sleep(0.6)
        ls = b.js("return localStorage.getItem('brush:apple')")
        L.chk("다-1 붓 크기를 과일별로 적어 둔다", ls == "77", ls)
        tool0 = L.ev(b, "S.tool")
        L.chk("다-2 사진을 열 때 기본 도구가 «자동채움»(AI 제안이 있는 사진)",
              tool0 == "smartadd", tool0)
        OUT["default_tool"] = tool0
        # 노란 점선 후보가 있는 사진 → 자동 확대(맞춤보다 배율이 크다)
        st = L.status_of(FR)
        cand = [s for s, r in st.items()
                if "후보" in str(r.get("note") or "") and "(" in str(r.get("note") or "")]
        if cand:
            open_exact(b, FR, sorted(cand)[0])
            time.sleep(1.2)
            z = L.ev(b, "[S.view.s, Math.min(cv.width/(cv._dpr||1)/S.W,"
                        " cv.height/(cv._dpr||1)/S.H)*0.97, (S.noteBoxes||[]).length]")
            OUT["autozoom"] = z
            L.chk("다-3 ❗«할 일» 후보가 있는 사진은 자동으로 확대된다(맞춤 배율보다 크다)",
                  z[2] > 0 and z[0] > z[1] * 1.05, z)
        else:
            L.warn("다-3 이 모래상자에 «후보 좌표» 가 적힌 사진이 없다 — 건너뜀")
        # 마스크(AI 제안)가 없는 사진은 기본이 «붓»
        noai = [x["stem"] for x in L.Api().get("/api/list?fruit=peach&page_size=5")["items"]]
        open_exact(b, "peach", noai[0])
        time.sleep(1.0)
        OUT["tool_peach"] = L.ev(b, "[S.tool, !!S.ai]")
        L.chk("다-4 AI 제안이 없는 사진은 예전대로 «붓»",
              OUT["tool_peach"][1] or OUT["tool_peach"][0] == "brush", OUT["tool_peach"])
        # 페이지를 통째로 새로 읽어도 붓 크기가 남아 있나
        # ⚠ 정직하게: 이 시험 도구(scripts/ff.py)는 Browser() 마다 **새 파이어폭스 프로필**을 만들어
        #    localStorage 가 비어 버린다. 그래서 «창을 새로 여는 것» 대신 **새로고침**(같은 프로필에서
        #    JS 를 처음부터 다시 읽는 것)으로 시험한다 — 붓 크기를 localStorage 에서 읽어 오는
        #    코드 경로는 똑같다. 실제 사람의 브라우저는 프로필이 남으므로 창을 닫아도 유지된다.
        chars = L.count_text(b, "#view-edit")["chars"]
        shot(b, "c4_04_mask_convenience")
        b.go("/")
        b.wait("return !!document.querySelector('#fruit option')", 60)
        time.sleep(1.5)
        open_exact(b, FR, stems[4])
        time.sleep(0.8)
        br = L.ev(b, "[S.brush, document.querySelector('#brush').value]")
        OUT["brush_after_reload"] = br
        L.chk("다-5 ❗새로고침해도 붓 크기가 남아 있다(사과 77)",
              br[0] == 77 and str(br[1]) == "77", br)
        L.warn("다-5b 시험 도구가 프로필을 새로 만들어 «창을 새로 여는 것» 자체는 못 잰다 — 새로고침으로 대신함")

        # ── [마] 글자 예산
        print("\n[마] 편집 화면 글자 수(#view-edit) — 사이클3 3차 때와 비교", flush=True)
        for t, name in (("mask", "①"), ("box", "②"), ("num", "③")):
            open_exact(b, FR, stems[5])
            task(b, t)
            time.sleep(0.8)
            c = L.count_text(b, "#view-edit")
            OUT["chars_" + t] = c["chars"]
            print("      %s %s : %d자" % (name, t, c["chars"]))
        L.chk("마-1 편집 화면 글자 300자 이내(그림판식 · s6_layout 배치-5 와 같은 기준)",
              max(OUT["chars_mask"], OUT["chars_box"], OUT["chars_num"]) <= 300,
              {k: v for k, v in OUT.items() if k.startswith("chars_")})
        OUT["chars_edit_view"] = chars
        shot(b, "c4_05_chars")
    finally:
        if b:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)


# ═══════════════════════════ [라] 옛 서버 가드 ═══════════════════════════
def part_old():
    print("\n[라] 옛 서버(5312) + 새 화면 — 가드가 뜨고 사진이 안 넘어간다", flush=True)
    L.sync(L.SB_OLD, old=True)
    L.reset_status(L.SB_OLD)
    p = L.start(port=L.OLD_PORT, sb=L.SB_OLD)
    b = None
    try:
        b = L.browser(1366, 768, base="http://127.0.0.1:%d" % L.OLD_PORT)
        b.js("document.querySelector('#who').value='가드확인';")
        b.js("const s=document.querySelector('#fruit');s.value='apple';"
             "s.dispatchEvent(new Event('change'))")
        b.wait("return document.querySelectorAll('#grid .card').length>1", 60)
        time.sleep(1.2)
        b.js("document.querySelectorAll('#grid .card')[0].click()")
        b.wait("return document.querySelector('#loading').classList.contains('hidden')"
               " && document.querySelector('#stemname').textContent.length>3", 90)
        time.sleep(1.2)
        stem0 = b.js("return document.querySelector('#stemname').textContent")
        before = dict(L.status_of("apple", L.SB_OLD).get(stem0) or {})
        b.js("[...document.querySelectorAll('.task')].find(x=>x.dataset.task==='box').click()")
        time.sleep(1.0)
        line = b.js("return document.querySelector('#todo').textContent").strip()
        OUT["old_guard_line"] = line
        print("      옛 서버의 ② 하단 줄: «%s»" % line)
        L.chk("라-1 ❗«서버가 아직 상자 확정을 모릅니다» 가 뜬다", "서버가 아직" in line and "상자" in line,
              line)
        unfocus(b)
        b.key(ENTER)
        time.sleep(3.0)
        L.eat_alert(b)
        stem1 = b.js("return document.querySelector('#stemname').textContent")
        aft = dict(L.status_of("apple", L.SB_OLD).get(stem0) or {})
        OUT["old_after"] = {k: aft.get(k) for k in ("status", "by", "confirmed", "confirmed_boxes")}
        L.chk("라-2 ❗#stemname 이 그대로다(다음 사진으로 안 넘어간다)", stem1 == stem0,
              "%s → %s" % (stem0, stem1))
        L.chk("라-3 옛 서버에 확정이 한 건도 안 쓰였다",
              not aft.get("confirmed") and not aft.get("confirmed_boxes"), OUT["old_after"])
        L.chk("라-4 AI 제안(status·by)도 그대로다",
              aft.get("status") == before.get("status") and aft.get("by") == before.get("by"),
              (before.get("by"), aft.get("by")))
        flashes = b.js("return document.querySelector('#saveflash').textContent")
        OUT["old_flash"] = flashes
        shot(b, "c4_06_oldserver_guard")
    finally:
        if b:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)


def main():
    L.sync()
    L.reset_status()
    part_new()
    part_old()
    with open(os.path.join(L.HERE, "t2_ui.json"), "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1)
    return L.summary("t2_ui")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
