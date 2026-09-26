# C17 경고가 실제 ✨(도우미 /sam) 결과에서 얼마나 뜨는지 재는 스크립트 — 열매 한가운데 클릭(잘못 경고) vs 열매 밖 클릭(경고가 떠야 좋음)
import base64, io, json, os, random, sys, urllib.request
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
T = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(T, "app"))
os.environ.setdefault("LABELTOOL_DATA_ROOT", open(os.path.join(T, "app/logs/last_data_root")).read().strip())
from core.paths import img_path
from api import instances as I
URL = "http://127.0.0.1:5112"
ELONG, ROUND, IMG, LARGE, MINN = 3.5, 0.2, 0.1, 6, 5          # paint.js SAMW·SUS 와 같은 값


def post(body):
    req = urllib.request.Request(URL + "/sam", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def warn(m, others, npx):
    ys, xs = np.nonzero(m); n = len(xs)
    if n < 30: return ""
    cxx, cyy, cxy = xs.var(), ys.var(), ((xs - xs.mean()) * (ys - ys.mean())).mean()
    t, d = (cxx + cyy) / 2, np.sqrt(((cxx - cyy) / 2) ** 2 + cxy ** 2)
    el = np.sqrt((t + d + 1 / 12) / (t - d + 1 / 12))
    p = np.pad(m, 1); edge = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    rnd = min(1.0, 4 * np.pi * n / max(edge.sum(), 1) ** 2 / (np.pi ** 2 / 8))
    w = []
    if el > ELONG: w.append("elong")
    elif rnd < ROUND: w.append("round")
    if n / npx > IMG: w.append("img")
    elif len(others) >= MINN and n / np.sort(others)[len(others) // 2] > LARGE: w.append("large")
    return ",".join(w)


random.seed(1)
res = {"fruit": [], "bg": []}
for f in ["apple", "blueberry", "peach"]:
    st = I._stems(f); random.shuffle(st); used = 0
    for s in st:
        L, kind, _ = I.load_inst(f, s)
        if L is None or (f == "apple" and kind != "gt"): continue   # 사과만 사람 정답, 블루베리·복숭아는 초벌
        ids, cnt = np.unique(L[L > 0], return_counts=True)
        if len(ids) < 3: continue
        img = img_path(f, s)
        for v in random.sample(list(ids), min(5, len(ids))):
            m = L == v
            if m.sum() < 60: continue
            dt = distance_transform_edt(m); y, x = np.unravel_index(dt.argmax(), dt.shape)
            j = post({"img": img, "x": int(x), "y": int(y), "crop": 384})
            if not j.get("cands"): continue
            c = j["cands"][0]; cm = np.array(Image.open(io.BytesIO(base64.b64decode(c["png"])))) > 127
            res["fruit"].append((f, s, int(v), warn(cm, cnt[ids != v], L.size)))
        bgm = distance_transform_edt(L == 0)
        yy, xx = np.nonzero(bgm > 15)
        for k in random.sample(range(len(xx)), min(3, len(xx))):
            j = post({"img": img, "x": int(xx[k]), "y": int(yy[k]), "crop": 384})
            if not j.get("cands"): continue
            c = j["cands"][0]; cm = np.array(Image.open(io.BytesIO(base64.b64decode(c["png"])))) > 127
            res["bg"].append((f, s, int(xx[k]), int(yy[k]), warn(cm, cnt, L.size)))
        used += 1
        if used >= 6: break
os.makedirs(os.path.join(T, "tests/_out/c17"), exist_ok=True)
with open(os.path.join(T, "tests/_out/c17/real_check.json"), "w") as fo:
    json.dump(res, fo, ensure_ascii=False, indent=0)
for k in res:
    for f in ["apple", "blueberry", "peach"]:
        r = [x[-1] for x in res[k] if x[0] == f]
        print(k, f, "경고", sum(1 for w in r if w), "/", len(r), [w for w in r if w])
