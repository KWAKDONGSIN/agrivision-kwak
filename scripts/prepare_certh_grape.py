# CERTH 포도 데이터셋(COCO RLE)을 우리 저장소 형식(images/ + 이진 마스크 PNG)으로 변환
"""
CERTH Grape Dataset -> 우리 이진 세그멘테이션 형식으로 변환.

원본
    CERTH_images.zip       2,502장 PNG (2160x3840 세로형)
    CERTH_annotations.zip  COCO 형식, RLE 마스크, 클래스 3개(Immature/Semi Mature/Mature)

출력 (make_folds.py 가 바로 먹을 수 있는 구조)
    {OUT}/images/*.png      리사이즈된 이미지
    {OUT}/masks/*.png       이진 마스크 (0=배경, 255=포도)
    {OUT}/prepare_manifest.json   무엇을 어떻게 뽑았는지 기록

성숙도 3클래스는 전부 하나로 합칩니다. 우리 연구는 과일/배경 이진 분할이기 때문입니다.

----------------------------------------------------------------------------
리사이즈 정책 (2026-07-30 교수님 지시 ⑦)
----------------------------------------------------------------------------
녹취록 55:23  "화소를 튼 비율은 유지를 해가지고 ... 768,768인가 그 정도가
              가장 많이 쓰는 화소잖아요"
녹취록 56:31  "화소가 아니고 그 이미지 비율에 따라 크롭을 해야 될 것 같아요"

--resize 는 **긴 변** 기준입니다. CERTH 는 가로:세로 = 2160:3840 = 1:1.778 이므로
    --resize 1024  ->  576 x 1024
이고 픽셀 수는 576*1024 = 589,824 = **768x768 과 정확히 같습니다.**
즉 "비율은 유지하면서 768x768 정도의 화소로 노멀라이즈"라는 지시를
가로세로비를 왜곡하지 않고 만족시키는 값이 1024 입니다. (기본값)

또한 학습 크롭이 512x512 이므로 576x1024 이면 **패딩이 전혀 생기지 않습니다.**
(원본 2160x3840 을 그대로 쓰면 512 크롭은 긴 변의 13%밖에 안 되는 조각이 됩니다.)

----------------------------------------------------------------------------
사용법
----------------------------------------------------------------------------
    # 토이 예제 — train 에서 100장만 무작위로 (0730 팀 합의)
    python tools/prepare_certh_grape.py \
        --images .../CERTH_images.zip --ann .../CERTH_annotations.zip \
        --out .../certh_grape_toy100 \
        --splits mimc_train_images.json --sample 100 --seed 42

    # 전체 2,502장
    python tools/prepare_certh_grape.py \
        --images .../CERTH_images.zip --ann .../CERTH_annotations.zip \
        --out .../certh_grape_full

zip 을 풀지 않고 zip 째로 읽을 수 있습니다. pycocotools 없이 동작합니다(RLE 디코더 내장).
"""
import argparse
import io
import json
import os
import random
import re
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None       # 2160x3840 대용량 이미지 경고 방지


def rle_decode(rle):
    """COCO RLE -> (H, W) 이진 마스크. counts 는 list(비압축) 또는 LEB128 문자열(압축)."""
    h, w = rle["size"]
    counts = rle["counts"]
    if isinstance(counts, list):
        nums = counts
    else:
        if isinstance(counts, str):
            counts = counts.encode("ascii")
        nums, p = [], 0
        while p < len(counts):
            x, k, more = 0, 0, True
            while more:
                c = counts[p] - 48
                x |= (c & 0x1F) << (5 * k)
                more = bool(c & 0x20)
                p += 1
                k += 1
                if not more and (c & 0x10):
                    x |= -1 << (5 * k)
            if len(nums) > 2:
                x += nums[-2]
            nums.append(x)

    mask = np.zeros(h * w, dtype=np.uint8)
    pos, val = 0, 0
    for cnt in nums:
        if val:
            mask[pos:pos + cnt] = 1
        pos += cnt
        val ^= 1
        if pos >= h * w:
            break
    return mask.reshape((h, w), order="F")      # RLE 은 열 우선


def preferred_dirs(split_file):
    """주석 json 파일명 -> 그 주석이 가리키는 이미지 폴더(우선 탐색할 경로 조각).

    CERTH_images.zip 의 폴더 구조
        images/multiple-instance-multiple-class/{train_set,valid_set,test_set}/
        images/single-instance-one-class/
    주석
        annotations/mimc_{train,valid,test}_images.json   -> mimc 의 해당 _set 폴더
        annotations/single-instance-one-class.json        -> single-instance-one-class 폴더

    같은 basename 이 두 폴더에 있는 경우(2026-09-16 확인: 15개 stem)를
    «주석이 온 split 의 폴더» 로 결정하기 위한 표입니다.
    """
    stem = os.path.basename(str(split_file))
    if stem.endswith(".json"):
        stem = stem[:-5]
    m = re.match(r"^mimc_(train|valid|test)(?:_images)?$", stem)
    if m:
        return [f"multiple-instance-multiple-class/{m.group(1)}_set/"]
    if "single-instance" in stem:
        return ["single-instance-one-class/"]
    return []


class Source:
    """zip 이든 폴더든 같은 방식으로 파일을 읽게 해주는 얇은 래퍼.

    주의: basename 이 zip 안에서 유일하지 않습니다(2026-09-16 발견).
    그래서 basename -> 전체경로 «목록» 을 들고 있다가, find() 에 prefer 를 받아
    해당 split 폴더의 것을 먼저 고릅니다. prefer 없이 충돌하면 경고를 찍습니다.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.zf = zipfile.ZipFile(path) if self.path.suffix == ".zip" else None
        if self.zf:
            names = [n for n in self.zf.namelist() if not n.endswith("/")]
        else:
            names = [str(p.relative_to(self.path)).replace("\\", "/")
                     for p in self.path.rglob("*") if p.is_file()]
        self._names = names
        # basename -> 전체경로 목록 (선형 탐색을 없애려고 미리 인덱싱)
        self._by_base = {}
        for n in names:
            self._by_base.setdefault(os.path.basename(n), []).append(n)
        self.ambiguous = {b: v for b, v in self._by_base.items() if len(v) > 1}

    def candidates(self, basename):
        return list(self._by_base.get(basename, []))

    def find(self, basename, prefer=None, warn=True):
        """(전체경로, 충돌여부) 를 돌려준다. 없으면 (None, False).

        prefer 는 우선 탐색할 경로 조각 목록(preferred_dirs() 의 결과).
        prefer 로 딱 하나가 걸리면 그것을 쓰고, 그래도 여러 개면 경로 사전순 첫 번째를 쓰되
        경고를 출력한다(어느 것을 썼는지는 manifest 의 source_path 에 남는다).
        """
        cands = self._by_base.get(basename)
        if not cands:
            return None, False
        conflict = len(cands) > 1
        if not conflict:
            return cands[0], False
        for frag in (prefer or []):
            hit = [c for c in cands if frag in c]
            if len(hit) == 1:
                return hit[0], True
            if len(hit) > 1:
                cands = hit
                break
        chosen = sorted(cands)[0]
        if warn:
            print(f"[경고] 파일명 충돌: {basename} 가 {len(self._by_base[basename])}곳에 있음 "
                  f"{self._by_base[basename]} -> {chosen} 를 사용 "
                  f"(prefer={prefer})", flush=True)
        return chosen, True

    def read(self, name):
        if self.zf:
            return self.zf.read(name)
        return (self.path / name).read_bytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="CERTH_images.zip 또는 압축 푼 폴더")
    ap.add_argument("--ann", required=True, help="CERTH_annotations.zip 또는 압축 푼 폴더")
    ap.add_argument("--out", required=True, help="출력 폴더 (images/, masks/ 생성)")
    ap.add_argument("--resize", type=int, default=1024,
                    help="긴 변 기준 리사이즈 픽셀. 0이면 원본 유지. "
                         "기본 1024 = 576x1024 = 768x768 과 같은 화소수 (교수님 지시 ⑦)")
    ap.add_argument("--splits", nargs="+",
                    default=["mimc_train_images.json", "mimc_valid_images.json",
                             "mimc_test_images.json"],
                    help="사용할 어노테이션 파일들")
    ap.add_argument("--sample", type=int, default=0,
                    help="N장만 무작위 추출 (0730 팀 합의: train 에서 100장)")
    ap.add_argument("--seed", type=int, default=42, help="추출 시드")
    ap.add_argument("--stems", default="",
                    help="쉼표로 구분한 stem 목록만 변환 (예: 104,1080). 검증용.")
    args = ap.parse_args()

    img_src = Source(args.images)
    ann_src = Source(args.ann)

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "masks").mkdir(parents=True, exist_ok=True)

    # 어노테이션을 이미지 파일명 기준으로 모은다
    per_image = {}
    split_of = {}          # 이미지 파일명 -> 그 주석이 온 split 파일 (폴더 선택에 씀)
    total_ann = 0
    used_splits = []
    for sp in args.splits:
        name, _ = ann_src.find(sp)
        if not name:
            print(f"[경고] 어노테이션 파일 없음: {sp}")
            continue
        d = json.loads(ann_src.read(name))
        byid = {i["id"]: i["file_name"] for i in d["images"]}
        for a in d["annotations"]:
            fn = byid.get(a["image_id"])
            if fn:
                if split_of.setdefault(fn, sp) != sp:
                    print(f"[경고] {fn} 이 여러 split 에 있음: {split_of[fn]} / {sp} "
                          f"-> {split_of[fn]} 폴더를 우선함")
                per_image.setdefault(fn, []).append(a)
        total_ann += len(d["annotations"])
        used_splits.append({"file": sp, "images": len(d["images"]),
                            "annotations": len(d["annotations"])})
        print(f"[정보] {sp}: 이미지 {len(d['images'])}장, 어노테이션 {len(d['annotations'])}개")

    files = sorted(per_image.keys())
    if args.stems:
        want = {x.strip() for x in args.stems.split(",") if x.strip()}
        files = [f for f in files if Path(f).stem in want]
        missing = want - {Path(f).stem for f in files}
        print(f"[정보] --stems 로 {len(files)}장만 변환" +
              (f" (주석에 없는 stem: {sorted(missing)})" if missing else ""))
    if args.sample and args.sample < len(files):
        rng = random.Random(args.seed)
        files = sorted(rng.sample(files, args.sample))
        print(f"[정보] 무작위 추출 {len(files)}장 (seed={args.seed})")

    print(f"[정보] 변환 대상 {len(files)}장 (어노테이션 총 {total_ann}개)")

    done, skipped, empty = 0, 0, 0
    n_conflict = 0
    records = []
    for i, fn in enumerate(files, 1):
        prefer = preferred_dirs(split_of.get(fn, ""))
        src_name, conflict = img_src.find(fn, prefer=prefer)
        if not src_name:
            skipped += 1
            continue
        if conflict:
            n_conflict += 1
            print(f"[알림] 파일명 충돌 해소: {fn} (주석 {split_of.get(fn)}) -> {src_name}",
                  flush=True)

        im = Image.open(io.BytesIO(img_src.read(src_name))).convert("RGB")
        W, H = im.size

        mask = np.zeros((H, W), dtype=np.uint8)
        n_inst = 0
        for a in per_image[fn]:
            seg = a.get("segmentation")
            if not isinstance(seg, dict):
                continue                      # 폴리곤 형식은 이 데이터셋에 없음
            m = rle_decode(seg)
            if m.shape != (H, W):
                continue
            mask |= m                          # 성숙도 클래스 구분 없이 전부 합침
            n_inst += 1

        if mask.sum() == 0:
            empty += 1
            continue

        fg_ratio_src = float(mask.mean())

        if args.resize:
            scale = args.resize / max(W, H)
            if scale < 1.0:
                nw, nh = int(round(W * scale)), int(round(H * scale))
                im = im.resize((nw, nh), Image.BILINEAR)
                mask = np.array(Image.fromarray(mask * 255).resize((nw, nh), Image.NEAREST))
                mask = (mask > 127).astype(np.uint8)

        stem = Path(fn).stem
        im.save(out / "images" / f"{stem}.png")
        Image.fromarray((mask * 255).astype(np.uint8)).save(out / "masks" / f"{stem}.png")
        done += 1
        records.append({"file": fn, "stem": stem,
                        "source_path": src_name,
                        "source_split": split_of.get(fn, ""),
                        "name_conflict": bool(conflict),
                        "conflict_candidates": img_src.candidates(fn) if conflict else [],
                        "src_size": [W, H], "out_size": list(im.size),
                        "instances": n_inst,
                        "fg_ratio_src": round(fg_ratio_src, 6),
                        "fg_ratio_out": round(float(mask.mean()), 6)})

        if i % 25 == 0:
            print(f"  {i}/{len(files)} 처리 중...", flush=True)

    manifest = {
        "source_images": str(args.images),
        "source_annotations": str(args.ann),
        "splits_used": used_splits,
        "resize_long_edge": args.resize,
        "sample": args.sample,
        "seed": args.seed,
        "stems": args.stems,
        "converted": done, "image_missing": skipped, "empty_mask": empty,
        "name_conflicts_resolved": n_conflict,
        "ambiguous_basenames_in_source": {b: v for b, v in sorted(img_src.ambiguous.items())},
        "records": records,
    }
    (out / "prepare_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if records:
        fg = [r["fg_ratio_out"] for r in records]
        inst = [r["instances"] for r in records]
        print(f"\n[통계] 전경비율 평균 {100*sum(fg)/len(fg):.2f}% "
              f"(최소 {100*min(fg):.2f}% / 최대 {100*max(fg):.2f}%)")
        print(f"[통계] 장당 송이 수 평균 {sum(inst)/len(inst):.2f} "
              f"(최소 {min(inst)} / 최대 {max(inst)})")
        print(f"[통계] 출력 해상도 {records[0]['out_size'][0]}x{records[0]['out_size'][1]}")

    print(f"\n[완료] 변환 {done}장 · 이미지 없음 {skipped}장 · 마스크 빈 것 {empty}장 "
          f"· 파일명 충돌 해소 {n_conflict}장")
    print(f"[출력] {out/'images'}  /  {out/'masks'}  /  {out/'prepare_manifest.json'}")


if __name__ == "__main__":
    main()
