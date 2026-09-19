"""내용이 **완전히 똑같은 파일들**을 하드링크로 합쳐 디스크를 되찾는다.

하드링크가 무엇인가 (아주 쉽게)
  파일은 「이름표」와 「실제 내용」이 따로 있습니다.
  똑같은 사진이 6군데에 복사돼 있으면 → 이름표 6개 + 내용 6덩어리 (디스크 6배)
  하드링크로 합치면       → 이름표 6개 + 내용 1덩어리 (디스크 1배)
  **경로는 6개 다 그대로 남고, 열어보면 똑같이 열립니다.** 프로그램은 차이를 못 느낍니다.
  심볼릭 링크(바로가기)와 달리 "원본"이라는 개념이 없어서, 6개 중 하나를 지워도
  나머지 5개는 멀쩡합니다.

왜 dataset_6fold 에 필요한가
  폴드 6개가 각각 블루베리 사진 1,195장을 **통째로 복사**해서 갖고 있습니다.
  (2026-07-20에 남의 계정에서 복사해 올 때 그렇게 됨)
  6 × 9.2GB = 55GB 인데 실제 고유 내용은 9.2GB 뿐 → **약 46GB가 낭비**입니다.
  나중에 만든 다른 데이터셋(fruitseg30/minneapple/strawdi 5폴드)은 이미 심볼릭 링크라
  용량이 수십 MB 밖에 안 됩니다. 블루베리만 옛 방식으로 남아 있는 것입니다.

🔴 주의 — 하드링크로 합친 파일은 **하나를 고치면 전부 같이 바뀝니다.**
  데이터셋 사진처럼 "읽기만 하는 파일"에만 쓰세요. 학습 결과나 로그에는 쓰지 마세요.

안전장치
  - 크기가 같아도 **파일 전체 지문(md5)이 일치할 때만** 합칩니다.
  - 합치기는 `임시 링크 생성 → os.replace(원자적 교체)` 순서라 중간에 끊겨도 파일이 사라지지 않습니다.
  - `--apply` 를 주지 않으면 **아무것도 바꾸지 않고 계획만 출력**합니다(기본값).
  - 서로 다른 디스크에 있는 파일은 하드링크가 불가능하므로 자동으로 건너뜁니다.

사용 예
  # 1) 먼저 계획만 본다 (아무것도 안 바뀜)
  $PY tools/dedup_hardlink.py --root /data/project/2026summer/kds0206/dataset_6fold
  # 2) 실제로 합친다
  $PY tools/dedup_hardlink.py --root /data/project/2026summer/kds0206/dataset_6fold --apply
"""
import argparse
import hashlib
import os
from collections import defaultdict

SKIP_DIRS = {'.git', '__pycache__', '.pylibs'}


def full_digest(path: str) -> str:
    m = hashlib.md5()
    with open(path, 'rb') as fh:
        while True:
            chunk = fh.read(8 * 1024 * 1024)
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest()


def human(n: float) -> str:
    return f'{n/1e9:.2f} GB' if n >= 1e9 else f'{n/1e6:.1f} MB'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--min-kb', type=float, default=64.0,
                    help='이 크기 미만은 건너뜀 (작은 파일은 합쳐도 이득이 없음)')
    ap.add_argument('--apply', action='store_true',
                    help='실제로 합친다. 주지 않으면 계획만 출력')
    args = ap.parse_args()

    min_bytes = int(args.min_kb * 1024)

    # 1단계 — (크기) 별로 모으되, 이미 같은 inode 인 것은 한 번만 센다
    by_size = defaultdict(list)
    n_file = n_link = 0
    for dirpath, dirnames, filenames in os.walk(args.root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                n_link += 1
                continue
            try:
                st = os.lstat(path)
            except OSError:
                continue
            n_file += 1
            if st.st_size >= min_bytes:
                by_size[st.st_size].append((path, st.st_dev, st.st_ino))

    cand = {s: v for s, v in by_size.items() if len(v) > 1}
    print(f'[검사] 실파일 {n_file:,}개 (심볼릭 링크 {n_link:,}개 제외)')
    print(f'       크기가 겹치는 후보 {sum(len(v) for v in cand.values()):,}개 '
          f'/ 그룹 {len(cand):,}개', flush=True)

    plan = []            # (keeper, [합칠 것들], 파일크기)
    reclaim = 0
    for size, entries in cand.items():
        # 같은 디스크끼리만 묶는다
        by_dev = defaultdict(list)
        for path, dev, ino in entries:
            by_dev[dev].append((path, ino))
        for dev, items in by_dev.items():
            if len(items) < 2:
                continue
            # 파일 전체 지문으로 확정
            by_hash = defaultdict(list)
            for path, ino in items:
                try:
                    by_hash[full_digest(path)].append((path, ino))
                except OSError as e:
                    print(f'  읽기 실패, 건너뜀: {path} ({e})')
            for group in by_hash.values():
                inodes = {ino for _, ino in group}
                if len(group) < 2 or len(inodes) < 2:
                    continue          # 이미 합쳐져 있음
                group.sort(key=lambda t: t[0])
                keeper = group[0][0]
                keeper_ino = group[0][1]
                targets = [p for p, ino in group[1:] if ino != keeper_ino]
                if not targets:
                    continue
                plan.append((keeper, targets, size))
                reclaim += size * len(targets)

    print(f'\n[계획] 합칠 그룹 {len(plan):,}개 / 되찾는 용량 **{human(reclaim)}**')
    for keeper, targets, size in plan[:5]:
        print(f'   예) {human(size)} — 남길 것 {os.path.relpath(keeper, args.root)}')
        for t in targets[:3]:
            print(f'        합칠 것 {os.path.relpath(t, args.root)}')
        if len(targets) > 3:
            print(f'        ... 외 {len(targets)-3}개')
    if len(plan) > 5:
        print(f'   ... 외 {len(plan)-5:,}개 그룹')

    if not args.apply:
        print('\n🔴 --apply 를 주지 않았으므로 **아무것도 바꾸지 않았습니다.**')
        return

    print('\n[실행] 하드링크로 합치는 중...', flush=True)
    done = failed = 0
    for keeper, targets, size in plan:
        for dup in targets:
            tmp = dup + '.dedup_tmp'
            try:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                os.link(keeper, tmp)     # 같은 내용의 새 이름표를 만든다
                os.replace(tmp, dup)     # 원자적으로 갈아끼운다 (중간에 끊겨도 파일 안 사라짐)
                done += 1
            except OSError as e:
                failed += 1
                print(f'  실패: {dup} ({e})')
                if os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
        if done % 2000 == 0 and done:
            print(f'   {done:,}개 완료...', flush=True)

    print(f'\n[완료] 합침 {done:,}개 / 실패 {failed:,}개 / 되찾은 용량 약 {human(reclaim)}')

    # 검증 — 표본 그룹의 내용이 그대로인지 다시 확인
    print('\n[검증] 표본 5그룹의 내용이 변하지 않았는지 재확인')
    ok = True
    for keeper, targets, size in plan[:5]:
        kd = full_digest(keeper)
        for t in targets:
            td = full_digest(t)
            same_inode = os.lstat(keeper).st_ino == os.lstat(t).st_ino
            if kd != td or not same_inode:
                ok = False
                print(f'  ❌ {t}  지문일치={kd==td} 같은inode={same_inode}')
    print('  ✅ 표본 전부 내용 동일 + 하드링크 확인' if ok else '  ❌ 문제 발견 — 확인 필요')


if __name__ == '__main__':
    main()
