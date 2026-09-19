# -*- coding: utf-8 -*-
"""데이터 정리(내보내기) — 시작 · 진행 · 목록 · 미리 세기.

구조 사이클 2(2026-09-20)에 `server.py` 에서 그대로 옮겼다(라우트 4개).
실제로 내보내는 코드는 CLI 와 **같은 함수**다(`export/export_dataset.py`·`api/boxes.py`).
"""

from __future__ import annotations
from typing import Any
import json
import os
import sys
import threading
from datetime import datetime
from types import SimpleNamespace

from flask import jsonify, request

from api import boxes as _boxes
from api import instances as _instances
from core.paths import (DATA_DIR, EXPORTS_DIR, FRUITS, ROOT, box_set, stems_of)
from core.status_store import read_status
from core.util import err_json, lock_for, log_exc, now_str, short_path
from domain import dupes as DUP
from domain import rules
from domain.statusfmt import STATUSES, confirmed_of

EXPORT_KINDS = ["mask", "instances", "boxes", "counts"]   # counts = 0919 개수 표(counts.csv)
_jobs = {}                      # job id -> 아래 job 딕셔너리 (dict(_jobs) 는 C 층에서 한 번에 복사된다)
_exp_mod = None
_exp_guard = threading.Lock()


def export_module() -> Any:
    """export/export_dataset.py 를 한 번만 불러온다(CLI 와 **같은 코드**를 쓰기 위해)."""
    global _exp_mod
    with _exp_guard:
        if _exp_mod is None:
            d = os.path.join(ROOT, "export")
            if d not in sys.path:
                sys.path.insert(0, d)
            import export_dataset
            _exp_mod = export_dataset
        return _exp_mod


def export_args(fruit: str, kinds: Any, confirmed_only: bool, out: Any, dry_run: bool=False) -> Any:
    """export_one() 에 넘길 «명령줄 흉내» — CLI 와 뜻이 같아야 한다.
    keep_duplicates·drop_flag 는 CLI 기본값 그대로(=False)."""
    return SimpleNamespace(fruit=fruit, out=out, dry_run=dry_run, keep_duplicates=False,
                           drop_flag=False, confirmed_only=bool(confirmed_only),
                           copy_images=False, instances=("instances" in (kinds or [])),
                           counts=("counts" in (kinds or [])))


def export_caps(fruit: str) -> Any:
    """이 과일에 무슨 자료가 있나 + 사람 확정이 몇 장인가 — 화면이 체크칸을 비활성으로 만들고
    «지금 확정된 사진 N장» 을 늘 보여 주는 데 쓴다."""
    stems = stems_of(fruit)
    st = read_status(fruit)
    c = {k: 0 for k in STATUSES}
    cb = {k: 0 for k in STATUSES}
    ci = {k: 0 for k in STATUSES}
    # 0918 사이클4 3차 전 소수정(총괄 결정 2): «나갈 상자» 는 **상자 파일이 실제로 있는 사진**만
    # 센다. 확정만 얹고 상자를 한 번도 저장하지 않은 사진이 있으면(확정은 화면에서 막지 않는다)
    # 예전에는 «나갈 상자 1장» 이라고 말하면서 txt 를 0장 냈다(실측 2차 §4-4 2번 · c2_boxout [가]).
    # 내보내는 쪽(export_boxes_to)이 이미 «파일이 있어야 txt» 이므로, 세는 쪽을 그 규칙에 맞춘다.
    bset = box_set(fruit)
    n_box_out = 0
    for s in stems:
        v = confirmed_of(st.get(s))
        c[v["status"] if v else "unreviewed"] += 1
        vb = confirmed_of(st.get(s), "boxes")
        cb[vb["status"] if vb else "unreviewed"] += 1
        if vb and rules.goes_out(vb["status"]) and s in bset:
            n_box_out += 1
        vi = confirmed_of(st.get(s), "instances")
        ci[vi["status"] if vi else "unreviewed"] += 1
    d = os.path.join(DATA_DIR, fruit, "boxes")
    n_box = len([n for n in os.listdir(d) if n.endswith(".json")]) if os.path.isdir(d) else 0
    return {"n_images": len(stems),
            "has_mask": os.path.isdir(os.path.join(DUP.dataset_for(fruit), fruit, "masks")),
            "has_instances": bool(_instances.has_numbers(fruit)),
            "n_box_images": n_box,
            "confirmed_counts": c,
            # 사람이 확정한 것 중 **실제로 나갈 수 있는 것**(ok·fixed). flag·exclude 는 빠진다.
            "n_confirmed": sum(c.values()) - c["unreviewed"],
            "n_confirmed_out": sum(c[k] for k in rules.CONFIRM_OUT),
            # 0918 사이클4 결정 1 — 종류별 «확정 장수». 화면의 «지금 확정된 사진 N장» 줄이
            # 고른 종류(세그 마스크·열매 번호·상자 YOLO)에 맞는 숫자를 말하게 한다.
            "confirmed_counts_boxes": cb,
            "n_confirmed_boxes": sum(cb.values()) - cb["unreviewed"],
            # ok·fixed 이면서 **상자 파일이 있는** 사진만(총괄 결정 2) = 실제로 나가는 txt 수
            "n_confirmed_boxes_out": n_box_out,
            "confirmed_counts_instances": ci,
            "n_confirmed_instances": sum(ci.values()) - ci["unreviewed"],
            "n_confirmed_instances_out": sum(ci[k] for k in rules.CONFIRM_OUT)}


JOB_FIELDS = ("job", "fruit", "kinds", "confirmed_only", "by", "state", "done", "total", "msg",
              "started", "finished", "n_images", "n_dropped", "n_instances",
              "n_box_images", "n_boxes", "n_counts")


def job_public(j: Any) -> dict[str, Any]:
    """내보내기 작업에서 화면에 공개할 상태만 골라 돌려준다."""
    out = {k: j.get(k) for k in JOB_FIELDS}
    out["out"] = short_path(j.get("out"))
    return out


def write_job_json(job: Any) -> None:
    """<out>/job.json — **시작할 때 «running» 으로 먼저 쓰고**, 끝나면 같은 자리에 덮어쓴다.
    0918 사이클3 3차 전 소수정(2차 §4-4): 전에는 **끝날 때만** 썼다. 그래서 서버가 도중에 죽으면
    job.json 이 없는 반쪽 폴더가 남고, 목록에도 안 보이고 상태를 물으면 404 였다.
    지금은 «running» 인 채 남으므로 목록이 «도는 중(중단됐을 수 있음)» 이라고 말해 준다."""
    try:
        with open(os.path.join(job["out"], "job.json"), "w", encoding="utf-8") as f:
            json.dump(job_public(job), f, ensure_ascii=False, indent=1)
    except Exception:
        log_exc("job.json 을 쓰지 못했습니다: %s", job.get("out"))


def export_worker(job: Any) -> None:
    """오래 걸리는 일 — 자물쇠 **밖**의 daemon 스레드에서 돈다."""
    out, fruit, kinds = job["out"], job["fruit"], job["kinds"]
    try:
        def on_step(i, n):
            job["done"], job["total"] = i, n
            job["msg"] = "사진 %d / %d" % (i, n)

        # 🔴 0919 «개수 세기» **사이클4**(사이클1 2차 §2-4·§4-5): 판정 기록을 **여기서 한 번만** 읽고
        # 세 갈래(마스크·개수·상자 YOLO)에 **같은 스냅샷**을 넘긴다. 전에는 `export_one` 이 한 번,
        # `write_counts_csv` 가 (사이클1 이 고친 뒤로는 export_one 이 넘겨 주지만 «개수만» 갈래에서는
        # 스스로) 한 번, 아래 상자 갈래가 **세 번째로** 또 읽었다. 사과 1,001장은 수십 초가 걸려서
        # 그 사이에 누가 확정하면 manifest 에는 «제외» 인 사진이 상자 YOLO 에는 나갔다.
        st_snap = read_status(fruit)
        if "mask" in kinds or "instances" in kinds:
            res = export_module().export_one(
                fruit, out, export_args(fruit, kinds, job["confirmed_only"], out),
                on_step=on_step, st=st_snap) or {}
            job["n_images"] = res.get("n_out", 0)
            job["n_dropped"] = res.get("n_dropped", 0)
            job["n_instances"] = res.get("n_instances", 0)
            job["n_counts"] = res.get("n_counts", 0)      # 0919 «개수 세기» — export_one 이 같이 쓴다
        elif "counts" in kinds:
            # 개수 표 **만** 고른 때. 사진·마스크는 내보내지 않는다(상자 YOLO 만 고를 수 있는 것과 같다).
            job["msg"] = "개수를 세는 중…"
            job["n_counts"] = export_module().write_counts_csv(
                fruit, out, export_args(fruit, kinds, job["confirmed_only"], out), st=st_snap)
        if "boxes" in kinds:
            job["msg"] = "상자를 내보내는 중…"
            # 0918 사이클4 결정 1: «사람 확정만» 이면 **`confirmed_boxes` 가 ok·fixed 인 사진만**
            # 낸다. 사이클3 2차 §2 중간 5 «상자 YOLO 는 사람 확정을 전혀 가리지 않는다» 가 여기서
            # 메워진다 — 확정이 없는 사진의 txt 는 아예 만들어지지 않는다.
            # (마스크 확정으로 **대체하지 않는다** — 상자를 본 적 없는 사람의 확정이기 때문이다.)
            keep = None
            if job["confirmed_only"]:
                keep = [s for s in stems_of(fruit)      # 위 `st_snap` — 세 번째 읽기를 없앴다(사이클4)
                        if rules.goes_out((confirmed_of(st_snap.get(s), "boxes") or {}).get("status"))]
            b = _boxes.export_boxes_to(DATA_DIR, fruit, os.path.join(out, "boxes"),
                                       os.path.join(out, "boxes", "boxes_all.json"), at=now_str(),
                                       stems=keep)
            job["n_box_images"] = (b or {}).get("n_images", 0)
            job["n_boxes"] = (b or {}).get("n_boxes", 0)
        job["state"] = "done"
        job["msg"] = "끝났습니다 — 사진 %d장 · 제외 %d장" % (job["n_images"], job["n_dropped"])
    except Exception as e:                                  # noqa: BLE001 (무엇이 나도 job 에 남긴다)
        job["state"] = "error"
        job["msg"] = "실패했습니다: %s" % e
        log_exc("내보내기 실패 %s", job.get("job"))
    job["finished"] = now_str()
    write_job_json(job)                                      # 시작할 때 쓴 «running» 을 덮어쓴다

def register(app: Any, ctx: Any) -> None:
    """라우트 4개를 붙인다."""


    @app.route("/api/export_start", methods=["POST"])
    def api_export_start():
        """데이터셋을 서버에 저장한다. 폴더 이름은 **서버가** 정한다(사람이 덮어쓸 수 없게)."""
        d = request.get_json(force=True, silent=True) or {}
        # 0918 사이클3 3차 전 소수정(2차 §4-5): 몸통이 `[1,2,3]`·`"peach"` 면 `.get` 이 없어 **500** 이었다.
        # 사이클3 이 만든 새 주소만 여기서 막는다(다른 옛 주소는 사이클4 «입력 검증» 묶음에서 한 번에).
        if not isinstance(d, dict):
            return err_json("보낸 내용이 «이름:값» 꾸러미가 아닙니다(JSON 객체여야 합니다).", 400)
        fruit = d.get("fruit", "")
        if fruit not in FRUITS:
            return err_json("과일 이름이 잘못됐습니다.", 400)
        kinds = d.get("kinds")
        if not isinstance(kinds, list) or not kinds or any(k not in EXPORT_KINDS for k in kinds):
            return err_json("내보낼 종류를 고르세요(세그 마스크·열매 번호·상자 중에서).", 400)
        kinds = [k for k in EXPORT_KINDS if k in kinds]          # 순서를 고정한다(표시·폴더 순서)
        if "instances" in kinds and "mask" not in kinds:
            return err_json("열매 번호는 세그 마스크와 함께 나갑니다 — 세그 마스크도 같이 고르세요.", 400)
        # 0918 사이클3 3차 전 소수정(2차 §4-6): 전에는 `bool()` 이라 `null`·`0`·`""`·`[]` 가 **False**
        # (= AI 제안 포함, 더 헐거운 쪽)가 됐다. 값을 «비워» 보내는 쪽이 더 많이 내보내면 안 된다.
        # 없거나 None 이면 **사람 확정만**(안전한 쪽) · 참/거짓이 아닌 값은 되묻는다.
        confirmed_only = d.get("confirmed_only", True)           # 기본값 = 사람 확정만(3차 결정 1)
        if confirmed_only is None:
            confirmed_only = True
        if not isinstance(confirmed_only, bool):
            return err_json("조건(confirmed_only)은 참·거짓이어야 합니다.", 400)
        by = str(d.get("by") or "익명")[:rules.NAME_MAX]
        job_id = datetime.now().strftime("%y%m%d_%H%M%S") + "_" + fruit
        out = os.path.join(EXPORTS_DIR, job_id)
        # 자물쇠는 **_jobs 를 보는 동안만** 잡는다(실제 내보내기는 오래 걸리므로 스레드에서).
        with lock_for("export:" + fruit):
            for j in dict(_jobs).values():
                if j["fruit"] == fruit and j["state"] == "running":
                    # 0918 사이클3 3차 전 소수정(2차 §4-7): 문구는 그대로 두고 `fruit` 칸을 같이 준다 —
                    # 화면(ui.js)이 이미 가진 FRUIT_KO 로 «복숭아» 라고 바꿔 쓴다(이름표를 두 군데 두지 않는다).
                    msg = "지금 %s 를 내보내는 중입니다 — 끝난 뒤에 다시 누르세요." % fruit
                    return jsonify({"ok": False, "error": msg, "msg": msg, "fruit": fruit}), 409
            try:
                os.makedirs(out, exist_ok=False)                 # ← 덮어쓰기 금지는 이 한 줄이 전부
            except FileExistsError:
                return err_json("같은 이름의 폴더가 이미 있습니다(같은 초에 두 번 눌렀을 수 있습니다). "
                                "1초 뒤에 다시 눌러 주세요 — 있는 폴더는 건드리지 않았습니다.", 409)
            job = {"job": job_id, "fruit": fruit, "kinds": kinds, "confirmed_only": confirmed_only,
                   "by": by, "state": "running", "done": 0, "total": 0, "msg": "준비 중…",
                   "out": out, "started": now_str(), "finished": "",
                   "n_images": 0, "n_dropped": 0, "n_instances": 0, "n_box_images": 0, "n_boxes": 0,
                   "n_counts": 0}
            _jobs[job_id] = job
            write_job_json(job)                                  # «running» 으로 먼저 써 둔다(2차 §4-4)
        # 0918 사이클3 3차 전 소수정(2차 §4-2): 스레드를 못 띄우면 job 이 **running 인 채** 남아서
        # 그 과일은 서버를 껐다 켜기 전에는 영영 409 였다(취소 주소가 없다). 지금은 error 로 바꾸고
        # 500 대신 사람 말로 답한다 — 다음에 누르면 정상으로 시작한다.
        try:
            threading.Thread(target=export_worker, args=(job,), daemon=True).start()
        except Exception as e:                                   # noqa: BLE001
            job["state"] = "error"
            job["msg"] = "시작하지 못했습니다(서버가 바쁩니다): %s" % e
            job["finished"] = now_str()
            write_job_json(job)
            log_exc("내보내기 스레드를 띄우지 못했습니다: %s", job_id)
            return err_json("지금은 서버가 바빠 내보내기를 시작하지 못했습니다 — 잠시 뒤에 다시 눌러 주세요.", 503)
        return jsonify({"ok": True, "job": job_id, "out": short_path(out)})


    @app.route("/api/export_status")
    def api_export_status():
        job = os.path.basename(request.args.get("job", ""))
        j = dict(_jobs).get(job)
        if j is not None:
            out = job_public(j)
            out["ok"] = True
            return jsonify(out)
        # 서버를 껐다 켜면 _jobs 가 비어 있다 → 폴더의 job.json 으로 답한다
        p = os.path.join(EXPORTS_DIR, job, "job.json") if job else ""
        if p and os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    out = json.load(f)
                out["ok"] = True
                return jsonify(out)
            except Exception:
                return err_json("그 작업의 기록(job.json)을 읽지 못했습니다.", 500)
        return err_json("그런 작업이 없습니다.", 404)


    @app.route("/api/export_list")
    def api_export_list():
        """끝난 폴더 목록(각 폴더의 job.json) + 과일마다 무슨 자료가 있나.
        화면은 이 주소가 **404 면 서버가 아직 이 기능을 모른다** 고 보고 탭을 잠근다."""
        items = []
        if os.path.isdir(EXPORTS_DIR):
            for n in sorted(os.listdir(EXPORTS_DIR), reverse=True):
                p = os.path.join(EXPORTS_DIR, n, "job.json")
                if not os.path.isfile(p):
                    continue                                     # job.json 이 없는 폴더(사람이 만든 것)
                try:
                    with open(p, encoding="utf-8") as f:
                        it = json.load(f)
                except Exception:
                    continue
                # 0918 사이클3 3차 전 소수정(2차 §4-4): 이제 job.json 은 **시작할 때** 도 쓴다.
                # «running» 인데 지금 도는 것이 아니면 서버가 도중에 죽은 것이다 →
                # 화면이 «도는 중(중단됐을 수 있음)» 이라고 적을 수 있게 표를 하나 붙인다.
                if it.get("state") == "running" and it.get("job") not in _jobs:
                    it["stale"] = True
                # 0918 사이클5(총괄) ③: 끝났는데 **아무것도 안 나간** 폴더(manifest 만 있는 빈 날짜 폴더)에
                # 표를 하나 붙인다. 사이클4 2차 §4-4 7번이 3차에 넘기고 3차가 사이클5 로 넘긴 것이다.
                # «만들지 않기»(가드)는 사이클3 2차가 못박은 «상자만 골라도 저장이 된다»(a5b_ui 화면-4-A)를
                # 깨고, 서버가 폴더를 지우는 것은 사람이 만든 파일까지 지울 위험이 있다 → **표시만** 한다.
                # 화면(ui.js expTable)이 그 줄 앞에 «빈 폴더» 라고 적고, 사람이 보고 지운다.
                # 0919 개수 사이클1 **2차 검수 C-1**: `n_counts` 를 세지 않아서 «개수(counts.csv)» 만
                # 고른 폴더가 줄이 있어도 «빈 폴더» 로 적혔다(실측 `stage2/a2_stale.py` [라] 라-2).
                if it.get("state") == "done" and not (it.get("n_images") or it.get("n_instances")
                                                      or it.get("n_box_images") or it.get("n_counts")):
                    it["empty"] = True
                items.append(it)
        return jsonify({"ok": True, "items": items[:rules.EXPORT_LIST_MAX], "n_all": len(items),
                        "running": [job_public(j) for j in dict(_jobs).values() if j["state"] == "running"],
                        "dir": short_path(EXPORTS_DIR), "kinds": EXPORT_KINDS,
                        "fruits": {f: export_caps(f) for f in FRUITS}})


    @app.route("/api/export_plan")
    def api_export_plan():
        """«지금 누르면 몇 장 나가나» — 파일은 하나도 쓰지 않는다(export_one 의 --dry-run 과 같은 길).
        확인창에 적는 숫자와 실제로 나가는 숫자가 **같은 코드**에서 나오게 하려고 이렇게 센다."""
        fruit = request.args.get("fruit", "")
        if fruit not in FRUITS:
            return err_json("과일 이름이 잘못됐습니다.", 400)
        confirmed_only = request.args.get("confirmed_only", "1") != "0"
        # instances 는 넣지 않는다 — 번호 출처를 보려고 장마다 파일을 열면 느리다(사과 1,001장 ≈ 100초)
        a = export_args(fruit, [], confirmed_only, None, dry_run=True)
        out = export_module().export_one(fruit, "(미리 세기 — 아무것도 쓰지 않습니다)", a) or {}
        out["ok"] = True
        out["caps"] = export_caps(fruit)
        return jsonify(out)
