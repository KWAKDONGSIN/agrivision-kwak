# -*- coding: utf-8 -*-
"""근접 중복 묶음 — 대표 1장 고르기·제외 목록. (작업자 B 의 duplicates.json 을 읽는다)

구조 사이클 2(2026-09-20): 경로 상수는 `core/paths.py`, 대표 고르기 규칙은
`domain/rules.py`, status.json 읽기는 `core/status_store.py` 로 갔다. 이 모듈은 그것을
다시 내보내므로 `app/dupes.py` 를 통한 옛 import(`from dupes import ...`)가 그대로 돈다.
"""

from __future__ import annotations
from typing import Any
import json
import os

from core.paths import (APP_DIR, DATA_DIR, DATASET, DEFAULT_DATASET, FRUITS, ROOT,
                        dataset_for)
from core.status_store import read_status
from domain.rules import pick_representative



def load_duplicate_groups(fruit: str) -> Any:
    """작업자 B 의 duplicates.json → [[stem, stem, ...], ...] (2장 이상인 그룹만)"""
    p = os.path.join(DATA_DIR, fruit, "duplicates.json")
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return []
    groups = d.get("groups") or []
    return [g for g in groups if isinstance(g, list) and len(g) >= 2]


def representative_map(groups: Any, status: Any) -> Any:
    """{stem: 그 stem 이 속한 그룹의 대표stem}. 대표 자신도 포함(자기 자신으로 매핑)."""
    out = {}
    for g in groups:
        rep = pick_representative(g, status)
        for s in g:
            out[s] = rep
    return out


def duplicate_exclusions(fruit: str) -> Any:
    """이 과일에서 «근접 중복이라 빼야 할» 사진 목록 → [(stem, 대표stem), ...]"""
    st = read_status(fruit)
    groups = load_duplicate_groups(fruit)
    if not groups:
        return []
    rep = representative_map(groups, st)
    return [(s, r) for s, r in sorted(rep.items()) if s != r]


def excluded_stems(fruit: str, include_duplicates: bool=True, drop_flag: bool=False) -> set[str]:
    """내보내기에서 빠지는 사진 전부 → [(stem, 이유)]"""
    st = read_status(fruit)
    out = {}
    # 근접 중복 이유를 먼저 적는다(일괄 제외로 status 가 exclude 가 돼 있어도
    # «왜 빠졌는지» 는 '어느 사진과 중복이라' 가 더 쓸모 있으므로)
    if include_duplicates:
        for s, r in duplicate_exclusions(fruit):
            out[s] = "duplicate_of:" + r
    for s, rec in st.items():
        if s in out:
            continue
        v = rec.get("status", "unreviewed")
        if v == "exclude":
            out[s] = "status_exclude"
        elif drop_flag and v == "flag":
            out[s] = "status_flag"
    return sorted(out.items())
