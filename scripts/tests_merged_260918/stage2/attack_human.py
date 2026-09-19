# -*- coding: utf-8 -*-
"""2차 검수 §2 — «사람 확정» 시나리오 공격. 입력은 전부 모래상자 사본(실자료 무변경)."""
import csv, json, os, shutil, subprocess, sys, collections
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox", "human")
KDS = "/data/project/2026summer/kds0206"
BUILD = "/data/project/2026summer/kds0206/semantic-segmentation/tools/build_merged_dataset.py"
PY = sys.executable
REV917 = os.path.join(KDS, "datasets_reviewed_260917")
ORIG = os.path.join(KDS, "datasets_resized_2mp")
fails = []


def check(n, ok, msg=""):
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n + (" — " + msg if msg else ""))


def build_sand():
    if os.path.exists(SAND):
        shutil.rmtree(SAND)
    rows = list(csv.DictReader(open(os.path.join(REV917, "apple", "manifest.csv"), encoding="utf-8")))
    keep = [r for r in rows if not r["action"].startswith("excluded")][:14]
    # 같은 split_group 안에 «대표(남김)» 와 «제외» 가 같이 있는 묶음을 고른다(되살림 시나리오용)
    bygrp = collections.defaultdict(list)
    for r in rows:
        bygrp[r["split_group"]].append(r)
    pair_grp = next(g for g, rs in bygrp.items()
                    if any(x["action"] == "excluded_duplicate" for x in rs)
                    and any(not x["action"].startswith("excluded") for x in rs) and len(rs) >= 2)
    grp_rows = bygrp[pair_grp]
    drop = [r for r in rows if r["action"] == "excluded_duplicate"][:8]
    sel, seen = [], set()
    for r in keep + grp_rows + drop:
        if r["stem"] not in seen:
            seen.add(r["stem"]); sel.append(r)
    rd = os.path.join(SAND, "rev917", "apple")
    os.makedirs(os.path.join(rd, "images")); os.makedirs(os.path.join(rd, "masks"))
    od = os.path.join(SAND, "orig", "apple")
    os.makedirs(os.path.join(od, "images")); os.makedirs(os.path.join(od, "masks"))
    for r in sel:
        s = r["stem"]
        for sub in ("images", "masks"):
            a = os.path.join(REV917, "apple", sub, s + ".png")
            if os.path.exists(a):
                shutil.copy2(a, os.path.join(rd, sub, s + ".png"))
            b = os.path.join(ORIG, "apple", sub, s + ".png")
            if os.path.exists(b):
                shutil.copy2(b, os.path.join(od, sub, s + ".png"))
    with open(os.path.join(rd, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(sel)
    return sel, pair_grp, grp_rows


sel, pair_grp, grp_rows = build_sand()
kept = [r["stem"] for r in sel if not r["action"].startswith("excluded")]
dropped = [r["stem"] for r in sel if r["action"].startswith("excluded")]
rep = [r["stem"] for r in grp_rows if not r["action"].startswith("excluded")][0]
dupmate = [r["stem"] for r in grp_rows if r["action"] == "excluded_duplicate"][0]
print("모래상자 사과 %d장 (남김 %d · 제외 %d) · 되살림 묶음 %s (대표 %s ↔ 중복 %s)"
      % (len(sel), len(kept), len(dropped), pair_grp, rep, dupmate))

H = "곽동신"
AI = "AI 3회 검수(Opus5→Opus5→Fable5.1)"
status = {}
cases = {}


def put(stem, rec, label):
    status[stem] = rec
    cases[label] = stem


put(kept[0], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "ok", "by": H, "at": "2"}}, "confirmed_ok")
put(kept[1], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "fixed", "by": H, "at": "2"}}, "confirmed_fixed_no_file")
put(kept[2], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "flag", "by": H, "at": "2"}}, "confirmed_flag")
put(kept[3], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "exclude", "by": H, "at": "2"}}, "confirmed_exclude")
put(kept[4], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "unreviewed", "by": H, "at": "2"}}, "confirmed_unreviewed")
put(kept[5], {"status": "exclude", "by": H, "at": "1"}, "legacy_human_exclude")
put(kept[6], {"status": "unreviewed", "by": H, "at": "1"}, "human_cleared")
put(kept[7], {"status": "flag", "by": AI, "at": "1", "prev": {"status": "exclude", "by": AI}}, "prev_only")
put(kept[8], {"status": "exclude", "by": "AI 3회 검수", "src": "human", "at": "1"}, "by_AI_but_src_human")
put(kept[9], {"status": "exclude", "by": H, "src": "ai", "at": "1"}, "by_human_but_src_ai")
put(kept[10], {"status": "fixed", "by": H, "at": "1"}, "legacy_fixed_no_file")
put(dropped[0], {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "ok", "by": H, "at": "2"}}, "revive_confirmed_ok")
put(dupmate, {"status": "ok", "by": AI, "at": "1", "confirmed": {"status": "ok", "by": H, "at": "2"}}, "revive_dupmate")
put(dropped[1], {"status": "exclude", "by": AI, "at": "1", "confirmed": {"status": "fixed", "by": H, "at": "2"}}, "revive_fixed_no_file")

td = os.path.join(SAND, "tool", "apple")
os.makedirs(os.path.join(td, "masks_fixed"))
json.dump(status, open(os.path.join(td, "status.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

out = os.path.join(SAND, "out")
os.makedirs(out)
r = subprocess.run([PY, BUILD, "--fruits", "apple", "--out-root", out, "--date", "260918",
                    "--suffix", "human", "--no-prev",
                    "--reviewed-260917", os.path.join(SAND, "rev917"),
                    "--original-root", os.path.join(SAND, "orig"),
                    "--tool-data", os.path.join(SAND, "tool")], capture_output=True, text=True)
print("\n빌드 exit=%d" % r.returncode)
print(r.stdout[-1500:])
od = os.path.join(out, "datasets_merged_260918_human")
if not os.path.isdir(od):
    od += "_INCOMPLETE"
M = {x["stem"]: x for x in csv.DictReader(open(os.path.join(od, "manifest.csv"), encoding="utf-8"))}

exp = {
    "confirmed_ok": ("keep", "human_confirmed", ""),
    "confirmed_fixed_no_file": ("mask_fixed", "human_confirmed", ""),
    "confirmed_flag": ("excluded_flag", "human_confirmed", "confirmed_flag"),
    "confirmed_exclude": ("excluded_human", "human_confirmed", "human_exclude"),
    "confirmed_unreviewed": (None, "ai", ""),
    "legacy_human_exclude": ("excluded_human", "human_legacy", "human_exclude"),
    "human_cleared": (None, "ai", ""),
    "prev_only": (None, "ai", ""),
    "by_AI_but_src_human": ("excluded_human", "human_legacy", "human_exclude"),
    "by_human_but_src_ai": (None, "ai", ""),
    "legacy_fixed_no_file": ("mask_fixed", "human_legacy", ""),
    "revive_confirmed_ok": ("keep", "human_confirmed", ""),
    "revive_dupmate": ("keep", "human_confirmed", ""),
    "revive_fixed_no_file": ("mask_fixed", "human_confirmed", ""),
}
print("\n== 시나리오별 결과 ==")
for label, stem in cases.items():
    row = M[stem]
    ea, es, er = exp[label]
    ok = (ea is None or row["action"] == ea) and row["source"] == es and (er == "" or row["reason"] == er)
    check("%-24s action=%-16s source=%-15s reason=%-14s" % (label, row["action"], row["source"], row["reason"] or "-"),
          ok, "기대 action=%s source=%s reason=%s" % (ea, es, er))

print("\n== 되살림이 «중복 두 장 동시 생존» 을 만드나 ==")
alive = [s for s in (rep, dupmate) if not M[s]["action"].startswith("excluded")]
print("  묶음 %s 의 대표 %s(action=%s, split_group=%s) · 중복 %s(action=%s, split_group=%s)"
      % (pair_grp, rep, M[rep]["action"], M[rep]["split_group"], dupmate, M[dupmate]["action"], M[dupmate]["split_group"]))
check("되살아난 중복과 대표가 같은 split_group(누수 없음)", M[rep]["split_group"] == M[dupmate]["split_group"],
      "%s vs %s" % (M[rep]["split_group"], M[dupmate]["split_group"]))
print("  → 같은 묶음 안에 %d장이 동시에 남습니다(의도인가? 설계 판단)" % len(alive))

print("\n== masks_fixed 파일이 없는 «수정함» ==")
prob = json.load(open(os.path.join(od, "build_summary.json"), encoding="utf-8"))["problems"]
print("  problems %d건:" % len(prob))
for p in prob:
    print("    - " + p)
check("masks_fixed 없음이 문제 목록에 적힘", any("masks_fixed" in p for p in prob))
for label in ("confirmed_fixed_no_file", "legacy_fixed_no_file", "revive_fixed_no_file"):
    s = cases[label]
    check("%s: mask_source 가 원본으로 되돌아감" % label, M[s]["mask_source"] != "masks_fixed",
          M[s]["mask_source"])
    check("%s: note 에 경고" % label, "masks_fixed 파일 없음" in M[s]["note"], M[s]["note"][:80])

print("\n== 되살린 사진의 파일이 실제로 나왔나 ==")
for label in ("revive_confirmed_ok", "revive_dupmate", "revive_fixed_no_file"):
    s = cases[label]
    check("%s 이미지·마스크 존재" % label,
          os.path.exists(os.path.join(od, "apple", "images", s + ".png"))
          and os.path.exists(os.path.join(od, "apple", "masks", s + ".png")))
    check("%s image_source 기록" % label, M[s]["image_source"] in ("reviewed_260917", "resized_2mp"),
          M[s]["image_source"])

print("\n" + ("전부 통과" if not fails else "실패 %d건:" % len(fails)))
for x in fails:
    print("  - " + x)
sys.exit(1 if fails else 0)
