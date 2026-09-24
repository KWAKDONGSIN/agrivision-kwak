# -*- coding: utf-8 -*-
# 복숭아 원본(전북대 Seo 2024, COCO 폴리곤)의 열매별 정답 번호를 우리 2MP 사진 크기의 번호 마스크(uint16 PNG)로 만든다
"""작성: 2026-09-23
입력: 연구실 블루베리/datasets_verified/peach_instance_segmentation/peach-data/{train,val,test}.json
출력: 260916_라벨링툴/data/peach/instances_gt/<stem>.png (없는 파일만 새로 씀) + 우리 이진 마스크와의 겹침(IoU) 보고
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
SRC = "/data/project/2026summer/kds0206/연구실 블루베리/datasets_verified/peach_instance_segmentation/peach-data"
IMG = "/data/project/2026summer/kds0206/datasets_resized_2mp/peach/images"
MSK = "/data/project/2026summer/kds0206/datasets_reviewed_260916/peach/masks"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "peach", "instances_gt")
os.makedirs(OUT, exist_ok=True)
ious = []
for sp in ("train", "val", "test"):
    d = json.load(open(os.path.join(SRC, sp + ".json")))
    anns = {}
    for a in d["annotations"]:
        anns.setdefault(a["image_id"], []).append(a)
    for im in d["images"]:
        stem = os.path.splitext(os.path.basename(im["file_name"].replace("\\", "/")))[0]
        W0, H0 = im["width"], im["height"]
        with Image.open(os.path.join(IMG, stem + ".png")) as q:
            W, H = q.size
        lab = np.zeros((H, W), np.uint16)
        # 큰 열매부터 칠하고 작은 열매를 위에(겹친 곳은 작은/앞 열매)
        for k, a in enumerate(sorted(anns.get(im["id"], []), key=lambda a: -a.get("area", 0))):
            for poly in a["segmentation"]:
                pts = np.array(poly, np.float64).reshape(-1, 2) * [W / W0, H / H0]
                cv2.fillPoly(lab, [np.round(pts).astype(np.int32)], int(k + 1))
        out = os.path.join(OUT, stem + ".png")
        if not os.path.exists(out):
            Image.fromarray(lab).save(out)
        m = np.array(Image.open(os.path.join(MSK, stem + ".png")))
        m = (m[..., 0] if m.ndim == 3 else m) > 0
        g = lab > 0
        ious.append((stem, (m & g).sum() / max(1, (m | g).sum()), len(anns.get(im["id"], []))))
v = np.array([x[1] for x in ious])
print("사진 %d · 열매 %d · 우리 마스크와 IoU 중앙 %.3f 최소 %.3f (%s)" % (len(ious), sum(x[2] for x in ious), np.median(v), v.min(), min(ious, key=lambda x: x[1])[0]))
