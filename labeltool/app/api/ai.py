# -*- coding: utf-8 -*-
# 그림판의 AI 도움 주소 — «클릭 칠하기»(SAM 도우미 5112 로 넘김)와 «모델 초벌»(미리 만든 번호 PNG) 을 준다
"""작성: 2026-09-23

- POST /api/sam   {fruit, stem, x, y, crop} 또는 {fruit, stem, points:[[x,y,1|0]], box:[x0,y0,x1,y1]} → 도우미(127.0.0.1:5112)가 준 모양 후보를 그대로 돌려준다.
  도우미가 꺼져 있으면 503 과 사람 말 안내. 사진 경로는 여기서 정한다(화면이 경로를 보내지 않는다).
- POST /api/sam_similar {fruit, stem, ex:{x0,y0,png}} → 도우미 /similar(C14 비슷한 열매 한꺼번에 찾기)의 후보를 그대로 돌려준다.
- GET  /draft?fruit&stem → data/<fruit>/draft/<stem>.png (모델 초벌 번호 마스크, uint16) · 없으면 404.
  &kind=gt → 원본 데이터셋의 열매별 정답 번호(복숭아·블루베리 instances_gt · 포도 instances_seed).
  초벌은 **화면에서 사람이 불러와 고쳐 저장해야** 라벨이 된다. 이 주소는 읽기만 한다.
"""
import json
import os
import urllib.error
import urllib.request
from typing import Any

from flask import Response, jsonify, request

SAM_URL = "http://127.0.0.1:%s/sam" % os.environ.get("SAM_PORT", "5112")
SIM_URL = SAM_URL[:-len("/sam")] + "/similar"


def register(app: Any, ctx: Any) -> None:
    check, img_path, err_json = ctx["check"], ctx["img_path"], ctx["err_json"]
    data_dir = ctx["DATA_DIR"]

    @app.route("/api/sam", methods=["POST"])
    def api_sam():
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        try:
            body = {"img": img_path(fruit, stem), "crop": int(d.get("crop") or 384)}
            if d.get("points"):          # [[x, y, 1|0], ...] — 0 = 빼기 점
                body["points"] = [[int(p[0]), int(p[1]), 1 if int(p[2]) else 0] for p in d["points"]][:20]
            elif d.get("x") is not None:
                body["x"], body["y"] = int(d.get("x")), int(d.get("y"))
            if d.get("box"):             # [x0, y0, x1, y1] 네모 범위
                body["box"] = [int(v) for v in d["box"]][:4]
            if "points" not in body and "x" not in body and "box" not in body:
                return err_json("누른 자리나 네모가 필요합니다.", 400)
        except (TypeError, ValueError, IndexError):
            return err_json("누른 자리(x·y)는 숫자여야 합니다.", 400)
        return _relay(SAM_URL, body, 60)

    def _relay(url, body, timeout):
        req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return Response(r.read(), mimetype="application/json")
        except urllib.error.HTTPError as e:
            return Response(e.read(), status=e.code, mimetype=e.headers.get_content_type() or "application/json")
        except Exception:
            return err_json("클릭 칠하기 도우미가 꺼져 있습니다. 1분쯤 뒤 다시 눌러 보세요(자동으로 다시 켜집니다).", 503)

    @app.route("/api/sam_similar", methods=["POST"])
    def api_sam_similar():
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        ex = d.get("ex") or {}
        try:
            body = {"img": img_path(fruit, stem), "limit": 300,
                    "ex": {"x0": int(ex["x0"]), "y0": int(ex["y0"]), "png": str(ex["png"])}}
        except (KeyError, TypeError, ValueError):
            return err_json("본보기 열매(x0·y0·png)가 필요합니다.", 400)
        return _relay(SIM_URL, body, 90)

    @app.route("/draft")
    def serve_draft():
        fruit, stem = request.args.get("fruit", ""), request.args.get("stem", "")
        check(fruit, stem)
        # kind=gt: 원본 데이터셋의 열매별 정답 번호(복숭아·블루베리 = instances_gt, 포도 = CERTH 송이 instances_seed)
        if request.args.get("kind") == "gt":
            sub = "instances_seed" if fruit == "grape" else "instances_gt"
            p = os.path.join(data_dir, fruit, sub, stem + ".png")
            if not os.path.exists(p):
                return err_json("이 사진에는 원본 정답 번호가 없습니다.", 404)
        else:
            # 새로 학습한 초벌(draft_v2, 포도·복숭아 정답 번호로 학습)이 있으면 그것, 없으면 첫 초벌(draft)
            p = os.path.join(data_dir, fruit, "draft_v2", stem + ".png")
            if not os.path.exists(p):
                p = os.path.join(data_dir, fruit, "draft", stem + ".png")
            if not os.path.exists(p):
                return err_json("이 사진에는 모델 초벌이 없습니다.", 404)
        with open(p, "rb") as f:
            return Response(f.read(), mimetype="image/png", headers={"Cache-Control": "no-cache"})
