# -*- coding: utf-8 -*-
"""2차 검수 즉시수정 회귀시험 — 고치기 전에는 실패하고, 고친 뒤에는 통과해야 한다."""
import csv, json, os, shutil, subprocess, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox", "fixes")
BUILD = "/data/project/2026summer/kds0206/semantic-segmentation/tools/build_merged_dataset.py"
CIH = "/data/project/2026summer/platform/work/choi_inhun"
PY = sys.executable
fails = []


def check(n, ok, msg=""):
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n)


def run(tag, extra):
    out = os.path.join(SAND, "out")
    os.makedirs(out, exist_ok=True)
    d = os.path.join(out, "datasets_merged_260918_" + tag)
    if os.path.isdir(d):
        shutil.rmtree(d)
    r = subprocess.run([PY, BUILD, "--fruits", "peach", "--out-root", out, "--date", "260918",
                        "--suffix", tag, "--no-prev"] + extra, capture_output=True, text=True)
    return r, d


print("F1 복숭아 중복 후보가 split_group 을 가로지르지 않는가 (누수)")
r, d = run("f1", [])
M = list(csv.DictReader(open(os.path.join(d, "manifest.csv"), encoding="utf-8")))
g = collections.defaultdict(set)
sess = collections.defaultdict(set)
for x in M:
    if x["peach_dup_candidate"]:
        g[x["peach_dup_candidate"]].add(x["split_group"])
        sess[x["peach_dup_candidate"]].add(x["session"])
cross = {k: sorted(v) for k, v in g.items() if len(v) > 1}
check("F1-a 중복 후보 그룹이 한 split_group 안에 있다", not cross, str(cross))
crosss = {k: sorted(v) for k, v in sess.items() if len(v) > 1}
check("F1-b 중복 후보 그룹이 한 session 안에 있다(시리즈 간 오탐 제외 — REPORT §3)",
      not crosss, str(crosss))
print("     후보 %d장 · %d그룹" % (sum(1 for x in M if x["peach_dup_candidate"]), len(g)))

print("\nF2 망가진 similar_pairs.csv 에 멈추지 않는가")
bad = os.path.join(SAND, "badcih", "dup_audit_260917", "peach")
os.makedirs(bad, exist_ok=True)
src = open(os.path.join(CIH, "dup_audit_260917", "peach", "similar_pairs.csv"), encoding="utf-8").read()
open(os.path.join(bad, "similar_pairs.csv"), "w", encoding="utf-8").write(src[:500])   # 줄 중간에서 잘림
r2, d2 = run("f2", ["--cih-root", os.path.join(SAND, "badcih")])
check("F2 잘린 CSV 에도 exit 0", r2.returncode == 0, (r2.stderr or "")[-300:])
open(os.path.join(bad, "similar_pairs.csv"), "w", encoding="utf-8").write("x,y,z\n1,2,3\n")  # 칸 이름이 다름
r3, d3 = run("f3", ["--cih-root", os.path.join(SAND, "badcih")])
check("F2-b 칸 이름이 달라도 exit 0", r3.returncode == 0, (r3.stderr or "")[-300:])

print("\nF3 --date·--suffix 에 경로 구분자가 들어가면 막는가")
out = os.path.join(SAND, "out")
r4 = subprocess.run([PY, BUILD, "--fruits", "peach", "--out-root", out, "--date", "260918",
                     "--suffix", "../탈출", "--no-prev", "--dry-run"], capture_output=True, text=True)
check("F3-a --suffix '../…' 를 거부(exit≠0)", r4.returncode != 0, "exit=%d" % r4.returncode)
r5 = subprocess.run([PY, BUILD, "--fruits", "peach", "--out-root", out, "--date", "../../etc",
                     "--no-prev", "--dry-run"], capture_output=True, text=True)
check("F3-b --date '../../etc' 를 거부(exit≠0)", r5.returncode != 0, "exit=%d" % r5.returncode)
r6 = subprocess.run([PY, BUILD, "--fruits", "peach", "--out-root", out, "--date", "260918",
                     "--suffix", "정상이름", "--no-prev", "--dry-run"], capture_output=True, text=True)
check("F3-c 멀쩡한 이름은 그대로 통과", r6.returncode == 0, "exit=%d" % r6.returncode)

print("\nF4 출력 폴더가 입력 폴더 안이면 막는가")
r7 = subprocess.run([PY, BUILD, "--fruits", "peach", "--dry-run", "--no-prev",
                     "--out-root", "/data/project/2026summer/kds0206/datasets_reviewed_260916"],
                    capture_output=True, text=True)
check("F4 --out-root 가 검수판이면 거부(exit≠0)", r7.returncode != 0,
      "exit=%d %s" % (r7.returncode, r7.stdout[-200:]))

print("\nF5 _INCOMPLETE 판을 «직전 빌드» 로 고르지 않는가")
pv = os.path.join(SAND, "prev")
os.makedirs(pv, exist_ok=True)
REG = {"cih:mask_audit:suspects.csv": {"path": "x", "exists": True, "kind": "file",
                                       "sha256": "0" * 64, "n_rows": 1}}
for tag, at in (("good", "2026-09-18 10:00:00"), ("bad_INCOMPLETE", "2099-01-01 00:00:00")):
    t = os.path.join(pv, "datasets_merged_260918_" + tag)
    os.makedirs(t, exist_ok=True)
    json.dump({"built_at": at, "input_registry": REG, "inputs": {}},
              open(os.path.join(t, "build_summary.json"), "w", encoding="utf-8"))
r8 = subprocess.run([PY, BUILD, "--fruits", "peach", "--out-root", pv, "--date", "260918",
                     "--suffix", "pv", "--dry-run"], capture_output=True, text=True)
check("F5 _INCOMPLETE 를 직전 빌드로 고르지 않음", "_INCOMPLETE" not in r8.stdout,
      [l for l in r8.stdout.splitlines() if "직전 빌드" in l])

print("\nF6 팀원 입력이 읽히지 않으면 눈에 띄게 알리는가")
r9 = subprocess.run([PY, BUILD, "--fruits", "peach", "--dry-run", "--no-prev",
                     "--psm-root", "/없음", "--cih-root", "/없음", "--lsh-root", "/없음"],
                    capture_output=True, text=True)
check("F6 읽지 못한 입력 목록을 찍는다", "읽지 못한 입력" in r9.stdout, r9.stdout[:400])

print("\nF7 빈 툴 상자 파일이 박성문 gt 를 밀어내지 않는가 (데이터 소실)")
r10, d10 = run("f7", [])
M7 = {x["stem"]: x for x in csv.DictReader(open(os.path.join(d10, "manifest.csv"), encoding="utf-8"))}
row = M7["210629-t4-17"]
txt = os.path.join(d10, "peach", "boxes", "210629-t4-17.txt")
n = sum(1 for _ in open(txt)) if os.path.exists(txt) else 0
check("F7-a 빈 툴 파일이 boxes_source 를 가로채지 않는다", row["boxes_source"] == "psm_gt", row["boxes_source"])
check("F7-b 정답 상자 4개가 살아 있다", n == 4, "txt %d줄" % n)
def box_lines(d):
    """그 빌드가 낸 복숭아 YOLO txt 줄 수 합계(뺀 사진은 세지 않는다)."""
    n = 0
    for x in csv.DictReader(open(os.path.join(d, "manifest.csv"), encoding="utf-8")):
        if x["action"].startswith("excluded"):
            continue
        t = os.path.join(d, "peach", "boxes", x["stem"] + ".txt")
        n += sum(1 for _ in open(t)) if os.path.exists(t) else 0
    return n


allt = box_lines(d10)
# 🔴 2026-09-20 구조 사이클 2 (시험 위생 · 사이클 1 3차 판정): 전에는 `allt == 977` 이라고
#   **손으로 적어** 두었다. 그 977 은 공용 `data/peach/status.json` 에 매달린 수여서, 09-19 22:55 에
#   누가 복숭아 한 장을 «문제 있음» 으로 확정하자 975 가 되어 이 시험이 실패했다(툴 코드 문제가 아니다).
#   그래서 «빈 툴 json 을 **감춘** 빌드» 와 견주는 것으로 바꾼다 — 고치기 전 코드에서는 빈 툴 json 이
#   박성문 정답 상자를 밀어내므로 두 수가 4줄 달라지고(973 ≠ 977), 고친 뒤에는 **늘 같다.**
#   사람이 판정을 몇 장 바꾸든 두 빌드가 같이 움직이므로 다시 낡지 않는다.
TOOLDATA_NOW = (os.environ.get("MERGED_TOOL_DATA", "").strip()
                or "/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/data")
HIDE = os.path.join(SAND, "tool_nohollow")
if os.path.isdir(HIDE):
    shutil.rmtree(HIDE)
for fruit in sorted(os.listdir(TOOLDATA_NOW)):
    fd = os.path.join(TOOLDATA_NOW, fruit)
    if not os.path.isdir(fd):
        continue
    os.makedirs(os.path.join(HIDE, fruit), exist_ok=True)
    for e in sorted(os.listdir(fd)):
        if e != "boxes":
            os.symlink(os.path.realpath(os.path.join(fd, e)), os.path.join(HIDE, fruit, e))
            continue
        os.makedirs(os.path.join(HIDE, fruit, "boxes"), exist_ok=True)
        for b in sorted(os.listdir(os.path.join(fd, "boxes"))):
            if fruit == "peach" and b == "210629-t4-17.json":
                continue                      # ← 빈 툴 json 을 감춘다
            os.symlink(os.path.realpath(os.path.join(fd, "boxes", b)),
                       os.path.join(HIDE, fruit, "boxes", b))
r10b, d10b = run("f7c", ["--tool-data", HIDE])
allt2 = box_lines(d10b)
check("F7-c 빈 툴 json 을 감춘 빌드와 상자 줄 수가 같다(= 정답 상자를 밀어내지 않았다)",
      allt == allt2, "지금 %d줄 · 감춘 판 %d줄" % (allt, allt2))
print("     복숭아 상자 합계 %d줄 (손으로 적지 않는다 — 두 빌드를 견준다)" % allt)


print("\n" + ("전부 통과" if not fails else "실패 %d건: %s" % (len(fails), fails)))
sys.exit(1 if fails else 0)
