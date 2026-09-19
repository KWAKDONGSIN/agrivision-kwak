"""블루베리 1,195장을 **7:1:2** 로 랜덤 분할해 6폴드를 만든다.

왜 별도 스크립트인가
--------------------
팀 표준 분할기 `tools/make_folds.py` 는 사진 한 장 한 장을 랜덤으로 뽑아
7:1:2 를 만든다. 사과·복숭아·포도는 서로 다른 사진이라 이 방식으로 충분하다.

그런데 **블루베리만 사정이 다르다.** 파일명이
    `Camera 3 Video (11)_181.png`
처럼 «어느 영상의 몇 번째 프레임» 이다. 같은 영상에서 뽑은 프레임들은 거의
같은 장면이므로, 한 장씩 랜덤으로 뽑으면 **같은 영상의 프레임이 train 과 test 에
동시에 들어간다.** 그러면 모델이 이미 본 장면을 시험 보는 셈이라 점수가 부풀려진다
(= 데이터 누수, data leakage).

그래서 여기서는 **영상 단위로 랜덤하게 뽑는다.**
  - 뽑기 단위: 사진 1장이 아니라 «영상 1개»(288개)
  - 목표 비율: 사진 장수 기준 train 70% / val 10% / test 20%
  - 카메라(1~4)별로 따로 뽑아서 어느 split 에도 특정 카메라가 쏠리지 않게 함(층화)

폴드 k 의 시드는 `base_seed + k` 라서
  ① 같은 명령을 다시 돌리면 똑같은 분할이 재현되고
  ② 나중에 `--folds 7 8` 로 폴드를 덧붙여도 기존 폴드는 한 장도 안 바뀐다.
(팀 표준 `make_folds.py` 와 같은 규약)

입력  <root>/{images,masks}/*.png          (분할 안 된 통짜 폴더)
출력  <out>/cv{k}/{train,val,test}/{images,masks}/*   (전부 심볼릭 링크 = 디스크 추가 0)
      <out>/folds_manifest.json

사용 예
  $PY tools/make_blueberry_folds_712.py \
      --root /data/project/2026summer/kds0206/datasets_resized_2mp/blueberry \
      --out  /data/project/2026summer/kds0206/datasets_resized_2mp/splits/blueberry \
      --folds 1 2 3 4 5 6
"""
import argparse
import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

SPLITS = ('train', 'val', 'test')
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.JPG', '.JPEG', '.PNG'}

# 'Camera 3 Video (11)_181.png' -> 그룹 'Camera 3 Video (11)' / 층화키 'Camera 3'
GROUP_RE = re.compile(r'^(Camera (\d+) Video \(\d+\))_\d+$')


def parse_keys(stem: str):
    """파일 이름에서 (영상 그룹, 카메라) 를 뽑는다."""
    m = GROUP_RE.match(stem)
    if not m:
        raise SystemExit(f'[에러] 파일명에서 영상 이름을 못 읽었습니다: {stem}')
    return m.group(1), f'Camera {m.group(2)}'


def collect_pairs(root: Path):
    """<root>/images 와 <root>/masks 에서 (이미지, 마스크, stem) 짝을 전부 모은다."""
    idir, mdir = root / 'images', root / 'masks'
    if not idir.is_dir() or not mdir.is_dir():
        raise SystemExit(f'[에러] {root} 아래에 images/ masks/ 가 필요합니다.')
    mask_by_stem = {p.stem: p for p in sorted(mdir.iterdir()) if p.suffix in IMG_EXT}

    pairs, missing = [], []
    for ip in sorted(idir.iterdir()):
        if ip.suffix not in IMG_EXT:
            continue
        mp = mask_by_stem.get(ip.stem)
        if mp is None:
            missing.append(ip.name)
            continue
        # 심볼릭 링크를 또 링크하면 깨지기 쉬우므로 실제 파일 경로로 풀어둔다
        pairs.append((ip.resolve(), mp.resolve(), ip.stem))
    if missing:
        raise SystemExit(f'[에러] 마스크 짝이 없는 이미지 {len(missing)}장: {missing[:5]}')
    return pairs


def take_groups(groups, sizes, target, rng_order):
    """영상 그룹을 순서대로 담아 목표 장수(target)에 **가장 가깝게** 채운다.

    그룹은 통째로만 담을 수 있으므로 정확히 target 에 맞출 수는 없다.
    "넣으면 목표를 넘지만, 안 넣는 것보다 목표에 가까운" 경우까지는 넣는다.
    반환: (담은 그룹 집합, 남은 그룹 리스트)
    """
    chosen, rest, n = set(), [], 0
    full = False
    for g in rng_order:
        if full:
            rest.append(g)
            continue
        s = sizes[g]
        if n + s <= target:
            chosen.add(g)
            n += s
            if n == target:
                full = True
        elif abs(n + s - target) < abs(n - target):
            chosen.add(g)
            n += s
            full = True
        else:
            full = True
            rest.append(g)
    return chosen, rest


def repair_assignment(assign, sizes, targets):
    """랜덤 배정 뒤 «영상 1개 옮기기» 로 7:1:2 오차를 더 줄인다.

    그룹을 통째로만 옮길 수 있어 greedy 만으로는 목표에서 최대 1%p 남짓 벗어난다.
    여기서 «어느 영상 하나를 다른 split 으로 옮기면 오차 합이 줄어드는가» 를 보고
    더 줄어들지 않을 때까지 반복한다. 어느 영상이 어디로 갈지는 여전히 **랜덤 배정
    결과에서 출발**하므로 임의성은 유지된다. (결정적 = 재현 가능)
    """
    cur = {s: sum(sizes[g] for g, v in assign.items() if v == s) for s in SPLITS}
    err = lambda c: sum(abs(c[s] - targets[s]) for s in SPLITS)

    while True:
        best, best_err = None, err(cur)
        for g in sorted(assign):                       # 순서 고정 = 재현 가능
            src, s = assign[g], sizes[g]
            for dst in SPLITS:
                if dst == src:
                    continue
                trial = dict(cur)
                trial[src] -= s
                trial[dst] += s
                e = err(trial)
                if e < best_err:
                    best, best_err = (g, src, dst), e
        if best is None:
            return assign
        g, src, dst = best
        assign[g] = dst
        cur[src] -= sizes[g]
        cur[dst] += sizes[g]


def build_fold(pairs, fold, base_seed, val_r, test_r):
    """폴드 하나 분량의 {split: [(img, mask, stem), ...]} 를 만든다.

    카메라별로 따로 7:1:2 를 뜨고(층화), 뽑는 단위는 영상 그룹이다.
    """
    rng = random.Random(base_seed + fold)

    by_cam = defaultdict(lambda: defaultdict(list))   # 카메라 -> 영상 -> 사진들
    for ip, mp, stem in pairs:
        grp, cam = parse_keys(stem)
        by_cam[cam][grp].append((ip, mp, stem))

    out = {s: [] for s in SPLITS}
    assign = {}                                        # 영상 -> split (검증용)
    for cam in sorted(by_cam):                         # 순서 고정해야 재현된다
        vids = by_cam[cam]
        sizes = {g: len(v) for g, v in vids.items()}
        n_cam = sum(sizes.values())
        order = sorted(vids)                           # 정렬 후 섞어야 재현된다
        rng.shuffle(order)

        te_groups, rest = take_groups(vids, sizes, round(n_cam * test_r), order)
        va_groups, tr_groups = take_groups(vids, sizes, round(n_cam * val_r), rest)

        cam_assign = {g: 'train' for g in tr_groups}
        cam_assign.update({g: 'val' for g in va_groups})
        cam_assign.update({g: 'test' for g in te_groups})
        cam_assign = repair_assignment(cam_assign, sizes, {
            'train': n_cam - round(n_cam * val_r) - round(n_cam * test_r),
            'val': round(n_cam * val_r),
            'test': round(n_cam * test_r),
        })

        for g, split in cam_assign.items():
            out[split] += sorted(vids[g], key=lambda t: t[2])
            assign[g] = split

    # 안전장치 ①: 한 영상이 두 split 에 걸치면 즉시 중단 (누수 방지의 핵심)
    seen = defaultdict(set)
    for split, items in out.items():
        for _, _, stem in items:
            seen[parse_keys(stem)[0]].add(split)
    leaked = {g: sorted(s) for g, s in seen.items() if len(s) > 1}
    if leaked:
        raise SystemExit(f'[에러] cv{fold} 영상 누수: {list(leaked.items())[:5]}')

    # 안전장치 ②: 총 장수가 맞는지
    tot = sum(len(v) for v in out.values())
    if tot != len(pairs):
        raise SystemExit(f'[에러] cv{fold} 장수 불일치: {tot} != {len(pairs)}')
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
    ap.add_argument('--root', required=True, help='통짜 블루베리 폴더 (images/ masks/)')
    ap.add_argument('--out', required=True, help='폴드를 만들 위치')
    ap.add_argument('--folds', type=int, nargs='+', default=[1, 2, 3, 4, 5, 6])
    ap.add_argument('--val-ratio', type=float, default=0.1)
    ap.add_argument('--test-ratio', type=float, default=0.2)
    ap.add_argument('--seed', type=int, default=42, help='base seed. 폴드 k는 seed+k 를 쓴다')
    ap.add_argument('--clean', action='store_true',
                    help='--out 안의 기존 cv 폴더를 지우고 새로 만든다')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    root, out = Path(args.root), Path(args.out)
    pairs = collect_pairs(root)
    n_groups = len({parse_keys(s)[0] for _, _, s in pairs})
    print(f'[수집] 사진 {len(pairs)}장 / 영상 그룹 {n_groups}개  ← {root}')

    if args.clean and not args.dry_run:
        for k in args.folds:
            d = out / f'cv{k}'
            if d.exists():
                shutil.rmtree(d)
                print(f'[정리] 기존 {d} 삭제')

    manifest = {
        'source_root': str(root),
        'n_pairs': len(pairs),
        'n_video_groups': n_groups,
        'val_ratio': args.val_ratio, 'test_ratio': args.test_ratio,
        'base_seed': args.seed,
        'split_method': ('group-aware ShuffleSplit — 뽑기 단위는 영상(Camera N Video (X)), '
                         '카메라별 층화, 폴드 k 는 seed=base_seed+k'),
        'folds': {},
    }
    print(f"\n{'폴드':>5} | {'train':>6} | {'val':>4} | {'test':>5} |   비율(%)         | 링크")
    print('-' * 62)
    for k in args.folds:
        sm = build_fold(pairs, k, args.seed, args.val_ratio, args.test_ratio)
        n = write_fold(out, k, sm, args.dry_run)
        counts = {s: len(sm[s]) for s in SPLITS}
        tot = sum(counts.values())
        manifest['folds'][f'cv{k}'] = {
            'counts': counts,
            'ratio_pct': {s: round(counts[s] / tot * 100, 2) for s in SPLITS},
            'seed': args.seed + k,
            **{s: sorted(t[2] for t in sm[s]) for s in SPLITS},
        }
        ratio = ' : '.join(f'{counts[s] / tot * 100:5.2f}' for s in SPLITS)
        print(f'  cv{k:<3} | {counts["train"]:>6} | {counts["val"]:>4} | {counts["test"]:>5} '
              f'| {ratio} | {n}쌍')

    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        mpath = out / 'folds_manifest.json'
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f'\n[저장] {mpath}')
    else:
        print('\n[dry-run] 아무것도 쓰지 않았습니다.')


if __name__ == '__main__':
    main()
