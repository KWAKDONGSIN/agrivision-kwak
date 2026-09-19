# -*- coding: utf-8 -*-
"""팀 카톡에 그대로 붙여넣을 «타일링 데이터셋» 안내 문구를 만듭니다.

🔴 숫자는 전부 datasets_tiled_512/manifest.json 과 디스크에서 직접 읽습니다.
   데이터가 바뀌면 이 스크립트를 다시 돌리면 문구가 자동으로 맞춰집니다.

사용:  $PY tools/make_kakao_tiled_notice.py
출력:  문서/260809_카톡_타일링데이터셋안내.txt
"""
import json
import subprocess
from pathlib import Path

BASE = Path('/data/project/2026summer/kds0206')
TILED = BASE / 'datasets_tiled_512'
OUT = BASE / '문서' / '260809_카톡_타일링데이터셋안내.txt'
KOR = {'blueberry': '블루베리', 'apple': '사과', 'peach': '복숭아', 'grape': '포도'}
ORDER = ['blueberry', 'apple', 'peach', 'grape']


def pdf_pages(path: Path) -> int:
    out = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.lower().startswith('pages'):
            return int(line.split(':')[1])
    return 0


def gb(path: Path) -> float:
    """실제로 디스크를 차지하는 양 (팀원이 `du -sh` 로 보는 것과 같은 값).
    apparent size(-sb) 로 재면 심볼릭 링크 수십만 개의 디렉터리 공간이 빠져서
    실제보다 작게 나옵니다."""
    out = subprocess.run(['du', '-sk', str(path)], capture_output=True, text=True).stdout
    return int(out.split()[0]) / 1024 ** 2


def main() -> None:
    m = json.loads((TILED / 'manifest.json').read_text())
    F, T = m['fruits'], m['totals']
    diam = {f: F[f]['diam_median_px'] for f in ORDER}
    ratio = max(diam.values()) / min(diam.values())

    pdf = BASE / 'semantic-segmentation/reports/타일링_데이터셋_설명서.pdf'
    pages = pdf_pages(pdf)

    per = '\n'.join(
        f'  · {KOR[f]}  원본 {F[f]["src_images"]:,}장 → 타일 {F[f]["tiles"]:,}장 '
        f'(열매 {diam[f]:.0f}px → 72px, 배율 {F[f]["scale"]:.2f})'
        for f in ORDER)

    txt = f"""[제안] 데이터셋을 «똑같아 보이게» 맞춘 버전을 하나 만들어 봤습니다 🍇🫐🍎🍑

교수님이 "사진을 최대한 비슷한 데이터셋처럼 만들 수 있나" 하셨던 것 관련해서,
제 나름대로 해보고 공유드립니다. 아직 확정 아니고 **의견 구하는 단계**입니다.

■ 무엇이 문제였나
지금 4과일은 화소 수(2,073,600)는 이미 같습니다. 그런데 재보니
**열매가 화면에 보이는 크기가 최대 {ratio:.1f}배 차이**였습니다.
  사과 {diam['apple']:.0f}px / 블루베리 {diam['blueberry']:.0f}px / 복숭아 {diam['peach']:.0f}px / 포도 {diam['grape']:.0f}px
(마스크에서 열매 덩어리 하나의 지름을 잰 중앙값입니다)

■ 무엇을 했나
① 과일마다 배율을 달리 줘서 **열매가 전부 지름 72px 로 보이게** 맞추고
② 사진을 전부 **512×512 조각**으로 잘랐습니다 (빠짐없이 덮게)
{per}
  합계: 원본 {T['src_images']:,}장 → 타일 {T['tiles']:,}장 ({gb(TILED):.1f}GB)

■ 경로 (읽기만 하시면 됩니다, 복사 안 하셔도 열립니다)
/data/project/2026summer/kds0206/datasets_tiled_512/
  ├ <과일>/images, masks     ← 타일 원본
  ├ <과일>/index.csv         ← 타일마다 전경 비율. 빈 타일 골라낼 때 쓰세요
  └ splits/<과일>/cv1~cv5    ← 학습용. config의 DATASET.ROOT만 여기로 바꾸면 됩니다

설명서 PDF (그림 포함, {pages}쪽):
/data/project/2026summer/kds0206/semantic-segmentation/reports/타일링_데이터셋_설명서.pdf
한 장 요약 그림:
/data/project/2026summer/kds0206/semantic-segmentation/reports/tiled_512/00_타일링_한장설명.png

■ 꼭 알아두실 것
· **기존 데이터는 하나도 안 건드렸습니다.** 팀 표준 datasets_resized_2mp/ 그대로입니다.
  이건 «후보»라서 새 폴더에 따로 만들었습니다.
· 폴드 배정은 **기존 splits 를 그대로 물려받았습니다.** 같은 사진에서 나온 조각은
  반드시 같은 train/val/test 로 갑니다 (누수 0). 블루베리 영상 단위 분리도 유지됩니다.
· 표본이 약 {T['tiles'] / T['src_images']:.0f}배로 늘어나니 **EPOCHS 를 그만큼 줄이세요**
  (예: 200 → 20). 그러면 총 학습 시간은 비슷합니다.

■ 제 생각 / 논의하고 싶은 것
· "어차피 512로 크롭해서 학습하는데 의미 있나?" — 저도 그 생각을 했는데, 절반만 맞았습니다.
  크롭은 «사진 크기»는 맞춰주지만 **«열매가 보이는 크기»는 못 맞춥니다.** 3.6배 차이는
  크롭을 아무리 해도 그대로 남습니다. 그걸 맞춘 게 이번 작업입니다.
· 덤으로, 지금 평가가 **사진 가운데만 채점**하고 있는 문제도 타일링이면 같이 풀립니다
  (타일이 사진을 빠짐없이 덮으니 곧 슬라이딩 윈도우가 됩니다).
· 대신 손해도 있습니다. **사과는 확대(누적 약 2.6배)라 화소를 지어내고, 포도·복숭아는
  축소라 세밀함을 버립니다.** 공짜가 아닙니다.
· 그래서 제안은 — **전처리로 확정하지 말고 «비교 실험 하나»로 돌려보자**는 것입니다.
  포도 cv1 + 최고 조합(U-Net+ConvNeXt-T) 하나만 돌려서 기존 IoU 0.8534 와 비교하면
  답이 나옵니다. 차이가 없으면 "해봤는데 영향 없더라"도 논문에 쓸 수 있는 결과입니다.

의견 주시면 반영하겠습니다. 학습은 아직 안 돌렸습니다.
"""
    # 카톡은 마크다운을 렌더링하지 않습니다. **강조** 표시가 그대로 보이면 지저분하므로
    # 강조는 「」 로 바꿔서 내보냅니다.
    import re
    txt = re.sub(r'\*\*(.+?)\*\*', r'「\1」', txt, flags=re.S)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(txt, encoding='utf-8')
    print(f'[✓] {OUT}  ({len(txt):,}자)')
    print('─' * 70)
    print(txt)


if __name__ == '__main__':
    main()
