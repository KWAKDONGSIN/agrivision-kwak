# -*- coding: utf-8 -*-
"""5차 — «규격 검사·맞춤»(팀 표준 2MP) 회귀시험.

작성: 2026-09-19. 고치기 전 판(`tools/_backup_260919_m5_build_merged_dataset.py`)에서는 실패하고,
고친 뒤에는 전부 통과해야 한다.

고치기 전 판으로 돌리려면:
    BUILD_PY=/data/project/2026summer/kds0206/semantic-segmentation/tools/_backup_260919_m5_build_merged_dataset.py \
      /home/kds0206/.conda/envs/kwak/bin/python stage5/test_spec.py

무엇을 보는가 — 모래상자 입력에 **일부러 원본 해상도 파일**을 섞는다(전부 사과 8장).
    S1 masks_fixed 가 2배 크기(2160x3840)           → 최근접으로 표준(1080x1920)으로 맞춤
    S2 instances_fixed 가 2배 크기                   → 최근접 · 번호 id 집합 보존
    S3 툴 상자 json 이 2배 기준(width/height·좌표)   → 픽셀 좌표 비율 변환(±1px) · YOLO 는 그대로
    S4 박성문 gt json 이 2배 기준(image_size_hw)     → 같은 변환 · YOLO 0~1
    S5 전부 표준                                     → `spec_fixed` 가 «-»
    S6 masks_fixed 의 **비율**이 다름(1080x1440)     → 맞추지 않고 **채택하지 않음** + 문제 목록
    S7 검수판 이미지만 2배(표준본은 따로 있음)        → **표준본(resized_2mp)을 씀** · note
    S8 표준본이 아예 없고 검수판 이미지·마스크가 2배  → 원래 규칙으로 표준을 계산해 둘 다 맞춤

모래상자(`stage5/sandbox/`) 안에서만 만든다. 검수판·원본·툴 data·팀원 폴더는 **읽기만** 한다.
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
ORIG = os.path.join(KDS, "datasets_resized_2mp")
PY = sys.executable
HUMAN = "곽동신"
AI = "AI 3회 검수(Opus5→Opus5→Fable5.1)"
STD = (1080, 1920)                 # 사과 표준 크기(= datasets_resized_2mp 사과 전체)
BIG = (2160, 3840)                 # «원본 해상도» 흉내 — 표준의 정확히 2배(비율 같음)
SKEW = (1080, 1440)                # 비율이 다른 크기(0.75 vs 0.5625 → 33% 차이)
CASES = ["S1_mask_2x", "S2_inst_2x", "S3_toolbox_2x", "S4_psmbox_2x",
         "S5_clean", "S6_ratio_mask", "S7_img_2x_std있음", "S8_표준없음_2x"]
fails = []
n_checks = [0]
print("시험 대상 스크립트: %s" % BUILD)

sys.path.insert(0, TOOLS)
import build_merged_dataset as B                      # noqa: E402


def check(n, ok, msg=""):
    n_checks[0] += 1
    print(("  [통과] " if ok else "  [실패] ") + n + (("  — " + msg) if msg and not ok else ""))
    if not ok:
        fails.append(n + (" — " + msg if msg else ""))
    return ok


def up(src_path, dst_path, to_wh, nearest):
    """src 를 to_wh 로 키워 저장한다(원본 해상도 파일 흉내). nearest 면 최근접."""
    with Image.open(src_path) as im:
        arr = np.array(im)
    if nearest:
        big = Image.fromarray(arr.astype(np.int32), mode="I").resize(to_wh, Image.NEAREST)
        B.write_u16(dst_path, np.array(big).astype(np.uint32))
    else:
        with Image.open(src_path) as im:
            im.convert("RGB").resize(to_wh, Image.LANCZOS).save(dst_path, "PNG")


def size_of(p):
    with Image.open(p) as im:
        return tuple(im.size)


# ─────────────────────────────────────────── 모래상자
def build_sandbox():
    shutil.rmtree(SAND, ignore_errors=True)
    rev = os.path.join(SAND, "rev917", "apple")
    org = os.path.join(SAND, "orig", "apple")
    for d in (os.path.join(rev, "images"), os.path.join(rev, "masks"),
              os.path.join(org, "images"), os.path.join(org, "masks")):
        os.makedirs(d)
    src_rows = list(csv.DictReader(io.open(os.path.join(REV917, "apple", "manifest.csv"),
                                          encoding="utf-8")))
    keep = [r for r in src_rows if r["action"] == "keep"][:len(CASES)]
    if len(keep) < len(CASES):
        raise SystemExit("검수판 사과에 남긴 사진이 %d장보다 적습니다" % len(CASES))
    with io.open(os.path.join(rev, "manifest.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(src_rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(keep)
    stems = [r["stem"] for r in keep]
    case_of = dict(zip(stems, CASES))

    tdir = os.path.join(SAND, "tool", "apple")
    os.makedirs(os.path.join(tdir, "boxes"))
    os.makedirs(os.path.join(tdir, "masks_fixed"))
    os.makedirs(os.path.join(tdir, "instances_fixed"))
    psm_json = os.path.join(SAND, "psm", "bbox_outputs", "apple", "gt_boxes", "json")
    psm_yolo = os.path.join(SAND, "psm", "bbox_outputs", "apple", "gt_boxes", "yolo_labels")
    os.makedirs(psm_json)
    os.makedirs(psm_yolo)
    st = {}
    want = {}          # stem → 기대값 모음

    for s in stems:
        c = case_of[s]
        ri, rm = os.path.join(rev, "images", s + ".png"), os.path.join(rev, "masks", s + ".png")
        shutil.copy2(os.path.join(REV917, "apple", "images", s + ".png"), ri)
        shutil.copy2(os.path.join(REV917, "apple", "masks", s + ".png"), rm)
        assert size_of(ri) == STD, "검수판 사과가 %s 가 아닙니다: %s" % (STD, size_of(ri))
        # 표준본(= datasets_resized_2mp 흉내). S8 만 일부러 **없게** 둔다.
        if c != "S8_표준없음_2x":
            shutil.copy2(os.path.join(ORIG, "apple", "images", s + ".png"),
                         os.path.join(org, "images", s + ".png"))
            shutil.copy2(os.path.join(ORIG, "apple", "masks", s + ".png"),
                         os.path.join(org, "masks", s + ".png"))
        rec = {"status": "ok", "by": AI, "at": "2026-09-19 00:00", "note": "AI 제안"}
        w0 = dict(spec="-", img_src="reviewed_260917", msk_src="reviewed_260917", box_src="none")

        if c == "S1_mask_2x":
            m = B.load_mask_bool(rm)
            big = Image.fromarray((m.astype(np.uint8)) * 255, "L").resize(BIG, Image.NEAREST)
            big.save(os.path.join(tdir, "masks_fixed", s + ".png"), "PNG")
            rec["confirmed"] = {"status": "fixed", "by": HUMAN, "at": "2026-09-19 01:00", "note": ""}
            w0.update(spec="mask:2160x3840->1080x1920", msk_src="masks_fixed")
        elif c == "S2_inst_2x":
            m = B.load_mask_bool(rm)
            arr = np.zeros(m.shape, np.uint32)
            ys, xs = np.nonzero(m)
            arr[m] = 7
            arr[ys[:len(ys) // 2], xs[:len(xs) // 2]] = 9      # 번호 두 개(7·9)
            B.write_u16(os.path.join(SAND, "_tmp_inst.png"), arr)
            up(os.path.join(SAND, "_tmp_inst.png"),
               os.path.join(tdir, "instances_fixed", s + ".png"), BIG, True)
            rec["confirmed_instances"] = {"status": "ok", "by": HUMAN,
                                          "at": "2026-09-19 01:05", "note": ""}
            w0.update(spec="instances:2160x3840->1080x1920")
        elif c == "S3_toolbox_2x":
            json.dump({"stem": s, "fruit": "apple", "width": BIG[0], "height": BIG[1],
                       "by": HUMAN, "at": "2026-09-19 01:02", "note": "",
                       "boxes": [{"id": 1, "cls": "fruit", "xyxy": [200, 400, 600, 1000],
                                  "src": "human"}]},
                      io.open(os.path.join(tdir, "boxes", s + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False)
            rec["confirmed_boxes"] = {"status": "ok", "by": HUMAN, "at": "2026-09-19 01:00",
                                      "note": ""}
            w0.update(spec="boxes:2160x3840->1080x1920", box_src="tool")
        elif c == "S4_psmbox_2x":
            json.dump({"image_name": s + ".png", "image_size_hw": [BIG[1], BIG[0]],
                       "total_fruit_count": 1,
                       "detections": [{"id": 1, "bbox_xyxy": [100, 200, 500, 800],
                                       "bbox_xywh": [100, 200, 400, 600],
                                       "center": [300, 500], "area_pixels": 240000}]},
                      io.open(os.path.join(psm_json, s + ".json"), "w", encoding="utf-8"))
            w0.update(spec="boxes:2160x3840->1080x1920", box_src="psm_gt")
        elif c == "S5_clean":
            json.dump({"image_name": s + ".png", "image_size_hw": [STD[1], STD[0]],
                       "total_fruit_count": 1,
                       "detections": [{"id": 1, "bbox_xyxy": [50, 100, 250, 400],
                                       "bbox_xywh": [50, 100, 200, 300],
                                       "center": [150, 250], "area_pixels": 60000}]},
                      io.open(os.path.join(psm_json, s + ".json"), "w", encoding="utf-8"))
            w0.update(box_src="psm_gt")
        elif c == "S6_ratio_mask":
            m = B.load_mask_bool(rm)
            Image.fromarray((m.astype(np.uint8)) * 255, "L").resize(SKEW, Image.NEAREST) \
                 .save(os.path.join(tdir, "masks_fixed", s + ".png"), "PNG")
            rec["confirmed"] = {"status": "fixed", "by": HUMAN, "at": "2026-09-19 01:00", "note": ""}
            w0.update(spec="-", msk_src="reviewed_260917")     # 채택하지 않고 검수판 마스크로
        elif c == "S7_img_2x_std있음":
            up(os.path.join(REV917, "apple", "images", s + ".png"), ri, BIG, False)
            w0.update(spec="-", img_src="resized_2mp")
        elif c == "S8_표준없음_2x":
            up(os.path.join(REV917, "apple", "images", s + ".png"), ri, BIG, False)
            up(os.path.join(REV917, "apple", "masks", s + ".png"), rm, BIG, True)
            w0.update(spec="image:2160x3840->1080x1920;mask:2160x3840->1080x1920")
        st[s] = rec
        want[s] = w0
    json.dump(st, io.open(os.path.join(tdir, "status.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    if os.path.exists(os.path.join(SAND, "_tmp_inst.png")):
        os.remove(os.path.join(SAND, "_tmp_inst.png"))
    return stems, case_of, want


def run(extra):
    out = os.path.join(SAND, "out")
    os.makedirs(out, exist_ok=True)
    cmd = [PY, BUILD, "--fruits", "apple", "--out-root", out, "--date", "260919",
           "--reviewed-260917", os.path.join(SAND, "rev917"),
           "--original-root", os.path.join(SAND, "orig"),
           "--tool-data", os.path.join(SAND, "tool"),
           "--psm-root", os.path.join(SAND, "psm"),
           "--cih-root", os.path.join(SAND, "없는폴더_cih"),
           "--lsh-root", os.path.join(SAND, "없는폴더_lsh"), "--no-prev"] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True), out


def main():
    stems, case_of, want = build_sandbox()
    print("\nS5-0 빌드")
    r, out = run(["--suffix", "s5"])
    d = os.path.join(out, "datasets_merged_260919_s5")
    if not check("S5-0 빌드가 통과(exit 0 · 자체 검사 통과)", r.returncode == 0,
                 (r.stdout + r.stderr)[-1200:]):
        print(r.stdout[-4000:])
        return 1
    man = {row["stem"]: row for row in csv.DictReader(io.open(os.path.join(d, "manifest.csv"),
                                                             encoding="utf-8"))}
    adir = os.path.join(d, "apple")
    bs = json.load(io.open(os.path.join(d, "build_summary.json"), encoding="utf-8"))

    print("\nS5-A 출력 크기 = 표준 · 총 화소 2,073,600±0.15%")
    for s in stems:
        c = case_of[s]
        ip = os.path.join(adir, "images", s + ".png")
        mp = os.path.join(adir, "masks", s + ".png")
        check("S5-A %s 사진이 표준(%dx%d)" % (c, STD[0], STD[1]), size_of(ip) == STD, str(size_of(ip)))
        check("S5-A %s 마스크가 표준" % c, size_of(mp) == STD, str(size_of(mp)))
        w0, h0 = size_of(ip)
        check("S5-A %s 총 화소 ±0.15%%" % c, abs(w0 * h0 - 2073600) <= 2073600 * 0.0015,
              str(w0 * h0))
        with Image.open(mp) as im:
            check("S5-A %s 마스크 L 모드·값 {0,255}" % c,
                  im.mode == "L" and set(np.unique(np.array(im)).tolist()) <= {0, 255},
                  im.mode + str(np.unique(np.array(im))[:5].tolist()))

    print("\nS5-B manifest 의 spec_fixed · 출처 칸")
    for s in stems:
        c, w0 = case_of[s], want[s]
        row = man[s]
        check("S5-B %s spec_fixed" % c, row.get("spec_fixed", "") == w0["spec"],
              "기대 %s · 실제 %s" % (w0["spec"], row.get("spec_fixed", "(칸 없음)")))
        check("S5-B %s image_source" % c, row["image_source"] == w0["img_src"], row["image_source"])
        check("S5-B %s mask_source" % c, row["mask_source"] == w0["msk_src"], row["mask_source"])
        check("S5-B %s boxes_source" % c, row["boxes_source"] == w0["box_src"], row["boxes_source"])

    print("\nS5-C 값 집합 보존 — 번호 id")
    s2 = [s for s in stems if case_of[s] == "S2_inst_2x"][0]
    ip2 = os.path.join(adir, "instances", s2 + ".png")
    check("S5-C1 S2 번호 파일이 나왔다", os.path.exists(ip2))
    if os.path.exists(ip2):
        arr = B.read_u16(ip2)
        check("S5-C2 번호 크기가 표준", tuple(arr.shape[::-1]) == STD, str(arr.shape))
        check("S5-C3 번호 id 집합이 {7,9} 그대로", set(B.ids_of(arr).tolist()) == {7, 9},
              str(sorted(set(B.ids_of(arr).tolist()))[:6]))
        check("S5-C4 instances_source=tool_confirmed", man[s2]["instances_source"] == "tool_confirmed",
              man[s2]["instances_source"])
    s8 = [s for s in stems if case_of[s] == "S8_표준없음_2x"][0]
    ip8 = os.path.join(adir, "instances", s8 + ".png")
    check("S5-C5 S8 은 2배 번호 마스크(원본 마스크)도 표준으로 맞췄다",
          os.path.exists(ip8) and tuple(B.read_u16(ip8).shape[::-1]) == STD,
          str(B.read_u16(ip8).shape) if os.path.exists(ip8) else "파일 없음")

    print("\nS5-D 상자 픽셀 좌표 비율 변환(±1px) · YOLO 0~1")
    s3 = [s for s in stems if case_of[s] == "S3_toolbox_2x"][0]
    j3 = json.load(io.open(os.path.join(adir, "boxes", s3 + ".json"), encoding="utf-8"))
    check("S5-D1 툴 json 의 width·height 가 표준", (j3.get("width"), j3.get("height")) == STD,
          str((j3.get("width"), j3.get("height"))))
    got = (j3.get("boxes") or [{}])[0].get("xyxy")
    check("S5-D2 툴 상자 좌표가 절반(±1px): [100,200,300,500]",
          got is not None and all(abs(a - b) <= 1 for a, b in zip(got, [100, 200, 300, 500])),
          str(got))
    check("S5-D3 툴 YOLO txt 가 0~1", not B.yolo_range_bad(os.path.join(adir, "boxes", s3 + ".txt")),
          str(B.yolo_range_bad(os.path.join(adir, "boxes", s3 + ".txt"))))
    t3 = io.open(os.path.join(adir, "boxes", s3 + ".txt")).read().split()
    check("S5-D4 툴 YOLO 값은 배율에 안 바뀐다(중심 0.185185·0.182292)",
          len(t3) == 5 and abs(float(t3[1]) - 400 / 2160) < 2e-4
          and abs(float(t3[2]) - 700 / 3840) < 2e-4, " ".join(t3))
    s4 = [s for s in stems if case_of[s] == "S4_psmbox_2x"][0]
    j4 = json.load(io.open(os.path.join(adir, "boxes", s4 + ".json"), encoding="utf-8"))
    check("S5-D5 박성문 json 의 image_size_hw 가 표준 [1920,1080]",
          j4.get("image_size_hw") == [STD[1], STD[0]], str(j4.get("image_size_hw")))
    d4 = (j4.get("detections") or [{}])[0]
    check("S5-D6 bbox_xyxy 절반(±1px): [50,100,250,400]",
          all(abs(a - b) <= 1 for a, b in zip(d4.get("bbox_xyxy") or [], [50, 100, 250, 400])),
          str(d4.get("bbox_xyxy")))
    check("S5-D7 bbox_xywh 절반(±1px): [50,100,200,300]",
          all(abs(a - b) <= 1 for a, b in zip(d4.get("bbox_xywh") or [], [50, 100, 200, 300])),
          str(d4.get("bbox_xywh")))
    check("S5-D8 center 절반(±1px): [150,250]",
          all(abs(a - b) <= 1 for a, b in zip(d4.get("center") or [], [150, 250])),
          str(d4.get("center")))
    check("S5-D9 area_pixels 가 1/4(±1%): 60000", d4.get("area_pixels") is not None
          and abs(d4["area_pixels"] - 60000) <= 600, str(d4.get("area_pixels")))
    check("S5-D10 박성문 YOLO txt 가 0~1",
          not B.yolo_range_bad(os.path.join(adir, "boxes", s4 + ".txt")),
          str(B.yolo_range_bad(os.path.join(adir, "boxes", s4 + ".txt"))))
    s5 = [s for s in stems if case_of[s] == "S5_clean"][0]
    j5 = json.load(io.open(os.path.join(adir, "boxes", s5 + ".json"), encoding="utf-8"))
    check("S5-D11 규격이 맞는 json 은 손대지 않는다(spec_fixed 칸 없음)", "spec_fixed" not in j5)
    check("S5-D12 규격이 맞는 json 은 바이트까지 그대로",
          io.open(os.path.join(adir, "boxes", s5 + ".json"), "rb").read()
          == io.open(os.path.join(SAND, "psm", "bbox_outputs", "apple", "gt_boxes", "json",
                                 s5 + ".json"), "rb").read())

    print("\nS5-E 비율이 다르면 채택하지 않는다 + 문제 목록")
    s6 = [s for s in stems if case_of[s] == "S6_ratio_mask"][0]
    probs = bs["problems"]
    check("S5-E1 문제 목록에 «가로세로비가 표준과 0.5% 넘게 달라» 가 있다",
          any("가로세로비" in x and s6 in x for x in probs), str(probs[:3]))
    check("S5-E2 그 마스크를 채택하지 않고 검수판 마스크를 썼다",
          man[s6]["mask_source"] == "reviewed_260917", man[s6]["mask_source"])
    check("S5-E3 note 에 이유가 적힌다", "비율이 표준과 달라" in man[s6]["note"],
          man[s6]["note"][:140])
    check("S5-E4 그래도 사진은 남는다(8장 그대로)",
          sum(1 for s in stems if not man[s]["action"].startswith("excluded")) == len(CASES))
    s7 = [s for s in stems if case_of[s] == "S7_img_2x_std있음"][0]
    check("S5-E5 사진이 표준 크기가 아니면 표준본(resized_2mp)을 쓴다고 note 에 적힌다",
          "표준본(resized_2mp)" in man[s7]["note"], man[s7]["note"][:140])

    print("\nS5-F build_summary · README")
    cnt = bs["counts"]["apple"]
    check("S5-F1 counts.n_spec_fixed 가 종류별로 있다",
          cnt.get("n_spec_fixed") == {"mask": 2, "instances": 1, "boxes": 2, "image": 1},
          str(cnt.get("n_spec_fixed")))
    check("S5-F2 counts.n_spec_fixed_rows = 5", cnt.get("n_spec_fixed_rows") == 5,
          str(cnt.get("n_spec_fixed_rows")))
    check("S5-F3 counts.n_spec_mismatch_ratio = 0(마스크는 다른 후보로 넘겼으므로 사진은 안 뺀다)",
          cnt.get("n_spec_mismatch_ratio") == 0, str(cnt.get("n_spec_mismatch_ratio")))
    sp = (bs.get("spec") or {}).get("apple") or {}
    check("S5-F4 summary.spec 에 표준 규칙(2,073,600·8의 배수·±0.15%)이 적힌다",
          sp.get("target_pixels") == 2073600 and sp.get("multiple") == 8
          and sp.get("pixel_tolerance") == 0.0015, str(sp)[:160])
    check("S5-F5 summary.spec 의 표준 크기표가 1080x1920 8장", sp.get("std_sizes") == {"1080x1920": 8},
          str(sp.get("std_sizes")))
    check("S5-F6 S8 의 표준은 «계산»(computed)으로 잡혔다",
          (sp.get("std_from") or {}).get("computed") == 1, str(sp.get("std_from")))
    rme = io.open(os.path.join(d, "README.md"), encoding="utf-8").read()
    check("S5-F7 README 에 «규격 (팀 표준 2MP)» 절이 있다", "## 규격 (팀 표준 2MP)" in rme)
    check("S5-F8 README 에 2,073,600 ±0.15% 와 해상도 5종 설명이 있다",
          "2,073,600" in rme and "±0.15%" in rme and "5종" in rme)
    check("S5-F9 README 표에 표준 해상도 `1080x1920` 이 있다", "| `1080x1920` |" in rme)
    check("S5-F10 README 에 spec_fixed 칸 설명이 있다", "`spec_fixed`" in rme)
    check("S5-F11 manifest 칸 목록에 spec_fixed 가 있다", "`spec_fixed`" in rme)

    print("\nS5-G 자체 검사(verify) 가 규격 어긋남을 잡는가")
    sys.path.insert(0, TOOLS)
    import importlib
    M = importlib.import_module(os.path.basename(BUILD)[:-3])
    rows = list(csv.DictReader(io.open(os.path.join(d, "manifest.csv"), encoding="utf-8")))
    std_map = {("apple", s): STD for s in stems}
    try:
        check("S5-G0 규격이 맞으면 verify 가 아무것도 잡지 않는다",
              M.verify(d, ["apple"], rows, std_map) == [], str(M.verify(d, ["apple"], rows, std_map)[:3]))
    except TypeError as e:
        check("S5-G0 verify 가 표준 크기표(spec_std)를 받는다", False, str(e))
    s1 = [s for s in stems if case_of[s] == "S1_mask_2x"][0]
    keep = io.open(os.path.join(adir, "images", s1 + ".png"), "rb").read()
    with Image.open(io.BytesIO(keep)) as im:
        im.resize((540, 960), Image.LANCZOS).save(os.path.join(adir, "images", s1 + ".png"), "PNG")
    try:
        bad = M.verify(d, ["apple"], rows, std_map)
    except TypeError:
        bad = []
    io.open(os.path.join(adir, "images", s1 + ".png"), "wb").write(keep)
    check("S5-G1 표준 크기가 아닌 사진을 잡는다", any("팀 표준 크기가 아닙니다" in x for x in bad),
          str(bad[:3]))
    check("S5-G2 총 화소 ±0.15% 밖을 잡는다", any("총 화소" in x for x in bad), str(bad[:3]))
    check("S5-G3 사진·마스크 크기 불일치를 잡는다", any("크기가 다릅니다" in x for x in bad),
          str(bad[:3]))
    tp = os.path.join(adir, "boxes", s3 + ".txt")
    keep_t = io.open(tp).read()
    io.open(tp, "w").write("0 1.5 0.5 0.1 0.1\n")
    try:
        bad2 = M.verify(d, ["apple"], rows, std_map)
    except TypeError:
        bad2 = []
    io.open(tp, "w").write(keep_t)
    check("S5-G4 YOLO 값이 0~1 밖이면 잡는다", any("YOLO txt 값이 0~1 밖" in x for x in bad2),
          str(bad2[:3]))

    print("\nS5-H 멱등 — 두 번 돌려도 manifest 가 바이트까지 같다")
    r2, _ = run(["--suffix", "s5b"])
    d2 = os.path.join(out, "datasets_merged_260919_s5b")
    check("S5-H1 두 번째 빌드도 exit 0", r2.returncode == 0, (r2.stdout + r2.stderr)[-500:])
    if r2.returncode == 0:
        check("S5-H2 manifest 바이트 동일",
              io.open(os.path.join(d, "manifest.csv"), "rb").read()
              == io.open(os.path.join(d2, "manifest.csv"), "rb").read())
        for s in stems:
            a = io.open(os.path.join(d, "apple", "masks", s + ".png"), "rb").read()
            b = io.open(os.path.join(d2, "apple", "masks", s + ".png"), "rb").read()
            if a != b:
                check("S5-H3 마스크도 바이트 동일(%s)" % case_of[s], False)
                break
        else:
            check("S5-H3 맞춘 마스크까지 바이트 동일(8장)", True)

    print("\n검사 %d항목 — %s" % (n_checks[0],
          "전부 통과" if not fails else "실패 %d건:" % len(fails)))
    for x in fails:
        print("  - " + x)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
