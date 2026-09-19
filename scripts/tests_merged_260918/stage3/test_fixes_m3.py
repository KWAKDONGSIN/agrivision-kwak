# -*- coding: utf-8 -*-
"""3차 소수정(D1·D2·D3·D4·D9) 회귀시험 — 고치기 전에는 실패하고, 고친 뒤에는 통과해야 한다.

고치기 전 판으로 돌리려면:
    BUILD_PY=/…/tools/_backup_260918_m3_build_merged_dataset.py $PY stage3/test_fixes_m3.py

모래상자(`stage3/sandbox/`) 안에서만 만듭니다. 검수판·원본·툴 data·팀원 폴더는 **읽기만** 합니다.
"""
import csv, io, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox")
TOOLS = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("BUILD_PY", os.path.join(TOOLS, "build_merged_dataset.py"))
KDS = "/data/project/2026summer/kds0206"
REV917 = os.path.join(KDS, "datasets_reviewed_260917")
# 🔴 2026-09-20 구조 사이클 2(시험 위생): 시험이 «지금» 의 공용 판정을 읽으면 사람이 툴에서
#   한 장을 확정할 때마다 손으로 적어 둔 숫자가 어긋난다(09-19 22:55 실측 977→975).
#   `MERGED_TOOL_DATA` 가 있으면 **얼려 둔 툴 자료**를 쓴다(`tests/merged/run_merged.sh` 가 만든다).
#   변수를 주지 않으면 예전과 한 글자도 다르지 않다(실제 빌드는 늘 지금 자료를 본다).
TOOLDATA = (os.environ.get("MERGED_TOOL_DATA", "").strip()
            or "/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/data")
PY = sys.executable
fails = []
print("시험 대상 스크립트: %s" % BUILD)


def check(n, ok, msg=""):
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n)


def rd(p):
    return io.open(p, encoding="utf-8").read()


def run(args):
    return subprocess.run([PY, BUILD] + args, capture_output=True, text=True)


# ─────────────────────────────────────────────────────────────── 준비 ①: 미니 사과 모래상자
# 검수판 사과에서 «남긴 2장 + 검수판이 뺀 중복 1장» 만 뽑아 만든다(1.4GB 를 다 복사하지 않으려고).
rev = os.path.join(SAND, "rev917", "apple")
shutil.rmtree(os.path.join(SAND, "rev917"), ignore_errors=True)
os.makedirs(os.path.join(rev, "images"))
os.makedirs(os.path.join(rev, "masks"))
src_rows = list(csv.DictReader(io.open(os.path.join(REV917, "apple", "manifest.csv"), encoding="utf-8")))
keep = [r for r in src_rows if r["action"] == "keep"][:2]
dup = [r for r in src_rows if r["action"] == "excluded_duplicate"][:1]
rows = keep + dup
with io.open(os.path.join(rev, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(src_rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
for r in keep:                                   # 뺀 사진은 검수판에 파일이 없다(원본에서 되살아난다)
    for sub in ("images", "masks"):
        shutil.copy2(os.path.join(REV917, "apple", sub, r["stem"] + ".png"),
                     os.path.join(rev, sub, r["stem"] + ".png"))
tool_a = os.path.join(SAND, "tool", "apple")
shutil.rmtree(os.path.join(SAND, "tool"), ignore_errors=True)
os.makedirs(tool_a)
# 확정 칸 없이 «사람» 이 누른 판정 = D2 가 이름을 바꾼 바로 그 경우.
json.dump({dup[0]["stem"]: {"status": "ok", "by": "곽동신", "at": "2026-09-18 18:00",
                            "note": "이 장도 쓰자"}},
          io.open(os.path.join(tool_a, "status.json"), "w", encoding="utf-8"), ensure_ascii=False)

out = os.path.join(SAND, "out")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)

print("\nM3-A 미니 사과 빌드 (D2 이름 · D1 되살린 중복 집계 · D9 영문 토큰)")
rA = run(["--fruits", "apple", "--out-root", out, "--date", "260918", "--suffix", "a",
          "--reviewed-260917", os.path.join(SAND, "rev917"),
          "--tool-data", os.path.join(SAND, "tool"), "--no-prev"])
dA = os.path.join(out, "datasets_merged_260918_a")
check("M3-A0 빌드가 통과(exit 0)", rA.returncode == 0, (rA.stdout + rA.stderr)[-600:])
if rA.returncode == 0:
    M = {r["stem"]: r for r in csv.DictReader(io.open(os.path.join(dA, "manifest.csv"), encoding="utf-8"))}
    man_txt = rd(os.path.join(dA, "manifest.csv"))
    rme = rd(os.path.join(dA, "README.md"))
    row = M[dup[0]["stem"]]

    # ── D2
    check("D2-a 확정 없이 사람이 누른 판정의 source 가 human_unconfirmed",
          row["source"] == "human_unconfirmed", row["source"])
    check("D2-b manifest 에 옛 이름 human_legacy 가 남아 있지 않다",
          "human_legacy" not in man_txt, "manifest 에 human_legacy 가 있다")
    check("D2-c README 의 값 표가 human_unconfirmed 로 바뀌었다",
          "`human_unconfirmed`" in rme and "| `human_legacy` |" not in rme, "README")

    # ── D1 (되살린 중복은 대표와 함께 그대로 남기고 «세기만» 한다)
    check("D1-a 사람이 되살린 중복이 남아 있다(action=keep)", row["action"] == "keep", row["action"])
    check("D1-b note 에 «되살림» 이 적힌다", "되살림" in row["note"], row["note"])
    check("D1-c README 에 «사람이 되살린 중복 N장» 줄이 있다",
          "사람이 되살린 중복** 1장" in rme,
          [l for l in rme.splitlines() if "되살린" in l][:2])
    bs = json.load(io.open(os.path.join(dA, "build_summary.json"), encoding="utf-8"))
    check("D1-d build_summary 의 counts 에 n_revived 가 있다",
          bs["counts"]["apple"].get("n_revived") == 1, str(bs["counts"]["apple"].get("n_revived")))

    # ── D9
    vals = {r["instances_source"] for r in M.values()}
    check("D9-a instances_source 값이 전부 ASCII(영문 토큰)",
          all(v.isascii() for v in vals), str(vals))
    check("D9-b 사과 원본 번호 마스크가 reviewed_number_mask 로 적힌다",
          "reviewed_number_mask" in vals, str(vals))
    check("D9-c README 에 instances_source 값 사전이 있다",
          "instances_source` 값 사전" in rme and "| `detect_seed` |" in rme, "README")

# ─────────────────────────────────────────────────────────────── D3
print("\nM3-B 직전 빌드에 있던 입력이 사라지면 멈추는가 (D3)")
prev = os.path.join(SAND, "prev")
shutil.rmtree(prev, ignore_errors=True)
g = os.path.join(prev, "datasets_merged_260918_prev")
os.makedirs(g)
json.dump({"built_at": "2026-09-18 10:00:00", "inputs": {},
           "input_registry": {"cih:mask_audit:suspects.csv":
                              {"path": "…/choi_inhun/mask_audit_260908/suspects.csv",
                               "exists": True, "kind": "file", "sha256": "0" * 64, "n_rows": 10}}},
          io.open(os.path.join(g, "build_summary.json"), "w", encoding="utf-8"))
gone = ["--fruits", "peach", "--out-root", prev, "--date", "260918", "--dry-run",
        "--cih-root", os.path.join(SAND, "없는폴더")]
r1 = run(gone + ["--suffix", "b1"])
check("D3-a 사라진 입력에 exit 3 으로 멈춘다", r1.returncode == 3, "exit=%d" % r1.returncode)
check("D3-b 무엇이 사라졌는지 이름을 찍는다",
      "cih:mask_audit:suspects.csv" in r1.stdout, r1.stdout[-300:])
r2 = run(gone + ["--suffix", "b2", "--allow-missing-input"])
check("D3-c --allow-missing-input 이면 경고만 하고 진행(exit 0)", r2.returncode == 0,
      "exit=%d %s" % (r2.returncode, r2.stdout[-200:]))
r3 = run(["--fruits", "peach", "--out-root", prev, "--date", "260918", "--dry-run",
          "--suffix", "b3", "--no-prev", "--cih-root", os.path.join(SAND, "없는폴더")])
check("D3-d 직전 빌드가 없으면 경고만 하고 진행(exit 0)", r3.returncode == 0, "exit=%d" % r3.returncode)

# ─────────────────────────────────────────────────────────────── D4
print("\nM3-C 폴더 안 파일 하나의 mtime 만 바뀌어도 잡는가 (D4)")
# 툴 복숭아를 모래상자로 복사하고, boxes/ 에 파일 2개를 서로 다른 시각으로 놓는다.
tp = os.path.join(SAND, "tool", "peach")
shutil.copytree(os.path.join(TOOLDATA, "peach"), tp)
bx = os.path.join(tp, "boxes")
os.makedirs(bx, exist_ok=True)
json.dump({"boxes": []}, io.open(os.path.join(bx, "__sandbox_dummy.json"), "w", encoding="utf-8"))
now = time.time()
os.utime(os.path.join(bx, "__sandbox_dummy.json"), (now - 3000, now - 3000))   # 오래된 쪽
for fn in sorted(os.listdir(bx)):
    if fn != "__sandbox_dummy.json":
        os.utime(os.path.join(bx, fn), (now, now))                             # 최신 = 이 파일
rC1 = run(["--fruits", "peach", "--out-root", out, "--date", "260918", "--suffix", "c1",
           "--tool-data", os.path.join(SAND, "tool"), "--no-prev"])
check("M3-C0 첫 빌드 exit 0", rC1.returncode == 0, (rC1.stdout + rC1.stderr)[-400:])
regC = json.load(io.open(os.path.join(out, "datasets_merged_260918_c1", "build_summary.json"),
                         encoding="utf-8"))["input_registry"]
e = regC.get("tool:peach:boxes", {})
check("D4-a 폴더 입력에도 지문(sha256)이 남는다", bool(e.get("sha256")), str(sorted(e)))
check("D4-b 지문의 종류가 «파일 목록+크기+mtime» 이라고 적힌다",
      e.get("fingerprint") == "names+size+mtime", str(e.get("fingerprint")))
# 파일 수도 최신 시각도 그대로인 채, «오래된 쪽» 파일의 mtime 만 더 옛날로 바꾼다.
os.utime(os.path.join(bx, "__sandbox_dummy.json"), (now - 9000, now - 9000))
rC2 = run(["--fruits", "peach", "--out-root", out, "--date", "260918", "--suffix", "c2",
           "--tool-data", os.path.join(SAND, "tool"), "--dry-run"])
lines = rC2.stdout.split("직전 빌드와 견준")[-1].splitlines()[1:]
chg = [l.split() for l in lines if l.startswith("    ") and "→" in l]
keys = {c[0] for c in chg}
check("D4-c 그 폴더 한 줄만 «바뀜» 으로 뜬다", keys == {"tool:peach:boxes"}, str(sorted(keys)) or "없음")
check("D4-d 바뀐 칸이 «지문» 이다(파일 수·최신 시각은 그대로)",
      [c[1] for c in chg] == ["지문"], str(chg))

print("\n" + ("전부 통과" if not fails else "실패 %d건: %s" % (len(fails), fails)))
sys.exit(1 if fails else 0)
