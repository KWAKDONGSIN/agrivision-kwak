"""복숭아 «정답» 인스턴스 — 배포된 COCO json 을 그대로 읽어 개체를 만든다.

복숭아에는 인스턴스 정답이 있다 (2026-08-10 곽동신 확인).
  연구실 블루베리/datasets_verified/peach_instance_segmentation/peach-data/{train,val,test}.json
  train 99장 805개 · val 13장 88개 · test 13장 84개  =  125장 977개 (장당 7.82)

그래서 복숭아는 사과와 같이 **정답으로 검증되는 데이터셋**이다.
watershed 로 세면 931개(장당 7.4)라 정답 대비 -4.7% 였다 → 정답을 쓴다.

주의할 점
  - train.json 의 file_name 은 **역슬래시**(`JPEGImages\\xxx.jpg`, 윈도우에서 만든 파일).
    그대로 Path().stem 하면 파일명이 통째로 남아 매칭이 깨진다. 반드시 `/` 로 바꿔 읽는다.
  - 폴리곤 좌표는 **원본 해상도** 기준이다. 팀 표준본은 리사이즈됐으므로 배율을 곱해 그린다.
  - 한 개체의 segmentation 이 여러 조각(잎에 가려 끊긴 것)이어도 **같은 라벨 번호**를 준다.
    이게 «가려져 끊긴 것을 따로 세는» 오류를 막아 준다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path, PurePosixPath

import numpy as np
from skimage.draw import polygon as sk_polygon

ROOT = Path("/data/project/2026summer/kds0206")
COCO_DIR = (ROOT / "연구실 블루베리/datasets_verified/peach_instance_segmentation/peach-data")
SPLITS = ("train.json", "val.json", "test.json")


@lru_cache(maxsize=1)
def _index() -> dict:
    """stem -> {"size": (w0, h0), "polys": [ [poly, poly, ...], ... ]}  (개체당 한 항목)"""
    out: dict[str, dict] = {}
    for f in SPLITS:
        d = json.loads((COCO_DIR / f).read_text())
        by_id = {}
        for im in d["images"]:
            stem = PurePosixPath(im["file_name"].replace("\\", "/")).stem
            by_id[im["id"]] = stem
            out.setdefault(stem, {"size": (im["width"], im["height"]), "polys": []})
        for a in d["annotations"]:
            stem = by_id[a["image_id"]]
            seg = a["segmentation"]
            if not isinstance(seg, list):        # RLE 는 이 데이터셋에 없다
                continue
            out[stem]["polys"].append([np.asarray(s, float).reshape(-1, 2) for s in seg])
    return out


def has(stem: str) -> bool:
    return stem in _index()


def n_objects(stem: str) -> int:
    """그 사진의 정답 개체 수 (그림을 그리지 않고 개수만 필요할 때)."""
    rec = _index().get(stem)
    return len(rec["polys"]) if rec else 0


def label_map(stem: str, H: int, W: int) -> tuple[np.ndarray, np.ndarray]:
    """정답 폴리곤을 (H, W) 라벨맵으로. 반환 = (라벨맵, 라벨번호들)"""
    rec = _index().get(stem)
    if rec is None:
        return np.zeros((H, W), np.int32), np.zeros(0, int)

    w0, h0 = rec["size"]
    sx, sy = W / w0, H / h0
    lab = np.zeros((H, W), np.int32)
    for i, parts in enumerate(rec["polys"], start=1):
        for pts in parts:
            if len(pts) < 3:
                continue
            cc = np.clip(pts[:, 0] * sx, 0, W - 1)
            rr = np.clip(pts[:, 1] * sy, 0, H - 1)
            yy, xx = sk_polygon(rr, cc, shape=(H, W))
            lab[yy, xx] = i
    idx = np.unique(lab)
    return lab, idx[idx > 0]


def totals() -> tuple[int, int]:
    """(장수, 개체 수) — 검증 문구에 쓸 합계."""
    ix = _index()
    return len(ix), sum(len(v["polys"]) for v in ix.values())


def props(stem: str, H: int, W: int) -> tuple[np.ndarray, np.ndarray]:
    """통계용 — 개체별 (넓이, 중심). 폴리곤을 개체 bbox 안에서만 래스터화한다."""
    rec = _index().get(stem)
    if rec is None:
        return np.zeros(0, float), np.zeros((0, 2))
    w0, h0 = rec["size"]
    sx, sy = W / w0, H / h0
    areas, cents = [], []
    for parts in rec["polys"]:
        pts = np.concatenate(parts, 0)
        cc_all = np.clip(pts[:, 0] * sx, 0, W - 1)
        rr_all = np.clip(pts[:, 1] * sy, 0, H - 1)
        r0, r1 = int(np.floor(rr_all.min())), int(np.ceil(rr_all.max())) + 1
        c0, c1 = int(np.floor(cc_all.min())), int(np.ceil(cc_all.max())) + 1
        sub = np.zeros((max(r1 - r0, 1), max(c1 - c0, 1)), bool)
        for p in parts:
            if len(p) < 3:
                continue
            cc = np.clip(p[:, 0] * sx, 0, W - 1) - c0
            rr = np.clip(p[:, 1] * sy, 0, H - 1) - r0
            yy, xx = sk_polygon(rr, cc, shape=sub.shape)
            sub[yy, xx] = True
        a = int(sub.sum())
        if a == 0:
            continue
        yy, xx = np.nonzero(sub)
        areas.append(float(a))
        cents.append((yy.mean() + r0, xx.mean() + c0))
    return np.asarray(areas, float), np.asarray(cents, float)


if __name__ == "__main__":
    n_img, n_obj = totals()
    print(f"복숭아 정답: {n_img}장 {n_obj}개 (장당 {n_obj / n_img:.2f})")
