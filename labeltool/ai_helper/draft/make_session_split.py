# -*- coding: utf-8 -*-
# 정직한 성능 측정용 — yolo_ds_v2 와 같은 라벨을 «촬영 단위(영상·세션·나무·번호 구간)» 로 학습/검증을 나눠 yolo_ds_v3 로 만든다
"""작성: 2026-09-23
거의 같은 프레임이 학습·검증에 동시에 들어가면 점수가 부풀려진다 → 같은 묶음은 한쪽에만.
묶음: 사과 = 파일 이름 앞부분(세션) · 블루베리 = Camera·Video · 포도 = 번호 50개 구간(CERTH 는 연속 번호가 이웃 프레임) · 복숭아 = 나무(t1~t4).
과일마다 묶음을 무작위로 골라 사진의 약 15% 를 검증으로. 사진·라벨은 v2 를 링크한다(복사 없음).
"""
import os, re, random, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "yolo_ds_v2"); OUT = os.path.join(HERE, "..", "yolo_ds_v3")
def group(fruit, stem):
    if fruit == "apple":
        m = re.match(r"^(.+?)(?:_image|_)\d+$", stem); return m.group(1) if m else stem
    if fruit == "blueberry":
        m = re.match(r"^(Camera\s*\d+\s*Video\s*\(\d+\))", stem); return m.group(1) if m else stem
    if fruit == "grape":
        return str(int(stem) // 50) if stem.isdigit() else stem
    m = re.match(r"^(\d+-t\d+)", stem); return m.group(1) if m else stem
items = []
for sp in ("train", "val"):
    for n in os.listdir(os.path.join(SRC, "labels", sp)):
        f, stem = n[:-4].split("__", 1)
        img = [x for x in os.listdir(os.path.join(SRC, "images", sp)) if x.startswith(n[:-4] + ".")] if False else None
        items.append((f, stem, sp, n[:-4]))
imgs = {}
for sp in ("train", "val"):
    for x in os.listdir(os.path.join(SRC, "images", sp)):
        imgs[os.path.splitext(x)[0]] = os.path.join(SRC, "images", sp, x)
random.seed(0); val = set()
byf = collections.defaultdict(lambda: collections.defaultdict(list))
for f, stem, sp, key in items: byf[f][group(f, stem)].append(key)
for f, gs in byf.items():
    keys = list(gs); random.shuffle(keys); total = sum(len(v) for v in gs.values()); n = 0
    for g in keys:
        if n >= 0.15 * total: break
        val.update(gs[g]); n += len(gs[g])
    print(f, "묶음", len(gs), "검증 사진", n, "/", total)
for sp in ("train", "val"):
    for k in ("images", "labels"): os.makedirs(os.path.join(OUT, k, sp), exist_ok=True)
for f, stem, sp, key in items:
    dsp = "val" if key in val else "train"
    li = os.path.join(OUT, "labels", dsp, key + ".txt")
    if not os.path.lexists(li): os.symlink(os.path.realpath(os.path.join(SRC, "labels", sp, key + ".txt")), li)
    src = imgs[key]; di = os.path.join(OUT, "images", dsp, os.path.basename(src))
    if not os.path.lexists(di): os.symlink(os.path.realpath(src), di)
open(os.path.join(OUT, "data.yaml"), "w").write("path: %s\ntrain: images/train\nval: images/val\nnames: {0: apple, 1: blueberry, 2: grape, 3: peach}\n" % os.path.abspath(OUT))
print("끝")
