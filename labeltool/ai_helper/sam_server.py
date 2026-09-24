# -*- coding: utf-8 -*-
# 그림판 «클릭 칠하기» 도우미 — GPU 에 SAM2.1 을 올려 두고, 누른 점 주변의 열매 모양 후보를 돌려준다
"""작성: 2026-09-23

- 127.0.0.1:5112 에서만 듣는다(밖에서 못 들어온다). 라벨링 툴(5111)의 /api/sam 이 대신 부른다.
- 요청: POST /sam {"img": 사진 경로, "x": .., "y": .., "crop": 384}
  또는 {"img", "points": [[x, y, 1|0], ...], "box": [x0, y0, x1, y1]} — 0 = 빼기 점(여기는 아님), box = 네모 범위
- 답: {"ok": true, "cands": [{"x0","y0","w","h","score","png"(자른 칸 크기의 0/255 PNG, base64)}...]}
  점수 높은 순. 잘라 낸 칸의 40% 넘게 덮는 후보(배경)는 뺀다.
  1등 후보가 자른 칸 가장자리에 닿으면(열매가 칸보다 큼) 칸을 두 배로 키워 한 번 더 한다.
실행: ai_helper/run_helper.sh (GPU 는 비어 있는 것을 고른다)
"""
import base64, io, os, threading, time

import cv2
import numpy as np
from flask import Flask, jsonify, request
from PIL import Image
from ultralytics.models.sam import SAM2Predictor

HERE = os.path.dirname(os.path.abspath(__file__))
PRED = SAM2Predictor(overrides=dict(model=os.path.join(HERE, "weights", "sam2.1_b.pt"), device=0,
                                    conf=0.0, verbose=False, save=False))
LOCK = threading.Lock()
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
