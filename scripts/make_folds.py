"""이미 정리된 데이터셋을 K개 폴드로 **미리 나눠서 고정**한다.

왜 필요한가 (2026-07-27 교수님 지시)
  녹취록 55:57 "그러니까 다 그렇게 나눠 놓으세요. 일단은 미리 다 픽스를 해놓고
  그래서 할 때마다 랜덤하게 이제 달라지지 않도록"
  → 학습을 돌릴 때마다 분할이 달라지면 폴드끼리 비교가 성립하지 않는다.
    그래서 분할을 **파일로 먼저 만들어 놓고**, 학습은 그 폴더만 읽게 한다.

분할 방식 (녹취록 59:53 에서 확정)
  교수님: "그냥 뭐 아무튼 랜덤하게 그냥 뽑아서 만들면 되지 않을까요? ...
           나중에 10폴드 필요하면 5폴드 더 추가하고 랜덤하게 뽑아가지고"
  → K-Fold(전체를 K등분해 서로 겹치지 않게)가 아니라
    **ShuffleSplit(매 폴드마다 전체에서 랜덤으로 7:1:2를 다시 뽑는 방식)** 이다.
    이 방식이라야 나중에 폴드를 "추가"할 수 있다 (K-Fold는 K를 바꾸면 전부 다시 나눠야 함).
    폴드 k의 시드는 base_seed + k 라서, 나중에 --folds 6 7 로 6·7번 폴드만
    덧붙여도 기존 1~5번 폴드는 **한 장도 바뀌지 않는다.**

입력  <root>/{train,val,test}/{images,masks}/*        (이미 만들어 둔 데이터셋)
      또는 <root>/{images,masks}/*                     (분할 안 된 통짜 폴더)
출력  <out>/cv{k}/{train,val,test}/{images,masks}/*   (전부 심볼릭 링크 = 디스크 추가 0)
      <out>/folds_manifest.json                       (어느 파일이 어느 폴드 어느 split인지)

층화(stratify)
  --group-by 로 그룹 키를 주면 그룹별로 따로 7:1:2를 뜬다.
  예) FruitSeg30 은 파일명이 '<과일이름>__<번호>.jpg' 이므로
      --group-by "prefix:__" 로 주면 과일 종류별 층화가 된다.
  안 주면 전체를 통째로 섞는다.

사용 예
  $PY tools/make_folds.py \
      --root /data/project/2026summer/kds0206/dataset_fruitseg30 \
      --out  /data/project/2026summer/kds0206/dataset_fruitseg30_5fold \
      --folds 1 2 3 4 5 --group-by "prefix:__"
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

SPLITS = ('train', 'val', 'test')
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.JPG', '.JPEG', '.PNG'}


def collect_pairs(root: Path):
    """<root> 아래에서 (이미지, 마스크) 짝을 전부 모은다.

    train/val/test 로 이미 나뉘어 있으면 **셋을 다시 합쳐서** 하나의 풀로 만든다.
    (이번 지시는 '기존 분할을 무시하고 새로 폴드를 뜨는 것'이기 때문)
    """
    img_dirs = []
    if (root / 'images').is_dir():
        img_dirs.append(root / 'images')
    for s in SPLITS:
        if (root / s / 'images').is_dir():
            img_dirs.append(root / s / 'images')
    if not img_dirs:
        raise SystemExit(f"[에러] {root} 아래에 images 폴더가 없습니다.")

    pairs, missing = [], []
    seen_stems = set()
    for idir in img_dirs:
        mdir = idir.parent / 'masks'
        if not mdir.is_dir():
            raise SystemExit(f"[에러] {mdir} 가 없습니다.")
        # 마스크는 확장자가 다를 수 있으므로 stem -> 경로 로 미리 색인한다
        mask_by_stem = {p.stem: p for p in sorted(mdir.iterdir()) if p.suffix in IMG_EXT}
        for ip in sorted(idir.iterdir()):
            if ip.suffix not in IMG_EXT:
                continue
            mp = mask_by_stem.get(ip.stem)
            if mp is None:
                missing.append(str(ip))
                continue
            if ip.stem in seen_stems:           # 같은 stem이 두 split에 있으면 첫 것만
                continue
            seen_stems.add(ip.stem)
            # 심볼릭 링크를 또 링크하면 깨지기 쉬우므로 실제 파일 경로로 풀어둔다
            pairs.append((ip.resolve(), mp.resolve(), ip.stem))
    return pairs, missing


def group_key(stem: str, rule: str | None) -> str:
    """--group-by 규칙에 따라 층화용 그룹 이름을 만든다."""
    if not rule:
        return '_all'
    if rule.startswith('prefix:'):
        sep = rule.split(':', 1)[1]
        return stem.split(sep)[0] if sep in stem else stem
    raise SystemExit(f"[에러] 모르는 --group-by 규칙: {rule}")


def split_counts(n: int, val_r: float, test_r: float):
    """n장을 train/val/test 장수로 나눈다. val·test 최소 1장 보장."""
    n_test = max(1, round(n * test_r))
    n_val = max(1, round(n * val_r))
    if n_test + n_val >= n:                     # 그룹이 아주 작을 때 방어
        n_test, n_val = max(1, n - 2), 1
    return n - n_val - n_test, n_val, n_test


def build_fold(pairs, fold: int, base_seed: int, val_r: float, test_r: float, rule):
    """폴드 하나 분량의 {split: [(img, mask, stem), ...]} 를 만든다.

    시드를 base_seed + fold 로 두는 것이 핵심이다. 폴드마다 다른 분할이 나오면서도
    같은 명령을 다시 돌리면 **똑같은 분할이 재현**된다.
    """
    rng = random.Random(base_seed + fold)
    by_group = defaultdict(list)
    for item in pairs:
        by_group[group_key(item[2], rule)].append(item)

    out = {s: [] for s in SPLITS}
    for gname in sorted(by_group):              # 그룹 순서를 고정해야 재현된다
        items = sorted(by_group[gname], key=lambda t: t[2])
        rng.shuffle(items)
        n_tr, n_va, n_te = split_counts(len(items), val_r, test_r)
        out['train'] += items[:n_tr]
        out['val'] += items[n_tr:n_tr + n_va]
        out['test'] += items[n_tr + n_va:n_tr + n_va + n_te]
    return out


def write_fold(out_root: Path, fold: int, split_map, dry: bool) -> int:
    n = 0
    for split, items in split_map.items():
        idir = out_root / f'cv{fold}' / split / 'images'
        mdir = out_root / f'cv{fold}' / split / 'masks'
        if not dry:
            idir.mkdir(parents=True, exist_ok=True)
            mdir.mkdir(parents=True, exist_ok=True)
        for ip, mp, stem in items:
            # 이미지와 마스크의 링크 이름 stem 을 맞춘다 (Dataset이 stem으로 짝을 찾음)
            ilink, mlink = idir / f'{stem}{ip.suffix}', mdir / f'{stem}{mp.suffix}'
            if dry:
                n += 1
                continue
            for link, src in ((ilink, ip), (mlink, mp)):
                if link.is_symlink() or link.exists():
                    link.unlink()
                link.symlink_to(src)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='이미 정리된 데이터셋 폴더')
    ap.add_argument('--out', required=True, help='폴드를 만들 위치')
    ap.add_argument('--folds', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    ap.add_argument('--val-ratio', type=float, default=0.1)
    ap.add_argument('--test-ratio', type=float, default=0.2)
    ap.add_argument('--seed', type=int, default=42, help='base seed. 폴드 k는 seed+k 를 쓴다')
    ap.add_argument('--group-by', default=None, help='예: "prefix:__" (층화 분할)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    root, out = Path(args.root), Path(args.out)
    pairs, missing = collect_pairs(root)
    print(f'[수집] 이미지-마스크 짝 {len(pairs)}개'
          + (f' / 짝을 못 찾은 이미지 {len(missing)}개' if missing else ''))
    if missing[:5]:
        for m in missing[:5]:
            print(f'   - 짝 없음: {m}')
    if not pairs:
        raise SystemExit('[에러] 짝을 하나도 못 찾았습니다.')

    manifest = {
        'source_root': str(root),
        'n_pairs': len(pairs),
        'val_ratio': args.val_ratio, 'test_ratio': args.test_ratio,
        'base_seed': args.seed, 'group_by': args.group_by,
        'split_method': 'ShuffleSplit (fold k uses seed=base_seed+k)',
        'folds': {},
    }
    for k in args.folds:
        sm = build_fold(pairs, k, args.seed, args.val_ratio, args.test_ratio, args.group_by)
        n = write_fold(out, k, sm, args.dry_run)
        counts = {s: len(sm[s]) for s in SPLITS}
        manifest['folds'][f'cv{k}'] = {
            'counts': counts,
            'seed': args.seed + k,
            **{s: sorted(t[2] for t in sm[s]) for s in SPLITS},
        }
        tot = sum(counts.values())
        ratio = ' : '.join(f'{counts[s] / tot * 100:.1f}' for s in SPLITS)
        print(f'[cv{k}] train {counts["train"]} / val {counts["val"]} / test {counts["test"]}'
              f'  (= {ratio})  링크 {n}쌍')

    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        mpath = out / 'folds_manifest.json'
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f'[저장] {mpath}')
    else:
        print('[dry-run] 아무것도 쓰지 않았습니다.')


if __name__ == '__main__':
    main()
