# -*- coding: utf-8 -*-
# 학습한 초벌 모델로 모든 사진의 번호 마스크(uint16 PNG)를 만들어 data/<fruit>/draft/ 에 둔다 — 그림판 «모델 초벌» 이 읽는다
"""작성: 2026-09-23
실행: CUDA_VISIBLE_DEVICES=3 LABELTOOL_DATA_ROOT=$(cat ../../app/logs/last_data_root) ~/venvs/labelai/bin/python predict.py runs/full/weights/best.pt
- 이미 있는 초벌 파일은 건너뛴다(--force 로만 덮어씀). 사람 라벨(masks_fixed 등)은 건드리지 않는다.
- 과일마다 그 과일 클래스의 예측만 쓴다. 큰 것부터 칠하고 작은 것을 위에 칠한다.
"""
import os, sys
import numpy as np
from PIL import Image
from ultralytics import YOLO
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from core.paths import DATA_DIR, img_path, stems_of     # noqa: E402

FR = ["apple", "blueberry", "grape", "peach"]
model = YOLO(sys.argv[1]); force = "--force" in sys.argv
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x] or FR
for ci, f in enumerate(FR):
    if f not in ONLY:
        continue
    out = os.path.join(DATA_DIR, f, os.environ.get("DRAFT_DIR", "draft")); os.makedirs(out, exist_ok=True)
    todo = [s for s in stems_of(f) if force or not os.path.exists(os.path.join(out, s + ".png"))]
    for k in range(0, len(todo), 8):
        chunk = todo[k:k + 8]
        rs = model.predict([img_path(f, s) for s in chunk], imgsz=1280, conf=0.25, retina_masks=True,
                           classes=[ci], verbose=False, max_det=1000)
        for s, r in zip(chunk, rs):
            H, W = r.orig_shape
            lab = np.zeros((H, W), np.uint16)
            if r.masks is not None:
                m = r.masks.data.cpu().numpy() > 0.5
                for j, i in enumerate(np.argsort(-m.reshape(len(m), -1).sum(1))):
                    lab[m[i]] = j + 1
            tmp = os.path.join(out, s + ".png.tmp")
            Image.fromarray(lab).save(tmp, format="PNG"); os.replace(tmp, os.path.join(out, s + ".png"))
        print(f, min(k + 8, len(todo)), "/", len(todo), flush=True)
print("끝")
