"""4과일 **전 장**에 개체를 색칠한 사본을 만든다 (4,823장).

그림에 넣는 샘플 몇 장만이 아니라 «전수»를 눈으로 확인할 수 있게 하는 산출물이다.
개체 정의는 통계와 완전히 같다 (`instance_split.label_instances`) —
  사과   마스크 픽셀값 = 인스턴스 ID (정답)
  복숭아 peach-data COCO 폴리곤 (정답)
  포도   CERTH COCO RLE, 송이 단위 (정답)
  블루베리 정답이 없어 거리변환+watershed 분리 결과

색은 «개체 번호»에 따라 정해지므로 같은 색 = 같은 개체다. 인접한 개체가 다른 색이면
그 둘을 따로 세고 있다는 뜻이다.

출력  datasets_overlay_2mp/<과일>/<원본파일명>.jpg   (원본은 건드리지 않는다)
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
from pathlib import Path

import numpy as np
from PIL import Image

from instance_split import label_instances

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"
OUT = ROOT / "datasets_overlay_2mp"

FRUITS = ["blueberry", "apple", "peach", "grape"]
ALPHA = 0.55
QUALITY = 85


def palette(n: int, seed: int = 0) -> np.ndarray:
    """개체 번호 -> 색. 0번(배경)은 검정. 인접 번호가 확 다른 색이 되게 섞는다."""
    rng = np.random.default_rng(seed)
    hues = (np.arange(n) * 0.61803398875) % 1.0          # 황금비로 골고루
    sat = 0.65 + rng.random(n) * 0.3
    val = 0.75 + rng.random(n) * 0.25
    i = (hues * 6).astype(int)
    f = hues * 6 - i
    p, q, t = val * (1 - sat), val * (1 - f * sat), val * (1 - (1 - f) * sat)
    r = np.choose(i % 6, [val, q, p, p, t, val])
    g = np.choose(i % 6, [t, val, val, q, p, p])
    b = np.choose(i % 6, [p, p, t, val, val, q])
    col = (np.stack([r, g, b], 1) * 255).astype(np.uint8)
    col[0] = 0
    return col


def one(args) -> tuple[str, int]:
    fruit, ip, mp_, op = args
    img = np.array(Image.open(ip).convert("RGB"))
    raw = np.array(Image.open(mp_))
    if raw.ndim == 3:
        raw = raw[..., 0]

    lab, idx, _ = label_instances(raw, fruit, stem=Path(mp_).stem, prefer_gt=True)
    keep = np.isin(lab, idx)
    if keep.any():
        # 라벨 번호를 1..N 으로 다시 매겨 색이 골고루 퍼지게 한다
        remap = np.zeros(int(lab.max()) + 1, np.int32)
        remap[idx] = np.arange(1, len(idx) + 1)
        small = remap[np.where(keep, lab, 0)]
        col = palette(len(idx) + 1)[small]
        out = img.copy()
        out[keep] = (img[keep] * (1 - ALPHA) + col[keep] * ALPHA).astype(np.uint8)
    else:
        out = img

    Path(op).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(op, "JPEG", quality=QUALITY, optimize=True)
    return fruit, int(len(idx))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fruits", nargs="+", default=FRUITS)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    outroot = Path(a.out)
    grand_img = grand_obj = 0
    lines = []
    for fruit in a.fruits:
        masks = sorted(p for p in (POOL / fruit / "masks").iterdir() if p.is_file())
        if a.limit:
            masks = masks[:a.limit]
        imgs = {p.stem: p for p in (POOL / fruit / "images").iterdir() if p.is_file()}
        tasks = [(fruit, str(imgs[m.stem]), str(m), str(outroot / fruit / f"{m.stem}.jpg"))
                 for m in masks]
        print(f"[{fruit}] {len(tasks)}장 색칠 시작...", flush=True)
        with mp.Pool(a.workers) as pool:
            res = pool.map(one, tasks, chunksize=4)
        n_obj = sum(r[1] for r in res)
        grand_img += len(res)
        grand_obj += n_obj
        lines.append(f"{fruit:10s} {len(res):5d}장  {n_obj:7,d}개")
        print(f"  → {len(res)}장 완료, 개체 {n_obj:,}개", flush=True)

    readme = outroot / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "# datasets_overlay_2mp — 개체를 색칠한 전수 사본\n\n"
        "작성: 2026-08-10\n\n"
        f"팀 표준본 `datasets_resized_2mp/` 의 **{grand_img:,}장 전부**에 개체를 색칠한 것입니다.\n"
        "색이 다르면 서로 다른 개체입니다. 원본은 손대지 않았습니다.\n\n"
        "```\n" + "\n".join(lines) + f"\n{'합계':10s} {grand_img:5d}장  {grand_obj:7,d}개\n```\n\n"
        "## 개체를 무엇으로 셌나\n\n"
        "| 과일 | 근거 |\n|---|---|\n"
        "| 사과 | 마스크 픽셀값 = 인스턴스 ID (정답) |\n"
        "| 복숭아 | peach-data COCO 폴리곤 (정답) |\n"
        "| 포도 | CERTH COCO 인스턴스 마스크, 송이 단위 (정답) |\n"
        "| 블루베리 | 정답 라벨이 없어 거리변환+watershed 분리 |\n\n"
        "숫자는 `semantic-segmentation/output/object_stats_4fruits_split.json` 과 같습니다.\n"
        "재생성: `python tools/make_overlays_all.py`\n",
        encoding="utf-8")

    print(f"\n합계 {grand_img:,}장 / 개체 {grand_obj:,}개")
    print(f"저장: {outroot}")


if __name__ == "__main__":
    main()
