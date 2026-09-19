# -*- coding: utf-8 -*-
"""파일이 어디 있나 — 경로·과일 목록·데이터셋 폴더는 **여기 한 곳에만** 둔다.

구조 사이클 2(2026-09-20)에서 `server.py`·`dupes.py` 에 두 벌로 있던 경로 계산을 합쳤다.
값은 한 글자도 바뀌지 않았다(`app/dupes.py` 가 그대로 이 모듈을 다시 내보낸다).
"""

from __future__ import annotations
from typing import Any
import json
import os

from flask import abort


# ---------------------------------------------------------------- 경로 설정
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # app/ (이 파일은 app/core/)
ROOT = os.path.dirname(APP_DIR)                      # 260916_라벨링툴/
DATA_DIR = os.path.join(ROOT, "data")                # data/<fruit>/
CACHE_DIR = os.path.join(APP_DIR, "cache", "thumbs")
FRUITS = ["peach", "grape", "apple", "blueberry"]    # 검수 우선순위 순서(복숭아 -> 포도 -> 사과 -> 블루베리)
# 원본 이미지·마스크 폴더. 환경변수 LABELTOOL_DATA_ROOT 로 바꿀 수 있다
# (나중에 «검수 완료 수정판 데이터셋» 폴더를 가리키려고). 하위 구조는 같다고 가정:
#   <root>/<fruit>/images/<stem>.png , <root>/<fruit>/masks/<stem>.png
DEFAULT_DATASET = "/data/project/2026summer/kds0206/datasets_resized_2mp"
DATASET = os.environ.get("LABELTOOL_DATA_ROOT", "").strip() or DEFAULT_DATASET


def dataset_for(fruit: str) -> str:
    """과일마다 원본 폴더를 따로 고른다.

    검수판 폴더(`datasets_reviewed_260916`)에는 복숭아·포도만 있다. 그 폴더를 가리킨 채로
    사과·블루베리를 열면 «사진 0장» 이 된다(0917 확인). 그래서 그 과일 폴더가 없으면
    팀 표준 원본으로 되돌린다. 둘 다 읽기 전용이다.
    """
    if os.path.isdir(os.path.join(DATASET, fruit, "images")):
        return DATASET
    return DEFAULT_DATASET


def _mtime(p):
    """그 파일·폴더가 마지막으로 바뀐 시각(없으면 None) — 캐시가 «낡았나» 를 보는 데 쓴다."""
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


mtime_of = _mtime          # 공개 이름(뜻이 같은 별칭)


EXPORTS_DIR = os.path.join(ROOT, "exports")      # 데이터 정리 탭이 내보내는 곳(툴 폴더 안)
MAX_UPLOAD_BYTES = 64 * 1024 * 1024              # 한 요청 상한(수정본 PNG 는 2MP 기준 수백 KB)


def status_file(fruit: str) -> str:
    """그 과일의 판정 파일 `data/<fruit>/status.json`."""
    return os.path.join(DATA_DIR, fruit, "status.json")



def img_path(fruit: str, stem: str) -> str:
    """과일과 사진 이름에 해당하는 원본 이미지 경로를 돌려준다."""
    return os.path.join(dataset_for(fruit), fruit, "images", stem + ".png")


def gt_path(fruit: str, stem: str) -> str:
    """과일과 사진 이름에 해당하는 원본 마스크 경로를 돌려준다."""
    return os.path.join(dataset_for(fruit), fruit, "masks", stem + ".png")


def fixed_path(fruit: str, stem: str) -> str:
    """사람이 고친 이진 마스크의 저장 경로를 돌려준다."""
    return os.path.join(DATA_DIR, fruit, "masks_fixed", stem + ".png")


def proposal_path(fruit: str, stem: str) -> str:
    """AI가 제안한 이진 마스크의 경로를 돌려준다."""
    return os.path.join(DATA_DIR, fruit, "proposals", stem + ".png")

def inst_fixed_path(fruit: str, stem: str) -> str:
    """사람이 고친 **번호본** `data/<fruit>/instances_fixed/<stem>.png` (uint16)."""
    return os.path.join(DATA_DIR, fruit, "instances_fixed", stem + ".png")


def box_json_path(fruit: str, stem: str) -> str:
    """사람이 저장한 상자 `data/<fruit>/boxes/<stem>.json`."""
    return os.path.join(DATA_DIR, fruit, "boxes", stem + ".json")


def stems_listdir(fruit: str) -> list[str]:
    """그 과일 원본 폴더의 stem 목록(정렬) — 캐시 없이 한 번 읽는다. 폴더가 없으면 빈 목록."""
    d = os.path.join(dataset_for(fruit), fruit, "images")
    try:
        return sorted(n[:-4] for n in os.listdir(d) if n.lower().endswith(".png"))
    except OSError:
        return []



# ---------------------------------------------------------------- 파일 목록 캐시
_stems_cache = {}


def stems_of(fruit: str) -> list[str]:
    """데이터셋의 stem 목록(정렬). images 폴더가 바뀌면(사진 추가/삭제) 자동으로 다시 읽는다."""
    if fruit not in FRUITS:
        abort(404)
    d = os.path.join(dataset_for(fruit), fruit, "images")
    m = _mtime(d)
    hit = _stems_cache.get(fruit)
    if hit is not None and hit[0] == m:
        return hit[1]
    if m is None:
        _stems_cache[fruit] = (None, [], set())
        return []
    names = sorted(n[:-4] for n in os.listdir(d) if n.lower().endswith(".png"))
    _stems_cache[fruit] = (m, names, set(names))
    return names


def stem_set(fruit: str) -> set[str]:
    """과일별 사진 이름 집합을 캐시해 돌려준다."""
    stems_of(fruit)                       # 캐시 갱신
    return _stems_cache[fruit][2]


def check(fruit: str, stem: str) -> Any:
    """경로 조작 방지 — 데이터셋에 실제로 있는 stem 만 허용."""
    if fruit not in FRUITS:
        abort(404, "unknown fruit")
    if stem not in stem_set(fruit):
        abort(404, "unknown stem")
    return True


def has_proposals(fruit: str) -> bool:
    """해당 과일의 AI 제안 PNG가 하나라도 있는지 확인한다."""
    d = os.path.join(DATA_DIR, fruit, "proposals")
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.lower().endswith(".png"):
                    return True
    except OSError:
        return False
    return False


def fixed_set(fruit: str) -> set[str]:
    """수정된 마스크가 있는 사진 이름 집합을 돌려준다."""
    d = os.path.join(DATA_DIR, fruit, "masks_fixed")
    out = set()
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.lower().endswith(".png"):
                    out.add(e.name[:-4])
    except OSError:
        pass
    return out


# 0918 사이클4: 상자(bbox)가 **저장된** 사진 이름 + 상자 개수. 목록 2,400장에서 장마다 파일을
# 여는 대신 폴더를 한 번 훑는다. 개수는 파일을 읽어야 알 수 있으므로 **한 장 상세에서만** 센다.
def box_set(fruit: str) -> set[str]:
    """사람이 저장한 상자가 있는 사진 이름 집합을 돌려준다."""
    d = os.path.join(DATA_DIR, fruit, "boxes")
    out = set()
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.lower().endswith(".json"):
                    out.add(e.name[:-5])
    except OSError:
        pass
    return out


def n_boxes_of(fruit: str, stem: str) -> Any:
    """그 사진에 저장된 상자 개수 — 없으면 None(파일이 없음)."""
    p = os.path.join(DATA_DIR, fruit, "boxes", stem + ".json")
    try:
        with open(p, encoding="utf-8") as f:
            return len(json.load(f).get("boxes") or [])
    except Exception:
        return None


_prop_cache = {}


def _prop_names(fruit):
    d = os.path.join(DATA_DIR, fruit, "proposals")
    m = _mtime(d)
    key = ("propnames", fruit)
    if key in _prop_cache and _prop_cache[key][0] == m:
        return _prop_cache[key][1]
    out = set()
    try:
        with os.scandir(d) as it:
            for e in it:
                if e.name.lower().endswith(".png"):
                    out.add(e.name[:-4])
    except OSError:
        pass
    _prop_cache[key] = (m, out)
    return out
