# -*- coding: utf-8 -*-
"""datasets_tiled_512/ 를 전수 검증합니다.

확인하는 것
  1. 깨진 심볼릭 링크가 없는가
  2. 이미지↔마스크가 1:1 로 맞는가 (이름·장수)
  3. 타일이 전부 512x512 인가 (표본)
  4. 🔴 정보 누수 — 같은 원본 사진에서 나온 조각이 train/val/test 에 흩어지지 않았는가
  5. index.csv 의 타일 수 = 실제 파일 수
  6. 원본(datasets_resized_2mp)이 훼손되지 않았는가 (장수·수정시각 확인)

사용:  $PY tools/verify_tiled_dataset.py
"""
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

BASE = Path('/data/project/2026summer/kds0206')
TILED = BASE / 'datasets_tiled_512'
POOL = BASE / 'datasets_resized_2mp'
ORDER = ['blueberry', 'apple', 'peach', 'grape']
KOR = {'blueberry': '블루베리', 'apple': '사과', 'peach': '복숭아', 'grape': '포도'}

fails = []


def check(cond: bool, msg: str) -> None:
    print(('  ✅ ' if cond else '  ❌ ') + msg)
    if not cond:
        fails.append(msg)


def main() -> None:
    m = json.loads((TILED / 'manifest.json').read_text())
    rng = random.Random(0)

    for fruit in ORDER:
        print(f'\n■ {KOR[fruit]}')
        img_dir, msk_dir = TILED / fruit / 'images', TILED / fruit / 'masks'
        imgs = {p.name for p in img_dir.glob('*.png')}
        msks = {p.name for p in msk_dir.glob('*.png')}

        check(imgs == msks,
              f'이미지↔마스크 이름 일치 (이미지 {len(imgs):,} / 마스크 {len(msks):,}, '
              f'차이 {len(imgs ^ msks)})')

        with open(TILED / fruit / 'index.csv') as fh:
            rows = list(csv.DictReader(fh))
        check(len(rows) == len(imgs), f'index.csv {len(rows):,}행 = 실제 타일 {len(imgs):,}개')
        check(len(rows) == m['fruits'][fruit]['tiles'],
              f'manifest 기록 {m["fruits"][fruit]["tiles"]:,} = index.csv {len(rows):,}')

        # 크기 표본 검사
        sample = rng.sample(sorted(imgs), min(60, len(imgs)))
        bad = []
        for n in sample:
            if Image.open(img_dir / n).size != (512, 512):
                bad.append(n)
            if Image.open(msk_dir / n).size != (512, 512):
                bad.append(n)
        check(not bad, f'표본 {len(sample)}장 전부 512x512 (어긋난 것 {len(bad)}개)')

        # 폴드 — 깨진 링크 + 누수
        sp_root = TILED / 'splits' / fruit
        broken = 0
        leak_total = 0
        fold_report = []
        for cv in sorted(p for p in sp_root.iterdir() if p.is_dir()):
            stem_split = defaultdict(set)
            counts = {}
            for split in ('train', 'val', 'test'):
                d = cv / split / 'images'
                if not d.is_dir():
                    continue
                names = list(d.iterdir())
                counts[split] = len(names)
                for p in names:
                    if not p.resolve().exists():
                        broken += 1
                    stem_split[p.name.split('__r')[0]].add(split)
            leak = [s for s, v in stem_split.items() if len(v) > 1]
            leak_total += len(leak)
            fold_report.append(f'{cv.name}({"/".join(str(counts.get(s, 0)) for s in ("train", "val", "test"))})')
        check(broken == 0, f'깨진 링크 {broken}개')
        check(leak_total == 0,
              f'🔴 누수 검사 — 한 사진의 조각이 두 split 에 걸친 경우 {leak_total}건')
        print(f'     폴드: {" ".join(fold_report)}')

    # 원본 훼손 검사
    print('\n■ 원본(datasets_resized_2mp) 훼손 검사')
    src = json.loads((POOL / 'manifest.json').read_text())
    for fruit in ORDER:
        n_now = len(list((POOL / fruit / 'images').glob('*.png')))
        n_man = int(src['fruits'][fruit]['images_used'])
        check(n_now == n_man, f'{KOR[fruit]} 원본 {n_now:,}장 (manifest 기록 {n_man:,}장)')

    print('\n' + '─' * 64)
    if fails:
        print(f'❌ 실패 {len(fails)}건')
        for f in fails:
            print('   -', f)
        sys.exit(1)
    print('✅ 전부 통과')


if __name__ == '__main__':
    main()
