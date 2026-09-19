# -*- coding: utf-8 -*-
"""단위 ③ `app/instances.py` — 열매 **번호**(uint16 PNG) 왕복과 개수 규칙. 작성: 2026-09-19

번호본은 16비트 PNG 다. 8비트로 잘리면 «번호 256» 이 «0(배경)» 이 되어 열매가 조용히 사라진다.
그래서 경계값 1·255·256·257·32768·65535 를 **왕복**시켜 본다
(0919 Codex 최종점검이 «PNG 해독기를 검증하라» 고 한 목록 중 번호 왕복 부분).
서버를 띄우지 않는다.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "app"))
import sandbox as L                                   # noqa: E402  tests/lib/sandbox.py
import instances as IN                                # noqa: E402  app/instances.py
import boxes as BX                                    # noqa: E402  app/boxes.py

WORK = os.path.join(L.SB_ROOT, "unit_inst")
EDGE = [1, 255, 256, 257, 32768, 65535]


def main():
    os.makedirs(WORK, exist_ok=True)
    # ── ① 경계 번호 왕복
    arr = np.zeros((4, len(EDGE)), np.uint32)
    for i, v in enumerate(EDGE):
        arr[1, i] = v
    p = os.path.join(WORK, "edge.png")
    IN.write_u16_atomic(p, arr)
    back = IN.read_u16(p)
    L.chk("단위3-1 번호 1·255·256·257·32768·65535 가 왕복해도 그대로",
          bool((back == arr).all()), "다른 화소 %d개 · 읽은 값 %s"
          % (int((back != arr).sum()), sorted(set(back.ravel().tolist()))))
    L.chk("단위3-2 읽은 배열은 uint32(8비트로 잘리지 않는다)", back.dtype == np.uint32, back.dtype)
    L.chk("단위3-3 모양이 유지된다", back.shape == arr.shape, back.shape)
    L.chk("단위3-4 임시파일(.tmp*)을 남기지 않는다",
          not [n for n in os.listdir(WORK) if ".tmp" in n], os.listdir(WORK))

    # ── ② ids_of = 열매 개수
    L.chk("단위3-5 ids_of 는 0(배경)을 빼고 번호만 센다",
          sorted(IN.ids_of(back).tolist()) == sorted(EDGE), IN.ids_of(back).tolist())
    L.chk("단위3-6 번호가 하나도 없으면 개수 0",
          IN.ids_of(np.zeros((3, 3), np.uint32)).size == 0)

    # ── ③ png_u16_bytes 도 같은 값
    import io
    from PIL import Image
    with Image.open(io.BytesIO(IN.png_u16_bytes(arr))) as im:
        got = np.array(im).astype(np.uint32)
    L.chk("단위3-7 png_u16_bytes 도 같은 값을 낸다", bool((got == arr).all()))

    # ── ④ 번호 → 상자: 번호 개수와 상자 개수가 맞나(4화소 미만은 빠진다)
    lab = np.zeros((10, 10), np.uint32)
    lab[0:2, 0:2] = 7          # 4화소 → 남는다
    lab[5:7, 5:7] = 300        # 4화소 → 남는다 (8비트로 잘리면 44 가 되어 티가 안 난다)
    lab[9, 9] = 9              # 1화소 → 빠진다
    b = BX.boxes_of(lab)
    L.chk("단위3-8 4화소 미만 번호는 상자를 만들지 않는다(번호 3개 → 상자 2개)",
          len(b) == 2, [x["xyxy"] for x in b])
    L.chk("단위3-9 상자 id 는 1부터 다시 붙는다", [x["id"] for x in b] == [1, 2])

    # ── ⑤ 상수·이름표가 코드에 있다(문서와 어긋나지 않게)
    L.chk("단위3-10 초벌 출처 이름표가 코드에 있다(SEED_SOURCE·KIND_SOURCE)",
          isinstance(IN.SEED_SOURCE, dict) and isinstance(IN.KIND_SOURCE, dict),
          {"SEED_SOURCE": IN.SEED_SOURCE, "KIND_SOURCE": IN.KIND_SOURCE})
    return L.summary("unit/u3_instances_u16")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
