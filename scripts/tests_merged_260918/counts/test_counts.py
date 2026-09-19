# -*- coding: utf-8 -*-
"""«개수 칸» 대조시험 — 2026-09-19 «개수 세기» 사이클1 (지시서 §1-4).

같은 규칙이 **세 곳에** 있다(일부러 그렇게 만들었다 — 통합 스크립트는 툴의 app/ 을 import 하지 않는다):
  ① 툴 화면   : `260916_라벨링툴/app/boxes.py human_count()`        (server.counts_of 가 부른다)
  ② 툴 내보내기: `260916_라벨링툴/export/export_dataset.py counts_rows()`  (counts.csv)
  ③ 통합       : `semantic-segmentation/tools/build_merged_dataset.py count_cells()`  (manifest.csv)
이 시험은 세 구현이 **갈라지지 않았는지**를 본다. 갈라지면 여기서 실패한다.

무엇을 보는가
  [가] 규칙 격자 — (상자 수 × 번호 수 × 상자 확정 × 번호 확정) 전수 조합을 ①과 ③에 넣어 대조
  [나] 진짜 자료 — 툴 `counts_rows()` 를 실제 data 로 돌려(읽기만) 그 줄을 ③에 넣어 대조
  [다] counts.csv 의 형식 — 칸 이름·개수·«사람 확정만» 걸러내기·빈칸과 0 의 구별·«나간 사진» 제한
  [라] 문서 — build_merged 의 MANIFEST_COLS 에 다섯 칸이 있고 README 설명이 붙어 있나

쓰기: 모래상자 `counts/sandbox/` 한 곳뿐. 원본·검수판·툴 data·팀원 폴더는 **읽기만** 한다.
돌리는 법:
    PY=/home/kds0206/.conda/envs/kwak/bin/python
    $PY tools/tests_merged_260918/counts/test_counts.py
"""
import csv
import io
import itertools
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox")
TOOLS = os.path.dirname(os.path.dirname(HERE))
TOOL = "/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴"
PY = sys.executable

sys.path.insert(0, TOOLS)
import build_merged_dataset as B                       # noqa: E402  (count_cells·MANIFEST_COLS)

sys.path.insert(0, os.path.join(TOOL, "app"))
sys.path.insert(0, os.path.join(TOOL, "export"))
from boxes import human_count                          # noqa: E402  ① 툴 화면의 규칙
import export_dataset as X                             # noqa: E402  ② 툴 counts.csv

fails = []
n_checks = [0]


def check(name, ok, msg=""):
    n_checks[0] += 1
    print(("  [통과] " if ok else "  [실패] ") + name + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(name + ((" — " + msg) if msg else ""))
    return ok


def merged_cells(nb, ni, cb, ci):
    """③ 통합 count_cells() 를 ①과 같은 모양((개수, 출처, 어긋남))으로 돌려준다."""
    row = B.count_cells({"n_boxes": "" if nb is None else str(nb),
                         "n_instances": "" if ni is None else str(ni),
                         "boxes_confirmed_status": cb or "-",
                         "instances_confirmed_status": ci or "-"})
    n = row["n_count_human"]
    return (None if n == "" else int(n),
            "" if row["count_source"] == "none" else row["count_source"],
            row["count_conflict"] == "1")


# ───────────────────────────────────────────── [가] 규칙 격자
def part_a():
    print("\n[가] 규칙 격자 — 툴 human_count() vs 통합 count_cells()")
    NS = [None, 0, 1, 15, 16, 204]
    CS = [None, "ok", "fixed", "flag", "exclude", "unreviewed"]
    bad = []
    n = 0
    for nb, ni, cb, ci in itertools.product(NS, NS, CS, CS):
        n += 1
        a = human_count(nb, ni, cb, ci)
        c = merged_cells(nb, ni, cb, ci)
        if a != c:
            bad.append((nb, ni, cb, ci, a, c))
    check("전수 조합 %d개가 두 구현에서 같다" % n, not bad,
          "다른 것 %d개, 예: %s" % (len(bad), bad[:3]))
    # 규칙 자체가 지시서 §1-2 와 같은지 (못 박아 둔다 — 다음 사이클이 말없이 뒤집지 못하게)
    # 🔴 2026-09-19 «개수 세기» 사이클1 **3차 전 총괄 결정 1**: 둘 다 확정인데 수가 다르면
    # **n_human 을 비운다**(`source="conflict"`). 전 기대값은 `(15, "instances", True)` —
    # 번호 쪽을 썼다. 사람이 16과 15 중 어느 쪽인지 고르지 않은 수를 논문 표(MAE·RMSE·R²)에
    # 넣으면 사후 정당화가 되고, README·help·풍선말의 «툴은 고르지 않습니다» 도 거짓이 된다.
    check("어긋나면 개수를 비운다(source=conflict) — 총괄 결정 1",
          human_count(16, 15, "fixed", "ok") == (None, "conflict", True))
    check("번호 확정이 상자 확정보다 먼저다(수가 같을 때 출처로 확인)",
          human_count(16, 16, "fixed", "ok") == (16, "instances", False))
    check("번호 확정이 없으면 상자 수를 쓴다",
          human_count(16, 15, "fixed", None) == (16, "boxes", False))
    check("flag·exclude 확정은 «확정» 으로 세지 않는다",
          human_count(16, 15, "flag", "exclude") == (None, "", False))
    check("확정은 있는데 셀 수가 없으면 없음이다",
          human_count(None, 15, "fixed", None) == (None, "", False))
    check("0개도 «값 없음» 이 아니다", human_count(0, None, "ok", None) == (0, "boxes", False))
    check("수가 같으면 어긋남이 아니다", human_count(16, 16, "ok", "ok")[2] is False)
    check("뺀 사진(«-»)은 확정으로 세지 않는다",
          merged_cells(None, None, "-", "-") == (None, "", False))


# ───────────────────────────────────────────── [나] 진짜 자료로 대조
def part_b():
    print("\n[나] 진짜 자료 — 툴 counts_rows() 의 줄을 통합 count_cells() 에 넣어 대조")
    tot = 0
    for fruit in ("peach", "grape", "apple", "blueberry"):
        try:
            rows, n_human = X.counts_rows(fruit, confirmed_only=False)
        except Exception as e:                          # noqa: BLE001
            check("[%s] counts_rows() 가 돌았다" % fruit, False, repr(e))
            continue
        st = X.read_status(fruit)
        bad = []
        for r in rows:
            d = dict(zip(X.COUNTS_COLS, r))
            s, nb, ni = d["stem"], d["n_boxes"], d["n_instances"]
            nh, src, cf = d["n_human"], d["human_source"], d["count_conflict"]
            rec = st.get(s, {})
            cb = X._conf(rec, "confirmed_boxes").get("status")
            ci = X._conf(rec, "confirmed_instances").get("status")
            want = merged_cells(None if nb == "" else int(nb),
                                None if ni == "" else int(ni), cb, ci)
            got = (None if nh == "" else int(nh), src, cf == "1")
            if want != got:
                bad.append((fruit, s, want, got))
        tot += len(rows)
        check("[%s] %d줄(사람 확정 개수 %d장)이 두 구현에서 같다" % (fruit, len(rows), n_human),
              not bad, "다른 것 %d개, 예: %s" % (len(bad), bad[:3]))
    check("대조한 줄이 0줄이 아니다", tot > 0, "0줄 — 툴 data 를 못 읽었을 수 있다")


# ───────────────────────────────────────────── [나2] 모래상자 — 확정이 있는 자료로 전 갈래
# [나] 는 진짜 data 를 읽지만 2026-09-19 지금 상자·번호 확정이 **한 장도 없다**(실측: 네 과일
# status.json 의 confirmed_boxes·confirmed_instances 가 0). 그래서 ok/fixed/어긋남 갈래가
# 한 번도 안 돌았다. 여기서는 가짜 툴 data 를 모래상자에 만들어 **counts_rows() 를 그대로**
# 돌린다(패치하는 것은 «어느 폴더를 읽나» 뿐이다 — 규칙 코드는 손대지 않는다).
CASES = [
    # stem,        상자 json 개수(None=파일 없음), 번호 캐시, 상자 확정, 번호 확정,
    #                                                기대 (n_human, source, conflict)
    ("c01_both_same",   16,   16,   "ok",      "ok",       (16,   "instances", False)),
    # 총괄 결정 1(2026-09-19): 어긋나면 비운다. 전 기대값 (15, "instances", True)
    ("c02_both_diff",   16,   15,   "fixed",   "ok",       (None, "conflict",  True)),
    ("c03_box_only",    16,   15,   "fixed",   None,       (16,   "boxes",     False)),
    ("c04_inst_only",   None, 15,   None,      "fixed",    (15,   "instances", False)),
    ("c05_none",        16,   15,   None,      None,       (None, "",          False)),
    ("c06_flag",        16,   15,   "flag",    "exclude",  (None, "",          False)),
    ("c07_zero_box",    0,    None, "ok",      None,       (0,    "boxes",     False)),
    ("c08_conf_nofile", None, None, "ok",      "ok",       (None, "",          False)),
    ("c09_inst_nocache", 16,  None, "ok",      "ok",       (16,   "boxes",     False)),
]


def part_b2():
    print("\n[나2] 모래상자 — 확정이 있는 자료로 ok·fixed·어긋남 갈래 전부")
    import json
    import shutil
    from PIL import Image
    import instances as INST
    sb = os.path.join(SAND, "tooldata")
    ds = os.path.join(SAND, "ds")
    shutil.rmtree(sb, ignore_errors=True)
    shutil.rmtree(ds, ignore_errors=True)
    os.makedirs(os.path.join(sb, "peach", "boxes"))
    os.makedirs(os.path.join(ds, "peach", "images"))
    st, cache = {}, {}
    for stem, nb, ni, cb, ci, _want in CASES:
        Image.new("RGB", (8, 8)).save(os.path.join(ds, "peach", "images", stem + ".png"))
        if nb is not None:
            json.dump({"stem": stem, "fruit": "peach", "width": 8, "height": 8,
                       "by": "시험", "at": "2026-09-19 00:00", "note": "",
                       "boxes": [{"id": i + 1, "cls": "fruit", "xyxy": [0, 0, 2, 2],
                                  "src": "human"} for i in range(nb)]},
                      io.open(os.path.join(sb, "peach", "boxes", stem + ".json"), "w",
                              encoding="utf-8"), ensure_ascii=False)
        rec = {"status": "ok", "by": "AI 3회 검수", "at": "2026-09-19 00:00", "note": ""}
        if cb:
            rec["confirmed_boxes"] = {"status": cb, "by": "곽동신",
                                      "at": "2026-09-19 01:00", "note": ""}
        if ci:
            rec["confirmed_instances"] = {"status": ci, "by": "곽동신",
                                          "at": "2026-09-19 01:05", "note": ""}
        st[stem] = rec
        if ni is not None:
            cache[stem] = ni
    json.dump(st, io.open(os.path.join(sb, "peach", "status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)

    # 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**: `INST.CACHE_DIR` 도 모래상자로 돌린다.
    #   까닭 — `cached_counts`·`count_one` 만 바꿔 끼우면 그 안의 `count_now()` 가 살아 있어서
    #   `save_counts()` 가 **진짜 공용 캐시**(`app/cache/instance_counts/peach.json`)에 시험용
    #   이름(`c01_both_same` 등 5개)을 적었다(실측 2026-09-19 19:22·20:24 두 번 재현).
    #   시험은 공용 자리에 한 글자도 쓰면 안 된다. `cache_file()` 이 이 전역을 보므로 한 줄로 끝난다.
    keep = (X.DATA_DIR, X.DUP.dataset_for, INST.cached_counts, INST.count_one, X.read_status,
            INST.CACHE_DIR)
    try:
        INST.CACHE_DIR = os.path.join(sb, "_cache_시험전용")
        X.DATA_DIR = sb
        X.DUP.dataset_for = lambda f: ds
        X.read_status = lambda f: json.load(io.open(os.path.join(sb, f, "status.json"),
                                                   encoding="utf-8"))
        INST.cached_counts = lambda f: dict(cache)
        # 캐시에 없으면 «셀 수 없음» — c08·c09 가 그 갈래다(툴은 NO_NUM=-1 을 그렇게 다룬다)
        INST.count_one = lambda f, s: cache.get(s, INST.NO_NUM)
        rows, n_human = X.counts_rows("peach", confirmed_only=False)
        conf, _ = X.counts_rows("peach", confirmed_only=True)
    finally:
        (X.DATA_DIR, X.DUP.dataset_for, INST.cached_counts, INST.count_one, X.read_status,
         INST.CACHE_DIR) = keep

    by = {r[0]: r for r in rows}
    check("모래상자 %d장이 다 나왔다" % len(CASES), len(rows) == len(CASES), str(sorted(by)))
    nh_expect = 0
    for stem, nb, ni, cb, ci, want in CASES:
        r = by.get(stem)
        if not r:
            check("[%s] 줄이 있다" % stem, False)
            continue
        d = dict(zip(X.COUNTS_COLS, r))
        got = (None if d["n_human"] == "" else int(d["n_human"]),
               d["human_source"], d["count_conflict"] == "1")
        check("[%s] counts.csv 값이 기대와 같다" % stem, got == want,
              "기대 %s · 나온 것 %s (n_boxes=%r n_instances=%r)"
              % (want, got, d["n_boxes"], d["n_instances"]))
        check("[%s] 통합 count_cells() 도 같다" % stem,
              merged_cells(None if d["n_boxes"] == "" else int(d["n_boxes"]),
                           None if d["n_instances"] == "" else int(d["n_instances"]),
                           cb, ci) == got)
        if want[0] is not None:
            nh_expect += 1
            src_key = "confirmed_instances" if want[1] == "instances" else "confirmed_boxes"
            check("[%s] confirmed_by·at 이 그 개수를 낳은 확정의 것이다" % stem,
                  d["confirmed_by"] == "곽동신" and d["confirmed_at"] == st[stem][src_key]["at"],
                  "by=%r at=%r" % (d["confirmed_by"], d["confirmed_at"]))
    check("«사람 확정만» 이 %d장만 낸다" % nh_expect, len(conf) == nh_expect == n_human,
          "확정만 %d · n_human %d · 기대 %d" % (len(conf), n_human, nh_expect))
    ib = X.COUNTS_COLS.index("n_boxes")
    check("상자 0개 저장분은 «0» 이고 빈칸이 아니다", by["c07_zero_box"][ib] == "0",
          repr(by["c07_zero_box"][ib]))
    check("상자 파일이 없으면 빈칸이다", by["c04_inst_only"][ib] == "",
          repr(by["c04_inst_only"][ib]))
    ig = X.COUNTS_COLS.index("gt_source")
    check("정답이 없는 사진은 gt_source 가 «-» 다", by["c01_both_same"][ig] == "-",
          repr(by["c01_both_same"][ig]))


# ───────────────────────────────────────────── [다] counts.csv 의 형식
def part_c():
    print("\n[다] counts.csv — 칸·«사람 확정만» 걸러내기")
    check("칸 이름이 지시서 §1-3 그대로다",
          X.COUNTS_COLS == ["stem", "n_boxes", "n_instances", "n_team_park", "n_team_im",
                            "n_gt", "gt_source",            # 0919 사이클2 논문대조 ②
                            "n_human", "human_source", "count_conflict",
                            "confirmed_by", "confirmed_at"],
          str(X.COUNTS_COLS))
    fruit = "peach"
    allrows, n_human = X.counts_rows(fruit, confirmed_only=False)
    conf, _ = X.counts_rows(fruit, confirmed_only=True)
    ih = X.COUNTS_COLS.index("n_human")       # 0919 3차 전: r[5] 로 굳어 있었다(n_gt 칸이 늘면서 어긋남)
    check("«사람 확정만» 은 n_human 이 있는 줄만이다(%d ⊂ %d)" % (len(conf), len(allrows)),
          len(conf) == n_human and all(r[ih] != "" for r in conf),
          "확정만 %d · n_human %d" % (len(conf), n_human))
    # 🔴 총괄 결정 2(2026-09-19): counts.csv 는 «그 job 이 나간 사진» 만 담는다
    two = {r[0] for r in allrows[:2]}
    lim, _ = X.counts_rows(fruit, confirmed_only=False, only=two)
    check("only= 를 주면 그 사진들만 낸다(총괄 결정 2 — «나간 사진» 으로 제한)",
          {r[0] for r in lim} == two and len(lim) == len(two), str(len(lim)))
    check("«AI 제안 포함» 은 빈칸을 허용한다",
          len(allrows) >= len(conf) and all(len(r) == len(X.COUNTS_COLS) for r in allrows))
    ib = X.COUNTS_COLS.index("n_boxes")
    check("빈칸과 0 을 구별한다(빈칸 = 파일 없음 · 0 = 열매 없음)",
          all(r[ib] in ("",) or r[ib].isdigit() for r in allrows))
    # 0919 사이클2 논문대조 ② — 정답 개수(MAE·RMSE·R² 의 정답 쪽)
    ig, igs = X.COUNTS_COLS.index("n_gt"), X.COUNTS_COLS.index("gt_source")
    have = [r for r in allrows if r[ig] != ""]
    check("복숭아 정답 개수가 채워졌다(%d/%d장)" % (len(have), len(allrows)),
          len(have) == len(allrows) and all(r[igs] == "psm_gt_boxes" for r in have),
          "채워진 장수 %d · 출처 %s" % (len(have), sorted({r[igs] for r in allrows})))
    tot = sum(int(r[ig]) for r in have)
    check("복숭아 정답 합계가 박성문 표와 같다(977알)", tot == 977, "합계 %d" % tot)
    bl, _ = X.counts_rows("blueberry", confirmed_only=False)
    check("블루베리는 정답 상자가 없어 빈칸·«-» 다",
          all(r[ig] == "" and r[igs] == "-" for r in bl),
          str(sorted({(r[ig] == "", r[igs]) for r in bl})))
    os.makedirs(SAND, exist_ok=True)
    n = X.write_counts_csv(fruit, SAND, SimpleNamespace(confirmed_only=True))
    p = os.path.join(SAND, "counts.csv")
    got = list(csv.reader(io.open(p, encoding="utf-8")))
    check("파일 머리줄이 칸 이름과 같다", got and got[0] == X.COUNTS_COLS, str(got[:1]))
    check("파일 줄 수가 돌려준 값과 같다(%d)" % n, len(got) - 1 == n,
          "파일 %d · 반환 %d" % (len(got) - 1, n))


# ───────────────────────────────────────────── [라] 통합 manifest·README
def part_d():
    print("\n[라] 통합 manifest 의 칸과 README 설명")
    want = ["n_boxes", "n_instances", "n_count_human", "count_source", "count_conflict",
            "n_gt"]                                     # 0919 사이클2 논문대조 ②
    check("MANIFEST_COLS 에 다섯 칸이 다 있다", all(c in B.MANIFEST_COLS for c in want),
          str([c for c in want if c not in B.MANIFEST_COLS]))
    check("여섯 칸이 맨 뒤에 붙어 있다(앞 칸 순서를 건드리지 않았다)",
          B.MANIFEST_COLS[-6:] == want, str(B.MANIFEST_COLS[-6:]))
    # 두 구현이 **같은 파일**을 같은 법으로 세는가
    gp = B.gt_counts("/data/project/2026summer/platform/work/park_seongmoon", "peach")
    gx = X.gt_counts("peach")
    check("정답 개수를 두 구현이 같게 센다(복숭아 %d장)" % len(gp), gp == gx and len(gp) > 0,
          "통합 %d장 · 툴 %d장" % (len(gp), len(gx)))
    check("블루베리는 두 구현 모두 빈 딕셔너리다",
          B.gt_counts("/data/project/2026summer/platform/work/park_seongmoon", "blueberry") == {}
          and X.gt_counts("blueberry") == {})
    src = io.open(os.path.join(TOOLS, "build_merged_dataset.py"), encoding="utf-8").read()
    check("README 생성부에 «개수 칸» 절이 있다", "### 개수 칸 (2026-09-19 부터)" in src)
    check("뺀 사진은 «-» 로 적는다는 코드가 있다",
          'row["n_boxes"] = row["n_instances"] = row["n_count_human"] = "-"' in src)
    check("n_instances 는 «나간 파일» 을 센다", 'str(int(ids_of(cut).size))' in src)
    check("뺀 사진에도 n_gt 는 남긴다(정답은 나간 파일과 무관)",
          '# `n_gt` 는 덮지 않는다' in src)
    check("README 생성부에 n_gt 설명이 있다", '| `n_gt` | **정답 개수**' in src)
    check("count_cells 를 나간 파일을 센 뒤에 부른다",
          "for j in jobs:\n        count_cells(row_of[j[\"stem\"]])" in src)


def main():
    print("개수 칸 대조시험 — 툴 %s" % TOOL)
    part_a()
    part_b()
    part_b2()
    part_c()
    part_d()
    print("\n통과 %d / 실패 %d" % (n_checks[0] - len(fails), len(fails)))
    for f in fails:
        print("  - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
