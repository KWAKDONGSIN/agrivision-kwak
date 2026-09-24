# -*- coding: utf-8 -*-
# 모델 초벌 학습용 YOLO 분할 데이터셋을 만든다 — 툴이 지금 보여 주는 번호 라벨(사람 수정 > 팀 초벌 > 원본)을 다각형으로
"""작성: 2026-09-23
실행(kwak 환경, 툴과 같은 원본 폴더): LABELTOOL_DATA_ROOT=$(cat ../../app/logs/last_data_root) python make_yolo_ds.py
결과: ../yolo_ds/{images,labels}/{train,val}/<fruit>__<stem>.* (사진은 심볼릭 링크 — 원본 안 건드림), data.yaml
클래스: 0 apple · 1 blueberry · 2 grape · 3 peach. 사람이 «뺀» 사진(confirmed exclude)은 넣지 않는다.
"""
import os, sys, random, json
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from core.paths import img_path, stems_of                     # noqa: E402
from api.instances import load_inst, mask_path_of              # noqa: E402
from domain.maskio import load_mask_bool                       # noqa: E402
from scipy import ndimage                                      # noqa: E402
from core.status_store import read_status                      # noqa: E402

FR = ["apple", "blueberry", "grape", "peach"]
OUT = os.path.join(HERE, "..", "yolo_ds")
random.seed(0)
n_img = n_obj = 0
for sp in ("train", "val"):
    for k in ("images", "labels"):
        os.makedirs(os.path.join(OUT, k, sp), exist_ok=True)
ONLY = sys.argv[1:] or FR
for ci, f in enumerate(FR):
    if f not in ONLY:
        continue
    st = read_status(f)
    for stem in stems_of(f):
        c = (st.get(stem) or {}).get("confirmed") or {}
        if c.get("status") == "exclude":
            continue
        arr, kind, _ = load_inst(f, stem)
        if arr is None:                      # 번호가 없는 과일(포도 원본): 칠한 덩어리마다 한 열매(툴의 cc4 와 같다)
            mp = mask_path_of(f, stem)
            if not os.path.exists(mp):
                continue
            arr = ndimage.label(load_mask_bool(mp), structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])[0]
        H, W = arr.shape
        lines = []
        for v in np.unique(arr):
            if v == 0:
                continue
            cs, _ = cv2.findContours((arr == v).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cs = [c for c in cs if cv2.contourArea(c) >= 12]
            if not cs:
                continue
            c = max(cs, key=cv2.contourArea).reshape(-1, 2)      # 가려져 조각난 열매는 가장 큰 조각
            if len(c) < 3:
                continue
            lines.append("%d " % ci + " ".join("%.5f %.5f" % (x / W, y / H) for x, y in c))
        if not lines:
            continue
        sp = "val" if random.random() < 0.1 else "train"
        src = img_path(f, stem)
        name = "%s__%s" % (f, stem)
        dst = os.path.join(OUT, "images", sp, name + os.path.splitext(src)[1])
        if not os.path.lexists(dst):
            os.symlink(src, dst)
        with open(os.path.join(OUT, "labels", sp, name + ".txt"), "w") as fo:
            fo.write("\n".join(lines) + "\n")
        n_img += 1; n_obj += len(lines)
    print(f, "done", n_img, n_obj, flush=True)
with open(os.path.join(OUT, "data.yaml"), "w") as fo:
    fo.write("path: %s\ntrain: images/train\nval: images/val\nnames: {0: apple, 1: blueberry, 2: grape, 3: peach}\n" % os.path.abspath(OUT))
print("합계 사진 %d · 열매 %d" % (n_img, n_obj))
