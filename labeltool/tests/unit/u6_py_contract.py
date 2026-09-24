# -*- coding: utf-8 -*-
"""u6 — **파이썬 쪽 계약**: 구조 사이클 2 가 서버를 쪼개도 옛 import 가 그대로 돌아야 한다.
작성: 2026-09-20 (구조 정리 사이클 2 · 사이클 1 3차 판정 §2 «호환 껍데기(높음)»)

왜 필요한가
  `app/boxes.py`·`instances.py`·`dupes.py`·`maskio.py` 를 이름으로 부르는 곳이 툴 **밖**에 있다 —
    · `semantic-segmentation/tools/build_merged_dataset.py:1480`  `import boxes` → `export_boxes_to`
    · `semantic-segmentation/tools/tests_merged_260918/counts/test_counts.py:158`  `import instances`
    · `export/export_dataset.py`  `from dupes import …` · `from maskio import …` · `from instances import …`
    · 지난 사이클 시험 수십 개
  `build_merged_dataset.py` 는 그 import 가 실패하면 **조용히 자체 구현으로 떨어졌다**(사이클 1
  2차 검수 §7-4). 그래서 «공개 이름이 하나라도 사라지면 여기서 먼저 실패한다» 를 못박는다.

무엇을 보나 (서버를 띄우지 않는다 — 모듈을 들여오기만 한다)
  ① 리팩터 **전** 코드에서 얼려 둔 공개 함수·상수 이름이 **전부 아직 있다**
     (얼린 파일 `tests/fixtures/py_contract_260920.json` — 만든 도구는
      `cycles/260920_structure/cycle_2/stage1/tools/contract_probe.py`)
  ② 그 상수들의 **값**이 같다(CLASSES·MAX_BOXES·MIN_SIDE·TEAM_BOX_DIRS·SEED_SOURCE·CC4 …)
  ③ 주소표(`server.app.url_map`)가 **37개 그대로**다 — 규칙·엔드포인트·메서드까지
  ④ 곁따라 들어온 «모듈 별칭»(np·os·ndimage 같은 것)이 바뀐 것은 **경고**로만 센다
     (그것은 계약이 아니라 import 정리의 결과다)
  ⑤ 껍데기가 정말 얇은가 — `app/*.py` 네 파일이 각각 30줄 이하
"""
import io
import json
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "app"))
import sandbox as L                                   # noqa: E402  tests/lib/sandbox.py

FIX = os.path.join(L.FIX, "py_contract_260920.json")
SHELLS = ("boxes.py", "instances.py", "dupes.py", "maskio.py")
SHELL_MAX = 30          # 껍데기 한 파일의 줄 수 상한(코드가 아니라 다시 내보내기만 있어야 한다)


def probe():
    """지금 코드에서 계약을 뽑는다 — `tools/contract_probe.py` 와 **같은 규칙**."""
    out = {"modules": {}, "aliases": {}, "values": {}, "routes": []}
    for name in ("maskio", "dupes", "boxes", "instances"):
        m = __import__(name)
        pub = [n for n in dir(m) if not n.startswith("_")]
        out["modules"][name] = sorted(n for n in pub
                                      if not isinstance(getattr(m, n), types.ModuleType))
        out["aliases"][name] = sorted(n for n in pub
                                      if isinstance(getattr(m, n), types.ModuleType))
    import boxes
    import dupes
    import instances
    out["values"] = {
        "boxes.CLASSES": boxes.CLASSES,
        "boxes.MAX_BOXES": boxes.MAX_BOXES,
        "boxes.MIN_SIDE": boxes.MIN_SIDE,
        "boxes.TEAM_CLS": boxes.TEAM_CLS,
        "boxes.TEAM_BOX_DIRS": [list(t) for t in boxes.TEAM_BOX_DIRS],
        "dupes.FRUITS": dupes.FRUITS,
        "dupes.DEFAULT_DATASET": dupes.DEFAULT_DATASET,
        "instances.CC4": instances.CC4,
        "instances.NO_NUM": instances.NO_NUM,
        "instances.SEED_SOURCE": instances.SEED_SOURCE,
        "instances.KIND_SOURCE": instances.KIND_SOURCE,
        "instances.SEED_DIRS_keys": sorted(instances.SEED_DIRS),
        "instances.ERROR_CSV_keys": sorted(instances.ERROR_CSV),
    }
    import server
    for r in server.app.url_map.iter_rules():
        out["routes"].append({"rule": str(r.rule), "endpoint": r.endpoint,
                              "methods": sorted(x for x in r.methods
                                                if x not in ("HEAD", "OPTIONS"))})
    out["routes"].sort(key=lambda d: (d["rule"], d["endpoint"]))
    return out


def main():
    if not os.path.exists(FIX):
        L.chk("u6-0 얼린 계약 파일이 있다 (%s)" % FIX, False,
              "없으면 `cycles/260920_structure/cycle_2/stage1/tools/contract_probe.py` 로 다시 뜨세요")
        return L.summary("u6_py_contract")
    want = json.load(io.open(FIX, encoding="utf-8"))
    got = probe()

    # ① 공개 이름
    for mod in sorted(want["modules"]):
        lost = [n for n in want["modules"][mod] if n not in got["modules"].get(mod, [])]
        L.chk("u6-1 %s — 얼려 둔 공개 이름 %d개가 전부 있다"
              % (mod, len(want["modules"][mod])), not lost, "사라진 이름: %s" % lost)
        new = [n for n in got["modules"].get(mod, []) if n not in want["modules"][mod]]
        if new:
            L.warn("u6-1b %s — 늘어난 공개 이름(더하는 것은 괜찮다)" % mod, new)

    # ② 상수 값
    for k in sorted(want["values"]):
        L.chk("u6-2 %s 값이 그대로다" % k, want["values"][k] == got["values"].get(k),
              "%r → %r" % (want["values"][k], got["values"].get(k)))

    # ③ 기존 주소 보존 + 사용자 승인한 읽기 전용 팀원 자료 주소 두 개.
    added = {("/api/team_review", "team_review", ("GET",)), ("/team_photo/grape/<stem>", "team_photo", ("GET",)),
             ("/old", "index_old", ("GET",)),   # 0923: 첫 화면을 그림판으로 바꾸고 옛 툴은 /old 로 옮김
             ("/api/sam", "api_sam", ("POST",)), ("/draft", "serve_draft", ("GET",))}   # 0923: 그림판 AI 도움
    L.chk("u6-3 기존%d개와 승인한 주소5개" % len(want["routes"]),
          len(want["routes"]) + len(added) == len(got["routes"]),
          "%d → %d" % (len(want["routes"]), len(got["routes"])))
    wr = {(r["rule"], r["endpoint"], tuple(r["methods"])) for r in want["routes"]}
    gr = {(r["rule"], r["endpoint"], tuple(r["methods"])) for r in got["routes"]}
    L.chk("u6-3b 사라진 주소가 없다", not (wr - gr), sorted(wr - gr))
    L.chk("u6-3c 추가는 승인한 주소5개뿐", gr - wr == added, sorted(gr - wr))

    # ④ 모듈 별칭은 경고만
    for mod in sorted(want.get("aliases") or {}):
        a, b = want["aliases"][mod], got["aliases"].get(mod, [])
        if a != b:
            L.warn("u6-4 %s — 모듈 별칭이 바뀌었다(계약 아님)" % mod,
                   "빠짐 %s · 더함 %s" % ([n for n in a if n not in b], [n for n in b if n not in a]))

    # ⑤ 껍데기는 얇아야 한다
    for fn in SHELLS:
        p = os.path.join(L.T, "app", fn)
        n = len(io.open(p, encoding="utf-8").read().splitlines())
        L.chk("u6-5 app/%s 는 %d줄 이하(코드 없이 다시 내보내기만)" % (fn, SHELL_MAX),
              n <= SHELL_MAX, "%d줄" % n)
    return L.summary("u6_py_contract")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
