#!/usr/bin/env python
"""CERTH 포도 데이터셋의 **원 논문 분할**을 심볼릭 링크로 재현한다.

CERTH_annotations.zip 안에는 분할이 이미 세 파일로 나뉘어 있다.
    mimc_train_images.json  2,000장
    mimc_valid_images.json    251장
    mimc_test_images.json     251장   (합 2,502장)

우리 팀 규칙은 7:1:2 5폴드지만, 원 논문과 숫자를 비교하려면 이 분할도 필요하다.
그래서 팀 폴드(cv1~cv5)와 **따로** official/ 로 만들어 둔다.

사용법
    python tools/make_grape_official_split.py \
        --pool .../datasets_resized_2mp/grape \
        --ann  .../share_grape_certh/CERTH_annotations.zip \
        --out  .../datasets_resized_2mp/splits/grape_2502/official
"""
from __future__ import annotations

import argparse
import io
import json
import os
import zipfile
from pathlib import Path

SPLIT_FILES = {
    "train": "mimc_train_images.json",
    "val": "mimc_valid_images.json",
    "test": "mimc_test_images.json",
}


def load_stems(ann: Path, fname: str) -> set[str]:
    """어노테이션 json 에서 이미지 파일명 stem 집합을 뽑는다. zip/폴더 둘 다 지원."""
    if ann.is_dir():
        cands = list(ann.rglob(fname))
        if not cands:
            raise SystemExit(f"[에러] {fname} 을 {ann} 에서 찾지 못했습니다.")
        data = json.loads(cands[0].read_text())
    else:
        with zipfile.ZipFile(ann) as z:
            name = next((n for n in z.namelist() if n.endswith(fname)), None)
            if name is None:
                raise SystemExit(f"[에러] {fname} 이 zip 안에 없습니다.")
            data = json.load(io.BytesIO(z.read(name)))
    return {Path(im["file_name"]).stem for im in data["images"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, help="images/ masks/ 가 있는 풀 폴더")
    ap.add_argument("--ann", required=True, help="CERTH_annotations.zip 또는 압축 푼 폴더")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pool, ann, out = Path(args.pool), Path(args.ann), Path(args.out)
    have = {p.stem for p in (pool / "images").iterdir() if p.suffix == ".png"}

    total_linked, missing_all = 0, {}
    for split, fname in SPLIT_FILES.items():
        stems = load_stems(ann, fname)
        usable = sorted(stems & have)
        missing = sorted(stems - have)
        if missing:
            missing_all[split] = missing
        for kind in ("images", "masks"):
            d = out / split / kind
            d.mkdir(parents=True, exist_ok=True)
            for s in usable:
                link, tgt = d / f"{s}.png", pool / kind / f"{s}.png"
                if link.is_symlink() or link.exists():
                    link.unlink()
                os.symlink(os.path.relpath(tgt, d), link)
        total_linked += len(usable)
        print(f"[{split:5}] {len(usable):>5}장 링크"
              + (f"  (풀에 없어 건너뜀 {len(missing)}장)" if missing else ""))

    with open(out / "official_split_manifest.json", "w") as f:
        json.dump({
            "source": str(ann),
            "split_files": SPLIT_FILES,
            "pool": str(pool),
            "linked_total": total_linked,
            "missing_from_pool": missing_all,
        }, f, indent=2, ensure_ascii=False)
    print(f"[저장] {out/'official_split_manifest.json'}  (총 {total_linked}장)")


if __name__ == "__main__":
    main()
