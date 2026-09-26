# 초벌 모델이 사진마다 얼마나 «헷갈리는지» 를 재서 그림판의 «헷갈리는 사진 먼저» 순서를 만든다 (MaskAL 2022 의 불확실성 우선 라벨링)
"""작성: 2026-09-24
실행: CUDA_VISIBLE_DEVICES=5 IMGSZ=1280 LABELTOOL_DATA_ROOT=$(cat ../../app/logs/last_data_root) ~/venvs/labelai/bin/python uncertainty.py <best.pt> [--limit N]
결과: data/<fruit>/uncertainty.json 과 app/static/paint/unc/<fruit>.json (같은 내용)
  {stem: {"unc": 0~1, "sure": 확신 열매 수(점수≥0.5), "unsure": 애매한 열매 수(0.1~0.5), "conf": 확신 열매 평균 점수}}
  unc = 애매한 열매 비율 × 0.7 + (1 − 확신 열매 평균 점수) × 0.3 — 높을수록 사람이 먼저 봐야 할 사진.
사람 라벨·초벌 파일은 건드리지 않는다(읽지도 않는다).
"""
import json, os, sys
import numpy as np
from ultralytics import YOLO
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from core.paths import DATA_DIR, img_path, stems_of     # noqa: E402

FR = ["apple", "blueberry", "grape", "peach"]
model = YOLO(sys.argv[1])
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
IMGSZ = int(os.environ.get("IMGSZ", 1280))
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x] or FR
STATIC = os.path.join(HERE, "..", "..", "app", "static", "paint", "unc")
os.makedirs(STATIC, exist_ok=True)
for ci, f in enumerate(FR):
    if f not in ONLY:
        continue
    stems = stems_of(f)[:LIMIT] if LIMIT else stems_of(f)
    res = {}
    for k in range(0, len(stems), 8):
        chunk = stems[k:k + 8]
        rs = model.predict([img_path(f, s) for s in chunk], imgsz=IMGSZ, conf=0.1, classes=[ci], verbose=False, max_det=1000)
        for s, r in zip(chunk, rs):
            c = r.boxes.conf.cpu().numpy() if r.boxes is not None else np.zeros(0)
            sure, unsure = c[c >= 0.5], c[(c >= 0.1) & (c < 0.5)]
            ratio = len(unsure) / max(1, len(sure) + len(unsure))
            mconf = float(sure.mean()) if len(sure) else 0.0
            res[s] = {"unc": round(0.7 * ratio + 0.3 * (1 - mconf), 4), "sure": int(len(sure)),
                      "unsure": int(len(unsure)), "conf": round(mconf, 3)}
        print(f, min(k + 8, len(stems)), "/", len(stems), flush=True)
    txt = json.dumps(res, ensure_ascii=False)
    for p in (os.path.join(DATA_DIR, f, "uncertainty.json"), os.path.join(STATIC, f + ".json")):
        with open(p + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(p + ".tmp", p)
print("끝")
