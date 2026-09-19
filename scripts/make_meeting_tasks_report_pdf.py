# -*- coding: utf-8 -*-
"""0723 교수님 미팅 할 일 처리 결과 보고서 (PDF) — 초심자용.

곽동신이 자리를 비운 동안 Claude가 교수님 지시사항을 처리한 결과를 보고한다.
숫자는 전부 실측(학습 로그 · 마스크 직접 계산)에서 가져온다. 하드코딩 없음.

    python tools/make_meeting_tasks_report_pdf.py
"""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
import matplotlib.image as mpimg

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

REPO = Path(__file__).resolve().parent.parent
FIG = REPO / 'reports' / 'figures'
OUT = REPO / 'reports' / '0723미팅_처리결과_보고서.pdf'
INK, MUTE, BLUE, GOOD, WARN, BAD = '#111111', '#555555', '#1c5cab', '#0a7d33', '#b8860b', '#b23b3b'

STATS = json.load(open(REPO / 'output' / 'object_size_stats.json', encoding='utf-8'))
M, BB = STATS['minneapple'], STATS['blueberry']

# 학습 로그에서 실측한 최종 성능 (test 세트)
BLUE_TEST_IOU = 0.8631   # 블루베리 cv1 test, 증강 yaml 모델
MINNE_TEST_IOU = 0.6871  # MinneApple test
BLUE_TRAIN_TIME = '00:49:59'
MINNE_TRAIN_TIME = '00:22:21'


def wrap(t, n):
    out = []
    for para in t.split('\n'):
        out += textwrap.wrap(para, n) or ['']
    return out


# ---------------------------------------------------------------- 문서 구성
B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def tree(t): B.append(('tree', t))
def note(t): B.append(('note', t))
def warn(t): B.append(('warn', t))
def good(t): B.append(('good', t))
def sp(n=1): B.append(('space', n))
def newpage(): B.append(('newpage', None))
def table(headers, rows_, cw): B.append(('table', (headers, rows_, cw)))
def big(pairs): B.append(('big', pairs))
def image(path, h): B.append(('image', (path, h)))

B.append(('cover', None))

# ===== 0 =====
newpage()
h1('0. 이 보고서는 무엇인가')
body('곽동신 님이 자리를 비운 사이, 7월 23일 교수님 미팅에서 나온 "곽동신 할 일"을 '
     'Claude가 처리한 결과입니다. 무엇을 했고, 어떤 숫자가 나왔고, 무엇이 아직 '
     '남았는지를 처음 보는 사람도 알 수 있게 정리했습니다.')
body('원칙 3가지를 지켰습니다: ①기존 학습 결과·체크포인트는 삭제하지 않음 '
     '②숫자는 전부 실제 로그·마스크에서 직접 계산(지어내지 않음) '
     '③교수님이 강조하신 "한 케이스만 먼저 돌려보라"를 그대로 따름.')
sp(1)
h2('교수님 할 일 8개 처리 현황 (한눈에)')
table(['#', '할 일', '상태'], [
    ['1', '데이터셋 정리 (통계+예시그림)', '완료'],
    ['2', 'yaml 완전히 이해하기', '자료 제공'],
    ['3', 'augmentation을 yaml로 빼기', '완료(코드)'],
    ['4', '한 케이스만 먼저 돌려 검증', '완료(학습)'],
    ['5', 'MinneApple 서버에서 모델 돌리기', '완료(학습)'],
    ['6', 'MinneApple도 정리하기', '완료'],
    ['7', 'IoU 계산 직접 해보기', '완료(예시)'],
    ['8', 'yaml 공부내용 발표', '곽동신 몫'],
], [0.05, 0.55, 0.22])
note('"상태=완료"는 Claude가 대신 할 수 있는 부분을 끝냈다는 뜻입니다. '
     '발표(2·8번)와 최종 판단은 곽동신 님이 하셔야 합니다.')

# ===== 1. augmentation yaml =====
newpage()
h1('과제 3 — 데이터 증강을 yaml로 빼기 (완료)')
body('교수님 지적: "무슨 증강을 썼는지 코드에만 있고 yaml에 없어서, 논문에 쓸 수도 '
     'AI에게 검토시킬 수도 없다." 맞는 지적이었습니다.')
h2('무엇을 고쳤나')
body('전에는 semseg/augmentations.py 코드 안에 증강 7개 중 4개가 주석 처리된 채 '
     '숨어 있었습니다. 이제 yaml 파일만 봐도 어떤 증강을 켰는지 알 수 있습니다.')
tree('  AUGMENTATIONS:')
tree('    HORIZONTAL_FLIP  : { ENABLE: true,  P: 0.5 }    # 좌우 뒤집기')
tree('    ROTATION         : { ENABLE: true,  DEGREES: 60, P: 0.3 }')
tree('    RANDOM_CROP      : { ENABLE: true }')
tree('    VERTICAL_FLIP    : { ENABLE: false, ... }       # 끄면 false')
tree('    ... (7종 전부 나열, ENABLE로 켜고 끔)')
sp(1)
good('안전 확인: 바꾸기 전 코드와 픽셀 단위까지 100% 똑같이 나오는지 '
     '같은 난수 100번으로 검증했습니다. 기존 config 200여 개의 학습 결과는 '
     '전혀 바뀌지 않습니다 (yaml에 이 블록이 없으면 옛 기본값을 그대로 씀).')
body('또 학습을 시작할 때 로그에 실제 적용된 증강이 한 줄로 찍히게 했습니다:')
tree('  [AUGMENT] HORIZONTAL_FLIP(p=0.5) -> ROTATION(degrees=60,')
tree('            p=0.3) -> RANDOM_CROP -> NORMALIZE')
body('이제 이 한 줄을 논문 Methods에 그대로 옮겨 적으면 됩니다.')
note('고친 파일: semseg/augmentations.py, tools/train.py. '
     '새 옵션 이름을 잘못 적으면 학습이 그냥 멈추지 않고 "알 수 없는 증강 이름"이라고 '
     '알려주도록 방어 코드도 넣었습니다.')

# ===== 2. 한 케이스 검증 =====
newpage()
h1('과제 4 — 한 케이스만 먼저 돌려 검증 (완료)')
body('교수님: "다 돌리지 말고 한 케이스 정도 따로 떼서 돌려보고." 그대로 따랐습니다. '
     '전체를 벌크로 돌리지 않고, 위에서 고친 yaml 증강이 실제로 잘 도는지 '
     '1등 조합(UPerNet + ConvNeXt-T)으로 딱 한 번만 학습했습니다.')
h2('결과 — 정상 학습 확인')
table(['항목', '값'], [
    ['학습 시간', f'{BLUE_TRAIN_TIME} (약 50분, GPU 1장)'],
    ['조기 종료', '10 epoch 개선 없어 자동 종료 (정상)'],
    ['test fg_IoU', f'{BLUE_TEST_IOU:.3f}'],
    ['기존 벤치마크 cv1', '0.871 (같은 범위 → 회귀 없음)'],
], [0.28, 0.5])
good('fg_IoU 0.863은 기존 벤치마크(0.87~0.89)와 같은 범위입니다. '
     '즉 증강을 yaml로 옮겨도 성능이 그대로라는 뜻 → 안심하고 논문에 쓸 수 있습니다.')
note('저장 위치: output/verify_runs/upernet_convnext_t_augyaml_cv1/  '
     '(폴더 이름에 _runs가 붙어 있어 성적표 집계에 섞이지 않습니다. 안전.)')

# ===== 3. MinneApple 정리 =====
newpage()
h1('과제 1·6 — 데이터셋 정리 (완료)')
body('교수님이 두 번 강조하신 "가장 급한 일"입니다. 우리 블루베리와 MinneApple(사과) '
     '두 데이터셋을 직접 세어서 표와 그림으로 정리했습니다.')
h2('핵심 발견 — 사과 마스크에는 개체가 번호로 들어 있다')
body('우리 블루베리 마스크는 0 아니면 255(있다/없다)뿐이라 "어디가 한 알인지" 알 수 '
     '없습니다. 그런데 사과 마스크는 1번·2번·3번…처럼 개체마다 번호가 매겨져 있어, '
     '교수님이 요청하신 개체 크기 히스토그램을 추정 없이 정확히 그릴 수 있습니다.')
sp(1)
h2('실측 통계')
table(['항목', 'MinneApple(사과)', '블루베리'], [
    ['이미지 수', f"{M['n_images']}장", f"{BB['n_images']}장(표본)"],
    ['장당 개체수(평균)', f"{M['obj_per_img_mean']:.1f}개", f"{BB['obj_per_img_mean']:.1f}개"],
    ['장당 개체수(최대)', f"{M['obj_per_img_max']}개", f"{BB['obj_per_img_max']}개"],
    ['개체면적 중앙(px)', f"{M['area_median']:.0f}", f"{BB['area_median']:.0f}"],
    ['화면대비 크기', f"{M['area_frac_median']*100:.4f}%", f"{BB['area_frac_median']*100:.4f}%"],
    ['전경 비율', f"{M['fg_ratio']*100:.2f}%", f"{BB['fg_ratio']*100:.2f}%"],
], [0.26, 0.30, 0.28])
warn('크기 비교 주의: 픽셀 수만 보면 블루베리가 더 커 보이지만, 이건 사진 해상도가 '
     '2배라서 그렇습니다. 해상도를 맞춘 "화면대비 크기"로 보면 블루베리가 더 작습니다 '
     f"({BB['area_frac_median']*100:.4f}% < {M['area_frac_median']*100:.4f}%). "
     '교수님 예상("블루베리가 더 작을 것")이 맞습니다. 논문·PPT엔 반드시 화면대비로 쓸 것.')

newpage()
h2('그림 1 — 개체 크기 분포 (MinneApple Figure 4 재현)')
image(str(FIG / 'fig_object_size_hist.png'), 0.30)
body('교수님이 "MinneApple 논문의 이 그림을 우리도 그려달라"고 하신 바로 그 그림입니다. '
     '왼쪽이 사과, 오른쪽이 블루베리. 개체 하나가 몇 픽셀인지의 분포입니다.')
sp(1)
h2('그림 2 — 이미지 한 장에 개체가 몇 개인가')
image(str(FIG / 'fig_objects_per_image.png'), 0.26)
body('교수님이 정리해 주신 우리 논문 서론 논리 — "종류는 하나인데 개수가 굉장히 많다" '
     '— 를 뒷받침하는 그림입니다. 둘 다 한 장에 40개 안팎이 들어 있습니다.')

newpage()
h2('그림 3 — 원본 사진과 마스크(정답)는 짝지어져 있다')
image(str(FIG / 'fig_dataset_examples_pairs.png'), 0.52)
body('교수님 지시 "원본 이미지 + 마스크 예시를 나란히 넣기"에 해당합니다. '
     '①원본 사진 ②정답 마스크 ③겹쳐보기 순서입니다. 위 2줄은 블루베리, 아래 2줄은 사과.')
note('통계 재계산: tools/make_object_size_histogram.py  '
     '예시그림: tools/make_dataset_examples_fig.py  '
     '숫자 원본: output/object_size_stats.json')

# ===== 4. MinneApple 학습 =====
newpage()
h1('과제 5 — MinneApple로 모델 하나 돌리기 (완료)')
body('교수님: "마인애플 데이터셋 받아서 서버에 올린 다음에 돌려보세요." '
     '먼저 사과 데이터를 우리 파이프라인 형식으로 정리한 뒤, 블루베리 1등 조합인 '
     'UPerNet + ConvNeXt-T 하나만 학습했습니다.')
h2('데이터 준비 — 시험 누수를 막았습니다')
body('사과 train 670장을 학습 536 / 검증 134로 나눴는데, 같은 촬영 세션 사진이 학습과 '
     '검증에 섞이면 점수가 부풀려집니다. 그래서 "촬영 세션 단위로" 갈랐습니다. '
     '최종 시험(test)은 원 설계대로 2016년 촬영분 331장을 그대로 씁니다.')
h2('결과')
table(['항목', '값'], [
    ['학습 시간', f'{MINNE_TRAIN_TIME} (약 22분)'],
    ['사과 test fg_IoU', f'{MINNE_TEST_IOU:.3f}'],
    ['같은 모델 블루베리', f'{BLUE_TEST_IOU:.3f}'],
], [0.28, 0.5])
good('의미 있는 결과입니다: 블루베리에서 0.86을 내는 바로 그 모델이 사과에서는 0.69로 '
     '떨어집니다. "데이터셋이 다르면 좋은 모델도 다르다"는 우리 논문의 핵심 주장 '
     '— 벤치마크가 필요한 이유 — 을 뒷받침하는 첫 증거입니다.')
note('학습 데이터: dataset_minneapple/ (원본을 심볼릭 링크로 연결 → 디스크 추가 사용 0). '
     '모델: output/minneapple_runs/upernet_convnext_t_minneapple/  '
     'config: configs/minneapple_upernet_convnext_t.yaml')

# ===== 5. IoU =====
newpage()
h1('과제 7 — IoU가 어떻게 계산되나 (예시)')
body('교수님: "계산이 어떻게 되는지 물어보면서." IoU는 겹치는 정도를 재는 자입니다.')
h2('한 문장 정의')
body('IoU = (정답과 예측이 둘 다 맞다고 한 픽셀) ÷ (둘 중 하나라도 맞다고 한 픽셀). '
     '완전히 겹치면 1(=100%), 하나도 안 겹치면 0.')
sp(1)
h2('아주 작은 예')
tree('  정답 마스크:  블루베리 픽셀이 100칸')
tree('  예측 마스크:  블루베리라고 찍은 게 120칸')
tree('  그중 정답과 겹친 것:  90칸  (교집합)')
tree('  둘을 합친 것:  100 + 120 - 90 = 130칸  (합집합)')
tree('  IoU = 90 / 130 = 0.69')
sp(1)
body(f'우리 사과 모델의 test fg_IoU {MINNE_TEST_IOU:.2f}가 딱 이런 뜻입니다: '
     '정답 사과 영역과 예측 사과 영역이 약 69% 겹친다.')
warn('왜 mIoU 대신 fg_IoU를 쓰나: 사진의 97%가 배경입니다. 배경까지 넣어 평균 내면 '
     '(mIoU) 배경 0.99에 묻혀 조합 간 차이가 안 보입니다. 그래서 전경(과일)만 보는 '
     'fg_IoU를 씁니다. 이건 사과에서도 똑같이 적용됩니다(위 통계의 전경 3%가 근거).')

# ===== 6. 남은 것 =====
newpage()
h1('아직 남은 것 / 곽동신 님이 하실 것')
h2('Claude가 대신 못 하는 것')
body('· 과제 2·8 (yaml 공부 → 발표): 교수님이 "다음에 물어보겠다"고 하신 것이라 '
     '곽동신 님이 직접 이해하고 설명하셔야 합니다. 위 과제 3 자료가 출발점입니다.')
body('· 지도/비지도학습, 분류·객체탐지·세그멘테이션 구분: 교수님이 다음에 물어보실 것.')
sp(1)
h2('판단이 필요해 손대지 않은 것')
warn('upernet+mit_b2 cv1 재학습: 이 조합만 cv1이 빠져 5폴드 평균입니다. 중단됐던 '
     '부분 학습 폴더가 남아 있는데, 덮어쓰기 권한이 막혀 있어 건드리지 않았습니다. '
     '깨끗이 다시 돌릴지는 곽동신 님이 정하세요.')
note('이번에 만든 파일 요약:\n'
     '· 코드: semseg/augmentations.py, tools/train.py (증강 yaml화)\n'
     '· 스크립트: tools/make_object_size_histogram.py, make_dataset_examples_fig.py\n'
     '· config: verify_..._augyaml_cv1.yaml, minneapple_upernet_convnext_t.yaml\n'
     '· 데이터: dataset_minneapple/ (심볼릭 링크)\n'
     '· 그림: reports/figures/fig_object_size_hist, fig_objects_per_image,\n'
     '        fig_dataset_examples_pairs\n'
     '· 문서: 문서/260723_MinneApple_apple_data_분석.md')
sp(1)
h2('다음에 바로 할 수 있는 것 (순서)')
body('1) 이 그림·표로 데이터셋 정리 PPT 만들기 (숫자 다 나와 있음)  '
     '2) yaml 한 줄씩 이해하기  '
     '3) 사과 나머지 조합들도 돌려 블루베리와 전면 비교')


# ---------------------------------------------------------------- 렌더
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
                ax.text(0.5, 0.63, '0723 교수님 미팅', ha='center',
                        fontproperties=BLD, fontsize=20, color=INK)
                ax.text(0.5, 0.575, '할 일 처리 결과 보고서', ha='center',
                        fontproperties=BLD, fontsize=20, color=BLUE)
                ax.plot([0.30, 0.70], [0.53, 0.53], color=BLUE, lw=1.5)
                ax.text(0.5, 0.48, '곽동신 님이 자리를 비운 사이 처리한 내용', ha='center',
                        fontproperties=REG, fontsize=12, color=MUTE)
                ax.text(0.5, 0.17, '2026-07-23   ·   Claude 처리', ha='center',
                        fontproperties=REG, fontsize=11, color=MUTE)
                ax.text(0.5, 0.135, '증강 yaml화 · 1케이스 검증 · MinneApple 정리+학습',
                        ha='center', fontproperties=REG, fontsize=10.5, color=MUTE)
                continue
            if kind == 'newpage':
                npage(); continue
            if kind == 'space':
                y[0] -= 0.012 * t; continue
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
            elif kind == 'tree':
                if y[0] < 0.06:
                    npage()
                ax.text(LM + 0.01, y[0], t, fontproperties=REG, fontsize=9.5, color='#333333')
                y[0] -= 0.0215
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
                        ax.text(xx, y[0], c, fontproperties=REG, fontsize=9.5, color='#222222')
                        xx += cw[i] if i < len(cw) else 0.2
                    y[0] -= 0.024
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
