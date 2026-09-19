# -*- coding: utf-8 -*-
"""단위 ① `app/boxes.py` 가 이미 가지고 있는 자체 점검(`demo()`)을 그대로 부른다.
작성: 2026-09-19

서버를 띄우지 않는다. 상자 정리 규칙(`clean`) · 번호→상자(`boxes_of`) ·
개수 유도 규칙(`human_count`) 을 **실제 함수**로 확인한다.
원본: `app/boxes.py` 의 `demo()` (runall.sh 는 `$PY app/boxes.py` 로 불렀다).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "app"))
import sandbox as L                                   # noqa: E402  tests/lib/sandbox.py
import boxes as BX                                   # noqa: E402  app/boxes.py


def main():
    try:
        BX.demo()
        L.chk("단위1-1 app/boxes.py demo() — clean·boxes_of·human_count 전부 통과", True)
    except AssertionError as e:
        L.chk("단위1-1 app/boxes.py demo() — clean·boxes_of·human_count 전부 통과", False, e)
    # demo() 가 덮지 않는 칸 몇 개를 더 못박는다(값은 코드에서 읽어 온다 — 매직 넘버를 베끼지 않는다)
    L.chk("단위1-2 상한 상수가 있다(MAX_BOXES·MIN_SIDE)",
          isinstance(BX.MAX_BOXES, int) and isinstance(BX.MIN_SIDE, int),
          "MAX_BOXES=%s MIN_SIDE=%s" % (BX.MAX_BOXES, BX.MIN_SIDE))
    out, dropped, over = BX.clean([], 100, 100)
    L.chk("단위1-3 빈 목록은 빈 목록(«전부 탈락» 과 구별은 서버 쪽 몫)",
          (out, dropped, over) == ([], 0, 0), (out, dropped, over))
    L.chk("단위1-4 개수 어긋남은 개수를 비운다", BX.human_count(3, 4, "ok", "ok")[1] == "conflict")
    L.chk("단위1-5 확정이 없으면 개수도 출처도 없다", BX.human_count(3, 4, None, None) == (None, "", False))
    return L.summary("unit/u1_boxes_selftest")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
