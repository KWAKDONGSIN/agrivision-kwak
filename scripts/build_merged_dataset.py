# -*- coding: utf-8 -*-
"""네 과일(사과·포도·복숭아·블루베리) 통합 데이터셋 빌드 — 작성: 2026-09-18

무엇을 하나
    ① 바탕 = 검수판 manifest
         복숭아·포도 : datasets_reviewed_260916/<과일>/manifest.csv (칸 5개)
         사과·블루베리: datasets_reviewed_260917/<과일>/manifest.csv (칸 9개, session·split_group 포함)
    ② 그 위에 라벨링 툴의 «사람 판정» 을 덮는다
         data/<과일>/status.json 의 `confirmed` 칸  (= human_confirmed · **마스크** 확정)
         confirmed 가 없으면 `by` 가 «AI» 로 시작하지 않는 판정 (= human_unconfirmed ·
         **확정 칸 없이 사람이 누른 모든 판정** — 사이클2 이전 저장분도, 오늘 사람이 마스크만
         고쳐 저장한 것도 여기 들어온다. 2026-09-18 3차 결정 D2 로 human_legacy 에서 이름을 바꿨다)
         ok=남김 · fixed=masks_fixed 사용 · exclude=제외 · flag=제외(confirmed_flag)
       사람 판정이 없으면 검수판 판정 그대로. 사람이 ok 로 확정하면 검수판 제외도 되살린다.
    ③ 열매 번호(instances)·상자(boxes)도 있으면 같이 복사한다.
       🔴 2026-09-19 (툴 사이클 4 «종류별 확정» 반영 · 총괄 결정):
         확정 칸은 **세 개이고 서로 독립**이다(툴 app/server.py CONFIRM_KINDS).
           마스크 = `confirmed` · 상자 = `confirmed_boxes` · 번호 = `confirmed_instances`
         · 상자: `confirmed_boxes` 가 ok/fixed → 툴 `boxes/<stem>.json` 을 **사람 상자**로 채택
           (`boxes_source=tool`). exclude/flag → 그 사진의 상자는 **없음**(파일을 만들지 않는다).
           확정이 없으면 채택 순서는 **박성문 gt > 임성후** 이고, 확정 없는 툴 json 이
           비어 있지 않으면 `boxes_source=tool_unconfirmed` 로 **표시만** 한다(채택하지 않는다).
         · 번호: `confirmed_instances` 가 ok/fixed → `instances_fixed/`(없으면 원본 번호본)을
           채택하고 `instances_source=tool_confirmed`. exclude/flag → 번호 없음.
         · 마스크 `confirmed` 규칙은 **한 글자도 바뀌지 않았다.**

    입력(검수판·원본·툴 data)은 **한 글자도 쓰지 않는다**. 심볼릭 링크가 아니라 실제 복사다.

쓰는 법
    PY=/home/kds0206/.conda/envs/kwak/bin/python
    $PY tools/build_merged_dataset.py --dry-run      # 장수·제외 사유만 보여 주고 파일은 안 씀
    $PY tools/build_merged_dataset.py                # datasets_merged_<오늘>/ 을 만든다
    $PY tools/build_merged_dataset.py --date 260920  # 날짜를 직접 정할 때

안전장치
    · 만들 폴더가 이미 있으면 **바로 멈춘다**(exit 2). 같은 날 또 만들려면 --suffix 를 준다.
    · 다 만든 뒤 스스로 검사한다(이미지↔마스크 1:1 · 마스크 값 0/255 · 번호 ⊆ 마스크 · manifest 장수).
      한 가지라도 어긋나면 폴더 이름 뒤에 _INCOMPLETE 를 붙이고 exit 1.
    · 같은 입력이면 몇 번을 돌려도 manifest.csv 가 바이트까지 같다(시각은 build_summary.json 에만).
    · 직전 빌드에 «있음» 이던 입력이 이번에 «없음» 이면 **멈춘다**(exit 3). 그래도 만들어야 하면
      --allow-missing-input 을 준다. (2026-09-18 3차 결정 D3)

툴 규칙과의 관계
    마스크 우선순위(masks_fixed > 원본)와 «이진본이 번호본을 자른다» 는 툴
    app/instances.py 의 규칙이다. 여기서는 **함수를 부르지 않고 같은 규칙을 다시 구현**했다
    (독립 증거를 만들기 위해서다). 두 구현이 같은 집합을 내는지는
    tools/tests_merged_260918/test_build_merged.py 가 export/export_dataset.py 와 대조한다.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import time

import numpy as np
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

# ────────────────────────────────── 기본 경로
KDS = "/data/project/2026summer/kds0206"
WORK = "/data/project/2026summer/platform/work"
TOOL_ROOT = os.path.join(WORK, "kwak_dongsin/260916_라벨링툴")
# 🔴 2026-09-20 구조 사이클 2(시험 위생): 시험이 «지금» 의 공용 판정을 읽으면 사람이 툴에서
#   한 장을 확정할 때마다 손으로 적어 둔 숫자가 어긋난다(09-19 22:55 실측 977→975).
#   `MERGED_TOOL_DATA` 가 있으면 **얼려 둔 툴 자료**를 쓴다(`tests/merged/run_merged.sh` 가 만든다).
#   변수를 주지 않으면 예전과 한 글자도 다르지 않다(실제 빌드는 늘 지금 자료를 본다).
DEF_TOOL_DATA = (os.environ.get("MERGED_TOOL_DATA", "").strip()
                 or os.path.join(TOOL_ROOT, "data"))
DEF_REV916 = os.path.join(KDS, "datasets_reviewed_260916")
DEF_REV917 = os.path.join(KDS, "datasets_reviewed_260917")
DEF_ORIG = os.path.join(KDS, "datasets_resized_2mp")
# 팀원 산출물(전부 읽기 전용). 폴더가 통째로 없어도 «없음» 으로 적고 계속 간다.
DEF_PSM = os.path.join(WORK, "park_seongmoon")      # 박성문 — gt 상자·번호맵·사과 번호 점검
DEF_CIH = os.path.join(WORK, "choi_inhun")          # 최인훈 — 복숭아 중복 감사·마스크 감사
DEF_LSH = os.path.join(WORK, "im_seonghu")          # 임성후 — watershed 상자(09-07)

FRUITS = ["apple", "grape", "peach", "blueberry"]
REVIEWED_OF = {"peach": "260916", "grape": "260916", "apple": "260917", "blueberry": "260917"}
KOR = {"apple": "사과", "grape": "포도", "peach": "복숭아", "blueberry": "블루베리"}
# 툴이 쓰는 판정값(app/server.py STATUSES). unreviewed 는 «판정 없음» 이라 덮어쓰기에 쓰지 않는다
REAL_STATUS = ("ok", "fixed", "flag", "exclude")
# 2026-09-19: 확정 칸은 작업 **종류마다 따로**다 — 툴 app/server.py CONFIRM_KINDS 와 같은 이름·같은 뜻.
# 세 칸은 서로 독립이다(마스크를 확정해도 상자·번호는 «미확정» 그대로). 옛 자료에는 새 두 칸이 없다.
CONFIRM_KINDS = {"mask": "confirmed", "boxes": "confirmed_boxes",
                 "instances": "confirmed_instances"}
# 검출 팀이 만든 번호 초벌(읽기 전용) — 툴 app/instances.py SEED_DIRS 와 같은 값
# 🔴 2026-09-19 «개수 세기» **사이클5**(사이클4 2차 §7-1·§9-2 · 3차 §3 «데이터 결정»):
#   복숭아를 **더했다**. 툴은 사이클4 M1 에서 이미 박성문 님 워터셰드 번호본을 복숭아 초벌로 쓰는데
#   통합 빌더만 그것을 몰라서, 툴에서 «번호 확정» 을 해도 manifest 가 `count_source=none` 이었다
#   (사이클4 2차 `b2_export.py` ⑤-b′ 가 «알려진 틈» 으로 찍어 둔 자리).
#   ▶ **0920 빌드부터 복숭아에 `instances/` 가 생긴다**(그 전 판에는 없다). 번호본이 **있는** 사진은
#     125장이지만 **사람이 «제외» 로 확정한 사진은 빠진다** — 2026-09-19 22:55:23 에 한 장
#     (`210629-t2-of13-03`)이 «문제 있음» 으로 확정돼 **실측 124장**이다(사이클5 2차 23:01).
#     0920 에 장수를 **다시 세라** — 사람이 더 누르면 더 줄어든다.
#   ▶ 그 번호는 **사람이 검수한 정답이 아니라 추정**이다 — 블루베리(`detect_seed`)와 같은 성격이고,
#     누가 만든 것인지 한눈에 보이게 값을 `psm_watershed` 로 따로 적는다(README «값 사전» 참조).
#   포도(CERTH 정답 송이)는 **넣지 않는다** — 교수님 확인 8번(포도 «송이» 정의)이 미결이고
#   툴도 같은 이유로 꺼 두었다(`app/instances.py` SEED_DIRS 주석).
PARK_SEED = "/data/project/2026summer/platform/work/park_seongmoon/bbox_outputs/%s/all/instance_maps"
SEED_DIRS = {"blueberry": PARK_SEED % "blueberry", "peach": PARK_SEED % "peach"}
# 그 초벌이 manifest `instances_source` 에 어떤 낱말로 들어가나(과일마다 다르게 적는 까닭은 위 주석).
# 블루베리는 예전 값을 **그대로** 둔다 — 값이 바뀌면 지난 빌드와 대조할 수 없다.
SEED_LABELS = {"blueberry": "detect_seed", "peach": "psm_watershed"}

MANIFEST_COLS = ["fruit", "stem", "image_source", "mask_source", "action", "reason", "note",
                 "source", "confirmed_by", "confirmed_at", "session", "split_group",
                 "has_instances", "has_boxes",
                 # 계획서 §3-4 의 14칸 **뒤에** 덧붙인 칸 — 검수판·팀원 산출물의 정보를 잃지 않으려는 것이다
                 "rule_pending", "overlap_neighbors", "instances_source",
                 # 2026-09-18 17:42 지시 — 팀원 산출물 반영
                 "boxes_source", "apple_check_verdict", "verdict_source",
                 "peach_dup_candidate", "mask_audit_reason",
                 # 2026-09-19 — 툴의 «종류별 확정»(상자·번호). 마스크 확정은 위 source·confirmed_by/at 이다.
                 # 값이 없으면 status 칸에 «-» 를 적는다(빈칸과 «확정 없음» 을 눈으로 구별하려는 것).
                 "boxes_confirmed_status", "boxes_confirmed_by", "boxes_confirmed_at",
                 "instances_confirmed_status",
                 # 2026-09-19 5차 — 팀 표준 2MP 규격에 맞추려고 크기를 바꾼 것(맞춘 것이 없으면 «-»)
                 "spec_fixed",
                 # 2026-09-19 «개수 세기» 사이클1 — 이 사진에 열매가 몇 개인가. 뺀 사진은 «-».
                 # n_boxes·n_instances 는 **이 폴더에 실제로 나간 파일**을 센 값이다(툴 저장분이 아니라).
                 "n_boxes", "n_instances", "n_count_human", "count_source", "count_conflict",
                 # 2026-09-19 사이클2 논문대조 1차: 정답 개수가 없으면 MAE·RMSE·R²
                 # (farjon2023countingreview p.16 식 (1)~(4))를 셀 수 없다.
                 "n_gt"]
# «출처» 칸은 빈칸을 두지 않는다(없으면 none / 뺀 사진은 -). 시험이 «빈 행 0» 을 본다.
SOURCE_COLS = ["source", "image_source", "mask_source", "instances_source",
               "boxes_source", "verdict_source"]

REASON_KOR = {
    "reviewed_duplicate": "검수판: 거의 같은 사진(대표만 남김)",
    "reviewed_not_grape": "검수판: 포도 사진이 아님",
    "human_exclude": "사람이 «제외» 로 판정",
    "confirmed_flag": "사람이 «문제 있음» 으로 판정(고치기 전이라 뺌)",
    "missing_image": "이미지 파일을 어디에서도 찾지 못함",
    "missing_mask": "마스크 파일을 어디에서도 찾지 못함",
    "spec_mismatch_ratio": "팀 표준 2MP 규격과 가로세로비가 0.5% 넘게 달라 쓰지 못함",
}


# ────────────────────────────────── 작은 도구들
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime_str(path):
    if not os.path.exists(path):
        return ""
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")


def natkey(s):
    """포도 stem 은 숫자 문자열이라 «2, 10» 이 «10, 2» 로 정렬되지 않게 한다(결과 재현성)."""
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s))


def load_mask_bool(path):
    """어떤 형식이든 «0보다 크면 전경» 으로 읽는다(툴 app/maskio.load_mask_bool 과 같은 규칙)."""
    with Image.open(path) as im:
        im = im.copy() if im.mode in ("L", "I;16", "I", "1") else im.convert("L")
        a = np.array(im)
    if a.ndim == 3:
        a = a.max(axis=2)
    return a > 0


def save_mask_255(path, arr_bool):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 🔴 2026-09-19 검수2 N4: `mode=` 인자는 Pillow 13(2026-10-15)에서 없어진다.
    #    uint8 배열은 Pillow 가 스스로 "L" 을 고르므로 인자를 빼도 결과는 **바이트까지 같다**.
    Image.fromarray((np.asarray(arr_bool).astype(np.uint8)) * 255).save(path, format="PNG")


def read_u16(path):
    with Image.open(path) as im:
        a = np.array(im)
    if a.ndim == 3:
        a = a[:, :, 0]
    return a.astype(np.uint32)


def write_u16(path, arr):
    """번호 마스크를 16비트 PNG 로 저장.

    🔴 2026-09-19 검수2 N4: 예전에는 `Image.fromarray(arr.astype("<u2"), mode="I;16")` 이었다.
    그 `mode=` 인자는 Pillow 12 에서 **DeprecationWarning** 을 내고 **Pillow 13(2026-10-15)에서
    없어진다** — 그러면 번호 마스크를 쓰는 모든 빌드가 멈춘다. 인자를 빼면 Pillow 가 uint16
    배열에서 스스로 `I;16` 을 고르고, 저장된 PNG 는 **바이트까지 같다**(실측 확인).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint16)).save(path, format="PNG")


def ids_of(arr):
    v = np.unique(arr)
    return v[v > 0]


def src_of(rec):
    """그 판정을 누가 넣었나 — 툴 app/server.py src_of 와 **같은 규칙**.

    `src` 칸은 이미 «어느 단추가 제외했나»(dup_bulk 등)로 쓰이고 있으므로 ai/human 일 때만 믿고,
    그 밖이면 `by` 가 «AI» 로 시작하는지로 판단한다.
    """
    v = (rec or {}).get("src")
    if v in ("ai", "human"):
        return v
    return "ai" if str((rec or {}).get("by") or "").startswith("AI") else "human"


def human_verdict(rec):
    """이 사진에 «사람 판정» 이 있나 → (판정, 어디서, by, at, note) · 없으면 (None, …).

    ① confirmed 칸이 있으면 그것(= human_confirmed)
    ② 없으면 by 가 «AI» 로 시작하지 않는 판정(= human_unconfirmed · **확정 칸 없이 사람이 누른 모든 판정**.
       사이클2 이전 저장분뿐 아니라 오늘 사람이 마스크만 고쳐 저장한 것도 여기 들어온다)
    둘 다 status 가 unreviewed 면 «판정을 지운 것» 이므로 덮어쓰지 않는다.
    """
    if not isinstance(rec, dict):
        return None, None, "", "", ""
    c = rec.get("confirmed")
    if isinstance(c, dict) and c.get("status") in REAL_STATUS:
        return c["status"], "human_confirmed", c.get("by", ""), c.get("at", ""), c.get("note", "")
    if isinstance(c, dict):                      # confirmed 는 있는데 unreviewed — 사람이 판정을 지웠다
        return None, "confirmed_unreviewed", c.get("by", ""), c.get("at", ""), c.get("note", "")
    if src_of(rec) == "human" and rec.get("status") in REAL_STATUS:
        return rec["status"], "human_unconfirmed", rec.get("by", ""), rec.get("at", ""), rec.get("note", "")
    if src_of(rec) == "human":
        return None, "human_cleared", rec.get("by", ""), rec.get("at", ""), rec.get("note", "")
    return None, None, "", "", ""


def confirmed_kind(rec, kind):
    """**종류별** 사람 확정 → (판정, by, at, note) · 없으면 (None, "", "", "").

    툴 app/server.py `confirmed_of(rec, kind)` 와 같은 칸(`CONFIRM_KINDS`)을 본다. 다른 점 하나:
    툴은 `unreviewed` 도 «확정 객체» 로 돌려주지만(값 검사가 STATUSES 이므로) 여기서는
    `unreviewed` 를 **확정 없음**으로 본다 — 마스크 쪽 `human_verdict()` 가 예전부터
    «confirmed 는 있는데 unreviewed = 사람이 판정을 지웠다» 로 다루던 것과 같은 규칙이다.
    """
    c = (rec or {}).get(CONFIRM_KINDS[kind]) if isinstance(rec, dict) else None
    if isinstance(c, dict) and c.get("status") in REAL_STATUS:
        return c["status"], c.get("by", ""), c.get("at", ""), c.get("note", "")
    return None, "", "", ""


# ────────────────────────────── 개수 칸 (2026-09-19 «개수 세기» 사이클1, 지시서 §1-4)
# ⚠ 이것은 툴 `app/boxes.py human_count()` 를 **일부러 다시 구현한 것**이다(지시서가 그렇게 시켰다).
#    이 스크립트는 툴의 app/ 을 import 하지 않는다(다른 파이썬 환경에서도 돌아야 한다). 두 구현이
#    갈라지지 않는지는 시험 `tools/tests_merged_260918/counts/test_counts.py` 가 **같은 입력을 두
#    구현에 넣어** 대조한다(툴 export/export_dataset.py 의 counts_rows 와도 대조한다).
# 규칙(툴과 한 글자도 같아야 하는 것):
#   ① 번호 확정(ok·fixed)이 있고 번호 수를 알면 → 번호 수 (count_source=instances)
#   ② 아니면 상자 확정(ok·fixed)이 있고 상자 수를 알면 → 상자 수 (count_source=boxes)
#   ③ 둘 다 없으면 → 없음 (count_source=none · 툴은 빈 문자열, 여기는 다른 «출처» 칸과 맞춰 none)
#   둘 다 확정됐는데 수가 다르면 **비운다**(`count_source=conflict` · `count_conflict=1`) —
#   툴 `app/boxes.py human_count()` 와 같은 규칙이다(0919 사이클1 3차 총괄 결정 1).
#   ⚠ 0919 «개수 세기» 사이클5 **2차 정정**: 이 줄은 «①을 쓰되» 라고 적혀 있어 아래 코드
#   (`count_cells` 의 `conflict` 갈래 — 비운다)와 **반대 말을 하고 있었다**. 코드가 옳다.
def count_cells(row):
    """`row` 의 `n_boxes`·`n_instances`·확정 칸을 보고 개수 세 칸을 채운다(같은 row 를 돌려준다).

    n_boxes·n_instances 는 write_fruit 가 **실제로 나간 파일을 세어** 넣은 문자열이고, 없으면 빈칸
    (= «셀 수 없음»)이다. 0 과 빈칸은 다르다 — 0 은 «열매가 없다», 빈칸은 «파일이 없다» 다.
    """
    nb, ni = row.get("n_boxes", ""), row.get("n_instances", "")
    ok_b = row.get("boxes_confirmed_status") in ("ok", "fixed") and nb not in ("", "-", None)
    ok_i = row.get("instances_confirmed_status") in ("ok", "fixed") and ni not in ("", "-", None)
    conflict = bool(ok_b and ok_i and str(nb) != str(ni))
    if conflict:
        # 🔴 2026-09-19 «개수 세기» 사이클1 **3차 전 총괄 결정 1**: 둘 다 확정됐는데 수가 다르면
        # **비운다**(전에는 번호 수를 그대로 적었다). 사람이 16과 15 중 어느 쪽인지 고르지 않은 수를
        # MAE·RMSE·R² 표에 넣으면 그것이 사후 정당화다. 툴 `app/boxes.py human_count()` 와 같은 규칙.
        row["n_count_human"], row["count_source"] = "", "conflict"
    elif ok_i:
        row["n_count_human"], row["count_source"] = ni, "instances"
    elif ok_b:
        row["n_count_human"], row["count_source"] = nb, "boxes"
    else:
        row["n_count_human"], row["count_source"] = "", "none"
    row["count_conflict"] = "1" if conflict else "0"
    return row


# 검출 팀 박성문 님의 «정답 상자» 표(읽기 전용). 한 줄 = 상자 하나 → 사진마다 줄을 센다.
# blueberry 는 gt_boxes 가 **없다**(`all/` 은 watershed 자동 추정이라 정답이 아니다) → 빈칸.
# 툴 `export/export_dataset.py gt_counts()` 와 같은 파일·같은 세는 법이다.
def gt_counts(psm_root, fruit):
    """{stem: 정답 상자 수} — 파일이 없거나 못 읽으면 빈 딕셔너리."""
    p = os.path.join(psm_root, "bbox_outputs", fruit, "gt_boxes", "csv", "detections.csv")
    out = {}
    if not os.path.exists(p):
        return out
    try:
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                n = (r.get("image_name") or "").strip()
                if n.lower().endswith(".png"):
                    n = n[:-4]
                if n:
                    out[n] = out.get(n, 0) + 1
    except Exception:
        return {}
    return out


def n_box_in(path):
    """상자 json 한 개에 상자가 몇 개인가 — 툴 형식(boxes)과 검출 팀 형식(detections)을 둘 다 센다.
    못 읽으면 None."""
    d = read_json(path, None)
    if not isinstance(d, dict):
        return None
    v = d.get("boxes")
    if v is None:
        v = d.get("detections")
    return len(v) if isinstance(v, list) else None


def read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return default
    return d


# ────────────────────────────────── 규격(팀 표준 2MP) 검사·맞춤   ← 2026-09-19 5차
# 팀 표준은 `datasets_resized_2mp/` 이고, 그것을 만든 규칙은
# `tools/resize_datasets_to_common_pixels.py`(0806 교수님미팅 지시) 이다. 그대로 베껴 온다.
#   · 비율(가로세로)을 유지한다
#   · 총 화소 수를 1440x1440 = 2,073,600 에 가장 가깝게 맞춘다
#   · 변의 길이는 8의 배수로 반올림한다 → 실제로 쓰이는 해상도는 5종뿐이다
#       1440x1440 · 1920x1080 · 1080x1920 · 1664x1248 · 1248x1664
#     (앞 세 종은 정확히 2,073,600. 1664x1248 은 2,076,672 = +0.148% 로 ±0.15% 안이다)
#   · 이미지는 LANCZOS · 마스크·번호는 **NEAREST**(보간하면 없는 라벨값이 생긴다)
SPEC_TARGET_PIXELS = 1440 * 1440        # 2,073,600
SPEC_MULTIPLE = 8
SPEC_PIXEL_TOL = 0.0015                 # 총 화소 ±0.15%
SPEC_RATIO_TOL = 0.005                  # 가로세로비 0.5% — 넘으면 맞추지 않고 채택도 하지 않는다
SPEC_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")
SPEC_KINDS = ("image", "mask", "instances", "boxes")


def img_size_of(path):
    """헤더만 읽어 **화면에 보이는** (w,h). 못 읽으면 None.

    🔴 2026-09-19 검수1: EXIF 회전을 반영한다 — 원래 규칙(`resize_datasets_to_common_pixels.py`
    의 `exif_size()`)이 그렇게 세기 때문이다. 반영하지 않으면 회전 정보가 붙은 사진(휴대전화
    사진·eXIf 청크가 있는 PNG)에서 4032x3024 로 읽고, 정작 리사이즈는 회전 반영한 3024x4032 을
    1664x1248 로 **찌그러뜨린다**(검수1 X1 에서 77.8% 왜곡을 실제로 재현했다).
    화소는 여전히 읽지 않는다(4,823장 0.5초 이내).
    """
    if not path or not os.path.exists(path):
        return None
    try:
        with Image.open(path) as im:
            w, h = im.size
            orientation = exif_orientation(im)
    except Exception:
        return None
    return (h, w) if orientation in (5, 6, 7, 8) else (w, h)


def exif_orientation(im):
    """열어 둔 이미지의 EXIF 회전값(1~8). **화소를 읽지 않는다.**

    `im.getexif()` 를 쓰면 안 된다 — PNG 는 eXIf 청크가 IDAT 뒤에 올 수 있어서 Pillow 가
    그림 전체를 풀어 버린다(4,823장이 3.8초 → 몇 분으로 늘어나는 것을 실측했다).
    JPEG·PNG 모두 `open()` 단계에서 `info["exif"]` 에 원본 바이트가 들어오므로 그것만 푼다.
    """
    raw = im.info.get("exif")
    if not raw:
        return 1
    try:
        ex = Image.Exif()
        ex.load(raw)
        return int(ex.get(0x0112, 1) or 1)
    except Exception:
        return 1


def find_image(dirpath, stem):
    """<dirpath>/<stem>.* 에서 이미지 하나를 찾는다(확장자는 SPEC_EXTS 순서)."""
    for e in SPEC_EXTS:
        q = os.path.join(dirpath, stem + e)
        if os.path.exists(q):
            return q
    return None


def spec_target_size(w, h, target_px=SPEC_TARGET_PIXELS, multiple=SPEC_MULTIPLE):
    """`resize_datasets_to_common_pixels.py` 의 `target_size()` 와 **글자 하나까지 같은 식**."""
    scale = (target_px / (w * h)) ** 0.5
    nw = max(multiple, int(round(w * scale / multiple)) * multiple)
    nh = max(multiple, int(round(h * scale / multiple)) * multiple)
    return nw, nh


def spec_pixels_ok(w, h):
    return abs(w * h - SPEC_TARGET_PIXELS) <= SPEC_TARGET_PIXELS * SPEC_PIXEL_TOL


def spec_is_rule_pair(src_wh, std_wh):
    """`src_wh` 를 원래 규칙에 넣으면 바로 `std_wh` 가 나오는가.

    🔴 2026-09-19 검수1 X6: 8의 배수 반올림은 비율을 최대 ~1% 까지 바꿀 수 있다(예 6292x2503
    → 2280x912 는 0.55% 어긋난다). 그러면 «0.5% 넘게 다르다» 는 게이트가 **원래 규칙이 만든
    표준 자신을** 규격 위반으로 몰아낸다. 규칙의 출력인 것이 확인되면 규격 위반이 아니다."""
    try:
        return tuple(spec_target_size(int(src_wh[0]), int(src_wh[1]))) == tuple(std_wh)
    except Exception:
        return False


def spec_ratio_ok(src_wh, std_wh):
    """이 크기를 표준으로 맞춰도 되는가 = 비율이 0.5% 안이거나, 원래 규칙의 짝이거나."""
    return ratio_close(src_wh, std_wh) or spec_is_rule_pair(src_wh, std_wh)


def photo_thumb(path, n=32):
    """«같은 사진인가» 만 보기 위한 32x32 회색 축소판. 실패하면 None."""
    try:
        with Image.open(path) as im:
            t = ImageOps.exif_transpose(im).convert("L").resize((n, n), Image.LANCZOS)
        return np.asarray(t, dtype=np.float64)
    except Exception:
        return None


def same_photo(a, b, tol=8.0):
    """두 파일이 **같은 사진**인가(크기가 달라도 된다). 평균 밝기차가 tol(0~255) 안이면 같다고 본다."""
    ta, tb = photo_thumb(a), photo_thumb(b)
    if ta is None or tb is None:
        return False
    return float(np.abs(ta - tb).mean()) <= tol


def ratio_close(a, b, tol=SPEC_RATIO_TOL):
    """두 크기의 가로세로비가 tol 안에서 같은가."""
    if not a or not b or 0 in a or 0 in b:
        return False
    return abs((a[0] / a[1]) / (b[0] / b[1]) - 1.0) <= tol


def wh(t):
    return "%dx%d" % (t[0], t[1])


def build_spec_table(fruit, args, stems, rev_dir):
    """이 과일의 **팀 표준 크기표** — stem → (w,h).

    1순위 `datasets_resized_2mp/<과일>/images/<stem>.*` (= 팀 표준 그 자체)
    2순위 검수판 이미지 (원본 폴더에 그 stem 이 없을 때. 검수판은 표준에서 뜬 것이라 같은 크기다)
    둘 다 없으면 표에 넣지 않는다(그 사진은 규격을 견줄 기준이 없으므로 맞추지 않고 `no_std` 로 적는다).

    헤더만 읽으므로 4,823장이 1초 안에 끝난다.
    """
    std, std_src, no_std = {}, {}, []
    odir = os.path.join(args.original_root, fruit, "images")
    rdir = os.path.join(rev_dir, "images")
    for s in stems:
        sz = img_size_of(find_image(odir, s))
        if sz:
            std[s], std_src[s] = sz, "resized_2mp"
            continue
        sz = img_size_of(find_image(rdir, s))
        if sz:
            if spec_pixels_ok(*sz):
                std[s], std_src[s] = sz, "reviewed"
            else:
                # 검수판 이미지마저 **원본 해상도**다 → 원래 규칙(비율 유지·2MP·8의 배수)으로 계산한다.
                std[s], std_src[s] = spec_target_size(*sz), "computed"
            continue
        no_std.append(s)
    return std, std_src, no_std


def box_json_size(kind, path):
    """상자 json 이 «어느 크기의 사진» 을 기준으로 쓰였나 → (w,h) 또는 None.

    툴 json  : `width`·`height`          (app/boxes.py)
    박성문·임성후: `image_size_hw` = [h,w]  (bbox_outputs/*/json)
    """
    rec = read_json(path, {})
    if not isinstance(rec, dict):
        return None
    if kind == "tool":
        w, h = rec.get("width"), rec.get("height")
    else:
        hw = list(rec.get("image_size_hw") or [])
        h, w = (hw + [None, None])[:2]
    try:
        w, h = int(w), int(h)
    except (TypeError, ValueError):
        return None
    return (w, h) if w > 0 and h > 0 else None


def nn_resize_u16(arr, to_wh):
    """uint16 번호 마스크를 **최근접 보간**으로 크기 변경. PIL 의 I 모드 NEAREST 를 쓴다
    (보간이 섞이면 없는 번호가 생긴다). 값 집합은 부분집합으로만 줄어들 수 있다."""
    # 🔴 2026-09-19 검수2 N4: `mode="I"` 를 뺐다(Pillow 13 에서 없어지는 인자).
    #    int32 배열은 Pillow 가 스스로 "I" 를 고른다 — 결과 배열은 그대로다.
    im = Image.fromarray(np.asarray(arr).astype(np.int32))
    return np.array(im.resize((int(to_wh[0]), int(to_wh[1])), Image.NEAREST)).astype(np.uint32)


def nn_resize_mask(m, to_wh):
    """0/255 이진 마스크를 **최근접 보간**으로 크기 변경(원래 리사이즈 규칙과 같다)."""
    im = Image.fromarray((np.asarray(m).astype(np.uint8)) * 255)   # 검수2 N4: mode= 없이(Pillow 13)
    return np.array(im.resize((int(to_wh[0]), int(to_wh[1])), Image.NEAREST)) > 0


def resize_image_to_spec(src, dst, to_wh):
    """사진을 표준 크기로. 원래 규칙과 같은 **LANCZOS**. EXIF 회전도 원래 규칙대로 반영한다."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        out = im.resize((int(to_wh[0]), int(to_wh[1])), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst, format="PNG")


def scale_box_json(kind, src, dst, from_wh, to_wh):
    """상자 json 의 **픽셀 좌표**를 표준 크기에 맞춰 비율 변환해 새로 쓴다(원본 json 은 읽기만).

    YOLO txt 는 0~1 정규화 좌표라 균일 배율에는 바뀌지 않으므로 손대지 않는다.
    면적(`area_pixels`)은 두 배율의 곱으로 바꾼다.
    """
    rec = read_json(src, {})
    sx, sy = to_wh[0] / from_wh[0], to_wh[1] / from_wh[1]

    def pt(vals, muls):
        return [round(v * m, 2) for v, m in zip(vals, muls)]

    if kind == "tool":
        rec["width"], rec["height"] = int(to_wh[0]), int(to_wh[1])
        for b in rec.get("boxes") or []:
            if "xyxy" in b:
                b["xyxy"] = pt(b["xyxy"], (sx, sy, sx, sy))
    else:
        rec["image_size_hw"] = [int(to_wh[1]), int(to_wh[0])]
        for d in rec.get("detections") or []:
            if "bbox_xyxy" in d:
                d["bbox_xyxy"] = pt(d["bbox_xyxy"], (sx, sy, sx, sy))
            if "bbox_xywh" in d:
                d["bbox_xywh"] = pt(d["bbox_xywh"], (sx, sy, sx, sy))
            if "center" in d and isinstance(d["center"], (list, tuple)) and len(d["center"]) == 2:
                d["center"] = pt(d["center"], (sx, sy))
            if isinstance(d.get("area_pixels"), (int, float)):
                d["area_pixels"] = round(d["area_pixels"] * sx * sy, 2)
    rec["spec_fixed"] = "%s->%s" % (wh(from_wh), wh(to_wh))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False)


def yolo_range_bad(path, eps=1e-6):
    """YOLO txt 의 값이 0~1 밖으로 나가면 그 줄을 돌려준다(빈 목록이면 통과)."""
    out = []
    try:
        with open(path) as f:
            for i, ln in enumerate(f, 1):
                t = ln.split()
                if not t:
                    continue
                if len(t) != 5:
                    out.append("%d행 칸이 5개가 아님: %r" % (i, ln.strip()))
                    continue
                try:
                    v = [float(x) for x in t[1:]]
                except ValueError:
                    out.append("%d행 숫자가 아님: %r" % (i, ln.strip()))
                    continue
                if any(x < -eps or x > 1 + eps for x in v):
                    out.append("%d행 0~1 밖: %r" % (i, ln.strip()))
    except Exception as e:
        out.append("읽지 못함: %s" % e)
    return out


# ────────────────────────────────── 팀원 산출물 (전부 읽기 전용 · 없으면 «없음» 으로 넘어간다)
def owner_of(path):
    try:
        import pwd
        return pwd.getpwuid(os.stat(path).st_uid).pw_name
    except Exception:
        return ""


def count_rows(path):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return None


def reg_add(reg, key, path, used_for):
    """입력 하나를 «출처 등록표» 에 적는다. 없으면 exists=False 로 적고 그대로 진행한다."""
    e = {"path": path, "used_for": used_for, "exists": os.path.exists(path)}
    if e["exists"]:
        e["owner"] = owner_of(path)
        if os.path.isdir(path):
            names, latest, lines = [], 0.0, []
            with os.scandir(path) as it:
                for x in it:
                    names.append(x.name)
                    try:
                        st = x.stat()
                        latest = max(latest, st.st_mtime)
                        lines.append((x.name, st.st_size, int(st.st_mtime * 1e6)))
                    except OSError:
                        lines.append((x.name, -1, -1))
            e["kind"], e["n_files"] = "dir", len(names)
            # 2026-09-18 3차 D4: 폴더 지문 = 파일 목록(이름·크기·mtime)의 sha256.
            # 파일 수와 최신 시각이 같은 채 «안쪽 한 파일만» 바뀌어도 이것으로 잡힌다.
            h = hashlib.sha256()
            for nm, sz, mt in sorted(lines):
                h.update(("%s\x00%d\x00%d\n" % (nm, sz, mt)).encode("utf-8", "surrogateescape"))
            e["sha256"] = h.hexdigest()
            e["fingerprint"] = "names+size+mtime"
            e["latest_mtime"] = (datetime.datetime.fromtimestamp(latest)
                                 .strftime("%Y-%m-%d %H:%M:%S") if latest else mtime_str(path))
        else:
            e["kind"], e["size"] = "file", os.path.getsize(path)
            e["mtime"] = mtime_str(path)
            if e["size"] <= 5 << 20:
                e["sha256"] = sha256_of(path)
                e["fingerprint"] = "content"       # 2026-09-18 3차 D4: 파일은 내용 해시
            if path.endswith(".csv"):
                e["n_rows"] = count_rows(path)
    reg[key] = e
    return e


def load_apple_check(psm_root):
    """박성문 `apple_check/` — 사람이 사과 열매 번호 오류를 눈으로 판정한 결과.

    review_list.csv(전부) + confirmed_errors.csv(확정된 오류)를 사진(stem)마다 모은다.
    돌려주는 것: {stem: (판정 요약, 어디서 왔나)}
    """
    out = {}
    rl = os.path.join(psm_root, "apple_check", "review_list.csv")
    ce = os.path.join(psm_root, "apple_check", "confirmed_errors.csv")
    per = collections.defaultdict(collections.Counter)
    conf = collections.defaultdict(collections.Counter)
    for path, bag in ((rl, per), (ce, conf)):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                s, v = (r.get("stem") or "").strip(), (r.get("verdict") or "").strip()
                if s and v:
                    bag[s][v] += 1
    for s in set(per) | set(conf):
        c = per.get(s) or conf.get(s)
        txt = " ".join("%s=%d" % kv for kv in sorted(c.items()))
        if s in per and s in conf:
            src = "psm_review_list+confirmed_errors"
        elif s in per:
            src = "psm_review_list"
        else:
            src = "psm_confirmed_errors"
        if s in conf:
            txt += " · 확정오류 %d" % sum(conf[s].values())
        out[s] = (txt, src)
    return out


PEACH_BURST = re.compile(r"^(\d{6}-t\d+-of\d+)-\d+$")


def load_peach_dup(cih_root):
    """최인훈 `dup_audit_260917/peach/` — 복숭아 중복 «후보». **제외하지 않는다.**

    ① REPORT.md §1 의 버스트 촬영 = 파일명 `210629-t2-ofNN-*` (9그룹 45장, 사람이 눈으로 확인).
       → 그룹 id `burst_ofNN`.
    ② similar_pairs.csv 중 **dhash 해밍 ≤ 22 이고 히스토그램 거리 ≤ 0.17** 인 쌍
       (= REPORT §2 표가 다루는 범위)을 버스트가 아닌 사진끼리만 이어 `pair_NN` 그룹으로.
       버스트 그룹에 든 사진은 ①이 이깁니다(두 신호를 섞으면 9그룹이 한 덩어리로 뭉개집니다).
    """
    base = os.path.join(cih_root, "dup_audit_260917", "peach")
    pairs_csv = os.path.join(base, "similar_pairs.csv")
    out, pairs = {}, []
    n_cross = 0
    if not os.path.isdir(base):
        return out, {"exists": False}
    burst = {}
    if os.path.exists(pairs_csv):
        with open(pairs_csv, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                # 2026-09-18 2차 검수 M2-2: 칸이 없거나 줄이 잘린 CSV 에 멈추지 않는다.
                # (잘린 similar_pairs.csv 는 DictReader 가 None 을 주고 float(None) 이 TypeError 로 터졌다)
                a, b = (r.get("a") or ""), (r.get("b") or "")
                if not (a and b):
                    continue
                a = a[:-4] if a.endswith(".png") else a
                b = b[:-4] if b.endswith(".png") else b
                for s in (a, b):
                    m = PEACH_BURST.match(s)
                    if m:
                        burst[s] = "burst_" + m.group(1).split("-")[-1]
                try:
                    if int(r["dhash_ham"]) <= 22 and float(r["hist_dist"]) <= 0.17:
                        # 2026-09-18 2차 검수 M2-1(누수): **같은 촬영(session) 안의 쌍만** 잇는다.
                        # REPORT.md §2 는 «시리즈 내 근접 프레임», §3 은 시리즈를 가로지른 쌍을
                        # «오탐 — 중복 아님, 유지» 로 못박았다. 문턱만으로 이으면 t2↔t4 처럼
                        # 나무가 다른 쌍(210629-t2-07 ↔ 210629-t4-20, hist 0.1545)이 한 그룹이 되고,
                        # 그 그룹이 split_group 두 개로 갈려 «중복 후보가 학습·시험으로 갈라지는»
                        # 누수를 만든다(2차 검수 실측). 가로지른 쌍은 세지만 잇지 않는다.
                        if peach_session(a) == peach_session(b):
                            pairs.append((a, b))
                        else:
                            n_cross += 1
                except (ValueError, KeyError, TypeError):
                    pass
    # 버스트 그룹은 파일명만으로 정해진다 — similar_pairs 에 안 나온 장도 넣는다(REPORT §1 그대로)
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for a, b in pairs:
        if not (PEACH_BURST.match(a) or PEACH_BURST.match(b)):
            par[find(b)] = find(a)
    comp = collections.defaultdict(list)
    for x in list(par):
        comp[find(x)].append(x)
    for i, (_, xs) in enumerate(sorted(comp.items(), key=lambda kv: min(kv[1])), 1):
        if len(xs) >= 2:
            for s in xs:
                out[s] = "pair_%02d" % i
    out.update(burst)                      # 버스트가 이긴다
    return out, {"exists": True, "n_pairs_used": len(pairs), "n_burst": len(burst),
                 "n_pairs_cross_session_skipped": n_cross,
                 "n_pair_groups": len({v for v in out.values() if v.startswith("pair_")})}


def load_mask_audit(cih_root):
    """최인훈 `mask_audit_260908/` — «의심 마스크».

    ⚠ 실측(2026-09-18): `mask_stats.csv` 에는 `reason` 칸이 **없다**(전체 4,823장의 통계표).
       `reason` 칸이 있는 것은 **`suspects.csv`**(240행, 전부 `bottom_5pct_ratio`)다.
       그래서 의심 사유는 suspects.csv 에서 읽고, mask_stats.csv 는 등록만 한다.
    """
    out = {}
    p = os.path.join(cih_root, "mask_audit_260908", "suspects.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                stem = (r.get("mask") or "")
                stem = stem[:-4] if stem.endswith(".png") else stem
                if stem and (r.get("reason") or "").strip():
                    out[(r.get("fruit", ""), stem)] = r["reason"].strip()
    return out


def box_index(fruit, args):
    """이 과일의 상자 후보를 **두 벌로 나눠** 모은다(2026-09-19 종류별 확정).

    돌려주는 것: (base, tool, 통계)
      base = {stem: (출처, json, yolo txt 또는 None)} — 박성문 gt > 임성후. 사람 확정과 무관한
             «정답/추정» 상자다.
      tool = {stem: (json 경로, 상자 개수)} — 툴 `boxes/` 에 있는 것 **전부**(빈 것도 담는다).
             채택할지는 `confirmed_boxes` 를 보고 plan_fruit 가 정한다.

    ⛔ 예전 판은 이 함수 안에서 «툴이 최우선» 으로 덮어썼다. 그러면 사람이 **확정하지 않은**
       초벌 저장본이 박성문 정답 상자를 밀어낸다(2차 검수 M2-7 이 빈 json 만 막았던 자리다).
       이제 확정 여부는 여기서 알 수 없으므로(상태 파일은 plan_fruit 가 읽는다) 덮지 않는다.
    """
    idx, stat = {}, {}
    lsh = os.path.join(args.lsh_root, "bbox_outputs", fruit, "all", "json")
    psm = os.path.join(args.psm_root, "bbox_outputs", fruit, "gt_boxes")
    tool = os.path.join(args.tool_data, fruit, "boxes")
    if os.path.isdir(lsh):
        for fn in os.listdir(lsh):
            if fn.endswith(".json"):
                idx[fn[:-5]] = ("lsh", os.path.join(lsh, fn), None)
    stat["lsh"] = len(idx)
    n_psm = 0
    if os.path.isdir(os.path.join(psm, "json")):
        for fn in os.listdir(os.path.join(psm, "json")):
            if not fn.endswith(".json"):
                continue
            t = os.path.join(psm, "yolo_labels", fn[:-5] + ".txt")
            idx[fn[:-5]] = ("psm_gt", os.path.join(psm, "json", fn), t if os.path.exists(t) else None)
            n_psm += 1
    stat["psm_gt"] = n_psm
    tidx = {}
    n_tool = n_tool_empty = 0
    if os.path.isdir(tool):
        for fn in os.listdir(tool):
            if fn.endswith(".json") and fn != "boxes_all.json":
                # 2026-09-18 2차 검수 M2-7(데이터 소실): **상자가 하나도 없는** 툴 파일이
                # 박성문 gt 를 밀어내어 정답 상자 9개·4개가 사라졌다(v2 실측: grape/740 ·
                # peach/210629-t4-17 — by=«자동시험 정리(검수C1B)»·«검수C2B 되돌림», 사람이
                # 그린 것이 아니라 툴 자동시험이 남긴 껍데기). 이제는 **세어만 두고**,
                # 채택 여부는 `confirmed_boxes` 를 본 plan_fruit 가 정한다.
                n = len((read_json(os.path.join(tool, fn), {}) or {}).get("boxes") or [])
                tidx[fn[:-5]] = (os.path.join(tool, fn), n)
                if n:
                    n_tool += 1
                else:
                    n_tool_empty += 1
    stat["tool"] = n_tool                       # 툴 json 중 **상자가 있는** 것
    stat["tool_empty_skipped"] = n_tool_empty   # 빈 껍데기(확정이 없으면 여전히 무시한다)
    stat["overlap_psm_lsh"] = n_psm and stat["lsh"] and len(
        set(os.listdir(os.path.join(psm, "json"))) & set(os.listdir(lsh))) or 0
    return idx, tidx, stat


def yolo_from_detect_json(src_json, dst_txt):
    """박성문·임성후 형식(json)의 상자를 YOLO txt 로. 클래스는 0(fruit) 하나.

    `bbox_xywh`(폭·높이를 포함으로 센 값)를 그대로 쓴다 — 박성문이 `gt_boxes/yolo_labels/` 를
    만든 방식과 **같은 숫자**가 나온다(2026-09-18 대조로 확인).
    """
    rec = read_json(src_json, {})
    h, w = (rec.get("image_size_hw") or [1, 1])[:2]
    lines = []
    for d in rec.get("detections", []):
        if "bbox_xywh" in d:
            x, y, bw, bh = d["bbox_xywh"]
        else:
            x1, y1, x2, y2 = d["bbox_xyxy"]
            x, y, bw, bh = x1, y1, x2 - x1, y2 - y1
        lines.append("0 %.6f %.6f %.6f %.6f"
                     % ((x + bw / 2) / w, (y + bh / 2) / h, bw / w, bh / h))
    with open(dst_txt, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    return len(lines)


def box_crosscheck(args, all_rows):
    """박성문 gt 상자와 임성후 watershed 상자가 같은 사진에서 몇 개나 다른가(기록만 한다)."""
    out = {}
    for fruit in args.fruits:
        pj = os.path.join(args.psm_root, "bbox_outputs", fruit, "gt_boxes", "json")
        lj = os.path.join(args.lsh_root, "bbox_outputs", fruit, "all", "json")
        if not (os.path.isdir(pj) and os.path.isdir(lj)):
            continue
        n_both = n_diff = 0
        dsum = 0
        ex = []
        for r in all_rows:
            if r["fruit"] != fruit or r["boxes_source"] != "psm_gt":
                continue
            a = os.path.join(pj, r["stem"] + ".json")
            b = os.path.join(lj, r["stem"] + ".json")
            if not (os.path.exists(a) and os.path.exists(b)):
                continue
            ca, cb = box_count_of(a), box_count_of(b)
            n_both += 1
            if ca != cb:
                n_diff += 1
                dsum += abs(ca - cb)
                if len(ex) < 5:
                    ex.append({"stem": r["stem"], "psm_gt": ca, "lsh": cb})
        out[fruit] = {"n_both": n_both, "n_count_differs": n_diff,
                      "mean_abs_diff": round(dsum / n_diff, 2) if n_diff else 0, "examples": ex}
    return out


def box_count_of(path):
    rec = read_json(path, {})
    n = rec.get("total_fruit_count")
    return int(n) if isinstance(n, int) else len(rec.get("detections", []))


# ────────────────────────────────── 촬영 단위(session)·분할 묶음(split_group)
def peach_session(stem):
    """복숭아 `210629-t1-01` · `210629-t2-of15-04` → 촬영 단위 `210629-t1` · `210629-t2`.

    파일명 규칙 = «날짜-t나무번호[-of곁가지]-장번호». 날짜와 나무 번호까지가 한 촬영이다.
    of10~of18 은 t2 나무의 곁가지 묶음이라 t2 안에 둔다(거친 쪽이 분할에 안전하다).
    """
    m = re.match(r"^(\d{6}-t\d+)", stem)
    return m.group(1) if m else stem


def grape_session(stem):
    """포도(CERTH)는 촬영 단위를 **확인할 수 없다** → 사진 한 장이 한 촬영.

    근거(2026-09-18 실측):
      · 원본 COCO(`share_grape_certh/CERTH_annotations.zip`)의 `file_name` 이 `0.png`…`2501.png`
        번호뿐이고 폴더 구분이 없다. `date_captured` 는 전부 빈 문자열, `info` 도 공란이다.
      · 툴 `data/grape/duplicates.json` 의 sequence_stats: `n_sequences` 1 ·
        이웃 번호 2,501쌍의 상관계수 중앙값 0.110(사과처럼 연속 프레임이면 훨씬 높다).
        즉 번호 순서가 촬영 순서가 아니다.
    """
    return stem


def build_groups(stems, sessions, dup_groups, prefix):
    """split_group = duplicates.json 묶음 ∪ 같은 session. 이름은 stem 정렬만으로 정해진다(재현성)."""
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[rb] = ra

    for s in stems:
        find(s)
    for g in dup_groups:
        members = [m for m in g if m in par]
        for m in members[1:]:
            union(members[0], m)
    by_sess = collections.defaultdict(list)
    for s in stems:
        by_sess[sessions[s]].append(s)
    for members in by_sess.values():
        for m in members[1:]:
            union(members[0], m)
    comp = collections.defaultdict(list)
    for s in stems:
        comp[find(s)].append(s)
    order = sorted(comp.values(), key=lambda xs: natkey(min(xs, key=natkey)))
    out = {}
    for i, xs in enumerate(order, 1):
        for s in xs:
            out[s] = "%s%04d" % (prefix, i)
    return out


# ────────────────────────────────── 한 과일 계산(파일은 아직 쓰지 않는다)
def plan_fruit(fruit, args, team):
    """그 과일의 manifest 행과 «무엇을 어디서 복사할지» 를 정한다. 파일은 만들지 않는다."""
    rev_root = args.reviewed_260916 if REVIEWED_OF[fruit] == "260916" else args.reviewed_260917
    rev_dir = os.path.join(rev_root, fruit)
    mani = os.path.join(rev_dir, "manifest.csv")
    if not os.path.exists(mani):
        raise SystemExit("[%s] 검수판 manifest 가 없습니다: %s" % (fruit, mani))
    with open(mani, encoding="utf-8", newline="") as f:
        rev_rows = list(csv.DictReader(f))
    has_session = "session" in (rev_rows[0] if rev_rows else {})

    st = read_json(os.path.join(args.tool_data, fruit, "status.json"), {})
    dup = read_json(os.path.join(args.tool_data, fruit, "duplicates.json"), {})
    dup_groups = [g for g in (dup.get("groups") or []) if isinstance(g, list) and len(g) >= 2]

    stems = [r["stem"] for r in rev_rows]
    if not has_session:
        sess_fn = peach_session if fruit == "peach" else grape_session
        sessions = {s: sess_fn(s) for s in stems}
        extra = list(dup_groups)
        if fruit == "peach":
            # 2026-09-18 2차 검수 M2-1(누수): 최인훈 «중복 후보» 묶음도 split_group 에 잇는다.
            # 후보가 학습·시험으로 갈라지면 누수다. 지금 자료에서는 후보가 전부 한 촬영 안에 있어
            # 결과가 바뀌지 않지만, 앞으로 후보가 늘어도 갈라지지 않게 구조로 못박아 둔다.
            byg = collections.defaultdict(list)
            for s, g in (team.get("peach_dup") or {}).items():
                byg[g].append(s)
            extra += [v for v in byg.values() if len(v) >= 2]
        groups = build_groups(stems, sessions, extra, fruit[0])
    else:
        sessions = {r["stem"]: r.get("session", "") for r in rev_rows}
        groups = {r["stem"]: r.get("split_group", "") for r in rev_rows}

    orig_dir = os.path.join(args.original_root, fruit)
    # 🔴 2026-09-19 5차: 팀 표준 2MP 크기표. 헤더만 읽으므로 몇 초 안에 끝난다.
    std, std_src, no_std = build_spec_table(fruit, args, stems, rev_dir)
    fixed_dir = os.path.join(args.tool_data, fruit, "masks_fixed")
    inst_fixed_dir = os.path.join(args.tool_data, fruit, "instances_fixed")
    seed_dir = SEED_DIRS.get(fruit)
    bidx, tbox, bstat = box_index(fruit, args)
    gtc = gt_counts(args.psm_root, fruit)         # 2026-09-19 사이클2: 정답 개수(없는 과일은 빈칸)
    verdicts = team["apple_check"] if fruit == "apple" else {}
    dup_cand = team["peach_dup"] if fruit == "peach" else {}
    mask_audit = team["mask_audit"]

    # 이 과일의 «원본 마스크가 열매 번호 마스크인가»(사과만 그렇다) — 한 장만 열어 보고 정한다.
    # --dry-run 표에 번호 장수를 적기 위한 미리보기다. 장마다의 진짜 판정은 write_fruit 가 한다.
    number_masks = False
    probe_dir = os.path.join(rev_dir, "masks")
    probe = sorted((p for p in os.listdir(probe_dir) if p.endswith(".png")))[:1] \
        if os.path.isdir(probe_dir) else []
    if probe:
        v = ids_of(read_u16(os.path.join(probe_dir, probe[0])))
        number_masks = bool(v.size > 1 or (v.size == 1 and v[0] != 255))

    rows, jobs, problems = [], [], []
    spec_files = []                 # 2026-09-19 검수2 N2: 규격을 맞춘 파일 한 줄씩
    for r in sorted(rev_rows, key=lambda r: natkey(r["stem"])):
        s = r["stem"]
        base_action = r["action"]
        note = (r.get("note") or "").strip()
        hv, hsrc, hby, hat, hnote = human_verdict(st.get(s))
        # 2026-09-19: 상자·번호의 확정은 마스크 확정과 **아무 상관이 없다**(세 칸 독립).
        bst, bby, bat, bnote = confirmed_kind(st.get(s), "boxes")
        ist, iby, iat, inote = confirmed_kind(st.get(s), "instances")
        rec_exists = s in st
        if hsrc in ("human_confirmed", "human_unconfirmed"):
            source = hsrc
        elif rec_exists:
            source = "ai"                    # 툴에 AI 판정이 있고 사람은 아직 안 눌렀다
        else:
            source = "reviewed"              # 툴에 아무 기록도 없다 = 검수판 판정 그대로
        if hsrc in ("confirmed_unreviewed", "human_cleared"):
            note = (note + " · 사람이 툴에서 판정을 지움(unreviewed) — 검수판 판정 유지").strip(" ·")

        reason = ""
        action = base_action
        if hv == "ok":
            action = "keep"
            if base_action.startswith("excluded"):
                note = (note + " · 검수판 제외를 사람이 되살림").strip(" ·")
        elif hv == "fixed":
            action = "mask_fixed"
            if base_action.startswith("excluded"):
                note = (note + " · 검수판 제외를 사람이 되살림").strip(" ·")
        elif hv == "exclude":
            action, reason = "excluded_human", "human_exclude"
        elif hv == "flag":
            action, reason = "excluded_flag", "confirmed_flag"
        elif base_action == "excluded_duplicate":
            reason = "reviewed_duplicate"
        elif base_action == "excluded_not_grape":
            reason = "reviewed_not_grape"
        if hnote:
            note = (note + " · 사람 메모: " + hnote).strip(" ·")

        vtxt, vsrc = verdicts.get(s, ("", "none"))
        row = dict(fruit=fruit, stem=s, image_source="", mask_source="", action=action,
                   reason=reason, note=note, source=source,
                   confirmed_by=hby if hsrc in ("human_confirmed", "human_unconfirmed") else "",
                   confirmed_at=hat if hsrc in ("human_confirmed", "human_unconfirmed") else "",
                   session=sessions.get(s, ""), split_group=groups.get(s, ""),
                   has_instances="0", has_boxes="0",
                   rule_pending=r.get("rule_pending", "") or "",
                   overlap_neighbors=r.get("overlap_neighbors", "") or "",
                   instances_source="none", boxes_source="none",
                   apple_check_verdict=vtxt, verdict_source=vsrc,
                   peach_dup_candidate=dup_cand.get(s, ""),
                   mask_audit_reason=mask_audit.get((fruit, s), ""),
                   boxes_confirmed_status=bst or "-", boxes_confirmed_by=bby,
                   boxes_confirmed_at=bat, instances_confirmed_status=ist or "-",
                   spec_fixed="-",
                   # 2026-09-19 «개수 세기»: write_fruit 가 **실제로 나간 파일**을 세어 채운다.
                   # 여기서 채우지 않는 까닭 — 규격을 맞추다 번호가 사라질 수 있어서 계획 단계의
                   # 수는 결과와 다를 수 있다(spec_warn). manifest 는 결과를 말해야 한다.
                   n_boxes="", n_instances="", n_count_human="", count_source="none",
                   count_conflict="0",
                   # 2026-09-19 사이클2: 정답 개수는 «나간 파일» 과 무관한 **바깥 자료**라 계획
                   # 단계에서 바로 채운다(뺀 사진에도 정답은 있다 — 아래에서 «-» 로 덮지 않는다).
                   n_gt=("" if gtc.get(s) is None else str(gtc[s])))
        if bnote:
            row["note"] = note = (note + " · 상자 메모: " + bnote).strip(" ·")
        if inote:
            row["note"] = note = (note + " · 번호 메모: " + inote).strip(" ·")

        if action.startswith("excluded"):
            row["image_source"] = row["mask_source"] = "-"
            # 2026-09-19: 뺀 사진은 나간 파일이 없으니 개수도 «-» 다(0 이라고 적으면 «열매가 없는
            # 사진» 으로 읽힌다 — MAE·R² 를 셀 때 그 0 이 그대로 섞여 들어간다).
            row["n_boxes"] = row["n_instances"] = row["n_count_human"] = "-"
            row["count_source"] = row["count_conflict"] = "-"
            # `n_gt` 는 덮지 않는다 — 정답 개수는 이 폴더에 무엇이 나갔나와 상관이 없고,
            # 뺀 사진의 정답 수는 «왜 뺐나» 를 볼 때 쓰인다.
            rows.append(row)
            continue

        # ── 어디서 가져올지 (검수판에 파일이 있으면 그것, 되살린 사진은 원본에서)
        img_rev = os.path.join(rev_dir, "images", s + ".png")
        msk_rev = os.path.join(rev_dir, "masks", s + ".png")
        img_org = os.path.join(orig_dir, "images", s + ".png")
        msk_org = os.path.join(orig_dir, "masks", s + ".png")
        if os.path.exists(img_rev):
            img_src, img_label = img_rev, "reviewed_" + REVIEWED_OF[fruit]
        elif os.path.exists(img_org):
            img_src, img_label = img_org, "resized_2mp"
        else:
            problems.append("%s/%s: 이미지 파일을 찾지 못해 뺐습니다" % (fruit, s))
            row.update(action="excluded_missing", reason="missing_image",
                       image_source="-", mask_source="-")
            rows.append(row)
            continue

        msk_fixed = os.path.join(fixed_dir, s + ".png")
        if hv == "fixed":
            if os.path.exists(msk_fixed):
                msk_src, msk_label = msk_fixed, "masks_fixed"
            else:
                msk_src = msk_rev if os.path.exists(msk_rev) else msk_org
                msk_label = "reviewed_" + REVIEWED_OF[fruit] if os.path.exists(msk_rev) else "resized_2mp"
                problems.append("%s/%s: 사람이 «수정함» 으로 판정했으나 masks_fixed 파일이 없습니다"
                                " — 원본 마스크를 씁니다" % (fruit, s))
                note = (note + " · masks_fixed 파일 없음 → 원본 마스크 사용").strip(" ·")
                row["note"] = note
        elif os.path.exists(msk_fixed) and source in ("human_confirmed", "human_unconfirmed"):
            # 사람이 마스크를 고쳐 두고 판정은 ok 로 누른 경우 — 툴 규칙(masks_fixed 우선)을 따른다
            msk_src, msk_label = msk_fixed, "masks_fixed"
        elif os.path.exists(msk_rev):
            msk_src, msk_label = msk_rev, "reviewed_" + REVIEWED_OF[fruit]
        elif os.path.exists(msk_org):
            msk_src, msk_label = msk_org, "resized_2mp"
        else:
            problems.append("%s/%s: 마스크 파일을 찾지 못해 뺐습니다" % (fruit, s))
            row.update(action="excluded_missing", reason="missing_mask",
                       image_source="-", mask_source="-")
            rows.append(row)
            continue
        # ── 🔴 2026-09-19 5차 «규격 검사·맞춤». 팀원이 **원본 해상도**로 만든 라벨 산출물이
        #    섞여 들어올 수 있다. 여기서 팀 표준과 대조해 «맞출 것 / 채택하지 않을 것» 만 정하고,
        #    실제 리사이즈는 write_fruit 가 한다(dry-run 에서도 예측이 보이게 하려는 것이다).
        std_wh = std.get(s)
        spec = {}                     # 종류 → (원래 크기, 표준 크기)
        if std_wh is None:
            note = (note + " · 팀 표준 크기를 찾지 못해 규격을 견주지 못했습니다").strip(" ·")
            row["note"] = note
        else:
            # ① 사진. 크기가 다르면 «원본 해상도 사진이 들어온 것» 이므로 **표준본을 먼저 쓴다**.
            isz = img_size_of(img_src)
            if isz and isz != std_wh:
                alt = find_image(os.path.join(orig_dir, "images"), s)
                alt_ok = bool(alt) and img_size_of(alt) == std_wh
                # 🔴 2026-09-19 검수1 X2: 표준본이 **같은 사진** 일 때만 되돌린다. 사람이 아예
                #    다른(올바른) 사진으로 교정해 둔 것이면(포도 `image_replaced` 12장 같은 경우)
                #    표준본으로 되돌리는 것은 사람 교정을 조용히 버리는 것이다.
                if alt_ok and not same_photo(img_src, alt):
                    problems.append("%s/%s: 검수판 사진이 표준본과 «다른 사진» 입니다 — 사람이"
                                    " 교정한 것으로 보고 표준본으로 되돌리지 않고 검수판 사진을"
                                    " 표준 크기로 줄였습니다(%s → %s)"
                                    % (fruit, s, wh(isz), wh(std_wh)))
                    note = (note + " · 검수판 사진이 표준본과 다른 사진(사람 교정)이어서 표준본으로"
                            " 되돌리지 않고 %s → %s 로 줄였습니다" % (wh(isz), wh(std_wh))).strip(" ·")
                    row["note"] = note
                    alt_ok = False
                if alt_ok:
                    img_src, img_label = alt, "resized_2mp"
                    note = (note + " · 사진이 표준 크기(%s)가 아니라 %s 여서 표준본(resized_2mp)을 썼습니다"
                            % (wh(std_wh), wh(isz))).strip(" ·")
                    row["note"] = note
                elif not spec_ratio_ok(isz, std_wh):
                    problems.append("%s/%s: 사진의 가로세로비가 표준과 0.5%% 넘게 달라 뺐습니다"
                                    "(%s · 표준 %s)" % (fruit, s, wh(isz), wh(std_wh)))
                    row.update(action="excluded_spec", reason="spec_mismatch_ratio",
                               image_source="-", mask_source="-")
                    row["note"] = (note + " · 사진 %s 의 가로세로비가 표준 %s 와 0.5%% 넘게 달라"
                                   " 뺐습니다" % (wh(isz), wh(std_wh))).strip(" ·")
                    rows.append(row)
                    continue
                else:
                    spec["image"] = (isz, std_wh)
            # ② 마스크. 비율이 맞으면 최근접으로 맞추고, 비율이 다르면 **채택하지 않고** 다음 후보로.
            msz = img_size_of(msk_src)
            if msz and msz != std_wh:
                if spec_ratio_ok(msz, std_wh):
                    spec["mask"] = (msz, std_wh)
                else:
                    # 🔴 2026-09-19 검수1 F6: 예전에는 마스크 크기를 «표준» 자리에 찍어
                    #    정작 표준 크기를 한 번도 보여 주지 않았다.
                    problems.append("%s/%s: 마스크(%s · %s)의 가로세로비가 표준(%s)과 0.5%% 넘게"
                                    " 달라 채택하지 않았습니다"
                                    % (fruit, s, msk_label, wh(msz), wh(std_wh)))
                    alt, alt_lab = None, ""
                    for cand, lab in ((msk_rev, "reviewed_" + REVIEWED_OF[fruit]),
                                      (msk_org, "resized_2mp")):
                        if cand != msk_src and img_size_of(cand) == std_wh:
                            alt, alt_lab = cand, lab
                            break
                    if alt:
                        note = (note + " · 마스크(%s %s)의 비율이 표준과 달라 %s 의 마스크를 대신 썼습니다"
                                % (msk_label, wh(msz), alt_lab)).strip(" ·")
                        row["note"] = note
                        msk_src, msk_label = alt, alt_lab
                    else:
                        row.update(action="excluded_spec", reason="spec_mismatch_ratio",
                                   image_source="-", mask_source="-")
                        row["note"] = (note + " · 마스크 %s 의 가로세로비가 표준 %s 와 0.5%% 넘게"
                                       " 달라 쓸 수 있는 마스크가 없어 뺐습니다"
                                       % (wh(msz), wh(std_wh))).strip(" ·")
                        rows.append(row)
                        continue
        row["image_source"], row["mask_source"] = img_label, msk_label

        # ── 열매 번호(있으면). 우선순위 = 사람이 고친 것 > 검출팀 초벌 > 원본 번호 마스크
        #    2026-09-19: 그 앞에 **번호 확정**(`confirmed_instances`)이 온다 — 마스크 확정으로
        #    대체하지 않는다(번호를 한 번도 보지 않은 사람의 «원본 OK» 가 번호까지 확정한 것처럼
        #    새어 나가면 안 된다 · 툴 export/export_dataset.py 와 같은 규칙).
        inst_src, inst_label, inst_block = None, "", False
        p = os.path.join(inst_fixed_dir, s + ".png")
        seed_p = os.path.join(seed_dir, s + ".png") if seed_dir else ""
        if ist in ("exclude", "flag"):
            inst_block = True                      # 사람이 번호를 «제외/문제 있음» 으로 확정 → 번호 없음
            note = (note + " · 번호 확정 «%s» — 이 사진의 열매 번호는 넣지 않았습니다" % ist).strip(" ·")
            row["note"] = note
        elif ist in ("ok", "fixed"):
            # 사람이 번호를 확정했다 → 툴이 고친 번호본, 없으면 원본 번호본을 그대로 채택한다.
            if os.path.exists(p):
                inst_src, inst_label = p, "tool_confirmed"
            elif seed_p and os.path.exists(seed_p):
                inst_src, inst_label = seed_p, "tool_confirmed"
                note = (note + " · 번호 확정은 있으나 instances_fixed 파일이 없어 원본 번호본을 씀").strip(" ·")
                row["note"] = note
            elif number_masks:
                inst_label = "tool_confirmed"      # 검수판 마스크 자체가 번호 마스크(사과)
            else:
                problems.append("%s/%s: 번호를 «%s» 로 확정했는데 번호 마스크를 어디에서도 찾지 못했습니다"
                                % (fruit, s, ist))
                note = (note + " · 번호 확정은 있으나 번호 마스크가 없음").strip(" ·")
                row["note"] = note
        elif os.path.exists(p):
            inst_src, inst_label = p, "instances_fixed"
        elif seed_p and os.path.exists(seed_p):
            inst_src, inst_label = seed_p, SEED_LABELS.get(fruit, "detect_seed")   # 사이클5: 복숭아
        elif number_masks:
            # 2026-09-18 3차 D9: 값은 전부 영문 토큰으로 통일한다(학습 코드가 파싱하기 쉽게).
            inst_label = "reviewed_number_mask"   # 원본 마스크 자체가 번호 마스크(사과)
        # ③ 번호 규격. 비율이 맞으면 최근접으로 맞추고, 다르면 **번호를 넣지 않는다**.
        if inst_src and std_wh:
            zsz = img_size_of(inst_src)
            if zsz and zsz != std_wh:
                if spec_ratio_ok(zsz, std_wh):
                    spec["instances"] = (zsz, std_wh)
                else:
                    problems.append("%s/%s: 번호 마스크(%s)의 가로세로비가 표준(%s)과 0.5%% 넘게"
                                    " 달라 번호를 넣지 않았습니다" % (fruit, s, inst_label, wh(zsz)))
                    note = (note + " · 번호 마스크 %s 의 비율이 표준과 달라 채택하지 않았습니다"
                            % wh(zsz)).strip(" ·")
                    row["note"] = note
                    inst_src, inst_label = None, ""
        row["instances_source"] = inst_label or "none"
        row["has_instances"] = "1" if inst_label else "0"

        # ── 상자. 2026-09-19 종류별 확정(총괄 결정):
        #    ok/fixed  → 툴 json 을 **사람 상자**로 채택(boxes_source=tool)
        #    exclude/flag → 그 사진의 상자는 **없음**(파일을 아예 만들지 않는다)
        #    확정 없음  → 박성문 gt > 임성후. 확정 없는 툴 json 이 비어 있지 않으면 «tool_unconfirmed»
        #                 로 표시만 하고 **채택하지 않는다**(확정하지 않은 초벌 저장본이 정답 상자를
        #                 밀어내면 안 된다 — 2차 검수 M2-7 이 빈 json 에서 실제로 겪은 사고다).
        base, tl = bidx.get(s), tbox.get(s)
        box = None
        if bst in ("ok", "fixed"):
            if tl:
                box = ("tool", tl[0], None)
                if not tl[1]:
                    problems.append("%s/%s: 상자를 «%s» 로 확정했는데 툴 json 에 상자가 0개입니다"
                                    " — 그대로(상자 0개) 채택했습니다" % (fruit, s, bst))
                    note = (note + " · 확정된 툴 상자가 0개(빈 json)").strip(" ·")
                    row["note"] = note
            else:
                box = base
                problems.append("%s/%s: 상자를 «%s» 로 확정했는데 툴 boxes json 이 없습니다"
                                " — 기존 우선순위(박성문 gt > 임성후)를 씁니다" % (fruit, s, bst))
                note = (note + " · 상자 확정은 있으나 툴 json 없음 → 기존 우선순위 사용").strip(" ·")
                row["note"] = note
        elif bst in ("exclude", "flag"):
            note = (note + " · 상자 확정 «%s» — 이 사진의 상자는 넣지 않았습니다" % bst).strip(" ·")
            row["note"] = note
        else:
            box = base
            if tl and tl[1]:
                if base is None:
                    row["boxes_source"] = "tool_unconfirmed"   # 표시만 한다(채택하지 않는다)
                note = (note + " · 확정 없는 툴 상자 json 있음(상자 %d개) — 채택하지 않았습니다"
                        % tl[1]).strip(" ·")
                row["note"] = note
        # ④ 상자 규격. json 의 `image_size`(툴 width/height · 팀원 image_size_hw)를 본다.
        #    비율이 맞으면 픽셀 좌표를 비율 변환하고, 다르면 **그 상자는 채택하지 않는다**.
        #    YOLO txt 는 0~1 정규화라 균일 배율에는 값이 바뀌지 않으므로 손대지 않는다.
        if box and std_wh:
            bsz = box_json_size(box[0], box[1])
            if bsz is None:
                # 🔴 2026-09-19 검수1 X5: 기준 크기가 없으면 규격을 견줄 수 없다. 예전에는
                #    아무 말 없이 좌표를 그대로 복사했다(어긋난 좌표가 조용히 나갔다).
                problems.append("%s/%s: 상자 json(%s)에 기준 사진 크기가 적혀 있지 않아 규격을"
                                " 견주지 못했습니다 — 픽셀 좌표를 그대로 두었습니다"
                                % (fruit, s, box[0]))
                note = (note + " · 상자 json 에 기준 크기가 없어 규격을 견주지 못했습니다").strip(" ·")
                row["note"] = note
            elif bsz != std_wh:
                if spec_ratio_ok(bsz, std_wh):
                    spec["boxes"] = (bsz, std_wh)
                else:
                    problems.append("%s/%s: 상자 json(%s)의 기준 크기 %s 가 표준(%s)과 비율이"
                                    " 0.5%% 넘게 달라 채택하지 않았습니다"
                                    % (fruit, s, box[0], wh(bsz), wh(std_wh)))
                    note = (note + " · 상자 json 의 기준 크기 %s 가 표준과 비율이 달라"
                            " 채택하지 않았습니다" % wh(bsz)).strip(" ·")
                    row["note"] = note
                    box = None
        if box:
            row["has_boxes"], row["boxes_source"] = "1", box[0]
        row["spec_fixed"] = ";".join("%s:%s->%s" % (k, wh(spec[k][0]), wh(spec[k][1]))
                                     for k in SPEC_KINDS if k in spec) or "-"
        # 🔴 2026-09-19 검수2 N2: 맞춘 파일을 **한 줄씩** 남긴다(누구에게 알려야 하는지 알려면
        #    «어느 폴더의 누구 파일» 인지가 있어야 한다). README 표·build_summary 가 이것을 쓴다.
        if spec:
            path_of = {"image": img_src, "mask": msk_src, "instances": inst_src,
                       "boxes": box[1] if box else None}
            for k in SPEC_KINDS:
                if k not in spec:
                    continue
                p = path_of.get(k) or ""
                spec_files.append(dict(
                    fruit=fruit, stem=s, kind=k,
                    src_size=wh(spec[k][0]), dst_size=wh(spec[k][1]),
                    path=p, owner=owner_of(p) if p else "",
                    source=({"image": row["image_source"], "mask": row["mask_source"],
                             "instances": row["instances_source"],
                             "boxes": box[0] if box else ""}).get(k, "")))

        rows.append(row)
        jobs.append(dict(stem=s, img=img_src, mask=msk_src, inst=inst_src, inst_label=inst_label,
                         inst_block=inst_block, box=box, spec=spec))
    # 2026-09-19: «툴 상자를 몇 장 채택했나 / 확정 없이 남아 있는 것이 몇 장인가» 를 남긴다.
    bstat = dict(bstat,
                 tool_adopted_confirmed=sum(1 for r in rows if r["boxes_source"] == "tool"),
                 tool_unconfirmed_marked=sum(1 for r in rows if r["boxes_source"] == "tool_unconfirmed"),
                 boxes_confirm_exclude=sum(1 for r in rows
                                           if r["boxes_confirmed_status"] in ("exclude", "flag")))
    kept_stems = [r["stem"] for r in rows if not r["action"].startswith("excluded")]
    spec_info = dict(
        target_pixels=SPEC_TARGET_PIXELS, multiple=SPEC_MULTIPLE,
        pixel_tolerance=SPEC_PIXEL_TOL, ratio_tolerance=SPEC_RATIO_TOL,
        std_from=dict(collections.Counter(std_src.get(t, "none") for t in kept_stems)),
        std_sizes=dict(collections.Counter(wh(std[t]) for t in kept_stems if t in std)),
        n_no_std=len([t for t in kept_stems if t not in std]),
        no_std_examples=[t for t in kept_stems if t not in std][:5],
        fixed=dict(collections.Counter(
            k for r in rows if r["spec_fixed"] not in ("", "-")
            for k in (x.split(":")[0] for x in r["spec_fixed"].split(";")))),
        n_fixed_rows=sum(1 for r in rows if r["spec_fixed"] not in ("", "-")),
        mismatch_ratio=[r["stem"] for r in rows if r["reason"] == "spec_mismatch_ratio"],
        # 2026-09-19 검수2 N2: 맞춘 파일 목록(누구에게 알릴지 알려면 소유자가 있어야 한다)
        fixed_files=spec_files,
        fixed_owners=dict(collections.Counter(e["owner"] or "(모름)" for e in spec_files)),
    )
    return rows, jobs, problems, dict(n_manifest=len(rev_rows), reviewed_dir=rev_dir,
                                      status_json=os.path.join(args.tool_data, fruit, "status.json"),
                                      dup_groups=len(dup_groups), box_stat=bstat, spec=spec_info,
                                      spec_std=std)   # spec_std 는 summary 에 넣지 않는다(4천 줄)


# ────────────────────────────────── 실제로 만들기
def write_fruit(fruit, out_dir, rows, jobs, problems):
    fdir = os.path.join(out_dir, fruit)
    os.makedirs(os.path.join(fdir, "images"), exist_ok=True)
    os.makedirs(os.path.join(fdir, "masks"), exist_ok=True)
    row_of = {r["stem"]: r for r in rows}
    n_inst = n_box = 0
    tool_stems = []
    for j in jobs:
        s = j["stem"]
        row_of[s]["has_instances"], row_of[s]["instances_source"] = "0", "none"  # 진짜로 쓴 것만 1 로
        sp = j.get("spec") or {}        # 2026-09-19 5차 «규격 맞춤» — plan_fruit 가 정한 것
        if "image" in sp:
            resize_image_to_spec(j["img"], os.path.join(fdir, "images", s + ".png"), sp["image"][1])
        else:
            shutil.copy2(j["img"], os.path.join(fdir, "images", s + ".png"))
        m = load_mask_bool(j["mask"])
        if "mask" in sp:
            # 🔴 2026-09-19 검수1 X3: 예전에는 «전경이 **다** 없어졌을 때» 만 경고했다.
            #    1픽셀 두께 경계나 3x3 작은 알은 소리 없이 사라졌다(23덩어리 → 21덩어리를 재현).
            #    최근접으로 줄이는 것은 되돌릴 수 없으니, 줄일 때마다 **얼마나 잃었는지** 남긴다.
            before_px, (bh, bw) = int(m.sum()), m.shape[:2]
            m = nn_resize_mask(m, sp["mask"][1])      # 마스크는 반드시 최근접(값 {0,255} 보존)
            after_px = int(m.sum())
            exp = before_px * float(sp["mask"][1][0] * sp["mask"][1][1]) / float(bw * bh) \
                if bw * bh else 0.0
            lost = ((exp - after_px) * 100.0 / exp) if exp > 0 else 0.0
            if before_px and not after_px:
                problems.append("%s/%s: spec_warn — 마스크를 표준 크기(%s)로 줄이니 전경이 다 없어졌습니다"
                                % (fruit, s, wh(sp["mask"][1])))
            else:
                problems.append("%s/%s: spec_warn — 마스크를 표준 크기(%s)로 줄였습니다:"
                                " 전경 %d → %d화소(같은 비율이면 %d) · 손실 %.1f%%%s"
                                % (fruit, s, wh(sp["mask"][1]), before_px, after_px, round(exp),
                                   lost, (" ← 5%를 넘습니다. 1픽셀 두께 경계나 작은 알이"
                                          " 사라졌을 수 있으니 눈으로 보십시오") if lost > 5 else ""))
        save_mask_255(os.path.join(fdir, "masks", s + ".png"), m)
        arr, label = None, ""
        if j.get("inst_block"):
            pass                                # 2026-09-19: 번호 확정이 exclude/flag → 번호를 안 낸다
        elif j["inst"]:
            arr, label = read_u16(j["inst"]), j["inst_label"]
            if "instances" in sp:
                before = set(ids_of(arr).tolist())
                arr = nn_resize_u16(arr, sp["instances"][1])   # 번호도 반드시 최근접
                after = set(ids_of(arr).tolist())
                if before != after:
                    problems.append("%s/%s: spec_warn — 번호를 표준 크기(%s)로 맞추니 번호 %d개가"
                                    " 사라졌습니다(작은 알): %s"
                                    % (fruit, s, wh(sp["instances"][1]), len(before - after),
                                       sorted(before - after)[:8]))
        else:                                   # 원본 마스크 자체가 번호 마스크인가(사과)
            raw = read_u16(j["mask"])
            if "mask" in sp:
                # 이진본을 표준으로 맞췄으면 **같은 파일에서 나온 번호본도** 같이 맞춘다.
                before = set(ids_of(raw).tolist())
                raw = nn_resize_u16(raw, sp["mask"][1])
                lost = before - set(ids_of(raw).tolist())
                if lost:
                    problems.append("%s/%s: spec_warn — 번호(원본 마스크)를 표준 크기(%s)로 맞추니"
                                    " 번호 %d개가 사라졌습니다: %s"
                                    % (fruit, s, wh(sp["mask"][1]), len(lost), sorted(lost)[:8]))
            v = ids_of(raw)
            if v.size > 1 or (v.size == 1 and v[0] != 255):
                # 2026-09-18 3차 D9 · 2026-09-19: 사람이 번호를 확정했으면 tool_confirmed 로 적는다
                arr, label = raw, j["inst_label"] or "reviewed_number_mask"
        if arr is not None:
            if arr.shape != m.shape:
                problems.append("%s/%s: 번호 마스크 크기가 이진 마스크와 달라 번호를 빼놨습니다"
                                " (번호 %s · 이진 %s)" % (fruit, s, arr.shape, m.shape))
            else:
                row_of[s]["instances_source"] = label
                cut = arr.copy()
                cut[~m] = 0                     # «이진본이 번호본을 자른다»(툴 instances.load_inst 규칙)
                write_u16(os.path.join(fdir, "instances", s + ".png"), cut)
                row_of[s]["has_instances"] = "1"
                # 2026-09-19 «개수 세기»: **나간 번호 파일**의 번호 수(이진본으로 자른 뒤·규격을
                # 맞춘 뒤의 값). 위 spec_warn 이 «번호 N개가 사라졌습니다» 라고 말한 그 결과다.
                row_of[s]["n_instances"] = str(int(ids_of(cut).size))
                n_inst += 1
        if j["box"]:
            kind, jp, tp = j["box"]
            bdir = os.path.join(fdir, "boxes")
            os.makedirs(bdir, exist_ok=True)
            if "boxes" in sp:
                # 픽셀 좌표를 표준 크기에 맞춰 비율 변환해 **새 json 으로** 쓴다(원본은 읽기만)
                scale_box_json(kind, jp, os.path.join(bdir, s + ".json"), *sp["boxes"])
            else:
                shutil.copy2(jp, os.path.join(bdir, s + ".json"))
            if kind == "tool":
                tool_stems.append(s)                    # YOLO txt 는 툴 함수가 한꺼번에 만든다
            elif tp:
                shutil.copy2(tp, os.path.join(bdir, s + ".txt"))   # 박성문이 만든 txt 를 그대로
            else:
                yolo_from_detect_json(jp, os.path.join(bdir, s + ".txt"))
            # 2026-09-19 «개수 세기»: **나간 상자 json** 을 센다(규격을 맞춰 새로 쓴 것이면 그것).
            nbx = n_box_in(os.path.join(bdir, s + ".json"))
            row_of[s]["n_boxes"] = "" if nbx is None else str(nbx)
            n_box += 1
    if tool_stems:
        used = export_tool_boxes(out_dir, fruit, tool_stems)
        if not str(used).startswith("app/boxes.py"):
            problems.append("%s: 툴 app/boxes.py 의 export_boxes_to 를 불러오지 못해 **자체 구현**으로"
                            " 상자 YOLO 를 만들었습니다 — %s" % (fruit, used))
    # 2026-09-19 «개수 세기»: 나간 파일을 다 센 **뒤에** 사람 확정 개수를 유도한다(순서가 중요하다 —
    # n_boxes·n_instances 가 채워지기 전에 부르면 늘 «없음» 이 된다).
    for j in jobs:
        count_cells(row_of[j["stem"]])
    return n_inst, n_box


# 툴 `app/boxes.py` 를 못 읽어 **자체 구현**으로 떨어진 기록. 한 건이라도 있으면 verify 가 실패한다.
TOOL_BOXES_FALLBACK = []


def export_tool_boxes(out_dir, fruit, stems):
    """**툴에서 사람이 그린** 상자 → YOLO txt. 툴 app/boxes.py 의 `export_boxes_to()` 를 그대로 쓴다.

    그 함수는 «폴더 하나를 통째로» 읽으므로, 우리가 고른 stem 의 json 만 임시 폴더에 모아 놓고
    돌린다(다른 출처의 json 은 형식이 달라 섞이면 안 된다). 임시 폴더는 스스로 정리된다.
    툴 `data/` 에는 아무것도 쓰지 않는다 — 결과 txt·boxes_all_tool.json 은 우리 출력 폴더에만.
    """
    import tempfile
    box_dir = os.path.join(out_dir, fruit, "boxes")
    all_json = os.path.join(box_dir, "boxes_all_tool.json")
    with tempfile.TemporaryDirectory(prefix="merged_boxes_") as stage:
        sd = os.path.join(stage, fruit, "boxes")
        os.makedirs(sd)
        for s in stems:
            shutil.copy2(os.path.join(box_dir, s + ".json"), os.path.join(sd, s + ".json"))
        try:
            sys.path.insert(0, os.path.join(TOOL_ROOT, "app"))
            import boxes as TOOLBOXES           # noqa: E402
            TOOLBOXES.export_boxes_to(stage, fruit, box_dir, all_json=all_json, at="")
            return "app/boxes.py export_boxes_to"
        except Exception as e:                  # pragma: no cover - 환경에 따라서만 탄다
            # 🔴 2026-09-20 구조 사이클 2 (사이클 1 2차 검수 §7-4 · 3차 판정 §2):
            #   전에는 여기서 **조용히** 자체 구현으로 떨어졌다. 툴 `app/boxes.py` 를 못 읽으면
            #   ① 아무도 모르고 ② 자체 구현에는 «줄 0개 json 은 txt 를 만들지 않는다»(0919 개수
            #   사이클5) 규칙이 없어서 0바이트 YOLO 라벨이 나갔다(검출 학습이 «이 사진에는 열매가
            #   없다» 는 정답으로 읽는다). 이제 ㉠ 흔적을 남겨 verify 를 실패시키고
            #   ㉡ 0줄 규칙을 여기에도 둔다.
            TOOL_BOXES_FALLBACK.append("%s: %s" % (fruit, e))
            classes = ["fruit", "bunch", "other"]
            allrec, n_box = [], 0
            for s in stems:
                rec = read_json(os.path.join(sd, s + ".json"), {})
                w, h = rec.get("width") or 1, rec.get("height") or 1
                lines = []
                for b in rec.get("boxes", []):
                    x1, y1, x2, y2 = b["xyxy"]
                    lines.append("%d %.6f %.6f %.6f %.6f" % (
                        classes.index(b.get("cls", "fruit")) if b.get("cls") in classes else 0,
                        (x1 + x2) / 2 / w, (y1 + y2) / 2 / h, (x2 - x1) / w, (y2 - y1) / h))
                if not lines:
                    continue          # 0줄 json 은 txt 를 만들지 않는다(툴 export_boxes_to 와 같은 규칙)
                with open(os.path.join(box_dir, s + ".txt"), "w") as f:
                    f.write("\n".join(lines) + "\n")
                allrec.append(rec)
                n_box += len(lines)
            with open(all_json, "w", encoding="utf-8") as f:
                json.dump({"fruit": fruit, "classes": classes, "at": "",
                           "n_images": len(allrec), "n_boxes": n_box, "images": allrec},
                          f, ensure_ascii=False, indent=1)
            return "자체 구현(툴 boxes.py 를 못 읽음: %s)" % e


# ────────────────────────────────── 출처 등록표 · 직전 빌드와 견주기
def collect_registry(args):
    """읽은 입력을 전부 적어 둔다(경로·주인·시각·개수·지문·어느 칸에 썼나). 없으면 «없음» 으로."""
    reg = {}
    for f in args.fruits:
        rr = args.reviewed_260916 if REVIEWED_OF[f] == "260916" else args.reviewed_260917
        reg_add(reg, "reviewed:%s:manifest" % f, os.path.join(rr, f, "manifest.csv"),
                "바탕 판정(action·note·session·split_group)")
        for sub in ("images", "masks"):
            reg_add(reg, "reviewed:%s:%s" % (f, sub), os.path.join(rr, f, sub),
                    "사진·마스크 원본(복사 대상)")
        reg_add(reg, "original:%s:images" % f, os.path.join(args.original_root, f, "images"),
                "되살린 사진의 출처(image_source=resized_2mp)")
        reg_add(reg, "original:%s:masks" % f, os.path.join(args.original_root, f, "masks"),
                "되살린 마스크의 출처")
        reg_add(reg, "tool:%s:status.json" % f, os.path.join(args.tool_data, f, "status.json"),
                "사람 판정(source·confirmed_by·confirmed_at·action)")
        reg_add(reg, "tool:%s:duplicates.json" % f, os.path.join(args.tool_data, f, "duplicates.json"),
                "복숭아·포도 split_group 의 근접 중복 묶음")
        reg_add(reg, "tool:%s:masks_fixed" % f, os.path.join(args.tool_data, f, "masks_fixed"),
                "mask_source=masks_fixed")
        reg_add(reg, "tool:%s:instances_fixed" % f, os.path.join(args.tool_data, f, "instances_fixed"),
                "instances_source=instances_fixed")
        reg_add(reg, "tool:%s:boxes" % f, os.path.join(args.tool_data, f, "boxes"),
                "boxes_source=tool")
        reg_add(reg, "psm:%s:gt_boxes.json" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "gt_boxes", "json"),
                "boxes_source=psm_gt (정답 마스크에서 뽑은 상자)")
        reg_add(reg, "psm:%s:gt_boxes.yolo" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "gt_boxes", "yolo_labels"),
                "boxes/<stem>.txt (박성문이 만든 YOLO txt 를 그대로 복사)")
        reg_add(reg, "psm:%s:gt_boxes.summary" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "gt_boxes", "summary.md"), "참고(설명)")
        reg_add(reg, "psm:%s:gt_boxes.csv" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "gt_boxes", "csv", "detections.csv"),
                "n_gt (정답 상자 수 — 카운팅 MAE·RMSE·R² 의 정답)")
        reg_add(reg, "psm:%s:all.json" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "all", "json"),
                "참고 — 임성후 판과 바이트 동일(watershed 추정, 미검증)")
        reg_add(reg, "psm:%s:all.instance_maps" % f,
                os.path.join(args.psm_root, "bbox_outputs", f, "all", "instance_maps"),
                "블루베리(instances_source=detect_seed)·복숭아(psm_watershed) 사용 · 나머지 과일은 쓰지 않음")
        reg_add(reg, "lsh:%s:all.json" % f,
                os.path.join(args.lsh_root, "bbox_outputs", f, "all", "json"),
                "boxes_source=lsh (박성문 gt 가 없는 과일에서만)")
    for n, use in (("review_list.csv", "apple_check_verdict · verdict_source"),
                   ("confirmed_errors.csv", "apple_check_verdict 의 «확정오류 N»"),
                   ("duplicates_keep_list.csv", "참고(반영 안 함)"),
                   ("duplicates_folds.csv", "참고(반영 안 함)"),
                   ("per_image.csv", "참고(반영 안 함)"),
                   ("summary.json", "참고(반영 안 함)")):
        reg_add(reg, "psm:apple_check:" + n, os.path.join(args.psm_root, "apple_check", n), use)
    for n, use in (("REPORT.md", "근거 문서(버스트 9그룹 45장)"),
                   ("similar_pairs.csv", "peach_dup_candidate 의 pair_* 그룹"),
                   ("clusters.txt", "참고(해밍 22 묶음 — 너무 거칠어 반영 안 함)")):
        reg_add(reg, "cih:peach_dup:" + n,
                os.path.join(args.cih_root, "dup_audit_260917", "peach", n), use)
    reg_add(reg, "cih:mask_audit:suspects.csv",
            os.path.join(args.cih_root, "mask_audit_260908", "suspects.csv"),
            "mask_audit_reason (reason 칸이 있는 것은 이 파일이다)")
    reg_add(reg, "cih:mask_audit:mask_stats.csv",
            os.path.join(args.cih_root, "mask_audit_260908", "mask_stats.csv"),
            "참고 — reason 칸 없음(전체 마스크 통계)")
    reg_add(reg, "cih:mask_audit:summary.json",
            os.path.join(args.cih_root, "mask_audit_260908", "summary.json"), "참고")
    return reg


def find_prev(out_root, out_dir):
    """직전 빌드의 build_summary.json 을 찾는다(가장 최근에 만든 datasets_merged_*)."""
    best, best_at = None, ""
    for n in sorted(os.listdir(out_root)) if os.path.isdir(out_root) else []:
        d = os.path.join(out_root, n)
        if not n.startswith("datasets_merged_") or d == out_dir or not os.path.isdir(d):
            continue
        if n.endswith("_INCOMPLETE"):
            continue        # 2026-09-18 2차 검수 M2-4: 검사에 걸린 판을 기준으로 삼지 않는다
        p = os.path.join(d, "build_summary.json")
        if not os.path.exists(p):
            continue
        at = (read_json(p, {}) or {}).get("built_at", "") or mtime_str(p)
        if at > best_at:
            best, best_at = p, at
    return best


def legacy_registry(prev_inputs):
    """출처 등록표가 없던 옛 build_summary.json 에서 견줄 수 있는 만큼만 뽑아낸다.

    첫 판(2026-09-18 17:39)은 `inputs` 에 과일별 status.json 지문·시각과 검수판 manifest 지문만
    갖고 있다. 그것만으로도 «툴에서 사람이 더 눌렀나» 는 알 수 있다.
    """
    reg = {}
    for f, i in (prev_inputs or {}).items():
        if i.get("reviewed_manifest_sha256"):
            reg["reviewed:%s:manifest" % f] = {"path": os.path.join(i.get("reviewed_dir", ""), "manifest.csv"),
                                               "exists": True, "sha256": i["reviewed_manifest_sha256"]}
        if i.get("status_json"):
            reg["tool:%s:status.json" % f] = {"path": i["status_json"], "exists": bool(i.get("status_json_sha256")),
                                              "sha256": i.get("status_json_sha256", ""),
                                              "mtime": i.get("status_json_mtime", "")}
    return reg


def compare_registry(prev_reg, cur_reg):
    """직전 빌드와 견줘 «바뀐 입력» 만 뽑는다 → [(key, 무엇이, 그때, 지금)]"""
    out = []
    for k in sorted(set(prev_reg) | set(cur_reg)):
        a, b = prev_reg.get(k), cur_reg.get(k)
        if a is None:
            out.append((k, "새로 생김", "(없던 항목)", "있음" if b.get("exists") else "없음"))
            continue
        if b is None:
            out.append((k, "이번에 안 읽음", "있음" if a.get("exists") else "없음", "(안 읽음)"))
            continue
        if bool(a.get("exists")) != bool(b.get("exists")):
            out.append((k, "있다/없다", "있음" if a.get("exists") else "없음",
                        "있음" if b.get("exists") else "없음"))
            continue
        if not b.get("exists"):
            continue
        for fld, kor in (("n_files", "파일 수"), ("n_rows", "행 수"),
                         ("latest_mtime", "최신 시각"), ("mtime", "시각"), ("sha256", "지문")):
            if fld in a and fld in b:      # 양쪽에 다 있는 칸만 견준다(옛 판의 요약과도 견줄 수 있게)
                if a.get(fld) != b.get(fld):
                    va, vb = a.get(fld), b.get(fld)
                    if fld == "sha256":
                        va, vb = str(va)[:12], str(vb)[:12]
                    out.append((k, kor, str(va), str(vb)))
    return out


# ────────────────────────────────── 검사
def verify(out_dir, fruits, all_rows, spec_std=None, notes=None):
    """스스로 검사 — 어긋난 것을 글로 돌려준다(빈 목록이면 통과).

    `spec_std` = {(과일, stem): (w,h)} 팀 표준 크기표. 주면 «출력 크기 = 표준» 까지 본다
    (없으면 이미지끼리의 크기 일치와 총 화소 ±0.15% 만 본다).
    `notes` = 리스트를 주면 «실패는 아니지만 사람이 볼 것» 을 거기에 적는다(2026-09-19 검수2 N6).
    """
    bad = []
    # 2026-09-20 구조 사이클 2: 툴 boxes.py 를 못 읽어 자체 구현으로 떨어졌으면 **실패**다.
    #   맨 앞에 둔다 — 아래 «40건 넘으면 생략» 에 밀려 사라지지 않게.
    for q in TOOL_BOXES_FALLBACK:
        bad.append("툴 app/boxes.py 의 export_boxes_to 를 못 불러 자체 구현으로 상자를 만들었습니다: %s" % q)
    spec_std = spec_std or {}
    notes = notes if notes is not None else []
    empty = [(r["fruit"], r["stem"], c) for r in all_rows for c in SOURCE_COLS if not r.get(c)]
    if empty:
        bad.append("출처 칸이 빈 행이 %d개 있습니다(예: %s)" % (len(empty), empty[:3]))
    for fruit in fruits:
        fdir = os.path.join(out_dir, fruit)
        imgs = {p[:-4] for p in os.listdir(os.path.join(fdir, "images")) if p.endswith(".png")}
        msks = {p[:-4] for p in os.listdir(os.path.join(fdir, "masks")) if p.endswith(".png")}
        if imgs != msks:
            bad.append("[%s] images 와 masks 의 이름이 다릅니다(%d vs %d, 차이 %d개)"
                       % (fruit, len(imgs), len(msks), len(imgs ^ msks)))
        rows = [r for r in all_rows if r["fruit"] == fruit]
        kept = {r["stem"] for r in rows if not r["action"].startswith("excluded")}
        if kept != imgs:
            bad.append("[%s] manifest 의 남긴 장수(%d)와 images 폴더(%d)가 다릅니다"
                       % (fruit, len(kept), len(imgs)))
        inst_dir = os.path.join(fdir, "instances")
        box_dir = os.path.join(fdir, "boxes")
        for r in rows:
            s = r["stem"]
            # ── 2026-09-19 종류별 확정 검사(뺀 사진에도 적용한다 — 파일이 남아 있으면 안 되니까)
            if r.get("boxes_confirmed_status") in ("exclude", "flag"):
                left = [e for e in (".json", ".txt") if os.path.exists(os.path.join(box_dir, s + e))]
                if left or r["has_boxes"] == "1":
                    bad.append("[%s/%s] 상자 확정이 «%s» 인데 상자가 나갔습니다(%s · has_boxes=%s)"
                               % (fruit, s, r["boxes_confirmed_status"], left, r["has_boxes"]))
            if r["boxes_source"] == "tool_unconfirmed":
                left = [e for e in (".json", ".txt") if os.path.exists(os.path.join(box_dir, s + e))]
                if left or r["has_boxes"] == "1":
                    bad.append("[%s/%s] 확정 없는 툴 상자(tool_unconfirmed)를 채택했습니다(%s · has_boxes=%s)"
                               % (fruit, s, left, r["has_boxes"]))
            if r.get("instances_confirmed_status") in ("exclude", "flag"):
                if os.path.exists(os.path.join(inst_dir, s + ".png")) or r["has_instances"] == "1":
                    bad.append("[%s/%s] 번호 확정이 «%s» 인데 번호가 나갔습니다"
                               % (fruit, s, r["instances_confirmed_status"]))
            if r["action"].startswith("excluded"):
                continue
            # ── 2026-09-19 5차 규격 검사: 출력 크기 = 표준 · 총 화소 2,073,600±0.15%
            isz = img_size_of(os.path.join(fdir, "images", s + ".png"))
            msz = img_size_of(os.path.join(fdir, "masks", s + ".png"))
            want = spec_std.get((fruit, s))
            if isz and msz and isz != msz:
                bad.append("[%s/%s] 사진(%s)과 마스크(%s)의 크기가 다릅니다"
                           % (fruit, s, wh(isz), wh(msz)))
            if isz and want and isz != want:
                bad.append("[%s/%s] 사진이 팀 표준 크기가 아닙니다(%s · 표준 %s)"
                           % (fruit, s, wh(isz), wh(want)))
            if msz and want and msz != want:
                bad.append("[%s/%s] 마스크가 팀 표준 크기가 아닙니다(%s · 표준 %s)"
                           % (fruit, s, wh(msz), wh(want)))
            # 🔴 2026-09-19 검수1: 표준 크기와 같으면 통과다. 8의 배수 반올림 때문에 원래 규칙이
            #    ±0.15% 를 넘는 표준을 주는 비율도 있다(6292x2503 → 2280x912 = +0.278%).
            #    그 경우 «규칙이 만든 표준» 을 «규격 위반» 이라고 부르면 안 된다.
            if isz and not spec_pixels_ok(*isz) and not (want and tuple(isz) == tuple(want)):
                bad.append("[%s/%s] 총 화소가 2,073,600±0.15%% 밖입니다(%s = %d화소)"
                           % (fruit, s, wh(isz), isz[0] * isz[1]))
            if r["has_instances"] == "1":
                zsz = img_size_of(os.path.join(inst_dir, s + ".png"))
                if zsz and isz and zsz != isz:
                    bad.append("[%s/%s] 번호 마스크 크기(%s)가 사진(%s)과 다릅니다"
                               % (fruit, s, wh(zsz), wh(isz)))
            if r["has_boxes"] == "1":
                yb = yolo_range_bad(os.path.join(box_dir, s + ".txt"))
                if yb:
                    bad.append("[%s/%s] YOLO txt 값이 0~1 밖입니다: %s" % (fruit, s, yb[:2]))
                # 🔴 2026-09-19 검수2 N5: 나간 상자 json 의 **기준 사진 크기**(툴 `width`/`height` ·
                #    팀원 `image_size_hw`)가 나간 사진 크기와 다르면 픽셀 좌표가 어긋나 있다.
                #    «못 읽었다» 는 검수1 X5 가 problems 로 남기지만, «읽었는데 다르다» 는
                #    아무도 보지 않았다(규격 맞춤 길을 타지 않은 경우). 한 줄로 막는다.
                bsz = box_json_size(r["boxes_source"], os.path.join(box_dir, s + ".json"))
                if bsz and isz and tuple(bsz) != tuple(isz):
                    bad.append("[%s/%s] 상자 json 의 기준 사진 크기(%s)가 나간 사진(%s)과 다릅니다"
                               " — 픽셀 좌표가 어긋나 있습니다(출처 %s)"
                               % (fruit, s, wh(bsz), wh(isz), r["boxes_source"]))
            m = None
            try:
                with Image.open(os.path.join(fdir, "masks", s + ".png")) as im:
                    a = np.array(im)
                    if im.mode != "L":
                        bad.append("[%s/%s] 마스크가 L 모드가 아닙니다(%s)" % (fruit, s, im.mode))
                u = np.unique(a)
                if not set(u.tolist()) <= {0, 255}:
                    bad.append("[%s/%s] 마스크 값이 0/255 가 아닙니다: %s" % (fruit, s, u[:6].tolist()))
                m = a > 0
            except Exception as e:
                bad.append("[%s/%s] 마스크를 읽지 못했습니다: %s" % (fruit, s, e))
            if r["has_instances"] == "1":
                p = os.path.join(inst_dir, s + ".png")
                if not os.path.exists(p):
                    bad.append("[%s/%s] has_instances=1 인데 번호 파일이 없습니다" % (fruit, s))
                elif m is not None:
                    arr = read_u16(p)
                    if arr.shape != m.shape or bool(((arr > 0) & ~m).any()):
                        bad.append("[%s/%s] 번호가 마스크 밖으로 나갑니다" % (fruit, s))
            if len(bad) > 40:
                bad.append("… (이하 생략)")
                return bad
    # ── 🔴 2026-09-19 검수2 N6: «마스크 확정이 fixed 인데 mask_source 가 masks_fixed 가 아님».
    #    사람이 툴에서 «수정함» 으로 확정했는데 그 마스크가 나가지 않은 것이다(masks_fixed 파일이
    #    없었거나, 비율이 표준과 달라 검수판 마스크로 **강등**됐을 때 생긴다 — note 에는 남는다).
    #    **실패로 세지 않는다**(지금 자료는 0장이고, 근거 없이 빌드를 멈추면 안 된다).
    #    ⛔ `action == "mask_fixed"` 만 보면 안 된다 — **검수판(AI 3회 검수)이 이미 mask_fixed 로
    #       적어 둔 행**까지 걸린다(복숭아 39장이 실제로 그렇다 · v3 에도 그대로 있다). 그것은
    #       사람 확정이 아니므로 «사람이 고친 마스크를 잃었다» 가 아니다. `source` 로 가른다.
    downgraded = [(r["fruit"], r["stem"], r["mask_source"]) for r in all_rows
                  if r["action"] == "mask_fixed" and r["mask_source"] != "masks_fixed"
                  and r["source"] in ("human_confirmed", "human_unconfirmed")]
    if downgraded:
        notes.append("마스크 확정이 «수정함(fixed)» 인데 `mask_source` 가 `masks_fixed` 가 아닌 행이"
                     " %d개 있습니다 — 사람이 고친 마스크가 나가지 않았습니다(예: %s)"
                     % (len(downgraded),
                        ", ".join("%s/%s→%s" % t for t in downgraded[:3])))
    return bad


# ────────────────────────────────── 표·문서
def count_table(rows, fruits):
    """과일별 (남긴 장수, 제외 사유별 장수, 번호·상자 장수)."""
    out = {}
    for fruit in fruits:
        rs = [r for r in rows if r["fruit"] == fruit]
        kept = [r for r in rs if not r["action"].startswith("excluded")]
        out[fruit] = dict(
            n_manifest=len(rs), n_keep=len(kept),
            actions=dict(collections.Counter(r["action"] for r in kept)),
            reasons=dict(collections.Counter(r["reason"] or r["action"]
                                             for r in rs if r["action"].startswith("excluded"))),
            sources=dict(collections.Counter(r["source"] for r in kept)),
            n_instances=sum(1 for r in kept if r["has_instances"] == "1"),
            n_boxes=sum(1 for r in kept if r["has_boxes"] == "1"),
            n_sessions=len({r["session"] for r in kept}),
            n_split_groups=len({r["split_group"] for r in kept}),
            n_rule_pending=sum(1 for r in kept if r["rule_pending"]),
            boxes_sources=dict(collections.Counter(r["boxes_source"] for r in kept)),
            n_apple_check=sum(1 for r in kept if r["apple_check_verdict"]),
            n_peach_dup=sum(1 for r in kept if r["peach_dup_candidate"]),
            peach_dup_groups=len({r["peach_dup_candidate"] for r in kept if r["peach_dup_candidate"]}),
            n_mask_audit=sum(1 for r in kept if r["mask_audit_reason"]),
            # 2026-09-18 3차 D1: 대표와 함께 살아남은 «되살린 중복» 을 세기만 한다(빼지 않는다)
            n_revived=sum(1 for r in kept if "되살림" in (r.get("note") or "")),
            # 2026-09-19 종류별 확정 — **뺀 사진까지 센다**(확정이 제외의 이유일 수 있으므로).
            # 마스크 확정은 source 칸에, 상자·번호 확정은 각자의 status 칸에 있다.
            n_confirmed_mask=sum(1 for r in rs if r["source"] == "human_confirmed"),
            n_confirmed_boxes=sum(1 for r in rs if r["boxes_confirmed_status"] not in ("", "-")),
            n_confirmed_instances=sum(1 for r in rs
                                      if r["instances_confirmed_status"] not in ("", "-")),
            boxes_confirmed=dict(collections.Counter(
                r["boxes_confirmed_status"] for r in rs if r["boxes_confirmed_status"] not in ("", "-"))),
            instances_confirmed=dict(collections.Counter(
                r["instances_confirmed_status"] for r in rs
                if r["instances_confirmed_status"] not in ("", "-"))),
            instances_sources=dict(collections.Counter(r["instances_source"] for r in kept)),
            # 2026-09-19 5차 «규격 검사·맞춤» — 종류(image·mask·instances·boxes)별로 센다.
            # 뺀 사진까지 센다(비율이 달라 뺀 사진이 여기에 잡힌다).
            n_spec_fixed=dict(collections.Counter(
                k for r in rs if r.get("spec_fixed") not in (None, "", "-")
                for k in (x.split(":")[0] for x in r["spec_fixed"].split(";")))),
            n_spec_fixed_rows=sum(1 for r in rs if r.get("spec_fixed") not in (None, "", "-")),
            n_spec_mismatch_ratio=sum(1 for r in rs if r["reason"] == "spec_mismatch_ratio"),
        )
    return out


def print_table(tab, fruits):
    print("\n  과일        manifest   남김   제외   번호   상자   촬영단위  분할묶음")
    for f in fruits:
        t = tab[f]
        print("  %-10s %7d %7d %6d %6d %6d %8d %9d"
              % (KOR[f], t["n_manifest"], t["n_keep"], t["n_manifest"] - t["n_keep"],
                 t["n_instances"], t["n_boxes"], t["n_sessions"], t["n_split_groups"]))
    print("\n  제외 사유")
    for f in fruits:
        for k, v in sorted(tab[f]["reasons"].items()):
            print("    %-10s %-22s %6d  %s" % (KOR[f], k, v, REASON_KOR.get(k, "")))
    print("\n  판정 출처(남긴 사진)")
    for f in fruits:
        print("    %-10s %s" % (KOR[f], ", ".join("%s=%d" % kv for kv in sorted(tab[f]["sources"].items()))))
    print("\n  종류별 사람 확정(뺀 사진까지 · 마스크 = status.json `confirmed` · 상자·번호 = 각자의 칸)")
    for f in fruits:
        t = tab[f]
        print("    %-10s 마스크 %4d · 상자 %4d %s · 번호 %4d %s"
              % (KOR[f], t["n_confirmed_mask"], t["n_confirmed_boxes"],
                 "(" + ", ".join("%s=%d" % kv for kv in sorted(t["boxes_confirmed"].items())) + ")"
                 if t["boxes_confirmed"] else "", t["n_confirmed_instances"],
                 "(" + ", ".join("%s=%d" % kv for kv in sorted(t["instances_confirmed"].items())) + ")"
                 if t["instances_confirmed"] else ""))
    print("\n  규격(팀 표준 2MP) 맞춤 — 종류별 장수 · 비율이 달라 못 쓴 것")
    for f in fruits:
        t = tab[f]
        print("    %-10s 맞춘 사진 %4d장 (%s) · 비율 불일치 %d"
              % (KOR[f], t["n_spec_fixed_rows"],
                 ", ".join("%s=%d" % kv for kv in sorted(t["n_spec_fixed"].items())) or "없음",
                 t["n_spec_mismatch_ratio"]))
    print("\n  상자 출처(남긴 사진) · 팀원 산출물 반영")
    for f in fruits:
        t = tab[f]
        print("    %-10s 상자 %s · 사과번호판정 %d · 복숭아중복후보 %d(%d그룹) · 의심마스크 %d"
              % (KOR[f], ", ".join("%s=%d" % kv for kv in sorted(t["boxes_sources"].items())),
                 t["n_apple_check"], t["n_peach_dup"], t["peach_dup_groups"], t["n_mask_audit"]))


def print_spec_fix_warning(spec_files):
    """🔴 2026-09-19 검수2 N2: 규격을 맞춘 파일이 **한 장이라도** 있으면 표준 출력 맨 끝에
    굵은 경고를 찍는다. 맞추고 진행하는 것은 총괄 결정(사용자 지시 «그걸 다 맞춰서 해줘») 이지만,
    **조용히** 맞춰서 나가면 아무도 모른 채 «한 번 줄인 것을 다시 줄인» 라벨이 정본이 된다.
    그래서 ① 몇 장을 맞췄나 ② 누구 폴더의 파일인가 ③ 그 사람에게 무엇을 알려야 하나 를 찍는다.
    맞춘 것이 없으면 아무것도 찍지 않는다(조용한 것이 정상이다)."""
    if not spec_files:
        return
    stems = {(e["fruit"], e["stem"]) for e in spec_files}
    print("\n" + "=" * 78)
    print("🔴🔴 **규격(팀 표준 2MP)을 맞춘 파일이 있습니다 — 사람이 볼 것** 🔴🔴")
    print("=" * 78)
    print("  맞춘 파일 %d개 · 사진 %d장 (종류별 %s)"
          % (len(spec_files), len(stems),
             ", ".join("%s=%d" % kv for kv in
                       sorted(collections.Counter(e["kind"] for e in spec_files).items()))))
    print("  팀원별(파일 소유자):")
    for own, n in sorted(collections.Counter(e["owner"] or "(모름)" for e in spec_files).items(),
                         key=lambda kv: -kv[1]):
        who = sorted({e["fruit"] for e in spec_files if (e["owner"] or "(모름)") == own})
        print("      %-16s %4d개  (%s)" % (own, n, ", ".join(KOR.get(f, f) for f in who)))
    print("  **원본 해상도에서 작업한 것으로 보입니다** — 그 팀원에게")
    print("  «`datasets_resized_2mp` (팀 표준 2MP 판)에서 작업해 달라» 고 알리십시오.")
    print("  (맞추기는 했지만 한 번 줄인 것을 또 줄이는 셈이라 1픽셀 두께 경계·작은 알이 사라집니다.)")
    print("  어느 파일인지는 README 의 «규격 맞춘 파일» 표와 build_summary.json 의")
    print("  `spec_fixed_files` 를 보십시오. 맞춘 것이 있을 때 **멈추고 싶으면** `--strict-spec`.")
    print("=" * 78)


def vanished_inputs(prev_reg, cur_reg):
    """직전 빌드에 «있음» 이던 입력이 이번에 «없음/못 읽음» 인 것 → 그 키 목록.

    2026-09-18 3차 결정 D3. «있다 → 없다» 는 거의 언제나 사고다(폴더가 옮겨졌거나 권한이 막혔거나).
    그대로 두면 그 칸이 **조용히 비어 나간다.** 직전 빌드가 없으면(첫 판) 견줄 것이 없으므로 빈 목록.

    이번에 **아예 읽지 않은** 입력(예: --fruits 로 과일을 줄여 그 과일 칸이 없는 경우)은 사고가
    아니므로 세지 않는다. 이번에도 읽었는데 «없음» 인 것만 본다.
    """
    out = []
    for k, v in sorted((prev_reg or {}).items()):
        if not v.get("exists"):
            continue
        cur = (cur_reg or {}).get(k)
        if cur is not None and not cur.get("exists"):
            out.append(k)
    return out


def print_changes(changes, prev_path, note=""):
    print("\n  직전 빌드와 견준 «바뀐 입력» (%s)" % (prev_path or "직전 빌드 없음"))
    if note:
        print("    ※ " + note)
    if not prev_path:
        return
    if not changes:
        print("    바뀐 것 없음")
        return
    for k, what, a, b in changes[:40]:
        print("    %-38s %-10s %s → %s" % (k, what, a, b))
    if len(changes) > 40:
        print("    … 그 밖 %d건은 build_summary.json 의 input_changes 에" % (len(changes) - 40))


def write_readme(out_dir, args, tab, fruits, problems, summary, changes=None, prev_path=None,
                 prev_note=""):
    L = []
    A = L.append
    A("# 네 과일 통합 데이터셋 — %s" % os.path.basename(out_dir))
    A("")
    A("작성: %s" % summary["date_iso"])
    A("만든 것: `semantic-segmentation/tools/build_merged_dataset.py` (자동 생성 폴더입니다)")
    A("")
    A("## 이 폴더가 무엇인가")
    A("")
    A("검수판 데이터셋(사람·AI 가 눈으로 본 결과)에 **라벨링 툴에서 사람이 누른 확정**을 덮어서")
    A("네 과일을 한 곳에 모은 것입니다. 원본(`datasets_resized_2mp`)·검수판·툴 `data/` 는")
    A("**한 글자도 바꾸지 않았습니다.** 전부 실제 파일 복사입니다(심볼릭 링크 아님).")
    A("")
    A("## 구조")
    A("")
    A("```")
    A("%s/" % os.path.basename(out_dir))
    for f in fruits:
        t = tab[f]
        extra = ""
        if t["n_instances"]:
            extra += "  instances/ (%d)" % t["n_instances"]
        if t["n_boxes"]:
            extra += "  boxes/ (%d + YOLO txt)" % t["n_boxes"]
        A("├── %-10s images/ (%d)  masks/ (%d)%s  manifest.csv" % (f, t["n_keep"], t["n_keep"], extra))
    A("├── manifest.csv        ← 네 과일 전부(제외한 사진 행도 들어 있음)")
    A("├── build_summary.json  ← 입력 지문·장수·소요 시간")
    A("└── README.md")
    A("```")
    A("")
    A("## 장수")
    A("")
    A("| | 검수판 manifest 행 | 남긴 사진 | 제외 | 열매 번호 | 상자 | 촬영 단위 | 분할 묶음 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for f in fruits:
        t = tab[f]
        A("| %s | %d | **%d** | %d | %d | %d | %d | %d |"
          % (KOR[f], t["n_manifest"], t["n_keep"], t["n_manifest"] - t["n_keep"],
             t["n_instances"], t["n_boxes"], t["n_sessions"], t["n_split_groups"]))
    A("| **합계** | %d | **%d** | %d | %d | %d | | |"
      % (sum(tab[f]["n_manifest"] for f in fruits), sum(tab[f]["n_keep"] for f in fruits),
         sum(tab[f]["n_manifest"] - tab[f]["n_keep"] for f in fruits),
         sum(tab[f]["n_instances"] for f in fruits), sum(tab[f]["n_boxes"] for f in fruits)))
    A("")
    A("**사람이 되살린 중복** %d장 — 검수판이 «거의 같은 사진» 이라고 뺐던 것을 사람이 되살려"
      " **묶음 대표와 함께** 남은 사진입니다. 사람 판정이 코드 규칙보다 위이므로"
      " 대표를 자동으로 빼지 않습니다(2026-09-18 결정 D1)."
      % sum(tab[f]["n_revived"] for f in fruits))
    A("")
    A("## 제외 사유")
    A("")
    A("| 과일 | 사유 | 장수 | 뜻 |")
    A("|---|---|---:|---|")
    for f in fruits:
        for k, v in sorted(tab[f]["reasons"].items()):
            A("| %s | `%s` | %d | %s |" % (KOR[f], k, v, REASON_KOR.get(k, "")))
    A("")
    # ── 2026-09-19 5차 «규격 검사·맞춤»
    sp = summary.get("spec") or {}
    A("## 규격 (팀 표준 2MP)")
    A("")
    A("이 폴더의 사진·마스크·번호·상자는 모두 **팀 표준 2MP 규격**입니다 —")
    A("**비율(가로세로) 유지 · 총 화소 2,073,600(=1440x1440) ±0.15% · 변의 길이는 8의 배수**.")
    A("그래서 실제로 쓰이는 해상도는 **5종**뿐입니다. 이 규칙은 0806 교수님미팅 지시로 만든")
    A("`semantic-segmentation/tools/resize_datasets_to_common_pixels.py` 의 것을 그대로 쓴 것이고,")
    A("그 결과물 `datasets_resized_2mp/` 이 **표준 그 자체**입니다(사진 크기는 여기서 가져옵니다).")
    A("")
    # 🔴 2026-09-19 검수2 N1: «±0.15% 는 8의 배수 반올림의 최대오차» 라는 설명은 **틀렸다**.
    A("**±0.15% 가 어디서 온 값인가** — 아래 표준표 5종을 모두 담는 **가장 좁은 값**입니다"
      "(`1664x1248` = +0.148%).")
    A("8의 배수 반올림이 임의 크기에서 만드는 오차는 이보다 크고 **최대 ±0.49%** 까지 갑니다."
      " 그래서 규격 위반 판정은")
    A("**표준표(`datasets_resized_2mp`)와의 일치를 먼저** 보고, 총 화소 검사는 **표준을 찾지 못한"
      " 사진에만** 적용합니다.")
    A("")
    A("| 해상도 | 총 화소 | 2,073,600 과의 차 | %s |" % " | ".join(KOR[f] for f in fruits))
    A("|---|---:|---:|%s" % ("---:|" * len(fruits)))
    allsz = {}
    for f in fruits:
        for k, v in ((sp.get(f) or {}).get("std_sizes") or {}).items():
            allsz.setdefault(k, {})[f] = v
    for k in sorted(allsz, key=lambda x: -sum(allsz[x].values())):
        w0, h0 = (int(v) for v in k.split("x"))
        A("| `%s` | %s | %+.3f%% | %s |"
          % (k, "{:,}".format(w0 * h0), (w0 * h0 - SPEC_TARGET_PIXELS) * 100.0 / SPEC_TARGET_PIXELS,
             " | ".join(str(allsz[k].get(f, 0)) for f in fruits)))
    A("")
    A("**읽어 들인 라벨 산출물을 표준과 대조해 맞춘 것**(`manifest.csv` 의 `spec_fixed` 칸)")
    A("")
    A("| 과일 | 맞춘 사진 | 종류별 | 비율이 달라 쓰지 못한 것 | 표준을 찾지 못한 사진 |")
    A("|---|---:|---|---:|---:|")
    for f in fruits:
        t, q = tab[f], (sp.get(f) or {})
        A("| %s | %d | %s | %d | %d |"
          % (KOR[f], t["n_spec_fixed_rows"],
             ", ".join("`%s`=%d" % kv for kv in sorted(t["n_spec_fixed"].items())) or "—",
             t["n_spec_mismatch_ratio"], q.get("n_no_std", 0)))
    A("| **합계** | **%d** | | **%d** | **%d** |"
      % (sum(tab[f]["n_spec_fixed_rows"] for f in fruits),
         sum(tab[f]["n_spec_mismatch_ratio"] for f in fruits),
         sum((sp.get(f) or {}).get("n_no_std", 0) for f in fruits)))
    A("")
    # ── 🔴 2026-09-19 검수2 N2: 맞춘 파일을 **한 줄씩** 적는다. «몇 장» 만으로는 누구에게
    #    «표준 폴더에서 작업해 달라» 고 알려야 하는지 알 수 없다.
    sfiles = summary.get("spec_fixed_files") or []
    A("**규격 맞춘 파일**(한 줄에 하나 · `spec_fixed` 칸의 내역)")
    A("")
    if not sfiles:
        A("맞춘 파일이 **없습니다** — 읽어 들인 모든 산출물이 이미 팀 표준 2MP 였습니다"
          "(이것이 정상입니다).")
    else:
        A("| 과일 | stem | 종류 | 원래 → 맞춘 크기 | 출처 | 출처 폴더 소유자 |")
        A("|---|---|---|---|---|---|")
        for e in sfiles[:200]:
            A("| %s | `%s` | `%s` | `%s` → `%s` | `%s` | **%s** |"
              % (KOR.get(e.get("fruit"), e.get("fruit", "")), e.get("stem", ""), e.get("kind", ""),
                 e.get("src_size", ""), e.get("dst_size", ""), e.get("source", "") or "-",
                 e.get("owner") or "(모름)"))
        if len(sfiles) > 200:
            A("")
            A("… 이하 %d개 생략 — 전부는 `build_summary.json` 의 `spec_fixed_files` 에 있습니다."
              % (len(sfiles) - 200))
        A("")
        A("🔴 **이 표에 줄이 있으면 그 «출처 폴더 소유자» 에게 알리십시오** —")
        A("«원본 해상도에서 작업한 것으로 보입니다. `datasets_resized_2mp`(팀 표준 2MP 판)에서")
        A("작업해 주십시오.» 맞추기는 했지만 한 번 줄인 것을 또 줄이는 셈이라 1픽셀 두께 경계와")
        A("작은 알이 되돌릴 수 없이 사라집니다(위 `problems` 의 `spec_warn` 을 함께 보십시오).")
    A("")
    A("`spec_fixed` 는 `mask:4032x3024->1664x1248;boxes:4032x3024->1664x1248` 처럼 적습니다"
      "(맞춘 것이 없으면 `-`). 맞추는 방법은 **원래 리사이즈 규칙과 같습니다** —")
    A("사진은 `LANCZOS`, 마스크·번호는 **최근접(NEAREST)**(보간하면 없는 라벨값·번호가 생깁니다),")
    A("상자 json 의 **픽셀 좌표는 비율 변환**, YOLO txt 는 0~1 정규화라 균일 배율에는 값이 바뀌지 않아")
    A("그대로 둡니다. 마스크·번호를 줄일 때마다 «전경이 얼마나 줄었나 · 번호가 몇 개 사라졌나» 를"
      " `problems` 에 `spec_warn` 으로 적습니다(최근접으로 줄이면 1픽셀 두께 경계와 작은 알은"
      " 되돌릴 수 없이 사라집니다).")
    A("가로세로비가 표준과 **0.5% 넘게** 다르면 맞추지 않고 **그 파일을 채택하지 않습니다**"
      "(마스크는 다른 후보로 넘기고, 후보가 없으면 그 사진을 `excluded_spec` 으로 뺍니다).")
    A("")
    A("**왜 이 칸이 필요한가** — 팀원이 **원본 해상도**(예: 복숭아 4032x3024)로 새 마스크·번호·상자를")
    A("만들어 자기 폴더에 두면, 아무 검사 없이 섞이면 학습 때 크기가 안 맞아 조용히 깨집니다.")
    A("그래서 읽어 들이는 모든 산출물을 표준과 대조합니다. 사진이 표준 크기가 아니면"
      " **표준본(`datasets_resized_2mp`)을 먼저 씁니다**(원본 해상도 사진이 들어온 것이므로).")
    A("")
    A("**실측(2026-09-19 · 스크립트가 세는 값과 별개로 사람이 확인한 것)**")
    A("")
    A("- 크기가 바뀌는 곳은 **0 원본 → 1 팀 표준(`datasets_resized_2mp`) 한 군데뿐**입니다 —")
    A("  사과 720x1280 → 1080x1920 · 블루베리 4K 128장 → 1080x1920 · 복숭아 6종 → 4종 ·")
    A("  포도 CERTH 2160x3840 → 1080x1920.")
    A("- **1 팀 표준 → 2 검수판 → 3 통합판은 크기 변화가 0**입니다(장수만 줄어듭니다).")
    A("- 통합 v3 의 이미지·마스크 **4,071장 전부 2MP**, 툴 `masks_fixed` 복숭아 **39장 전부 2MP**,")
    A("  박성문·임성후 상자 json 의 `image_size_hw` **4,823건 전부 2MP 와 일치**했습니다.")
    A("- 즉 «규격 같음» 은 «가로세로가 같음» 이 아니라 **«화소 수가 같음(2,073,600±0.15%) · 해상도 5종»**")
    A("  입니다.")
    A("")
    A("## 판정이 어디서 왔나 (`manifest.csv` 의 `source` 칸)")
    A("")
    A("| 값 | 뜻 |")
    A("|---|---|")
    A("| `human_confirmed` | 툴에서 사람이 **확정**(status.json 의 `confirmed` 칸) |")
    A("| `human_unconfirmed` | **확정 칸 없이 사람이 누른 판정**(`confirmed` 칸은 없고 `by` 가 «AI» 로 "
      "시작하지 않는 것). 사이클 2 이전 저장분뿐 아니라 **오늘 사람이 마스크만 고쳐 저장한 것**도 "
      "여기 들어옵니다(2026-09-18 이전 이름 `human_legacy`) |")
    A("| `ai` | 툴에 AI 판정만 있고 사람은 아직 안 누름 → 검수판 판정을 그대로 씀 |")
    A("| `reviewed` | 툴에 아무 기록도 없음 → 검수판 판정 그대로 |")
    A("")
    A("남긴 사진의 출처별 장수: " + " · ".join(
        "%s(%s)" % (KOR[f], ", ".join("%s=%d" % kv for kv in sorted(tab[f]["sources"].items())))
        for f in fruits))
    A("")
    # 2026-09-19 (툴 사이클 4 «종류별 확정»): 확정 칸이 셋이고 서로 독립이므로 표도 종류별로 센다.
    A("### 종류별 사람 확정 수 (2026-09-19 부터)")
    A("")
    A("툴의 확정 칸은 **셋이고 서로 독립**입니다 — 마스크 `confirmed` · 상자 `confirmed_boxes` ·")
    A("번호 `confirmed_instances`. 마스크를 확정해도 상자·번호는 «미확정» 그대로입니다(반대도 같습니다).")
    A("아래는 **뺀 사진까지 포함한** 장수입니다(확정이 제외의 이유일 수 있으므로).")
    A("")
    A("| 과일 | 마스크 확정 | 상자 확정 | 그 판정 | 번호 확정 | 그 판정 |")
    A("|---|---:|---:|---|---:|---|")
    for f in fruits:
        t = tab[f]
        A("| %s | %d | %d | %s | %d | %s |"
          % (KOR[f], t["n_confirmed_mask"], t["n_confirmed_boxes"],
             ", ".join("`%s`=%d" % kv for kv in sorted(t["boxes_confirmed"].items())) or "—",
             t["n_confirmed_instances"],
             ", ".join("`%s`=%d" % kv for kv in sorted(t["instances_confirmed"].items())) or "—"))
    A("| **합계** | **%d** | **%d** | | **%d** | |"
      % (sum(tab[f]["n_confirmed_mask"] for f in fruits),
         sum(tab[f]["n_confirmed_boxes"] for f in fruits),
         sum(tab[f]["n_confirmed_instances"] for f in fruits)))
    A("")
    A("| 칸 | 값 | 뜻 |")
    A("|---|---|---|")
    A("| `boxes_confirmed_status` | `ok`·`fixed` | 사람이 **상자를 확정** → 툴 `boxes/<stem>.json` 을"
      " 사람 상자로 채택(`boxes_source=tool`) |")
    A("| | `exclude`·`flag` | 사람이 상자를 «제외»·«문제 있음» 으로 확정 → **그 사진의 상자는 없음**"
      "(json·YOLO txt 를 만들지 않습니다) |")
    A("| | `-` | 상자 확정 없음 → `psm_gt` > `lsh` 순서 |")
    A("| `boxes_confirmed_by`·`_at` | 이름·시각 | 상자를 확정한 사람과 시각(확정이 없으면 빈칸) |")
    A("| `instances_confirmed_status` | `ok`·`fixed` | 사람이 **번호를 확정** → `instances_fixed/`"
      "(없으면 원본 번호본)을 채택(`instances_source=tool_confirmed`) |")
    A("| | `exclude`·`flag` | 번호 없음(`instances/` 에 파일을 만들지 않습니다) |")
    A("| | `-` | 번호 확정 없음 → 지금까지의 우선순위 그대로 |")
    A("")
    A("")
    # 2026-09-19 «개수 세기» 사이클1 (지시서 §1-4) — 카운팅 논문 지표(MAE·RMSE·R²)를 재려면
    # «이 사진에 열매가 몇 개인가» 가 manifest 에 있어야 한다. 사람이 따로 치는 칸은 두지 않았다.
    A("### 개수 칸 (2026-09-19 부터)")
    A("")
    A("카운팅(열매 수 세기) 지표를 재려면 «이 사진에 열매가 몇 개인가» 가 표에 있어야 합니다.")
    A("**개수를 사람이 따로 치는 칸은 두지 않습니다** — 상자 확정·번호 확정이 곧 개수 확정입니다.")
    A("")
    A("| 칸 | 뜻 |")
    A("|---|---|")
    A("| `n_boxes` | **이 폴더에 나간** `boxes/<stem>.json` 의 상자 수. 빈칸 = 상자 파일이 없음 |")
    A("| `n_instances` | **이 폴더에 나간** `instances/<stem>.png` 의 번호 수(이진 마스크로 자르고"
      " 규격을 맞춘 뒤의 값). 빈칸 = 번호 파일이 없음 |")
    A("| `n_count_human` | 사람이 확정한 열매 개수. **번호 확정이 있으면 `n_instances`, 없고 상자"
      " 확정이 있으면 `n_boxes`, 둘 다 없으면 빈칸**. 둘 다 확정인데 **수가 다르면 빈칸**입니다"
      " (2026-09-19 결정 — 사람이 고르지 않은 수는 표에 넣지 않습니다) |")
    A("| `count_source` | 그 개수가 어디서 나왔나 — `instances` · `boxes` · `conflict`(어긋나 비움)"
      " · `none` |")
    A("| `count_conflict` | `1` = 상자와 번호를 둘 다 확정했는데 개수가 다름 → `n_count_human` 은"
      " **빈칸**이고 `count_source=conflict` 입니다(툴이 고르지 않습니다 — 사람이 고칠 때까지 이"
      " 사진은 카운팅 지표에서 빠집니다). `0` = 어긋남 없음 |")
    A("| `n_gt` | **정답 개수** — 박성문 `bbox_outputs/<과일>/gt_boxes/csv/detections.csv` 의 그 사진"
      " 줄 수. 블루베리는 정답 상자가 없어 빈칸입니다(`all/` 은 watershed 자동 추정이라 정답이 아닙니다)."
      " 카운팅 MAE·RMSE·R²(`farjon2023countingreview` p.16 식 (1)~(4))의 정답 쪽입니다."
      " **뺀 사진에도 값이 있습니다** — 정답은 이 폴더에 무엇이 나갔나와 무관합니다 |")
    A("")
    A("뺀 사진은 나간 파일이 없으므로 다섯 칸 모두 `-` 입니다(`0` 이라고 적으면 «열매가 없는 사진» 으로")
    A("읽혀 MAE·R² 에 그대로 섞입니다). `0` 과 빈칸도 다릅니다 — `0` = 열매가 없다, 빈칸 = 셀 수 없다.")
    A("")
    A("번호가 먼저인 까닭: 번호는 알 하나하나에 붙은 라벨이고 상자는 그 번호에서 만든 것입니다")
    A("(툴 `/api/boxes_seed` 는 번호 마스크가 있으면 번호마다 상자 하나를 만듭니다). 사람이 상자를")
    A("합치거나 나눌 수 있어 상자는 «개수의 원본» 이 아닙니다.")
    A("")
    A("같은 규칙이 툴 쪽에도 있습니다 — `app/boxes.py human_count()`(화면의 «개수» 칸)와")
    A("`export/export_dataset.py counts_rows()`(`counts.csv`). 세 구현이 갈라지지 않는지는")
    A("`tools/tests_merged_260918/counts/test_counts.py` 가 같은 입력을 넣어 대조합니다.")
    A("")
    A("사람 판정을 어떻게 반영하는가: `ok`=남김(원본 마스크) · `fixed`=툴 `masks_fixed/` 마스크 사용 ·")
    A("`exclude`=제외(`human_exclude`) · `flag`=제외(`confirmed_flag`, 아직 고칠 것이라 «확실한 데이터» 가 아님).")
    A("**사람이 `ok` 로 확정하면 검수판에서 뺐던 사진도 되살아납니다**(`note` 에 «검수판 제외를 사람이 되살림»).")
    A("")
    A("## `session`(촬영 단위)과 `split_group`(분할 묶음)")
    A("")
    A("**분할(폴드 나누기)은 `session` 단위 GroupKFold 를 권고합니다.** 같은 촬영에서 나온 사진이")
    A("학습과 시험으로 갈라지면 점수가 부풀기 때문입니다. `split_group` 은 «그보다 잘게 나눌 때")
    A("지켜야 하는 최소 조건» 입니다.")
    A("")
    A("| 과일 | `session` 을 무엇으로 정했나 | 근거 |")
    A("|---|---|---|")
    A("| 사과 | 검수판 manifest 의 `session` 칸 그대로(파일명에서 끝 번호를 뗀 것) | `datasets_reviewed_260917/README.md` |")
    A("| 블루베리 | 검수판 manifest 의 `session` 칸 그대로(«Camera N Video (X)») | 같은 곳 |")
    A("| 복숭아 | 파일명 `210629-t1-01` → **`210629-t1`**(날짜 + 나무 번호). `t2-of10`~`of18` 은 t2 의 곁가지라 t2 에 넣음 | 파일명 규칙(125장 전부가 `YYMMDD-t번호[-of번호]-장번호`) |")
    A("| 포도 | **미확인** — 사진 한 장을 한 촬영으로 둠 | 아래 |")
    A("")
    A("🔴 **포도의 촬영 단위는 확인하지 못했습니다(미확인).** 근거:")
    A("원본 CERTH COCO 주석(`share_grape_certh/CERTH_annotations.zip`)의 `file_name` 이 `0.png`…`2501.png`")
    A("번호뿐이고 폴더 구분이 없으며 `date_captured` 가 전부 빈 문자열입니다. 툴 `data/grape/duplicates.json`")
    A("의 `sequence_stats` 도 `n_sequences`=1 이고 이웃 번호 2,501쌍의 상관계수 중앙값이 0.110 이라")
    A("**번호 순서가 촬영 순서가 아닙니다.** 그래서 포도는 `session` 을 만들지 않고 사진마다 하나로 두었습니다.")
    A("")
    A("🔴 **그래서 포도는 `session` 으로 GroupKFold 를 돌려도 사실상 무작위 분할입니다**"
      "(2026-09-18 2차 검수 실측: 남긴 포도 %d장의 `session` 이 %d개 = 장마다 하나, "
      "`split_group` 도 %d개로 **전부 한 장짜리**입니다). 즉 포도에는 **지금 누수를 막는 장치가 없습니다** "
      "— 검수판이 «거의 같은 사진» 을 미리 빼 둔 것이 유일한 방어입니다. "
      "포도 점수를 다른 과일과 나란히 놓을 때는 이 차이를 각주로 남기십시오."
      % (tab["grape"]["n_keep"], tab["grape"]["n_sessions"], tab["grape"]["n_split_groups"])
      if "grape" in tab else "")
    A("")
    A("`split_group` 은 복숭아·포도의 경우 **툴 `duplicates.json` 의 근접 중복 묶음 ∪ 같은 `session`** 으로")
    A("만들었습니다(사과·블루베리는 검수판 manifest 의 값을 그대로 씁니다).")
    A("")
    # 🔴 2026-09-19 «개수 세기» 사이클4(M13): 위 경고는 본문 한 문단이라 표만 옮겨 적으면 사라진다.
    # 논문·발표에 **그대로 붙일 각주 문장**을 만들어 둔다 — 옮겨 적는 사람이 다시 쓰지 않게.
    A("### 📌 논문에 그대로 붙일 각주 (포도 분할)")
    A("")
    A("> **각주.** 포도(CERTH)는 촬영 단위를 확인할 수 없어(원본 주석의 `file_name` 이 일련번호뿐이고")
    A("> `date_captured` 가 전부 비어 있음) 사진 한 장을 한 촬영으로 두었다. 따라서 **포도에는 촬영")
    A("> 단위 누수를 막는 장치가 없으며**, `session` 단위 GroupKFold 를 적용해도 사실상 무작위")
    A("> 분할이다. 다른 세 과일(사과·블루베리·복숭아)은 촬영 단위로 묶어 나누었다. 포도 점수를")
    A("> 나머지와 나란히 비교할 때는 이 차이를 고려해야 한다.")
    A("")
    A("(옮겨 적을 때 이 문장을 **줄이지 마십시오** — «포도만 장치가 없다» 가 핵심입니다.)")
    A("")
    A("## `manifest.csv` 의 칸")
    A("")
    A("`" + "` · `".join(MANIFEST_COLS) + "`")
    A("")
    A("`action` = `keep`·`mask_fixed`·`image_replaced`·`needs_human`(여기까지 남긴 사진) ·")
    A("`excluded_duplicate`·`excluded_not_grape`·`excluded_human`·`excluded_flag`·"
      "`excluded_spec`·`excluded_missing`(뺀 사진).")
    A("`needs_human` 은 «마스크에 문제가 있다고 AI 가 표시한 것» 이고 검수판과 마찬가지로 **남겨 두었습니다**.")
    A("마지막 세 칸(`rule_pending`·`overlap_neighbors`·`instances_source`)은 검수판의 정보를 잃지 않으려고")
    A("덧붙인 것입니다. `rule_pending` 은 오류가 아니라 **규칙이 정해지지 않은 사진**입니다"
      "(남긴 사진 기준 %s)."
      % " · ".join("%s %d" % (KOR[f], tab[f]["n_rule_pending"]) for f in fruits))
    A("")
    A("## 팀원 산출물을 어디에 반영했나")
    A("")
    A("| 칸 | 값 | 어디서 왔나 |")
    A("|---|---|---|")
    A("| `boxes_source` | `tool` | 라벨링 툴에서 **사람이 그린 상자 + 사람이 확정**"
      "(`confirmed_boxes` 가 `ok`·`fixed`)한 것 (`data/<과일>/boxes/`) |")
    A("| | `tool_unconfirmed` | 툴에 상자 json 은 있으나 **사람이 확정하지 않은 초벌 저장본**이고,"
      " 다른 출처도 없는 경우. **표시만 하고 쓰지 않습니다**(`has_boxes=0`) |")
    A("| | `psm_gt` | 박성문 `bbox_outputs/<과일>/gt_boxes/` — **정답 마스크에서 뽑은** 상자. YOLO txt 도 그쪽 것을 그대로 복사 |")
    A("| | `lsh` | 임성후 `bbox_outputs/<과일>/all/` — watershed **추정** 상자(**미검증**). 박성문 gt 가 없는 과일에서만 |")
    A("| | `none` | 상자 없음(상자 확정이 `exclude`·`flag` 인 사진도 여기) |")
    A("| `apple_check_verdict` | 예: `ok_one_apple=2 duplicate_polygon=1 · 확정오류 1` | 박성문 `apple_check/review_list.csv`(사람 눈 판정) + `confirmed_errors.csv` |")
    A("| `verdict_source` | `psm_review_list` / `psm_review_list+confirmed_errors` / `psm_confirmed_errors` / `none` | 같은 곳 |")
    A("| `peach_dup_candidate` | `burst_ofNN` / `pair_NN` / 빈칸 | 최인훈 `dup_audit_260917/peach/` — **제외하지 않습니다**(교수님 결정 항목) |")
    A("| `mask_audit_reason` | 예: `bottom_5pct_ratio` | 최인훈 `mask_audit_260908/suspects.csv` — 전경 비율이 아래 5% 인 마스크 |")
    A("| `instances_source` | `tool_confirmed`/`instances_fixed`/`detect_seed`/`psm_watershed`"
      "/`reviewed_number_mask`/`none` | 아래 «값 사전» |")
    A("")
    # 2026-09-18 3차 D9: 값은 전부 영문 토큰이고, 뜻을 여기 한 곳에 모아 둔다.
    A("### `instances_source` 값 사전 (열매 번호가 어디서 왔나)")
    A("")
    A("| 값 | 뜻 |")
    A("|---|---|")
    A("| `tool_confirmed` | 툴에서 **사람이 번호를 확정**(`confirmed_instances` 가 `ok`·`fixed`)한 것."
      " 파일은 `instances_fixed/` 를 먼저 쓰고 없으면 원본 번호본을 씁니다(2026-09-19 부터) |")
    A("| `instances_fixed` | 라벨링 툴에서 **사람이 고친** 번호 마스크(`data/<과일>/instances_fixed/`)."
      " **번호 확정은 아직 없는** 상태입니다 |")
    A("| `detect_seed` | 검출 팀 watershed **자동 초벌**(블루베리). 사람이 검수한 것이 아닙니다 |")
    # 2026-09-19 «개수 세기» 사이클5 — 복숭아 번호본을 더했다(SEED_DIRS 주석 참조)
    A("| `psm_watershed` | 박성문 님 watershed **자동 초벌**(복숭아 `bbox_outputs/peach/all/instance_maps`)."
      " 값만 다르고 성격은 `detect_seed` 와 같습니다 — **추정이고 사람이 검수한 것이 아닙니다.**"
      " 🔴 **0920 빌드부터** 복숭아에 `instances/` 가 생깁니다(그 전 판에는 없었습니다) |")
    A("| `reviewed_number_mask` | 검수판 **원본 마스크 자체가 번호 마스크**인 경우(사과). "
      "2026-09-18 이전 판에서는 한글 `원본번호` 였습니다 |")
    A("| `none` | 열매 번호 없음 |")
    A("")
    A("상자 우선순위는 **툴에서 사람이 «확정» 한 상자 > 박성문 gt > 임성후 > 없음** 입니다"
      "(2026-09-19 변경). 툴에 상자 json 이 있어도 **사람이 확정하지 않았으면 채택하지 않습니다** —"
      " 확정 없는 초벌 저장본이 정답 상자를 밀어내면 안 되기 때문입니다"
      "(2026-09-18 2차 검수 M2-7 에서 빈 json 이 박성문 정답 상자 9개·4개를 실제로 지웠습니다).")
    A("남긴 사진의 상자 출처: " + " · ".join(
        "%s(%s)" % (KOR[f], ", ".join("%s=%d" % kv for kv in sorted(tab[f]["boxes_sources"].items())))
        for f in fruits))
    A("")
    A("🔴 **교수님 결정 항목**")
    A("")
    A("- **복숭아 중복 후보** — 최인훈 검수에서 `210629-t2-ofNN` 9그룹 45장이 «같은 복숭아를 5각도로 찍은 버스트»")
    A("  로 확인됐습니다. 우리 검수판은 복숭아를 **한 장도 빼지 않았으므로** 이 판에도 전부 들어 있습니다.")
    A("  얼마나 솎을지는 교수님이 정하실 일이라 `peach_dup_candidate` 칸에 **표시만** 했습니다"
      "(이 판 %d장 · %d그룹)." % (tab["peach"]["n_peach_dup"] if "peach" in tab else 0,
                                 tab["peach"]["peach_dup_groups"] if "peach" in tab else 0))
    A("- **의심 마스크** — `mask_audit_reason` 이 붙은 사진(이 판 %d장)은 전경이 아주 작습니다. 빼지 않았습니다."
      % sum(tab[f]["n_mask_audit"] for f in fruits))
    A("- **사과 번호 오류** — `apple_check_verdict` 가 붙은 사진(이 판 %d장)은 박성문·사람 눈 판정입니다."
      % sum(tab[f]["n_apple_check"] for f in fruits))
    A("  `duplicate_polygon`·`one_apple_two_ids` 등은 **번호(instances) 쪽 문제**라 세그 마스크는 그대로 씁니다.")
    if changes is not None:
        A("")
        A("## 직전 빌드와 견준 «바뀐 입력»")
        A("")
        # 2026-09-18 3차 D3: «읽지 못한 입력» 이 README 에도 보이게 한다.
        if summary.get("missing_inputs"):
            A("읽지 못한 입력 **%d개** — 그 칸은 비어 나갔습니다: `%s`"
              % (len(summary["missing_inputs"]), "` · `".join(summary["missing_inputs"])))
            A("")
        if summary.get("vanished_inputs"):
            A("🔴 그중 **직전 빌드에는 있던 것 %d개**(`%s`)가 사라졌는데 `--allow-missing-input` 으로"
              " 그대로 만들었습니다. 폴더가 옮겨졌거나 권한이 막힌 것일 수 있으니 확인하십시오."
              % (len(summary["vanished_inputs"]), "` · `".join(summary["vanished_inputs"])))
            A("")
        if not prev_path:
            A("직전 빌드가 없어 견주지 않았습니다(이 폴더가 첫 판입니다).")
        elif not changes:
            A("견준 곳: `%s` — **바뀐 입력 없음**." % prev_path)
            if prev_note:
                A("")
                A("※ " + prev_note)
        else:
            A("견준 곳: `%s`" % prev_path)
            if prev_note:
                A("")
                A("※ " + prev_note)
            A("")
            A("| 입력 | 무엇이 | 그때 | 지금 |")
            A("|---|---|---|---|")
            for k, what, a, b in changes[:60]:
                A("| `%s` | %s | %s | %s |" % (k, what, a, b))
            if len(changes) > 60:
                A("")
                A("그 밖 %d건은 `build_summary.json` 의 `input_changes` 에 있습니다." % (len(changes) - 60))
    A("")
    A("## 주의")
    A("")
    A("- 마스크는 **전부 L 모드 0/255** 로 통일했습니다(사과 원본은 열매 번호, 블루베리 원본은 RGB 였습니다).")
    A("- 사과의 `instances/` 는 **원본 마스크의 열매 번호**이고, 블루베리·복숭아의 `instances/` 는")
    A("  검출 팀이 만든 **자동 초벌**(watershed)입니다 — 사람이 검수한 것이 아닙니다.")
    A("- 🔴 **복숭아 `instances/` 는 0920 빌드부터 생깁니다**(2026-09-19 «개수 세기» 사이클5)."
      " 값은 `instances_source=psm_watershed`(추정)입니다. 번호본이 있는 사진은 125장이지만"
      " **사람이 «제외» 로 확정한 사진은 빠집니다**(2026-09-19 22:55:23 에 한 장 —"
      " 그때 실측 124장 · 사이클5 2차). 그 전 판(`_260918`·`_v2`·`_v3`)에는"
      " 복숭아 번호가 **아예 없었습니다** — 두 판을 대조할 때 이 차이를 «데이터가 바뀐 것» 으로 읽지 마십시오.")
    A("- 번호는 «이진 마스크가 번호 마스크를 자른다» 규칙으로 잘라 저장했습니다(마스크 밖 번호 0개).")
    A("- 🔴 **`mask_source=masks_fixed` 경로는 아직 실자료로 검증되지 않았습니다.** 지금까지의 빌드에서는"
      " 해당 행이 0건이었습니다(사람이 툴에서 «수정함» 으로 확정한 사진이 아직 없기 때문). 이 판에 그 행이"
      " 생겼다면 **그중 한 장을 눈으로 열어** 툴에서 고친 마스크가 맞는지 확인하십시오(2026-09-18 결정 D5).")
    A("- 규격은 **전부 팀 표준 2MP**(비율 유지 · 총 화소 2,073,600±0.15% · 해상도 5종)로 맞췄습니다."
      " 자체 검사가 «출력 크기 = 표준 · 총 화소 ±0.15% · YOLO 0~1» 을 장마다 봅니다(위 «규격» 절).")
    A("- 사과는 출처마다 라벨 규칙이 다릅니다(MinneApple = 가려진 부분까지 · dataset1~4 = 보이는 것만).")
    A("  **성능은 출처별로 나눠 보고하십시오.**")
    # 🔴 2026-09-19 «개수 세기» 사이클4(M15 · 사이클3 3차 §2-7). 이 두 줄이 없으면 개수 정확도가
    # «우리 방법의 성능» 으로 읽힌다. 튜닝 자료가 사과뿐이고, 입력이 정답 마스크라 **상한**이다.
    A("- 🔴 **개수(카운팅) 숫자를 인용할 때 반드시 같이 적을 것 — 두 문장입니다.**")
    A("  ① **워터셰드 매개변수(`peak_frac` 1.1 · `radius_pct` 90)는 사과 정답 1,001장으로 골랐고**")
    A("  복숭아·블루베리에는 그대로 옮겨 썼습니다. 복숭아 정답으로 다시 재면 더 작은 값이 계속")
    A("  좋아집니다(0.7 → MAE 0.14 · 0.9 → 0.26 · 1.1 → 0.37 로 **단조**) — 즉 복숭아 최적은 훑은")
    A("  범위의 **끝값 아래**(0.7 이하)이고, 지금 값은 복숭아에 맞춘 값이 아닙니다.")
    A("  ② **보고한 개수 정확도는 «정답 마스크를 입력했을 때» 의 값 = 상한입니다.**")
    A("  지금 숫자는 전부 `mask_source=gt` 로 낸 것이고, **모델이 예측한 마스크**를 넣은 실험은")
    A("  아직 하지 않았습니다(재학습 단계 몫). 실제 오차는 이보다 커집니다.")
    A("  → 표 캡션에 «정답 마스크 입력 기준(상한)» 이라고 못 박으십시오.")
    A("- 개수 지표(MAE·RMSE·R²)는 `tools/count_metrics.py --counts <이 폴더>/manifest.csv` 로 냅니다")
    A("  (`farjon2023countingreview` p.16 식 (1)~(4)). 센 값과 정답이 **같은 파일**에서 나온 줄에는")
    A("  «⚠순환» 이 붙습니다 — 그 줄은 정확도가 아니라 «두 경로가 어긋나지 않는다» 는 확인입니다.")
    if problems:
        A("")
        A("## 이번 빌드에서 생긴 문제 (%d건)" % len(problems))
        A("")
        for p in problems[:50]:
            A("- %s" % p)
        if len(problems) > 50:
            A("- … 그 밖 %d건은 `build_summary.json` 의 `problems` 에 있습니다." % (len(problems) - 50))
    A("")
    A("## 다시 만들려면")
    A("")
    A("```bash")
    A("PY=/home/kds0206/.conda/envs/kwak/bin/python")
    A("cd /data/project/2026summer/kds0206/semantic-segmentation")
    A("$PY tools/build_merged_dataset.py --dry-run     # 무엇이 들어갈지만 본다")
    A("$PY tools/build_merged_dataset.py               # 오늘 날짜 폴더를 새로 만든다")
    A("```")
    A("")
    A("같은 날 두 번 만들려면 `--suffix <이름>` 을 주십시오(폴더가 있으면 **덮어쓰지 않고 멈춥니다**).")
    A("자세한 절차는 `문서/260918_통합데이터셋_갱신법.md` 를 보십시오.")
    A("")
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ────────────────────────────────── main
def main(argv=None):
    ap = argparse.ArgumentParser(description="네 과일 통합 데이터셋 빌드")
    ap.add_argument("--date", default=datetime.date.today().strftime("%y%m%d"),
                    help="폴더 이름에 쓸 날짜 YYMMDD (기본 오늘)")
    ap.add_argument("--out-root", default=KDS)
    ap.add_argument("--suffix", default="", help="같은 날 두 번 만들 때 폴더 이름 뒤에 붙일 말")
    ap.add_argument("--fruits", nargs="+", default=FRUITS, choices=FRUITS)
    ap.add_argument("--dry-run", action="store_true", help="장수·제외 사유만 보여 주고 파일은 쓰지 않음")
    ap.add_argument("--tool-data", default=DEF_TOOL_DATA)
    ap.add_argument("--reviewed-260916", default=DEF_REV916)
    ap.add_argument("--reviewed-260917", default=DEF_REV917)
    ap.add_argument("--original-root", default=DEF_ORIG)
    ap.add_argument("--psm-root", default=DEF_PSM, help="박성문 폴더(없으면 «없음» 으로 진행)")
    ap.add_argument("--cih-root", default=DEF_CIH, help="최인훈 폴더(없으면 «없음» 으로 진행)")
    ap.add_argument("--lsh-root", default=DEF_LSH, help="임성후 폴더(없으면 «없음» 으로 진행)")
    ap.add_argument("--prev", default=None,
                    help="견줄 직전 빌드의 build_summary.json (기본: 가장 최근 datasets_merged_* 를 자동으로 찾음)")
    ap.add_argument("--no-prev", action="store_true", help="직전 빌드와 견주지 않음")
    ap.add_argument("--allow-missing-input", action="store_true",
                    help="직전 빌드에 있던 입력이 사라져도 멈추지 않고 경고만 하고 진행(기본은 exit 3)")
    ap.add_argument("--strict-spec", action="store_true",
                    help="규격(팀 표준 2MP)을 맞춘 파일이 한 개라도 있으면 만들지 않고 멈춘다(exit 4)."
                         " 기본은 맞추고 진행하며 경고만 찍는다(2026-09-19 검수2 N2)")
    args = ap.parse_args(argv)

    t0 = time.time()
    # ── 2026-09-18 2차 검수 M2-3(안전): 폴더 이름으로 출력이 엉뚱한 곳에 생기지 않게 막는다.
    #    `--date ../../etc` · `--suffix ../탈출` 은 out_root 밖(검수판·원본 폴더 안까지)에
    #    폴더를 만들 수 있었다. 이름 칸에는 경로 구분자·`..`·제어문자를 넣지 못하게 한다.
    for lbl, val in (("--date", args.date), ("--suffix", args.suffix)):
        if val and (os.sep in val or (os.altsep and os.altsep in val)
                    or val in (".", "..") or val.startswith("..") or "\x00" in val):
            print("멈춥니다 — %s 에 경로를 넣을 수 없습니다: %r" % (lbl, val))
            return 2
    if not args.date:
        print("멈춥니다 — --date 가 비었습니다(폴더 이름이 `datasets_merged_` 가 됩니다).")
        return 2
    name = "datasets_merged_%s%s" % (args.date, ("_" + args.suffix) if args.suffix else "")
    out_dir = os.path.join(args.out_root, name)
    # 출력이 입력 폴더 **안**이면 멈춘다(입력에 쓰지 않는다는 약속을 구조로 지킨다).
    real_out = os.path.realpath(out_dir)
    for lbl, p in (("검수판(260916)", args.reviewed_260916), ("검수판(260917)", args.reviewed_260917),
                   ("원본", args.original_root), ("툴 data", args.tool_data),
                   ("박성문", args.psm_root), ("최인훈", args.cih_root), ("임성후", args.lsh_root)):
        rp = os.path.realpath(p)
        if real_out == rp or real_out.startswith(rp + os.sep):
            print("멈춥니다 — 만들 곳이 입력 폴더(%s) 안입니다: %s" % (lbl, out_dir))
            print("  --out-root 를 입력과 겹치지 않는 곳으로 바꾸십시오.")
            return 2
    if not args.dry_run and os.path.exists(out_dir):
        print("멈춥니다 — 그 폴더가 이미 있습니다(덮어쓰기 금지): %s" % out_dir)
        print("  같은 날 또 만들려면 --suffix <이름> 을 주십시오.")
        if not os.path.exists(os.path.join(out_dir, "build_summary.json")):
            # 2026-09-18 2차 검수 M2-6: Ctrl+C·전원 꺼짐으로 **끊긴 반쪽 폴더**는 겉보기에
            # 멀쩡한 결과 폴더와 똑같다(실측: 이미지 41장만 있고 manifest·README 가 없었다).
            print("  🔴 그런데 그 폴더에 build_summary.json 이 없습니다 — **중간에 끊긴 반쪽 폴더**입니다.")
            print("     쓰지 마십시오. 사람이 이름을 바꾸거나 지운 뒤 다시 만드십시오.")
        return 2

    print("통합 데이터셋 빌드")
    print("  검수판 : %s (복숭아·포도) · %s (사과·블루베리)" % (args.reviewed_260916, args.reviewed_260917))
    print("  툴 data: %s (읽기만)" % args.tool_data)
    print("  팀원   : 박성문 %s · 최인훈 %s · 임성후 %s (전부 읽기만)"
          % tuple("있음" if os.path.isdir(p) else "없음"
                  for p in (args.psm_root, args.cih_root, args.lsh_root)))
    print("  만들 곳: %s%s" % (out_dir, "  (--dry-run 이라 안 만듭니다)" if args.dry_run else ""))

    registry = collect_registry(args)
    missing = [k for k, v in registry.items() if not v["exists"]]
    print("  읽은 입력 %d개 (없어서 «없음» 으로 넘어간 것 %d개)" % (len(registry), len(missing)))
    # 2026-09-18 2차 검수 M2-5: «없음» 은 폴더가 옮겨졌거나 **권한이 막힌** 것일 수도 있다.
    # 조용히 칸이 비어 나가지 않도록 무엇을 못 읽었는지 이름을 찍는다(멈추지는 않는다).
    if missing:
        print("  🔴 읽지 못한 입력 %d개 — 그 칸은 비어 나갑니다:" % len(missing))
        for k in sorted(missing):
            print("       %-34s %s" % (k, registry[k]["path"]))
    peach_dup, dup_stat = load_peach_dup(args.cih_root)
    team = dict(apple_check=load_apple_check(args.psm_root),
                peach_dup=peach_dup, mask_audit=load_mask_audit(args.cih_root))
    print("  팀원 입력: 사과 번호 판정 %d장 · 복숭아 중복 후보 %d장 · 의심 마스크 %d장"
          % (len(team["apple_check"]), len(peach_dup), len(team["mask_audit"])))

    all_rows, per_fruit, problems, jobs_of, info_of = [], {}, [], {}, {}
    for fruit in args.fruits:
        rows, jobs, probs, info = plan_fruit(fruit, args, team)
        all_rows += rows
        jobs_of[fruit], info_of[fruit] = jobs, info
        problems += probs
    tab = count_table(all_rows, args.fruits)
    print_table(tab, args.fruits)

    prev_path = None if args.no_prev else (args.prev or find_prev(args.out_root, out_dir))
    prev_sum = read_json(prev_path, {}) if prev_path else {}
    prev_reg = (prev_sum or {}).get("input_registry") or {}
    prev_note = ""
    if prev_path and not prev_reg and (prev_sum or {}).get("inputs"):
        prev_reg = legacy_registry(prev_sum["inputs"])
        prev_note = ("직전 빌드에는 출처 등록표가 없어(그 기능 이전 판) "
                     "status.json·검수판 manifest 의 지문만 견줬습니다.")
    cur_for_cmp = {k: registry[k] for k in prev_reg if k in registry} if prev_note else registry
    changes = compare_registry(prev_reg, cur_for_cmp) if prev_reg else []
    print_changes(changes, prev_path if prev_reg else None, prev_note)

    # ── 2026-09-18 3차 결정 D3: 직전 빌드에 «있음» 이던 입력이 이번에 «없음» 이면 멈춘다(exit 3).
    #    폴더가 옮겨졌거나 권한이 막힌 것을 모르고 빌드하면 그 칸이 조용히 비어 나간다.
    #    --allow-missing-input 을 주면 경고만 하고 진행한다. 직전 빌드가 없으면(첫 판) 경고만.
    vanished = vanished_inputs(prev_reg, registry) if prev_reg else []
    if vanished:
        print("\n  🔴 직전 빌드에는 «있음» 이던 입력 %d개가 이번에는 «없음/못 읽음» 입니다:" % len(vanished))
        for k in vanished:
            print("       %-34s %s" % (k, registry.get(k, {}).get("path", prev_reg[k].get("path", ""))))
        print("     견준 곳: %s" % prev_path)
        if args.allow_missing_input:
            print("     (--allow-missing-input 이라 경고만 하고 그대로 진행합니다 — 그 칸은 비어 나갑니다.)")
        else:
            print("  멈춥니다 — 폴더가 옮겨졌거나 권한이 막힌 것일 수 있습니다. 먼저 확인하십시오.")
            print("  정말 그 상태로 만들어야 하면 --allow-missing-input 을 주십시오.")
            return 3
    elif missing and not prev_reg:
        print("\n  ※ 직전 빌드가 없어 «있다 → 없다» 를 견주지 못했습니다(위 «읽지 못한 입력» 은 경고만).")

    if problems:
        print("\n  문제 %d건:" % len(problems))
        for p in problems[:10]:
            print("    - " + p)
    # 🔴 2026-09-19 검수2 N2: 규격을 맞춘 파일 목록(누구 폴더의 파일인가까지).
    spec_files = [e for f in args.fruits for e in (info_of[f]["spec"].get("fixed_files") or [])]
    if args.dry_run:
        print("\n  (--dry-run 이라 아무 파일도 만들지 않았습니다.)")
        print_spec_fix_warning(spec_files)
        if spec_files and args.strict_spec:
            print("\n  멈춥니다(--strict-spec) — 규격을 맞춰야 하는 파일이 %d개 있습니다."
                  % len(spec_files))
            return 4
        return 0
    # --strict-spec: 맞춰야 할 것이 있으면 **폴더를 만들기 전에** 멈춘다(반쪽 폴더를 남기지 않는다)
    if spec_files and args.strict_spec:
        print_spec_fix_warning(spec_files)
        print("\n  멈춥니다(--strict-spec) — 규격을 맞춰야 하는 파일이 %d개 있습니다."
              % len(spec_files))
        print("  그 팀원이 `datasets_resized_2mp` 에서 다시 작업해 올린 뒤 다시 돌리십시오.")
        print("  그래도 맞춰서 만들어야 하면 --strict-spec 을 빼고 돌리십시오.")
        return 4

    os.makedirs(out_dir)
    n_before = len(problems)
    for fruit in args.fruits:
        n_i, n_b = write_fruit(fruit, out_dir, [r for r in all_rows if r["fruit"] == fruit],
                               jobs_of[fruit], problems)
        print("  [%s] 남김 %d장 · 번호 %d · 상자 %d" % (KOR[fruit], tab[fruit]["n_keep"], n_i, n_b))
    # 🔴 2026-09-19 검수1: 위 «문제 N건» 은 **파일을 쓰기 전에** 찍힌다. 그래서 `write_fruit` 가
    #    찾아낸 것(규격을 맞추다 라벨이 줄어든 `spec_warn` · 번호 크기 불일치)은 지금까지
    #    build_summary.json 에만 남고 **화면에는 한 줄도 나오지 않았다**. 갱신법 §5 는 로그를
    #    보라고 하므로 여기서 새로 생긴 것만 찍는다.
    if len(problems) > n_before:
        rest = problems[n_before:]
        print("\n  파일을 쓰면서 찾은 문제 %d건(규격을 맞추다 라벨이 줄어든 것 등):" % len(rest))
        for q in rest[:10]:
            print("    - " + q)
        if len(rest) > 10:
            print("    … 나머지는 build_summary.json 의 `problems` 를 보십시오")
    tab = count_table(all_rows, args.fruits)          # write_fruit 가 채운 칸을 반영해 다시 센다

    def dump_manifest(path, rows):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MANIFEST_COLS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    dump_manifest(os.path.join(out_dir, "manifest.csv"), all_rows)
    for fruit in args.fruits:
        dump_manifest(os.path.join(out_dir, fruit, "manifest.csv"),
                      [r for r in all_rows if r["fruit"] == fruit])

    spec_std = {(f, t): v for f in args.fruits for t, v in info_of[f]["spec_std"].items()}
    vnotes = []            # 2026-09-19 검수2 N6: 실패는 아니지만 사람이 볼 것
    bad = verify(out_dir, args.fruits, all_rows, spec_std, vnotes)
    if vnotes:
        print("\n  자체 검사가 찾은 «실패는 아닌» 문제 %d건:" % len(vnotes))
        for q in vnotes:
            print("    - " + q)
        problems += vnotes
    elapsed = round(time.time() - t0, 1)
    summary = dict(
        script=os.path.abspath(__file__), script_sha256=sha256_of(os.path.abspath(__file__)),
        built_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        date_iso="20%s-%s-%s" % (args.date[:2], args.date[2:4], args.date[4:6]),
        date_arg=args.date, out_dir=out_dir, fruits=list(args.fruits), elapsed_sec=elapsed,
        inputs={f: dict(reviewed_dir=info_of[f]["reviewed_dir"],
                        reviewed_manifest_sha256=sha256_of(os.path.join(info_of[f]["reviewed_dir"],
                                                                        "manifest.csv")),
                        reviewed_mtime=mtime_str(info_of[f]["reviewed_dir"]),
                        status_json=info_of[f]["status_json"],
                        status_json_sha256=(sha256_of(info_of[f]["status_json"])
                                            if os.path.exists(info_of[f]["status_json"]) else ""),
                        status_json_mtime=mtime_str(info_of[f]["status_json"]),
                        duplicate_groups=info_of[f]["dup_groups"],
                        box_stat=info_of[f]["box_stat"]) for f in args.fruits},
        input_registry=registry, input_changes=changes, prev_summary=prev_path,
        prev_note=prev_note,
        missing_inputs=sorted(missing), vanished_inputs=vanished,
        allow_missing_input=bool(args.allow_missing_input),
        peach_dup_stat=dup_stat, box_crosscheck=box_crosscheck(args, all_rows),
        spec={f: info_of[f]["spec"] for f in args.fruits},
        # 2026-09-19 검수2 N2: 규격을 맞춘 파일 전부(과일·stem·종류·원래→맞춘 크기·출처·소유자)
        spec_fixed_files=spec_files, n_spec_fixed_files=len(spec_files),
        strict_spec=bool(args.strict_spec),
        counts=tab, n_problems=len(problems), problems=problems,
        verify_notes=vnotes, verify_failed=bad)
    with open(os.path.join(out_dir, "build_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, sort_keys=True)
    write_readme(out_dir, args, tab, args.fruits, problems, summary, changes,
                 prev_path if prev_reg else None, prev_note)

    if bad:
        inc = out_dir + "_INCOMPLETE"
        os.rename(out_dir, inc)
        print("\n검사에 걸렸습니다 — 폴더 이름을 바꿨습니다: %s" % inc)
        for b in bad[:20]:
            print("  - " + b)
        print_spec_fix_warning(spec_files)     # 2026-09-19 검수2 N2: 맨 끝에 한 번 더
        return 1
    print("\n검사 통과. 만들었습니다: %s  (%.1f초)" % (out_dir, elapsed))
    print_spec_fix_warning(spec_files)         # 2026-09-19 검수2 N2: 표준 출력 맨 끝
    return 0


if __name__ == "__main__":
    sys.exit(main())
