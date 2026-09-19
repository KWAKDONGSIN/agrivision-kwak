# -*- coding: utf-8 -*-
"""2차 검수 §2 — 데이터 오염/소실 공격 (읽기 전용)"""
import csv, hashlib, json, os, random, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

KDS = "/data/project/2026summer/kds0206"
V2 = os.path.join(KDS, "datasets_merged_260918_v2")
REV = {"peach": "datasets_reviewed_260916", "grape": "datasets_reviewed_260916",
       "apple": "datasets_reviewed_260917", "blueberry": "datasets_reviewed_260917"}
ORIG = os.path.join(KDS, "datasets_resized_2mp")
W = "/data/project/2026summer/platform/work"
TOOL = os.path.join(W, "kwak_dongsin/260916_라벨링툴/data")
PSM = os.path.join(W, "park_seongmoon")
LSH = os.path.join(W, "im_seonghu")
random.seed(20260918)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rows():
    with open(os.path.join(V2, "manifest.csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


R = rows()
KEPT = [r for r in R if not r["action"].startswith("excluded")]
print("== A. 이미지 복사가 원본과 바이트 동일한가 (과일별 무작위 15장) ==")
for fruit in ("apple", "grape", "peach", "blueberry"):
    ks = [r for r in KEPT if r["fruit"] == fruit]
    bad = []
    for r in random.sample(ks, min(15, len(ks))):
        s = r["stem"]
        src = (os.path.join(KDS, REV[fruit], fruit, "images", s + ".png")
               if r["image_source"].startswith("reviewed") else
               os.path.join(ORIG, fruit, "images", s + ".png"))
        if md5(src) != md5(os.path.join(V2, fruit, "images", s + ".png")):
            bad.append(s)
    print("  %-10s 표본 %d · 다름 %d %s" % (fruit, min(15, len(ks)), len(bad), bad[:3]))

print("\n== B. 사과 instances 가 검수판 번호 마스크와 화소 동일한가 (무작위 30장) ==")
ap = [r for r in KEPT if r["fruit"] == "apple"]
bad, checked, cutpix = [], 0, []
for r in random.sample(ap, 30):
    s = r["stem"]
    a = np.array(Image.open(os.path.join(KDS, REV["apple"], "apple", "masks", s + ".png")))
    if a.ndim == 3:
        a = a[:, :, 0]
    b = np.array(Image.open(os.path.join(V2, "apple", "instances", s + ".png")))
    checked += 1
    if a.shape != b.shape or not np.array_equal(a.astype(np.uint32), b.astype(np.uint32)):
        bad.append((s, int((a != b).sum()), sorted(set(np.unique(a).tolist()) ^ set(np.unique(b).tolist()))[:6]))
print("  검사 %d장 · 화소가 다른 장 %d" % (checked, len(bad)))
for x in bad[:5]:
    print("    ", x)

print("\n== C. 번호 ⊆ 마스크 전수 + 잘린 화소 ==")
for fruit in ("apple", "blueberry"):
    ks = [r for r in KEPT if r["fruit"] == fruit and r["has_instances"] == "1"]
    out_of, cut_stats, lost_ids = 0, [], 0
    for r in ks:
        s = r["stem"]
        m = np.array(Image.open(os.path.join(V2, fruit, "masks", s + ".png"))) > 0
        inst = np.array(Image.open(os.path.join(V2, fruit, "instances", s + ".png"))).astype(np.uint32)
        if inst.ndim == 3:
            inst = inst[:, :, 0]
        if ((inst > 0) & ~m).any():
            out_of += 1
        # 원본 번호에서 얼마나 잘렸나
        if r["instances_source"] == "detect_seed":
            src = os.path.join(PSM, "bbox_outputs", fruit, "all", "instance_maps", s + ".png")
        elif r["instances_source"] == "instances_fixed":
            src = os.path.join(TOOL, fruit, "instances_fixed", s + ".png")
        else:
            src = os.path.join(KDS, REV[fruit], fruit, "masks", s + ".png")
        if os.path.exists(src):
            o = np.array(Image.open(src))
            if o.ndim == 3:
                o = o[:, :, 0]
            o = o.astype(np.uint32)
            if o.shape == inst.shape:
                cut = int(((o > 0) & (inst == 0)).sum())
                tot = int((o > 0).sum())
                cut_stats.append(cut / tot if tot else 0.0)
                ida, idb = set(np.unique(o).tolist()) - {0}, set(np.unique(inst).tolist()) - {0}
                if ida - idb:
                    lost_ids += 1
    cs = np.array(cut_stats) if cut_stats else np.array([0.0])
    print("  %-10s 번호 %d장 · 마스크 밖 번호가 있는 장 %d · 잘린 비율 중앙 %.4f 최대 %.4f · 번호(id)가 통째로 사라진 장 %d"
          % (fruit, len(ks), out_of, float(np.median(cs)), float(cs.max()), lost_ids))

print("\n== D. masks_fixed 사본이 진짜 수정본인가 ==")
mf = [r for r in KEPT if r["mask_source"] == "masks_fixed"]
print("  mask_source=masks_fixed 인 행 %d" % len(mf))
for r in mf[:20]:
    f, s = r["fruit"], r["stem"]
    p_fix = os.path.join(TOOL, f, "masks_fixed", s + ".png")
    p_rev = os.path.join(KDS, REV[f], f, "masks", s + ".png")
    p_out = os.path.join(V2, f, "masks", s + ".png")
    a = np.array(Image.open(p_fix)) > 0 if os.path.exists(p_fix) else None
    b = np.array(Image.open(p_rev)) > 0 if os.path.exists(p_rev) else None
    c = np.array(Image.open(p_out)) > 0
    if a is not None and a.ndim == 3:
        a = a.max(axis=2)
    if b is not None and b.ndim == 3:
        b = b.max(axis=2)
    print("   %s/%s  out==fixed %s · out==reviewed %s" % (
        f, s, (a is not None and np.array_equal(a, c)),
        (b is not None and np.array_equal(b, c))))

print("\n== E. 포도 image_replaced ==")
ir = [r for r in R if r["action"] == "image_replaced"]
print("  image_replaced 행 %d (과일: %s)" % (len(ir), {r["fruit"] for r in ir}))
for r in ir:
    f, s = r["fruit"], r["stem"]
    o = os.path.join(ORIG, f, "images", s + ".png")
    v = os.path.join(KDS, REV[f], f, "images", s + ".png")
    out = os.path.join(V2, f, "images", s + ".png")
    print("   %s  out==검수판 %s · out==원본(resized_2mp) %s · image_source=%s"
          % (s, os.path.exists(v) and md5(v) == md5(out),
             os.path.exists(o) and md5(o) == md5(out), r["image_source"]))

print("\n== F. YOLO txt — 값 범위 + 박성문 txt 와 바이트 동일(전수) ==")
for fruit in ("apple", "grape", "peach", "blueberry"):
    ks = [r for r in KEPT if r["fruit"] == fruit and r["has_boxes"] == "1"]
    n_same = n_diff = n_nopsm = 0
    oob = []
    for r in ks:
        s = r["stem"]
        t = os.path.join(V2, fruit, "boxes", s + ".txt")
        if not os.path.exists(t):
            oob.append((s, "txt 없음"))
            continue
        for ln in open(t):
            p = ln.split()
            if len(p) != 5:
                oob.append((s, "칸 수 %d" % len(p)))
                break
            vals = [float(x) for x in p[1:]]
            if any(v < 0 or v > 1 for v in vals) or vals[0] - vals[2] / 2 < -1e-6 or vals[0] + vals[2] / 2 > 1 + 1e-6 \
               or vals[1] - vals[3] / 2 < -1e-6 or vals[1] + vals[3] / 2 > 1 + 1e-6:
                oob.append((s, ln.strip()))
                break
        pt = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes", "yolo_labels", s + ".txt")
        if r["boxes_source"] == "psm_gt" and os.path.exists(pt):
            if md5(pt) == md5(t):
                n_same += 1
            else:
                n_diff += 1
        else:
            n_nopsm += 1
    print("  %-10s 상자 %d · psm txt 와 동일 %d · 다름 %d · 대조 불가 %d · 범위이탈/이상 %d %s"
          % (fruit, len(ks), n_same, n_diff, n_nopsm, len(oob), oob[:3]))

print("\n== G. 임성후(lsh) 변환 규칙이 박성문 규칙과 같은가 — 다른 stem 으로 재계산 ==")


def conv(src_json):
    rec = json.load(open(src_json, encoding="utf-8"))
    h, w = (rec.get("image_size_hw") or [1, 1])[:2]
    out = []
    for d in rec.get("detections", []):
        if "bbox_xywh" in d:
            x, y, bw, bh = d["bbox_xywh"]
        else:
            x1, y1, x2, y2 = d["bbox_xyxy"]
            x, y, bw, bh = x1, y1, x2 - x1, y2 - y1
        out.append("0 %.6f %.6f %.6f %.6f" % ((x + bw / 2) / w, (y + bh / 2) / h, bw / w, bh / h))
    return "\n".join(out) + ("\n" if out else "")


for fruit in ("apple", "grape", "peach"):
    ks = [r for r in KEPT if r["fruit"] == fruit and r["boxes_source"] == "psm_gt"]
    smp = random.sample(ks, min(40, len(ks)))
    bad = []
    for r in smp:
        s = r["stem"]
        pj = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes", "json", s + ".json")
        pt = os.path.join(PSM, "bbox_outputs", fruit, "gt_boxes", "yolo_labels", s + ".txt")
        if os.path.exists(pj) and os.path.exists(pt):
            if conv(pj) != open(pt).read():
                bad.append(s)
    print("  %-10s 내 변환 vs 박성문 txt: 표본 %d · 다름 %d %s" % (fruit, len(smp), len(bad), bad[:3]))
# 블루베리: lsh json 에 image_size_hw 가 있나
bb = [r for r in KEPT if r["fruit"] == "blueberry"][:5]
for r in bb:
    p = os.path.join(LSH, "bbox_outputs", "blueberry", "all", "json", r["stem"] + ".json")
    rec = json.load(open(p, encoding="utf-8"))
    print("  lsh json 키:", sorted(rec.keys()), "· image_size_hw:", rec.get("image_size_hw"),
          "· det 키:", sorted((rec.get("detections") or [{}])[0].keys()))
    break
