# C16 의심 열매 기준값을 실제 번호 마스크(읽기만)로 재는 스크립트 — paint.js suspects() 와 같은 계산
import os, sys, random
import numpy as np
from skimage.measure import label
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from api import instances as I

def stats(L):
    L = L.astype(np.int64)
    ids, A = np.unique(L[L > 0], return_counts=True)
    diff = np.zeros(L.shape, bool); touch = np.zeros(L.shape, bool)
    for a, b in ((L[:, 1:], L[:, :-1]), (L[1:, :], L[:-1, :])):
        d = a != b; o = d & (a > 0) & (b > 0)
        for sl in ((slice(None), slice(1, None)), (slice(None), slice(None, -1))) if a.shape[1] != L.shape[1] else ((slice(1, None), slice(None)), (slice(None, -1), slice(None))):
            diff[sl] |= d; touch[sl] |= o
    fg = L > 0
    P = np.bincount(L[diff & fg], minlength=L.max() + 1)[ids]
    T = np.bincount(L[touch & fg], minlength=L.max() + 1)[ids]
    comp = label(L, background=0, connectivity=1)
    cid, cn = np.unique(comp[comp > 0], return_counts=True)
    owner = np.zeros(cid.max() + 1, np.int64); owner[comp[fg]] = L[fg]
    extra = {}
    for c, n in zip(cid, cn):
        extra.setdefault(owner[c], []).append(n)
    out = []
    for v, a, p, t in zip(ids, A, P, T):
        ps = sorted(extra[v], reverse=True)
        pieces = sum(1 for n in ps[1:] if n >= max(20, 0.1 * a))
        rnd = min(1.0, 4 * np.pi * a / max(p, 1) ** 2 / (np.pi ** 2 / 8))
        out.append((int(v), int(a), rnd, t / max(p, 1), pieces))
    return out

random.seed(0)
rows = []
for f in ["apple", "blueberry", "grape", "peach"]:
    st = I._stems(f); random.shuffle(st); used = 0
    for s in st:
        arr, kind, _ = I.load_inst(f, s)
        if arr is None: continue
        r = stats(arr)
        if len(r) < 1: continue
        med = float(np.median([x[1] for x in r]))
        for v, a, rnd, tc, pc in r:
            rows.append((f, s, kind, v, a, a / med, len(r), rnd, tc, pc))
        used += 1
        if used >= 40: break
with open(os.path.join(HERE, "..", "_out", "c16", "calib.tsv"), "w") as fo:
    fo.write("fruit\tstem\tkind\tid\tarea\tarea_rel\tn\tround\ttouch\tpieces\n")
    for r in rows: fo.write("\t".join(str(x) for x in r) + "\n")
print(len(rows))
