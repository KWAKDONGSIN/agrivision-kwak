# -*- coding: utf-8 -*-
"""b3 — **진짜 파이어폭스 10장 시나리오** (1366×768): «화면 분리» 전후가 똑같은지 본다.
작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» 1차)

왜
  구조 사이클 3 은 `app.js`·`ui.js` 를 `static/js/*.js` 12파일로 쪼갠다. 시뮬(boxsim·modesim)은
  **떼어 낸 함수**만 보고, 기준선 ④(정적 파일 sha256)는 «달라졌다» 고만 한다. 그래서 «사람이
  쓰는 화면이 똑같은가» 를 보는 것은 **진짜 브라우저**뿐이다(cycle_1/stage2_review.md §2-1).

무엇을 보나 — 10걸음마다 ① 스크린샷 ② «상태 한 줄» 을 JSON 으로 적는다.
  쪼개기 **전** 트리에서 한 번, **뒤** 트리에서 한 번 돌려 그 JSON 을 글자까지 대조한다.
  ③ 파일 12개가 **다 실렸는가**(파일마다 UI 에 있어야 할 이름 하나씩) — 불러올 때 터진 파일이 있으면 잡힌다
  ④ 걸음마다 콘솔 오류(window.onerror·unhandledrejection) 0 개
  ⑤ 옛 서버(파이썬만 옛 판) + 새 화면 = 가드 문구가 그대로 뜨고 사진이 넘어가지 않는다

지키는 것
  · 모래상자 서버(빈 포트) 에만 붙는다. 실서버 5111 · 교수님 5100·5101·5105 에는 붙지 않는다.
  · 스크린샷은 `~/ff_shots/st3/<tag>/` 에만. 쓰기는 `tests/_sandbox/` 안에서만.
  · 사진을 **저장하지 않는다**(붓질·상자는 화면에만 남긴다) — 판정 자료를 건드리지 않는다.

쓰는 법
  python3 b3_struct3.py --tag before     (쪼개기 전 트리에서)
  python3 b3_struct3.py --tag after      (쪼갠 트리에서)
  python3 b3_struct3.py --diff <before.json> <after.json>
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))   # tests/lib
import sandbox as L                                      # tests/lib/sandbox.py

FRUIT = "peach"
STEM = "210629-t1-01"
SB = os.path.join(L.SB_ROOT, "sb_st3")
SB_OLD = os.path.join(L.SB_ROOT, "sb_st3_old")

# 파일 12개가 다 실렸는지 — 파일마다 «그 파일만 내놓는 이름» 하나
FILE_MARK = [("state.js", "UI.statusKo"), ("api.js", "UI.flash"), ("view.js", "UI.fitView"),
             ("mask.js", "UI.setTool"), ("boxes.js", "UI.saveBoxes"), ("instances.js", "UI.numKey"),
             ("counts.js", "UI.doAction"), ("list.js", "UI.openItem"), ("export.js", "window.expOpen"),
             ("tour.js", "UI.tourOpen"), ("keys.js", "UI.KEYS"), ("main.js", "S.fruit")]

HOOK = """
window.__errs = window.__errs || [];
if (!window.__hooked) {
  window.__hooked = 1;
  window.addEventListener("error", function (e) { window.__errs.push(String(e.message || e)); });
  window.addEventListener("unhandledrejection", function (e) { window.__errs.push("reject: " + String(e.reason)); });
}
return window.__errs.length;
"""

STATE = """
const q = (s) => document.querySelector(s);
const txt = (s) => { const e = q(s); return e ? (e.textContent || "").replace(/\\s+/g, " ").trim() : null; };
const vis = (s) => { const e = q(s); return e ? (getComputedStyle(e).display !== "none") : null; };
const chk = (s) => { const e = q(s); return e ? [!!e.checked, !!e.disabled] : null; };
return JSON.stringify({
  stem: S.stem, fruit: S.fruit, tool: S.tool, boxMode: !!S.boxMode, numMode: !!S.numMode,
  nBoxes: (S.boxes || []).length, bsel: S.bsel, bDirty: !!S.bDirty, edDirty: !!S.edDirty,
  numDirty: !!S.numDirty, instN: S.instN === undefined ? null : S.instN,
  nUndo: (S.undo || []).length, nBundo: (S.bundo || []).length,
  scale: Math.round((S.view ? S.view.s : 0) * 1000), dim: S.dim || 0, hideBox: !!S.hideBox,
  view: ["list", "edit", "dash", "exp"].filter((v) => { const e = q("#view-" + v); return e && !e.classList.contains("hidden"); }),
  todo: txt("#todo"), cnts: txt("#cnts"), boxinfo: txt("#boxinfo"), numinfo: txt("#numinfo"),
  stemname: txt("#stemname"), curtask: txt("#curtask"), taskbadge: txt("#taskbadge"),
  legend: (q("#legend") ? q("#legend").querySelectorAll("[data-tgl]").length : null),
  panels: { toolbox: vis("#toolbox"), boxpanel: vis("#boxpanel"), numpanel: vis("#numpanel"),
            legend: vis("#legend"), tour: vis("#tour") },
  layers: { gt: chk("#l-gt"), ai: chk("#l-ai"), ed: chk("#l-ed"), diff: chk("#l-diff"),
            num: chk("#l-num"), inst: chk("#l-inst") },
  cards: document.querySelectorAll("#grid .card").length,
  vsw: [...document.querySelectorAll(".vsw")].map((b) => b.className.indexOf("on") >= 0 ? 1 : 0),
  task: [...document.querySelectorAll(".task")].map((b) => (b.className.indexOf("on") >= 0 ? 1 : 0) + (b.disabled ? "d" : "")),
  errs: (window.__errs || []).slice()
});
"""


def ev(b, expr):
    """페이지의 «최상위 const»(S·API·UI)는 WebDriver 의 격리 칸에서 안 보인다 → window.eval 로 본다
    (tests/lib/sandbox.py 의 ev() 와 같은 까닭 · b1_browser.py 주석)."""
    return b.js("return window.eval(arguments[0])", expr)


def snap(b, out, name, tag):
    """걸음 하나 — 스크린샷 + 상태."""
    st = json.loads(ev(b, "(function(){" + STATE + "})()"))
    shot = os.path.join(L.SHOTS, tag, "%s.png" % name)
    os.makedirs(os.path.dirname(shot), exist_ok=True)
    b.shot(shot)
    errs = st.pop("errs")
    out[name] = st
    L.chk("%s: 콘솔 오류 0" % name, not errs, errs)
    return st


def run(tag):
    os.makedirs(os.path.join(L.SHOTS, tag), exist_ok=True)
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5501)
    p = L.start(port=port, sb=SB)
    out = {"_tag": tag, "_port": port}
    b = None
    try:
        b = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port)
        b.js(HOOK)
        # ③ 파일 12개가 다 실렸나 (쪼개기 전 트리에서는 그런 파일이 없으므로 경고로만)
        split = os.path.isdir(os.path.join(L.T, "app", "static", "js"))
        for fn, expr in FILE_MARK:
            got = ev(b, "(function(){ try { return typeof (%s) } catch (e) { return 'ReferenceError' } })()" % expr)
            ok = got not in ("undefined", "ReferenceError")
            if split:
                L.chk("파일이 실렸다: %s (%s)" % (fn, expr), ok, got)
            elif not ok:
                L.warn("쪼개기 전 트리라 %s 는 아직 없다(%s)" % (fn, expr), got)
        # 1) 목록
        b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
             "s.dispatchEvent(new Event('change'))", FRUIT)
        b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
        time.sleep(0.6)
        snap(b, out, "01_list", tag)
        # 2) 사진 열기
        b.open_photo(FRUIT, STEM)
        b.js(HOOK)
        snap(b, out, "02_edit", tag)
        # 3) Q — 보기 전환(원본만)
        b.key("q")
        time.sleep(0.6)
        snap(b, out, "03_view_photo_only", tag)
        b.key("q"); time.sleep(0.3); b.key("q"); time.sleep(0.6)      # 겹쳐로 되돌린다
        # 4) 붓(B) 으로 칠하기 — 저장하지 않는다
        b.key("b"); time.sleep(0.3)
        b.drag("#cv", 700, 380, 760, 420)
        time.sleep(0.6)
        snap(b, out, "04_brush", tag)
        # 5) 되돌리기(Ctrl+Z)
        b.js("document.querySelector('#undo').click()")
        time.sleep(0.5)
        snap(b, out, "05_undo", tag)
        # 6) D — 차이 보기
        b.key("d"); time.sleep(0.6)
        snap(b, out, "06_diff", tag)
        b.key("d"); time.sleep(0.4)
        # 7) X — 상자 모드 + 초벌
        b.key("x"); time.sleep(0.8)
        b.js("document.querySelector('#boxseed').click()")
        time.sleep(2.5)
        snap(b, out, "07_boxes_seed", tag)
        # 8) 상자 하나 그리기(저장 안 함)
        b.js("[...document.querySelectorAll('.btool')].find(e=>e.dataset.btool==='draw').click()")
        time.sleep(0.4)
        b.drag("#cv", 500, 300, 560, 360)
        time.sleep(0.6)
        snap(b, out, "08_box_draw", tag)
        b.js("document.querySelector('#boxundo').click()"); time.sleep(0.5)
        b.key("x"); time.sleep(0.6)                                   # 상자 모드 끄기
        # 9) K — 번호 편집 모드
        b.key("k"); time.sleep(1.0)
        snap(b, out, "09_num_mode", tag)
        b.key("k"); time.sleep(0.6)
        # 탭을 옮기기 전에 «저장 안 한 것» 딱지를 내린다 — 확인창이 뜨면 WebDriver 가 그것을
        # «취소» 로 처리해(기본값 dismiss) 시나리오가 갈라진다. 딱지 자체는 04·08 걸음의 상태
        # JSON(edDirty·bDirty·numDirty)에 이미 적혀 있으므로 전후 대조에서 빠지지 않는다.
        ev(b, "(function(){ S.edDirty=false; S.bDirty=false; S.numDirty=false; return 1 })()")
        # 10) 오른쪽 패널 펴기 + 현황 탭
        b.js("document.querySelector('#sidetgl').click()"); time.sleep(0.6)
        snap(b, out, "10_side_open", tag)
        b.js("[...document.querySelectorAll('.tab')].find(e=>e.dataset.view==='dash').click()")
        b.wait("return document.querySelector('#dash').innerHTML.length>200", 60)
        time.sleep(1.0)
        snap(b, out, "11_dash", tag)
        # 11) 데이터 정리 탭 + 안내 창(?)
        b.js("[...document.querySelectorAll('.tab')].find(e=>e.dataset.view==='exp').click()")
        time.sleep(1.5)
        snap(b, out, "12_export_tab", tag)
        b.js("[...document.querySelectorAll('.tab')].find(e=>e.dataset.view==='list').click()")
        time.sleep(0.6)
        b.key("?")
        time.sleep(0.8)
        snap(b, out, "13_tour", tag)
        b.js("document.querySelector('#tour-x').click()")
        time.sleep(0.4)
        # 단축키 표가 도움말과 같은 낱말인지(화면 쪽) — 표는 keys.js 에만 있다
        nkeys = ev(b, "(function(){ try { return (UI.KEYS || []).length } catch (e) { return -1 } })()")
        L.chk("화면에서도 단축키 표를 읽을 수 있다(UI.KEYS)", nkeys == -1 or nkeys >= 20, nkeys)
        errs = b.js("return (window.__errs || []).slice()")
        L.chk("시나리오 전체에서 콘솔 오류 0", not errs, errs)
        out["_errs"] = errs
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)

    # ⑤ 옛 서버(파이썬만 옛 판) + 새 화면 = 가드
    L.sync(SB_OLD, old=True)
    L.reset_status(SB_OLD)
    port2 = L.free_port(port + 1)
    p2 = L.start(port=port2, sb=SB_OLD)
    b2 = None
    try:
        b2 = L.browser(w=1366, h=768, base="http://127.0.0.1:%d" % port2)
        b2.js(HOOK)
        b2.open_photo(FRUIT, STEM)
        time.sleep(0.8)
        st = json.loads(ev(b2, "(function(){" + STATE + "})()"))
        out["90_oldserver"] = {k: st[k] for k in ("stem", "todo", "cnts", "view")}
        os.makedirs(os.path.join(L.SHOTS, tag), exist_ok=True)
        b2.shot(os.path.join(L.SHOTS, tag, "90_oldserver.png"))
        L.chk("옛 서버: 사진이 열린다", bool(st["stem"]), st["stem"])
        L.chk("옛 서버: 콘솔 오류 0", not st["errs"], st["errs"])
    finally:
        if b2 is not None:
            try:
                b2.close()
            except Exception:
                pass
        L.stop(p2)

    path = os.path.join(L.OUT_DIR, "b3_struct3_%s.json" % tag)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n상태 기록: %s\n스크린샷: %s" % (path, os.path.join(L.SHOTS, tag)))
    return L.summary("b3_struct3(%s)" % tag)


def diff(a_path, b_path):
    a = json.load(open(a_path, encoding="utf-8"))
    b = json.load(open(b_path, encoding="utf-8"))
    keys = sorted(set(a) | set(b))
    bad = 0
    for k in keys:
        if k.startswith("_"):
            continue
        va, vb = a.get(k), b.get(k)
        if va == vb:
            print("  같음  %s" % k)
            continue
        fa, fb = va or {}, vb or {}
        for f in sorted(set(fa) | set(fb)):
            if fa.get(f) != fb.get(f):
                bad += 1
                print("  다름  %s / %s : %r → %r" % (k, f, fa.get(f), fb.get(f)))
    print("\n다른 칸 %d개 (0 이면 전후 동일)" % bad)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="after")
    ap.add_argument("--diff", nargs=2)
    a = ap.parse_args()
    if a.diff:
        return 1 if diff(a.diff[0], a.diff[1]) else 0
    return 1 if run(a.tag) else 0


if __name__ == "__main__":
    sys.exit(main())
