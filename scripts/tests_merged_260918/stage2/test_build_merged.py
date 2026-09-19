# -*- coding: utf-8 -*-
"""build_merged_dataset.py 시험 — 작성: 2026-09-18

모래상자(검수판 각 과일 20장 사본 + 가짜 status.json)를 만들어 놓고 빌드를 돌려,
장수·`source`·제외 사유가 기대한 대로 나오는지 본다. 진짜 데이터는 읽기만 한다.

시험 목록
  T1 기대 장수·source·reason·마스크 출처·되살림
  T2 두 번 돌려도 manifest.csv 가 바이트까지 같다(멱등)
  T3 만들 폴더가 이미 있으면 exit 2
  T4 검사가 걸리면 폴더 이름 뒤에 _INCOMPLETE 가 붙고 exit 1
  T5 툴 export/export_dataset.py --confirmed-only 와 **같은 사진 집합**인지 대조(독립 증거)
  T6 진짜 입력으로 --dry-run 표

쓰는 법:
  PY=/home/kds0206/.conda/envs/kwak/bin/python
  $PY tools/tests_merged_260918/test_build_merged.py
모래상자·출력은 전부 tools/tests_merged_260918/sandbox/ 안에만 만든다(아무것도 지우지 않는다).
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
SAND = os.path.join(HERE, "sandbox")
BUILD = os.path.join(TOOLS, "build_merged_dataset.py")
PY = sys.executable
KDS = "/data/project/2026summer/kds0206"
TOOL_ROOT = "/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴"
REV = {"peach": os.path.join(KDS, "datasets_reviewed_260916"),
       "grape": os.path.join(KDS, "datasets_reviewed_260916"),
       "apple": os.path.join(KDS, "datasets_reviewed_260917"),
       "blueberry": os.path.join(KDS, "datasets_reviewed_260917")}
ORIG = os.path.join(KDS, "datasets_resized_2mp")
FRUITS = ["apple", "grape", "peach", "blueberry"]
N_KEEP, N_DROP = 20, 3
HUMAN = "곽동신"
AI = "AI 3회 검수(Opus5→Opus5→Fable5.1)"

sys.path.insert(0, TOOLS)
import build_merged_dataset as B                      # noqa: E402

fails = []


def check(name, ok, msg=""):
    print(("  [통과] " if ok else "  [실패] ") + name + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(name + (" — " + msg if msg else ""))
    return ok


# ───────────────────────────── 모래상자 만들기
def sandbox_paths():
    return dict(rev916=os.path.join(SAND, "reviewed_260916"),
                rev917=os.path.join(SAND, "reviewed_260917"),
                orig=os.path.join(SAND, "original"),
                tool=os.path.join(SAND, "tooldata"),
                psm=os.path.join(SAND, "team", "psm"),
                cih=os.path.join(SAND, "team", "cih"),
                lsh=os.path.join(SAND, "team", "lsh"),
                out=os.path.join(SAND, "out"))


def pick_stems(fruit):
    with open(os.path.join(REV[fruit], fruit, "manifest.csv"), encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: B.natkey(r["stem"]))
    keep = [r for r in rows if not r["action"].startswith("excluded")][:N_KEEP]
    drop = [r for r in rows if r["action"].startswith("excluded")][:N_DROP]
    return rows, keep, drop


def build_sandbox():
    """모래상자를 만든다. 사진 복사는 한 번만 하고(느리다), 가짜 status.json 같은 작은 것은 늘 다시 쓴다.
    아무것도 지우지 않는다."""
    p = sandbox_paths()
    done = os.path.join(SAND, "_sandbox_ready.json")
    copied = os.path.exists(done)
    plan = {}
    for fruit in FRUITS:
        rows, keep, drop = pick_stems(fruit)
        rev_out = os.path.join(p["rev916"] if REV[fruit].endswith("260916") else p["rev917"], fruit)
        for sub in ("images", "masks"):
            os.makedirs(os.path.join(rev_out, sub), exist_ok=True)
            os.makedirs(os.path.join(p["orig"], fruit, sub), exist_ok=True)
        if not copied:
            for r in keep:                              # 검수판 사본(남긴 사진)
                for sub in ("images", "masks"):
                    shutil.copy2(os.path.join(REV[fruit], fruit, sub, r["stem"] + ".png"),
                                 os.path.join(rev_out, sub, r["stem"] + ".png"))
                    sp = os.path.join(ORIG, fruit, sub, r["stem"] + ".png")
                    if os.path.exists(sp):
                        shutil.copy2(sp, os.path.join(p["orig"], fruit, sub, r["stem"] + ".png"))
            for r in drop:                              # 되살릴 수 있게 «원본» 쪽만 둔다
                for sub in ("images", "masks"):
                    sp = os.path.join(ORIG, fruit, sub, r["stem"] + ".png")
                    if os.path.exists(sp):
                        shutil.copy2(sp, os.path.join(p["orig"], fruit, sub, r["stem"] + ".png"))
        sel = keep + drop
        cols = list(rows[0].keys())
        with open(os.path.join(rev_out, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(sel)

        # ── 가짜 status.json (사람 확정 ok/fixed/flag/exclude/되살림/legacy 를 섞는다)
        ks = [r["stem"] for r in keep]
        ds = [r["stem"] for r in drop]
        st, exp = {}, {}
        def put(stem, rec, expect):
            st[stem] = rec
            exp[stem] = expect
        put(ks[0], {"status": "flag", "by": AI, "at": "2026-09-16 11:24", "note": "AI 제안",
                    "confirmed": {"status": "ok", "by": HUMAN, "at": "2026-09-18 10:00", "note": ""}},
            dict(kept=True, source="human_confirmed", action="keep"))
        put(ks[1], {"status": "fixed", "by": AI, "at": "x", "note": "",
                    "confirmed": {"status": "fixed", "by": HUMAN, "at": "2026-09-18 10:01", "note": "고침"}},
            dict(kept=True, source="human_confirmed", action="mask_fixed", mask_source="masks_fixed"))
        put(ks[2], {"status": "ok", "by": AI, "at": "x", "note": "",
                    "confirmed": {"status": "fixed", "by": HUMAN, "at": "2026-09-18 10:02", "note": ""}},
            dict(kept=True, source="human_confirmed", action="mask_fixed", mask_missing=True))
        put(ks[3], {"status": "ok", "by": AI, "at": "x", "note": "",
                    "confirmed": {"status": "exclude", "by": HUMAN, "at": "2026-09-18 10:03", "note": ""}},
            dict(kept=False, source="human_confirmed", action="excluded_human", reason="human_exclude"))
        put(ks[4], {"status": "ok", "by": AI, "at": "x", "note": "",
                    "confirmed": {"status": "flag", "by": HUMAN, "at": "2026-09-18 10:04", "note": ""}},
            dict(kept=False, source="human_confirmed", action="excluded_flag", reason="confirmed_flag"))
        put(ks[5], {"status": "ok", "by": "익명", "at": "2026-09-17 12:00", "note": "사람이 봄"},
            dict(kept=True, source="human_legacy", action="keep"))
        put(ks[6], {"status": "exclude", "by": "익명", "at": "2026-09-17 12:01", "note": ""},
            dict(kept=False, source="human_legacy", action="excluded_human", reason="human_exclude"))
        put(ks[7], {"status": "flag", "by": AI, "at": "x", "note": "AI 만 봄"},
            dict(kept=True, source="ai"))
        put(ks[8], {"status": "unreviewed", "by": "익명", "at": "x", "note": "수정본 되돌림"},
            dict(kept=True, source="ai", note_has="unreviewed"))
        for s in ks[9:]:
            exp[s] = dict(kept=True, source="reviewed")
        if ds:
            put(ds[0], {"status": "exclude", "by": AI, "at": "x", "note": "중복",
                        "confirmed": {"status": "ok", "by": HUMAN, "at": "2026-09-18 10:05", "note": ""}},
                dict(kept=True, source="human_confirmed", action="keep",
                     image_source="resized_2mp", note_has="되살림"))
            for s in ds[1:]:
                exp[s] = dict(kept=False, source="reviewed")
        tdir = os.path.join(p["tool"], fruit)
        os.makedirs(os.path.join(tdir, "masks_fixed"), exist_ok=True)
        os.makedirs(os.path.join(tdir, "instances_fixed"), exist_ok=True)
        os.makedirs(os.path.join(tdir, "boxes"), exist_ok=True)
        with open(os.path.join(tdir, "status.json"), "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1, sort_keys=True)
        shutil.copy2(os.path.join(TOOL_ROOT, "data", fruit, "duplicates.json"),
                     os.path.join(tdir, "duplicates.json"))

        # ks[1] 은 masks_fixed 를 «진짜로» 둔다(오른쪽 아래 20×20 을 전경으로 만든 것) — ks[2] 는 일부러 안 둔다
        m = B.load_mask_bool(os.path.join(rev_out, "masks", ks[1] + ".png"))
        mf = m.copy()
        mf[-20:, -20:] = True
        B.save_mask_255(os.path.join(tdir, "masks_fixed", ks[1] + ".png"), mf)
        # ks[0] 에는 사람이 고친 번호 마스크를 둔다(원본 번호보다 먼저 쓰이는지 본다).
        # ⚠ 사진마다 크기가 다르므로(블루베리) **그 사진의 마스크 크기**로 만들어야 한다.
        m0 = B.load_mask_bool(os.path.join(rev_out, "masks", ks[0] + ".png"))
        inst = np.zeros(m0.shape, np.uint32)
        inst[m0] = 7
        B.write_u16(os.path.join(tdir, "instances_fixed", ks[0] + ".png"), inst)
        # 상자 — 남긴 사진 하나(ks[9])와 뺀 사진 하나(ds[0] 이 아니라 ds[-1]) 에 둔다
        with Image.open(os.path.join(rev_out, "images", ks[9] + ".png")) as im:
            w, h = im.size
        for stem, keep_it in [(ks[9], True)] + ([(ds[-1], False)] if len(ds) > 1 else []):
            with open(os.path.join(tdir, "boxes", stem + ".json"), "w", encoding="utf-8") as f:
                json.dump({"stem": stem, "fruit": fruit, "width": w, "height": h,
                           "by": HUMAN, "at": "2026-09-18 10:10", "note": "",
                           "boxes": [{"id": 1, "cls": "fruit", "xyxy": [10, 10, 60, 80],
                                      "src": "human"}]}, f, ensure_ascii=False)
        plan[fruit] = dict(keep=ks, drop=ds, expect=exp,
                           boxes_kept=[ks[9]], masks_fixed=[ks[1]], inst_fixed=[ks[0]])
    build_team_sandbox(p, plan)
    os.makedirs(p["out"], exist_ok=True)
    with open(done, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    return p, plan


RUN = ""          # 돌릴 때마다 달라지는 꼬리표 — 아무것도 지우지 않고 다시 돌릴 수 있게(main 이 정한다)


def run_build(p, suffix, extra=()):
    cmd = [PY, BUILD, "--date", "260918", "--suffix", RUN + suffix, "--out-root", p["out"],
           "--tool-data", p["tool"], "--reviewed-260916", p["rev916"],
           "--reviewed-260917", p["rev917"], "--original-root", p["orig"],
           "--psm-root", p["psm"], "--cih-root", p["cih"], "--lsh-root", p["lsh"]] + list(extra)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r


def read_manifest(path):
    with open(path, encoding="utf-8", newline="") as f:
        return {(r["fruit"], r["stem"]): r for r in csv.DictReader(f)}


# ───────────────────────────── T1 기대값
def t1(p, plan, out_dir):
    man = read_manifest(os.path.join(out_dir, "manifest.csv"))
    ok_all = True
    for fruit in FRUITS:
        pl = plan[fruit]
        for stem, e in pl["expect"].items():
            r = man.get((fruit, stem))
            if r is None:
                ok_all = check("T1 %s/%s manifest 행 있음" % (fruit, stem), False)
                continue
            kept = not r["action"].startswith("excluded")
            ok = kept == e["kept"] and r["source"] == e["source"]
            for k in ("action", "reason", "image_source", "mask_source"):
                if k in e and r[k] != e[k]:
                    ok = False
            if "note_has" in e and e["note_has"] not in r["note"]:
                ok = False
            if not ok:
                ok_all = check("T1 %s/%s" % (fruit, stem), False,
                               "기대 %s · 실제 kept=%s source=%s action=%s reason=%s note=%s"
                               % (e, kept, r["source"], r["action"], r["reason"], r["note"][:60]))
            # 남긴 사진은 파일이 있어야 하고, 뺀 사진은 없어야 한다
            ip = os.path.join(out_dir, fruit, "images", stem + ".png")
            if os.path.exists(ip) != kept:
                ok_all = check("T1 %s/%s 파일 유무" % (fruit, stem), False)
        # 장수
        n_keep = sum(1 for s, e in pl["expect"].items() if e["kept"])
        n_file = len([x for x in os.listdir(os.path.join(out_dir, fruit, "images"))
                      if x.endswith(".png")])
        ok_all &= check("T1 %s 장수 %d" % (fruit, n_keep), n_file == n_keep,
                        "파일 %d장" % n_file)
        # masks_fixed 가 실제로 쓰였나
        s = pl["masks_fixed"][0]
        got = B.load_mask_bool(os.path.join(out_dir, fruit, "masks", s + ".png"))
        want = B.load_mask_bool(os.path.join(p["tool"], fruit, "masks_fixed", s + ".png"))
        ok_all &= check("T1 %s masks_fixed 반영" % fruit, bool((got == want).all()))
        # instances_fixed 가 원본 번호보다 먼저 쓰였나(있는 과일만)
        s = pl["inst_fixed"][0]
        ip = os.path.join(out_dir, fruit, "instances", s + ".png")
        if os.path.exists(ip):
            arr = B.read_u16(ip)
            m = B.load_mask_bool(os.path.join(out_dir, fruit, "masks", s + ".png"))
            ok_all &= check("T1 %s instances_fixed 우선·마스크로 자름" % fruit,
                            set(np.unique(arr).tolist()) <= {0, 7} and not ((arr > 0) & ~m).any())
            ok_all &= check("T1 %s manifest instances_source" % fruit,
                            man[(fruit, s)]["instances_source"] == "instances_fixed",
                            man[(fruit, s)]["instances_source"])
        # 상자: 남긴 사진 것만 나가고 사진마다 YOLO txt 가 있나
        bdir = os.path.join(out_dir, fruit, "boxes")
        jsons = {x[:-5] for x in os.listdir(bdir)
                 if x.endswith(".json") and not x.startswith("boxes_all")}
        txts = {x[:-4] for x in os.listdir(bdir) if x.endswith(".txt")}
        want = {st for (f2, st), r in man.items()
                if f2 == fruit and r["boxes_source"] != "none" and not r["action"].startswith("excluded")}
        ok_all &= check("T1 %s 상자 = 남긴 사진 것만 · json↔txt 1:1" % fruit,
                        jsons == want == txts, "json=%d want=%d txt=%d" % (len(jsons), len(want), len(txts)))
        ok_all &= check("T1 %s 툴 상자가 최우선" % fruit,
                        man[(fruit, pl["boxes_kept"][0])]["boxes_source"] == "tool",
                        man[(fruit, pl["boxes_kept"][0])]["boxes_source"])
    # session·split_group
    peach_sess = {r["session"] for k, r in man.items() if k[0] == "peach"}
    ok_all &= check("T1 복숭아 session 은 날짜-t번호",
                    all(re.fullmatch(r"\d{6}-t\d+", s) for s in peach_sess), str(peach_sess))
    grape = [r for k, r in man.items() if k[0] == "grape"]
    ok_all &= check("T1 포도 session 은 사진마다 하나(미확인)",
                    all(r["session"] == r["stem"] for r in grape))
    ok_all &= check("T1 사과 session 은 검수판 값 그대로",
                    man[("apple", plan["apple"]["keep"][0])]["session"]
                    == reviewed_cell("apple", plan["apple"]["keep"][0], "session"))
    return ok_all


def reviewed_cell(fruit, stem, col):
    with open(os.path.join(REV[fruit], fruit, "manifest.csv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["stem"] == stem:
                return r.get(col, "")
    return None


# ───────────────────────────── T5 툴 내보내기와 대조
def crosscheck(p, plan, out_dir):
    """export/export_dataset.py --confirmed-only 와 **사람이 확정한 사진에 한해** 같은 집합인가.

    툴 내보내기는 «확정 없는 사진은 전부 뺀다» 이고 우리 빌드는 «확정이 없으면 검수판 판정» 이라
    전체 집합은 애초에 다르다. 그래서 겹치는 자리 = **확정이 있는 사진**에서만 견준다.
    툴 코드는 data 폴더를 제 위치에서 찾으므로 모래상자에 코드 사본을 만들어 돌린다(실서버·실데이터 무변경).
    """
    copy_root = os.path.join(SAND, "toolcopy")
    if not os.path.exists(os.path.join(copy_root, "export", "export_dataset.py")):
        for sub in ("app", "export"):
            os.makedirs(os.path.join(copy_root, sub), exist_ok=True)
            for fn in os.listdir(os.path.join(TOOL_ROOT, sub)):
                if fn.endswith(".py") and not fn.startswith("_backup"):
                    shutil.copy2(os.path.join(TOOL_ROOT, sub, fn), os.path.join(copy_root, sub, fn))
        shutil.copytree(p["tool"], os.path.join(copy_root, "data"), dirs_exist_ok=True)
    man = read_manifest(os.path.join(out_dir, "manifest.csv"))
    ok_all = True
    for fruit in FRUITS:
        rev_root = p["rev916"] if REV[fruit].endswith("260916") else p["rev917"]
        out = os.path.join(SAND, "export_out", fruit)
        if not os.path.isdir(out):
            env = dict(os.environ, LABELTOOL_DATA_ROOT=rev_root)
            r = subprocess.run([PY, os.path.join(copy_root, "export", "export_dataset.py"),
                                "--fruit", fruit, "--out", out, "--confirmed-only", "--copy-images"],
                               capture_output=True, text=True, env=env)
            if r.returncode != 0:
                ok_all = check("T5 %s 툴 내보내기 실행" % fruit, False, r.stderr[-300:])
                continue
        theirs = {x[:-4] for x in os.listdir(os.path.join(out, "images")) if x.endswith(".png")}
        st = json.load(open(os.path.join(p["tool"], fruit, "status.json"), encoding="utf-8"))
        confirmed = {s for s, v in st.items() if isinstance(v.get("confirmed"), dict)}
        have = {x[:-4] for x in os.listdir(os.path.join(rev_root, fruit, "images"))}
        mine = {s for (f, s), r in man.items()
                if f == fruit and not r["action"].startswith("excluded")}
        ok_all &= check("T5 %s 확정된 사진에서 툴 내보내기와 같은 집합" % fruit,
                        (mine & confirmed & have) == (theirs & confirmed),
                        "우리 %s · 툴 %s" % (sorted(mine & confirmed & have), sorted(theirs & confirmed)))
    return ok_all


# ───────────────────────────── 팀원 산출물 모래상자
PSM = "/data/project/2026summer/platform/work/park_seongmoon"
CIH = "/data/project/2026summer/platform/work/choi_inhun"
LSH = "/data/project/2026summer/platform/work/im_seonghu"


def build_team_sandbox(p, plan):
    """팀원 폴더의 «작은 사본» — 진짜 파일 몇 개만 복사하고 나머지는 가짜로 만든다.

    ks[0:5] 는 박성문 gt 와 임성후 판이 **둘 다** 있게 해서 «최신(gt) 우선» 을 시험하고,
    ks[5:10] 은 임성후만 있게 해서 되넘김(lsh)을 시험한다.
    """
    for fruit in FRUITS:
        ks = plan[fruit]["keep"]
        # 박성문 gt_boxes (진짜 파일이 있는 과일만 — 블루베리는 원래 gt 가 없다)
        src = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes")
        if os.path.isdir(os.path.join(src, "json")):
            for sub in ("json", "yolo_labels"):
                os.makedirs(os.path.join(p["psm"], "bbox_outputs", fruit, "gt_boxes", sub), exist_ok=True)
            for s0 in ks[:5]:
                for sub, ext in (("json", ".json"), ("yolo_labels", ".txt")):
                    a = os.path.join(src, sub, s0 + ext)
                    if os.path.exists(a):
                        shutil.copy2(a, os.path.join(p["psm"], "bbox_outputs", fruit,
                                                     "gt_boxes", sub, s0 + ext))
        # 임성후 all/json (ks[0:10])
        src = os.path.join(LSH, "bbox_outputs", fruit, "all", "json")
        if os.path.isdir(src):
            d = os.path.join(p["lsh"], "bbox_outputs", fruit, "all", "json")
            os.makedirs(d, exist_ok=True)
            for s0 in ks[:10]:
                a = os.path.join(src, s0 + ".json")
                if os.path.exists(a):
                    shutil.copy2(a, os.path.join(d, s0 + ".json"))
    # 박성문 apple_check — 사과 ks[10]·ks[11] 에 가짜 판정
    ka = plan["apple"]["keep"]
    d = os.path.join(p["psm"], "apple_check")
    os.makedirs(d, exist_ok=True)
    cols = ["idx", "priority", "score", "stem", "subset", "fold_test", "inst_ids",
            "x0", "y0", "x1", "y1", "note", "verdict"]
    def wr(path, rows):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    row = lambda i, stem, v: dict(zip(cols, [i, "merge", "x", stem, "video", "1", "3",
                                             "0", "0", "1", "1", "메모", v]))
    wr(os.path.join(d, "review_list.csv"),
       [row(1, ka[10], "ok_one_apple"), row(2, ka[10], "duplicate_polygon"),
        row(3, ka[11], "ok_one_apple")])
    wr(os.path.join(d, "confirmed_errors.csv"), [row(2, ka[10], "duplicate_polygon")])
    # 최인훈 복숭아 중복 후보 + 의심 마스크
    kp = plan["peach"]["keep"]
    d = os.path.join(p["cih"], "dup_audit_260917", "peach")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "similar_pairs.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["a", "b", "dhash_ham", "phash_ham", "hist_dist"])
        w.writerow([kp[0] + ".png", kp[1] + ".png", 20, 25, 0.10])     # 버스트가 아닌 쌍 → pair_01
        w.writerow([kp[2] + ".png", kp[3] + ".png", 30, 40, 0.90])     # 문턱 밖 → 안 잡힘
    d = os.path.join(p["cih"], "mask_audit_260908")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "suspects.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["fruit", "mask", "fg_pixels", "total_pixels", "fg_ratio", "unique_nz", "reason"])
        w.writerow(["peach", kp[4] + ".png", 500, 2073600, 0.0002, 1, "bottom_5pct_ratio"])


def t_team(p, plan, out_dir):
    """T7~T10 — 팀원 산출물 반영."""
    man = read_manifest(os.path.join(out_dir, "manifest.csv"))
    ok = True
    for fruit in FRUITS:
        ks = plan[fruit]["keep"]
        bdir = os.path.join(out_dir, fruit, "boxes")
        want_psm = os.path.isdir(os.path.join(p["psm"], "bbox_outputs", fruit, "gt_boxes", "json"))
        if want_psm:
            ok &= check("T8 %s ks[0] 은 박성문 gt 우선" % fruit,
                        man[(fruit, ks[0])]["boxes_source"] == "psm_gt",
                        man[(fruit, ks[0])]["boxes_source"])
            # 박성문이 만든 YOLO txt 를 그대로 복사했나
            a = os.path.join(p["psm"], "bbox_outputs", fruit, "gt_boxes", "yolo_labels", ks[0] + ".txt")
            b = os.path.join(bdir, ks[0] + ".txt")
            if os.path.exists(a):
                ok &= check("T8 %s 박성문 YOLO txt 그대로" % fruit,
                            open(a, "rb").read() == open(b, "rb").read())
        if os.path.isdir(os.path.join(p["lsh"], "bbox_outputs", fruit, "all", "json")):
            src = "psm_gt" if want_psm else "lsh"
            ok &= check("T8 %s ks[7](임성후만 있는 사진) 상자 출처는 lsh" % fruit,
                        man[(fruit, ks[7])]["boxes_source"] == "lsh",
                        man[(fruit, ks[7])]["boxes_source"])
    ka = plan["apple"]["keep"]
    ok &= check("T9 사과 번호 판정이 칸에 들어감",
                "ok_one_apple=1" in man[("apple", ka[10])]["apple_check_verdict"]
                and "확정오류" in man[("apple", ka[10])]["apple_check_verdict"]
                and man[("apple", ka[10])]["verdict_source"] == "psm_review_list+confirmed_errors",
                man[("apple", ka[10])]["apple_check_verdict"])
    ok &= check("T9 판정 없는 사진의 verdict_source 는 none",
                man[("apple", ka[15])]["verdict_source"] == "none")
    kp = plan["peach"]["keep"]
    dup = {s: r["peach_dup_candidate"] for (f, s), r in man.items() if f == "peach" and r["peach_dup_candidate"]}
    ok &= check("T9 복숭아 중복 후보가 붙음", kp[0] in dup and kp[1] in dup and dup[kp[0]] == dup[kp[1]],
                str(list(dup.items())[:4]))
    ok &= check("T9 문턱 밖 쌍은 안 붙음", kp[2] not in dup and kp[3] not in dup)
    ok &= check("T9 중복 후보가 «제외» 로 새지 않음",
                all(not man[("peach", s)]["action"].startswith("excluded") for s in dup))
    ok &= check("T9 의심 마스크 사유가 붙음",
                man[("peach", kp[4])]["mask_audit_reason"] == "bottom_5pct_ratio",
                man[("peach", kp[4])]["mask_audit_reason"])
    empty = [(k, c) for k, r in man.items() for c in
             ("source", "image_source", "mask_source", "instances_source", "boxes_source", "verdict_source")
             if not r[c]]
    ok &= check("T10 출처 칸이 빈 행 0", not empty, str(empty[:3]))
    return ok


def t_yolo_same(p):
    """T12 — 내 YOLO 변환이 박성문이 만든 txt 와 **같은 숫자**인가(독립 대조)."""
    for fruit in FRUITS:
        d = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes")
        if not os.path.isdir(os.path.join(d, "json")):
            continue
        names = sorted(x for x in os.listdir(os.path.join(d, "json")) if x.endswith(".json"))[:3]
        for n in names:
            theirs = os.path.join(d, "yolo_labels", n[:-5] + ".txt")
            if not os.path.exists(theirs):
                continue
            mine = os.path.join(SAND, "yolo_check_%s_%s.txt" % (fruit, n[:-5]))
            B.yolo_from_detect_json(os.path.join(d, "json", n), mine)
            if open(mine, "rb").read() != open(theirs, "rb").read():
                return check("T12 %s/%s 박성문 YOLO txt 와 같은 숫자" % (fruit, n[:-5]), False)
    return check("T12 내 YOLO 변환 = 박성문 yolo_labels (표본 대조)", True)


# ───────────────────────────── main
def main():
    global RUN
    os.makedirs(SAND, exist_ok=True)
    os.makedirs(os.path.join(SAND, "out"), exist_ok=True)
    used = {int(m.group(1)) for m in
            (re.match(r"datasets_merged_260918_r(\d+)t", n) for n in os.listdir(os.path.join(SAND, "out")))
            if m}
    RUN = "r%d" % ((max(used) + 1) if used else 1)
    print("이번 시험 꼬리표: %s (지난 시험 폴더는 그대로 둡니다)" % RUN)
    print("모래상자 준비 중 … %s" % SAND)
    p, plan = build_sandbox()

    print("\nT1 기대 장수·source·reason")
    r = run_build(p, "t1")
    out_dir = os.path.join(p["out"], "datasets_merged_260918_%st1" % RUN)
    if not check("T1 빌드 성공(exit 0)", r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]):
        print(r.stdout[-3000:])
        return 1
    t1(p, plan, out_dir)
    probs = json.load(open(os.path.join(out_dir, "build_summary.json"), encoding="utf-8"))["problems"]
    check("T1 masks_fixed 없는 «수정함» 이 문제 목록에 적힘",
          sum(1 for x in probs if "masks_fixed 파일이 없습니다" in x) == len(FRUITS),
          str(probs[:4]))

    print("\nT2 멱등(두 번 돌려도 manifest 가 바이트까지 같다)")
    r2 = run_build(p, "t2")
    out2 = os.path.join(p["out"], "datasets_merged_260918_%st2" % RUN)
    same = (r2.returncode == 0 and
            open(os.path.join(out_dir, "manifest.csv"), "rb").read()
            == open(os.path.join(out2, "manifest.csv"), "rb").read())
    check("T2 통합 manifest 바이트 동일", same)
    check("T2 과일별 manifest 바이트 동일",
          all(open(os.path.join(out_dir, f, "manifest.csv"), "rb").read()
              == open(os.path.join(out2, f, "manifest.csv"), "rb").read() for f in FRUITS))
    def readme_body(d):
        """«직전 빌드와 견준» 절은 만들 때마다 달라지는 것이 맞으므로 빼고 견준다."""
        t = open(os.path.join(d, "README.md"), encoding="utf-8").read()
        t = t.replace(os.path.basename(d), "<폴더>")
        return t.split("## 직전 빌드와 견준")[0] + t.split("## 주의", 1)[-1]
    check("T2 README 도 같다(시각·직전빌드 절 빼고)", readme_body(out_dir) == readme_body(out2))

    print("\nT3 폴더가 이미 있으면 멈춘다")
    r3 = run_build(p, "t1")
    check("T3 exit 2 + 안내 문구", r3.returncode == 2 and "이미 있습니다" in r3.stdout,
          "%s / %s" % (r3.returncode, r3.stdout[-200:]))

    print("\nT4 검사가 걸리면 _INCOMPLETE")
    bad_dir = os.path.join(p["out"], "datasets_merged_260918_%st4" % RUN)
    orig_save = B.save_mask_255
    def bad_save(path, arr):                      # 0/128 짜리 마스크를 일부러 쓴다
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray((np.asarray(arr).astype(np.uint8)) * 128, mode="L").save(path)
    B.save_mask_255 = bad_save
    rc = B.main(["--date", "260918", "--suffix", RUN + "t4", "--out-root", p["out"],
                 "--tool-data", p["tool"], "--reviewed-260916", p["rev916"],
                 "--reviewed-260917", p["rev917"], "--original-root", p["orig"],
                 "--fruits", "peach"])
    B.save_mask_255 = orig_save
    check("T4 exit 1 + 폴더 이름에 _INCOMPLETE",
          rc == 1 and os.path.isdir(bad_dir + "_INCOMPLETE") and not os.path.isdir(bad_dir),
          "rc=%s" % rc)

    print("\nT5 툴 export_dataset.py --confirmed-only 와 대조(독립 증거)")
    crosscheck(p, plan, out_dir)

    print("\nT7 팀원 폴더가 통째로 없을 때")
    r7 = run_build(p, "t7", ["--psm-root", os.path.join(SAND, "없는폴더_psm"),
                             "--cih-root", os.path.join(SAND, "없는폴더_cih"),
                             "--lsh-root", os.path.join(SAND, "없는폴더_lsh")])
    out7 = os.path.join(p["out"], "datasets_merged_260918_%st7" % RUN)
    check("T7 exit 0 (멈추지 않음)", r7.returncode == 0, r7.stdout[-500:] + r7.stderr[-400:])
    if r7.returncode == 0:
        m7 = read_manifest(os.path.join(out7, "manifest.csv"))
        check("T7 상자 출처가 전부 none/tool",
              {r["boxes_source"] for r in m7.values()} <= {"none", "tool"},
              str({r["boxes_source"] for r in m7.values()}))
        check("T7 팀원 칸이 전부 빈칸·none",
              all(not r["apple_check_verdict"] and not r["peach_dup_candidate"]
                  and not r["mask_audit_reason"] and r["verdict_source"] == "none"
                  for r in m7.values()))
        reg = json.load(open(os.path.join(out7, "build_summary.json"), encoding="utf-8"))["input_registry"]
        check("T7 없는 입력이 등록표에 «없음» 으로 적힘",
              any(k.startswith("psm:") and not v["exists"] for k, v in reg.items()))

    print("\nT8~T10 팀원 산출물 반영")
    t_team(p, plan, out_dir)

    print("\nT11 직전 빌드와 견준 «바뀐 입력»")
    with open(os.path.join(p["cih"], "mask_audit_260908", "suspects.csv"), "a", encoding="utf-8") as f:
        f.write("peach,%s.png,400,2073600,0.0002,1,bottom_5pct_ratio\n" % plan["peach"]["keep"][5])
    r11 = run_build(p, "t11", ["--prev", os.path.join(out_dir, "build_summary.json")])
    out11 = os.path.join(p["out"], "datasets_merged_260918_%st11" % RUN)
    if check("T11 빌드 성공", r11.returncode == 0, r11.stdout[-400:]):
        ch = json.load(open(os.path.join(out11, "build_summary.json"), encoding="utf-8"))["input_changes"]
        check("T11 바뀐 입력을 잡아냄(suspects.csv 행 수)",
              any(k == "cih:mask_audit:suspects.csv" for k, _w, _a, _b in ch), str(ch[:3]))
        check("T11 README 에 «바뀐 입력» 표",
              "바뀐 입력" in open(os.path.join(out11, "README.md"), encoding="utf-8").read())

    print("\nT12 YOLO 변환 독립 대조")
    t_yolo_same(p)

    print("\nT6 진짜 입력으로 --dry-run")
    r6 = subprocess.run([PY, BUILD, "--dry-run"], capture_output=True, text=True)
    check("T6 dry-run 성공", r6.returncode == 0, r6.stderr[-400:])
    print(r6.stdout)
    with open(os.path.join(HERE, "dryrun_real_260918.txt"), "w", encoding="utf-8") as f:
        f.write(r6.stdout)

    print("\n" + ("전부 통과" if not fails else "실패 %d건:" % len(fails)))
    for x in fails:
        print("  - " + x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
