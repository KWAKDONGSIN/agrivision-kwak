# -*- coding: utf-8 -*-
"""단위 ② `app/maskio.py` — 마스크 읽기·쓰기 왕복. 작성: 2026-09-19

과일마다 마스크 형식이 다르다(사과 = 0..84 라벨 · 블루베리 = RGB 3채널 · 포도·복숭아 = 0/255).
«0보다 크면 전경» 규칙과 «저장은 늘 L 모드 0/255» 규칙을 실제 함수로 확인한다. 서버를 띄우지 않는다.
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "app"))
import sandbox as L                                   # noqa: E402  tests/lib/sandbox.py
import maskio as M                                    # noqa: E402  app/maskio.py

WORK = os.path.join(L.SB_ROOT, "unit_maskio")


def main():
    os.makedirs(WORK, exist_ok=True)
    # ── ① 사과꼴: L 모드 라벨 마스크(0,1,2,...,84)
    lab = np.zeros((6, 6), np.uint8)
    lab[0, 0] = 1
    lab[1, 1] = 84
    p = os.path.join(WORK, "apple_like.png")
    Image.fromarray(lab, mode="L").save(p)
    b = M.load_mask_bool(p)
    L.chk("단위2-1 라벨 마스크(1·84)는 «0보다 크면 전경» 으로 이진화된다",
          b.dtype == bool and int(b.sum()) == 2, "전경 %d화소" % int(b.sum()))
    raw = M.load_mask_raw(p)
    L.chk("단위2-2 load_mask_raw 는 값을 그대로 지킨다(1·84)",
          sorted(np.unique(raw).tolist()) == [0, 1, 84], np.unique(raw).tolist())

    # ── ② 블루베리꼴: RGB 3채널 0/255
    rgb = np.zeros((6, 6, 3), np.uint8)
    rgb[2, 2] = (0, 255, 0)
    p2 = os.path.join(WORK, "blueberry_like.png")
    Image.fromarray(rgb, mode="RGB").save(p2)
    L.chk("단위2-3 RGB 마스크는 채널 최댓값으로 합쳐 전경 1화소",
          int(M.load_mask_bool(p2).sum()) == 1)

    # ── ③ 왕복: bool → PNG → bool
    src = np.zeros((7, 5), bool)
    src[0, 0] = src[6, 4] = src[3, 2] = True
    p3 = os.path.join(WORK, "roundtrip.png")
    M.save_mask_atomic(p3, src)
    back = M.load_mask_bool(p3)
    L.chk("단위2-4 저장→읽기 왕복이 화소 단위로 같다", bool((back == src).all()),
          "다른 화소 %d개" % int((back != src).sum()))
    with Image.open(p3) as im:
        mode, arr = im.mode, np.array(im)
    L.chk("단위2-5 저장은 늘 L 모드 0/255",
          mode == "L" and sorted(np.unique(arr).tolist()) == [0, 255], (mode, np.unique(arr).tolist()))
    L.chk("단위2-6 임시파일(.tmp*)을 남기지 않는다",
          not [n for n in os.listdir(WORK) if ".tmp" in n], os.listdir(WORK))

    # ── ④ 크기·모양 유지
    L.chk("단위2-7 세로·가로 모양이 바뀌지 않는다(7x5)", back.shape == (7, 5), back.shape)

    # ── ⑤ bool_to_png_bytes / raw_to_png_bytes
    import io
    with Image.open(io.BytesIO(M.bool_to_png_bytes(src))) as im:
        L.chk("단위2-8 bool_to_png_bytes 도 L 0/255", im.mode == "L"
              and sorted(np.unique(np.array(im)).tolist()) == [0, 255])
    with Image.open(io.BytesIO(M.raw_to_png_bytes(lab))) as im:
        L.chk("단위2-9 raw_to_png_bytes 는 값 그대로(1·84)",
              sorted(np.unique(np.array(im)).tolist()) == [0, 1, 84])

    rep = M.mask_value_report(p)
    L.chk("단위2-10 mask_value_report 가 모드·고유값을 알려 준다",
          rep["mode"] == "L" and rep["n_uniques"] == 3, rep)
    return L.summary("unit/u2_maskio")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
