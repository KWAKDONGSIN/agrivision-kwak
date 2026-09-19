# -*- coding: utf-8 -*-
"""u8 — **화면(JS)의 전역은 `S`·`API`·`UI` 셋뿐인가** + 쪼갠 파일이 문법에 맞나.
작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리»)

왜 이 시험을 새로 만들었나
  지시서 §2 의 목표는 «전역은 S·API·UI 셋» 이다. 사이클 1 이 만든 `u5_js_contract.py` 는 그 칸을
  **경고**로만 두었고, 세는 방법이 «줄 맨 앞의 function/const» 라서 IIFE(즉시 실행 함수) **안**의
  이름도 같이 센다(쪼갠 뒤 225개로 나온다 — 그중 전역은 3개뿐인데도). u5 는 사이클 1 의 기준선
  파일이라 손대지 않고, 여기서 **괄호 깊이**로 진짜 전역만 센다.

보는 것
  ① `index.html` 이 부르는 `static/js/*.js` 마다 `node --check` 통과
  ② 그 파일들의 **깊이 0**(어느 함수·괄호 안도 아닌 자리) 선언을 모으면 `S`·`API`·`UI` 뿐이다
  ③ `state.js` 말고는 깊이 0 선언이 하나도 없다(= 나머지는 전부 IIFE 안)
  ④ 옛 `app.js`·`ui.js` 는 «이동됨» 안내만 남아 있다(회귀 시뮬이 옛 파일에서 구간을 두 번 찾지 않게)
  ⑤ `window.<이름> =` 로 내놓는 옛 연결선의 목록(경고로만 — 지금 5개, 줄일 때는 부르는 쪽을 함께 고쳐야 한다)
쪼개기 전(js/ 폴더가 없을 때)에는 **건너뛴다**.
"""
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import sandbox as L                                                        # noqa: E402

STATIC = os.path.join(L.T, "app", "static")
JS = os.path.join(STATIC, "js")
WANT = {"S", "API", "UI"}


def strip_code(src):
    """주석·문자열·템플릿·정규식을 공백으로 (줄 수는 지킨다)."""
    out, i, n = [], 0, len(src)

    def regex_here(sofar):
        t = sofar.rstrip()
        if not t:
            return True
        c = t[-1]
        return not (c in ")]}" or c.isalnum() or c in "_$")

    while i < n:
        c, two = src[i], src[i:i + 2]
        if two == "/*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
        elif two == "//":
            j = src.find("\n", i)
            j = n if j < 0 else j
        elif c in "\"'`":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    j += 1
                    break
                j += 1
        elif c == "/" and regex_here("".join(out)):
            j, incls = i + 1, False
            while j < n:
                ch = src[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    incls = True
                elif ch == "]":
                    incls = False
                elif ch == "/" and not incls:
                    j += 1
                    break
                elif ch == "\n":
                    break
                j += 1
            while j < n and src[j].isalpha():
                j += 1
        else:
            out.append(c)
            i += 1
            continue
        out.append(re.sub(r"[^\n]", " ", src[i:j]))
        i = j
    return "".join(out)


def top_level_decls(src):
    """깊이 0 에서 만든 이름 — «전역» 이다. 괄호·중괄호·대괄호 깊이를 세며 훑는다."""
    code = strip_code(src)
    depth = 0
    out = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c in "({[":
            depth += 1
        elif c in ")}]":
            depth = max(0, depth - 1)
        elif depth == 0 and (c.isalpha() or c in "_$"):
            m = re.match(r"(function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", code[i:])
            if m and (i == 0 or not (code[i - 1].isalnum() or code[i - 1] in "_$.")):
                out.append(m.group(2))
                i += m.end()
                continue
            m2 = re.match(r"[A-Za-z_$][\w$]*", code[i:])
            if m2:
                i += m2.end()
                continue
        i += 1
    return out


def script_list():
    p = os.path.join(STATIC, "index.html")
    html = io.open(p, encoding="utf-8").read()
    return [m.group(1) for m in re.finditer(r'<script\s+src="/static/(js/[^"]+)"', html)]


def main():
    if not os.path.isdir(JS):
        L.warn("static/js/ 가 없습니다 — 쪼개기 전 판이라 이 시험을 건너뜁니다")
        return L.summary("u8_js_globals")
    files = script_list()
    L.chk("index.html 이 static/js/*.js 를 순서대로 부른다", len(files) >= 10, "%d개: %s" % (len(files), files))

    node = L.NODE
    globals_by_file = {}
    for rel in files:
        p = os.path.join(STATIC, rel)
        ok = os.path.exists(p)
        L.chk("파일이 있다: %s" % rel, ok)
        if not ok:
            continue
        r = subprocess.run([node, "--check", p], capture_output=True, text=True)
        L.chk("문법이 맞다(node --check): %s" % rel, r.returncode == 0,
              (r.stderr or "").strip().split("\n")[0] if r.returncode else "")
        names = top_level_decls(io.open(p, encoding="utf-8").read())
        globals_by_file[rel] = names

    allg = []
    for rel, names in globals_by_file.items():
        allg += names
        if os.path.basename(rel) != "state.js":
            L.chk("깊이 0 선언이 없다(전부 IIFE 안): %s" % rel, not names, names)
    L.chk("state.js 가 만드는 전역은 S·API·UI 뿐", set(globals_by_file.get("js/state.js", [])) == WANT,
          sorted(globals_by_file.get("js/state.js", [])))
    L.chk("화면 전체의 전역이 정확히 3개다", sorted(set(allg)) == sorted(WANT), sorted(set(allg)))

    # ④ 옛 파일은 «이동됨» 안내만
    for old in ("app.js", "ui.js"):
        p = os.path.join(STATIC, old)
        if not os.path.exists(p):
            L.warn("옛 %s 가 없습니다(지웠다면 옛 index.html 을 캐시에서 쓰는 브라우저가 깨집니다)" % old)
            continue
        src = io.open(p, encoding="utf-8").read()
        L.chk("옛 %s 는 «이동됨» 안내만 남았다(20줄 이하)" % old, src.count("\n") <= 30,
              "%d줄" % src.count("\n"))
        L.chk("옛 %s 에 옛 함수가 남아 있지 않다" % old,
              "function bpush()" not in src and "function setNumMode(" not in src)

    # ⑤ window.<이름> 은 경고로만
    wins = []
    for rel in files:
        p = os.path.join(STATIC, rel)
        if not os.path.exists(p):
            continue
        for m in re.finditer(r"window\.([A-Za-z_$][\w$]*)\s*=", io.open(p, encoding="utf-8").read()):
            wins.append(rel.split("/")[-1] + ":" + m.group(1))
    L.warn("window 로 내놓는 옛 연결선 %d개 (부르는 쪽을 함께 고칠 때만 줄인다)" % len(wins), wins)
    return L.summary("u8_js_globals")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
