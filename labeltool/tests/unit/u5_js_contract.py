# -*- coding: utf-8 -*-
"""u5 — **화면 쪽(JS) 기준선**: 구조 사이클 3 이 `app.js` 를 쪼개도 시뮬이 살아남는 조건.
작성: 2026-09-19 (구조 정리 사이클 1 **2차 검수** §2)

왜 필요한가
  `sim/boxsim.js` 와 `sim/modesim.js` 는 «손으로 옮겨 적은 사본» 이 아니라 `app.js` 의 글자를
  **그대로 떼어 내** 돌린다. 떼어 내는 방법이 «이 문구부터 저 문구까지» 라서, 구조 사이클 3 이
  `app.js` 를 `static/js/*.js` 10파일로 쪼개면 그 문구를 못 찾고 **시뮬 81항목이 통째로 죽는다**
  (`throw new Error("app.js 에서 구간을 못 찾음")`). 기준선 ④(정적 파일 sha256)는 그때
  «달라졌다» 고만 하고 경고로 끝난다 — 그래서 **무엇을 지켜야 하는지** 를 여기 못박는다.

이 시험이 보는 것 (코드는 한 글자도 고치지 않는다 — 읽기만)
  ① 구간 표식 8개가 **JS 어딘가에 정확히 한 번** 나온다 (boxsim 의 `cut()` 이 찾는 문구)
  ② 그 표식들이 **한 파일 안에서 순서대로** 놓여 있다 (`cut()` 이 `indexOf` 두 개를 쓴다)
  ③ modesim 이 `fn()` 으로 떼어 내는 최상위 함수 3개가 **열 0번째 칸에서 닫힌다**(`\n}\n`)
  ④ 시뮬이 이름으로 꺼내 쓰는 함수·상수 25개가 살아 있다 («함수 이름은 유지한다» — 지시서 §2)
  ⑤ 전역은 `S`·`API`·`UI` 셋만 (지시서 §2 마지막 줄) — 지금은 **경고**로만 센다.
     지금 판(app.js 한 파일)은 최상위 `let`/`const`/`function` 이 수백 개라 규칙 밖이다.
     구조 3 이 끝나면 이 칸을 «실패» 로 올린다(그 전에는 몇 개인지 숫자만 남긴다).

쪼갠 뒤에 어떻게 통과시키나 (구조 3 이 할 일 — 셋 중 하나)
  (가) `tests/lib/paths.js` 의 `APP_JS` 대신 `appSources()` 가 돌려주는 파일들을 **이어 붙여**
       boxsim/modesim 에 넘긴다(시험 두 줄만 고친다. 이 시험이 그 파일 목록을 쓴다).
  (나) 쪼갠 파일 중 **상자 담당 한 파일**(`static/js/boxes.js`)에 ① 의 표식 8개를 다 모아 둔다.
  (다) 표식 문구를 바꿀 셈이면 이 파일의 `MARKERS` 를 같이 고치고 **왜** 바꿨는지 여기 적는다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import sandbox as L                                                        # noqa: E402

STATIC = os.path.join(L.T, "app", "static")

# ① boxsim.js 의 cut() 이 찾는 문구 — (시작, 끝) 네 쌍 = 표식 8개
CUTS = [("function bpush()", "function boxInfo(extra)"),
        ("function boxInfo(extra)", "function drawBoxes()"),
        ("const norm = (a, b, c, d)", "function delSelBox()"),
        ("async function saveBoxes()", "async function seedBoxes()")]
# ③ modesim.js 의 fn()/stmt() 가 찾는 것
FN_HEADS = ["function setTool(t) {", "function setNumMode(on, silent) {", "function numKey(e) {"]
STMT_HEADS = ['$("#box-mode").onchange = () => {', 'window.addEventListener("keydown", (e) => {']
# ④ 시뮬이 이름으로 꺼내 쓰는 것
NAMES = ["bpush", "boxUndo", "boxInfo", "hitBox", "hitBoxesAt", "hitHandle", "bHandleR", "bcommit",
         "boxMouseDown", "boxMouseMove", "boxMouseUp", "saveBoxes", "PICKTOL",
         "setTool", "setNumMode", "numKey", "delSelBox", "fitView", "doAction", "applyPolygon",
         "numUndo", "numRedo", "saveInstances", "seedBoxes", "drawBoxes"]


def js_files():
    """시뮬이 볼 수 있는 화면 소스 — 지금은 `app.js`·`ui.js`, 쪼갠 뒤에는 `static/js/*.js` 도."""
    out = []
    for n in ("app.js", "ui.js"):
        p = os.path.join(STATIC, n)
        if os.path.exists(p):
            out.append(p)
    jsd = os.path.join(STATIC, "js")
    if os.path.isdir(jsd):
        out += [os.path.join(jsd, n) for n in sorted(os.listdir(jsd)) if n.endswith(".js")]
    return out


def main():
    files = js_files()
    L.chk("화면 소스 파일을 찾았다", bool(files),
          ", ".join(os.path.relpath(p, L.T) for p in files))
    src = {p: io.open(p, encoding="utf-8").read() for p in files}

    # ① 표식이 정확히 한 번 나온다
    marks = []
    for a, b in CUTS:
        for m in (a, b):
            if m not in marks:
                marks.append(m)
    where = {}
    for m in marks:
        hits = [(p, src[p].count(m)) for p in files if m in src[p]]
        n = sum(c for _, c in hits)
        where[m] = hits
        L.chk("구간 표식이 딱 한 번 있다: %s" % m, n == 1,
              "찾은 곳 %s" % ([(os.path.basename(p), c) for p, c in hits] or "없음"))

    # ② 한 파일 안에서 순서대로
    for a, b in CUTS:
        fa = [p for p, _ in where.get(a, [])]
        fb = [p for p, _ in where.get(b, [])]
        same = bool(fa) and fa == fb
        order = same and src[fa[0]].index(a) < src[fa[0]].index(b)
        L.chk("«%s» → «%s» 가 한 파일 안에서 순서대로" % (a[:28], b[:28]), bool(order),
              os.path.basename(fa[0]) if fa else "없음")

    # ③ modesim 이 떼어 내는 최상위 함수가 «\n}\n» 로 닫힌다
    for head in FN_HEADS:
        good = False
        for p in files:
            i = src[p].find(head)
            if i >= 0:
                good = src[p].find("\n}\n", i) > i
                break
        L.chk("최상위 함수가 열 0에서 닫힌다(modesim fn()): %s" % head, good)
    for head in STMT_HEADS:
        L.chk("최상위 대입문이 그대로 있다(modesim stmt()): %s" % head[:40],
              any(head in src[p] for p in files))

    # ④ 이름이 살아 있다
    for name in NAMES:
        pat = re.compile(r"\b(?:function\s+|const\s+|let\s+|var\s+)%s\b" % re.escape(name))
        L.chk("이름이 살아 있다: %s" % name, any(pat.search(src[p]) for p in files))

    # ⑤ 전역 개수 (지금은 세기만 — 구조 3 이 끝나면 «S·API·UI 셋» 으로 올린다)
    top = set()
    for p in files:
        for m in re.finditer(r"^(?:function|const|let|var)\s+([A-Za-z_$][\w$]*)", src[p], re.M):
            top.add(m.group(1))
    L.warn("최상위 이름 %d개 (지시서 §2 목표는 S·API·UI 셋 — 구조 3 뒤에 «실패» 로 올린다)" % len(top),
           "S·API·UI 있나: %s" % [n for n in ("S", "API", "UI") if n in top])
    return L.summary("u5_js_contract")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
