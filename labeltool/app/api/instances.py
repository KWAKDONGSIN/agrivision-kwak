"""열매 번호(인스턴스 ID) 마스크 읽기·저장 — 0917 검출 팀 지시서 §3-3.

지시서: platform/work/park_seongmoon/260917_라벨링툴_열매번호편집_작업지시서.md
- 사과 원본 마스크는 L 모드에 화소값이 열매 번호(1..N)다. 0/255 로 바꿔 저장하면 번호가 사라진다.
- 그래서 번호 마스크는 `data/<과일>/instances_fixed/<stem>.png` (uint16) 에 따로 저장하고,
  같은 저장에서 «0보다 크면 255» 이진 마스크를 기존 `masks_fixed/` 에도 써서 세그 팀 흐름을 그대로 둔다.
- 블루베리·복숭아는 번호가 없으므로 검출 팀이 만든 watershed 초벌(instance_maps)을 초기값으로 읽는다(읽기 전용).
- 포도는 CERTH 원본에 **정답 송이**가 있어 그것을 uint16 번호본으로 옮겨 둔 것을 읽는다
  (2026-09-19 사이클4 M1 — 아래 SEED_DIRS 주석).

server.py 가 register(app, ctx) 를 부른다. 번호 마스크 규칙(어디서 읽을지·uint16 로 어떻게 쓸지)은
이 파일 한 군데에만 두고 export/export_dataset.py 도 여기서 가져다 쓴다(0917 사이클2: 두 벌이던 것을 합침).
"""

from __future__ import annotations
from typing import Any
import base64
import hashlib
import io
import json
import math
import os
import threading
import time

import numpy as np
from flask import Response, jsonify, request
from PIL import Image

from core import paths
from domain import dupes as DUP
from domain import rules
from domain.maskio import (ids_of, load_mask_bool,
                           png_u16_bytes, read_u16, write_u16_atomic)

# 검출 팀 산출물 (읽기 전용)
PARK = "/data/project/2026summer/platform/work/park_seongmoon"

# 🔴 0919 «개수 세기» **사이클4 결정 M1**(사이클3 3차 §2-1 · 2차 §11 1순위):
# «번호 초벌을 **다시 구현하지 말고** 박성문 님의 워터셰드 출력을 기본으로 돌려라 — 그 파일이 이미
#  워터셰드 출력이다». 근거(사이클3 2차 §5-4 실측): 복숭아 개수 MAE **0.30**(팀원 상자) ↔ **0.70**
#  (툴이 마스크를 4-연결로 센 값). 툴이 스스로 세는 CC 는 «없을 때만» 쓰는 폴백으로 내린다.
#   · 블루베리·복숭아 → 박성문 `bbox_outputs/<과일>/all/instance_maps`(워터셰드 uint16 번호본)
#   · 포도          → CERTH **정답 송이**를 uint16 번호본으로 옮겨 둔 `data/grape/instances_seed/`
#                     (`export/make_grape_instances.py` 산출 · 2,502장 오류 0 · 송이 9,832 — 0917
#                      사이클4 1차. 워터셰드는 포도에서 +123%, CC 는 +62% 로 자동 계수가 안 된다)
#   · 사과          → **원본 마스크에 정답 번호가 있다**(SEED_DIRS 에 넣지 않는다 — 넣으면 워터셰드가
#                     정답을 덮는다). `source_of()` 의 우선순위가 fixed > seed > gt 이기 때문이다.
# 🔴 **포도는 지금 꺼져 있다** — 2026-09-19 «개수 세기» 사이클4 **2차 검수**가 껐다.
#   까닭: 지난 결정이 아직 살아 있다 —
#     · `문서/260917_상자와번호기능_5회검수_최종판정.md` §1 표 «포도 송이 번호 = 켜지 않음» ·
#       §4 «그 전까지 사람 규칙 ③ 포도 켜지 않기» · §6 «켜기 = 이 한 줄 + 재시작»
#     · 남은 전제는 **교수님 확인 8번(포도 «송이» 정의 — 전경 기준을 우리 마스크로 두어도 되는가)** 이고
#       2026-09-19 현재 답이 없다.
#   1차가 «사이클3 3차 목록 1번» 을 이유로 켠 채로 넘겼으나, 그 목록은 사람 결정을 뒤집는 자리가 아니다.
#   ▶ **다시 켜는 법**: 아래 주석 한 줄(`"grape": ...`)을 되살리고 `bash app/run.sh restart`.
#     파일(`data/grape/instances_seed/` 2,502장 · 송이 9,832)은 그대로 있으므로 그것으로 끝난다.
#     켜면 같이 되돌려야 하는 곳(2차가 이번에 옛 값으로 돌려 둔 자리):
#       · `cycles/260917_신기능/cycle_5/stage1/live_c5.py` 와 `cycle_6_n6/stage1/live_c5.py` 의 포도 두 줄
#       · `cycles/260917_신기능/cycle_3/stage1/count_table.json` 포도 10줄의 `seed_after_expect_cnt4`
#     (복숭아는 **켠 채로** 둔다 — 복숭아 번호본은 교수님 확인 대상이 아니다)
SEED_DIRS = {"blueberry": os.path.join(PARK, "bbox_outputs/blueberry/all/instance_maps"),
             "peach": os.path.join(PARK, "bbox_outputs/peach/all/instance_maps")}
#            "grape": os.path.join(DUP.DATA_DIR, "grape", "instances_seed")   ← 교수님 확인 8번 뒤에 되살릴 줄

# 초벌이 «무엇에서» 나왔나 — 화면·API·counts.csv·README 가 **같은 낱말**을 쓰도록 이름을 한 곳에.
# (M1: 화면과 API 에 `seed_source` 를 표시한다. `team:<이름>` 은 상자 초벌의 `source` 와 같은 꼴이다)
SEED_SOURCE = {"blueberry": "team:박성문", "peach": "team:박성문", "grape": "certh_gt"}
#  kind(`source_of()` 가 돌려주는 것) → 사람에게 보여 줄 출처 이름
KIND_SOURCE = {"fixed": "human_fixed", "gt": "gt_numbers"}
CC4 = "cc4"                  # 번호가 아예 없어 이진 마스크를 4-연결로 센 것(ndimage.label 기본값)

ERROR_CSV = {"apple": os.path.join(PARK, "apple_check/confirmed_errors.csv")}


# ponytail: DATA_DIR·원본 폴더는 dupes 를 그대로 믿는다(server.py 의 ctx["DATA_DIR"]·gt_path 와 같은 값).
# 서버가 나중에 다른 data 폴더를 쓰게 되면 여기 두 함수도 ctx 를 받아야 한다.
inst_fixed_path = paths.inst_fixed_path


def source_of(fruit: str, stem: str, allow_fixed: bool=True) -> Any:
    """번호 마스크를 어디서 읽을지 — **사람이 고친 것 > 초벌(SEED_DIRS) > 원본 번호**.

    allow_fixed=False 면 «사람이 고친 것 말고 원본» 을 달라는 뜻이다.
    2026-09-19 사이클4(M1) 로 `SEED_DIRS` 가 블루베리·복숭아·포도 셋이 되어 **네 과일 모두** 번호본이
    있다(사과는 원본 마스크 자체가 번호 마스크라 `gt` 갈래로 온다). 번호본이 하나도 없는 사진만
    (None, None) 이고, 그 때만 부르는 쪽이 이진 마스크를 4-연결로 센다(= `seed_source` 의 `cc4`).
    ⚠ 우선순위가 `seed` > `gt` 이므로 **사과를 `SEED_DIRS` 에 넣으면 워터셰드가 정답 번호를 덮는다.**
    """
    if allow_fixed:
        p = inst_fixed_path(fruit, stem)
        if os.path.exists(p):
            return p, "fixed"
    d = SEED_DIRS.get(fruit)
    sp = d and os.path.join(d, stem + ".png")
    if sp and os.path.exists(sp):
        return sp, "seed"
    g = os.path.join(DUP.dataset_for(fruit), fruit, "masks", stem + ".png")
    if os.path.exists(g):
        vals = ids_of(read_u16(g))
        # 0/255 이진 마스크는 «번호 마스크» 가 아니다
        if vals.size > 1 or (vals.size == 1 and vals[0] != 255):
            return g, "gt"
    return None, None


def seed_source_of(fruit: str, stem: str) -> Any:
    """이 사진의 «초벌» 이 어디서 나오나 — **배열을 읽지 않고** 이름만 돌려준다(M1).

    돌려주는 낱말(하나뿐이고 화면·API·counts.csv·README 가 이것을 쓴다):
      `human_fixed`   사람이 고쳐 저장한 번호본(`instances_fixed/`) — 늘 제일 먼저다
      `team:박성문`   박성문 님 워터셰드 번호본(블루베리·복숭아 `instance_maps/`)
      `certh_gt`      CERTH 정답 송이 번호본(포도 `data/grape/instances_seed/`)
      `gt_numbers`    원본 마스크에 들어 있는 정답 번호(사과)
      `cc4`           번호가 아예 없어 이진 마스크를 **4-연결**로 센 폴백

    ⚠ `gt_numbers` 판단만 **과일 단위**다: 한 장이 번호 마스크인지 보려면 그 PNG 를 다 읽어야
    해서(사과 한 장 0.1초) `/api/item` 이 그만큼 느려진다. 그래서 이미 있는 `has_numbers()`
    (과일마다 앞 3장을 한 번만 보고 기억)를 쓴다. 정확한 값이 필요한 자리(상자 초벌 응답)는
    `load_inst()` 가 돌려준 `kind` 로 정하므로 이 어림을 쓰지 않는다.
    """
    if os.path.exists(inst_fixed_path(fruit, stem)):
        return KIND_SOURCE["fixed"]
    d = SEED_DIRS.get(fruit)
    if d and os.path.exists(os.path.join(d, stem + ".png")):
        return SEED_SOURCE.get(fruit, "team:박성문")
    return KIND_SOURCE["gt"] if has_numbers(fruit) else CC4


def source_name(fruit: str, kind: str) -> str:
    """`load_inst()` 의 kind(fixed·seed·gt·None) → `seed_source_of()` 와 **같은 낱말**."""
    if kind == "seed":
        return SEED_SOURCE.get(fruit, "team:박성문")
    return KIND_SOURCE.get(kind, CC4)


def mask_path_of(fruit: str, stem: str) -> Any:
    """이 사진의 «이진» 마스크 — 사람이 고친 것(masks_fixed) > 원본.

    내보내기(export_dataset.py)와 툴이 **같은 규칙**을 쓰도록 한 곳에 둔다(0917 사이클5 N1).
    """
    p = os.path.join(DUP.DATA_DIR, fruit, "masks_fixed", stem + ".png")
    return p if os.path.exists(p) else os.path.join(DUP.dataset_for(fruit), fruit, "masks", stem + ".png")


def load_inst(fruit: str, stem: str, allow_fixed: bool=True) -> Any:
    """번호 배열 — **이진본이 번호본을 자른다**(0917 사이클4 판정 N1).

    이진본이 배경인 자리의 번호는 0 으로 잘라서 준다(«없는 번호» 금지). 이진본이 전경인데 번호가
    없는 자리는 **채우지 않고 센다**(어느 번호인지 정할 수 없고 사람이 N·M 으로 붙일 자리다).
    파일은 고치지 않는다 — 읽을 때만 자른다.

    돌려주는 것 (arr, kind, chk). chk = {"cut": 잘린 화소, "lost_ids": 잘려 사라진 번호 수,
    "hole": 이진본 전경인데 번호 없는 화소}. 번호가 없는 사진은 (None, None, {}).
    """
    p, kind = source_of(fruit, stem, allow_fixed)
    if not p:
        return None, None, {}
    arr = read_u16(p)
    mp = mask_path_of(fruit, stem)
    if not os.path.exists(mp):
        return arr, kind, {"cut": 0, "lost_ids": 0, "hole": 0}
    m = load_mask_bool(mp)
    if m.shape != arr.shape:
        raise ValueError("번호 마스크와 이진 마스크의 크기가 다릅니다(번호 %s · 이진 %s)."
                         % (arr.shape, m.shape))
    out, chk = rules.cut_by_binary(arr, m)      # «이진본이 번호본을 자른다»(규칙 함수)
    return out, kind, chk


# ══════════════════ 열매 개수 집계(카운팅) — 디스크 캐시 ══════════════════
# 0917 UI 사이클3 ③. 번호 마스크 한 장을 세는 데 0.4~0.6초 걸린다(실측: 사과 0.404s ·
# 블루베리 0.602s). 사과 1,001 + 블루베리 1,195장이니 화면을 열 때마다 셀 수는 없다.
#   · 캐시는 **app/cache/instance_counts/<과일>.json 한 개** — 공용 data/ 에는 쓰지 않는다.
#   · 한 장이 낡았는지는 «번호 파일 + 이진 마스크의 mtime» 으로 본다 → 바뀐 장만 다시 센다.
#   · 개수 규칙(«이진본이 번호본을 자른다»)은 load_inst 를 그대로 쓴다 → 화면의 «번호 N개» 와 같은 숫자.
CACHE_DIR = os.path.join(paths.APP_DIR, "cache", "instance_counts")
NO_NUM = -1            # «이 사진에는 번호가 없다» 를 캐시에 적어 두는 값(복숭아·포도. 다시 세지 않게)
_counts_mem = {}       # {fruit: (캐시파일 mtime, {stem: [n, mt_src, mt_mask]})}
_run = {}             # {fruit: {"done": n, "total": N, "t0": 시각}}  — 지금 세고 있는 것
_run_guard = threading.Lock()


def _stems(fruit):
    d = os.path.join(DUP.dataset_for(fruit), fruit, "images")
    try:
        return sorted(n[:-4] for n in os.listdir(d) if n.lower().endswith(".png"))
    except OSError:
        return []


def _src_path(fruit, stem):
    """번호를 어디서 읽을지 — source_of 와 **같은 순서**지만 파일을 열지 않는다.

    source_of 는 «이게 번호 마스크가 맞나» 를 보려고 PNG 를 디코드한다(사과 0.13초). 지문만
    필요한 자리에서 1,001번 더 열면 그만큼 느려지므로, 여기서는 경로만 고른다.
    «번호가 맞나» 는 셀 때(count_one) load_inst 가 한 번 본다.
    """
    p = inst_fixed_path(fruit, stem)
    if os.path.exists(p):
        return p
    d = SEED_DIRS.get(fruit)
    if d:
        sp = os.path.join(d, stem + ".png")
        if os.path.exists(sp):
            return sp
    g = os.path.join(DUP.dataset_for(fruit), fruit, "masks", stem + ".png")
    return g if os.path.exists(g) else None


def _mt(p):
    try:
        return round(os.path.getmtime(p), 3)
    except OSError:
        return 0.0


def sig_of(fruit: str, stem: str) -> list[float]:
    """그 사진의 지문 [번호파일 mtime, 이진마스크 mtime]. 둘 중 하나라도 바뀌면 다시 센다."""
    p = _src_path(fruit, stem)
    return [_mt(p) if p else 0.0, _mt(mask_path_of(fruit, stem))]


def cache_file(fruit: str) -> str:
    """과일별 번호 개수 캐시 JSON 경로를 돌려준다."""
    return os.path.join(CACHE_DIR, fruit + ".json")


def load_counts(fruit: str) -> dict[str, Any]:
    """캐시 읽기(파일 mtime 이 그대로면 메모리에 둔 것을 준다 — server.py 의 _aux_cache 와 같은 방식)."""
    p = cache_file(fruit)
    m = _mt(p) if os.path.exists(p) else None
    if m is None:
        return {}
    hit = _counts_mem.get(fruit)
    if hit and hit[0] == m:
        return hit[1]
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        d = d if isinstance(d, dict) else {}
    except Exception:
        d = {}
    _counts_mem[fruit] = (m, d)
    return d


def save_counts(fruit: str, d: Any) -> None:
    """원자적 쓰기(임시파일 → os.replace). 세는 중에 서버가 꺼져도 캐시가 반쪽으로 남지 않는다."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    p = cache_file(fruit)
    tmp = p + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, p)


def stale_stems(fruit: str) -> list[str]:
    """다시 세야 할 사진 — 캐시에 없거나 지문이 달라진 것(파일을 열지 않고 mtime 만 본다)."""
    c = load_counts(fruit)
    out = []
    for s in _stems(fruit):
        rec = c.get(s)
        if not isinstance(rec, list) or len(rec) != 3 or rec[1:] != sig_of(fruit, s):
            out.append(s)
    return out


def count_one(fruit: str, stem: str) -> Any:
    """그 사진의 열매 번호 개수. 번호가 없으면 NO_NUM."""
    try:
        arr, _kind, _chk = load_inst(fruit, stem)
    except ValueError:
        return NO_NUM          # 번호본과 이진본 크기가 다른 사진 — 개수를 말할 수 없다
    if arr is None:
        return NO_NUM
    return int(ids_of(arr).size)


def recount(fruit: str, stems: Any, progress: Any=None) -> Any:
    """낡은 사진만 다시 세어 캐시에 적는다. 200장마다 한 번 저장한다(중간에 꺼져도 다시 안 세게)."""
    cache = dict(load_counts(fruit))
    for i, s in enumerate(stems, 1):
        sig = sig_of(fruit, s)          # 세기 «전» 의 지문 — 세는 동안 파일이 바뀌면 다음에 또 센다
        cache[s] = [count_one(fruit, s)] + sig
        if progress:
            progress(i)
        if i % 200 == 0:
            save_counts(fruit, cache)
    save_counts(fruit, cache)
    return cache


def cached_counts(fruit: str) -> Any:
    """{stem: 개수} — 목록 카드의 «N개» 딱지용. 캐시만 읽고 **새로 세지 않는다**.

    ⚠ **지문(mtime)을 보지 않는다** — 사람이 번호를 고쳐 저장한 뒤에도 옛 개수를 돌려준다.
    목록 딱지에는 그 편이 싸지만, «이 사진은 몇 개가 맞다» 를 말하는 자리(개수 칸·counts.csv)는
    아래 `count_fresh()` 를 써야 한다(0919 개수 사이클1 2차 검수 A-1).
    """
    return {s: v[0] for s, v in load_counts(fruit).items()
            if isinstance(v, list) and v and v[0] >= 0}


def count_fresh(fruit: str, stem: str) -> Any:
    """캐시가 **지금 그 파일**을 센 값일 때만 그 수를 준다(아니면 None = «다시 세야 한다»).

    🔴 0919 «개수 세기» 사이클1 **2차 검수 즉시 수정 A-1**(실측 `stage2/a2_stale.py` [가]·[나]):
    `cached_counts()` 는 지문을 보지 않아서, 사람이 번호를 10개로 고쳐 저장하고 «번호 확정» 이
    찍힌 뒤에도 화면 «개수» 칸과 `counts.csv` 가 **옛 95개**를 말했다. 같은 내보내기 job 에서
    나간 번호 PNG 는 10개였다 — 논문의 MAE·R² 가 그 표를 쓴다.
    `stale_stems()` 가 쓰는 것과 **같은 대조**(`rec[1:] == sig_of`)를 한 장에만 한다(stat 2번).
    """
    rec = load_counts(fruit).get(stem)
    if (isinstance(rec, list) and len(rec) == 3 and rec[0] is not None and rec[0] >= 0
            and rec[1:] == sig_of(fruit, stem)):
        return int(rec[0])
    return None



def count_now(fruit: str, stem: str) -> Any:
    """그 한 장을 **지금 세고 캐시에 적는다**(다음에 열 때는 0 ms). 셀 수 없으면 None.

    🔴 0919 «개수 세기» 사이클1 **3차 전 총괄 결정 3**(2차 검수 §4-3): 전에는 개수 칸·counts.csv 가
    «확정은 있는데 캐시에 없는» 사진을 **열 때마다** 다시 셌다(복숭아 3.9 → 66.3 ms · 블루베리는
    장당 약 0.6초). 센 값을 지문과 함께 캐시에 적으면 두 번째부터 공짜다.
    지문은 `sig_of()`(관련 파일 mtime+크기)이고 `stale_stems()`·`count_fresh()` 가 쓰는 것과 같다 —
    **세기 «전»** 의 지문을 적으므로, 세는 동안 파일이 바뀌면 다음에 또 센다(recount() 와 같은 규칙).
    ⚠ 이것은 **GET 이 파일을 쓰는** 유일한 자리다(캐시 `data/<과일>/cache/<과일>.json` 뿐 —
    `status.json`·마스크·번호본은 건드리지 않는다). 쓰기는 `save_counts()` 의 원자적 교체다.
    """
    sig = sig_of(fruit, stem)
    n = count_one(fruit, stem)
    cache = dict(load_counts(fruit))
    cache[stem] = [n] + sig
    try:
        save_counts(fruit, cache)
    except Exception:          # 캐시를 못 써도 개수는 돌려준다(읽기 전용 폴더·디스크 꽉 찬 경우)
        pass
    return n if n is not None and n >= 0 else None


_hasnum = {}


def has_numbers(fruit: str) -> bool:
    """이 과일에 «열매 번호» 라벨이 아예 있나 — 앞 3장만 보고 판단하고 기억한다.

    0918 UI사이클4 N9: 진행 현황의 «아직 안 센 N장 세기» 단추가 복숭아·포도에도 보여서, 누르면
    2,531장을 8분 세고 결과는 전부 0이었다. source_of() 가 «번호 마스크가 맞나» 를 보므로
    그것을 그대로 쓴다(한 장 0.1초). 과일마다 한 번만 재고 기억한다 — 번호가 «생기는» 것은
    사람이 instances_fixed 를 저장할 때뿐이고, 그때는 그 과일에 이미 번호가 있다.
    """
    if fruit not in _hasnum:
        _hasnum[fruit] = any(source_of(fruit, s)[0] for s in _stems(fruit)[:3])
    return _hasnum[fruit]


def summary(fruit: str) -> Any:
    """과일 한 개의 집계 — 합계·장당 평균·최대·아직 안 센 장수."""
    c = load_counts(fruit)
    ns = [v[0] for v in c.values() if isinstance(v, list) and v and v[0] >= 0]
    stems = _stems(fruit)
    return {"n_images": len(stems), "n_counted": len(ns), "n_cached": len(c),
            "n_instances": int(sum(ns)),
            "avg": round(sum(ns) / len(ns), 1) if ns else 0,
            "max": max(ns) if ns else 0,
            "stale": len(stale_stems(fruit)),
            # 화면이 «세기» 단추를 감출지 정하는 칸(추가만 — 기존 칸은 그대로다)
            "has_num": bool(has_numbers(fruit))}


def start_count(fruit: str) -> Any:
    """낡은 사진을 뒤에서(background thread) 센다. 이미 세고 있으면 아무것도 하지 않는다."""
    with _run_guard:
        if fruit in _run:
            return False
        stale = stale_stems(fruit)
        if not stale:
            return False
        _run[fruit] = {"done": 0, "total": len(stale), "t0": time.time()}

    def work():
        try:
            recount(fruit, stale, lambda i: _run[fruit].update(done=i))
        finally:
            with _run_guard:
                _run.pop(fruit, None)
    threading.Thread(target=work, daemon=True, name="instcount:" + fruit).start()
    return True


# ══════════════════ /instances 응답 캐시 — 2026-09-25 업그레이드 C07 ══════════════════
# 전에는 사진을 열 때마다 번호 PNG 를 다시 읽고 자르고 인코딩했다(0.2~0.3초 · 문서/260925_그림판_감사.md §2).
#   · 지문 = load_inst 가 읽을 수 있는 파일 **전부**(고친 번호·팀 초벌·원본 번호·고친 이진·원본 이진)의
#     경로+inode+mtime_ns+크기(C19 · 두번째의견 §2-1). 하나라도 바뀌면 다른 지문 → 새로 만든다.
#   · 같은 지문이면 ETag 가 같아 브라우저가 304 를 받고, 다른 브라우저라도 메모리에 둔 PNG 를 준다.
#   · ⚠ **저장 경로(api_save_instances 의 load_inst)는 이 캐시를 쓰지 않는다** — 늘 파일을 새로 읽는다.
_INST_CACHE_MAX = 48          # 한 장 수십~수백 KB → 최대 수십 MB
_inst_cache = {}              # {(fruit, stem, layer): (etag, png bytes, src)}  (넣은 순서 = 오래된 순)
_inst_cache_guard = threading.Lock()


def inst_etag(fruit: str, stem: str, layer: str) -> str:
    """이 사진·layer 의 /instances 응답 지문(파일을 열지 않고 stat 만 한다)."""
    d = SEED_DIRS.get(fruit)
    ps = (inst_fixed_path(fruit, stem), d and os.path.join(d, stem + ".png"),
          os.path.join(DUP.dataset_for(fruit), fruit, "masks", stem + ".png"),
          os.path.join(DUP.DATA_DIR, fruit, "masks_fixed", stem + ".png"))
    parts = [layer]
    for p in ps:
        try:
            st = os.stat(p) if p else None
            parts.append("%s:%d:%d:%d" % (p, st.st_ino, st.st_mtime_ns, st.st_size) if st else "-")
        except OSError:
            parts.append("-")
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:20]


def register(app: Any, ctx: Any) -> None:
    """Flask 앱에 이 모듈의 주소와 처리 함수를 등록한다."""
    check = ctx["check"]
    gt_path = ctx["gt_path"]
    fixed_path = ctx["fixed_path"]
    lock_for = ctx["lock_for"]
    err_json = ctx["err_json"]
    update_status = ctx["update_status"]
    fruits = ctx["FRUITS"]
    save_mask_atomic = ctx["save_mask_atomic"]
    now_str = ctx["now_str"]


    @app.route("/instances")
    def serve_instances():
        """uint16 PNG 를 그대로 준다(0/255 변환 금지). 이진본이 배경인 번호는 잘라서 준다(N1)."""
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        layer = request.args.get("layer", "auto")
        check(fruit, stem)
        # layer=="fixed" 는 «사람이 고친 것만», layer=="gt" 는 «고친 것 말고 원본·초벌» 을 달라는 뜻.
        # ponytail: 합치기 전에는 «고친 것이 있는데 원본이 0/255 이진» 일 때 그 이진 마스크를
        # 번호 마스크인 척 200 으로 줬다(복숭아·포도에서만 가능). 지금은 404 다 — 번호가 없는 게 맞다.
        if layer == "fixed" and not os.path.exists(inst_fixed_path(fruit, stem)):
            return err_json("이 사진에는 열매 번호 마스크가 없습니다.", 404)
        # C07: 지문이 같으면 304(브라우저 캐시) 또는 메모리의 PNG. no-cache = «쓰기 전에 늘 지문을 물어라».
        key = (fruit, stem, layer)
        etag = inst_etag(fruit, stem, layer)
        with _inst_cache_guard:
            hit = _inst_cache.get(key)
        if hit and hit[0] == etag:
            body, src = hit[1], hit[2]
        else:
            try:
                arr, src, _ = load_inst(fruit, stem, allow_fixed=(layer != "gt"))
            except ValueError as e:
                return err_json(str(e), 400)
            if arr is None:
                return err_json("이 사진에는 열매 번호 마스크가 없습니다.", 404)
            body = png_u16_bytes(arr)
            with _inst_cache_guard:
                _inst_cache.pop(key, None)
                _inst_cache[key] = (etag, body, src)
                while len(_inst_cache) > _INST_CACHE_MAX:
                    _inst_cache.pop(next(iter(_inst_cache)))
        r = Response(body, mimetype="image/png",
                     headers={"X-Instance-Source": src, "Cache-Control": "private, no-cache"})
        r.set_etag(etag)
        return r.make_conditional(request)

    @app.route("/api/instance_info")
    def api_instance_info():
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        check(fruit, stem)
        try:
            arr, src, chk = load_inst(fruit, stem)
        except ValueError as e:
            return err_json(str(e), 400)
        if arr is None:
            return jsonify({"ok": True, "has": False, "source": None, "n": 0})
        ids = ids_of(arr)
        return jsonify({"ok": True, "has": True, "source": src, "n": int(ids.size),
                        "max_id": int(ids.max()) if ids.size else 0,
                        "has_fixed": os.path.exists(inst_fixed_path(fruit, stem)),
                        # N1: 이진본이 번호본을 자른다 — 잘린 화소·«전경인데 번호 없는» 화소도 알려 준다
                        "cut_px": chk.get("cut", 0), "hole_px": chk.get("hole", 0),
                        "editable": True})

    def _decode(datauri, shape):
        """화면이 보낸 번호 마스크. uint16 PNG 이거나, RGBA 에 번호를 R+G*256 으로 담은 PNG."""
        if not datauri:
            raise ValueError("번호 마스크 그림이 들어 있지 않습니다. 새로고침한 뒤 다시 저장해 주세요.")
        if "," in datauri:
            datauri = datauri.split(",", 1)[1]
        try:
            raw = base64.b64decode(datauri)
            im = Image.open(io.BytesIO(raw))
        except Exception:
            raise ValueError("번호 마스크가 깨져서 읽을 수 없습니다. 새로고침한 뒤 다시 저장해 주세요.")
        with im:
            if im.size != (shape[1], shape[0]):
                raise ValueError("번호 마스크 크기가 원본과 다릅니다(보낸 것 %d×%d, 원본 %d×%d)."
                                 % (im.size[1], im.size[0], shape[0], shape[1]))
            a = np.array(im)
        if a.ndim == 3:                     # RGBA 인코딩: 번호 = R + G*256
            a = a[:, :, 0].astype(np.uint32) + a[:, :, 1].astype(np.uint32) * 256
        return a.astype(np.uint32)

    @app.route("/api/save_instances", methods=["POST"])
    def api_save_instances():
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        g = gt_path(fruit, stem)
        if not os.path.exists(g):
            return err_json("이 사진은 원본 마스크가 없습니다. 담당자에게 알려 주세요.", 404)
        with Image.open(g) as im:
            gw, gh = im.size
        try:
            arr = _decode(d.get("png"), (gh, gw))
        except ValueError as e:
            return err_json(str(e), 400)
        ids = ids_of(arr)
        counts = d.get("counts") if isinstance(d.get("counts"), dict) else {}
        p = inst_fixed_path(fruit, stem)
        with lock_for("inst:%s:%s" % (fruit, stem)):
            # N6(0917 사이클6 보충): 쓰기 규칙을 읽기 규칙과 **같은 문장**으로 맞춘다 —
            # «번호가 있던 화소만» 이진본에서 뺄 수 있다. 저장 직전의 «이진본으로 자른» 번호본을
            # 읽어서, 번호가 **없던** 전경(블루베리 초벌의 구멍·브러시로 넓힌 자리)은 이진본에 그대로 둔다.
            # 브러시로 지운 알은 이진본에 *없으므로* keep 에 들어오지 않는다(되살아나지 않는다).
            try:
                cur, _, _ = load_inst(fruit, stem)          # 저장 직전의 «이진본으로 자른» 번호본
            except ValueError as e:
                return err_json(str(e), 400)
            bfg = load_mask_bool(mask_path_of(fruit, stem))  # 지금 이진 마스크(고친 것이 있으면 그것)
            keep = rules.keep_numberless_foreground(bfg, cur, arr.shape)   # N6(규칙 함수)
            if keep.shape != arr.shape:
                return err_json("번호 마스크와 이진 마스크의 크기가 다릅니다(번호 %s · 이진 %s)."
                                % (arr.shape, keep.shape), 400)
            # 🔴 0919 사이클5(총괄) **3차 결정 1** — 번호를 0개로 지운 저장은 **서버가 막는다**.
            # 2차 검수 실측(§2-5-나 B-1~B-5): 0개로 저장하면 아래 save_mask_atomic 이
            # (arr>0)|keep 로 이진 마스크까지 비워(전경 1,180화소 → 0화소), 마스크를 «원본 OK» 로
            # 확정해 둔 사진이 «사람 확정만» 내보내기에 **빈 마스크 PNG** 로 나갔다(YOLO·분할 학습에서
            # «이 사진에는 열매가 없다» 는 라벨). 화면 확인창은 사이클4 회귀 `s1_flow` 나-4·나-5 를
            # 깨뜨리므로(WebDriver 가 창을 닫아 저장이 안 된다) **서버에서 400 으로 막고**, 그 기대값은
            # 이 결정의 주석과 함께 갱신했다. 파일·확정은 한 글자도 바뀌지 않는다(쓰기 전에 되돌아간다).
            # 열매가 정말 없는 사진은 «4 제외» 가 바른 길이다(이진 전경이 0이면 그대로 저장된다).
            if rules.zero_instance_save_blocked(ids.size, bfg):
                msg = ("번호를 전부 지운 저장은 막습니다. "
                       "열매가 정말 없는 사진이면 «4 제외»를 누르세요")
                return jsonify({"ok": False, "error": msg, "msg": msg,
                                "blocked": "instances_zero"}), 400
            write_u16_atomic(p, arr)
            save_mask_atomic(fixed_path(fruit, stem), (arr > 0) | keep)   # 번호가 있던 화소만 뺀다
            # ── 0917 ab사이클2 P2: 전에는 status 를 무조건 fixed 로, 메모를 «번호 편집» 으로
            # **덮어썼다.** 그래서 3차 판정의 flag(«사람 확인 필요 … 후보 좌표») 68장은 사람이
            # 번호를 한 번 저장하는 순간 왜 flag 였는지가 사라지고, exclude 였던 사진은 fixed 가
            # 되어 내보내기에 되살아났다. → 판정은 남기고, 메모는 앞에 붙이고, 직전 것은 prev 에 둔다.
            before = DUP.read_status(fruit).get(stem) or {}
            prev_status = before.get("status", "unreviewed")
            prev_note = str(before.get("note") or "")
            note = ("번호 편집 " + " ".join("%s=%s" % (k, counts.get(k)) for k in
                                         ("erase", "merge", "split", "add") if counts.get(k))).strip()
            # 0918 사이클2 (사이클1 3차 판정 ②-7): 세 저장 중 **번호 저장만** 사람이 적은 메모를
            # 서버에 안 보냈다. 앞머리 «번호 편집 …» 은 그대로 둔다 — P2 가 «두 번째 저장인가» 를
            # 그 앞머리로 판별하기 때문이다. 메모 칸은 이 사진의 옛 메모로 미리 채워져 있으므로
            # (app.js openItem), 옛 메모에 이미 들어 있는 말은 붙이지 않는다(두 번 적히지 않게).
            hn = (d.get("note") or "").strip()[:rules.NOTE_MAX]
            # 0918 사이클2 **2차 검수**: 위 규칙만으로는 **두 번째** 번호 저장에서 사람 메모가
            # 통째로 사라졌다(실측 s4_paint8 ②-7′ · s1_api 가-P2). 화면의 메모 칸은 «내 앞 저장»
            # 메모(«번호 편집 … · <사람 메모> · (이전) …»)로 미리 채워져 있어서, 그것을 그대로
            # 보내면 hn 이 prev_note 안에 있다는 이유로 버려졌기 때문이다.
            # → 자동으로 붙는 앞머리(«번호 편집 …»)와 꼬리(«(이전) …»)를 떼고 «사람이 쓴 몫» 만 남긴다.
            if hn.startswith("번호 편집"):
                hn = hn.split(" · (이전) ")[0]
                hn = hn.split(" · ", 1)[1] if " · " in hn else ""
            elif hn and hn == prev_note:
                # 메모 칸을 **손대지 않았다**(openItem 이 옛 메모로 채워 둔 그대로) → «(이전)» 으로 이미 남는다.
                # ⚠ «들어 있으면(in)» 으로 보면 안 된다 — 사람이 적은 메모는 앞 저장의 메모 안에
                #   들어 있으므로, 두 번째 저장에서 그것까지 버려진다(실측 s4_paint8 ②-7′).
                hn = ""
            if hn and hn not in note:
                note = (note + " · " + hn)[:rules.NOTE_MAX]
            # 0918 UI사이클3 2차: **두 번째 저장**에서도 «(이전) …» 를 지키지 않으면, 화면에 남는
            # 메모가 «번호 편집 …» 뿐이 되어 flag 사유와 P4 의 노란 점선(메모 좌표로 그린다)이
            # 사라진다(실측: 두 번 저장하니 노란 화소 117 → 0). prev 에 넣어 둔 «맨 처음» 메모를 쓴다.
            keep_note = prev_note
            if prev_note.startswith("번호 편집"):
                keep_note = str((before.get("prev") or {}).get("note") or "") \
                    if isinstance(before.get("prev"), dict) else ""
            if keep_note and not keep_note.startswith("번호 편집"):
                note = (note + " · (이전) " + keep_note)[:rules.NOTE_MAX]
            # exclude·flag 는 «이 사진을 어떻게 쓸지» 에 대한 판정이라 번호 편집이 뒤집지 않는다.
            new_status = rules.status_after_instance_save(prev_status)
            st = update_status(fruit, stem, new_status, (d.get("by") or "익명")[:rules.NAME_MAX], note[:rules.NOTE_MAX])
            if "prev" in before:
                st["prev"] = before["prev"]            # 두 번째 저장에서도 «맨 처음» 것을 지킨다
            elif prev_status != "unreviewed" or prev_note:
                st["prev"] = {"status": prev_status, "note": prev_note[:rules.NOTE_MAX],
                              "by": before.get("by") or ""}
            st["instances_edited"] = True
            st["instance_counts"] = {k: int(counts.get(k) or 0) for k in ("erase", "merge", "split", "add")}
            ctx["write_status_entry"](fruit, stem, st)
            # 0918 사이클4 결정 1: **저장 = 그 작업의 확정(수정함)**. 마스크 «수정본 저장» 과 같은
            # 규칙. `confirmed_instances` 칸에만 쓰므로 마스크 확정(`confirmed`)은 그대로다.
            # ⚠ 반드시 write_status_entry **뒤**에 — 그 함수는 항목을 통째로 덮어쓰기 때문이다.
            conf = ctx.get("confirm_status")
            if conf:
                conf(fruit, [(stem, "fixed")], (d.get("by") or "익명")[:rules.NAME_MAX], note[:rules.NOTE_MAX], "instances")
        return jsonify({"ok": True, "n_instances": int(ids.size),
                        "max_id": int(ids.max()) if ids.size else 0,
                        # N6: 전경인데 번호가 없어 이진본에 그대로 둔 화소
                        "hole_px": int(keep.sum()),
                        "fg_pixels": int((arr > 0).sum()), "status": st})

    @app.route("/api/revert_instances", methods=["POST"])
    def api_revert_instances():
        """번호 편집을 되돌린다 — 파일 두 개를 지우고 **편집 기록도 같이 지운다**(0917 사이클2).

        고치기 전에는 파일만 지우고 status.json 항목의 `instances_edited`·`instance_counts` 가
        그대로 남아서, 되돌린 사진이 목록·집계에서 계속 «번호를 편집한 사진» 으로 보였다.

        되돌릴 것이 «아무것도» 없으면(수정본 파일도 없고 편집 기록도 없으면) status 항목을
        건드리지 않는다 — 번호를 편집한 적이 없는 사진의 원래 상태·메모·검수자를 이 호출이
        `unreviewed` / «번호 편집 되돌림» 으로 덮어쓰지 않게 하려는 것이다.
        """
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        removed = []
        with lock_for("inst:%s:%s" % (fruit, stem)):
            for p in (inst_fixed_path(fruit, stem), fixed_path(fruit, stem)):
                if os.path.exists(p):
                    os.remove(p)
                    removed.append(os.path.basename(os.path.dirname(p)))
            # 편집 기록만 남고 파일은 이미 없는 사진(고치기 전 판이 만든 상태)도 치워야 한다.
            before = DUP.read_status(fruit).get(stem) or {}
            had_record = bool(before.get("instances_edited")) or ("instance_counts" in before)
            if not removed and not had_record:
                return jsonify({"ok": True, "removed": [], "changed": False, "status": before})
            # 0917 ab사이클2 P2: 번호 편집 «전» 의 판정·메모가 prev 에 있으면 그것으로 되돌린다.
            # (없으면 예전처럼 unreviewed — 번호만 고쳤던 사진이다)
            # 판정·메모·검수자는 «한 벌» 이므로 셋을 함께 되돌린다(누가 되돌렸는지는 at 로 남는다)
            prev = before.get("prev") if isinstance(before.get("prev"), dict) else None
            st = update_status(fruit, stem,
                               (prev or {}).get("status") or "unreviewed",
                               (prev.get("by") if prev else None) or (d.get("by") or "익명")[:rules.NAME_MAX],
                               (prev or {}).get("note") if prev else "번호 편집 되돌림")
            # ponytail: update_status 가 쓴 «편집 기록이 아직 남은» 항목을 곧바로 덮어써서 지운다.
            # 두 번 쓰는 사이(같은 inst 자물쇠 안이지만 status 자물쇠는 놓은 상태)에 다른 요청이
            # status.json 을 읽으면 기록이 아직 보일 수 있다 — 저장 쪽(api_save_instances)도 같은 방식이다.
            st.pop("instances_edited", None)
            st.pop("instance_counts", None)
            st.pop("prev", None)
            st = ctx["write_status_entry"](fruit, stem, st)
            # 0918 사이클4 3차 전 소수정(총괄 결정 1): 되돌렸으면 **번호 확정도 지운다.**
            # 마스크 쪽(/api/revert)과 **같은 함수**(server.clear_confirm) 한 곳에서 한다.
            # write_status_entry **뒤**에 — 그 함수는 항목을 통째로 덮어쓴다(저장 쪽과 같은 순서).
            cleared, st = ctx["clear_confirm"](fruit, stem, "instances")
        return jsonify({"ok": True, "removed": removed, "changed": True,
                        "restored": bool(prev), "status": st, "confirmed_cleared": cleared})

    # 0925 C18: 사진당 작업 시간·수정 횟수 — 논문의 «라벨링 시간 절감» 측정용.
    # app/logs/worklog.jsonl 에 한 줄씩 덧붙이기만 한다(data/·status.json 은 건드리지 않는다).
    # 모래상자는 app/ 을 통째로 복사해 돌므로 시험 기록은 실서버 로그에 섞이지 않는다.
    worklog = os.path.join(paths.APP_DIR, "logs", "worklog.jsonl")
    wl_nums = ("active_s", "wall_s", "edits", "undos", "redos", "sam", "n_open", "n_save")

    @app.route("/api/worklog", methods=["POST"])
    def api_worklog():
        d = request.get_json(force=True, silent=True) or {}
        fruit, stem = d.get("fruit", ""), d.get("stem", "")
        check(fruit, stem)
        if d.get("action") not in ("save", "exclude"):
            return err_json("action 은 save 나 exclude 입니다.", 400)
        row = {"at": now_str(), "fruit": fruit, "stem": stem, "action": d["action"],
               "by": str(d.get("by") or "익명")[:rules.NAME_MAX]}
        for k in wl_nums:
            try:
                v = float(d.get(k) or 0)
            except (TypeError, ValueError):
                v = 0.0
            # 0925 C24: NaN·Infinity 는 0 으로(NaN 은 min/max 를 빠져나가 int() 500·비표준 JSON 이 된다)
            v = min(max(v, 0.0), 1e6) if math.isfinite(v) else 0.0     # 이상한 값은 0~1e6 으로 자른다
            row[k] = round(v, 1) if k.endswith("_s") else int(v)   # 초는 소수 한 자리, 횟수·번호 수는 정수
        os.makedirs(os.path.dirname(worklog), exist_ok=True)
        with lock_for("worklog"):
            with open(worklog, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return jsonify({"ok": True})

    @app.route("/api/instance_errors")
    def api_instance_errors():
        """검출 팀이 눈으로 확인한 «번호 오류» 목록 — 목록 정렬·딱지·점선 상자에 쓴다(지시서 §3-4)."""
        fruit = request.args.get("fruit", "")
        if fruit not in fruits:
            return err_json("과일 이름이 잘못됐습니다.", 400)
        p = os.environ.get("LABELTOOL_ERROR_CSV_" + fruit.upper()) or ERROR_CSV.get(fruit)
        if not p or not os.path.exists(p):
            return jsonify({"ok": True, "rows": [], "by_stem": {}, "source": p})
        import csv
        rows, by_stem = [], {}
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    box = [int(float(r[k])) for k in ("x0", "y0", "x1", "y1")]
                except Exception:
                    box = None
                item = {"idx": r.get("idx"), "stem": r.get("stem"), "verdict": r.get("verdict"),
                        "inst_ids": r.get("inst_ids"), "note": r.get("note"), "box": box}
                rows.append(item)
                by_stem.setdefault(item["stem"], []).append(item)
        return jsonify({"ok": True, "n": len(rows), "n_stems": len(by_stem),
                        "rows": rows, "by_stem": by_stem, "source": p})
