# -*- coding: utf-8 -*-
"""`status.json` 한 항목의 **꼴**과 «AI 제안 / 사람 확정» 을 읽는 규칙, 그리고 작업자 B·C
산출물(inspection.csv · proposal_scores.csv · duplicates.json) 읽기.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다. 쓰기는 `core/status_store.py`.
"""

from __future__ import annotations
from typing import Any
import csv
import json
import os

from core.paths import DATA_DIR, gt_path, proposal_path, stem_set
from core.paths import _mtime
from core.util import log_warn

STATUSES = ["unreviewed", "ok", "fixed", "flag", "exclude"]


# ------------------------------------------------- 사람 확정(confirmed) — 0918 사이클2
# 방향 문서 §3-1: «AI 제안» 과 «사람 확정» 을 **다른 칸**으로 나눈다.
#   · status/by/at/note/prev 의 뜻은 하나도 바꾸지 않는다(P1·P2·N-A·N-C 계산식 그대로).
#   · 사람이 확정하면 `confirmed:{status,by,at,note}` 를 그 위에 얹는다. AI 제안은 지우지 않는다.
#   · `src` 는 «그 status 를 누가 넣었나» 다 — **읽기 전용으로 계산한다**(파일에 쓰지 않는다).
#     ⚠ 0918 사이클2 1차가 찾은 것: `status.json` 의 `src` 칸은 **이미 다른 뜻으로 쓰이고 있다**
#       (`dup_bulk`·`dup_group` = 어느 단추가 이 제외를 넣었나 · server.py 1241·1341행).
#       「일괄 제외 되돌리기」·「묶음 되돌리기」가 그 값만 보고 되돌린다(1283·1375행).
#       그래서 2차 설계안의 «src 를 쓸 때 ai/human 으로 적어 둔다» 는 **쓰지 않는 쪽으로** 바꿨다 —
#       적으면 그 표식을 덮어 되돌리기가 망가진다. 값이 `ai`/`human` 이면 그것을 믿고,
#       그 밖(=dup_bulk 등)이거나 없으면 `by` 로 미룬다. 마이그레이션 0 · 옛 코드 영향 0.
def src_of(rec: Any) -> str:
    """판정의 출처를 src 표식과 작성자 이름으로 판별한다."""
    v = (rec or {}).get("src")
    if v in ("ai", "human"):
        return v
    return "ai" if str((rec or {}).get("by") or "").startswith("AI") else "human"


# 0918 사이클4 결정 1: «확정» 을 작업 **종류별**로 나눈다. 칸 이름을 나누는 것이 핵심이다 —
# 한 칸에 섞으면 상자를 확정할 때 마스크 확정이 지워진다(사이클3 2차 §5-2).
#   mask      → confirmed            (사이클2 부터 있던 칸 · 이름을 바꾸지 않는다)
#   boxes     → confirmed_boxes      (새 칸)
#   instances → confirmed_instances  (새 칸)
# 세 칸은 서로 **독립**이다. 옛 자료에는 새 두 칸이 없으므로 «미확정» 으로 읽힌다(마이그레이션 0).
CONFIRM_KINDS = {"mask": "confirmed", "boxes": "confirmed_boxes",
                 "instances": "confirmed_instances"}


def confirmed_of(rec: Any, kind: str="mask") -> dict[str, Any] | None:
    """사람이 확정한 것 → {"status":…,"by":…,"at":…,"note":…} · 아직이면 None.

    kind 를 주지 않으면 **마스크 확정**이다 — 옛 호출(사이클2·3 의 코드·시험)이 한 글자도
    바뀌지 않게 하려는 것이다.
    """
    c = (rec or {}).get(CONFIRM_KINDS.get(kind, "confirmed"))
    return c if isinstance(c, dict) and c.get("status") in STATUSES else None


def verdict_of(rec: Any) -> str | None:
    """이 사진의 **최종** 판정. 사람이 확정한 것이 있으면 그것, 없으면 None(= 미확정)."""
    c = confirmed_of(rec)
    return c.get("status") if c else None


# ------------------------------------------------- 작업자 B/C 산출물 (없으면 무시)
_aux_cache = {}


def load_scores(fruit: str) -> dict[str, Any]:
    """작업자 C: proposal_scores.csv -> {stem: {...}}"""
    p = os.path.join(DATA_DIR, fruit, "proposal_scores.csv")
    m = _mtime(p)
    key = ("scores", fruit)
    if key in _aux_cache and _aux_cache[key][0] == m:
        return _aux_cache[key][1]
    out = {}
    if m is not None:
        try:
            with open(p, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    st = (row.get("stem") or "").strip()
                    if not st:
                        continue
                    rec = {}
                    for k in ("dice_vs_gt", "fg_gt_frac", "fg_pred_frac", "added_frac", "missed_frac"):
                        try:
                            rec[k] = float(row.get(k))
                        except (TypeError, ValueError):
                            rec[k] = None
                    rec["run_name"] = row.get("run_name")
                    out[st] = rec
        except Exception as e:
            log_warn("proposal_scores.csv 읽기 실패: %s", e)
            out = {}
    _aux_cache[key] = (m, out)
    return out


def load_inspection(fruit: str) -> dict[str, Any]:
    """작업자 B: inspection.csv -> {stem: {...}}"""
    p = os.path.join(DATA_DIR, fruit, "inspection.csv")
    m = _mtime(p)
    key = ("insp", fruit)
    if key in _aux_cache and _aux_cache[key][0] == m:
        return _aux_cache[key][1]
    out = {}
    if m is not None:
        try:
            with open(p, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    st = (row.get("stem") or "").strip()
                    if not st:
                        continue
                    flags = (row.get("suspect_flags") or "").strip()
                    rec = {"suspect_flags": flags, "suspect": bool(flags and flags.lower() not in ("none", "-", "0"))}
                    for k in ("fg_frac", "hole_frac", "largest_comp_frac"):
                        try:
                            rec[k] = float(row.get(k))
                        except (TypeError, ValueError):
                            rec[k] = None
                    for k in ("n_components", "tiny_comp_count"):
                        try:
                            rec[k] = int(float(row.get(k)))
                        except (TypeError, ValueError):
                            rec[k] = None
                    out[st] = rec
        except Exception as e:
            log_warn("inspection.csv 읽기 실패: %s", e)
            out = {}
    _aux_cache[key] = (m, out)
    return out


def split_flags(s: Any) -> Any:
    """suspect_flags 문자열 → 종류 목록. `;` 와 `|` 둘 다 구분자로 받는다
    (화면 쪽 ui.js 의 splitFlags 와 같은 규칙 — 두 곳이 다르면 «걸러도 그대로» 가 된다)."""
    return [x.strip() for x in str(s or "").replace(";", "|").split("|") if x.strip()]


def flag_counts(fruit: str, here: Any=None) -> Any:
    """이 과일에 실제로 있는 의심 종류와 장수 → {"filled_blob": 117, ...}
    데이터셋 «안» 사진만 센다(진행 현황 표와 같은 규칙)."""
    if here is None:
        here = stem_set(fruit)
    out = {}
    for s, rec in load_inspection(fruit).items():
        if s not in here:
            continue
        for f in split_flags(rec.get("suspect_flags")):
            out[f] = out.get(f, 0) + 1
    return out


def load_duplicates(fruit: str) -> Any:
    """작업자 B: duplicates.json -> {stem: group_index}, groups"""
    p = os.path.join(DATA_DIR, fruit, "duplicates.json")
    m = _mtime(p)
    key = ("dup", fruit)
    if key in _aux_cache and _aux_cache[key][0] == m:
        return _aux_cache[key][1]
    res = {"of_stem": {}, "groups": []}
    if m is not None:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            groups = d.get("groups") or []
            res["groups"] = groups
            for i, g in enumerate(groups):
                for st in g:
                    res["of_stem"][st] = i
        except Exception as e:
            log_warn("duplicates.json 읽기 실패: %s", e)
    _aux_cache[key] = (m, res)
    return res


def ai_boxes_status(fruit: str, stem: str, saved: Any=None, has_mask: Any=None) -> Any:
    """이 사진의 상자가 어디까지 와 있나 — 화면 하단 한 줄이 쓰는 말.
      "saved" = 사람이 저장한 상자 파일이 있다
      "seed"  = 아직 없지만 마스크가 있어 «초벌» 단추로 만들 수 있다
      "none"  = 마스크도 없어 초벌조차 못 만든다
    """
    if saved is None:
        saved = os.path.exists(os.path.join(DATA_DIR, fruit, "boxes", stem + ".json"))
    if saved:
        return "saved"
    if has_mask is None:
        has_mask = os.path.exists(gt_path(fruit, stem)) or os.path.exists(proposal_path(fruit, stem))
    return "seed" if has_mask else "none"
