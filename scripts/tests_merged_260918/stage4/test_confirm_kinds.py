# -*- coding: utf-8 -*-
"""4차 — 툴의 «종류별 확정»(상자 `confirmed_boxes` · 번호 `confirmed_instances`) 회귀시험.

작성: 2026-09-19. 고치기 전 판(`tools/_backup_260919_m4_build_merged_dataset.py`)에서는 실패하고,
고친 뒤에는 전부 통과해야 한다.

고치기 전 판으로 돌리려면:
    BUILD_PY=/data/project/2026summer/kds0206/semantic-segmentation/tools/_backup_260919_m4_build_merged_dataset.py \
      /home/kds0206/.conda/envs/kwak/bin/python stage4/test_confirm_kinds.py

무엇을 보는가 — 가짜 status.json 으로 다음 조합을 만들어 기대 출처·txt 유무·칸 값을 본다.
    (상자 ok / fixed / exclude / flag / 없음+빈 json / 없음+비지 않은 json) × (번호 ok / exclude / 없음)
  + 추가 두 가지: 확정 없는 툴 json 만 있고 다른 출처가 없을 때(`tool_unconfirmed` 표시만) ·
                 상자 확정은 있는데 툴 json 이 없을 때(기존 우선순위로 되넘김 + 문제 목록)

모래상자(`stage4/sandbox/`) 안에서만 만든다. 검수판·원본·툴 data·팀원 폴더는 **읽기만** 한다.
"""
import csv
import io
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox")
TOOLS = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("BUILD_PY", os.path.join(TOOLS, "build_merged_dataset.py"))
KDS = "/data/project/2026summer/kds0206"
REV917 = os.path.join(KDS, "datasets_reviewed_260917")
PSM = "/data/project/2026summer/platform/work/park_seongmoon"
PY = sys.executable
HUMAN = "곽동신"
AI = "AI 3회 검수(Opus5→Opus5→Fable5.1)"
fails = []
n_checks = [0]
print("시험 대상 스크립트: %s" % BUILD)

sys.path.insert(0, TOOLS)
import build_merged_dataset as B                      # noqa: E402  (load_mask_bool·write_u16 만 쓴다)


def check(n, ok, msg=""):
    n_checks[0] += 1
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n + (" — " + msg if msg else ""))
    return ok


# ─────────────────────────────────────────── 조합표
# 상자 6가지 × 번호 3가지 = 18 + 추가 2 = 20장
BOX_CASES = [
    ("ok",       "tool_json_full"),      # 확정 ok  + 툴 json(상자 1개)
    ("fixed",    "tool_json_full"),      # 확정 fixed
    ("exclude",  "tool_json_full"),      # 확정 exclude → 상자 없음
    ("flag",     "tool_json_full"),      # 확정 flag    → 상자 없음
    (None,       "tool_json_empty"),     # 확정 없음 + 빈 json  → psm_gt (M2-7 그대로)
    (None,       "tool_json_full"),      # 확정 없음 + 비지 않은 json → psm_gt (채택 안 함)
]
INST_CASES = ["ok", "exclude", None]


def expect_box(bst, kind, has_psm):
    """그 조합에서 기대하는 (boxes_source, txt 가 있나)."""
    if bst in ("ok", "fixed"):
        if kind in ("tool_json_full", "tool_json_empty"):
            return "tool", True
        return ("psm_gt", True) if has_psm else ("none", False)
    if bst in ("exclude", "flag"):
        return "none", False
    if has_psm:
        return "psm_gt", True
    if kind == "tool_json_full":
        return "tool_unconfirmed", False
    return "none", False


def expect_inst(ist, has_fixed):
    if ist in ("ok", "fixed"):
        return "tool_confirmed", True
    if ist in ("exclude", "flag"):
        return "none", False
    return ("instances_fixed", True) if has_fixed else ("reviewed_number_mask", True)


# ─────────────────────────────────────────── 모래상자
def build_sandbox():
    shutil.rmtree(SAND, ignore_errors=True)
    rev = os.path.join(SAND, "rev917", "apple")
    os.makedirs(os.path.join(rev, "images"))
    os.makedirs(os.path.join(rev, "masks"))
    src_rows = list(csv.DictReader(io.open(os.path.join(REV917, "apple", "manifest.csv"),
                                          encoding="utf-8")))
    keep = [r for r in src_rows if r["action"] == "keep"][:20]
    if len(keep) < 20:
        raise SystemExit("검수판 사과에 남긴 사진이 20장보다 적습니다(%d)" % len(keep))
    with io.open(os.path.join(rev, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(src_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(keep)
    for r in keep:
        for sub in ("images", "masks"):
            shutil.copy2(os.path.join(REV917, "apple", sub, r["stem"] + ".png"),
                         os.path.join(rev, sub, r["stem"] + ".png"))
    stems = [r["stem"] for r in keep]

    # 20장에 조합을 배정한다 — 앞 18장 = 6×3 전수, 뒤 2장 = 추가 경우
    plan = {}
    i = 0
    for bst, kind in BOX_CASES:
        for ist in INST_CASES:
            plan[stems[i]] = dict(box=bst, kind=kind, inst=ist, psm=True,
                                  fixed=(bst == "ok" and kind == "tool_json_full"))
            i += 1
    plan[stems[18]] = dict(box=None, kind="tool_json_full", inst=None, psm=False, fixed=False,
                           label="확정 없는 툴 json 만 있고 다른 출처 없음")
    plan[stems[19]] = dict(box="ok", kind="no_tool_json", inst=None, psm=True, fixed=False,
                           label="상자 확정은 있는데 툴 json 이 없음")

    # ── 가짜 status.json (마스크 확정은 일부러 **넣지 않는다** — 세 칸이 독립인지 보려는 것)
    tdir = os.path.join(SAND, "tool", "apple")
    os.makedirs(os.path.join(tdir, "boxes"))
    os.makedirs(os.path.join(tdir, "instances_fixed"))
    st = {}
    for s, p in plan.items():
        rec = {"status": "ok", "by": AI, "at": "2026-09-19 00:00", "note": "AI 제안"}
        if p["box"]:
            rec["confirmed_boxes"] = {"status": p["box"], "by": HUMAN,
                                      "at": "2026-09-19 01:00", "note": ""}
        if p["inst"]:
            rec["confirmed_instances"] = {"status": p["inst"], "by": HUMAN,
                                          "at": "2026-09-19 01:05", "note": ""}
        st[s] = rec
    json.dump(st, io.open(os.path.join(tdir, "status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)

    # ── 툴 상자 json · instances_fixed · 박성문 gt
    psm_json = os.path.join(SAND, "psm", "bbox_outputs", "apple", "gt_boxes", "json")
    psm_yolo = os.path.join(SAND, "psm", "bbox_outputs", "apple", "gt_boxes", "yolo_labels")
    os.makedirs(psm_json)
    os.makedirs(psm_yolo)
    real = os.path.join(PSM, "bbox_outputs", "apple", "gt_boxes")
    for s, p in plan.items():
        with Image.open(os.path.join(rev, "images", s + ".png")) as im:
            w, h = im.size
        if p["kind"] != "no_tool_json":
            boxes = [] if p["kind"] == "tool_json_empty" else \
                [{"id": 1, "cls": "fruit", "xyxy": [10, 10, 60, 80], "src": "human"}]
            json.dump({"stem": s, "fruit": "apple", "width": w, "height": h,
                       "by": HUMAN if boxes else "자동시험 정리", "at": "2026-09-19 01:02",
                       "note": "", "boxes": boxes},
                      io.open(os.path.join(tdir, "boxes", s + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False)
        if p["fixed"]:
            m = B.load_mask_bool(os.path.join(rev, "masks", s + ".png"))
            arr = np.zeros(m.shape, np.uint32)
            arr[m] = 7
            B.write_u16(os.path.join(tdir, "instances_fixed", s + ".png"), arr)
        if p["psm"]:
            a = os.path.join(real, "json", s + ".json")
            if os.path.exists(a):
                shutil.copy2(a, os.path.join(psm_json, s + ".json"))
                b = os.path.join(real, "yolo_labels", s + ".txt")
                if os.path.exists(b):
                    shutil.copy2(b, os.path.join(psm_yolo, s + ".txt"))
            else:           # 진짜 gt 가 없는 사진이면 같은 형식의 가짜를 만든다
                json.dump({"image_size_hw": [h, w], "total_fruit_count": 1,
                           "detections": [{"bbox_xywh": [20, 20, 40, 50]}]},
                          io.open(os.path.join(psm_json, s + ".json"), "w", encoding="utf-8"))
    return plan, stems


def run(extra):
    out = os.path.join(SAND, "out")
    os.makedirs(out, exist_ok=True)
    cmd = [PY, BUILD, "--fruits", "apple", "--out-root", out, "--date", "260919",
           "--reviewed-260917", os.path.join(SAND, "rev917"),
           "--tool-data", os.path.join(SAND, "tool"),
           "--psm-root", os.path.join(SAND, "psm"),
           "--cih-root", os.path.join(SAND, "없는폴더_cih"),
           "--lsh-root", os.path.join(SAND, "없는폴더_lsh"), "--no-prev"] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True), out


def main():
    plan, stems = build_sandbox()
    print("\nS4-0 빌드")
    r, out = run(["--suffix", "s4"])
    d = os.path.join(out, "datasets_merged_260919_s4")
    if not check("S4-0 빌드가 통과(exit 0 · 자체 검사 통과)", r.returncode == 0,
                 (r.stdout + r.stderr)[-900:]):
        print(r.stdout[-3000:])
        return 1
    man = {row["stem"]: row for row in csv.DictReader(io.open(os.path.join(d, "manifest.csv"),
                                                             encoding="utf-8"))}
    bdir, idir = os.path.join(d, "apple", "boxes"), os.path.join(d, "apple", "instances")

    print("\nS4-A 상자 — 확정 종류별 채택 (6가지 × 번호 3가지)")
    for s, p in sorted(plan.items(), key=lambda kv: stems.index(kv[0])):
        row = man[s]
        want_src, want_txt = expect_box(p["box"], p["kind"], p["psm"])
        name = "S4-A %s(상자 %s·%s%s)" % (s, p["box"] or "확정없음", p["kind"],
                                         ("·" + p["label"]) if p.get("label") else "")
        got_txt = os.path.exists(os.path.join(bdir, s + ".txt"))
        got_json = os.path.exists(os.path.join(bdir, s + ".json"))
        check(name + " boxes_source", row["boxes_source"] == want_src,
              "기대 %s · 실제 %s" % (want_src, row["boxes_source"]))
        check(name + " YOLO txt·json 유무", got_txt == want_txt and got_json == want_txt,
              "기대 %s · txt=%s json=%s" % (want_txt, got_txt, got_json))
        check(name + " has_boxes", row["has_boxes"] == ("1" if want_txt else "0"), row["has_boxes"])
        check(name + " boxes_confirmed_status", row.get("boxes_confirmed_status", "") == (p["box"] or "-"),
              row.get("boxes_confirmed_status", ""))
        if p["box"]:
            check(name + " boxes_confirmed_by/at",
                  row.get("boxes_confirmed_by", "") == HUMAN and row.get("boxes_confirmed_at", "") == "2026-09-19 01:00",
                  "%s / %s" % (row.get("boxes_confirmed_by", ""), row.get("boxes_confirmed_at", "")))
        else:
            check(name + " 확정이 없으면 by/at 은 빈칸",
                  not row.get("boxes_confirmed_by", "") and not row.get("boxes_confirmed_at", ""),
                  "%s / %s" % (row.get("boxes_confirmed_by", ""), row.get("boxes_confirmed_at", "")))

    print("\nS4-B 번호 — 확정 종류별 채택")
    for s, p in sorted(plan.items(), key=lambda kv: stems.index(kv[0])):
        row = man[s]
        want_src, want_png = expect_inst(p["inst"], p["fixed"])
        name = "S4-B %s(번호 %s·instances_fixed %s)" % (s, p["inst"] or "확정없음",
                                                      "있음" if p["fixed"] else "없음")
        got = os.path.exists(os.path.join(idir, s + ".png"))
        check(name + " instances_source", row["instances_source"] == want_src,
              "기대 %s · 실제 %s" % (want_src, row["instances_source"]))
        check(name + " 번호 파일 유무", got == want_png, "기대 %s · 실제 %s" % (want_png, got))
        check(name + " has_instances", row["has_instances"] == ("1" if want_png else "0"),
              row["has_instances"])
        check(name + " instances_confirmed_status",
              row.get("instances_confirmed_status", "") == (p["inst"] or "-"),
              row.get("instances_confirmed_status", ""))
        if want_png and p["fixed"] and p["inst"] in (None, "ok"):
            arr = B.read_u16(os.path.join(idir, s + ".png"))
            check(name + " instances_fixed 의 번호(7)를 썼다",
                  set(np.unique(arr).tolist()) <= {0, 7}, str(np.unique(arr)[:5].tolist()))

    print("\nS4-C 세 확정이 서로 독립인가 · 사람 메모·문제 목록")
    check("S4-C1 마스크 확정이 없으므로 source 는 human_* 이 아니다",
          {man[s]["source"] for s in plan} == {"ai"},
          str({man[s]["source"] for s in plan}))
    check("S4-C2 마스크 확정 칸(confirmed_by/at)은 비어 있다",
          all(not man[s]["confirmed_by"] and not man[s]["confirmed_at"] for s in plan))
    check("S4-C3 남긴 장수 20장 그대로(상자·번호 확정은 사진을 빼지 않는다)",
          sum(1 for s in plan if not man[s]["action"].startswith("excluded")) == 20)
    bs = json.load(io.open(os.path.join(d, "build_summary.json"), encoding="utf-8"))
    cnt = bs["counts"]["apple"]
    check("S4-C4 counts 에 n_confirmed_boxes(=상자 확정 13장)", cnt.get("n_confirmed_boxes") == 13,
          str(cnt.get("n_confirmed_boxes")))
    check("S4-C5 counts 에 n_confirmed_instances(=번호 확정 12장)",
          cnt.get("n_confirmed_instances") == 12, str(cnt.get("n_confirmed_instances")))
    check("S4-C6 counts 에 n_confirmed_mask=0(마스크는 아무도 확정하지 않았다)",
          cnt.get("n_confirmed_mask") == 0, str(cnt.get("n_confirmed_mask")))
    probs = bs["problems"]
    check("S4-C7 «확정은 있는데 툴 json 이 없음» 이 문제 목록에 적힌다",
          any("툴 boxes json 이 없습니다" in x for x in probs), str(probs[:3]))
    check("S4-C8 확정 없는 툴 json 을 채택하지 않았다고 note 에 적힌다",
          "채택하지 않았습니다" in man[stems[15]]["note"], man[stems[15]]["note"][:120])
    check("S4-C9 상자 확정 exclude 의 이유가 note 에 적힌다",
          "상자 확정 «exclude»" in man[stems[6]]["note"], man[stems[6]]["note"][:120])
    check("S4-C10 번호 확정 exclude 의 이유가 note 에 적힌다",
          "번호 확정 «exclude»" in man[stems[1]]["note"], man[stems[1]]["note"][:120])
    rme = io.open(os.path.join(d, "README.md"), encoding="utf-8").read()
    check("S4-C11 README 에 «종류별 사람 확정 수» 표가 있다", "종류별 사람 확정 수" in rme)
    check("S4-C12 README 값 사전에 tool_unconfirmed·tool_confirmed 가 있다",
          "`tool_unconfirmed`" in rme and "`tool_confirmed`" in rme)

    print("\nS4-D 자체 검사(verify) 가 어긋남을 잡는가 — 일부러 어긋난 파일을 만든다")
    # ① 상자 확정 exclude 인 사진에 txt 를 만들어 두고 다시 빌드하면… 는 빌드가 폴더를 새로 만들므로,
    #    대신 build_merged_dataset.verify() 를 직접 불러 본다(출력 폴더는 그대로 둔다).
    sys.path.insert(0, TOOLS)
    import importlib
    M = importlib.import_module(os.path.basename(BUILD)[:-3]) if BUILD.endswith(".py") else None
    rows = list(csv.DictReader(io.open(os.path.join(d, "manifest.csv"), encoding="utf-8")))
    ex_stem = stems[6]                                    # 상자 확정 exclude 인 사진
    io.open(os.path.join(bdir, ex_stem + ".txt"), "w").write("0 0.5 0.5 0.1 0.1\n")
    bad = M.verify(d, ["apple"], rows)
    os.remove(os.path.join(bdir, ex_stem + ".txt"))
    check("S4-D1 상자 확정 exclude 인데 txt 가 있으면 검사가 걸린다",
          any("상자 확정이 «exclude»" in x for x in bad), str(bad[:3]))
    tu_stem = stems[18]                                   # tool_unconfirmed 로 표시된 사진
    rows2 = [dict(r, has_boxes="1") if r["stem"] == tu_stem else r for r in rows]
    bad2 = M.verify(d, ["apple"], rows2)
    check("S4-D2 tool_unconfirmed 인데 채택됐으면 검사가 걸린다",
          any("tool_unconfirmed" in x for x in bad2), str(bad2[:3]))
    rows3 = [dict(r, has_instances="1") if r["stem"] == stems[1] else r for r in rows]
    bad3 = M.verify(d, ["apple"], rows3)
    check("S4-D3 번호 확정 exclude 인데 번호가 나갔으면 검사가 걸린다",
          any("번호 확정이 «exclude»" in x for x in bad3), str(bad3[:3]))

    print("\nS4-E 멱등 — 두 번 돌려도 manifest 가 바이트까지 같다")
    r2, _ = run(["--suffix", "s4b"])
    d2 = os.path.join(out, "datasets_merged_260919_s4b")
    check("S4-E1 두 번째 빌드도 exit 0", r2.returncode == 0, (r2.stdout + r2.stderr)[-400:])
    if r2.returncode == 0:
        check("S4-E2 manifest 바이트 동일",
              io.open(os.path.join(d, "manifest.csv"), "rb").read()
              == io.open(os.path.join(d2, "manifest.csv"), "rb").read())

    print("\n검사 %d항목 — %s" % (n_checks[0],
          "전부 통과" if not fails else "실패 %d건:" % len(fails)))
    for x in fails:
        print("  - " + x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
