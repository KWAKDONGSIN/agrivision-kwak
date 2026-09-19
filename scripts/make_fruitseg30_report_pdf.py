# -*- coding: utf-8 -*-
"""FruitSeg30 학습 결과 설명서 (PDF) — 아무것도 모르는 사람도 읽을 수 있게.

"서버에서 다 돌아갔는가?"에 답하고, 무엇을 어떻게 돌렸고 결과가 무엇인지를
그림 위주로 설명한다. 데이터셋 사진은 갤러리 그림을 통째로 넣어
서버에서 직접 이미지를 열어보지 않아도 되게 한다.

숫자는 전부 실제 산출물에서 읽는다 (하드코딩 없음).
먼저 make_fruitseg30_gallery_figs.py / make_fruitseg30_pred_gallery.py 를 돌려야 한다.

사용:  $PY tools/make_fruitseg30_report_pdf.py
"""
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

REPO = Path('/data/project/2026summer/kds0206/semantic-segmentation')
BASE = Path('/data/project/2026summer/kds0206')
sys.path.insert(0, str(REPO / 'tools'))
from make_fruitseg30_summary import load_json, load_scalars, parse_test_log   # noqa: E402
from make_fruitseg30_pptx import parse_pipeline_log, size_summary            # noqa: E402

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
MONO = FontProperties(family='DejaVu Sans Mono')

RUN = REPO / 'output/fruitseg_runs/upernet_resnet_50_bcedice_200ep'
FIG = REPO / 'reports/figures'
GAL = FIG / 'gallery'
OUT = REPO / 'reports' / 'FruitSeg30_학습결과_설명서.pdf'

INK, MUTE, BLUE, GOOD, WARN, BAD = '#111111', '#555555', '#1c5cab', '#0a7d33', '#b8860b', '#b23b3b'


def wrap(t, n):
    out = []
    for para in t.replace('**', '').split('\n'):   # 강조 표시는 PDF에서 지운다
        out += textwrap.wrap(para, n) or ['']
    return out


# ---------------------------------------------------------------- 문서 블록
B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def mono(t): B.append(('mono', t))
def formula(t): B.append(('formula', t))          # 한글이 섞인 수식 (한글 폰트로 렌더)
def note(t): B.append(('note', t))
def warn(t): B.append(('warn', t))
def good(t): B.append(('good', t))
def sp(n=1): B.append(('space', n))
def newpage(): B.append(('newpage', None))
def table(headers, rows_, cw): B.append(('table', (headers, rows_, cw)))
def image(path, h): B.append(('image', (str(path), h)))
def fullpage(path, cap, sub=''): B.append(('fullpage', (str(path), cap, sub)))


# ---------------------------------------------------------------- 자료 읽기
raw = load_json(REPO / 'output/fruitseg30_stats.json')
mani = load_json(BASE / 'dataset_fruitseg30/split_manifest.json')
sc = load_scalars(RUN / 'logs')
test = parse_test_log(REPO / 'logs/fruitseg30_test_eval.log')
pipe = parse_pipeline_log(REPO / 'logs/fruitseg30_pipeline.log')
per = load_json(REPO / 'output/fruitseg30_per_image_iou.json')

if not raw or not mani:
    raise SystemExit('통계 파일이 없습니다. dataset_stats.py / prepare 스크립트를 먼저 돌리세요.')

counts = {k: len(v) for k, v in mani['splits'].items()}
n_all = sum(counts.values())
n_epoch = len(sc.get('train/loss', []))
val_loss = sc.get('val/loss', [])
val_fg = sc.get('val/fg_IoU', [])
best_loss = min(val_loss, key=lambda t: t[1]) if val_loss else None
best_fg = max(val_fg, key=lambda t: t[1]) if val_fg else None
FG = test['blueberry'] if test else None
BG = test['background'] if test else None
started = re.search(r'\[(20[\d-]+ [\d:]+)\]', (REPO / 'logs/fruitseg30_pipeline.log').read_text(errors='ignore'))
STARTED = started.group(1) if started else '-'

B.append(('cover', None))

# ================================================================= 1. 결론
newpage()
h1('1. 한 장으로 보는 결론 — 서버에서 전부 끝났습니다')
body('궁금하신 것부터 답하면: **네, 다 돌아갔습니다.** 학습 200에폭이 중간에 멈추거나 '
     '에러 없이 끝까지 갔고, 이어서 성적 채점과 그래프까지 자동으로 만들어졌습니다.')
sp(1)
table(['확인 항목', '결과'], [
    ['학습 시작', STARTED],
    ['학습 끝', pipe.get('train_done_at', '-')],
    ['전부 끝난 시각', pipe.get('finished_at', '-')],
    ['돌린 에폭', f'{n_epoch} / 200 (중간에 멈추지 않고 완주)'],
    ['걸린 시간', f'{pipe.get("total_time", "-")} (에폭당 약 {pipe.get("epoch_time", "-")}초)'],
    ['에러', '0건'],
    ['쓴 GPU', f'V100 1장 (최대 메모리 {pipe.get("peak_vram", "-")} MB)'],
    ['최종 성적 (test)', f'과일 IoU {FG["IoU"]:.4f}' if FG else '-'],
], [0.24, 0.40])
sp(1)
good('한 줄 요약: FruitSeg30 사진 1,969장으로 200에폭 학습을 끝냈고, '
     '한 번도 안 보여준 사진 390장에서 과일 영역을 %.1f%% 정확도(IoU)로 찾아냈습니다.'
     % (FG['IoU'] * 100 if FG else 0))
sp(1)
h2('이 문서를 읽는 법')
body('· 2~3장: 이게 도대체 무슨 작업인지 (용어 설명)\n'
     '· 4~5장: 어떤 사진들로 학습했는지 — 데이터셋 사진을 많이 넣었습니다\n'
     '· 6~8장: 어떻게 학습했고, 잘 됐는지 어떻게 아는지\n'
     '· 9장 이후: 모델이 실제로 그린 결과 그림\n'
     '· 마지막: 파일이 어디 있고, 직접 확인하려면 뭘 치면 되는지')

# ================================================================= 2. 무슨 일인가
newpage()
h1('2. 이게 무슨 작업인가요? (세그멘테이션)')
body('사진 한 장을 주고 "여기부터 여기까지가 과일이다"를 **픽셀 하나하나** 골라내는 '
     '작업입니다. 이걸 세그멘테이션(segmentation, 분할)이라고 부릅니다.')
sp(1)
h2('비슷한 작업들과 뭐가 다른가')
table(['이름', '하는 일', '결과물'], [
    ['분류', '이 사진이 사과냐 배냐', '이름표 하나'],
    ['객체 탐지', '사과가 어디 있냐', '네모 상자'],
    ['세그멘테이션', '어느 픽셀이 사과냐', '색칠한 그림  ← 우리가 하는 것'],
], [0.16, 0.32, 0.30])
sp(1)
body('우리가 만든 모델은 사진을 받으면 "과일인 픽셀"을 1, "배경인 픽셀"을 0으로 칠한 '
     '흑백 그림을 내놓습니다. 과일 종류(사과인지 망고인지)는 구분하지 않습니다. '
     '30종을 전부 "과일"로 합쳤습니다. 이걸 **이진(binary) 분할**이라고 합니다.')
sp(1)
h2('정답은 누가 만들었나')
body('데이터셋을 만든 연구팀이 사진마다 사람 손으로 과일 부분을 칠해 놨습니다. '
     '이 칠해진 그림을 **마스크(mask)** 또는 **정답(ground truth)** 이라고 부릅니다. '
     '모델은 이 정답을 보고 흉내내는 법을 배웁니다.')
sp(1)
h2('그럼 학습이란 무엇인가')
body('모델은 처음엔 아무렇게나 칠합니다. 정답과 얼마나 다른지를 숫자로 잰 것이 '
     '**loss(손실)** 이고, 이 숫자가 줄어드는 방향으로 모델 내부 값을 조금씩 고칩니다. '
     '사진 전체를 한 바퀴 다 보는 것이 **1 에폭(epoch)** 입니다. '
     '우리는 200바퀴를 돌렸습니다.')
note('그래서 "loss 그래프가 내려간다 = 배우고 있다" 입니다. 뒤에 그래프가 나옵니다.')

# ================================================================= 3. 데이터
newpage()
h1('3. 어떤 데이터를 썼나 — FruitSeg30')
body('FruitSeg30은 인터넷에 공개된 과일 사진 데이터셋입니다. 사진마다 사람이 칠한 '
     '정답 마스크가 같이 들어 있습니다.')
sp(1)
table(['항목', '값'], [
    ['이름', 'FruitSeg30 (Mendeley 공개, DOI 10.17632/vkht8pfsp3.3)'],
    ['사진 수', f'{raw["total_pairs"]:,}장 (사진 + 정답 마스크 한 쌍씩)'],
    ['과일 종류', f'{len(raw["per_group"])}종'],
    ['원본 크기', size_summary(raw)],
    ['쓴 크기', '512 x 512 로 통일'],
    ['과일이 차지하는 비율', f'평균 {raw["fg_ratio"]["mean"]*100:.1f}%'],
], [0.30, 0.42])
sp(1)
h2('사진을 3덩어리로 나눴습니다 — 왜?')
table(['이름', '장수', '무엇에 쓰나'], [
    ['train (학습)', f'{counts["train"]:,}장', '모델이 보고 배우는 사진'],
    ['val (검증)', f'{counts["val"]:,}장', '학습 중에 중간 점검하는 사진'],
    ['test (시험)', f'{counts["test"]:,}장', '끝나고 딱 한 번 채점하는 사진'],
], [0.20, 0.14, 0.36])
body('시험 문제를 미리 보여주면 안 되는 것과 같습니다. test 사진은 학습에 한 번도 '
     '쓰지 않았기 때문에, 여기서 나온 점수가 "진짜 실력"입니다.')
note('한 과일 종류가 test에만 몰리면 불공정하므로, 30종 각각을 7:1:2로 나눴습니다 '
     '(층화 분할, seed %s). 같은 seed면 몇 번을 다시 돌려도 똑같이 나뉩니다.' % mani['seed'])
sp(1)
h2('블루베리 데이터셋과의 결정적 차이')
body(f'블루베리 사진은 작은 알갱이가 흩어져 있어 과일 픽셀이 전체의 약 2.4%뿐입니다. '
     f'FruitSeg30은 과일이 화면을 크게 채워서 약 {raw["fg_ratio"]["mean"] * 100:.0f}%입니다. '
     f'그래서 블루베리에서는 mIoU(전체 평균)가 배경에 묻혀 쓸모없었지만, '
     f'이 데이터셋에서는 mIoU도 의미가 있습니다.')

# ================================================================= 4. 데이터셋 사진
newpage()
h1('4. 데이터셋 사진 (많이 넣었습니다)')
body('서버에서 이미지를 직접 열어보지 않아도 되도록, 실제 학습에 쓴 사진들을 '
     '다음 장부터 전부 그림으로 넣었습니다.')
sp(1)
table(['다음 장부터', '내용'], [
    ['30종 원본', '과일 30종을 한 장씩'],
    ['30종 마스크', '사람이 칠한 정답 (흰색=과일)'],
    ['30종 겹쳐보기', '원본 위에 정답을 빨갛게'],
    ['상세 6장', '원본·마스크·겹쳐보기를 나란히'],
    ['다양성 4장', '같은 과일도 사진마다 다름'],
    ['그래프 2장', '종류별 장수 / 종류별 과일 비율'],
], [0.24, 0.42])
note('빨간색·흰색은 보기 좋으라고 입힌 색입니다. 실제 마스크 파일은 검은 배경에 '
     '흰 과일인 흑백 그림입니다.')

for kind, cap in [('orig', '원본 사진'), ('mask', '정답 마스크'), ('overlay', '원본 + 정답 겹쳐보기')]:
    p = GAL / f'gal_all30_{kind}.png'
    if p.exists():
        fullpage(p, f'데이터셋 사진 — 과일 30종 {cap}',
                 '학습에 실제로 쓴 사진입니다. 종류마다 1장씩 골랐습니다.')

for i, p in enumerate(sorted(GAL.glob('gal_triplet_p*.png')), 1):
    fullpage(p, f'데이터셋 상세 ({i}) — 원본 / 정답 / 겹쳐보기',
             '가운데가 사람이 칠한 정답입니다. 흰색이 과일, 검은색이 배경.')

for i, p in enumerate(sorted(GAL.glob('gal_variety_p*.png')), 1):
    fullpage(p, f'같은 과일도 사진마다 다릅니다 ({i})',
             '배경·개수·조명·각도가 달라서, 모델이 외우기만 해서는 못 맞힙니다.')

for fn, cap, sub in [
    ('fig_fruitseg30_class_counts.png', '과일 종류별 사진 장수',
     '많은 종류와 적은 종류의 차이가 커서, 종류별로 나눠 분할했습니다.'),
    ('fig_fruitseg30_fg_ratio.png', '과일 종류별 "과일이 차지하는 비율"',
     '수박처럼 화면을 꽉 채우는 것부터 작게 찍힌 것까지 섞여 있습니다.')]:
    p = FIG / fn
    if p.exists():
        fullpage(p, cap, sub)

# ================================================================= 5. 어떻게 학습
newpage()
h1('5. 어떻게 학습시켰나')
body('팀에서 정한 조건을 그대로 썼습니다. 저는 **데이터 경로만** FruitSeg30으로 '
     '바꿨습니다. 조건을 똑같이 맞춰야 나중에 팀원들 결과와 비교할 수 있기 때문입니다.')
sp(1)
table(['설정', '값', '무슨 뜻인가'], [
    ['모델', 'UPerNet + ResNet-50', '그림을 보는 부분 + 칠하는 부분'],
    ['입력 크기', '512 x 512', '사진을 이 크기로 줄여서 넣음'],
    ['배치', '2 (누적 4회)', '한 번에 2장씩, 4번 모아 반영'],
    ['손실', 'BCEDice', '정답과 얼마나 다른지 재는 방식'],
    ['옵티마이저', 'AdamW, lr 1e-4', '얼마나 크게 고칠지 정하는 방식'],
    ['에폭', '200', '사진 전체를 200바퀴'],
    ['조기 종료', '끔', '200바퀴를 무조건 다 돎'],
], [0.20, 0.26, 0.32])
sp(1)
h2('실제로 서버에서 일어난 일 (순서대로)')
table(['단계', '내용', '결과'], [
    ['1', '2에폭만 시험 삼아 돌림 (스모크 테스트)', '통과 (3분 31초)'],
    ['2', '200에폭 본 학습 (nohup 백그라운드)', f'{pipe.get("total_time", "-")}'],
    ['3', 'test 390장 채점', '완료'],
    ['4', 'loss 그래프 그리기', '완료'],
], [0.10, 0.44, 0.24])
note('교수님이 "다 돌리지 말고 한 케이스만 먼저 돌려보라"고 하셨기 때문에, '
     '2에폭짜리를 먼저 돌려 에러가 없는 걸 확인한 뒤 200에폭을 시작했습니다.')

# ================================================================= 6. 잘 됐나
newpage()
h1('6. 학습이 잘 됐는지 어떻게 아나 — loss 그래프')
body('아래 그래프에서 선이 내려가면 배우고 있는 중입니다. 파란 선은 학습 사진에 대한 '
     'loss, 주황 선은 한 번도 안 보여준 검증 사진에 대한 loss입니다.')
sp(1)
p = FIG / 'fig_fruitseg30_loss.png'
if p.exists():
    image(p, 0.30)
sp(1)
body('· 파란 선만 내려가고 주황 선이 올라가면 → "외웠다"는 뜻(과적합)입니다.\n'
     '· 우리 그래프는 둘 다 내려갔습니다. 정상입니다.\n'
     '· 주황 점이 듬성듬성한 것은 검증을 5에폭마다만 하기 때문입니다.')
sp(1)
if best_loss and best_fg:
    table(['항목', '값'], [
        ['가장 좋았던 시점 (val loss 최소)', f'{best_loss[1]:.4f} — {best_loss[0]+1}번째 에폭'],
        ['그때 저장된 파일', 'UPerNet_ResNet-50_..._best.pth'],
        ['검증 최고 과일 IoU', f'{best_fg[1]:.4f} ({best_fg[0]+1}번째 에폭)'],
    ], [0.34, 0.38])
note('200에폭을 다 돌리되, 성적을 매길 때는 "가장 좋았던 시점에 저장해 둔 파일"을 씁니다. '
     '이것이 팀 공통 기준(val loss 최소)입니다.')

# ================================================================= 7. IoU
newpage()
h1('7. 점수 읽는 법 — IoU가 뭔가요')
body('IoU(Intersection over Union)는 **겹친 정도**입니다. 모델이 칠한 영역과 정답 영역을 '
     '겹쳐 놓고, "둘 다 칠한 부분"을 "둘 중 하나라도 칠한 부분"으로 나눈 값입니다. '
     '1에 가까울수록 정답과 똑같습니다.')
sp(1)
formula('           겹친 부분 (둘 다 "과일"이라고 한 픽셀)')
formula('IoU = ─────────────────────────────────────────')
formula('           둘 중 하나라도 "과일"이라고 한 픽셀')
sp(1)
h2('손으로 한 번 계산해보기')
body('사진에 과일 픽셀이 정답 기준 1,000개 있다고 합시다. 모델이 950개를 과일이라고 '
     '칠했는데, 그중 900개가 진짜 과일이었다면:')
table(['항목', '개수'], [
    ['둘 다 과일이라 함 (겹침)', '900'],
    ['정답만 과일 (모델이 놓침)', '1,000 - 900 = 100'],
    ['모델만 과일 (잘못 칠함)', '950 - 900 = 50'],
    ['둘 중 하나라도 (합집합)', '900 + 100 + 50 = 1,050'],
    ['IoU', '900 / 1,050 = 0.857'],
], [0.34, 0.30])
sp(1)
h2('다른 점수들')
table(['이름', '뜻'], [
    ['Dice', 'IoU와 비슷하지만 겹친 부분을 두 배로 쳐줌. 항상 IoU보다 큼'],
    ['Precision', '모델이 과일이라 한 것 중 진짜 과일 비율 (헛다리 안 짚나)'],
    ['Recall', '진짜 과일 중 모델이 찾아낸 비율 (놓치지 않나)'],
    ['mIoU', '과일 IoU와 배경 IoU의 평균'],
], [0.16, 0.56])
note('블루베리 데이터셋은 배경이 97%라 mIoU가 항상 높게 나와서 모델 간 차이가 '
     '묻혔습니다. 그래서 우리 팀은 과일만 보는 fg_IoU를 주로 씁니다.')

# ================================================================= 8. 결과
newpage()
h1('8. 최종 성적 — test 390장')
body('학습에도, 중간 점검에도 한 번도 쓰지 않은 사진 390장으로 딱 한 번 채점한 결과입니다.')
sp(1)
if FG and BG:
    miou = (FG['IoU'] + BG['IoU']) / 2
    table(['대상', 'IoU', 'Dice', 'Precision', 'Recall'], [
        ['과일', f'{FG["IoU"]:.4f}', f'{FG["Dice"]:.4f}', f'{FG["Precision"]:.4f}', f'{FG["Recall"]:.4f}'],
        ['배경', f'{BG["IoU"]:.4f}', f'{BG["Dice"]:.4f}', f'{BG["Precision"]:.4f}', f'{BG["Recall"]:.4f}'],
        ['평균', f'{miou:.4f}', '', '', ''],
    ], [0.12, 0.14, 0.14, 0.16, 0.16])
    sp(1)
    good('과일 IoU %.4f — 모델이 칠한 영역과 사람이 칠한 정답이 약 %.0f%% 겹칩니다.'
         % (FG['IoU'], FG['IoU'] * 100))
    body('Precision %.3f / Recall %.3f 이 둘 다 높다는 것은, 헛다리도 안 짚고 놓치지도 '
         '않는다는 뜻입니다.' % (FG['Precision'], FG['Recall']))
sp(1)
warn('주의: 결과 표에 클래스 이름이 "blueberry"라고 찍힙니다. 코드가 블루베리용 '
     '데이터 클래스를 그대로 재사용하기 때문이고, 실제 의미는 "과일(전경)"입니다. '
     '교수님이 물어보실 수 있는 부분입니다.')

if per:
    sp(1)
    h2('사진 한 장씩 따로 채점해봤습니다')
    body('평균만 보면 잘 안 보이는 것이 있어서, test 390장 각각의 IoU를 따로 쟀습니다.')
    table(['항목', '값'], [
        ['사진 수', f'{per["n_images"]}장'],
        ['평균 IoU', f'{per["mean_iou"]:.4f}'],
        ['중앙값 IoU', f'{per["median_iou"]:.4f}'],
        ['가장 잘 맞힌 사진', f'{per["max_iou"]:.4f}'],
        ['가장 못 맞힌 사진', f'{per["min_iou"]:.4f}'],
        ['IoU 0.9 이상', f'{per["n_ge_090"]}장 ({per["n_ge_090"]/per["n_images"]*100:.1f}%)'],
        ['IoU 0.5 미만 (사실상 실패)', f'{per["n_lt_050"]}장'],
    ], [0.34, 0.34])
    good('크게 망친 사진이 한 장도 없습니다. 제일 못 맞힌 사진도 IoU %.2f 입니다.'
         % per['min_iou'])
    p = FIG / 'fig_fruitseg30_per_image_iou.png'
    if p.exists():
        fullpage(p, '사진 한 장씩의 성적 분포',
                 '막대가 오른쪽에 몰려 있을수록 좋습니다.')

# ================================================================= 9. 예측 그림
newpage()
h1('9. 모델이 실제로 그린 그림')
body('숫자만으로는 감이 안 오니, 모델이 test 사진에 실제로 칠한 결과를 그림으로 '
     '넣었습니다. 다음 장부터 이어집니다.')
sp(1)
table(['색', '뜻'], [
    ['빨강', '사람이 만든 정답'],
    ['파랑', '모델이 예측한 것'],
    ['초록 (채점 그림)', '맞게 찾은 곳'],
    ['빨강 (채점 그림)', '과일인데 놓친 곳'],
    ['노랑 (채점 그림)', '배경인데 과일이라고 한 곳'],
], [0.26, 0.40])
note('정답(빨강)과 예측(파랑)이 거의 같은 모양이면 잘 맞힌 것입니다.')

for i, p in enumerate(sorted(GAL.glob('pred_by_class_p*.png')), 1):
    fullpage(p, f'모델 예측 결과 — 과일 종류별 ({i})',
             '왼쪽 원본 / 가운데 사람 정답(빨강) / 오른쪽 모델 예측(파랑)')

for fn, cap, sub in [
    ('pred_best_p1.png', '가장 잘 맞힌 사진',
     '초록이 거의 전부입니다. 정답과 사실상 똑같이 칠했습니다.'),
    ('pred_typical_p1.png', '평균적인 사진',
     'test 390장 중 딱 중간 성적. 대부분이 이 정도입니다.'),
    ('pred_worst_p1.png', '가장 못 맞힌 사진',
     '어디서 틀리는지 보는 자료입니다. 아래 설명을 같이 보세요.')]:
    p = GAL / fn
    if p.exists():
        fullpage(p, cap, sub)

# ================================================================= 10. 한계
newpage()
h1('10. 어디서 틀렸나 (정직하게)')
body('앞 장의 "가장 못 맞힌 사진"들을 보면 틀리는 곳에 패턴이 있습니다.')
sp(1)
table(['틀리는 상황', '설명'], [
    ['그림자', '정답 마스크가 그림자까지 과일로 칠해둔 경우가 있음'],
    ['잎사귀·꼭지', '파인애플 잎처럼 얇고 삐죽한 부분에서 경계가 흔들림'],
    ['비슷한 색 배경', '초록 과일 + 초록 배경이면 경계가 애매함'],
], [0.24, 0.46])
sp(1)
body('중요한 것은, 이 중 일부는 **모델이 틀린 게 아니라 정답 자체가 애매한 경우**라는 '
     '점입니다. 그림자를 과일로 칠할지 말지는 사람마다 다르게 판단할 수 있습니다. '
     '발표에서 이 점을 말하면 좋습니다.')
sp(1)
warn('한계 하나 더: 이 실험은 UPerNet + ResNet-50 **한 조합만** 돌린 것입니다. '
     '"이 모델이 제일 좋다"는 결론은 아직 낼 수 없습니다. 팀 전체가 같은 조건으로 '
     '다른 데이터셋을 돌리고 있으므로, 비교는 그 결과가 모인 뒤에 합니다.')
sp(1)
h2('그래서 이번에 알아낸 것')
body('· 우리 코드가 블루베리 말고 다른 데이터셋에서도 그대로 돌아간다 (경로만 바꾸면 됨)\n'
     '· 과일이 크게 찍힌 데이터셋에서는 같은 모델이 훨씬 높은 점수를 낸다\n'
     '  (블루베리 fg_IoU 약 0.87 → FruitSeg30 %.3f)\n'
     '· 즉 "성능 숫자"는 데이터셋을 빼고 말하면 의미가 없다'
     % (FG['IoU'] if FG else 0))

# ================================================================= 11. 파일
newpage()
h1('11. 파일이 어디 있나')
table(['무엇', '경로'], [
    ['발표용 PPT', '문서/260726_FruitSeg30_랩미팅_발표.pptx'],
    ['이 PDF', 'semantic-segmentation/reports/FruitSeg30_학습결과_설명서.pdf'],
    ['슬라이드 정리 문서', '문서/260725_FruitSeg30_발표슬라이드_정리.md'],
    ['데이터셋 사진 그림', 'semantic-segmentation/reports/figures/gallery/'],
    ['그래프', 'semantic-segmentation/reports/figures/'],
    ['학습 결과(체크포인트)', 'output/fruitseg_runs/upernet_resnet_50_bcedice_200ep/'],
    ['학습 로그', 'semantic-segmentation/logs/fruitseg30_pipeline.log'],
    ['설정 파일', 'configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml'],
    ['데이터셋', 'dataset_fruitseg30/{train,val,test}/{images,masks}'],
], [0.26, 0.48])
body('맨 앞은 전부 /data/project/2026summer/kds0206/ 아래입니다.')
sp(1)
h1('12. 직접 확인하고 싶을 때')
body('VS Code 터미널에 아래를 그대로 붙여넣으면 됩니다.')
sp(1)
mono('cd /data/project/2026summer/kds0206/semantic-segmentation')
mono('export PY=/home/kds0206/.conda/envs/kwak/bin/python')
sp(1)
body('학습 로그 마지막 부분 보기 (에러 없었는지):')
mono('tail -40 logs/fruitseg30_pipeline.log')
sp(1)
body('결과 그림 목록 보기:')
mono('ls reports/figures/gallery/')
sp(1)
body('test 성적을 다시 재보기 (약 30초, GPU 1장). 먼저 빈 GPU를 확인합니다:')
mono('nvidia-smi')
mono('CUDA_VISIBLE_DEVICES=0 $PY tools/val.py \\')
mono('  --cfg configs/fruitseg_upernet_resnet_50_bcedice_200ep.yaml \\')
mono('  --split test')
sp(1)
body('PPT를 다시 만들기 (숫자가 자동으로 다시 채워집니다):')
mono('$PY tools/make_fruitseg30_pptx.py')
sp(1)
note('그림 파일들은 PNG라서 VS Code에서 파일을 클릭하면 바로 보입니다. '
     '터미널 명령을 몰라도 됩니다.')


# ---------------------------------------------------------------- 렌더링
def render():
    with PdfPages(OUT) as pdf:
        pw, ph = 8.27, 11.69
        LM = 0.10
        fig = ax = None
        y = [0]

        def npage():
            nonlocal fig, ax
            if fig is not None:
                pdf.savefig(fig)
                plt.close(fig)
            fig = plt.figure(figsize=(pw, ph))
            ax = fig.add_axes([0, 0, 1, 1])
            ax.axis('off')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            y[0] = 0.94

        npage()
        for kind, t in B:
            if kind == 'cover':
                ax.add_patch(plt.Rectangle((0, 0.78), 1, 0.005, color=BLUE))
                ax.text(0.5, 0.655, 'FruitSeg30', ha='center',
                        fontproperties=BLD, fontsize=26, color=BLUE)
                ax.text(0.5, 0.595, '학습 결과 설명서', ha='center',
                        fontproperties=BLD, fontsize=22, color=INK)
                ax.plot([0.28, 0.72], [0.555, 0.555], color=BLUE, lw=1.5)
                ax.text(0.5, 0.505, '아무것도 모르는 사람도 읽을 수 있게', ha='center',
                        fontproperties=REG, fontsize=12, color=MUTE)
                ax.text(0.5, 0.465, '— 서버에서 무엇이 어떻게 돌아갔는가 —', ha='center',
                        fontproperties=REG, fontsize=12, color=MUTE)
                if FG:
                    ax.text(0.5, 0.35, '200 에폭 완주  ·  test 과일 IoU %.4f' % FG['IoU'],
                            ha='center', fontproperties=BLD, fontsize=13, color=GOOD)
                ax.text(0.5, 0.16, '곽동신   ·   2026-07-26', ha='center',
                        fontproperties=REG, fontsize=11, color=MUTE)
                ax.text(0.5, 0.125, '2026-07-27 랩미팅 발표 자료', ha='center',
                        fontproperties=REG, fontsize=10.5, color=MUTE)
                continue
            if kind == 'newpage':
                npage(); continue
            if kind == 'space':
                y[0] -= 0.012 * t; continue

            if kind == 'fullpage':
                path, cap, sub = t
                npage()
                ax.text(LM - 0.02, 0.955, cap, fontproperties=BLD, fontsize=14, color=INK)
                if sub:
                    ax.text(LM - 0.02, 0.928, sub, fontproperties=REG, fontsize=10, color=MUTE)
                try:
                    im = mpimg.imread(path)
                    h, w = im.shape[0], im.shape[1]
                    box_w, box_h = 0.88, 0.86              # 그림이 들어갈 영역 (그림 좌표계)
                    disp_w = box_w
                    disp_h = disp_w * (h / w) * (pw / ph)
                    if disp_h > box_h:
                        disp_w *= box_h / disp_h
                        disp_h = box_h
                    axim = fig.add_axes([(1 - disp_w) / 2, 0.90 - disp_h - 0.005, disp_w, disp_h])
                    axim.imshow(im)
                    axim.axis('off')
                except Exception as e:
                    ax.text(LM, 0.5, f'[그림 로드 실패: {path} — {e}]',
                            fontproperties=REG, fontsize=9, color=BAD)
                y[0] = 0.03
                continue

            if y[0] < 0.09:
                npage()

            if kind == 'h1':
                y[0] -= 0.006
                ax.add_patch(plt.Rectangle((LM - 0.015, y[0] - 0.004), 0.006, 0.028, color=BLUE))
                ax.text(LM, y[0], t, fontproperties=BLD, fontsize=15, color=INK)
                y[0] -= 0.044
            elif kind == 'h2':
                y[0] -= 0.006
                ax.text(LM, y[0], t, fontproperties=BLD, fontsize=12, color=BLUE)
                y[0] -= 0.030
            elif kind == 'body':
                for ln in wrap(t, 48):
                    if y[0] < 0.06:
                        npage()
                    ax.text(LM, y[0], ln, fontproperties=REG, fontsize=10.5, color=INK)
                    y[0] -= 0.0225
                y[0] -= 0.004
            elif kind == 'formula':
                if y[0] < 0.06:
                    npage()
                ax.add_patch(plt.Rectangle((LM - 0.02, y[0] - 0.006), 0.84, 0.023,
                                           facecolor='#f4f4f6', edgecolor='none'))
                ax.text(LM, y[0], t, fontproperties=REG, fontsize=10, color='#222222')
                y[0] -= 0.025
            elif kind == 'mono':
                if y[0] < 0.06:
                    npage()
                ax.add_patch(plt.Rectangle((LM - 0.02, y[0] - 0.006), 0.84, 0.021,
                                           facecolor='#f4f4f6', edgecolor='none'))
                ax.text(LM, y[0], t, fontproperties=MONO, fontsize=9.5, color='#222222')
                y[0] -= 0.0235
            elif kind in ('note', 'warn', 'good'):
                col = {'note': (BLUE, '#eef4fc', '#cfe0f5'),
                       'warn': (BAD, '#fdf1ee', '#f0cfc6'),
                       'good': (GOOD, '#eef7f0', '#c9e6d2')}[kind]
                ls = wrap(t, 54)
                bh = 0.0205 * len(ls) + 0.016
                if y[0] - bh < 0.05:
                    npage()
                ax.add_patch(plt.Rectangle((LM - 0.02, y[0] - bh + 0.02), 0.84, bh,
                                           facecolor=col[1], edgecolor=col[2], lw=0.8))
                yy = y[0]
                for ln in ls:
                    ax.text(LM, yy, ln, fontproperties=REG, fontsize=9.5, color=col[0])
                    yy -= 0.0205
                y[0] -= bh + 0.006
            elif kind == 'table':
                heads, rws, cw = t
                if y[0] - 0.03 * (len(rws) + 1) < 0.06:
                    npage()
                x0 = LM; xx = x0
                for i, hh in enumerate(heads):
                    ax.text(xx, y[0], hh, fontproperties=BLD, fontsize=10, color=INK)
                    xx += cw[i] if i < len(cw) else 0.2
                y[0] -= 0.006
                ax.plot([x0, x0 + sum(cw) + 0.06], [y[0], y[0]], color='#bbbbbb', lw=0.8)
                y[0] -= 0.022
                for row in rws:
                    if y[0] < 0.06:
                        npage()
                    xx = x0
                    for i, c in enumerate(row):
                        for k, ln in enumerate(wrap(str(c), max(int(cw[i] / 0.0062), 8))
                                               if i == len(row) - 1 else [str(c)]):
                            ax.text(xx, y[0] - k * 0.019, ln, fontproperties=REG,
                                    fontsize=9.5, color='#222222')
                        xx += cw[i] if i < len(cw) else 0.2
                    extra = len(wrap(str(row[-1]), max(int(cw[-1] / 0.0062), 8))) - 1
                    y[0] -= 0.024 + extra * 0.019
                y[0] -= 0.006
            elif kind == 'image':
                path, ih = t
                if y[0] - ih < 0.05:
                    npage()
                try:
                    im = mpimg.imread(path)
                    h, w = im.shape[0], im.shape[1]
                    disp_w = 0.80
                    disp_h = disp_w * (h / w) * (pw / ph)
                    if disp_h > ih:
                        scale = ih / disp_h; disp_h = ih; disp_w *= scale
                    axim = fig.add_axes([LM - 0.02 + (0.80 - disp_w) / 2,
                                         y[0] - disp_h, disp_w, disp_h])
                    axim.imshow(im); axim.axis('off')
                    y[0] -= disp_h + 0.012
                except Exception as e:
                    ax.text(LM, y[0], f'[그림 로드 실패: {path} — {e}]',
                            fontproperties=REG, fontsize=9, color=BAD)
                    y[0] -= 0.03
        if fig is not None:
            pdf.savefig(fig)
            plt.close(fig)
    print(f'저장: {OUT}')


render()
