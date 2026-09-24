# -*- coding: utf-8 -*-
# 초벌 확신도 문턱을 과일마다 고른다 — 촬영 단위 검증 사진에서 한 번(conf 0.05) 예측해 두고 문턱별 F1 을 잰다(정답 = 원본 번호)
import os, sys, json, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare_variants as C
res = {}
for f, ci in C.FR.items():
    stems = sorted(n.split("__", 1)[1][:-4] for n in os.listdir(C.VAL) if n.startswith(f + "__"))
    stems = stems[::max(1, len(stems) // 120)][:120]
    cache = []
    for s in stems:
        im = cv2.imread(C.img_path(f, s)); H, W = im.shape[:2]
        ms, sc, _ = C.masks_from(C.MODEL.predict(im, imgsz=1280, conf=0.05, retina_masks=True, classes=[ci], verbose=False, max_det=1000)[0], H, W)
        cache.append((ms, sc, C.gt_of(f, s)))
    rows = []
    for t in (0.15, 0.25, 0.35, 0.45, 0.55, 0.65):
        acc = [C.score(ms[sc >= t], G) for ms, sc, G in cache]
        F1 = float(np.mean([a["F1"] for a in acc])); ce = 100 * sum(a["cnt_err"] for a in acc) / max(1, sum(a["n_gt"] for a in acc))
        rows.append((t, round(F1, 4), round(float(np.mean([a["P"] for a in acc])), 4), round(float(np.mean([a["R"] for a in acc])), 4), round(ce, 1)))
        print(f, rows[-1], flush=True)
    res[f] = rows
json.dump(res, open("conf_sweep.json", "w"), indent=1)
