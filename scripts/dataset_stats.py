"""데이터셋 기초 통계 (장수 / 해상도 / 마스크 픽셀값 / 전경 비율).

발표자료 ①(데이터셋 개수·해상도)용. 숫자를 하드코딩하지 않고 파일에서 직접 셉니다.

두 가지 폴더 구조를 모두 읽습니다.

  --raw-root   : <root>/<클래스>/Images/*.jpg + <root>/<클래스>/Mask/*.png
                 (FruitSeg30 원본 배치)
  --split-root : <root>/{train,val,test}/{images,masks}
                 (학습이 실제로 읽는 배치. BlueberryDataset과 동일)

사용 예:
  $PY tools/dataset_stats.py --raw-root "<...>/FruitSeg30" --out output/fruitseg30_stats.json
  $PY tools/dataset_stats.py --split-root /data/.../dataset_fruitseg30
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp'}


def collect_raw(root: Path):
    """<root>/<클래스>/Images + Mask 구조를 훑어 (그룹, 이미지경로, 마스크경로) 목록을 만든다."""
    pairs = []
    missing = []
    for cls_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        img_dir, mask_dir = cls_dir / 'Images', cls_dir / 'Mask'
        if not img_dir.is_dir():
            continue
        for img in sorted(img_dir.iterdir()):
            if img.suffix.lower() not in IMG_EXTS:
                continue
            mask = find_mask(mask_dir, img.stem)
            if mask is None:
                missing.append(str(img))
            else:
                pairs.append((cls_dir.name, img, mask))
    return pairs, missing


def collect_split(root: Path):
    """<root>/{train,val,test}/{images,masks} 구조를 훑는다."""
    pairs = []
    missing = []
    for split in ('train', 'val', 'test'):
        img_dir, mask_dir = root / split / 'images', root / split / 'masks'
        if not img_dir.is_dir():
            continue
        for img in sorted(img_dir.iterdir()):
            if img.suffix.lower() not in IMG_EXTS:
                continue
            mask = find_mask(mask_dir, img.stem)
            if mask is None:
                missing.append(str(img))
            else:
                pairs.append((split, img, mask))
    return pairs, missing


def find_mask(mask_dir: Path, stem: str):
    """이미지 stem에 대응하는 마스크를 찾는다.

    BlueberryDataset과 같은 규칙(stem 일치)을 먼저 보고,
    FruitSeg30 원본처럼 '<stem>_mask.png'인 경우도 받아준다.
    """
    if not mask_dir.is_dir():
        return None
    for cand in (stem, f'{stem}_mask'):
        hits = sorted(mask_dir.glob(f'{cand}.*'))
        hits = [h for h in hits if h.suffix.lower() in IMG_EXTS]
        if hits:
            return hits[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--raw-root', type=str, help='<클래스>/Images + Mask 구조')
    g.add_argument('--split-root', type=str, help='{train,val,test}/{images,masks} 구조')
    ap.add_argument('--out', type=str, default=None, help='통계 JSON 저장 경로')
    ap.add_argument('--sample-values', type=int, default=30,
                    help='마스크 고유 픽셀값을 조사할 표본 장수')
    args = ap.parse_args()

    if args.raw_root:
        root = Path(args.raw_root)
        pairs, missing = collect_raw(root)
        group_label = '클래스'
    else:
        root = Path(args.split_root)
        pairs, missing = collect_split(root)
        group_label = 'split'

    if not pairs:
        raise SystemExit(f'이미지를 찾지 못했습니다: {root}')

    per_group = Counter()
    img_sizes = Counter()
    mask_sizes = Counter()
    img_modes = Counter()
    mask_modes = Counter()
    size_mismatch = []
    fg_ratio_all = []
    fg_ratio_group = defaultdict(list)
    mask_values = Counter()

    for i, (group, img_path, mask_path) in enumerate(pairs):
        per_group[group] += 1
        with Image.open(img_path) as im:
            img_sizes[im.size] += 1
            img_modes[im.mode] += 1
            im_size = im.size
        with Image.open(mask_path) as mk:
            mask_sizes[mk.size] += 1
            mask_modes[mk.mode] += 1
            mk_size = mk.size
            arr = np.array(mk.convert('L'))

        if im_size != mk_size:
            size_mismatch.append((str(img_path), im_size, mk_size))

        # 학습 시 mask>0 이 1(전경)로 이진화되므로 같은 기준으로 잰다
        ratio = float((arr > 0).mean())
        fg_ratio_all.append(ratio)
        fg_ratio_group[group].append(ratio)

        if i < args.sample_values:
            mask_values.update(np.unique(arr).tolist())

    fg = np.array(fg_ratio_all)
    total = len(pairs)

    print('=' * 68)
    print(f'데이터셋 통계: {root}')
    print('=' * 68)
    print(f'이미지-마스크 쌍   : {total}장')
    print(f'{group_label} 수        : {len(per_group)}개')
    if missing:
        print(f'⚠️ 마스크 없는 이미지: {len(missing)}장  (예: {missing[:3]})')
    else:
        print('마스크 누락        : 없음 ✅')
    if size_mismatch:
        print(f'⚠️ 이미지-마스크 크기 불일치: {len(size_mismatch)}건 (예: {size_mismatch[:2]})')
    else:
        print('이미지-마스크 크기 : 전부 일치 ✅')

    print('\n--- 해상도 (이미지) ---')
    for (w, h), n in img_sizes.most_common():
        print(f'  {w}x{h} : {n}장 ({n / total * 100:.1f}%)')
    print('--- 해상도 (마스크) ---')
    for (w, h), n in mask_sizes.most_common():
        print(f'  {w}x{h} : {n}장')

    print(f'\n이미지 모드        : {dict(img_modes)}')
    print(f'마스크 모드        : {dict(mask_modes)}')
    print(f'마스크 고유 픽셀값 (표본 {min(args.sample_values, total)}장): '
          f'{sorted(mask_values)}')

    print('\n--- 전경(과일) 비율 ---')
    print(f'  평균 {fg.mean() * 100:.2f}%  중앙값 {np.median(fg) * 100:.2f}%  '
          f'최소 {fg.min() * 100:.2f}%  최대 {fg.max() * 100:.2f}%')

    print(f'\n--- {group_label}별 장수 ---')
    for name, n in sorted(per_group.items()):
        r = np.mean(fg_ratio_group[name]) * 100
        print(f'  {name:<24} {n:>5}장   전경 {r:5.2f}%')

    stats = {
        'root': str(root),
        'total_pairs': total,
        'group_label': group_label,
        'per_group': dict(sorted(per_group.items())),
        'per_group_fg_ratio_mean': {k: float(np.mean(v)) for k, v in fg_ratio_group.items()},
        'image_sizes': {f'{w}x{h}': n for (w, h), n in img_sizes.items()},
        'mask_sizes': {f'{w}x{h}': n for (w, h), n in mask_sizes.items()},
        'image_modes': dict(img_modes),
        'mask_modes': dict(mask_modes),
        'mask_unique_values_sampled': sorted(int(v) for v in mask_values),
        'fg_ratio': {
            'mean': float(fg.mean()), 'median': float(np.median(fg)),
            'min': float(fg.min()), 'max': float(fg.max()), 'std': float(fg.std()),
        },
        'missing_masks': missing,
        'size_mismatch_count': len(size_mismatch),
    }

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
        print(f'\n저장: {out}')


if __name__ == '__main__':
    main()
