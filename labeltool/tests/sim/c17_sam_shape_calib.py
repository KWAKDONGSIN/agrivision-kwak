# C17 ✨ 결과 경고 기준값(길쭉함·둥근 정도·사진 대비 넓이)을 실제 번호 마스크(읽기만)로 재는 스크립트 — paint.js samShapeWarn() 과 같은 계산
import os, sys, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from api import instances as I


def shape(m):
    """m: 한 열매의 bool 마스크 → (넓이, 길쭉함 = 긴 축÷짧은 축, 둥근 정도)"""
    ys, xs = np.nonzero(m)
    a = len(xs)
    cxx, cyy, cxy = xs.var(), ys.var(), ((xs - xs.mean()) * (ys - ys.mean())).mean()
    t, d = cxx + cyy, np.sqrt(((cxx - cyy) / 2) ** 2 + cxy ** 2)
    el = np.sqrt((t / 2 + d + 1 / 12) / (t / 2 - d + 1 / 12))
    p = np.pad(m, 1)
    edge = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    rnd = min(1.0, 4 * np.pi * a / max(edge.sum(), 1) ** 2 / (np.pi ** 2 / 8))
    return a, el, rnd


random.seed(0)
rows = []
for f in ["apple", "blueberry", "grape", "peach"]:
    st = I._stems(f); random.shuffle(st); used = 0
    for s in st:
        arr, kind, _ = I.load_inst(f, s)
        if arr is None: continue
        ids = [v for v in np.unique(arr) if v > 0]
        if not ids: continue
        for v in ids:
            m = arr == v
            if m.sum() < 30: continue                 # 너무 작은 번호는 ✨ 결과로 나올 일이 드묾
            a, el, rnd = shape(m)
            rows.append((f, s, kind, int(v), a, a / arr.size, el, rnd))
        used += 1
        if used >= 40: break
os.makedirs(os.path.join(HERE, "..", "_out", "c17"), exist_ok=True)
with open(os.path.join(HERE, "..", "_out", "c17", "calib.tsv"), "w") as fo:
    fo.write("fruit\tstem\tkind\tid\tarea\tarea_img\telong\tround\n")
    for r in rows: fo.write("\t".join(str(x) for x in r) + "\n")
R = np.array([r[4:] for r in rows], float)
F = np.array([r[0] for r in rows])
print("n", len(rows))
for f in ["all", "apple", "blueberry", "grape", "peach"]:
    k = np.ones(len(F), bool) if f == "all" else F == f
    if not k.any(): continue
    e, r, ai = R[k, 2], R[k, 3], R[k, 1]
    print(f, k.sum(), "elong p99/p99.5/max", *np.round(np.percentile(e, [99, 99.5, 100]), 2),
          "| round p1/p0.5", *np.round(np.percentile(r, [1, 0.5]), 3),
          "| area_img p99/p99.9/max", *np.round(np.percentile(ai, [99, 99.9, 100]), 4))
for th in [2.5, 3, 3.5, 4]:
    print("elong>", th, round(float((R[:, 2] > th).mean()) * 100, 2), "%")
for th in [0.2, 0.25, 0.3]:
    print("round<", th, round(float((R[:, 3] < th).mean()) * 100, 2), "%")
for th in [0.05, 0.1, 0.15, 0.25]:
    print("area_img>", th, round(float((R[:, 1] > th).mean()) * 100, 2), "%")
