# -*- coding: utf-8 -*-
# 그림판 «클릭 칠하기» 도우미 — GPU 에 SAM2.1 을 올려 두고, 누른 점 주변의 열매 모양 후보를 돌려준다
"""작성: 2026-09-23

- 127.0.0.1:5112 에서만 듣는다(밖에서 못 들어온다). 라벨링 툴(5111)의 /api/sam 이 대신 부른다.
- 요청: POST /sam {"img": 사진 경로, "x": .., "y": .., "crop": 384}
  또는 {"img", "points": [[x, y, 1|0], ...], "box": [x0, y0, x1, y1]} — 0 = 빼기 점(여기는 아님), box = 네모 범위
- 답: {"ok": true, "cands": [{"x0","y0","w","h","score","png"(자른 칸 크기의 0/255 PNG, base64)}...]}
  점수 높은 순. 잘라 낸 칸의 40% 넘게 덮는 후보(배경)는 뺀다.
  1등 후보가 자른 칸 가장자리에 닿으면(열매가 칸보다 큼) 칸을 두 배로 키워 한 번 더 한다.
- (C14, 2026-09-25) POST /similar {"img", "ex": {"x0","y0","png"(본보기 열매 0/255 PNG)}, "limit": 300}
  → 본보기와 크기·둥근 정도·색·SAM 특징이 비슷한 열매 후보를 사진 전체에서 찾는다(_similar). 답은 /sam 과 같은 cands(+sim·feat).
  2MP 사진 한 장에 약 1~7초. 그동안 LOCK 을 쥐므로 다른 사람의 ✨ 클릭은 기다린다.
실행: ai_helper/run_helper.sh (GPU 는 비어 있는 것을 고른다)
"""
import base64, io, os, threading, time

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from flask import Flask, jsonify, request
from PIL import Image
from ultralytics.models.sam import SAM2Predictor

HERE = os.path.dirname(os.path.abspath(__file__))
PRED = SAM2Predictor(overrides=dict(model=os.path.join(HERE, "weights", "sam2.1_b.pt"), device=0,
                                    conf=0.0, verbose=False, save=False))
LOCK = threading.Lock()
LW = float(os.environ.get("SIM_LW", "0.35"))            # C14 색 거리에서 밝기(L) 비중
HIST_MIN = float(os.environ.get("SIM_HIST_MIN", "0.15"))  # C14 색 분포 겹침 하한
SIZE = tuple(float(v) for v in os.environ.get("SIM_SIZE", "0.35,2.8").split(","))   # C14 본보기 대비 넓이 범위(멀고 가까운 열매)
FEAT_MIN = float(os.environ.get("SIM_FEAT_MIN", "0.55"))   # C14 SAM 특징 닮음(코사인) 하한
CIRC_K = float(os.environ.get("SIM_CIRC_K", "0.6"))    # C14 둥근 정도 하한 = 본보기 × 이 값(0.55 아래로는 안 내림 — 잎은 길쭉해서 빠진다)
_img_cache = {"path": None, "im": None}
app = Flask(__name__)


def _image(path):
    if _img_cache["path"] != path:
        im = cv2.imread(path, cv2.IMREAD_COLOR)
        if im is None:
            raise ValueError("사진을 읽지 못했습니다: %s" % path)
        _img_cache.update(path=path, im=im)
    return _img_cache["im"]


def _png(mask):
    buf = io.BytesIO()
    Image.fromarray(mask.astype(np.uint8) * 255).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _run(im, pts, box, cs):
    """pts = [[x, y, 1(포함)|0(빼기)], ...] · box = [x0, y0, x1, y1] 또는 None (둘 다 사진 좌표)."""
    H, W = im.shape[:2]
    if box:
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        cs = max(cs, int(1.4 * max(box[2] - box[0], box[3] - box[1])))
    else:                                   # 점이 여럿이면 점들의 가운데
        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) // 2
        cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) // 2
    if pts:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cs = max(cs, int(1.4 * max(max(xs) - min(xs), max(ys) - min(ys))))
    cs = int(min(cs, W, H))
    x0 = max(0, min(W - cs, cx - cs // 2))
    y0 = max(0, min(H - cs, cy - cs // 2))
    crop = im[y0:y0 + cs, x0:x0 + cs]
    PRED.set_image(crop)
    kw = {"multimask_output": not (box or len(pts) > 1)}
    if pts:
        kw["points"] = [[p[0] - x0, p[1] - y0] for p in pts]; kw["labels"] = [int(p[2]) for p in pts]
    if box:
        kw["bboxes"] = [[box[0] - x0, box[1] - y0, box[2] - x0, box[3] - y0]]
    r = PRED(**kw)[0]
    if r.masks is None:
        return [], x0, y0, cs
    masks = r.masks.data.cpu().numpy() > 0
    scores = r.boxes.conf.cpu().numpy()
    first_pos = next(((p[0] - x0, p[1] - y0) for p in pts if int(p[2]) == 1), None)
    out = []
    for j in np.argsort(-scores):
        m = masks[j]
        n = int(m.sum())
        if n < 9 or (n > 0.4 * m.size and not box):
            continue
        if first_pos and not m[first_pos[1], first_pos[0]]:
            continue
        out.append((m, float(scores[j])))
    return out, x0, y0, cs


def _shape(m):
    """(둥근 정도 4πA/P² — 1 = 원, 볼록한 정도 A/볼록껍질 — 1 = 오목한 곳 없음). 가장 큰 테두리 하나로 잰다."""
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return 0.0, 0.0
    c = max(cs, key=cv2.contourArea)
    p, hull = cv2.arcLength(c, True), cv2.contourArea(cv2.convexHull(c))
    n = float(m.sum())
    return (4 * np.pi * n / (p * p) if p > 0 else 0.0), (min(1.0, n / hull) if hull > 0 else 0.0)


def _feat(mask):
    """지금 set_image 한 칸의 SAM 특징(256×64×64)을 모양 안에서 평균 내 길이 1 로. mask = 칸 크기 bool 텐서(여럿이면 N×T×T)."""
    emb = PRED.features["image_embed"] if isinstance(PRED.features, dict) else PRED.features
    mk = F.adaptive_avg_pool2d(mask.float().view(-1, 1, *mask.shape[-2:]), emb.shape[-2:])[:, 0]   # N×64×64
    v = torch.einsum("chw,nhw->nc", emb[0].float(), mk) / mk.sum((1, 2)).clamp(min=1e-6)[:, None]
    return F.normalize(v, dim=1)


def _hist(px):
    """Lab 색 분포(밝기 3 × 색 8 × 8 칸, 합 1) — 평균 색만으로는 잎과 흰 가루 낀 열매가 구별이 안 돼서 분포를 겹쳐 본다."""
    h, _ = np.histogramdd(px, bins=(3, 8, 8), range=((0, 256 * LW), (0, 256), (0, 256)))
    return h / max(1.0, h.sum())


def _ex_tile(em, ex0, ey0, W, H, T):
    """C23 본보기 둘레 T×T 칸의 왼쪽 위(fx, fy)와 그 칸 크기의 본보기 모양(big).
    본보기 네모가 칸보다 크면(같은 번호가 멀리 떨어진 두 조각) 가장 큰 조각을 가운데 두고, 칸 밖은 잘라 쓴다 — 양쪽 좌표가 겹치는 곳만 옮긴다."""
    eh, ew = em.shape
    cx, cy = ex0 + ew // 2, ey0 + eh // 2
    if eh > T or ew > T:
        _, _, st, _ = cv2.connectedComponentsWithStats(em.astype(np.uint8), connectivity=8)
        x, y, w, h = st[1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])), :4]
        cx, cy = ex0 + int(x) + int(w) // 2, ey0 + int(y) + int(h) // 2
    fx = max(0, min(W - T, cx - T // 2)); fy = max(0, min(H - T, cy - T // 2))
    big = np.zeros((T, T), bool)
    x0, y0, x1, y1 = max(ex0, fx), max(ey0, fy), min(ex0 + ew, fx + T), min(ey0 + eh, fy + T)
    if x1 > x0 and y1 > y0:
        big[y0 - fy:y1 - fy, x0 - fx:x1 - fx] = em[y0 - ey0:y1 - ey0, x0 - ex0:x1 - ex0]
    return fx, fy, big


def _similar(im, ex, limit=300, budget=25.0):
    """C14 «비슷한 열매 한꺼번에 찾기» — 본보기 열매(ex = x0·y0·w·h·png)와 크기·둥근 정도·색이 비슷한 SAM 모양을 사진 전체에서 찾는다.
    1) 본보기 색(Lab, 밝기는 덜 봄)과 가까운 자리에만 반 지름 간격으로 씨앗 점을 뿌린다.
    2) 사진을 본보기 지름의 약 10배 칸으로 나눠 칸마다 한 번 SAM 을 돌리고, 씨앗 점마다 세 후보 중 크기가 가장 맞는 것을 고른다.
    3) 크기 0.35~2.8배 · 둥근 정도 0.6배 이상 · SAM 특징 닮음 0.55 이상 · 볼록 · 색 분포가 겹치는 것만 남기고, 겹치면 더 비슷한 것 하나만 둔다."""
    t0 = time.time()
    H, W = im.shape[:2]
    ex0, ey0 = int(ex["x0"]), int(ex["y0"])
    em = np.array(Image.open(io.BytesIO(base64.b64decode(ex["png"]))).convert("L")) > 127
    eh, ew = em.shape
    em = em[:max(0, H - ey0), :max(0, W - ex0)]
    A = int(em.sum())
    if A < 9:
        raise ValueError("본보기 열매가 너무 작습니다")
    d = float(np.sqrt(4 * A / np.pi))
    circ0, sol0 = _shape(em)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= LW                        # 밝기는 덜 본다 — 그늘진 열매와 해 받은 열매가 같은 색으로 잡히게
    px = lab[ey0:ey0 + em.shape[0], ex0:ex0 + em.shape[1]][em]
    mu, h0 = px.mean(0), _hist(px)
    spread = float(np.percentile(np.linalg.norm(px - mu, axis=1), 75))
    thr = max(18.0, 1.5 * spread)
    # 1) 씨앗 점: 흐린 색이 본보기 색과 가까운 격자 점(본보기 안은 뺀다)
    k = max(3, int(d / 3) | 1)
    near = np.linalg.norm(cv2.blur(lab, (k, k)) - mu, axis=2) < thr
    g = max(4.0, d / 2)
    while True:
        gy, gx = np.mgrid[g / 2:H:g, g / 2:W:g]
        gy, gx = gy.astype(int).ravel(), gx.astype(int).ravel()
        keep = near[gy, gx]
        inx = (gx >= ex0) & (gx < ex0 + em.shape[1]) & (gy >= ey0) & (gy < ey0 + em.shape[0])
        keep[inx] &= ~em[gy[inx] - ey0, gx[inx] - ex0]
        if keep.sum() <= 2000:
            break
        g *= 1.3
    seeds = np.stack([gx[keep], gy[keep]], 1)
    # 본보기의 SAM 특징: 다른 칸과 같은 배율(칸 크기 T)로 본보기 둘레를 잘라 잰다
    T = int(min(max(10 * d, 256), 1024, W, H))
    fx, fy, big = _ex_tile(em, ex0, ey0, W, H, T)
    PRED.set_image(im[fy:fy + T, fx:fx + T])
    f0 = _feat(torch.from_numpy(big).to(PRED.device))[0]
    # 2) 칸 나누기: 칸 크기 T, 가장자리 여유 mg(열매가 두 칸에 걸쳐도 한 칸에는 통째로 들어가게)
    mg = min(int(1.2 * d) + 8, T // 4)
    st = T - 2 * mg
    ox = sorted({min(i * st, W - T) for i in range(max(1, -(-(W - T) // st) + 1))})
    oy = sorted({min(i * st, H - T) for i in range(max(1, -(-(H - T) // st) + 1))})
    def core(arr, i, n):                     # 이 칸이 맡는 가운데 구간(첫 칸은 0부터, 끝 칸은 사진 끝까지)
        return arr[i] + (mg if i > 0 else 0), (arr[i] + T - mg if i < len(arr) - 1 else n)
    cands, n_tiles, partial = [], 0, False
    todo = np.ones(len(seeds), bool)         # 칸이 겹치는 곳의 씨앗을 두 번 돌리지 않게
    for iy, ty in enumerate(oy):
        cy0, cy1 = core(oy, iy, H)
        for ix, tx in enumerate(ox):
            cx0, cx1 = core(ox, ix, W)
            inn = todo & (seeds[:, 0] >= cx0) & (seeds[:, 0] < cx1) & (seeds[:, 1] >= cy0) & (seeds[:, 1] < cy1)
            sel = seeds[inn]
            if not len(sel):
                continue
            todo &= ~inn
            if time.time() - t0 > budget:
                partial = True
                break
            n_tiles += 1
            PRED.set_image(im[ty:ty + T, tx:tx + T])
            for b in range(0, len(sel), 64):
                pts = sel[b:b + 64]
                r = PRED(points=(pts - [tx, ty]).tolist(), labels=[1] * len(pts), multimask_output=True)[0]
                if r.masks is None:
                    continue
                ms = r.masks.data > 0
                sc = r.boxes.conf.view(len(pts), -1)
                ar = ms.flatten(1).sum(1).float().view(len(pts), -1)
                # 씨앗마다 세 모양 중: 크기가 범위 안이고 SAM 점수 0.5 이상인 것 가운데 «점수 − 크기 차이» 가 가장 좋은 것
                lr = (ar / A).log()
                ok = (lr > np.log(SIZE[0])) & (lr < np.log(SIZE[1])) & (sc >= 0.5)
                pick = (sc - 0.3 * lr.abs() - (~ok) * 9).cpu().numpy()
                best = torch.as_tensor(pick.argmax(1), device=ms.device)
                fs = (_feat(ms.view(len(pts), -1, T, T)[torch.arange(len(pts), device=ms.device), best]) @ f0).cpu().numpy()
                for j in range(len(pts)):
                    q = int(np.argmax(pick[j]))
                    if pick[j, q] < -5 or fs[j] < FEAT_MIN:
                        continue
                    m = ms[j * ms.shape[0] // len(pts) + q].cpu().numpy()
                    ys, xs = np.nonzero(m)
                    a0, b0, a1, b1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
                    # 칸 가장자리에 닿은 모양은 잘렸을 수 있다(옆 칸이 통째로 본다) — 사진 끝은 괜찮다
                    if (a0 == 0 and tx > 0) or (b0 == 0 and ty > 0) or (a1 == T and tx + T < W) or (b1 == T and ty + T < H):
                        continue
                    mm = m[b0:b1, a0:a1]
                    n = int(mm.sum())
                    if n / A < SIZE[0]:
                        continue
                    circ, sol = _shape(mm)
                    if circ < max(0.55, CIRC_K * circ0) or sol < min(0.9, sol0 - 0.05):
                        continue
                    cp = lab[ty + b0:ty + b1, tx + a0:tx + a1][mm]
                    cd = float(np.linalg.norm(cp.mean(0) - mu))
                    hi = float(np.minimum(_hist(cp), h0).sum())    # 색 분포가 겹치는 몫(1 = 같음)
                    if cd > thr * 1.2 or hi < HIST_MIN:
                        continue
                    sim = float(np.exp(-abs(np.log(n / A))) * min(1.0, circ / max(circ0, 1e-6)) * hi * max(0.0, float(fs[j])))
                    cands.append({"x0": tx + int(a0), "y0": ty + int(b0), "m": mm, "n": n,
                                  "score": float(sc[j, q]), "sim": sim, "feat": float(fs[j])})
        if partial:
            break
    # 3) 겹침 정리: 더 비슷한 것부터 두고, 이미 둔 것(또는 본보기)과 25% 넘게 겹치면 버린다
    cands.sort(key=lambda c: -c["sim"] * c["score"])
    kept = [{"x0": ex0, "y0": ey0, "m": em, "n": A}]
    for c in cands:
        h, w = c["m"].shape
        dup = False
        for k2 in kept:
            kh, kw = k2["m"].shape
            ix0, iy0 = max(c["x0"], k2["x0"]), max(c["y0"], k2["y0"])
            ix1, iy1 = min(c["x0"] + w, k2["x0"] + kw), min(c["y0"] + h, k2["y0"] + kh)
            if ix1 <= ix0 or iy1 <= iy0:
                continue
            inter = int((c["m"][iy0 - c["y0"]:iy1 - c["y0"], ix0 - c["x0"]:ix1 - c["x0"]] &
                         k2["m"][iy0 - k2["y0"]:iy1 - k2["y0"], ix0 - k2["x0"]:ix1 - k2["x0"]]).sum())
            if inter > 0.25 * min(c["n"], k2["n"]):
                dup = True
                break
        if not dup:
            kept.append(c)
        if len(kept) > limit:
            partial = True
            break
    out = [{"x0": c["x0"], "y0": c["y0"], "w": int(c["m"].shape[1]), "h": int(c["m"].shape[0]),
            "score": round(c["score"], 3), "sim": round(c["sim"], 3), "feat": round(c["feat"], 3), "png": _png(c["m"])} for c in kept[1:]]
    return out, {"seeds": int(len(seeds)), "tiles": n_tiles, "tile": T, "d": round(d, 1), "partial": partial}


@app.route("/similar", methods=["POST"])
def similar():
    d = request.get_json(force=True, silent=True) or {}
    try:
        ex = d["ex"]
        with LOCK:
            t = time.time()
            im = _image(d["img"])
            cands, info = _similar(im, ex, limit=max(1, min(500, int(d.get("limit") or 300))))
            dt = time.time() - t
    except (KeyError, ValueError, TypeError, IndexError, OSError) as e:
        return jsonify({"ok": False, "error": "본보기 열매를 읽지 못했습니다: %s" % e}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": "도우미 오류: %s" % e}), 500
    return jsonify({"ok": True, "cands": cands, "sec": round(dt, 3), **info})


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/sam", methods=["POST"])
def sam():
    d = request.get_json(force=True, silent=True) or {}
    try:
        cs = max(128, min(2048, int(d.get("crop") or 384)))
        if "points" in d:
            pts = [[int(p[0]), int(p[1]), 1 if int(p[2]) else 0] for p in d["points"]][:20]
        elif "x" in d:
            pts = [[int(d["x"]), int(d["y"]), 1]]
        else:
            pts = []
        box = [int(v) for v in d["box"]][:4] if d.get("box") else None
        if box:
            box = [min(box[0], box[2]), min(box[1], box[3]), max(box[0], box[2]), max(box[1], box[3])]
        if not pts and not box:
            raise ValueError("점이나 네모가 필요합니다")
        with LOCK:
            t = time.time()
            im = _image(d["img"])
            cands, x0, y0, cs = _run(im, pts, box, cs)
            # 1등이 칸 가장자리에 닿으면 열매가 칸보다 크다 → 칸을 키워 다시 (네모가 있으면 칸은 이미 넉넉)
            if cands and not box:
                m = cands[0][0]
                if (m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()) and cs < min(im.shape[:2]):
                    cands, x0, y0, cs = _run(im, pts, box, cs * 2)
            dt = time.time() - t
    except (KeyError, ValueError, TypeError, IndexError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:                  # GPU 메모리 부족 등 — 화면이 이유를 읽을 수 있게 늘 JSON 으로
        return jsonify({"ok": False, "error": "도우미 오류: %s" % e}), 500
    res = []
    for m, sc in cands:
        ys, xs = np.nonzero(m)
        a, b, c, e = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        res.append({"x0": x0 + a, "y0": y0 + b, "w": c - a, "h": e - b, "score": round(sc, 3),
                    "png": _png(m[b:e, a:c])})
    return jsonify({"ok": True, "cands": res, "crop": cs, "sec": round(dt, 3)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("SAM_PORT", "5112")), threaded=True)
