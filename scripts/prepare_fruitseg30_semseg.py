"""FruitSeg30 원본을 우리 학습 폴더 구조로 재배치한다.

원본:  <raw>/<클래스>/Images/<n>.jpg  +  <raw>/<클래스>/Mask/<n>_mask.png
출력:  <out>/{train,val,test}/{images,masks}/<클래스>__<n>.{jpg,png}

하는 일
  1) 30개 클래스를 하나로 합친다 (과일 종류 구분 없이 '과일 vs 배경' 이진 분할).
     BlueberryDataset이 mask>0 을 1로 만들므로 마스크 값 변환은 필요 없다.
  2) train:val:test = 7:1:2 로 나누되 **클래스별로 따로 나눈다(층화 분할)**.
     전체를 통째로 섞어 자르면 어떤 과일이 test에만 몰릴 수 있기 때문.
  3) 파일 이름이 클래스마다 겹치므로(1.jpg가 30개) '<클래스>__<n>' 으로 바꾼다.
     마스크는 '<n>_mask.png' 라 이름이 어긋나는데, 링크 이름을 이미지 stem과
     맞춰 붙인다 (BlueberryDataset이 stem 일치로 짝을 찾기 때문).
  4) 기본은 **심볼릭 링크**라 디스크를 추가로 쓰지 않는다.
     단, 512x512가 아니거나 이미지-마스크 크기가 다른 것(= Guava 55장,
     EXIF 회전 때문)은 EXIF를 보정하고 512x512로 리사이즈해 **실제 파일**로 저장한다.

사용 예:
  $PY tools/prepare_fruitseg30_semseg.py \
      --raw-root "<...>/FruitSeg30" \
      --out /data/project/2026summer/kds0206/dataset_fruitseg30
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageOps

SPLITS = ('train', 'val', 'test')
TARGET_SIZE = (512, 512)


def sanitize(name: str) -> str:
    """공백/슬래시를 '_'로 바꿔 파일 이름에 안전하게 만든다."""
    return name.replace(' ', '_').replace('/', '_')


def split_counts(n: int, val_r: float, test_r: float):
    """클래스 하나(n장)를 train/val/test 장수로 나눈다. 각각 최소 1장은 보장."""
    n_test = max(1, round(n * test_r))
    n_val = max(1, round(n * val_r))
    if n_test + n_val >= n:                     # 아주 작은 클래스 방어
        n_test = max(1, n - 2)
        n_val = 1
    return n - n_val - n_test, n_val, n_test


def needs_conversion(img_path: Path, mask_path: Path):
    """리사이즈/EXIF 보정이 필요한지 판정. (필요여부, 이미지크기, 마스크크기)"""
    with Image.open(img_path) as im:
        raw = im.size
        fixed = ImageOps.exif_transpose(im).size
    with Image.open(mask_path) as mk:
        ms = mk.size
    return (raw != TARGET_SIZE or ms != TARGET_SIZE or fixed != ms), raw, ms


def place(src: Path, dst: Path, convert: bool, is_mask: bool):
    """dst에 파일을 놓는다. convert=False면 심볼릭 링크, True면 512로 변환 저장."""
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if not convert:
        dst.symlink_to(src.resolve())
        return
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)         # 회전정보 실제로 적용
        if is_mask:
            im = im.convert('L').resize(TARGET_SIZE, Image.NEAREST)   # 라벨은 보간 금지
        else:
            im = im.convert('RGB').resize(TARGET_SIZE, Image.BILINEAR)
        im.save(dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--val-ratio', type=float, default=0.1)
    ap.add_argument('--test-ratio', type=float, default=0.2)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    raw = Path(args.raw_root)
    out = Path(args.out)

    # 1) 클래스별 (이미지, 마스크) 쌍 수집
    per_class = {}
    for cls_dir in sorted(p for p in raw.iterdir() if p.is_dir()):
        img_dir, mask_dir = cls_dir / 'Images', cls_dir / 'Mask'
        if not img_dir.is_dir() or not mask_dir.is_dir():
            print(f'  건너뜀(구조 다름): {cls_dir.name}')
            continue
        pairs = []
        for img in sorted(img_dir.iterdir(), key=lambda p: (len(p.stem), p.stem)):
            if img.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
                continue
            mask = mask_dir / f'{img.stem}_mask.png'
            if not mask.exists():
                hits = sorted(mask_dir.glob(f'{img.stem}.*'))
                if not hits:
                    print(f'  ⚠️ 마스크 없음, 제외: {img}')
                    continue
                mask = hits[0]
            pairs.append((img, mask))
        if pairs:
            per_class[cls_dir.name] = pairs

    total = sum(len(v) for v in per_class.values())
    print(f'클래스 {len(per_class)}개 / 이미지-마스크 쌍 {total}장 수집')

    # 2) 클래스별 층화 분할
    rng = random.Random(args.seed)
    assign = defaultdict(list)       # split -> [(클래스, img, mask)]
    per_class_counts = {}
    for cls, pairs in per_class.items():
        idx = list(range(len(pairs)))
        rng.shuffle(idx)
        n_tr, n_va, n_te = split_counts(len(pairs), args.val_ratio, args.test_ratio)
        per_class_counts[cls] = {'train': n_tr, 'val': n_va, 'test': n_te}
        for j, i in enumerate(idx):
            split = 'train' if j < n_tr else ('val' if j < n_tr + n_va else 'test')
            assign[split].append((cls, *pairs[i]))

    print('\n분할 결과')
    for s in SPLITS:
        print(f'  {s:<6} {len(assign[s]):>5}장 ({len(assign[s]) / total * 100:.1f}%)')

    if args.dry_run:
        print('\n--dry-run 이라 파일은 만들지 않았습니다.')
        return

    # 3) 배치
    for s in SPLITS:
        (out / s / 'images').mkdir(parents=True, exist_ok=True)
        (out / s / 'masks').mkdir(parents=True, exist_ok=True)

    manifest = {'seed': args.seed, 'raw_root': str(raw), 'splits': {},
                'per_class_counts': per_class_counts, 'converted': []}
    n_converted = 0
    for s in SPLITS:
        records = []
        for cls, img, mask in sorted(assign[s]):
            stem = f'{sanitize(cls)}__{img.stem}'
            conv, raw_sz, mask_sz = needs_conversion(img, mask)
            place(img, out / s / 'images' / f'{stem}.jpg', conv, is_mask=False)
            place(mask, out / s / 'masks' / f'{stem}.png', conv, is_mask=True)
            if conv:
                n_converted += 1
                manifest['converted'].append(
                    {'stem': stem, 'image_size': list(raw_sz), 'mask_size': list(mask_sz)})
            records.append({'stem': stem, 'class': cls,
                            'src_image': str(img), 'src_mask': str(mask),
                            'converted': conv})
        manifest['splits'][s] = records
        print(f'  {s} 배치 완료: {len(records)}장')

    print(f'\n512x512 변환(EXIF 보정 포함): {n_converted}장 / 나머지는 심볼릭 링크')

    # 4) 검증
    print('\n검증')
    ok = True
    for s in SPLITS:
        imgs = sorted((out / s / 'images').iterdir())
        masks = {p.stem for p in (out / s / 'masks').iterdir()}
        bad = [p.name for p in imgs if p.stem not in masks]
        broken = [p.name for p in imgs if not p.exists()]      # 끊어진 심볼릭 링크
        print(f'  {s:<6} 이미지 {len(imgs)} / 마스크 {len(masks)} / '
              f'짝없음 {len(bad)} / 깨진링크 {len(broken)}')
        if bad or broken or len(imgs) != len(masks):
            ok = False
            print(f'    ⚠️ {bad[:5]} {broken[:5]}')
    print('  결과:', '정상 ✅' if ok else '문제 있음 ❌')

    mf = out / 'split_manifest.json'
    mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f'\n분할 기록 저장: {mf}')


if __name__ == '__main__':
    main()
