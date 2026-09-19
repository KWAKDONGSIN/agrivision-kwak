# -*- coding: utf-8 -*-
"""«이 사진은 몇 개인가» — 개수 유도(번호 확정 > 상자 확정 > 없음)와 개수 집계 주소.

구조 사이클 2(2026-09-20)에 `server.py`(counts_of·COUNT_TEAM)와 `instances.py`
(`/api/instance_stats`)에서 그대로 옮겼다. 유도 규칙 자체는 `domain/rules.py human_count()`.
"""

from __future__ import annotations
from typing import Any
import time

from flask import jsonify, request

from api import boxes as _boxes
from api import instances as _instances
from core.paths import n_boxes_of
from core.util import err_json, now_str
from domain.statusfmt import confirmed_of



# 0919 «개수 세기» 사이클1 — 지시서 §1-1·§1-2. 이 사진이 «몇 개인가» 를 **한 함수에서만** 센다.
# 유도 규칙(번호 확정 > 상자 확정 > 없음 · 둘 다 확정이고 수가 다르면 어긋남)은 boxes.human_count()
# 한 군데에 있고, counts.csv(export/export_dataset.py)와 통합 manifest 도 같은 규칙을 쓴다.
COUNT_TEAM = [("박성문", "team_park"), ("임성후", "team_im")]


def counts_of(fruit: str, stem: str, rec: Any=None) -> dict[str, Any]:
    """화면 하단 «개수» 칸이 쓰는 값. 없는 것은 None(화면은 «-»).

    boxes      = 사람이 저장한 상자 수(파일이 없으면 None)
    instances  = 열매 번호 수(캐시에 없으면 None — «아직 안 셈»)
    team_park·team_im = 검출 팀이 자동으로 뽑아 둔 상자 수(읽기 전용, 참고 값)
    human·source·conflict = 사람 확정 개수와 그것이 어디서 나왔나 · 상자↔번호가 어긋나나
    seed_source = «AI 초벌» 이 무엇에서 나오나 — 0919 **사이클4 결정 M1**.
      `team:박성문`(워터셰드 번호본) · `certh_gt`(포도 정답 송이) · `gt_numbers`(사과 원본 번호) ·
      `human_fixed`(사람이 고친 번호) · `cc4`(번호가 없어 이진 마스크를 4-연결로 센 폴백).
      전에는 화면 풍선말이 **늘** «4-연결 덩어리 기준» 이라고 말했는데, M1 뒤로는 그것이
      마지막 폴백일 때만 맞다 — 그래서 화면이 지어내지 않게 서버가 이름을 준다.
    """
    nb = n_boxes_of(fruit, stem)
    # 🔴 0919 개수 사이클1 **2차 검수 A-1**: 전에는 `cached_counts()` 였다 — 캐시의 **지문을 보지
    # 않아서** 사람이 번호를 고쳐 저장한 뒤에도 옛 개수를 말했다(실측: 파일 10개 ↔ 화면 95개).
    # `count_fresh()` 는 지금 파일을 센 값일 때만 주고, 아니면 아래에서 그 한 장을 다시 센다.
    ni = _instances.count_fresh(fruit, stem)
    cb = (confirmed_of(rec, "boxes") or {}).get("status")
    ci = (confirmed_of(rec, "instances") or {}).get("status")
    # 번호를 확정했는데 캐시에 개수가 없으면(아직 «세기» 를 안 돌린 사진) 그 한 장만 지금 센다.
    # 확정한 사진은 드물어 값이 싸다 — 여기서 세지 않으면 «번호로 확정했는데 개수는 상자 수» 라는
    # 조용한 거짓말이 된다(유도 우선순위가 ②로 내려간다).
    # 🔴 0919 3차 전 총괄 결정 3: 센 값을 **캐시에 적는다**(`count_one` → `count_now`) — 다음에 이
    # 사진을 열면 0 ms 다(2차 검수 §4-3 실측 복숭아 66.3 ms · 블루베리 약 0.6초를 한 번만 낸다).
    if ni is None and ci in ("ok", "fixed"):
        ni = _instances.count_now(fruit, stem)
    out = {"boxes": nb, "instances": ni}
    for who, key in COUNT_TEAM:
        out[key] = _boxes.team_count(who, fruit, stem)
    out["human"], out["source"], out["conflict"] = _boxes.human_count(nb, ni, cb, ci)
    # 0919 사이클4 M1 — 파일이 있나만 보는 값이라 싸다(os.path.exists 2번 + 과일당 한 번 기억한 어림)
    out["seed_source"] = _instances.seed_source_of(fruit, stem)
    return out

def register(app: Any, ctx: Any) -> None:
    """`/api/instance_stats` — 과일별 열매 번호 집계(캐시만 읽는다)."""
    fruits = ctx["FRUITS"]
    err_json = ctx["err_json"]
    now_str = ctx["now_str"]
    @app.route("/api/instance_stats")
    def api_instance_stats():
        """과일별 열매 번호 집계 — **캐시만 읽어 바로 답한다**(0917 사이클3 ③).

        ?start=1&fruit=<과일> 이면 낡은 사진을 뒤에서 다시 센다(사과 1,001장 첫 계산 약 7분).
        세는 중에는 running 에 진행(done/total)이 들어오므로 화면이 그걸 보여 주면 된다.
        /api/boxes_stats 와 같은 모양({fruit: {...}})이다.
        """
        want = request.args.get("fruit")
        if want and want not in fruits:
            return err_json("과일 이름이 잘못됐습니다.", 400)
        started = bool(want) and request.args.get("start") == "1" and _instances.start_count(want)
        out, run = {}, {}
        for f in ([want] if want else fruits):
            out[f] = _instances.summary(f)
            r = _instances._run.get(f)
            if r:
                run[f] = {"done": r["done"], "total": r["total"],
                          "sec": round(time.time() - r["t0"], 1)}
        return jsonify({"ok": True, "stats": out, "running": run,
                        "started": started, "at": now_str()})
