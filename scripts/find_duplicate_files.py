"""서버에서 **완전히 똑같은 파일**(중복)을 찾아 목록만 출력한다. 지우지는 않는다.

왜 이렇게 만들었나
  60GB 넘는 파일이 수천 개라 전부 해시(지문)를 뜨면 몇 시간이 걸린다.
  그래서 3단계로 걸러 빠르게 찾는다.
    1단계 크기가 똑같은 것만 후보로 남긴다   (크기가 다르면 절대 같은 파일이 아니다)
    2단계 후보의 **앞 1MB만** 지문을 떠서 다시 걸러낸다
    3단계 그래도 살아남은 것만 **파일 전체** 지문을 떠서 확정한다
  심볼릭 링크는 원본을 가리키는 바로가기일 뿐 디스크를 쓰지 않으므로 처음부터 제외한다.

🔴 이 스크립트는 **아무것도 삭제하지 않는다.** 삭제는 사람이 목록을 보고 판단한다.

사용 예
  $PY tools/find_duplicate_files.py --root /data/project/2026summer/kds0206 --min-mb 50
"""
import argparse
import hashlib
import os
from collections import defaultdict

SKIP_DIRS = {'.git', '__pycache__', '.pylibs', 'node_modules'}


def digest(path: str, nbytes: int | None = None) -> str:
    """파일 지문. nbytes를 주면 앞부분만, 안 주면 파일 전체."""
    m = hashlib.md5()
    left = nbytes
    with open(path, 'rb') as fh:
        while True:
            chunk = fh.read(8 * 1024 * 1024)
            if not chunk:
                break
            if left is not None:
                chunk = chunk[:left]
                left -= len(chunk)
            m.update(chunk)
            if left is not None and left <= 0:
                break
    return m.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--min-mb', type=float, default=50.0, help='이 크기 이상만 검사')
    args = ap.parse_args()

    min_bytes = int(args.min_mb * 1024 * 1024)

    # 1단계 — 크기별로 모으기
    by_size = defaultdict(list)
    n_all = n_link = 0
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                n_link += 1
                continue
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            n_all += 1
            if size >= min_bytes:
                by_size[size].append(path)

    cand = {s: ps for s, ps in by_size.items() if len(ps) > 1}
    n_cand = sum(len(v) for v in cand.values())
    print(f'[1단계] 실파일 {n_all:,}개 (심볼릭 링크 {n_link:,}개 제외)')
    print(f'        {args.min_mb:g}MB 이상 {sum(len(v) for v in by_size.values()):,}개')
    print(f'        크기가 겹치는 후보 {n_cand:,}개 / 그룹 {len(cand):,}개', flush=True)

    # 2단계 — 앞 1MB 지문
    stage2 = []
    for size, paths in cand.items():
        groups = defaultdict(list)
        for p in paths:
            try:
                groups[digest(p, 1024 * 1024)].append(p)
            except OSError as e:
                print(f'  읽기 실패: {p} ({e})')
        for g in groups.values():
            if len(g) > 1:
                stage2.append((size, g))
    print(f'[2단계] 앞 1MB까지 같은 그룹 {len(stage2):,}개 → 전체 지문 확인', flush=True)

    # 3단계 — 파일 전체 지문
    total_waste = 0
    confirmed = []
    for size, paths in sorted(stage2, key=lambda kv: -kv[0]):
        groups = defaultdict(list)
        for p in paths:
            try:
                groups[digest(p)].append(p)
            except OSError as e:
                print(f'  읽기 실패: {p} ({e})')
        for g in groups.values():
            if len(g) > 1:
                waste = size * (len(g) - 1)
                total_waste += waste
                confirmed.append((size, waste, sorted(g)))

    print(f'\n[3단계] 완전히 동일한 파일 그룹 {len(confirmed):,}개\n')
    for size, waste, group in confirmed:
        print(f'■ 한 개 {size/1e9:.3f} GB × {len(group)}개  → 중복분 {waste/1e9:.3f} GB')
        for p in group:
            print(f'    {p.replace(args.root + "/", "")}')
        print()

    print('=' * 60)
    print(f'중복으로 낭비되는 용량 합계: {total_waste/1e9:.2f} GB')
    print('🔴 이 스크립트는 아무것도 삭제하지 않았습니다. 목록을 보고 사람이 판단하세요.')


if __name__ == '__main__':
    main()
