# 촬영 단위 검증(yolo_ds_v3/val)에서 v4(해상도 1536) 모델의 과일별 마스크 성능과 개수 오차를 잰다 — 결과는 v4_result.txt (eval_v3.py 를 본뜸)
import os, glob, sys, numpy as np
from ultralytics import YOLO
m = YOLO("runs/eval_v4/weights/best.pt")
r = m.val(data="../yolo_ds_v3/data.yaml", imgsz=1536, batch=8, plots=False, verbose=False, project="runs", name="eval_v4_val", exist_ok=True)
out = ["과일별 마스크 성능(촬영 단위 검증)"]
for i, c in enumerate(r.seg.ap_class_index):
    out.append("%-10s mask mAP50 %.3f  mAP50-95 %.3f  P %.3f  R %.3f" % (r.names[int(c)], r.seg.ap50[i], r.seg.ap[i], r.seg.p[i], r.seg.r[i]))
ims = sorted(glob.glob("../yolo_ds_v3/images/val/*")); res = {}
for k in range(0, len(ims), 16):
    ch = ims[k:k + 16]
    for p, rr in zip(ch, m.predict(ch, imgsz=1536, conf=0.25, verbose=False, max_det=1000)):
        f = os.path.basename(p).split("__")[0]
        lp = os.path.join("../yolo_ds_v3/labels/val", os.path.splitext(os.path.basename(p))[0] + ".txt")
        res.setdefault(f, []).append((sum(1 for _ in open(lp)), len(rr.boxes)))
out.append("개수(라벨 대비 · 사과·포도·복숭아는 원본 정답, 블루베리는 워터셰드 추정)")
for f, v in sorted(res.items()):
    a = np.array(v, float); e = np.abs(a[:, 1] - a[:, 0])
    out.append("%-10s 사진 %3d · 라벨 평균 %.1f · 예측 평균 %.1f · 오차 %.0f%%" % (f, len(a), a[:, 0].mean(), a[:, 1].mean(), 100 * e.sum() / a[:, 0].sum()))
open("v4_result.txt", "w").write("\n".join(out) + "\n"); print("\n".join(out))
