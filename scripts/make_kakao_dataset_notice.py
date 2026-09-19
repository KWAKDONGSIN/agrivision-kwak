#!/usr/bin/env python
"""팀 카톡에 그대로 붙여넣을 데이터셋 안내 문구를 만든다.

숫자를 손으로 적지 않는다. **디스크를 직접 세어서** 채운다.
(장수가 바뀌면 다시 돌리기만 하면 문구가 최신이 된다)

출력: 문서/260807_카톡_데이터셋안내.txt
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path("/data/project/2026summer/kds0206")
POOL = ROOT / "datasets_resized_2mp"

FRUITS = [
    ("blueberry", "🫐 블루베리"),
    ("apple", "🍎 사과 (MinneApple)"),
    ("peach", "🍑 복숭아"),
    ("grape", "🍇 포도 (CERTH)"),
]


def count(d: Path) -> int:
    return sum(1 for _ in d.iterdir()) if d.is_dir() else 0


def split_total(split_name: str) -> int:
    """그 분할이 실제로 쓰는 장수 = cv1 의 train+val+test.

    풀(pool)이 아니라 분할을 세는 이유: 분할이 풀 전체를 다 쓴다는 보장이 없습니다.
    (2026-08-08 이전 블루베리는 풀 1,195장 중 1,067장만 썼습니다.)
    """
    base = POOL / "splits" / split_name / "cv1"
    if not base.is_dir():
        return 0
    return sum(count(base / p / "images") for p in ("train", "val", "test"))


def fold_rows(fruit: str) -> list[tuple[str, int, int, int]]:
    base = POOL / "splits" / fruit
    # 포도 교체(swap) 전이면 새로 만든 grape_2502 쪽 숫자를 읽는다.
    # 교체는 이름만 바꾸는 작업이라 최종 경로는 어차피 splits/grape 가 된다.
    pending = POOL / "splits" / f"{fruit}_2502"
    if pending.is_dir() and count(base / "cv1" / "train" / "images") < \
            count(pending / "cv1" / "train" / "images"):
        base = pending
    rows = []
    if not base.is_dir():
        return rows
    for d in sorted(base.iterdir()):
        if not (d / "train" / "images").is_dir():
            continue
        rows.append((d.name, count(d / "train" / "images"),
                     count(d / "val" / "images"), count(d / "test" / "images")))
    # cv1, cv2, ... 를 앞으로, single/official 을 뒤로
    rows.sort(key=lambda r: (not r[0].startswith("cv"), r[0]))
    return rows


def resolutions(fruit: str, split_name: str | None = None) -> str:
    """해상도 분포. split_name 을 주면 그 분할이 실제로 쓰는 사진만 센다."""
    from collections import Counter
    d = POOL / fruit / "images"
    if not d.is_dir():
        return "?"
    only = None
    if split_name:
        base = POOL / "splits" / split_name / "cv1"
        only = {p.stem for part in ("train", "val", "test")
                for p in (base / part / "images").iterdir()} if base.is_dir() else None
    c = Counter()
    for p in sorted(d.iterdir()):
        if only is not None and p.stem not in only:
            continue
        with Image.open(p) as im:
            c[im.size] += 1
    parts = [f"{w}x{h}" + (f"({n}장)" if len(c) > 1 else "") for (w, h), n in c.most_common()]
    return " / ".join(parts)


def compress(rows: list[tuple[str, int, int, int]]) -> list[str]:
    """cv1~cv4 처럼 값이 같은 연속 폴드는 한 줄로 묶는다."""
    out, i = [], 0
    cvs = [r for r in rows if r[0].startswith("cv")]
    others = [r for r in rows if not r[0].startswith("cv")]
    while i < len(cvs):
        j = i
        while j + 1 < len(cvs) and cvs[j + 1][1:] == cvs[i][1:]:
            j += 1
        name = cvs[i][0] if i == j else f"{cvs[i][0]}~{cvs[j][0]}"
        out.append(f"   {name}: train {cvs[i][1]} / val {cvs[i][2]} / test {cvs[i][3]}")
        i = j + 1
    for r in others:
        out.append(f"   {r[0]}: train {r[1]} / val {r[2]} / test {r[3]}   ※ 비교실험엔 쓰지 마세요")
    return out


def build_short(pool_gb: float, full_gb: float) -> str:
    """카톡 한 번에 붙여넣기 좋은 짧은 버전. 경로는 전부 전체경로로 적는다."""
    S: list[str] = []
    A = S.append
    A("[데이터셋 안내] 4과일 화소 통일본")
    A("")
    A("교수님 지시대로 4개 데이터셋 사진의 가로세로 비율은 그대로 두고,")
    A("총 화소 수만 1440x1440(=2,073,600)에 맞춰 리사이즈했습니다.")
    A("해상도(가로x세로)는 데이터셋마다 다릅니다. 맞춘 건 '화소 수'예요.")
    A("(비율을 억지로 맞추면 사진이 찌그러져서 교수님이 그 방식을 물리셨습니다.")
    A(" 학습 때 어차피 512x512로 크롭하니 해상도가 달라도 됩니다.)")
    A("")
    A("[경로]")
    A(f"{POOL}/")
    A("")
    A("[과일별]")
    for key, kor in FRUITS:
        rows = fold_rows(key)
        n_cv = sum(1 for r in rows if r[0].startswith("cv"))
        A(f"{kor} {n_cv}폴드 {split_total(key):,}장")
        A(f"  {POOL}/splits/{key}/cv1   (cv1~cv{n_cv})")
    A(f"합계 {sum(split_total(k) for k, _ in FRUITS):,}장")
    A("")
    A("[쓰는 법] yaml 의 DATASET.ROOT 한 줄만 바꾸면 됩니다.")
    A("DATASET:")
    A(f"  ROOT: {POOL}/splits/apple/cv1")
    A("")
    A("4과일 비교는 cv1~cv5 로 맞추세요.")
    A("블루베리 cv6 은 예전 6-fold 실험용이라 비교표에는 빼주세요.")
    A("")
    A("[복사 안 하셔도 됩니다]")
    A("lab 그룹 전원이 읽을 수 있게 열어놨습니다. 위 경로를 그대로 쓰시면 됩니다.")
    A("꼭 복사하셔야 하면 -a 를 쓰세요. -L 은 절대 쓰지 마세요.")
    A(f"  (O) cp -a  {POOL} 내폴더/     → 약 {pool_gb:.0f}GB")
    A(f"  (X) cp -rL {POOL} 내폴더/     → 약 {full_gb:.0f}GB 로 불어납니다")
    A("splits 안이 전부 바로가기라, -L 을 붙이면 같은 사진이 폴드마다 복사됩니다.")
    A("")
    A("[꼭 알아두실 것]")
    A("1) 블루베리는 1,195장 전량 · 7:1:2 로 새로 나눴습니다 (2026-08-08).")
    A("   0806 미팅에서 뺐던 4K 128장을 다시 넣었고, 예전 분할이 7:1:2가 아니라")
    A("   약 67:17:17 이었어서 팀 규칙에 맞춰 다시 떴습니다.")
    A("   폴드 구성이 바뀌어 기존 블루베리 192런과 직접 비교는 안 됩니다. 재학습 필요합니다.")
    A("   ※ 블루베리만 '영상 단위'로 뽑습니다. 파일명이 '영상이름_프레임번호' 라,")
    A("     한 장씩 랜덤으로 뽑으면 같은 영상이 학습과 시험에 같이 들어가 점수가 부풀려집니다.")
    A("2) 사과는 720x1280 을 1080x1920 으로 1.5배 키운 겁니다. 논문 Method 에 적어야 합니다.")
    A("3) 포도는 토이 100장에서 전체 2,502장으로 교체했습니다. 기존 포도 결과와 비교 불가입니다.")
    A("4) 사과 cv1~cv5 는 사진 단위 무작위 분할이라 동영상 앞뒤 프레임이 학습/시험에")
    A("   갈릴 수 있습니다(점수가 실제보다 높게 나올 수 있음).")
    A("   single(2015학습/2016시험) 로도 한 번 돌려보시길 권합니다.")
    A("")
    A(f"자세한 설명은 {POOL}/README.md 에 있습니다.")
    return "\n".join(S) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "문서/260807_카톡_데이터셋안내.txt"))
    ap.add_argument("--short-out", default=str(ROOT / "문서/260807_카톡_데이터셋안내_짧은판.txt"),
                    help="카톡에 한 번에 붙여넣기 좋은 짧은 버전")
    args = ap.parse_args()

    # 포도 교체(swap)가 끝났는지 확인
    grape_cv1 = POOL / "splits/grape/cv1/train/images"
    grape_train = count(grape_cv1)
    pending = POOL / "splits/grape_2502"
    warn = ""
    if pending.is_dir() and grape_train < 1000:
        warn = ("\n⚠️ 아직 포도 폴드 교체를 안 하셨습니다. 먼저 아래를 실행하고 이 스크립트를 다시 돌리세요.\n"
                "   bash semantic-segmentation/scripts/swap_grape_splits_260807.sh\n")

    # 복사 안내에 쓸 실제 용량 (디스크에서 직접 계산)
    pool_bytes = sum(p.stat().st_size for f, _ in FRUITS
                     for sub in ("images", "masks")
                     for p in (POOL / f / sub).iterdir()
                     if (POOL / f / sub).is_dir())
    link_bytes, n_links = 0, 0
    for p in (POOL / "splits").rglob("*"):
        if p.is_symlink():
            n_links += 1
            try:
                link_bytes += p.stat().st_size      # stat() 은 링크를 따라간다
            except OSError:
                pass
    pool_gb = pool_bytes / 1e9
    full_gb = (pool_bytes + link_bytes) / 1e9

    L: list[str] = []
    A = L.append
    A("[데이터셋 안내] 4과일 화소 통일본 — 최종본")
    A("")
    A("교수님 지시대로 4개 데이터셋 사진의 가로세로 비율은 그대로 두고,")
    A("총 화소 수만 1440x1440(=2,073,600)에 맞춰 리사이즈했습니다.")
    A("")
    A("※ 해상도(가로x세로)는 데이터셋마다 다릅니다. 맞춘 건 '화소 수'입니다.")
    A("  비율을 억지로 맞추면 사진이 찌그러져서 교수님이 그 방식을 물리셨습니다.")
    A("  학습 때 어차피 512x512 로 크롭하므로 해상도가 달라도 됩니다.")
    A("")
    A("📁 공통 경로 (여기만 복사하시면 됩니다)")
    A(f"{POOL}/")
    A("")
    A("=" * 46)
    A("과일별 경로 · 폴드 수 · 장수")
    A("=" * 46)

    total = 0
    for key, kor in FRUITS:
        rows = fold_rows(key)
        n_img = split_total(key)
        total += n_img
        n_cv = sum(1 for r in rows if r[0].startswith("cv"))
        A("")
        A(f"■ {kor} — {n_cv}폴드 · 총 {n_img:,}장")
        A(f"   해상도: {resolutions(key, key)}")
        A(f"   경로: {POOL}/splits/{key}/cv1  (cv1~cv{n_cv})")
        L.extend(compress(rows))

    A("")
    A("=" * 46)
    A(f"합계 {total:,}장  (팀 표준 기준)")
    A("")
    A("▶ yaml 은 DATASET.ROOT 한 줄만 바꾸시면 됩니다.")
    A("DATASET:")
    A(f"  ROOT: {POOL}/splits/apple/cv1")
    A("")
    A("▶ 4과일 비교 실험은 cv1~cv5 로 맞추세요. 조건이 같아집니다.")
    A("   · 블루베리 cv6 은 예전 6-fold 실험(192런)과의 연속성 때문에 남긴 것이라")
    A("     비교표에는 넣지 마세요.")
    A("   · single / official 폴더는 각 데이터셋의 원래 분할입니다. 참고용입니다.")
    A("")
    A("=" * 46)
    A("꼭 알아두실 것 4가지")
    A("=" * 46)
    A("")
    A("1) 블루베리는 1,195장 전량 · 7:1:2 로 새로 나눴습니다 (2026-08-08).")
    A("   0806 미팅에서 뺐던 4K 128장(Camera 4)을 다시 넣어 전량을 씁니다.")
    A("   → 예전 분할은 7:1:2 가 아니라 약 67:17:17 이었어서 팀 규칙에 맞춰 다시 떴습니다.")
    A("   → 폴드 구성이 바뀌었으니 기존 블루베리 192런 결과와 직접 비교 불가. 재학습 필요합니다.")
    A("   → ※ 블루베리만 '영상 단위'로 뽑습니다. 파일명이 Camera 3 Video (11)_181.png 처럼")
    A("     '어느 영상의 몇 번째 프레임' 이라, 한 장씩 랜덤으로 뽑으면 같은 영상이")
    A("     학습과 시험에 동시에 들어가 점수가 부풀려집니다. 영상 288개를 통째로 갈랐고,")
    A("     같은 영상이 train/val/test 에 걸치는 경우는 6폴드 전부 0건입니다.")
    A("")
    A("2) 사과는 720x1280 -> 1080x1920 으로 1.5배 키운 겁니다.")
    A("   사진은 MinneApple 원본 그대로이고 크기만 키웠습니다. 논문 Method 에 명시 필요합니다.")
    A("")
    A("3) 포도는 토이 100장 -> 전체 2,502장으로 교체했습니다.")
    A("   기존 포도 결과(54조합)는 이 데이터와 비교 불가입니다. 데이터가 25배라 학습 시간도 늘어납니다.")
    A("")
    A("4) 사과 cv1~cv5 는 사진 단위 무작위 분할이라, 동영상 앞뒤 프레임이")
    A("   학습/시험에 갈라져 들어갈 수 있습니다(점수가 실제보다 높게 나올 수 있음).")
    A("   비교하려면 single(2015학습/2016시험) 로도 한 번 돌려보시는 걸 권합니다.")
    A("")
    A("=" * 46)
    A("복사 안 하셔도 됩니다 (중요)")
    A("=" * 46)
    A("")
    A("이 폴더는 lab 그룹 전원이 읽을 수 있게 열려 있습니다.")
    A("그냥 yaml 의 ROOT 에 위 경로를 그대로 적으시면 바로 학습됩니다.")
    A("→ 디스크도 안 쓰고, 제가 데이터를 고치면 자동으로 반영됩니다.")
    A("")
    A("굳이 내 폴더로 복사하셔야 한다면:")
    A("")
    A(f"  (O) cp -a  {POOL} 내폴더/     ← 약 {pool_gb:.0f}GB. 이걸 쓰세요")
    A(f"  (X) cp -rL {POOL} 내폴더/     ← 약 {full_gb:.0f}GB 로 불어납니다. 쓰지 마세요")
    A("")
    A("  · splits 안이 전부 바로가기(심볼릭 링크)라 -L 을 붙이면 같은 사진이")
    A(f"    폴드마다 실파일로 복사됩니다({n_links:,}개). -a 는 바로가기를 그대로 둡니다.")
    A("  · 바로가기가 상대경로라 폴더째 옮겨도 안 깨집니다.")
    A("")
    A("  폴드 하나만 따로 떼고 싶으시면 그때만 -L 을 쓰세요:")
    A(f"    cp -rL {POOL}/splits/grape/cv1 내폴더/")
    A("")
    A("▶ 자세한 설명은 그 폴더 안 README.md 에 있습니다.")
    A("")
    A(f"(작성 {datetime.now().strftime('%Y-%m-%d %H:%M')} 곽동신)")

    text = "\n".join(L) + "\n"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)

    short = build_short(pool_gb, full_gb)
    short_out = Path(args.short_out)
    short_out.write_text(short)

    print(short)
    if warn:
        print(warn)
    print(f"[저장] 짧은판 {short_out}  ({len(short)}자)")
    print(f"[저장] 전체판 {out}  ({len(text)}자)")


if __name__ == "__main__":
    main()
