# -*- coding: utf-8 -*-
"""u7 — **단축키가 한 곳인가**: `static/js/keys.js` 의 표 ↔ 도움말(help.html «단축키 한 장») ↔ 손잡이 코드.
작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리»)

왜 필요한가
  단축키의 «진실» 이 세 군데 있었다 — ① 손잡이 코드(app.js 의 keydown switch) ② 도움말 표
  (help.html) ③ 화면 단추의 풍선말. 하나를 고치면 나머지는 조용히 낡는다(실제로 그래 왔다:
  help.html 머리에 «그 뒤 사이클 2~4 가 단축키의 뜻을 바꿨다» 고 손으로 적혀 있다).
  구조 사이클 3 은 ①을 `keys.js` 한 파일로 모으고 그 안에 **표**(`const KEYS = [...]`)를 두었다.
  이 시험은 그 표가 도움말과 코드 **둘 다**와 맞는지 본다. 어긋나면 사람이 아니라 시험이 먼저 안다.

보는 것
  ① 표의 키가 도움말 «단축키 한 장» 절에 `<kbd>` 로 들어 있다
  ② 도움말 «단축키 한 장» 절의 `<kbd>` 키가 표에 다 들어 있다(설명용 낱말 몇 개는 빼고)
  ③ 표가 «어느 파일에 손잡이가 있다»(at) 고 적은 그 파일에 «있어야 하는 글자»(src)가 정말 있다
  ④ 표에 같은 키가 두 번 나오지 않는다
  ⑤ **keys.js 가 진짜로 받는 키가 표에 빠짐없이 있다** (2026-09-21 편의 U7 에서 더함)
쪼개기 전(js/ 폴더가 없을 때)에는 **건너뛴다**(그때는 표가 없는 것이 정상이다).

⑤ 를 왜 뒤늦게 더했나 — ①②③ 은 전부 «표에 적힌 것» 에서 출발한다. 그래서 표에 **안 적고**
  손잡이만 더하면(`case "w":` 한 줄) 세 검사 모두 조용히 통과했다. F1 겹창을 «표 한 장» 으로
  내놓는 이상, 그 표에 없는 키가 코드에 살아 있으면 표가 거짓말을 하는 것이다. 그래서 반대
  방향 — 코드의 `case "…"` 와 Ctrl 갈래에서 키를 긁어 **표에 다 있는지** 를 본다.
"""
import io
import subprocess
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import sandbox as L                                                        # noqa: E402

STATIC = os.path.join(L.T, "app", "static")
JS = os.path.join(STATIC, "js")

# 도움말 표에 «키가 아닌 것» 으로 들어 있는 kbd 낱말 — 조합키의 조각과 화면 단추 기호
NOT_KEYS = {"Ctrl", "Alt", "Shift", "Meta", "Cmd", "▸", "◂", "◀", "▶"}

# 손잡이 코드가 쓰는 글자 → 표가 쓰는 이름 (표에는 사람이 읽는 짧은 이름을 적는다)
CODE_ALIAS = {"Escape": "Esc", "Delete": "Del", "Backspace": "Del"}


def keys_table(src):
    """keys.js 의 `const KEYS = [ {…}, … ]` 를 읽는다(파이썬 쪽에서 JS 를 돌리지 않는다)."""
    m = re.search(r"const KEYS = \[(.*?)\n\];", src, re.S)
    if not m:
        return []
    out = []
    for row in re.finditer(r"\{\s*key:\s*\"((?:[^\"\\]|\\.)*)\",\s*ko:\s*\"((?:[^\"\\]|\\.)*)\","
                           r"\s*at:\s*\"([^\"]+)\",\s*\n?\s*src:\s*'((?:[^'\\]|\\.)*)'", m.group(1)):
        out.append(dict(key=row.group(1), ko=row.group(2), at=row.group(3), src=row.group(4)))
    return out


def handled_keys(src):
    """keys.js 의 손잡이가 **정말 받는** 키를 긁는다 — switch 의 `case "…"` · Ctrl 갈래 · 나머지.
    표가 쓰는 이름으로 바꿔서 돌려준다(한 글자는 대문자 · Escape→Esc · Delete/Backspace→Del)."""
    def name(k):
        return CODE_ALIAS.get(k, k.upper() if len(k) == 1 else k)
    # ⚠ 표(KEYS) 자체를 긁으면 안 된다 — `src:` 칸에 손잡이 글자가 그대로 적혀 있어서
    #   «코드가 받는 키» 가 아니라 «표가 적은 키» 를 되읽게 된다(첫 판이 여기서 헛돌았다).
    t = re.search(r"const KEYS = \[.*?\n\];", src, re.S)
    if t:
        src = src[t.end():]
    out = set(name(k) for k in re.findall(r'case "([^"]+)":', src))
    # Ctrl 갈래는 «Ctrl+무엇» 으로 적힌다 — 그 블록만 따로 떼어 본다
    m = re.search(r"if \(e\.ctrlKey \|\| e\.metaKey\) \{(.*?)\n  \}", src, re.S)
    if m:
        out |= set("Ctrl+" + k.upper() for k in re.findall(r'e\.key === "([A-Za-z])"', m.group(1)))
    rest = (src[:m.start()] + src[m.end():]) if m else src
    out |= set(name(k) for k in re.findall(r'e\.key === "([^"]+)"', rest))    # F1 · Escape …
    if 'e.code === "Space"' in src:
        out.add("Space")
    return out


def help_keys(html):
    """help.html 의 «단축키 한 장» 절에 있는 <kbd> 낱말."""
    m = re.search(r'<h2 id="keys">(.*?)<h2 ', html, re.S)
    if not m:
        return None
    return [k.strip() for k in re.findall(r"<kbd>(.*?)</kbd>", m.group(1))]


def main():
    if not os.path.isdir(JS):
        L.warn("static/js/ 가 없습니다 — 쪼개기 전 판이라 이 시험을 건너뜁니다")
        return L.summary("u7_keys_doc")
    kp = os.path.join(JS, "keys.js")
    L.chk("keys.js 가 있다", os.path.exists(kp), kp)
    if not os.path.exists(kp):
        return L.summary("u7_keys_doc")
    src = io.open(kp, encoding="utf-8").read()
    rows = keys_table(src)
    L.chk("keys.js 에 단축키 표(KEYS)가 있고 20줄 이상이다", len(rows) >= 20, "%d줄" % len(rows))

    # ④ 같은 키가 두 번
    seen = {}
    dup = [r["key"] for r in rows if r["key"] in seen or seen.setdefault(r["key"], 1) is None]
    L.chk("표에 같은 키가 두 번 나오지 않는다", not dup, dup)

    hp = os.path.join(STATIC, "help.html")
    html = io.open(hp, encoding="utf-8").read() if os.path.exists(hp) else ""
    if 'data-key-table' in html and '/static/js/keys.js' in html:
        rendered = subprocess.check_output([L.NODE, "-e", "const el={}; global.document={querySelectorAll:()=>[el]}; require(process.argv[1]); console.log(el.innerHTML)", kp], text=True)
        hk = re.findall(r"<kbd>(.*?)</kbd>", rendered)
    else:
        hk = help_keys(html)
    L.chk("help.html 에 «단축키 한 장» 절이 있다", hk is not None, hp)
    if hk is not None:
        hset = set(hk)
        # ① 표 → 도움말
        for r in rows:
            parts = [p for p in r["key"].split("+")]
            miss = [p for p in parts if p not in hset]
            L.chk("표의 키가 도움말에 있다: %s (%s)" % (r["key"], r["ko"][:18]), not miss,
                  "도움말에 없는 조각 %s" % miss if miss else "")
        # ② 도움말 → 표
        table_tokens = set()
        for r in rows:
            for p in r["key"].split("+"):
                table_tokens.add(p)
        extra = sorted(k for k in hset if k not in table_tokens and k not in NOT_KEYS)
        L.chk("도움말에 있는데 표에 없는 키가 없다", not extra, extra)

    # ③ 표가 가리키는 파일에 그 글자가 정말 있는가
    cache = {}
    for r in rows:
        p = os.path.join(JS, r["at"])
        if r["at"] not in cache:
            cache[r["at"]] = io.open(p, encoding="utf-8").read() if os.path.exists(p) else None
        body = cache[r["at"]]
        L.chk("손잡이가 표가 적은 자리에 있다: %s → %s" % (r["key"], r["at"]),
              bool(body) and r["src"] in body, r["src"])

    # ⑤ 반대 방향 — 코드가 받는 키가 표에 다 있는가 (①②③ 은 전부 표에서 출발한다)
    code = handled_keys(src)
    names = set(r["key"] for r in rows)
    orphan = sorted(k for k in code if k not in names)
    L.chk("keys.js 가 받는 키 %d개가 표에 빠짐없이 있다" % len(code), not orphan,
          ("표에 없는 키 %s" % orphan) if orphan else " ".join(sorted(code)))
    return L.summary("u7_keys_doc")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
