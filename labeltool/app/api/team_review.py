# 팀원의 포도 제외 목록과 사과 의심 개체를 읽기 전용으로 제공한다.
from pathlib import Path
import csv
import re
from flask import jsonify, request, send_file, abort
from core.paths import DEFAULT_DATASET
from api.instances import PARK

CHOI = Path(PARK).parent / "choi_inhun/260920_grape_삭제대상.md"
APPLE = Path(PARK) / "apple_check"


def register(app, ctx):
    @app.get("/team_photo/grape/<stem>")
    def team_photo(stem):
        # 제외돼 편집 목록에 없는 사진도 원본만 읽어 보여 준다. 저장 경로는 없다.
        if not stem.isascii() or not stem.isdigit():
            abort(404)
        path = Path(DEFAULT_DATASET) / "grape/images" / (stem + ".png")
        if not path.is_file():
            abort(404)
        if request.args.get("image") == "1":
            return send_file(path, mimetype="image/png")
        return ("<!doctype html><html lang='ko'><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                "<title>포도 원본 보기</title><style>body{font:17px sans-serif;margin:16px}"
                "img{max-width:100%;max-height:85vh}a{color:#1661a1}</style>"
                "<a href='/'>툴로 돌아가기</a><h1>포도 " + stem + " · 원본 보기</h1>"
                "<p>현재 편집 목록에 없는 사진입니다. 원본 확인만 하며 저장·삭제하지 않습니다.</p>"
                "<img alt='포도 원본 사진' src='?image=1'></html>")

    @app.get("/api/team_review")
    def team_review():
        fruit = request.args.get("fruit", "")
        if fruit == "grape":
            if not CHOI.is_file():
                return ctx["err_json"]("최인훈 검수 원본 문서가 없습니다.", 404)
            blocks = re.findall(r"```text\n(.*?)```", CHOI.read_text(), re.S)
            groups = []
            for text, source in zip(blocks[:2], ["곽동신 기존 육안 확정", "최인훈 육안 확정"]):
                groups.append({"source": source, "stems": re.findall(r"\d+", text)})
            return jsonify(ok=True, source=CHOI.name, groups=groups,
                           n=sum(len(g["stems"]) for g in groups))
        if fruit != "apple":
            return ctx["err_json"]("사과 또는 포도를 고르세요.", 400)
        if not (APPLE / "review_list.csv").is_file():
            return ctx["err_json"]("박성문 사과 검수 자료가 없습니다.", 404)
        stem = request.args.get("stem")
        rows, queue, seen = [], [], set()
        files = [APPLE / "review_list.csv", APPLE / "review_extra.csv"] + sorted(APPLE.glob("suspects_*.csv"))
        for path in files:
            if not path.is_file():
                continue
            with path.open(newline="", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    if path.name == "review_list.csv" and r["stem"] not in queue:
                        queue.append(r["stem"])
                    if not stem or r["stem"] != stem:
                        continue
                    ids = r.get("inst_ids") or r.get("inst") or "/".join(r[k] for k in ("inst_a", "inst_b") if r.get(k))
                    key = (r["stem"], ids, path.name)
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        box = [int(float(r[k])) for k in ("x0", "y0", "x1", "y1")]
                    except (KeyError, ValueError):
                        continue
                    rows.append(dict(stem=stem, inst_ids=ids, box=box,
                                     verdict=r.get("verdict") or "자동 의심", note=r.get("note", ""), source=path.name))
        return jsonify(ok=True, queue=queue, rows=rows, source="박성문 apple_check")
