# -*- coding: utf-8 -*-
"""u10 — **사용법 문서의 그림이 지금 화면인가**: `help.html`·`how_to.html` 이 가리키는 그림 스물둘.
작성: 2026-09-21 (편의·안정성 사이클 · G7)

왜 필요한가
  화면을 고칠 때마다 사용법 그림이 조용히 낡는다. 실제로 2026-09-21 G7 직전에는 스물두 장 중
  **열여섯 장**이 옛 파랑회색 상단 바(`#22303f`)를 그대로 달고 있었고, figcaption 두 곳은
  «⚠️ 이 그림은 재배치 전 화면입니다» 라고 손으로 적혀 있었다. 사람이 눈으로 볼 일이 아니다 —
  그림 한 화소를 읽으면 기계가 말할 수 있다.

보는 것
  ① 두 문서가 가리키는 그림이 **전부 디스크에 있다**(끊긴 그림 0개)
  ② 툴 화면을 찍은 그림의 맨 윗줄이 **지금 상단 바 색**과 같다
  ③ 그 색은 `style.css` 의 `--chrome` **한 곳**에서 온다(그림과 CSS 가 따로 놀지 않는다)
  ④ 두 문서에 «이 그림은 옛 화면» 류의 경고가 **남아 있지 않다**

  낡으면 다시 찍는 법은 `tests/browser/helpfigs.py` 에 있다(어떤 사진·어떤 상태인지가 코드로 적혀 있다).
  ②는 «상단 바가 있는 그림» 에만 묻는다 — 로그인 화면·사용법 화면·자료 예시(ex*.jpg)에는 상단 바가 없다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import sandbox as L                                                        # noqa: E402
from PIL import Image                                                      # noqa: E402

STATIC = os.path.join(L.T, "app", "static")
DOCS = ("help.html", "how_to.html")

# 상단 바가 찍혀 있는 그림 — 이 이름 규칙에 드는 것만 ② 를 묻는다
BAR = re.compile(r"/(ui_[a-z_]+_\d{6}|howto_\d{6}/[2-58]_)")

# «그림이 낡았다» 고 문서가 스스로 적어 둔 말 — 다시 찍었으면 사라져야 한다
STALE_WORDS = ("재배치 전", "재배치 <u>전</u>", "이 그림은 2026-09-18")


def chrome_rgb():
    """`style.css` 의 `--chrome: #1c1c1c;` 를 읽어 (r,g,b) 로."""
    css = io.open(os.path.join(STATIC, "style.css"), encoding="utf-8").read()
    m = re.search(r"--chrome\s*:\s*#([0-9a-fA-F]{6})\s*;", css)
    if not m:
        return None
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def top_row(path):
    """맨 윗줄(y=3)에서 제일 많이 나온 색 — 상단 바가 가로로 꽉 차 있으므로 그것이 바 색이다."""
    im = Image.open(path).convert("RGB")
    w = im.size[0]
    seen = {}
    for x in range(0, w, 7):
        c = im.getpixel((x, 3))
        seen[c] = seen.get(c, 0) + 1
    return max(seen.items(), key=lambda kv: kv[1])


def main():
    want = chrome_rgb()
    L.chk("style.css 에서 --chrome 을 읽었다", want is not None, str(want))
    if want is None:
        return L.summary("u10_help_figs")

    for doc in DOCS:
        p = os.path.join(STATIC, doc)
        if not os.path.exists(p):
            L.warn("%s 가 없다 — 건너뛴다" % doc)
            continue
        s = io.open(p, encoding="utf-8").read()
        refs = sorted(set(re.findall(r'(?:src|href)="(/static/help/[^"]+\.(?:png|jpg))"', s)))
        L.chk("%s 가 그림을 가리킨다" % doc, len(refs) > 0, "%d개" % len(refs))
        for r in refs:
            path = os.path.join(STATIC, r[len("/static/"):])
            ok = os.path.exists(path)
            L.chk("%s → %s 가 있다" % (doc, os.path.basename(r)), ok, r)
            if not ok or not BAR.search(r):
                continue
            c, n = top_row(path)
            L.chk("%s 의 상단 바가 지금 색이다" % os.path.basename(r), c == want,
                  "맨윗줄 최빈 %s (%d칸) · --chrome %s" % (str(c), n, str(want)))
        for w in STALE_WORDS:
            L.chk("%s 에 «%s» 경고가 안 남아 있다" % (doc, w), w not in s)
    return L.summary("u10_help_figs")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
