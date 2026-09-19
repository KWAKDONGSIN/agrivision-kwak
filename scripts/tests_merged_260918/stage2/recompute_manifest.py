# -*- coding: utf-8 -*-
"""2차 검수 — v2 manifest.csv 독립 재계산 (1차 스크립트를 import 하지 않는다).

검수판 manifest · 툴 status.json · 팀원 파일만 읽고, 계획서 §3 규칙을 내가 다시 구현해
datasets_merged_260918_v2/manifest.csv 와 행 단위로 대조한다.
"""
import csv, json, os, re, collections, sys

KDS = "/data/project/2026summer/kds0206"
W = "/data/project/2026summer/platform/work"
TOOL = os.path.join(W, "kwak_dongsin/260916_라벨링툴/data")
PSM, CIH, LSH = os.path.join(W, "park_seongmoon"), os.path.join(W, "choi_inhun"), os.path.join(W, "im_seonghu")
REV = {"peach": "datasets_reviewed_260916", "grape": "datasets_reviewed_260916",
       "apple": "datasets_reviewed_260917", "blueberry": "datasets_reviewed_260917"}
FRUITS = ["apple", "grape", "peach", "blueberry"]
V2 = os.path.join(KDS, "datasets_merged_260918_v2")
REAL = ("ok", "fixed", "flag", "exclude")


def jload(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def rows_of(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ── 사람 판정 (계획서 §3-2 를 내가 다시 읽고 구현)
def human(rec):
    if not isinstance(rec, dict):
        return None, None
    c = rec.get("confirmed")
    if isinstance(c, dict):
        return (c["status"], "human_confirmed") if c.get("status") in REAL else (None, "cleared")
    by = str(rec.get("by") or "")
    src = rec.get("src") if rec.get("src") in ("ai", "human") else ("ai" if by.startswith("AI") else "human")
    if src == "human":
        return (rec["status"], "human_legacy") if rec.get("status") in REAL else (None, "cleared")
    return None, None


# ── 팀원
def apple_check():
    per, conf = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for fn, bag in (("review_list.csv", per), ("confirmed_errors.csv", conf)):
        p = os.path.join(PSM, "apple_check", fn)
        if os.path.exists(p):
            for r in rows_of(p):
                s, v = (r.get("stem") or "").strip(), (r.get("verdict") or "").strip()
                if s and v:
                    bag[s][v] += 1
    out = {}
    for s in set(per) | set(conf):
        src = ("psm_review_list+confirmed_errors" if s in per and s in conf
               else "psm_review_list" if s in per else "psm_confirmed_errors")
        out[s] = src
    return out


def mask_audit():
    out = {}
    p = os.path.join(CIH, "mask_audit_260908", "suspects.csv")
    for r in rows_of(p) if os.path.exists(p) else []:
        m = (r.get("mask") or "")
        m = m[:-4] if m.endswith(".png") else m
        if m and (r.get("reason") or "").strip():
            out[(r.get("fruit", ""), m)] = r["reason"].strip()
    return out


BURST = re.compile(r"^(\d{6}-t\d+-of\d+)-\d+$")


def peach_dup():
    p = os.path.join(CIH, "dup_audit_260917", "peach", "similar_pairs.csv")
    burst, pairs = {}, []
    for r in rows_of(p) if os.path.exists(p) else []:
        a, b = [x[:-4] if x.endswith(".png") else x for x in (r["a"], r["b"])]
        for s in (a, b):
            m = BURST.match(s)
            if m:
                burst[s] = "burst_" + m.group(1).split("-")[-1]
        try:
            if int(r["dhash_ham"]) <= 22 and float(r["hist_dist"]) <= 0.17:
                pairs.append((a, b))
        except Exception:
            pass
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in pairs:
        if not (BURST.match(a) or BURST.match(b)):
            par[find(b)] = find(a)
    comp = collections.defaultdict(list)
    for x in list(par):
        comp[find(x)].append(x)
    out = {}
    for i, (_, xs) in enumerate(sorted(comp.items(), key=lambda kv: min(kv[1])), 1):
        if len(xs) >= 2:
            for s in xs:
                out[s] = "pair_%02d" % i
    out.update(burst)
    return out, burst


def boxes_idx(fruit):
    idx = {}
    d = os.path.join(LSH, "bbox_outputs", fruit, "all", "json")
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".json"):
                idx[fn[:-5]] = "lsh"
    d = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes", "json")
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".json"):
                idx[fn[:-5]] = "psm_gt"
    d = os.path.join(TOOL, fruit, "boxes")
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith(".json") and fn != "boxes_all.json":
                idx[fn[:-5]] = "tool"
    return idx


def main():
    AC, MA = apple_check(), mask_audit()
    PD, BURSTS = peach_dup()
    mine = {}
    for fruit in FRUITS:
        rev = os.path.join(KDS, REV[fruit], fruit)
        rrows = rows_of(os.path.join(rev, "manifest.csv"))
        st = jload(os.path.join(TOOL, fruit, "status.json"), {}) or {}
        bidx = boxes_idx(fruit)
        for r in rrows:
            s = r["stem"]
            hv, hsrc = human(st.get(s))
            if hsrc in ("human_confirmed", "human_legacy"):
                source = hsrc
            elif s in st:
                source = "ai"
            else:
                source = "reviewed"
            act, reason = r["action"], ""
            if hv == "ok":
                act = "keep"
            elif hv == "fixed":
                act = "mask_fixed"
            elif hv == "exclude":
                act, reason = "excluded_human", "human_exclude"
            elif hv == "flag":
                act, reason = "excluded_flag", "confirmed_flag"
            elif act == "excluded_duplicate":
                reason = "reviewed_duplicate"
            elif act == "excluded_not_grape":
                reason = "reviewed_not_grape"
            kept = not act.startswith("excluded")
            mine[(fruit, s)] = dict(
                action=act, reason=reason, source=source,
                session=r.get("session", "") if "session" in r else None,
                split_group=r.get("split_group", "") if "split_group" in r else None,
                boxes_source=(bidx.get(s, "none") if kept else "none"),
                has_boxes=("1" if kept and s in bidx else "0"),
                verdict_source=(AC.get(s, "none") if fruit == "apple" else "none"),
                peach_dup=(PD.get(s, "") if fruit == "peach" else ""),
                mask_audit=MA.get((fruit, s), ""),
            )

    v2 = {}
    for r in rows_of(os.path.join(V2, "manifest.csv")):
        v2[(r["fruit"], r["stem"])] = r

    print("내 재계산 행 %d · v2 manifest 행 %d" % (len(mine), len(v2)))
    print("키 차이:", len(set(mine) ^ set(v2)))
    diffs = collections.Counter()
    examples = collections.defaultdict(list)
    for k in sorted(set(mine) & set(v2), key=lambda t: (t[0], t[1])):
        a, b = mine[k], v2[k]
        for col, av in (("action", a["action"]), ("reason", a["reason"]), ("source", a["source"]),
                        ("boxes_source", a["boxes_source"]), ("has_boxes", a["has_boxes"]),
                        ("verdict_source", a["verdict_source"]),
                        ("peach_dup_candidate", a["peach_dup"]),
                        ("mask_audit_reason", a["mask_audit"])):
            bv = b[col]
            if col in ("boxes_source", "verdict_source") and not a["action"].startswith("excluded"):
                pass
            if a["action"].startswith("excluded") and col in ("boxes_source",):
                continue
            if av != bv:
                diffs[col] += 1
                if len(examples[col]) < 5:
                    examples[col].append((k, av, bv))
        for col in ("session", "split_group"):
            if a[col] is not None and a[col] != b[col]:
                diffs[col] += 1
                if len(examples[col]) < 5:
                    examples[col].append((k, a[col], b[col]))

    print("\n== 행 단위 대조(칸별 불일치 수) ==")
    if not diffs:
        print("  불일치 0")
    for c, n in diffs.most_common():
        print("  %-22s %d  예: %s" % (c, n, examples[c][:3]))

    # 장수
    print("\n== 장수 ==")
    for f in FRUITS:
        mk = sum(1 for (ff, s), v in mine.items() if ff == f and not v["action"].startswith("excluded"))
        vk = sum(1 for (ff, s), v in v2.items() if ff == f and not v["action"].startswith("excluded"))
        print("  %-10s 내 %5d · v2 %5d %s" % (f, mk, vk, "" if mk == vk else "  ← 다름"))
    # 복숭아 버스트 전수 확인
    peach_stems = [s for (f, s) in mine if f == "peach"]
    fs_burst = {s for s in peach_stems if BURST.match(s)}
    print("\n== 복숭아 버스트 ==")
    print("  파일명 규칙으로 센 버스트 장수 %d · similar_pairs 에서 잡힌 버스트 %d · 차집합 %s"
          % (len(fs_burst), len(BURSTS), sorted(fs_burst - set(BURSTS))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
