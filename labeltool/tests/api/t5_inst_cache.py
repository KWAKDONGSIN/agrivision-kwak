# -*- coding: utf-8 -*-
# /instances 응답 캐시(ETag/304·메모리) 시험 — 저장·되돌림 뒤에는 반드시 새 번호를 주는지 본다 (C07)
"""2026-09-25 업그레이드 C07 · C19(서버 쪽) 시험.
작성: 2026-09-25

모래상자 tests/_sandbox/c07 · 127.0.0.1:5441 에서만 돈다. 공용 T/data 에는 쓰지 않는다.
"""
import base64
import io
import os
import sys
import time
import urllib.error
import urllib.request

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import sandbox as L                                  # tests/lib/sandbox.py

PORT = 5441
SB = os.path.join(L.TESTS, "_sandbox", "c07")
BASE = "http://127.0.0.1:%d" % PORT
FR = "apple"


def fetch(a, path, etag=None):
    """(상태, 본문, 헤더) — 304 도 예외 없이 돌려준다."""
    h = {"If-None-Match": etag} if etag else {}
    try:
        with a.op.open(urllib.request.Request(BASE + path, headers=h), timeout=300) as f:
            return f.status, f.read(), f.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def ids(body):
    a = np.array(Image.open(io.BytesIO(body)))
    return set(np.unique(a).tolist()) - {0}, a


def main():
    L.sync(sb=SB)
    L.reset_status(sb=SB)
    p = L.start(port=PORT, sb=SB)
    try:
        a = L.Api(base=BASE)
        stem = a.get("/api/list?fruit=%s&page_size=20" % FR)["items"][5]["stem"]
        q = "/instances?fruit=%s&stem=%s&layer=auto" % (FR, stem)

        t0 = time.time(); c1, b1, h1 = fetch(a, q); t_first = time.time() - t0
        e1 = h1.get("ETag")
        L.chk("C07-1 첫 응답 200 + ETag + no-cache + 출처 머리글",
              c1 == 200 and e1 and "no-cache" in (h1.get("Cache-Control") or "")
              and h1.get("X-Instance-Source"), (c1, e1, h1.get("Cache-Control")))
        t0 = time.time(); c2, b2, h2 = fetch(a, q, e1); t_304 = time.time() - t0
        L.chk("C07-2 같은 지문이면 304 · 본문 없음", c2 == 304 and not b2, (c2, len(b2)))
        t0 = time.time(); c3, b3, _ = fetch(a, q); t_mem = time.time() - t0
        L.chk("C07-3 지문 없이 다시 받으면 메모리에서 같은 PNG", c3 == 200 and b3 == b1, (c3, len(b3)))
        _, _, hg = fetch(a, q.replace("layer=auto", "layer=gt"))
        L.chk("C07-4 layer 가 다르면 지문도 다르다", hg.get("ETag") != e1, hg.get("ETag"))

        # 번호 하나를 지워 저장 → 옛 지문으로 물어도 200 + 새 번호
        s0, arr = ids(b1)
        drop = max(s0)
        arr2 = arr.astype(np.uint16).copy(); arr2[arr2 == drop] = 0
        buf = io.BytesIO(); Image.fromarray(arr2).save(buf, "PNG")
        code, r = a.post("/api/save_instances", {"fruit": FR, "stem": stem, "by": "c07시험",
                                                 "png": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()})
        L.chk("C07-5 번호 저장 성공", code == 200 and r.get("ok"), (code, str(r)[:200]))
        c4, b4, h4 = fetch(a, q, e1)
        s4 = ids(b4)[0] if c4 == 200 else set()
        L.chk("C07-6 저장 뒤 옛 지문으로 물으면 200 · 지운 번호가 없다",
              c4 == 200 and h4.get("ETag") != e1 and drop not in s4 and s4 == s0 - {drop},
              (c4, len(s0), len(s4)))
        L.chk("C07-7 저장 뒤 출처는 human_fixed(fixed)", h4.get("X-Instance-Source") == "fixed",
              h4.get("X-Instance-Source"))
        # C19: /api/item 의 file_sig = /instances 지문 → 그림판 미리 받기가 같은 초 저장도 알아챈다
        fs = lambda: a.get("/api/item?fruit=%s&stem=%s" % (FR, stem)).get("file_sig")
        L.chk("C19-1 저장 뒤 /api/item file_sig = 새 ETag(옛 것과 다름)",
              fs() == (h4.get("ETag") or "").strip('"') and fs() != e1.strip('"'), (fs(), h4.get("ETag")))

        code, r = a.post("/api/revert_instances", {"fruit": FR, "stem": stem, "by": "c07시험"})
        c5, b5, h5 = fetch(a, q, h4.get("ETag"))
        L.chk("C07-8 되돌린 뒤 200 · 처음 번호와 같다 · 지문도 처음 것",
              code == 200 and c5 == 200 and ids(b5)[0] == s0 and h5.get("ETag") == e1,
              (code, c5, h5.get("ETag"), e1))
        L.chk("C19-2 되돌린 뒤 file_sig 도 처음 지문", fs() == e1.strip('"'), (fs(), e1))
        print("  시간: 첫 %.0fms · 304 %.0fms · 메모리 %.0fms" % (t_first * 1e3, t_304 * 1e3, t_mem * 1e3))
    finally:
        L.stop(p)
    return L.summary("t5_inst_cache")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
