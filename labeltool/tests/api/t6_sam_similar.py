# C14 도우미 /similar(비슷한 열매 한꺼번에 찾기)와 기존 /sam 이 함께 잘 도는지 보는 시험 — 쓰는 법: python t6_sam_similar.py [도우미주소=http://127.0.0.1:5441]
import base64, io, json, os, sys, time, urllib.error, urllib.request
import numpy as np
from PIL import Image
T = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(T, "app"))
os.environ.setdefault("LABELTOOL_DATA_ROOT", open(os.path.join(T, "app/logs/last_data_root")).read().strip())
from core.paths import img_path
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5441"
fails = 0
def ok(name, cond, info=""):
    global fails
    fails += not cond
    print(("통과 " if cond else "실패 ") + name, info, flush=True)
def post(path, body, timeout=120):
    req = urllib.request.Request(URL + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

# 본보기 = 사람이 준 복숭아 번호 마스크의 한 열매(맞는 답이 있는 사진)
import cv2
stem = "210629-t1-02"
L = cv2.imread(os.path.join(T, "data/peach/instances_gt", stem + ".png"), cv2.IMREAD_UNCHANGED).astype(np.int32)
if L.ndim == 3: L = L[..., 2] + L[..., 1] * 256
ids, cnt = np.unique(L[L > 0], return_counts=True)
v = ids[np.argsort(cnt)[len(cnt) // 2]]
m = L == v; ys, xs = np.nonzero(m); a0, b0, a1, b1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
buf = io.BytesIO(); Image.fromarray((m[b0:b1, a0:a1] * 255).astype(np.uint8)).save(buf, "PNG")
ex = {"x0": int(a0), "y0": int(b0), "png": base64.b64encode(buf.getvalue()).decode()}
img = img_path("peach", stem)

t = time.time(); st, j = post("/similar", {"img": img, "ex": ex}); dt = time.time() - t
ok("/similar 200·ok", st == 200 and j.get("ok"), f"{st} {dt:.1f}s")
cs = j.get("cands", [])
ok("후보가 1개 이상 · 필드", len(cs) >= 1 and all({"x0", "y0", "w", "h", "png", "score", "sim", "feat"} <= set(c) for c in cs), f"{len(cs)}개 {j.get('tiles')}칸")
ok("30초 안", dt < 30, f"{dt:.1f}s")
H, W = L.shape
inside = all(0 <= c["x0"] and 0 <= c["y0"] and c["x0"] + c["w"] <= W and c["y0"] + c["h"] <= H for c in cs)
ok("후보가 사진 안", inside)
def cm(c): return np.array(Image.open(io.BytesIO(base64.b64decode(c["png"])))) > 127
ok("PNG 크기 = w×h", all(cm(c).shape == (c["h"], c["w"]) for c in cs))
exov = max((int((cm(c) & m[c["y0"]:c["y0"] + c["h"], c["x0"]:c["x0"] + c["w"]]).sum()) / max(1, cm(c).sum()) for c in cs), default=0)
ok("본보기 자신은 후보에 없음(겹침 25% 이하)", exov <= 0.25, f"{exov:.2f}")
hit = 0
for c in cs:
    sub = L[c["y0"]:c["y0"] + c["h"], c["x0"]:c["x0"] + c["w"]][cm(c)]
    vv, nn = np.unique(sub, return_counts=True)
    hit += any(a not in (0, v) and n / (cm(c).sum() + (L == a).sum() - n) >= 0.5 for a, n in zip(vv, nn))
ok("후보 절반 이상이 사람 정답 열매와 맞음(IoU≥0.5)", hit >= 0.5 * len(cs) and hit >= 5, f"{hit}/{len(cs)} · 정답 {len(ids) - 1}개")
st, j = post("/similar", {"img": img, "ex": {"x0": 0, "y0": 0}})
ok("본보기 없음 → 400 JSON", st == 400 and j.get("ok") is False and j.get("error"), j.get("error"))
st, j = post("/similar", {"img": img, "ex": {"x0": 0, "y0": 0, "png": "!!"}})
ok("깨진 PNG → 400 JSON", st == 400 and j.get("ok") is False, j.get("error"))
# C23 같은 번호가 멀리 떨어진 두 조각(진짜 열매 + 사진 반대쪽 끝의 작은 네모) → 본보기 네모가 칸보다 커도 400 이 아니라 200
fy2 = H - 10 if b0 < H // 2 else 0
e0, e1 = min(b0, fy2), max(b1, fy2 + 10)
two = np.zeros((e1 - e0, a1 - a0), bool); two[b0 - e0:b1 - e0] = m[b0:b1, a0:a1]; two[fy2 - e0:fy2 - e0 + 10, :10] = True
buf = io.BytesIO(); Image.fromarray((two * 255).astype(np.uint8)).save(buf, "PNG")
st, j = post("/similar", {"img": img, "ex": {"x0": int(a0), "y0": int(e0), "png": base64.b64encode(buf.getvalue()).decode()}})
ok("C23 떨어진 두 조각(네모 %d×%d > 칸 %s) → 200·후보" % (two.shape[0], two.shape[1], j.get("tile")), st == 200 and j.get("ok") and len(j.get("cands", [])) >= 1 and two.shape[0] > j.get("tile", 1e9), f"{st} {len(j.get('cands', []))}개 {j.get('error', '')}")
st, j = post("/sam", {"img": img, "x": int((a0 + a1) // 2), "y": int((b0 + b1) // 2), "crop": 384})
ok("기존 /sam 그대로", st == 200 and j.get("ok") and len(j.get("cands", [])) >= 1, f"{len(j.get('cands', []))}개")
print("== 실패 %d" % fails); sys.exit(1 if fails else 0)
