# -*- coding: utf-8 -*-
"""5차 «규격 검사·맞춤» — **검수2(3차 판정 전 소수정 · m5c)** 단정 시험.

작성: 2026-09-19. 총괄(Fable)이 채택한 N1·N2·N4·N5·N6 만 본다(N3 은 «손대지 않음»).

고치기 전 판으로 돌리면 실패해야 한다:
    BUILD_PY=/data/project/2026summer/kds0206/semantic-segmentation/tools/_backup_260919_m5c_build_merged_dataset.py \
      /home/kds0206/.conda/envs/kwak/bin/python stage5/test_fix_m5c.py

무엇을 보는가
    N2  규격을 맞춘 파일이 있으면 ① 표준 출력 끝에 🔴 경고 블록 ② README «규격 맞춘 파일» 표
        ③ build_summary.json `spec_fixed_files` 가 있다. `--strict-spec` 이면 **exit 4** 로 멈춘다.
        맞춘 것이 **없으면** 경고도 없고 `--strict-spec` 으로도 멈추지 않는다(근거 없이 멈추지 않기).
    N4  `Image.fromarray(..., mode=...)` 가 소스에 0곳 · DeprecationWarning 0건 ·
        고치기 전 방식과 **PNG 바이트(md5) 동일**(사과 번호 마스크·복숭아 이진 마스크 실파일).
    N5  `verify` 가 상자 json 의 기준 사진 크기를 **나간 사진 크기**와 견주어 다르면 **실패**.
    N6  `verify` 가 «마스크 확정 fixed 인데 mask_source 가 masks_fixed 가 아님» 을 센다
        (실패가 아니라 «문제 목록» — 0장일 때 근거 없이 멈추지 않게).

모래상자(`stage5/sandbox_m5c/`) 안에서만 쓴다. 검수판·표준본·툴 data·팀원 폴더는 **읽기만**.
"""
import csv
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import warnings

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SAND = os.path.join(HERE, "sandbox_m5c")
TOOLS = os.path.dirname(os.path.dirname(HERE))
BUILD = os.environ.get("BUILD_PY", os.path.join(TOOLS, "build_merged_dataset.py"))
KDS = "/data/project/2026summer/kds0206"
REV917 = os.path.join(KDS, "datasets_reviewed_260917")
ORIG = os.path.join(KDS, "datasets_resized_2mp")
# 🔴 2026-09-20 구조 사이클 2(시험 위생): 시험이 «지금» 의 공용 판정을 읽으면 사람이 툴에서
#   한 장을 확정할 때마다 손으로 적어 둔 숫자가 어긋난다(09-19 22:55 실측 977→975).
#   `MERGED_TOOL_DATA` 가 있으면 **얼려 둔 툴 자료**를 쓴다(`tests/merged/run_merged.sh` 가 만든다).
#   변수를 주지 않으면 예전과 한 글자도 다르지 않다(실제 빌드는 늘 지금 자료를 본다).
TOOLDATA = (os.environ.get("MERGED_TOOL_DATA", "").strip()
            or "/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/data")
PY = sys.executable
HUMAN = "곽동신"
AI = "AI 3회 검수(Opus5→Opus5→Fable5.1)"
STD = (1080, 1920)
BIG = (2160, 3840)                 # 표준의 정확히 2배(비율 같음) = «원본 해상도» 흉내
SKEW = (1080, 1440)                # 비율이 다른 크기 → masks_fixed 가 **강등**된다(N6)
CASES = ["C1_mask_2x", "C2_clean", "C3_ratio_mask"]
fails = []
n_checks = [0]

print("시험 대상 스크립트: %s" % BUILD)
_spec = importlib.util.spec_from_file_location("bmd_under_test", BUILD)
B = importlib.util.module_from_spec(_spec)
sys.modules["bmd_under_test"] = B
_spec.loader.exec_module(B)


def check(n, ok, msg=""):
    n_checks[0] += 1
    msg = msg if isinstance(msg, str) else str(msg)
    msg = " ".join(msg.split())[:300]
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n + (" — " + msg if msg else ""))
    return ok


def size_of(p):
    with Image.open(p) as im:
        return tuple(im.size)


def md5(b):
    return hashlib.md5(b).hexdigest()


def md5_file(p):
    with open(p, "rb") as f:
        return md5(f.read())


# ─────────────────────────────────────────── 모래상자
def build_sandbox(clean_only=False):
    """clean_only=True 면 «맞출 것이 하나도 없는» 모래상자(경고가 없어야 한다)."""
    root = os.path.join(SAND, "clean" if clean_only else "fix")
    shutil.rmtree(root, ignore_errors=True)
    rev = os.path.join(root, "rev917", "apple")
    org = os.path.join(root, "orig", "apple")
    for d in (os.path.join(rev, "images"), os.path.join(rev, "masks"),
              os.path.join(org, "images"), os.path.join(org, "masks")):
        os.makedirs(d)
    src_rows = list(csv.DictReader(io.open(os.path.join(REV917, "apple", "manifest.csv"),
                                          encoding="utf-8")))
    keep = [r for r in src_rows if r["action"] == "keep"][:len(CASES)]
    with io.open(os.path.join(rev, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(src_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(keep)
    stems = [r["stem"] for r in keep]
    case_of = dict(zip(stems, CASES))

    tdir = os.path.join(root, "tool", "apple")
    os.makedirs(os.path.join(tdir, "masks_fixed"))
    st = {}
    for s in stems:
        c = case_of[s]
        ri = os.path.join(rev, "images", s + ".png")
        rm = os.path.join(rev, "masks", s + ".png")
        shutil.copy2(os.path.join(REV917, "apple", "images", s + ".png"), ri)
        shutil.copy2(os.path.join(REV917, "apple", "masks", s + ".png"), rm)
        shutil.copy2(os.path.join(ORIG, "apple", "images", s + ".png"),
                     os.path.join(org, "images", s + ".png"))
        shutil.copy2(os.path.join(ORIG, "apple", "masks", s + ".png"),
                     os.path.join(org, "masks", s + ".png"))
        rec = {"status": "ok", "by": AI, "at": "2026-09-19 00:00", "note": "AI 제안"}
        if clean_only:
            st[s] = rec
            continue
        if c == "C1_mask_2x":
            m = B.load_mask_bool(rm)
            Image.fromarray((m.astype(np.uint8)) * 255).resize(BIG, Image.NEAREST) \
                 .save(os.path.join(tdir, "masks_fixed", s + ".png"), "PNG")
            rec["confirmed"] = {"status": "fixed", "by": HUMAN, "at": "2026-09-19 01:00", "note": ""}
        elif c == "C3_ratio_mask":
            m = B.load_mask_bool(rm)
            Image.fromarray((m.astype(np.uint8)) * 255).resize(SKEW, Image.NEAREST) \
                 .save(os.path.join(tdir, "masks_fixed", s + ".png"), "PNG")
            rec["confirmed"] = {"status": "fixed", "by": HUMAN, "at": "2026-09-19 01:00", "note": ""}
        st[s] = rec
    json.dump(st, io.open(os.path.join(tdir, "status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    return root, stems, case_of


def run(root, extra, out_name="out"):
    out = os.path.join(root, out_name)
    os.makedirs(out, exist_ok=True)
    cmd = [PY, BUILD, "--fruits", "apple", "--out-root", out, "--date", "260919",
           "--reviewed-260917", os.path.join(root, "rev917"),
           "--original-root", os.path.join(root, "orig"),
           "--tool-data", os.path.join(root, "tool"),
           "--psm-root", os.path.join(root, "없는폴더_psm"),
           "--cih-root", os.path.join(root, "없는폴더_cih"),
           "--lsh-root", os.path.join(root, "없는폴더_lsh"), "--no-prev"] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True), out


# ─────────────────────────────────────────── N2
def test_n2():
    print("\nN2 규격을 맞춘 파일이 있을 때 — 경고 블록 · README 표 · spec_fixed_files · --strict-spec")
    root, stems, case_of = build_sandbox()
    s1 = [s for s in stems if case_of[s] == "C1_mask_2x"][0]
    s3 = [s for s in stems if case_of[s] == "C3_ratio_mask"][0]

    r, out = run(root, ["--suffix", "n2"])
    d = os.path.join(out, "datasets_merged_260919_n2")
    o = r.stdout + r.stderr
    if not check("N2-0 맞춘 것이 있어도 멈추지 않고 만든다(exit 0)", r.returncode == 0, o[-1500:]):
        print(o[-3000:])
        return
    # ① 표준 출력 끝의 경고 블록
    check("N2-1 표준 출력에 🔴 경고 블록이 있다",
          "규격(팀 표준 2MP)을 맞춘 파일이 있습니다" in o, o[-600:])
    check("N2-2 경고 블록이 **맨 끝**에 있다(«검사 통과» 줄 뒤)",
          "검사 통과" in o and o.index("검사 통과") < o.rindex("규격(팀 표준 2MP)을 맞춘 파일이 있습니다")
          if "규격(팀 표준 2MP)을 맞춘 파일이 있습니다" in o else False)
    check("N2-3 경고에 맞춘 파일 수·사진 수가 있다", "맞춘 파일 1개 · 사진 1장" in o,
          [ln for ln in o.splitlines() if "맞춘 파일" in ln][:2])
    check("N2-4 경고에 팀원별(파일 소유자) 줄이 있다",
          "팀원별(파일 소유자)" in o and os.environ.get("USER", "kds0206") in o)
    check("N2-5 경고에 «원본 해상도에서 작업한 것으로 보입니다» 가 있다",
          "원본 해상도에서 작업한 것으로 보입니다" in o)
    check("N2-6 경고에 «datasets_resized_2mp 에서 작업해 달라» 가 있다",
          "datasets_resized_2mp" in o and "작업해 달라" in o)
    # ② README 표
    rd = io.open(os.path.join(d, "README.md"), encoding="utf-8").read()
    check("N2-7 README 에 «규격 맞춘 파일» 표가 있다", "**규격 맞춘 파일**" in rd)
    check("N2-8 README 표에 stem·종류·원래→맞춘 크기·소유자가 한 줄로 있다",
          all(x in rd for x in ("`%s`" % s1, "`mask`", "`2160x3840`", "`1080x1920`",
                               os.environ.get("USER", "kds0206"))),
          [ln for ln in rd.splitlines() if s1 in ln][:2])
    check("N2-9 README 표에 «그 팀원에게 알리십시오» 가 있다", "출처 폴더 소유자» 에게 알리십시오" in rd)
    # ③ build_summary.json
    bs = json.load(io.open(os.path.join(d, "build_summary.json"), encoding="utf-8"))
    sf = bs.get("spec_fixed_files")
    check("N2-10 build_summary 에 spec_fixed_files 목록이 있다", isinstance(sf, list) and len(sf) == 1,
          str(type(sf)) + str(len(sf) if isinstance(sf, list) else ""))
    if isinstance(sf, list) and sf:
        e = sf[0]
        check("N2-11 목록 한 줄에 fruit·stem·kind·원래→맞춘 크기·출처·소유자가 다 있다",
              e.get("fruit") == "apple" and e.get("stem") == s1 and e.get("kind") == "mask"
              and e.get("src_size") == "2160x3840" and e.get("dst_size") == "1080x1920"
              and e.get("source") == "masks_fixed" and e.get("owner"), json.dumps(e, ensure_ascii=False))
        check("N2-12 목록에 그 파일의 경로가 있다",
              e.get("path", "").endswith(os.path.join("masks_fixed", s1 + ".png")), e.get("path", ""))
    check("N2-13 n_spec_fixed_files 가 목록 길이와 같다",
          bs.get("n_spec_fixed_files") == len(sf or []), str(bs.get("n_spec_fixed_files")))
    check("N2-14 spec.apple.fixed_owners 에 소유자별 개수가 있다",
          isinstance(((bs.get("spec") or {}).get("apple") or {}).get("fixed_owners"), dict)
          and sum(((bs.get("spec") or {}).get("apple") or {})["fixed_owners"].values()) == 1)
    check("N2-15 strict_spec 칸이 False 로 적혀 있다", bs.get("strict_spec") is False,
          str(bs.get("strict_spec")))

    # ④ --strict-spec → exit 4 · 폴더를 만들지 않는다
    r2, out2 = run(root, ["--suffix", "n2s", "--strict-spec"], out_name="out_strict")
    o2 = r2.stdout + r2.stderr
    check("N2-16 --strict-spec 이면 exit 4 로 멈춘다", r2.returncode == 4,
          "exit %d · %s" % (r2.returncode, o2[-800:]))
    check("N2-17 --strict-spec 은 출력 폴더를 만들지 않는다",
          not os.path.exists(os.path.join(out2, "datasets_merged_260919_n2s")))
    check("N2-18 --strict-spec 멈춤 문구에 이유가 있다",
          "멈춥니다(--strict-spec)" in o2 and "규격을 맞춰야 하는 파일이 1개" in o2, o2[-500:])
    check("N2-19 --strict-spec 도 경고 블록을 찍는다",
          "규격(팀 표준 2MP)을 맞춘 파일이 있습니다" in o2)
    # ⑤ dry-run
    r3, _ = run(root, ["--dry-run"], out_name="out_dry")
    o3 = r3.stdout + r3.stderr
    check("N2-20 --dry-run 도 경고 블록을 찍는다(exit 0)",
          r3.returncode == 0 and "규격(팀 표준 2MP)을 맞춘 파일이 있습니다" in o3,
          "exit %d" % r3.returncode)
    r4, _ = run(root, ["--dry-run", "--strict-spec"], out_name="out_dry2")
    check("N2-21 --dry-run --strict-spec 은 exit 4", r4.returncode == 4, "exit %d" % r4.returncode)
    # ⑥ 맞출 것이 **없으면** 경고도 없고 --strict-spec 으로도 멈추지 않는다
    croot, _, _ = build_sandbox(clean_only=True)
    r5, out5 = run(croot, ["--suffix", "clean", "--strict-spec"])
    o5 = r5.stdout + r5.stderr
    check("N2-22 맞출 것이 없으면 --strict-spec 으로도 통과(exit 0)", r5.returncode == 0, o5[-900:])
    check("N2-23 맞출 것이 없으면 경고 블록을 찍지 않는다",
          "규격(팀 표준 2MP)을 맞춘 파일이 있습니다" not in o5)
    d5 = os.path.join(out5, "datasets_merged_260919_clean")
    rd5 = io.open(os.path.join(d5, "README.md"), encoding="utf-8").read() \
        if os.path.exists(os.path.join(d5, "README.md")) else ""
    check("N2-24 맞출 것이 없으면 README 는 «맞춘 파일이 없습니다» 라고 적는다",
          "맞춘 파일이 **없습니다**" in rd5, "README 가 없습니다" if not rd5 else rd5[:80])
    bs5 = json.load(io.open(os.path.join(d5, "build_summary.json"), encoding="utf-8")) \
        if os.path.exists(os.path.join(d5, "build_summary.json")) else {}
    check("N2-25 맞출 것이 없으면 spec_fixed_files 는 빈 목록", bs5.get("spec_fixed_files") == [],
          str(bs5.get("spec_fixed_files")))
    return d, s1, s3


# ─────────────────────────────────────────── N1 (값은 그대로 · 문서와 코드가 어긋나지 않나)
def test_n1():
    print("\nN1 허용오차 — 값은 그대로 · «표준과 같으면 총 화소를 다시 묻지 않는다» 가 코드에 있나")
    check("N1-1 SPEC_PIXEL_TOL 이 0.0015 그대로", B.SPEC_PIXEL_TOL == 0.0015, str(B.SPEC_PIXEL_TOL))
    check("N1-2 SPEC_RATIO_TOL 이 0.005 그대로", B.SPEC_RATIO_TOL == 0.005, str(B.SPEC_RATIO_TOL))
    # 표준표 5종은 전부 ±0.15% 안 · 1664x1248 이 가장 넓은 값(+0.148%)
    five = [(1440, 1440), (1080, 1920), (1920, 1080), (1664, 1248), (1248, 1664)]
    check("N1-3 표준표 5종이 전부 ±0.15% 안", all(B.spec_pixels_ok(*t) for t in five))
    worst = max(abs(w * h - B.SPEC_TARGET_PIXELS) / B.SPEC_TARGET_PIXELS for w, h in five)
    check("N1-4 5종 중 가장 먼 것이 +0.148%(=1664x1248)", abs(worst - 0.0014814814) < 1e-6,
          "%.6f%%" % (worst * 100))
    check("N1-5 0.14% 로 좁히면 1664x1248 이 규격 밖(그래서 0.15% 가 가장 좁은 값)",
          abs(1664 * 1248 - B.SPEC_TARGET_PIXELS) > B.SPEC_TARGET_PIXELS * 0.0014)
    # «8의 배수 반올림 최대오차» 가 아님을 숫자로 못박는다 — 임의 크기에서 ±0.15% 를 넘는 것이 많다
    rng = np.random.RandomState(20260919)
    out_of, worst_any = 0, 0.0
    for _ in range(200):
        w = int(rng.randint(300, 8000))
        h = max(300, min(8000, int(w / float(rng.uniform(0.3, 3.0)))))
        nw, nh = B.spec_target_size(w, h)
        d = abs(nw * nh - B.SPEC_TARGET_PIXELS) / float(B.SPEC_TARGET_PIXELS)
        worst_any = max(worst_any, d)
        if not B.spec_pixels_ok(nw, nh):
            out_of += 1
    check("N1-6 원래 규칙이 임의 크기에서 ±0.15% 를 넘는 표준을 만든다(그래서 «반올림 최대오차» 설명은 틀렸다)",
          out_of > 0, "벗어난 개수 %d" % out_of)
    check("N1-7 그 최대오차가 ±0.15%% 보다 크다(실측 최대 %.3f%%)" % (worst_any * 100),
          worst_any > B.SPEC_PIXEL_TOL, "%.5f" % worst_any)
    # 그래서 규격 판정은 «표준표와의 일치» 를 먼저 본다 — 규칙의 짝이면 비율 게이트를 통과한다
    check("N1-8 규칙의 짝이면 비율 게이트를 통과한다(6292x2503 → 2280x912)",
          B.spec_is_rule_pair((6292, 2503), B.spec_target_size(6292, 2503))
          and B.spec_ratio_ok((6292, 2503), B.spec_target_size(6292, 2503)))
    doc = os.path.join(os.path.dirname(HERE), "stage5_spec.md")
    txt = io.open(doc, encoding="utf-8").read()
    check("N1-9 stage5_spec.md §1 의 틀린 설명이 «틀렸다» 로 고쳐져 있다",
          "처음 설명은 틀렸다" in txt and "최대 ±0.49%" in txt
          and "가장 좁은 값" in txt, doc)
    check("N1-10 stage5_spec.md 가 «표준표와의 일치를 먼저» 를 적고 있다",
          "표준표(`datasets_resized_2mp`)와의 일치를 먼저 보고" in txt)


# ─────────────────────────────────────────── N4
def test_n4():
    print("\nN4 Pillow 13 대비 — mode= 0곳 · DeprecationWarning 0건 · md5 동일")
    # 주석·설명글에 적힌 `mode="I;16"` 은 세지 않는다 — **실제 호출**만 AST 로 센다.
    import ast
    tree = ast.parse(io.open(BUILD, encoding="utf-8").read())
    hits = []
    for nd in ast.walk(tree):
        if not isinstance(nd, ast.Call):
            continue
        fn = nd.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name in ("fromarray", "new", "frombuffer") and any(k.arg == "mode" for k in nd.keywords):
            hits.append("%d행 %s(mode=…)" % (nd.lineno, name))
    check("N4-1 실제 호출에 `mode=` 인자가 0곳(Pillow 13 에서 없어진다)", not hits, "; ".join(hits))

    arr = np.array([[0, 1, 70000], [65535, 3, 2]], dtype=np.uint32)
    m = np.array([[True, False], [False, True]])
    tmp = os.path.join(SAND, "n4")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        B.write_u16(os.path.join(tmp, "a.png"), arr)
        B.save_mask_255(os.path.join(tmp, "b.png"), m)
        B.nn_resize_u16(arr, (6, 4))
        B.nn_resize_mask(m, (4, 4))
        dep = [str(w.message) for w in ws if issubclass(w.category, DeprecationWarning)]
    check("N4-2 네 함수에서 DeprecationWarning 0건", not dep, "; ".join(dep)[:300])

    # 고치기 전 방식과 **PNG 바이트 동일** — 실파일로 본다(읽기만)
    def old_u16_bytes(a):
        bio = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Image.fromarray(a.astype("<u2"), mode="I;16").save(bio, format="PNG")
        return bio.getvalue()

    def old_mask_bytes(mm):
        bio = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            Image.fromarray((np.asarray(mm).astype(np.uint8)) * 255, mode="L").save(bio, format="PNG")
        return bio.getvalue()

    ap = sorted(p for p in os.listdir(os.path.join(REV917, "apple", "masks"))
                if p.endswith(".png"))[:3]
    for i, fn in enumerate(ap, 1):
        a = B.read_u16(os.path.join(REV917, "apple", "masks", fn))
        p = os.path.join(tmp, "apple%d.png" % i)
        B.write_u16(p, a)
        check("N4-3.%d 사과 번호 마스크 %s — write_u16 md5 가 고치기 전과 같다" % (i, fn[:24]),
              md5_file(p) == md5(old_u16_bytes(a)),
              "%s vs %s" % (md5_file(p)[:12], md5(old_u16_bytes(a))[:12]))
    pf = os.path.join(TOOLDATA, "peach", "masks_fixed")
    pl = sorted(p for p in os.listdir(pf) if p.endswith(".png"))[:3] if os.path.isdir(pf) else []
    for i, fn in enumerate(pl, 1):
        mm = B.load_mask_bool(os.path.join(pf, fn))
        p = os.path.join(tmp, "peach%d.png" % i)
        B.save_mask_255(p, mm)
        check("N4-4.%d 복숭아 마스크 %s — save_mask_255 md5 가 고치기 전과 같다" % (i, fn),
              md5_file(p) == md5(old_mask_bytes(mm)),
              "%s vs %s" % (md5_file(p)[:12], md5(old_mask_bytes(mm))[:12]))
        a = B.read_u16(os.path.join(pf, fn))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            oldarr = np.array(Image.fromarray(a.astype(np.int32), mode="I")
                              .resize((540, 960), Image.NEAREST)).astype(np.uint32)
        check("N4-5.%d 복숭아 %s — nn_resize_u16 결과 배열이 고치기 전과 같다" % (i, fn),
              bool((B.nn_resize_u16(a, (540, 960)) == oldarr).all()))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            oldm = np.array(Image.fromarray((mm.astype(np.uint8)) * 255, mode="L")
                            .resize((540, 960), Image.NEAREST)) > 0
        check("N4-6.%d 복숭아 %s — nn_resize_mask 결과가 고치기 전과 같다" % (i, fn),
              bool((B.nn_resize_mask(mm, (540, 960)) == oldm).all()))
    # 툴 쪽 `app/instances.py` 는 **여기서 고치지 않는다**(총괄 지시 — 보고서에만 적는다).
    # 그 자리가 아직 남아 있다는 것을 «읽기만» 해서 기록으로 남긴다.
    tp = os.path.join(os.path.dirname(TOOLDATA), "app", "instances.py")
    still = (io.open(tp, encoding="utf-8").read().count('mode="I;16"')
             if os.path.exists(tp) else -1)
    check("N4-7 툴 쪽 app/instances.py 에 같은 자리가 **아직 남아 있다**(여기서는 고치지 않는다)",
          still != 0, "mode=\"I;16\" %d곳 (파일 없으면 -1)" % still)
    return len(ap), len(pl)


# ─────────────────────────────────────────── N5 · N6 (verify 단위시험)
def _tiny_out(root, boxes_hw, img_wh=(1080, 1920)):
    """verify 가 읽을 최소 출력 폴더를 손으로 만든다(사진·마스크·상자 json·YOLO txt)."""
    shutil.rmtree(root, ignore_errors=True)
    f = os.path.join(root, "apple")
    for d in ("images", "masks", "boxes"):
        os.makedirs(os.path.join(f, d))
    Image.new("RGB", img_wh, (10, 20, 30)).save(os.path.join(f, "images", "x.png"))
    mk = np.zeros((img_wh[1], img_wh[0]), bool)
    mk[10:40, 10:40] = True
    B.save_mask_255(os.path.join(f, "masks", "x.png"), mk)
    json.dump({"image_name": "x.png", "image_size_hw": list(boxes_hw), "total_fruit_count": 1,
               "detections": [{"id": 1, "bbox_xyxy": [10, 10, 40, 40],
                               "bbox_xywh": [10, 10, 30, 30], "center": [25, 25],
                               "area_pixels": 900}]},
              io.open(os.path.join(f, "boxes", "x.json"), "w", encoding="utf-8"))
    io.open(os.path.join(f, "boxes", "x.txt"), "w").write("0 0.1 0.1 0.02 0.02\n")


def _row(**kw):
    r = {c: "" for c in B.MANIFEST_COLS}
    r.update(fruit="apple", stem="x", action="keep", reason="", note="",
             image_source="reviewed_260917", mask_source="reviewed_260917",
             source="reviewed", instances_source="none", boxes_source="psm_gt",
             verdict_source="none", has_instances="0", has_boxes="1",
             boxes_confirmed_status="-", instances_confirmed_status="-", spec_fixed="-")
    r.update(kw)
    return r


def test_n5():
    print("\nN5 verify 가 상자 json 의 기준 사진 크기를 나간 사진 크기와 견준다")
    root = os.path.join(SAND, "n5_ok")
    _tiny_out(root, (1920, 1080))                       # image_size_hw = [h,w] = 맞다
    bad = B.verify(root, ["apple"], [_row()], {("apple", "x"): (1080, 1920)})
    check("N5-1 기준 크기가 나간 사진과 같으면 통과", not bad, "; ".join(bad)[:400])
    root2 = os.path.join(SAND, "n5_bad")
    _tiny_out(root2, (3840, 2160))                      # 2배 기준 — 픽셀 좌표가 어긋나 있다
    bad2 = B.verify(root2, ["apple"], [_row()], {("apple", "x"): (1080, 1920)})
    hit = [b for b in bad2 if "상자 json" in b and "기준 사진 크기" in b]
    check("N5-2 기준 크기가 다르면 **실패**로 잡는다", bool(hit), "; ".join(bad2)[:400])
    check("N5-3 실패 문구에 두 크기와 출처가 적힌다",
          bool(hit) and "2160x3840" in hit[0] and "1080x1920" in hit[0] and "psm_gt" in hit[0],
          hit[0] if hit else "")
    root3 = os.path.join(SAND, "n5_none")
    _tiny_out(root3, (1920, 1080))
    j = os.path.join(root3, "apple", "boxes", "x.json")
    rec = json.load(io.open(j, encoding="utf-8"))
    rec.pop("image_size_hw")
    json.dump(rec, io.open(j, "w", encoding="utf-8"))
    bad3 = B.verify(root3, ["apple"], [_row()], {("apple", "x"): (1080, 1920)})
    check("N5-4 기준 크기를 못 읽으면 verify 는 **멈추지 않는다**(plan 이 problems 에 적는 자리다)",
          not [b for b in bad3 if "기준 사진 크기" in b], "; ".join(bad3)[:300])


def test_n6():
    print("\nN6 verify 가 «마스크 확정 fixed 인데 mask_source 가 masks_fixed 가 아님» 을 센다")
    root = os.path.join(SAND, "n6")
    _tiny_out(root, (1920, 1080))
    std = {("apple", "x"): (1080, 1920)}

    def v5(rows, notes):
        """5칸 호출. 고치기 전 판은 4칸까지라 TypeError 가 난다 → 그것이 «전 실패» 다."""
        try:
            return B.verify(root, ["apple"], rows, std, notes), ""
        except TypeError as e:
            return None, "verify 가 notes 칸을 받지 못합니다: %s" % e

    notes = []
    bad, err = v5([_row(action="mask_fixed", mask_source="reviewed_260917",
                        source="human_confirmed")], notes)
    check("N6-1 어긋난 행을 «문제 목록» 에 적는다", len(notes) == 1, err or str(notes))
    check("N6-2 몇 개인지와 예시가 적힌다",
          bool(notes) and "1개" in notes[0] and "apple/x→reviewed_260917" in notes[0],
          err or (notes[0] if notes else ""))
    check("N6-3 그것 때문에 **실패하지는 않는다**", bad == [], err or str(bad))
    notes2 = []
    v5([_row(action="mask_fixed", mask_source="masks_fixed", source="human_confirmed")], notes2)
    check("N6-4 제대로 masks_fixed 가 나갔으면 아무 말도 하지 않는다", notes2 == [], str(notes2))
    notes3 = []
    v5([_row()], notes3)
    check("N6-5 확정이 fixed 가 아니면 세지 않는다(0장일 때 근거 없이 멈추지 않는다)",
          notes3 == [], str(notes3))
    # 🔴 실자료 함정: 검수판(AI 3회 검수)이 이미 `mask_fixed` 로 적어 둔 행은 **사람 확정이 아니다**
    #    (복숭아 39장 · v3 에도 그대로 있다). 그것까지 세면 «사람이 고친 마스크를 잃었다» 는
    #    거짓 경고가 실자료에서 39건 뜬다.
    notes4 = []
    v5([_row(action="mask_fixed", mask_source="reviewed_260916", source="ai")], notes4)
    check("N6-5b 검수판이 적어 둔 mask_fixed(source=ai)는 세지 않는다(복숭아 39장 거짓경고 방지)",
          notes4 == [], str(notes4))
    notes5 = []
    v5([_row(action="mask_fixed", mask_source="reviewed_260916", source="reviewed")], notes5)
    check("N6-5c source=reviewed 도 세지 않는다", notes5 == [], str(notes5))
    notes6 = []
    v5([_row(action="mask_fixed", mask_source="reviewed_260916", source="human_unconfirmed")],
       notes6)
    check("N6-5d 확정 칸 없이 사람이 누른 «수정함»(human_unconfirmed)도 센다", len(notes6) == 1,
          str(notes6))
    check("N6-6 notes 를 주지 않아도 옛 3칸·4칸 호출이 그대로 된다",
          B.verify(root, ["apple"], [_row()], std) == []
          and B.verify(root, ["apple"], [_row()]) == [])


def test_n6_end2end(d, s3):
    """C3(비율이 달라 masks_fixed 가 강등된 사진)이 실제 빌드에서도 잡히나."""
    print("\nN6-E 실제 빌드에서도 잡히나(C3_ratio_mask = 확정 fixed + 강등)")
    if not d:
        check("N6-E 빌드 결과가 있어야 한다", False, "N2 빌드가 실패했습니다")
        return
    man = {r["stem"]: r for r in csv.DictReader(io.open(os.path.join(d, "manifest.csv"),
                                                       encoding="utf-8"))}
    r3 = man.get(s3, {})
    check("N6-E1 C3 의 action 이 mask_fixed · mask_source 가 masks_fixed 가 아니다",
          r3.get("action") == "mask_fixed" and r3.get("mask_source") != "masks_fixed",
          "%s / %s" % (r3.get("action"), r3.get("mask_source")))
    bs = json.load(io.open(os.path.join(d, "build_summary.json"), encoding="utf-8"))
    vn = bs.get("verify_notes") or []
    check("N6-E2 build_summary 의 verify_notes 에 그 줄이 있다",
          any("masks_fixed" in x and "수정함" in x for x in vn), str(vn)[:400])
    check("N6-E3 그 줄이 problems 에도 들어간다(README 에 나온다)",
          any("masks_fixed" in x and "수정함" in x for x in (bs.get("problems") or [])))


def main():
    d = s1 = s3 = None
    got = test_n2()
    if got:
        d, s1, s3 = got
    test_n1()
    test_n4()
    test_n5()
    test_n6()
    test_n6_end2end(d, s3)
    print("\n─────────────────────────────────────────────")
    print("항목 %d개 · 실패 %d개" % (n_checks[0], len(fails)))
    for f in fails:
        print("  ✗ " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
