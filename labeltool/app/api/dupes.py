# -*- coding: utf-8 -*-
"""근접 중복 — 미리 보기 · 일괄 제외와 되돌리기 · 한 묶음 제외와 되돌리기 · 제외 목록 내보내기.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다(라우트 6개).
"""

from __future__ import annotations
from typing import Any
import os
import threading

from flask import abort, jsonify, request

from core.paths import DATA_DIR, FRUITS, check, stem_set
from core.status_store import backup_status, read_status, write_status
from core.util import err_json, lock_for, now_str
from domain import dupes as DUP
from domain import rules
from domain.rules import SRC_DUP_BULK, SRC_DUP_GROUP
from domain.statusfmt import load_duplicates

def register(app: Any, ctx: Any) -> None:
    """라우트 6개를 붙인다."""


    # ------------------------------------------------- 근접 중복 일괄 제외 / 제외 목록
    @app.route("/api/duplicate_preview")
    def api_duplicate_preview():
        """중복 그룹에서 대표 외에 몇 장이 빠지게 되는지 미리 보여준다(쓰기 없음)."""
        fruit = request.args.get("fruit", "")
        if fruit not in FRUITS:
            abort(404)
        groups = DUP.load_duplicate_groups(fruit)
        pairs = DUP.duplicate_exclusions(fruit)
        st = read_status(fruit)
        # 「검수자별」 표와 같은 규칙: **지금 데이터셋에 있는 사진만** 센다.
        # (이미 빼낸 사진까지 세면 «제외 2» 옆 버튼이 «95장을 제외합니다» 라고 물어보게 된다)
        here = stem_set(fruit)
        inside = [(s, r) for s, r in pairs if s in here]
        outside = len(pairs) - len(inside)
        already = sum(1 for s, _ in inside if st.get(s, {}).get("status") == "exclude")
        # 사람이 이미 본 사진(ok·수정함·문제 있음)은 일괄 제외가 건드리지 않는다 → 몇 장인지 미리 알려 준다
        kept_human = sum(1 for s, _ in inside
                         if st.get(s, {}).get("status", "unreviewed") not in ("unreviewed", "exclude"))
        # 되돌리기로 되돌아올 장수 = «이 단추가 넣은 표식» 이 있는 것만(3차 판정 제외는 안 건드림)
        undoable = sum(1 for rec in st.values()
                       if rec.get("status") == "exclude" and rec.get("src") == SRC_DUP_BULK)
        other_excludes = sum(1 for rec in st.values()
                             if rec.get("status") == "exclude" and rec.get("src") != SRC_DUP_BULK)
        return jsonify({"fruit": fruit, "n_groups": len(groups), "n_to_exclude": len(inside),
                        "already_excluded": already, "outside_dataset": outside,
                        "n_to_exclude_all": len(pairs), "kept_human": kept_human,
                        "n_will_change": len(inside) - already - kept_human,
                        "n_undoable": undoable, "n_other_excludes": other_excludes,
                        "sample": [{"stem": s, "rep": r} for s, r in inside[:rules.DUP_SAMPLE_MAX]]})


    @app.route("/api/apply_duplicate_exclusions", methods=["POST"])
    def api_apply_duplicate_exclusions():
        """중복 그룹의 대표가 아닌 사진들을 한 번에 status=exclude 로 바꾼다.
        원본 파일은 건드리지 않는다. 사람이 편집 화면에서 개별로 되돌릴 수 있다."""
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        if fruit not in FRUITS:
            abort(404)
        by = (d.get("by") or "익명").strip()[:rules.NAME_MAX]
        pairs = DUP.duplicate_exclusions(fruit)
        if not pairs:
            return err_json("중복 목록(duplicates.json)이 없거나 중복 그룹이 없습니다.", 200)
        changed = skipped = kept_human = 0
        with lock_for("status:" + fruit):
            data = read_status(fruit)
            for s, rep in pairs:
                if s not in stem_set(fruit):
                    skipped += 1
                    continue
                rec = data.get(s, {})
                cur = rec.get("status", "unreviewed")
                if cur == "exclude":
                    skipped += 1
                    continue
                if cur != "unreviewed":
                    # 0917 ab사이클2 P1(다): 전에는 flag·ok·수정함 을 **덮어썼다.**
                    # 사람(또는 AI 판정)이 이미 본 사진은 건드리지 않는다.
                    kept_human += 1
                    continue
                rec["status"] = "exclude"
                rec["by"] = by
                rec["note"] = "중복: %s" % rep
                rec["at"] = now_str()
                rec["src"] = SRC_DUP_BULK        # 되돌리기가 «이 단추가 넣은 것» 만 알아보게 하는 표식
                data[s] = rec
                changed += 1
            write_status(fruit, data)
        return jsonify({"ok": True, "changed": changed, "skipped": skipped,
                        "kept_human": kept_human, "n_pairs": len(pairs)})


    @app.route("/api/undo_duplicate_exclusions", methods=["POST"])
    def api_undo_duplicate_exclusions():
        """위 일괄 제외를 되돌린다 — **그 단추가 넣은 것만**(`src` 표식이 있는 항목만).

        0917 ab사이클2 P1(나): 전에는 «상태가 exclude 이고 메모가 «중복: » 으로 시작» 이면 전부
        되돌렸다. 그래서 단추를 한 번 누르면 **AI 3회 검수가 반영한 제외 314장(사과)·71장(블루베리)이
        통째로 «아직 안 봄» 으로 지워졌다**(메모까지). 3차 판정과 이 단추는 메모 형식이 같아서
        메모로는 구분할 수 없다 → 이 단추가 쓸 때 `src="dup_bulk"` 를 남기고, 되돌리기는 그것만 본다.
        표식이 없는 옛 항목·다른 출처(AI 판정·사람 손)의 제외는 kept_other 로만 세고 건드리지 않는다.
        """
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        if fruit not in FRUITS:
            abort(404)
        changed = kept_other = 0
        backup = None
        with lock_for("status:" + fruit):
            # ⚠️ 이 되돌리기는 **다시 «일괄 제외» 를 눌러도 원래대로 돌아오지 않는다**
            #    (이미 데이터셋에서 빠진 사진은 «제외» 로 다시 표시할 수 없기 때문).
            #    그래서 손대기 «전» 의 status.json 을 통째로 한 벌 남겨 둔다.
            #    0918 UI사이클4 N10: 다만 **되돌릴 것이 0장이면** 백업도 만들지 않는다. 전에는 0장에도
            #    _status_backup_<시각>.json 이 하나씩 생겨 공용 data/ 에 쌓였다(사이클3 2차가 11개를 남겼다).
            data = read_status(fruit)
            # 0918 UI사이클5 2차: 전에는 «메모가 «중복: » 으로 시작» 도 같이 봤다. 그 조건은 `src` 표식이
            # 생긴 뒤로는 덤인데(표식은 이 단추만 남긴다), **번호 저장을 한 번 하면 메모 앞부분이
            # «번호 편집 … · (이전) 중복: …» 으로 바뀌어**(instances.py) 이 단추가 자기가 넣은 제외를
            # 못 되돌렸다(실측 cycle_5/stage2/r2_undo.py G3). 판별은 `src` 표식 하나로만 한다.
            n_undoable = sum(1 for r in data.values()
                             if r.get("status") == "exclude" and r.get("src") == SRC_DUP_BULK)
            if n_undoable:
                backup = backup_status(fruit)
            for s, rec in list(data.items()):
                if rec.get("status") != "exclude":
                    continue
                if rec.get("src") != SRC_DUP_BULK:
                    kept_other += 1        # 3차 판정·사람이 넣은 제외 — 그대로 둔다
                    continue
                rec["status"] = "unreviewed"
                rec["note"] = ""
                rec["at"] = now_str()
                rec.pop("src", None)
                # 0918 UI사이클5 2차: `prev`(=«제외» 한 벌)를 남겨 두면, 이 단추로 제외를 푼 사진에
                # «수정본 되돌리기» 를 누르는 순간 제외가 되살아난다. 그때는 src 표식이 없으니 이
                # 단추로 다시 풀 수도 없다(실측 r2_undo.py G2). 되돌렸으면 돌아갈 자리도 없앤다.
                rec.pop("prev", None)
                changed += 1
            if changed:
                write_status(fruit, data)      # 0장이면 파일도 건드리지 않는다(사이클4 N10)
        return jsonify({"ok": True, "changed": changed, "kept": kept_other,
                        "kept_other": kept_other, "backup": backup})


    @app.route("/api/exclude_group", methods=["POST"])
    def api_exclude_group():
        """**한 묶음만** — 대표를 뺀 나머지를 «제외» 로 표시한다(0917 UI 사이클3 ①).

        과일 통째 일괄 제외(/api/apply_duplicate_exclusions)와 다른 점 두 가지:
          · 지금 보고 있는 사진이 든 묶음 하나만 건드린다.
          · **사람이 이미 판정한 사진(ok·fixed·flag·exclude)은 건너뛴다.** 왜 건너뛰었는지
            skipped 로 돌려주므로 화면이 «3장 중 1장은 이미 «수정함» 이라 그대로 뒀습니다» 라고 말할 수 있다.
        메모는 기존 일괄 제외와 **같은 형식**(«중복: <대표stem>») 이라 되돌리기·내보내기가 한 규칙으로 돈다.
        """
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        stem = d.get("stem", "")
        check(fruit, stem)
        dup = load_duplicates(fruit)
        gi = dup["of_stem"].get(stem)
        if gi is None:
            return err_json("이 사진은 «거의 같은 사진» 묶음에 들어 있지 않습니다.", 400)
        group = dup["groups"][gi]
        by = (d.get("by") or "익명").strip()[:rules.NAME_MAX]
        here = stem_set(fruit)
        changed, skipped = [], []
        with lock_for("status:" + fruit):
            data = read_status(fruit)
            rep = DUP.pick_representative(group, data)
            for s in group:
                if s == rep:
                    continue
                if s not in here:
                    skipped.append({"stem": s, "why": "outside"})     # 이미 폴더에서 빠진 사진
                    continue
                rec = data.get(s, {})
                cur = rec.get("status", "unreviewed")
                if cur != "unreviewed":
                    skipped.append({"stem": s, "why": cur})           # 사람이 이미 본 사진은 안 건드린다
                    continue
                rec["status"] = "exclude"
                rec["by"] = by
                rec["note"] = "중복: %s" % rep
                rec["at"] = now_str()
                rec["src"] = SRC_DUP_GROUP       # 되돌리기가 «이 단추가 넣은 것» 만 알아보게 하는 표식
                data[s] = rec
                changed.append(s)
            if changed:
                write_status(fruit, data)
        return jsonify({"ok": True, "group": gi, "rep": rep, "members": group,
                        "changed": changed, "skipped": skipped})


    @app.route("/api/undo_exclude_group", methods=["POST"])
    def api_undo_exclude_group():
        """위 단추로 **방금** 제외한 것만 되돌린다 — 보낸 stem 목록 중 네 가지가 모두 맞는 것만.

          ① 지금 상태가 exclude   ② 메모가 «중복: » 으로 시작
          ③ `src` 표식이 이 단추의 것(dup_group)   ④ by 가 보낸 이름과 같다
        ③④ 때문에 3차 AI 판정이 넣어 둔 기존 «중복: …» 제외는 이 단추로 지워지지 않는다
        (0917 ab사이클2 P1(나)과 같은 규칙).
        """
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        if fruit not in FRUITS:
            abort(404)
        by = (d.get("by") or "익명").strip()[:rules.NAME_MAX]
        stems = [s for s in (d.get("stems") or []) if isinstance(s, str)][:rules.UNDO_STEMS_MAX]
        changed, kept = [], []
        with lock_for("status:" + fruit):
            data = read_status(fruit)
            for s in stems:
                rec = data.get(s)
                # 0918 UI사이클5 2차: «메모가 «중복: » 으로 시작» 조건을 뺐다 — 번호를 한 번 저장하면
                # 메모 앞부분이 «번호 편집 …» 으로 바뀌어(instances.py) 이 단추가 **방금 자기가 넣은**
                # 제외를 못 되돌리고, 화면은 «1장은 다른 사람이 넣은 제외라 그대로 둡니다» 라고
                # 사실과 다른 말을 했다(실측 cycle_5/stage2/r2_undo.py G3). 판별은 src·by 두 개로 한다.
                if (not rec or rec.get("status") != "exclude"
                        or rec.get("src") != SRC_DUP_GROUP
                        or (rec.get("by") or "") != by):
                    kept.append(s)
                    continue
                rec["status"] = "unreviewed"
                rec["note"] = ""
                rec["at"] = now_str()
                rec.pop("src", None)
                rec.pop("prev", None)      # 0918 2차: 남기면 «수정본 되돌리기» 가 제외를 되살린다(G2)
                changed.append(s)
            if changed:
                write_status(fruit, data)
        return jsonify({"ok": True, "changed": changed, "kept": kept})


    @app.route("/api/export_excluded", methods=["POST"])
    def api_export_excluded():
        """제외된 사진 목록을 data/<fruit>/excluded_list.txt 로 저장."""
        d = request.get_json(force=True, silent=True) or {}
        fruit = d.get("fruit", "")
        if fruit not in FRUITS:
            abort(404)
        items = DUP.excluded_stems(fruit, include_duplicates=True,
                                   drop_flag=bool(d.get("drop_flag")))
        p = os.path.join(DATA_DIR, fruit, "excluded_list.txt")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        lines = ["# 제외 목록 — %s — %s" % (fruit, now_str()),
                 "# 형식: <stem><TAB><이유>   (원본은 전혀 건드리지 않았습니다)",
                 "# 이 목록으로 실제 파일을 지우려면: export/make_delete_script.py 로 스크립트를 만든 뒤",
                 "# 곽동신이 내용을 직접 확인하고 실행하세요."]
        for s, r in items:
            lines.append("%s\t%s" % (s, r))
        tmp = p + ".tmp%d.%d" % (os.getpid(), threading.get_ident())  # 0918 사이클4 2차: 같은 파일을 두 요청이 동시에 쓰면 PID 만으로는 임시 이름이 겹쳐 500 이 난다
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, p)
        return jsonify({"ok": True, "path": p, "n": len(items)})
