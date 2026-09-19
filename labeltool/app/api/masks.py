# -*- coding: utf-8 -*-
"""마스크 — 스마트 채우기 · 수정본 저장 · 되돌리기 · 판정/사람 확정 저장.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다(라우트 4개).
"""

from __future__ import annotations
from typing import Any
import base64
import io
import os
import threading

from flask import jsonify, request
from PIL import Image

import numpy as np

from api import instances as _instances
from core.paths import (FRUITS, check, fixed_path, gt_path, img_path, proposal_path,
                        stem_set)
from core.status_store import (clear_confirm, confirm_status, read_status, update_status,
                               write_status_entry)
from core.util import as_int, err_json, lock_for, now_str
from domain.maskio import bool_to_png_bytes, load_mask_bool, save_mask_atomic
from domain import rules
from domain.statusfmt import CONFIRM_KINDS, STATUSES, confirmed_of



# ---------------------------------------------------------------- 스마트 채우기
_label_cache = {}
_label_lock = threading.Lock()


def labeled(fruit: str, stem: str, source: str) -> Any:
    """연결성분 라벨 배열을 계산(작은 LRU 캐시)."""
    key = (fruit, stem, source)
    with _label_lock:
        if key in _label_cache:
            return _label_cache[key]
    p = proposal_path(fruit, stem) if source == "ai" else gt_path(fruit, stem)
    if not os.path.exists(p):
        return None
    arr = load_mask_bool(p)
    try:
        from scipy import ndimage
        lab, n = ndimage.label(arr)
    except Exception:
        from skimage.measure import label as sklabel
        lab = sklabel(arr)
    with _label_lock:
        if len(_label_cache) > rules.LABEL_CACHE_MAX:
            _label_cache.clear()
        _label_cache[key] = lab
    return lab


# ---------------------------------------------------------------- 저장
def _size_msg(got, expect):
    return ("수정본 그림의 크기가 원본과 다릅니다(보낸 것 %d×%d, 원본 %d×%d). "
            "사진을 다시 연 뒤 고쳐서 저장해 주세요." % (got[1], got[0], expect[1], expect[0]))


def _decode_png_mask(datauri, expect_shape):
    """화면이 보낸 수정본 PNG 를 읽는다. 실패하면 **초보도 읽을 수 있는 한국어 문장**으로 알린다
    (파이썬 내부 메시지·메모리 주소가 화면에 그대로 뜨지 않게)."""
    if not datauri:
        raise ValueError("수정본 그림이 들어 있지 않습니다. 사진을 다시 연 뒤 저장해 보세요.")
    if "," in datauri:
        datauri = datauri.split(",", 1)[1]
    try:
        raw = base64.b64decode(datauri)
    except Exception:
        raise ValueError("수정본 그림이 깨져서 읽을 수 없습니다. 새로고침한 뒤 다시 고쳐서 저장해 주세요.")
    try:
        im = Image.open(io.BytesIO(raw))
    except Exception:
        raise ValueError("수정본이 그림 파일(PNG)이 아닙니다. 새로고침한 뒤 다시 고쳐서 저장해 주세요.")
    with im:
        w, h = im.size
        if (h, w) != tuple(expect_shape):
            # 배열로 펴기 «전에» 막는다 — 엉뚱하게 큰 PNG 로 메모리를 잡아먹지 않게
            raise ValueError(_size_msg((h, w), tuple(expect_shape)))
        try:
            im = im.convert("L") if im.mode not in ("L", "1") else im.copy()
            a = np.array(im)
        except Exception:
            raise ValueError("수정본 그림을 여는 중에 실패했습니다. 새로고침한 뒤 다시 저장해 주세요.")
    if a.ndim == 3:
        a = a.max(axis=2)
    if a.shape != tuple(expect_shape):
        raise ValueError(_size_msg(a.shape, tuple(expect_shape)))
    return a > 127


def _save_verdict(fruit, stem, by, note):
    """마스크를 저장했을 때 판정을 어떻게 적을지 — 한 곳에서 정한다(0918 UI사이클5 N-C).

    규칙: **«제외» 는 마스크 저장이 뒤집지 않는다.** 번호 저장(instances.py, 0917 ab사이클2 P2)과
    같은 규칙이다 — exclude 는 «이 사진을 쓸지» 에 대한 판정이라, 그림을 고친 것으로 풀리지 않는다.
    고치기 전에는 제외 사진에 붓질 한 번을 저장하면 `fixed` 가 되어 **AI 3회 검수가 동결한 제외
    (사과·블루베리 수백 장)가 데이터셋에 되살아났다**(확인창도 경고도 없었다).
    flag 는 지금처럼 `fixed` 로 풀린다 — 사람이 실제로 고쳤으므로 풀리는 것이 맞다.

    메모: 제외로 남길 때는 **원래 메모를 앞에 그대로 둔다.** «중복: …» 로 시작하는지를 보고
    되돌리는 곳(undo_duplicate_exclusions)과 내보내기 기록이 있어서, 앞부분이 바뀌면 안 된다.
    사람이 메모를 적었으면 그 뒤에 이어 붙인다.
    반환: (status 항목, 제외를 지켰나)
    """
    with lock_for("status:" + fruit):
        before = read_status(fruit).get(stem) or {}
    if not rules.mask_save_keeps_exclude(before.get("status")):
        return update_status(fruit, stem, "fixed", by, note, keep_prev=True), False
    old = str(before.get("note") or "")
    # 메모 칸은 **이 사진의 메모로 미리 채워져** 있다(app.js:338). 그래서 보통 note 는 `old` 로
    # 시작한다 — 그 때는 보낸 것을 그대로 쓴다(사람이 뒤에 몇 글자 덧붙인 것까지 그대로 남는다).
    # 0918 UI사이클5 **2차**: 앞 판은 «글자가 똑같을 때만» 안 붙였다(`old.startswith(note)`).
    # 그래서 사람이 미리 채워진 메모 뒤에 한 마디를 덧붙이면(가장 흔한 행동) 옛 메모가 통째로
    # 한 번 더 붙었다 — 실측 «중복: A · (수정본 저장) 중복: A 다시 봤음»(cycle_5/stage2/r1_mix.py S4).
    # 칸을 비우고 딴 말을 적은 경우만 뒤에 이어 붙인다. 어느 쪽이든 **앞부분(old)이 그대로 남는다**
    # — «중복: » 으로 시작하는지를 보는 곳들이 있기 때문이다.
    new_note = rules.merge_exclude_note(old, note)      # 앞부분(old)은 늘 그대로(규칙 함수)
    # keep_prev=True 로 «제외» 를 prev 에도 한 벌 적어 둔다 — «수정본 되돌리기» 가 돌아갈 자리다.
    st = update_status(fruit, stem, "exclude", by, new_note, keep_prev=True)
    return st, True

def register(app: Any, ctx: Any) -> None:
    """라우트 4개를 붙인다."""


    @app.route("/api/component", methods=["POST"])
    def api_component():
        """클릭 좌표가 속한 연결성분을 0/255 PNG 로 반환(클라이언트가 더하거나 뺀다)."""
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        stem = d.get("stem", "")
        check(fruit, stem)
        source = d.get("source", "ai")
        if source not in ("ai", "gt"):
            source = "ai"
        x = as_int(d.get("x", -1), None)
        y = as_int(d.get("y", -1), None)
        if x is None or y is None:
            return err_json("클릭한 좌표(x·y)는 숫자여야 합니다.", 400)
        lab = labeled(fruit, stem, source)
        if lab is None:
            return err_json("그 레이어의 마스크가 없습니다.", 404)
        h, w = lab.shape
        if not (0 <= x < w and 0 <= y < h):
            return err_json("클릭한 곳이 사진 밖입니다.", 400)
        v = int(lab[y, x])
        if v == 0:
            return err_json("그 지점은 비어 있습니다(배경). 과일 안쪽을 클릭해 주세요.", 200)
        comp = (lab == v)
        png = bool_to_png_bytes(comp)
        return jsonify({"ok": True, "n_pixels": int(comp.sum()),
                        "png": "data:image/png;base64," + base64.b64encode(png).decode("ascii")})


    @app.route("/api/save", methods=["POST"])
    def api_save():
        """action = ok | ai | fixed | flag | exclude"""
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        stem = d.get("stem", "")
        check(fruit, stem)
        action = d.get("action", "")
        by = (d.get("by") or "익명").strip()[:rules.NAME_MAX]
        note = (d.get("note") or "").strip()[:rules.NOTE_MAX]

        gtp = gt_path(fruit, stem)
        if not os.path.exists(gtp):
            return err_json("이 사진은 원본 마스크(masks/)가 없습니다. 담당자에게 알려 주세요.", 404)
        with Image.open(gtp) as im:
            gw, gh = im.size
        expect = (gh, gw)

        with lock_for("mask:%s:%s" % (fruit, stem)):
            if action == "ok":
                # 0918 사이클2 «3차 판정 전 소수정»(N1): 사람이 «1~4» 를 누르면 AI 3회 검수의
                # 판정·검수자·메모가 **되살릴 수 없게** 지워졌다(실측 stage2/s5_live_guard [C]).
                # keep_prev=True 로 «AI 제안이던 것» 을 한 벌만 prev 에 적어 둔다 — 마스크 저장
                # 길(_save_verdict)이 이미 쓰는 것과 **같은 장치**이고, 「수정본 되돌리기」
                # (/api/revert)가 그 prev 로 되살린다. 사람이 이미 prev 를 가졌으면 덮지 않는다.
                st = update_status(fruit, stem, "ok", by, note, keep_prev=True)
                # 내보내기는 masks_fixed 가 있으면 그것을 쓴다 → «원본 그대로» 와 어긋날 수 있어 알려 준다
                return jsonify({"ok": True, "status": st, "wrote_mask": False,
                                "has_fixed": os.path.exists(fixed_path(fruit, stem))})

            if action in ("flag", "exclude"):
                # 같은 이유(N1) — «3 문제 있음»·«4 제외» 도 옛 판정을 prev 에 남긴다
                st = update_status(fruit, stem, action, by, note, keep_prev=True)
                return jsonify({"ok": True, "status": st, "wrote_mask": False})

            if action == "ai":
                p = proposal_path(fruit, stem)
                if not os.path.exists(p):
                    return err_json("이 사진에는 AI 제안 마스크가 없습니다.", 404)
                arr = load_mask_bool(p)
                if arr.shape != expect:
                    return err_json("AI 제안 마스크의 크기가 원본과 다릅니다. 담당자에게 알려 주세요.", 400)
                save_mask_atomic(fixed_path(fruit, stem), arr)
                st, kept = _save_verdict(fruit, stem, by, note or "AI 제안으로 교체")
                return jsonify({"ok": True, "status": st, "wrote_mask": True,
                                "kept_exclude": kept, "fg_pixels": int(arr.sum())})

            if action == "fixed":
                try:
                    arr = _decode_png_mask(d.get("png"), expect)
                except ValueError as e:
                    return err_json(str(e), 400)
                except Exception:
                    return err_json("수정본을 저장하지 못했습니다. 새로고침한 뒤 다시 시도해 주세요.", 400)
                save_mask_atomic(fixed_path(fruit, stem), arr)
                st, kept = _save_verdict(fruit, stem, by, note)
                return jsonify({"ok": True, "status": st, "wrote_mask": True,
                                "kept_exclude": kept, "fg_pixels": int(arr.sum())})

        return err_json("알 수 없는 action 입니다(ok·ai·fixed·flag·exclude 만 됩니다).", 400)


    @app.route("/api/revert", methods=["POST"])
    def api_revert():
        """수정본을 버리고 원본 GT 로 되돌린다(masks_fixed 의 파일만 삭제).

        0917 사이클5 N1-c: 열매 번호를 고친 사진은 **거절한다.** 이진본만 지우면 번호 파일이 낡아
        내보낼 때 «없는 번호»(유령 번호)가 나가고 status 의 편집 기록도 남는다. 번호까지 되돌리려면
        번호 패널의 «번호 되돌리기»(/api/revert_instances)가 파일 두 개와 기록을 함께 치운다.
        """
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        stem = d.get("stem", "")
        check(fruit, stem)
        by = (d.get("by") or "익명").strip()[:rules.NAME_MAX]
        if os.path.exists(_instances.inst_fixed_path(fruit, stem)):
            return err_json("이 사진은 열매 번호를 고친 사진입니다. 번호 패널의 «번호 되돌리기» 를 쓰세요.", 400)
        p = fixed_path(fruit, stem)
        removed = False
        with lock_for("mask:%s:%s" % (fruit, stem)):
            # 0918 UI사이클4 2차: 전에는 **무조건** «아직 안 봄» + 메모 «수정본 되돌림» 으로 썼다.
            # 그래서 AI 3회 검수의 제외(«중복: …»)나 flag 사유(«…x1,y1,x2,y2: …»)가 있던 사진에
            # 붓질 한 번 저장했다가 되돌리면 그 판정과 메모가 **통째로 사라졌다**(되살릴 길 없음).
            # 저장 때 update_status(keep_prev=True) 가 적어 둔 `prev` 로 되돌린다 —
            # 번호 쪽 api_revert_instances 와 **같은 규칙**이다. prev 가 없으면 예전과 똑같다.
            prev = (read_status(fruit).get(stem) or {}).get("prev")
            prev = prev if isinstance(prev, dict) else None
            if os.path.exists(p):
                os.remove(p)
                removed = True
            st = update_status(fruit, stem,
                               (prev or {}).get("status") or "unreviewed",
                               (prev.get("by") if prev else None) or by,
                               (prev or {}).get("note") if prev else "수정본 되돌림")
            if prev:
                st = write_status_entry(fruit, stem, {k: v for k, v in st.items() if k != "prev"})
            # 0918 사이클4 3차 전 소수정(총괄 결정 1): 파일을 지웠으면 **마스크 확정도 지운다.**
            # 반드시 위 두 쓰기 **뒤**에 — write_status_entry 는 항목을 통째로 덮어쓴다.
            cleared, st = clear_confirm(fruit, stem, "mask")
        return jsonify({"ok": True, "removed": removed, "restored": bool(prev), "status": st,
                        "confirmed_cleared": cleared})


    @app.route("/api/status", methods=["POST"])
    def api_status():
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        stem = d.get("stem", "")
        check(fruit, stem)
        s = d.get("status", "")
        if s not in STATUSES:
            return err_json("알 수 없는 상태입니다(unreviewed·ok·fixed·flag·exclude 만 됩니다).", 400)
        by = (d.get("by") or "익명")[:rules.NAME_MAX]
        note = (d.get("note") or "")[:rules.NOTE_MAX]
        # 0918 사이클4 N8: 사람 이름이 «AI» 로 시작하면 `src_of()` 가 그 판정을 **AI 제안**으로 읽는다
        # (server.py src_of — `by` 가 "AI" 로 시작하면 ai). 그러면 큐·내보내기·화면이 사람이 누른 것을
        # AI 초벌로 취급한다(실측 s1_api 검증-10). 이름 쪽을 막는 것이 제일 싸다.
        # ⚠ **여기(/api/status)에서만** 막는다. 0918 사이클4 2차가 실측으로 고친 근거(§3-2):
        #   `data/*/status.json` 에 «AI 3회 검수(…)» 이름으로 적힌 990행(사과 623·포도 180·복숭아 102·
        #   블루베리 85)은 **HTTP 가 아니라 파일로 직접** 쓰인 것이고(T/scripts·inspect·ai_pass·export·
        #   final 어디에도 /api/save 를 부르는 코드가 없다), 그 이름으로 /api/save 를 부르는 것은
        #   **우리 시험 스크립트뿐**이다. 그래도 여기만 막는 이유는 두 가지다 —
        #   ① 사람이 그 길로 갈 수 있는 자리는 «이름 칸» 하나뿐이고 그것이 이 주소다.
        #   ② /api/save·/api/save_instances 까지 막으면 우리 회귀 시험 10여 개가 죽는다(동작 이득 0).
        if rules.ai_name_rejected(by):
            return err_json("«AI» 로 시작하는 이름은 쓸 수 없습니다 — AI 제안과 구별해야 합니다.", 400)
        if d.get("confirm"):
            # 0918 사이클2 — «사람 확정». AI 제안(status)은 그대로 두고 confirmed 칸만 얹는다.
            # stems 를 같이 보내면 **묶음째** 확정한다(대표 = OK · 나머지 = 제외). 한 자물쇠 안에서 한 번에.
            # 0918 사이클4 결정 1: `kind` 로 **어느 작업의 확정인가**를 고른다(기본 mask = 옛 화면 호환).
            kind = d.get("kind", "mask")
            if kind not in CONFIRM_KINDS:
                return err_json("알 수 없는 작업 종류입니다(mask·boxes·instances 만 됩니다).", 400)
            pairs = [(stem, s)]
            # 0918 사이클4 N7: `stems` 가 목록이 아니면(문자열·숫자·dict) 예전에는 글자·열쇠를 하나씩
            # 돌다 `.get` 이 없어 **500** 이 났다(실측 s1_api 검증-8·9). 사람 말로 400 을 준다.
            raw_stems = d.get("stems")
            if raw_stems is None:
                raw_stems = []
            if not isinstance(raw_stems, list):
                return err_json("묶음 목록(stems)은 [{stem,status}, …] 꼴이어야 합니다.", 400)
            for it in raw_stems[:rules.CONFIRM_STEMS_MAX]:
                if not isinstance(it, dict):
                    return err_json("묶음 목록(stems)의 항목은 «이름:값» 꾸러미여야 합니다.", 400)
                s2 = it.get("stem", "")
                v2 = it.get("status", "")
                check(fruit, s2)
                if v2 not in STATUSES:
                    return err_json("알 수 없는 상태입니다(unreviewed·ok·fixed·flag·exclude 만 됩니다).", 400)
                pairs.append((s2, v2))
            conf, skipped = confirm_status(fruit, pairs, by, note, kind)
            # `n` 의 뜻은 그대로 둔다(= 이 묶음이 몇 장짜리였나). 0918 소수정(N3)으로 **건너뛴 장**은
            # `skipped` 한 칸으로 따로 알려 준다 — 옛 화면·옛 시험은 `n` 만 보므로 영향이 없다.
            return jsonify({"ok": True, "confirmed": conf, "n": len(pairs), "skipped": skipped,
                            "kind": kind})
        st = update_status(fruit, stem, s, by, note)
        return jsonify({"ok": True, "status": st})
