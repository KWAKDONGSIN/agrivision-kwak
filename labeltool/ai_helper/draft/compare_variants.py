# -*- coding: utf-8 -*-
# 초벌을 더 좋게 만드는 방법들(TTA · SAM 상자 다듬기 · 타일 추론)을 원본 정답과 비교해 고른다 — 촬영 단위 검증 사진만 쓴다
"""작성: 2026-09-23
실행: CUDA_VISIBLE_DEVICES=5 YOLO_OFFLINE=1 ~/venvs/labelai/bin/python compare_variants.py A,B,D
      (C = SAM 다듬기는 SAM 을 같은 GPU 에 올린다)
모델: runs/eval_v3/weights/best.pt (검증 묶음을 학습에 안 쓴 모델)
정답: 사과 = 원본 번호 마스크(툴 load_inst) · 포도 = CERTH instances_seed · 복숭아 = instances_gt
지표(사진마다 → 평균): 열매 짝맞춤(IoU≥0.5) 정밀도·재현율·F1 · 짝지은 열매의 마스크 IoU · Boundary IoU(Cheng 2021 방식, 띠 폭 3화소 — 기본 2% 는 작은 열매에서 마스크 IoU 와 같아져서 바꿈) · 개수 오차
결과: variants_result.csv (한 줄 = 과일×방법)
"""
import os, sys, csv, time
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "app"))
from core.paths import DATA_DIR, img_path          # noqa: E402
from api.instances import load_inst                  # noqa: E402
from ultralytics import YOLO                         # noqa: E402

VAL = os.path.join(HERE, "..", "yolo_ds_v3", "labels", "val")
FR = {"apple": 0, "grape": 2, "peach": 3}
MODEL = YOLO(os.path.join(HERE, "runs", "eval_v3", "weights", "best.pt"))
SAM = None


def gt_of(f, s):
    if f == "apple":
        return load_inst(f, s)[0]
    sub = "instances_seed" if f == "grape" else "instances_gt"
    return np.array(Image.open(os.path.join(DATA_DIR, f, sub, s + ".png")))


def boundary(m, d):
    """마스크 안쪽 d 화소 띠(Boundary IoU 정의)."""
    er = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=d)
    return m & ~er.astype(bool)


def masks_from(r, H, W):
    if r.masks is None:
        return np.zeros((0, H, W), bool), np.zeros(0), np.zeros((0, 4))
    return r.masks.data.cpu().numpy() > 0.5, r.boxes.conf.cpu().numpy(), r.boxes.xyxy.cpu().numpy()


def nms_masks(ms, sc, thr=0.5):
    keep = []
    for i in np.argsort(-sc):
        if all(((ms[i] & ms[j]).sum() / max(1, (ms[i] | ms[j]).sum())) < thr for j in keep):
            keep.append(i)
    return ms[keep], sc[keep]


def predict(f, path, how):
    im = cv2.imread(path); H, W = im.shape[:2]
    kw = dict(imgsz=1280, conf=0.25, retina_masks=True, classes=[FR[f]], verbose=False, max_det=1000)
    if how == "B":
        kw["augment"] = True
    ms, sc, bx = masks_from(MODEL.predict(im, **kw)[0], H, W)
    if how == "D":                       # 타일 2×2(겹침 20%) + 전체 → 마스크 NMS
        th, tw = int(H * 0.6), int(W * 0.6)
        allm, alls = [ms], [sc]
        for y0 in (0, H - th):
            for x0 in (0, W - tw):
                tm, ts, _ = masks_from(MODEL.predict(im[y0:y0 + th, x0:x0 + tw], **kw)[0], th, tw)
                full = np.zeros((len(tm), H, W), bool); full[:, y0:y0 + th, x0:x0 + tw] = tm
                allm.append(full); alls.append(ts)
        ms, sc = nms_masks(np.concatenate(allm), np.concatenate(alls))
    if how == "C" and len(bx):           # SAM 상자 다듬기: YOLO 상자 → SAM 마스크
        global SAM
        if SAM is None:
            from ultralytics.models.sam import SAM2Predictor
            SAM = SAM2Predictor(overrides=dict(model=os.path.join(HERE, "..", "weights", "sam2.1_b.pt"),
                                               device=0, conf=0.0, verbose=False, save=False))
        SAM.set_image(im)
        r = SAM(bboxes=bx.tolist(), multimask_output=False)[0]
        if r.masks is not None and len(r.masks.data) == len(ms):
            sm = r.masks.data.cpu().numpy() > 0
            # SAM 이 상자 안을 거의 못 채우면(열매 아님) YOLO 마스크를 그대로 둔다
            ok = np.array([(sm[i] & ms[i]).sum() / max(1, (sm[i] | ms[i]).sum()) > 0.3 for i in range(len(ms))])
            ms = np.where(ok[:, None, None], sm, ms)
    return ms


def _bb(m):
    ys, xs = np.nonzero(m)
    return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) else None


def score(pred, G):
    H, W = G.shape; d = 3   # 경계 띠 3화소 — 논문 기본(대각선 2% ≈ 44화소)은 사과(지름 약 40화소)보다 커서 마스크 IoU 와 같아진다
    ids = [v for v in np.unique(G) if v]
    gts = [G == v for v in ids]
    gbb = [_bb(g) for g in gts]
    pred = [p for p in pred if p.any()]
    used, ious, bious = set(), [], []
    for i in np.argsort([-p.sum() for p in pred]):
        pb = _bb(pred[i]); best, bj, bbox = 0, -1, None
        for j, gb in enumerate(gbb):
            if j in used or gb is None or gb[0] >= pb[2] or pb[0] >= gb[2] or gb[1] >= pb[3] or pb[1] >= gb[3]:
                continue
            x0, y0, x1, y1 = min(pb[0], gb[0]), min(pb[1], gb[1]), max(pb[2], gb[2]), max(pb[3], gb[3])
            a, g = pred[i][y0:y1, x0:x1], gts[j][y0:y1, x0:x1]
            v = (a & g).sum() / max(1, (a | g).sum())
            if v > best:
                best, bj, bbox = v, j, (x0, y0, x1, y1)
        if best >= 0.5:
            used.add(bj); ious.append(best)
            x0, y0, x1, y1 = bbox; x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
            a, g = pred[i][y0:y1 + 1, x0:x1 + 1], gts[bj][y0:y1 + 1, x0:x1 + 1]
            pa, ga = boundary(a, d), boundary(g, d)
            bious.append((pa & ga).sum() / max(1, (pa | ga).sum()))
    tp = len(used); P = tp / max(1, len(pred)); R = tp / max(1, len(gts))
    return dict(P=P, R=R, F1=2 * P * R / max(1e-9, P + R), mIoU=np.mean(ious) if ious else 0,
                bIoU=np.mean(bious) if bious else 0, cnt_err=abs(len(pred) - len(gts)), n_gt=len(gts))


def main():
    hows = (sys.argv[1] if len(sys.argv) > 1 else "A,B,C,D").split(",")
    out = os.path.join(HERE, "variants_result_%s.csv" % "".join(hows))
    rows = []
    for f in FR:
        stems = sorted(n.split("__", 1)[1][:-4] for n in os.listdir(VAL) if n.startswith(f + "__"))
        stems = stems[::max(1, len(stems) // 120)][:120]      # 과일마다 최대 120장(고르게)
        for how in hows:
            t = time.time(); acc = []
            for s in stems:
                acc.append(score(predict(f, img_path(f, s), how), gt_of(f, s)))
            m = {k: float(np.mean([a[k] for a in acc])) for k in ("P", "R", "F1", "mIoU", "bIoU")}
            m["cnt_err_pct"] = 100 * sum(a["cnt_err"] for a in acc) / max(1, sum(a["n_gt"] for a in acc))
            rows.append(dict(fruit=f, how=how, n=len(stems), sec_per_img=round((time.time() - t) / len(stems), 2),
                             **{k: round(v, 4) for k, v in m.items()}))
            print(rows[-1], flush=True)
    with open(out, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("끝", out)


if __name__ == "__main__":
    main()
