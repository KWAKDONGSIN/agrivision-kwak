# -*- coding: utf-8 -*-
"""진행 현황(대시보드)과 살아 있는지 확인.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다(라우트 2개).
"""

from __future__ import annotations
from typing import Any
import os

from flask import jsonify, request

from core.paths import DATASET, DATA_DIR, FRUITS, fixed_set, stem_set, stems_of
from core.status_store import read_status
from core.util import now_str
from core.auth import AUTH_COOKIE, LABELTOOL_PASSWORD, auth_cookie_ok
from domain import dupes as DUP
from domain.statusfmt import STATUSES

def register(app: Any, ctx: Any) -> None:
    """라우트 2개를 붙인다."""

    # ---------------------------------------------------------------- 대시보드
    @app.route("/api/stats")
    def api_stats():
        out = {"fruits": [], "by_person": {}, "generated": now_str()}
        for f in FRUITS:
            stems = stems_of(f)
            st = read_status(f)
            counts = {k: 0 for k in STATUSES}
            for s in stems:
                v = st.get(s, {}).get("status", "unreviewed")
                counts[v if v in STATUSES else "unreviewed"] += 1
            # status.json 에는 «이미 데이터셋에서 빠진 사진»(중복 제외 뒤 실제로 지워진 것)의
            # 기록도 남아 있다. 그것까지 세면 위 과일별 표와 숫자가 어긋나므로 따로 센다.
            here = stem_set(f)
            for s, rec in st.items():
                v = rec.get("status", "unreviewed")
                if v == "unreviewed":
                    continue
                if s not in here:
                    out["outside_dataset"] = out.get("outside_dataset", 0) + 1
                    continue
                who = rec.get("by") or "(이름없음)"
                p = out["by_person"].setdefault(who, {k: 0 for k in STATUSES})
                if v in STATUSES:
                    p[v] += 1
            groups = DUP.load_duplicate_groups(f)
            dup_pairs = DUP.duplicate_exclusions(f)
            # 검수자별 표와 같은 규칙 — 데이터셋 «안» 사진만 세고, 밖은 따로 적는다.
            # (사과는 사진이 0장인데 «중복 84장» 으로 나오던 문제)
            dup_inside = sum(1 for s, _ in dup_pairs if s in here)
            out["fruits"].append({"fruit": f, "n_images": len(stems), "counts": counts,
                                  "n_fixed": len(fixed_set(f)),
                                  "n_dup_groups": len(groups),
                                  "n_dup_extra": dup_inside,
                                  "n_dup_extra_all": len(dup_pairs),
                                  "outside_dataset": len(dup_pairs) - dup_inside})
        return jsonify(out)


    @app.route("/api/health")
    def api_health():
        """살아 있는지만 확인하는 곳(로그인 없이 열려 있음).
        로그인하지 않은 사람에게는 서버 폴더 경로·PID 를 알려 주지 않는다."""
        out = {"ok": True, "time": now_str()}
        if not LABELTOOL_PASSWORD or auth_cookie_ok(request.cookies.get(AUTH_COOKIE)):
            out.update({"pid": os.getpid(), "data_root": DATASET, "out_dir": DATA_DIR})
        return jsonify(out)
