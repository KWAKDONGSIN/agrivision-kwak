# -*- coding: utf-8 -*-
"""`status.json` **쓰는 길은 여기 하나뿐**이다 — 읽기·쓰기·백업·확정 얹기/벗기기.

구조 사이클 2(2026-09-20): 전에는 `server.py`(6곳)와 `dupes.py`(읽기 1곳)가 각자 파일을
열었다. 이제 `app/dupes.py`·`export/`·`api/*` 가 모두 이 모듈 하나를 부른다.
규칙(`prev` 에 한 벌 남기기 · 사람 확정은 덮지 않기 · 되돌리면 확정을 벗기기)은 한 글자도
바뀌지 않았다 — 아래 함수들의 docstring 이 그 결정 기록이다.
"""

from __future__ import annotations
from typing import Any
import json
import os
import threading
from datetime import datetime

from core.paths import DATA_DIR, status_file
from core.util import lock_for, now_str
from domain.statusfmt import CONFIRM_KINDS, confirmed_of



def read_status(fruit: str) -> dict[str, Any]:
    """판정 JSON을 읽으며 없거나 잘못된 파일은 빈 사전으로 돌려준다."""
    p = status_file(fruit)
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def write_status(fruit: str, data: Any) -> None:
    """판정 사전을 임시 파일에 쓴 뒤 원자적으로 교체한다."""
    p = status_file(fruit)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # 0918 UI사이클3 2차: 임시 이름이 «PID» 뿐이라 **한 서버 안의 두 요청이 같은 임시 파일**을 썼다.
    # 한쪽이 os.replace 로 옮기면 다른 쪽은 FileNotFoundError(500)로 죽고, 그 사이 다른 사람이
    # 저장한 판정이 통째로 사라졌다(실측: 동시 46요청에서 판정 40건 손실 · 500 3건).
    # 요청(스레드)마다 다른 임시 이름을 쓴다.
    tmp = p + ".tmp%d.%d" % (os.getpid(), threading.get_ident())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, p)


def backup_status(fruit: str) -> str | None:
    """status.json 을 손대기 «전» 에 한 벌 복사해 둔다 → data/<fruit>/_status_backup_<시각>.json
    (되돌릴 수 없는 일괄 작업 전에 부른다. 파일이 없으면 아무것도 안 하고 None)"""
    p = status_file(fruit)
    if not os.path.exists(p):
        return None
    b = os.path.join(os.path.dirname(p),
                     "_status_backup_%s.json" % datetime.now().strftime("%y%m%d_%H%M%S"))
    try:
        with open(p, "rb") as f:
            raw = f.read()
        tmp = b + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, b)
        return b
    except OSError:
        return None


def update_status(fruit: str, stem: str, status: Any=None, by: Any=None, note: Any=None, keep_prev: bool=False) -> Any:
    """status.json 의 한 항목을 고친다.

    keep_prev=True — 지금 판정이 **flag·exclude** 면 그것을 `prev` 에 한 벌 적어 둔다(0918 UI사이클4 2차).
    왜: 마스크를 «수정본 저장» 하면 판정이 «수정함» 으로 덮이는데, 그 뒤 «수정본 되돌리기» 가
    돌아갈 자리를 몰라 **«아직 안 봄» + 메모 «수정본 되돌림»** 으로 지워 버렸다. 그래서
    AI 3회 검수의 제외(사과 454·블루베리 81장)와 flag 사유·노란 점선 좌표(51·4장)가
    단추 두 번에 사라졌다(실측 cycles/260917_ui/cycle_4/stage2/t9_revertbug.py).
    번호 쪽(instances.py api_save_instances·api_revert_instances)은 0917 ab사이클2 P2 때
    이미 같은 `prev` 장치를 넣었다 — 마스크 쪽에만 빠져 있던 것을 같은 모양으로 맞춘다.
    (판정이 «수정함» 으로 풀리는 것 자체는 그대로 둔다 — 사람이 고쳤으면 풀리는 것이 맞다.)
    """
    with lock_for("status:" + fruit):
        d = read_status(fruit)
        rec = d.get(stem, {})
        # 0919 사이클5 **2차 검수**(실측: 2차 시나리오 10단계 · 복숭아 `210629-t2-05`):
        # 위 조건이 **flag·exclude 뿐**이어서, AI 제안이 «원본 OK»(ok)·«수정함»(fixed) 인 사진은
        # 붓질 한 번 저장했다가 «수정본 되돌리기» 를 누르면 판정과 메모가 **되살릴 수 없게**
        # `unreviewed` + «수정본 되돌림» 으로 지워졌다(실측: `status: ok · note: «3회 검수 이상 없음 /
        # 위와 같음(뒷줄)»` → `status: unreviewed · note: «수정본 되돌림»`). 방향 문서 §5
        # «AI 가 넣은 판정은 지우지 않고 «AI 제안» 으로 강등한다» 에 어긋나고, 그 뒤 Enter 는
        # «이 사진에는 아직 판정이 없습니다» 로 거부하는데 하단 한 줄은 여전히 «Enter=맞다» 라고
        # 말한다(사이클4 3차 «되돌린 뒤 Enter 한 번» 과도 어긋난다).
        # → «아직 안 봄» 이 아닌 **모든** 판정을 prev 에 한 벌 남긴다(사과 없음·복숭아 ok 77·fixed 18·
        #   포도 fixed 12 장이 이 구멍에 있었다).
        if keep_prev and "prev" not in rec and rec.get("status") not in (None, "", "unreviewed"):
            rec["prev"] = {"status": rec.get("status"), "note": str(rec.get("note") or "")[:300],
                           "by": rec.get("by") or ""}
        if status:
            rec["status"] = status
        if by is not None:
            rec["by"] = by
        if note is not None:
            rec["note"] = note
        rec["at"] = now_str()
        d[stem] = rec
        write_status(fruit, d)
        return rec


def confirm_status(fruit: str, pairs: Any, by: Any, note: Any, kind: str="mask") -> Any:
    """사람 확정을 status.json 에 얹는다 — **쓰는 곳은 여기 하나뿐**이다.

    0918 사이클4 결정 1: `kind`(mask·boxes·instances) 한 인자로 **쓰는 칸만** 바뀐다.
    자물쇠·묶음 건너뛰기 규칙은 종류가 달라도 똑같다(아래 N3 주석 그대로).
    기본값이 `mask` 라 옛 호출은 전과 한 글자도 다르지 않다.

    pairs = [(stem, status), ...] (묶음째 확정이면 여러 장). `status:<과일>` 자물쇠 안에서
    한 번에 읽고 한 번에 쓰므로, 묶음 안에서 일부만 저장되는 일이 없다(N-A 와 같은 층).
    `status`·`note`·`prev` 는 건드리지 않는다.

    0918 «3차 판정 전 소수정»(N3): **구성원(pairs[1:]) 중 사람이 이미 확정한 장은 건너뛴다.**
    기존 「묶음 제외」 단추(api_exclude_group)의 «사람이 판정한 사진은 건너뛴다» 와 같은 규칙이다.
    화면(ui.js enterConfirm)이 이미 걸러 보내지만, **두 사람이 동시에** 같은 묶음을 확정하면
    화면만으로는 못 막는다 — 여기가 마지막 방어선이다(실측 stage2/s1_api [마]-2).
    반환: (확정한 것, 건너뛴 stem 목록). 대표(pairs[0])는 사람이 **지금 누른** 장이라 건너뛰지 않는다.
    """
    key = CONFIRM_KINDS.get(kind, "confirmed")
    out = {}
    skipped = []
    with lock_for("status:" + fruit):
        d = read_status(fruit)
        at = now_str()
        for i, (stem, v) in enumerate(pairs):
            rec = d.get(stem) or {}
            if i and confirmed_of(rec, kind):
                skipped.append(stem)       # 남의 확정(또는 내 옛 확정)을 덮지 않는다
                continue
            # `src` 는 적지 않는다 — 위 주석대로 그 칸은 이미 «어느 단추가 제외했나» 표식이다.
            rec[key] = {"status": v, "by": by, "at": at, "note": note}
            d[stem] = rec
            out[stem] = rec[key]
        write_status(fruit, d)
    return out, skipped


def clear_confirm(fruit: str, stem: str, kind: str) -> Any:
    """**되돌리기가 성공하면 그 종류의 사람 확정을 지운다** — 쓰는 곳은 여기 하나뿐이다.

    0918 사이클4 «3차 판정 전 소수정» 총괄 결정 1. 왜 «note 에 적어 두기» 가 아니라 «지우기» 인가:
    확정이 «수정함» 으로 남으면 manifest 는 `confirmed_status=fixed`·`source=human` 인데 실제로
    나가는 파일은 **원본**이다(실측 cycle_4/stage2c/c1_revert.py [가]-9 고치기 전). 내보내기가
    거짓말을 하는 것이라, 사람이 누른 판정을 지우는 값을 치른다. 사람은 되돌린 뒤 Enter 를
    한 번 더 눌러 다시 확정하면 된다 — 화면이 «확정이 풀렸습니다» 를 1초 힌트로 알려 준다.

    마스크(`/api/revert`)·번호(`/api/revert_instances`)·상자(되돌리기 주소가 생기면 그때)가
    **모두 이 함수 하나를** 부른다. 종류마다 칸 이름을 따로 적으면 한 군데만 고치고 지나간다.
    `confirm_status()` 와 짝이다(그쪽이 얹고, 이쪽이 벗긴다). `status`·`by`·`note`·`prev` 와
    다른 두 종류의 확정 칸은 **한 글자도 건드리지 않는다.**

    돌려주는 것: (지운 종류 or None, 지금 status 항목) — 부르는 쪽이 응답에 그대로 싣는다.
    """
    key = CONFIRM_KINDS.get(kind)
    with lock_for("status:" + fruit):
        d = read_status(fruit)
        rec = d.get(stem) or {}
        if not key or key not in rec:
            return None, rec                   # 원래 확정이 없었다 → 아무것도 바꾸지 않는다
        rec.pop(key, None)
        d[stem] = rec
        write_status(fruit, d)
        return kind, rec


def write_status_entry(fruit: str, stem: str, entry: Any) -> Any:
    """status.json 의 한 사진 항목을 통째로 바꿔 쓴다(번호 편집 기록용, 0917).

    0918 UI사이클3 2차: 여기만 **자물쇠 없이** 읽고 썼다(다른 쓰기는 전부 status:<과일> 안에서 한다).
    번호 저장이 판정 저장과 겹치면 방금 저장된 판정을 덮어쓸 수 있다 — 같은 자물쇠를 쓴다.
    (부르는 쪽은 inst:<과일>:<사진> 자물쇠만 쥐고 있어 겹치지 않는다.)
    """
    with lock_for("status:" + fruit):
        d = read_status(fruit)
        d[stem] = entry
        write_status(fruit, d)
    return entry
