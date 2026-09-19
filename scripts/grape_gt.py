"""포도 «정답» 송이 인스턴스 — CERTH 배포 COCO 어노테이션(RLE)을 읽는다.

CERTH_annotations.zip 안에 **송이별 인스턴스 마스크**가 들어 있다 (2026-08-10 확인).
  mimc_train 2,000장 7,959 · mimc_valid 251장 914 · mimc_test 251장 959
  = 2,502장 **9,832송이** (장당 3.93)  ← 논문 Table 1 의 "9,832 bunches" 와 일치

⛔ 왜 이게 필요한가 — 이진 마스크를 connected components 로 세면 **15,102개**가 나온다.
   정답보다 54% 많다. 잎·가지가 송이를 가려 **한 송이가 두세 조각으로 끊긴 것**을
   따로 세기 때문이다. 인스턴스 어노테이션은 조각이 몇 개든 한 송이로 묶여 있다.

카테고리 3개(Immature / Semi Mature / Mature)는 성숙도 구분일 뿐 전부 «송이»다.
팀 표준 마스크도 3클래스를 하나로 합친 것이므로 성숙도 구분 없이 전부 센다.

RLE 는 COCO **압축 문자열** 형식이고 `pycocotools` 가 이 서버에 없어서 직접 푼다
(LEB128 비슷한 가변길이 부호 + 이전 run 과의 차분. 원본 구현 rleFrString 과 같은 규칙).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path("/data/project/2026summer/kds0206")
ANN_DIR = ROOT / "semantic-segmentation/data/certh_annotations"   # 없으면 zip 에서 풀어 씀
ZIP = ROOT / "연구실 블루베리/_서버업로드용/CERTH_annotations.zip"
SPLITS = ("mimc_train_images.json", "mimc_valid_images.json", "mimc_test_images.json")


def rle_counts_from_str(s: str) -> list[int]:
    """COCO 압축 RLE 문자열 -> run 길이 목록."""
    cnts: list[int] = []
    p, m = 0, 0
    n = len(s)
    while p < n:
        x, k, more = 0, 0, True
        while more:
            c = ord(s[p]) - 48
            x |= (c & 0x1F) << (5 * k)
            more = bool(c & 0x20)
            p += 1
            k += 1
            if not more and (c & 0x10):
                x |= -1 << (5 * k)
        if m > 2:
            x += cnts[m - 2]
        cnts.append(x)
        m += 1
    return cnts


def rle_runs(seg: dict) -> tuple[np.ndarray, np.ndarray, int, int]:
    """(전경 run 의 시작 위치, 길이, h, w). 위치는 **열 우선(Fortran)** 평탄 인덱스."""
    h, w = seg["size"]
    counts = seg["counts"]
    if isinstance(counts, (bytes, bytearray)):
        counts = counts.decode()
    c = np.asarray(rle_counts_from_str(counts) if isinstance(counts, str) else counts, np.int64)
    ends = np.cumsum(c)
    starts = ends - c
    # counts 는 배경으로 시작해 배경/전경이 번갈아 나온다 → 홀수 번째가 전경
    fg = np.arange(len(c)) % 2 == 1
    return starts[fg], c[fg], h, w


@lru_cache(maxsize=1)
def _index() -> dict:
    """stem -> [segmentation(dict), ...]"""
    src = ANN_DIR if ANN_DIR.is_dir() else None
    data = {}
    if src is None:                      # zip 에서 바로 읽는다 (풀지 않음)
        import zipfile
        with zipfile.ZipFile(ZIP) as z:
            for f in SPLITS:
                data[f] = json.loads(z.read(f"annotations/{f}").decode())
    else:
        for f in SPLITS:
            data[f] = json.loads((src / f).read_text())

    out: dict[str, list] = {}
    for f, d in data.items():
        by_id = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
        for im in d["images"]:
            out.setdefault(Path(im["file_name"]).stem, [])
        for a in d["annotations"]:
            out[by_id[a["image_id"]]].append(a["segmentation"])
    return out


def has(stem: str) -> bool:
    return stem in _index()


def n_objects(stem: str) -> int:
    return len(_index().get(stem, ()))


def label_map(stem: str, H: int, W: int) -> tuple[np.ndarray, np.ndarray]:
    """정답 송이를 (H, W) 라벨맵으로. 원본(3840x2160)에서 풀고 정수배로 줄인다."""
    segs = _index().get(stem)
    if not segs:
        return np.zeros((H, W), np.int32), np.zeros(0, int)

    h0, w0 = segs[0]["size"]
    flat = np.zeros(h0 * w0, np.int32)
    for i, seg in enumerate(segs, start=1):
        starts, lens, _, _ = rle_runs(seg)
        for s, l in zip(starts, lens):
            flat[s:s + l] = i
    lab = flat.reshape((h0, w0), order="F")

    if (h0, w0) != (H, W):
        ys = (np.arange(H) * (h0 / H)).astype(int).clip(0, h0 - 1)
        xs = (np.arange(W) * (w0 / W)).astype(int).clip(0, w0 - 1)
        lab = lab[np.ix_(ys, xs)]
    idx = np.unique(lab)
    return lab.astype(np.int32), idx[idx > 0]


def totals() -> tuple[int, int]:
    ix = _index()
    return len(ix), sum(len(v) for v in ix.values())


def props(stem: str, H: int, W: int) -> tuple[np.ndarray, np.ndarray]:
    """통계용 — 라벨맵을 만들지 않고 개체별 (넓이, 중심)만 계산한다.

    전수 카운팅에서 2,502장 × 8.3M 픽셀을 다 펼치면 느리고 메모리도 크다.
    RLE run 은 «열 우선» 평탄 인덱스이므로 인덱스에서 행/열을 바로 뽑아 합산할 수 있다.
    반환 좌표·넓이는 (H, W) 격자 기준으로 환산한 값.
    """
    segs = _index().get(stem)
    if not segs:
        return np.zeros(0, float), np.zeros((0, 2))

    h0, w0 = segs[0]["size"]
    sy, sx = H / h0, W / w0
    areas, cents = [], []
    for seg in segs:
        starts, lens, _, _ = rle_runs(seg)
        if len(starts) == 0:
            areas.append(0.0)
            cents.append((0.0, 0.0))
            continue
        # 한 run 은 같은 열 안에서 이어지는 행들 (열 우선)
        cols = starts // h0
        rows0 = starts % h0
        n = lens.astype(np.int64)
        area = float(n.sum())
        # 행 합 = sum_{k=0..n-1}(rows0 + k) = n*rows0 + n(n-1)/2
        row_sum = float((n * rows0 + n * (n - 1) // 2).sum())
        col_sum = float((n * cols).sum())
        areas.append(area * sy * sx)
        cents.append((row_sum / area * sy, col_sum / area * sx))
    return np.asarray(areas, float), np.asarray(cents, float)


if __name__ == "__main__":
    n_img, n_obj = totals()
    print(f"포도 정답: {n_img}장 {n_obj}송이 (장당 {n_obj / n_img:.2f})")
