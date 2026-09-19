# -*- coding: utf-8 -*-
"""사진 — 과일 목록 · 사진 목록 · 한 장 상세 · 그림/마스크/썸네일 서빙 · 화면 파일.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다(라우트 9개).
"""

from __future__ import annotations
from typing import Any
import os
import threading

from flask import abort, jsonify, request, send_file, send_from_directory, Response
from PIL import Image

from api import counts as _counts
from api import instances as _instances
from core.paths import (APP_DIR, CACHE_DIR, DATASET, DATA_DIR, FRUITS, box_set, check,
                        fixed_path, fixed_set, gt_path, has_proposals, img_path,
                        n_boxes_of, proposal_path, _prop_names, stem_set, stems_of)
from core.status_store import read_status
from core.util import as_int, err_json, now_str
from domain import dupes as DUP
from domain.maskio import bool_to_png_bytes, load_mask_bool, load_mask_raw, raw_to_png_bytes
from domain import rules
from domain.statusfmt import (CONFIRM_KINDS, STATUSES, ai_boxes_status, confirmed_of,
                              flag_counts, load_duplicates, load_inspection, load_scores,
                              split_flags, src_of)



def dup_rep_ai_excluded(fruit: str, st: Any, dup: Any) -> Any:
    """«AI 가 제외한 묶음» 의 대표 stem 들 — 검수 큐에서 «묶음째 확인» 으로 앞에 세운다."""
    out = set()
    for g in dup["groups"]:
        if not isinstance(g, list) or len(g) < 2:
            continue
        rep = DUP.pick_representative(g, st)
        for m in g:
            r = st.get(m) or {}
            if m != rep and r.get("status") == "exclude" and src_of(r) == "ai":
                out.add(rep)
                break
    return out

def register(app: Any, ctx: Any) -> None:
    """라우트 9개를 붙인다."""


    # ---------------------------------------------------------------- 정적 파일
    @app.route("/")
    def index():
        return send_from_directory(os.path.join(APP_DIR, "static"), "index.html")


    @app.route("/box")
    def index_box():
        """0919 사용자 요청 «상자 툴을 따로»: 같은 화면을 **상자 작업만** 보이게 연다(ui.js 가 주소를 보고
        ▭ 상자를 켜고 마스크·번호 단추를 숨긴다). 데이터·저장 규칙은 `/` 와 완전히 같다."""
        return send_from_directory(os.path.join(APP_DIR, "static"), "index.html")


    @app.route("/static/<path:fn>")
    def static_files(fn):
        return send_from_directory(os.path.join(APP_DIR, "static"), fn)


    # ---------------------------------------------------------------- API: 과일 목록
    @app.route("/api/fruits")
    def api_fruits():
        out = []
        for f in FRUITS:
            stems = stems_of(f)
            st = read_status(f)
            counts = {k: 0 for k in STATUSES}
            cconf = {k: 0 for k in STATUSES}          # 사람이 «확정» 한 것만 (미확정 = unreviewed 칸)
            # 0918 사이클4 결정 1: 상자·번호 확정도 **따로** 센다(마스크 칸은 한 글자도 안 바뀐다).
            cbox = {k: 0 for k in STATUSES}
            cinst = {k: 0 for k in STATUSES}
            by_person, today_by = {}, {}
            today = now_str()[:10]
            for s in stems:
                counts[st.get(s, {}).get("status", "unreviewed") if st.get(s, {}).get("status") in STATUSES else "unreviewed"] += 1
                c = confirmed_of(st.get(s))
                cconf[c["status"] if c else "unreviewed"] += 1
                cb = confirmed_of(st.get(s), "boxes")
                cbox[cb["status"] if cb else "unreviewed"] += 1
                ci = confirmed_of(st.get(s), "instances")
                cinst[ci["status"] if ci else "unreviewed"] += 1
                if c:
                    who = c.get("by") or "익명"
                    by_person[who] = by_person.get(who, 0) + 1
                    if str(c.get("at") or "").startswith(today):
                        today_by[who] = today_by.get(who, 0) + 1
            out.append({
                "fruit": f,
                "n_images": len(stems),
                "counts": counts,
                "reviewed": len(stems) - counts["unreviewed"],
                "has_proposals": has_proposals(f),
                "has_scores": bool(load_scores(f)),
                "has_inspection": bool(load_inspection(f)),
                "has_duplicates": bool(load_duplicates(f)["groups"]),
                "n_fixed": len(fixed_set(f)),
                # 0918 사이클2: 사람 확정 진행률의 원천. counts(=AI 제안 포함 옛 칸)는 그대로 둔다.
                "confirmed_counts": cconf,
                "n_confirmed": sum(cconf.values()) - cconf["unreviewed"],
                "by_person": by_person,
                "today_by_person": today_by,
                # 0918 사이클4 — 작업 종류별 확정 집계(추가만 · 위 칸은 그대로)
                "confirmed_counts_boxes": cbox,
                "n_confirmed_boxes": sum(cbox.values()) - cbox["unreviewed"],
                "confirmed_counts_instances": cinst,
                "n_confirmed_instances": sum(cinst.values()) - cinst["unreviewed"],
                "has_instances": bool(_instances.has_numbers(f)),
            })
        return jsonify({"fruits": out, "statuses": STATUSES, "data_root": DATASET})


    # ---------------------------------------------------------------- API: 사진 목록
    @app.route("/api/list")
    def api_list():
        fruit = request.args.get("fruit", FRUITS[0])
        if fruit not in FRUITS:
            abort(404)
        f_status = request.args.get("status", "all")
        only_dup = request.args.get("dup") == "1"
        only_sus = request.args.get("suspect") == "1"
        only_prop = request.args.get("proposal") == "1"
        # 0917 UI 사이클3 ②: 의심 «종류» 로 걸러 본다(filled_blob 만, fg_too_low 만 …).
        # 이름이 없으면 예전과 똑같이 동작한다(빈 문자열 = 안 거름).
        only_flag = (request.args.get("flag") or "").strip()
        q = (request.args.get("q") or "").strip().lower()
        sort = request.args.get("sort", "priority")
        # 0918 사이클2 — 사람 확정으로 거르기. 두 값이 다 없으면 **예전과 한 글자도 다르지 않다.**
        only_conf = (request.args.get("confirmed") or "").strip()      # "0" = 미확정만 · "1" = 확정된 것만
        only_by = (request.args.get("by") or "").strip()               # 그 사람이 확정한 것만
        # 0918 사이클4 결정 1 — «어느 작업의 확정을 볼 것인가». 없으면 mask(= 예전과 똑같다).
        qmode = request.args.get("mode", "mask")
        if qmode not in CONFIRM_KINDS:
            qmode = "mask"
        page = as_int(request.args.get("page", 1), None)
        page_size = as_int(request.args.get("page_size", rules.PAGE_SIZE_DEFAULT), None)
        if page is None or page_size is None:
            return err_json("쪽 번호(page)·한 쪽 장수(page_size)는 숫자여야 합니다.", 400)
        page = max(1, page)
        page_size = min(rules.PAGE_SIZE_MAX, max(rules.PAGE_SIZE_MIN, page_size))

        stems = stems_of(fruit)
        st = read_status(fruit)
        scores = load_scores(fruit)
        insp = load_inspection(fruit)
        dup = load_duplicates(fruit)
        fixed = fixed_set(fruit)
        props = _prop_names(fruit) if only_prop else None    # 2,400장 목록에서 매번 폴더를 읽지 않도록 한 번만
        ninst = _instances.cached_counts(fruit)              # 열매 개수 — 캐시에 있는 것만(새로 세지 않는다)
        hasbox = box_set(fruit)                              # 0918 사이클4: 상자가 저장된 사진(폴더 한 번만 훑는다)

        items = []
        for s in stems:
            rec = st.get(s, {})
            status = rec.get("status", "unreviewed")
            if status not in STATUSES:
                status = "unreviewed"
            sc = scores.get(s)
            ip = insp.get(s)
            gi = dup["of_stem"].get(s)
            if f_status != "all" and status != f_status:
                continue
            if only_dup and gi is None:
                continue
            if only_sus and not (ip and ip.get("suspect")):
                continue
            if only_flag and only_flag not in split_flags((ip or {}).get("suspect_flags")):
                continue
            if only_prop and s not in props:
                continue
            if q and q not in s.lower():
                continue
            conf = confirmed_of(rec)
            # 거르기(«내 큐» = 미확정만)도 **지금 모드의** 확정을 본다 — 상자 모드에서 «내 큐» 를 켜면
            # 상자를 아직 확정하지 않은 사진이 나와야 한다(0918 사이클4).
            mconf = conf if qmode == "mask" else confirmed_of(rec, qmode)
            if only_conf == "0" and mconf:
                continue
            if only_conf == "1" and not mconf:
                continue
            if only_by and (not mconf or (mconf.get("by") or "") != only_by):
                continue
            items.append({
                "stem": s,
                "status": status,
                "by": rec.get("by"),
                "at": rec.get("at"),
                "note": rec.get("note"),
                "dice": (sc or {}).get("dice_vs_gt"),
                "added_frac": (sc or {}).get("added_frac"),
                "missed_frac": (sc or {}).get("missed_frac"),
                "suspect": bool(ip and ip.get("suspect")),
                "suspect_flags": (ip or {}).get("suspect_flags"),
                "dup_group": gi,
                "has_fixed": s in fixed,
                "n_inst": ninst.get(s),
                # 0918 사이클2 — 더한 칸 넷. 위 "status" 칸의 뜻은 그대로다(옛 화면·회귀 시험이 쓴다).
                "ai_status": status,                     # AI 제안(지금 status 칸과 같은 값)
                "src": src_of(rec),                      # 그 제안을 누가 넣었나 (ai / human)
                "confirmed": (conf or {}).get("status"),  # 사람이 확정한 판정 · 미확정이면 null
                "confirmed_by": (conf or {}).get("by"),
                # 0918 사이클4 결정 1 — 작업 종류별 확정(추가만). 위 "confirmed" 는 **마스크** 확정 그대로다.
                "confirmed_boxes": (confirmed_of(rec, "boxes") or {}).get("status"),
                "confirmed_instances": (confirmed_of(rec, "instances") or {}).get("status"),
                "ai_boxes_status": "saved" if s in hasbox else "seed",
            })

        if sort == "priority":
            items.sort(key=lambda r: (r["dice"] if r["dice"] is not None else 2.0,
                                     0 if r["suspect"] else 1,
                                     r["stem"]))
        elif sort == "added":
            items.sort(key=lambda r: (-(r["added_frac"] or -1), r["stem"]))
        elif sort == "queue":
            # «내 큐» — 방향 문서 §3-2 의 순서: ① AI 가 «문제» 라고 한 것 → ② AI 가 제외한 묶음의
            # 대표(묶음째 확인) → ③ 나머지 미확정 → ④ 사람이 확정한 것은 맨 뒤.
            # 0918 사이클4 결정 1: `mode=mask|boxes|instances` 로 **그 작업의** 미확정을 앞에 세운다.
            # 값이 없거나 이상하면 예전과 똑같다(= mask).
            qmode = request.args.get("mode", "mask")
            if qmode not in CONFIRM_KINDS:
                qmode = "mask"
            ckey = {"mask": "confirmed", "boxes": "confirmed_boxes",
                    "instances": "confirmed_instances"}[qmode]
            reps = dup_rep_ai_excluded(fruit, st, dup)
            def qkey(r):
                if r[ckey]:
                    return (3, r["stem"])
                if r["ai_status"] == "flag" and r["src"] == "ai":
                    return (0, r["stem"])
                if r["stem"] in reps:
                    return (1, r["stem"])
                return (2, r["stem"])
            items.sort(key=qkey)
        elif sort == "status":
            order = {s: i for i, s in enumerate(["flag", "unreviewed", "fixed", "ok", "exclude"])}
            items.sort(key=lambda r: (order.get(r["status"], 9), r["stem"]))
        else:
            items.sort(key=lambda r: r["stem"])

        total = len(items)
        s0 = (page - 1) * page_size
        return jsonify({
            "fruit": fruit, "total": total, "page": page, "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
            "items": items[s0:s0 + page_size],
            # 이 과일에 실제로 있는 의심 «종류»(없는 종류는 단추도 안 만든다) — 0917 사이클3 ②
            "flag_counts": flag_counts(fruit),
            "flag": only_flag,
            "features": {
                "proposals": has_proposals(fruit),
                "scores": bool(scores),
                "inspection": bool(insp),
                "duplicates": bool(dup["groups"]),
            },
        })


    # ---------------------------------------------------------------- API: 한 장 상세
    @app.route("/api/item")
    def api_item():
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        check(fruit, stem)
        allst = read_status(fruit)
        st = allst.get(stem, {})
        scores = load_scores(fruit).get(stem)
        insp = load_inspection(fruit).get(stem)
        dup = load_duplicates(fruit)
        gi = dup["of_stem"].get(stem)
        # 0917 UI 사이클3 ①: «이 묶음에서 어느 장이 대표인가» 를 화면이 알 길이 없었다
        # (서버는 dupes.representative_map 으로 이미 안다). 묶음 구성원의 지금 상태도 같이 준다 —
        # 없으면 화면이 구성원 수만큼 /api/item 을 다시 부르게 된다.
        members = dup["groups"][gi] if gi is not None else []
        rep = DUP.pick_representative(members, allst) if members else None
        with Image.open(img_path(fruit, stem)) as im:
            w, h = im.size
        # 🔴 0919 개수 사이클1 2차 §4-5 → **사이클4 에서 정리**: 아래 옛 칸 `n_inst` 는 지문을 보지 않는
        # `cached_counts()` 값이었다. 같은 응답 안에 «번호가 몇 개인가» 를 뜻하는 칸이 **둘**(옛 `n_inst` ·
        # 새 `counts.instances`)이고, 사람이 번호를 고쳐 저장한 사진에서 두 값이 갈렸다(옛 칸이 낡은 수).
        # 칸 이름은 **그대로 두고**(옛 화면·시험이 읽는다) 값을 `counts.instances` 와 **같은 것**으로 맞춘다
        # = 지문을 보는 값 하나뿐이다. 계산은 한 번만 한다(전에는 `counts_of()` 와 따로 세었다).
        cnt = _counts.counts_of(fruit, stem, st)
        return jsonify({
            "fruit": fruit, "stem": stem, "width": w, "height": h,
            "status": st.get("status", "unreviewed"), "by": st.get("by"),
            "at": st.get("at"), "note": st.get("note", ""),
            "has_gt": os.path.exists(gt_path(fruit, stem)),
            "has_proposal": os.path.exists(proposal_path(fruit, stem)),
            "has_fixed": os.path.exists(fixed_path(fruit, stem)),
            "scores": scores, "inspection": insp,
            "dup_group": gi,
            "dup_members": members,
            "dup_rep": rep,
            "dup_member_status": [allst.get(s, {}).get("status", "unreviewed") for s in members],
            # 0918 사이클2 — 하단 상태 줄이 «AI 제안 / 사람 확정» 을 말하려면 한 장 상세에도 있어야 한다
            "ai_status": st.get("status", "unreviewed"),
            "src": src_of(st),
            "confirmed": confirmed_of(st),
            "dup_member_confirmed": [(confirmed_of(allst.get(s)) or {}).get("status") for s in members],
            # 0918 사이클4 결정 1 — 상자·번호의 확정과 «AI 초벌이 어디까지 와 있나»(하단 한 줄이 쓴다)
            "confirmed_boxes": confirmed_of(st, "boxes"),
            "confirmed_instances": confirmed_of(st, "instances"),
            "ai_boxes_status": ai_boxes_status(fruit, stem),
            "n_boxes": cnt["boxes"],                 # = counts.boxes (같은 파일을 두 번 읽지 않는다)
            "n_inst": cnt["instances"],               # 옛 칸 — counts.instances 와 **같은 값**(위 주석)
            # 0919 «개수 세기» 사이클1 — 하단 «개수» 칸(상자·번호·팀원)과 사람 확정 개수
            "counts": cnt,
        })


    # ---------------------------------------------------------------- 이미지/마스크 서빙
    @app.route("/img")
    def serve_img():
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        check(fruit, stem)
        return send_file(img_path(fruit, stem), mimetype="image/png", conditional=True,
                         max_age=3600)


    @app.route("/mask")
    def serve_mask():
        """layer = gt | ai | fixed. 항상 0/255 L 모드 PNG 로 변환해서 준다."""
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        layer = request.args.get("layer", "gt")
        check(fruit, stem)
        if layer in ("gt", "gt_raw"):
            p = gt_path(fruit, stem)
        elif layer == "ai":
            p = proposal_path(fruit, stem)
        elif layer == "fixed":
            p = fixed_path(fruit, stem)
        else:
            abort(400, "bad layer")
        if not os.path.exists(p):
            abort(404, "no mask")
        if layer == "gt_raw":
            # 이진화하지 않고 원본 값 그대로(사과 = 인스턴스 라벨 1,2,3,... 알 하나하나)
            data = raw_to_png_bytes(load_mask_raw(p))
        else:
            data = bool_to_png_bytes(load_mask_bool(p))
        resp = Response(data, mimetype="image/png")
        resp.headers["Cache-Control"] = "no-cache"
        return resp


    @app.route("/thumb")
    def serve_thumb():
        fruit = request.args.get("fruit", "")
        stem = request.args.get("stem", "")
        check(fruit, stem)
        size = rules.THUMB_PX
        out = os.path.join(CACHE_DIR, fruit, stem + ".jpg")
        if not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with Image.open(img_path(fruit, stem)) as im:
                im = im.convert("RGB")
                im.thumbnail((size, size), Image.BILINEAR)
                tmp = out + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
                #   실측: 브라우저 두 대가 같은 목록을 열면 같은 썸네일을 동시에 만들어 500(FileNotFoundError)
                im.save(tmp, "JPEG", quality=rules.THUMB_QUALITY)
                os.replace(tmp, out)
        return send_file(out, mimetype="image/jpeg", conditional=True, max_age=86400)
