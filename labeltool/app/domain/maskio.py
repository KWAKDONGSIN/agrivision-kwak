# -*- coding: utf-8 -*-
"""마스크 PNG 입출력 — 이진(0/255)본과 번호(uint16)본의 **파일 형식 한 곳**.

구조 사이클 2(2026-09-20): `instances.py` 의 uint16 읽기·쓰기(read_u16·png_u16_bytes·
write_u16_atomic·ids_of)를 여기로 모았다 — 같은 «파일 형식» 일이라서다.
`app/maskio.py` 가 이 모듈을 그대로 다시 내보내므로 옛 import 는 그대로 돈다.
(원래 머리말)
마스크 PNG 입출력 공통 모듈 (작업자 A)

데이터셋 마스크는 과일마다 형식이 다르다 — 실측(2026-09-16):
  apple     : L 모드, 값 0..84 (인스턴스 라벨 마스크!)  -> 0보다 크면 전경
  blueberry : RGB 3채널, 값 0/255
  grape     : L 모드, 값 0/255
  peach     : L 모드, 값 0/255
따라서 "0/255 인지 0/1 인지"를 가리지 않고 **0보다 크면 전경**으로 이진화한다.
내부 표현은 bool(numpy), 저장은 항상 L 모드 0/255 PNG.
"""

from __future__ import annotations
from typing import Any
import io
import os
import threading

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def load_mask_bool(path: Any) -> Any:
    """어떤 형식이든 읽어서 bool 2차원 배열로."""
    with Image.open(path) as im:
        if im.mode not in ("L", "I;16", "I", "1"):
            im = im.convert("L")
        else:
            im = im.copy()
        a = np.array(im)
    if a.ndim == 3:
        a = a.max(axis=2)
    return a > 0


def load_mask_raw(path: Any) -> Any:
    """이진화하지 않고 **원본 값 그대로** 2차원 uint8 배열로 읽는다.
    사과처럼 인스턴스 라벨(1,2,3,... 이 알 하나하나)인 마스크를 값별로 색칠하려고 쓴다.
    RGB 마스크는 채널 최댓값으로 합친다."""
    with Image.open(path) as im:
        if im.mode not in ("L", "I;16", "I", "1", "P"):
            im = im.convert("L")
        else:
            im = im.copy()
        a = np.array(im)
    if a.ndim == 3:
        a = a.max(axis=2)
    if a.dtype != np.uint8:
        a = np.clip(a, 0, 255).astype(np.uint8)
    return a


def raw_to_png_bytes(arr: Any) -> bytes:
    """uint8 2차원 배열을 값 그대로 L 모드 PNG 바이트로."""
    import io as _io
    buf = _io.BytesIO()
    Image.fromarray(np.asarray(arr).astype(np.uint8), mode="L").save(
        buf, format="PNG", optimize=False, compress_level=1)
    return buf.getvalue()


def bool_to_png_bytes(arr: Any) -> bytes:
    """bool 배열 -> 0/255 L 모드 PNG 바이트."""
    a = (np.asarray(arr).astype(np.uint8)) * 255
    im = Image.fromarray(a, mode="L")
    import io
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=False, compress_level=1)
    return buf.getvalue()


def save_mask_atomic(path: Any, arr: Any) -> str:
    """0/255 PNG 로 원자적 저장(임시파일 -> os.replace)."""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
    a = (np.asarray(arr).astype(np.uint8)) * 255
    Image.fromarray(a, mode="L").save(tmp, format="PNG")
    os.replace(tmp, path)
    return path


def mask_value_report(path: Any) -> Any:
    """진단용: 이 마스크 파일의 모드·고유값."""
    with Image.open(path) as im:
        mode = im.mode
        a = np.array(im)
    u = np.unique(a)
    return {"mode": mode, "shape": list(a.shape), "uniques": u[:10].tolist(), "n_uniques": int(u.size)}

# ── 열매 번호(uint16) 본 — 0917 검출 팀 지시서 §3-3 (구조 2 에서 instances.py 에서 옮겨 왔다)


def read_u16(path: Any) -> Any:
    """PNG를 읽어 원래 정수 라벨 번호를 유지한 배열로 돌려준다."""
    with Image.open(path) as im:
        a = np.array(im)
    if a.ndim == 3:                      # RGB 저장본이면 첫 채널
        a = a[:, :, 0]
    return a.astype(np.uint32)


def png_u16_bytes(arr: Any) -> bytes:
    """정수 라벨 배열을 16비트 PNG 바이트로 인코딩한다."""
    im = Image.fromarray(arr.astype("<u2"), mode="I;16")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def write_u16_atomic(path: Any, arr: Any) -> str:
    """번호를 잃지 않게 uint16 PNG 로 원자적 저장(임시파일 → os.replace)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
    with open(tmp, "wb") as f:
        f.write(png_u16_bytes(arr))
    os.replace(tmp, path)
    return path


def ids_of(arr: Any) -> Any:
    """0(배경)을 뺀 번호 목록. 열매 «개수» 는 ids_of(arr).size."""
    v = np.unique(arr)
    return v[v > 0]
