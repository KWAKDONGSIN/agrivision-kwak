# -*- coding: utf-8 -*-
"""연구 개요 + 폴더 역할 안내 PDF 생성 (한글, matplotlib PdfPages)."""
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
MONO = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')

OUT = Path('reports/연구개요_및_폴더안내.pdf')
INK, MUTE, BLUE, LINE = '#111111', '#555555', '#1c5cab', '#d8d8d4'

# ---- document content as blocks ----
# ('h1'|'h2'|'body'|'tree'|'note'|'space', text)
B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def tree(t): B.append(('tree', t))
def note(t): B.append(('note', t))
def sp(n=1): B.append(('space', n))

# ===== COVER =====
B.append(('cover', None))
B.append(('newpage', None))

# ===== 1. 연구 목표 =====
h1('1. 이 연구가 원하는 것 (연구 목표)')
body('한 줄 요약: 공개 블루베리 사진에서 "블루베리 열매만 정확히 오려내는(분할) 인공지능"을 만들되, '
     '새 모델을 발명하는 것이 아니라 이미 있는 여러 모델 조합 중 무엇이 가장 좋은지를 공정하게 '
     '비교(벤치마크)하는 것이 목표다.')
sp()
h2('왜 이 연구가 중요한가')
body('· 스마트팜을 휴머노이드 로봇이 관리하는 시대를 대비 — 사람 눈높이 카메라로 열매를 인식.')
body('· 블루베리는 서로 겹치고 가려지고 크기가 제각각이라, 일반 사진에서 잘 되는 모델이 '
     '농업 사진에서도 잘 된다고 보장할 수 없다. 그래서 직접 비교가 필요하다.')
sp()
h2('무엇을 비교하는가 (32개 조합)')
body('세그멘테이션 모델은 [백본] + [헤더] 두 부품의 조합으로 만든다.')
body('· 백본(특징 추출) 8종: ConvNeXt-T, MiT-B2, PVTv2-B2, UniFormer-S, PoolFormer-S36, '
     'Swin-T, ResNetD-50, ResNet-50')
body('· 헤더(픽셀 예측) 4종: CCASeg, Mask2Former, OneFormer, UPerNet')
body('· 4 x 8 = 32개 조합을, 6-fold 교차검증(데이터를 6번 다르게 나눠 반복)으로 공정 비교.')
sp()
h2('어떻게 평가하는가')
body('· 성능 지표: Precision, Recall, Dice, IoU (블루베리 픽셀 기준)')
body('· 통계 검정으로 "이 조합이 정말 더 낫다"를 검증 (대응표본 t-검정 / Friedman 검정)')
body('· 효율: 학습시간, GPU 메모리, 연산량(FLOPs) 대비 성능')
sp()
h2('최종 산출물')
body('블루베리 영상에 가장 적합한 모델 조합을 근거와 함께 제시하는 논문. '
     '논문 뼈대는 0720 미팅에서 채택한 "위장관 세그멘테이션 벤치마크 논문" 구조를 따른다.')
sp()
note('현재 상태(2026-07-22): 32조합 6-fold 학습 191런 완료(실패 0). 최고 조합은 '
     'UPerNet + ConvNeXt-T (IoU 0.8900). 결과표·그림·통계 정리 완료.')

B.append(('newpage', None))

# ===== 2. 폴더 역할 =====
h1('2. 각 폴더가 하는 역할')
body('자료는 크게 세 곳에 나뉜다: (A) 연구 자료·회의록 폴더, (B) 서버 실험 코드/결과 폴더, '
     '(C) 원본 데이터 폴더.')
sp()

h2('(A) 연구 자료 폴더  —  "연구실 블루베리"')
body('논문 조사, 회의록, 발표자료 등 사람이 읽는 문서 모음 (455개 파일).')
tree('01_선행연구_벤치마크조사   백본-헤더 벤치마크 선행논문 조사')
tree('02_데이터셋_조사          공개 데이터셋(MinneApple, PhenoBench 등) 비교')
tree('03_참고논문_리뷰          해바라기·손실함수 등 참고논문 해설')
tree('04_코드_저장소_검토       실험 코드 진단·개선 제안서')
tree('05_우리논문_작성          우리 논문 초안(docx)·그림표 계획')
tree('06_교수님미팅_기록        ★ 교수님 지시 원본·요약 (가장 중요)')
tree('07_초보자_학습자료        쉬운 설명 자료')
tree('08_종합정리_인덱스        전체 자료 통합 인덱스')
tree('99_기타                  프롬프트·미리보기 등')
tree('semantic-segmentation    (참고용 코드 사본 — 실제 실험은 서버 B에서)')
tree('빅데이터분석             교차검증·통계검정 등 수업 자료')
note('가장 먼저 볼 파일: 06_교수님미팅_기록 / 260720_0720교수님미팅_요약및지시사항.txt')
sp()

h2('(B) 서버 실험 폴더  —  semantic-segmentation')
body('실제 학습·평가가 돌아가는 코드와 결과. 경로: /data/project/2026summer/kds0206/semantic-segmentation')
tree('configs/     조합별 설정 파일(yaml) — 어떤 백본·헤더·데이터로 학습할지')
tree('semseg/      모델 코드 (models/backbones, models/heads, datasets 등)')
tree('tools/       실행 스크립트 (train.py 학습, val.py 평가,')
tree('             aggregate_results.py 집계, plot_benchmark_figures.py 그림)')
tree('scripts/     여러 조합을 한 번에 돌리는 실행 스크립트(.sh)')
tree('output/      ★ 학습 결과 — 조합별 체크포인트(.pth)·학습로그(TensorBoard)')
tree('reports/     ★ 정리된 결과물 — 표(md/tex)·그림(pdf/png)·요약(이 문서 포함)')
tree('logs/        스윕 실행 로그')
note('결과 요약은 reports/00_연구현황_종합요약.md 에 정리되어 있음.')
sp()

h2('(C) 원본 데이터 폴더  —  dataset_6fold')
body('학습에 쓰는 블루베리 이미지와 정답 마스크. 경로: /data/project/2026summer/kds0206/dataset_6fold')
tree('cv1 ~ cv6    6가지로 나눈 교차검증 세트')
tree('  각 cv/ 안에 train / val / test')
tree('    images/  원본 사진(.bmp)     masks/  정답 마스크(.png, 흰색=블루베리)')
note('fold당 train 약 797장 / val 199장 / test 199장 (총 약 1,195장).')

B.append(('newpage', None))

# ===== 3. 한 장 흐름 =====
h1('3. 연구 전체 흐름 (교수님 지시 순서)')
body('교수님 0720 지시에 따른 논문 전개 순서:')
sp()
tree('1) 조합 선정 기준 문서화        어떤 32조합을 왜 골랐는지 (실험 전 선행)')
tree('2) 1-fold 전량 학습 → 수렴 확인   미수렴 조합은 튜닝')
tree('3) Early stopping 유무 통계 비교   차이 없음을 보이고 → 전체 교차검증 근거')
tree('4) 전체 6-fold 교차검증          [현재 완료된 부분]')
tree('5) 결과 제시                     Loss → Precision/Recall → Dice/IoU')
tree('                                → 학습시간+GPU메모리 → 정성분석 → 고도화')
tree('6) Top5 고도화                   초기화·모델크기·옵티마이저 비교 → 최종 Best')
tree('7) 정성분석                      GT+Top5+최적화 7열, TP/FP/FN 색 구분')
sp()
note('현재 4번(6-fold 교차검증)까지 완료. 나머지(1,2,3,5,6,7)는 진행 예정 — '
     '상세 체크리스트는 reports/00_연구현황_종합요약.md 참고.')


# ---------- render ----------
def wrap(t, n):
    out = []
    for para in t.split('\n'):
        out += textwrap.wrap(para, n) or ['']
    return out

def render():
    with PdfPages(OUT) as pdf:
        page_w, page_h = 8.27, 11.69  # A4
        y = None; fig = ax = None
        def newpage():
            nonlocal fig, ax, y
            if fig is not None:
                pdf.savefig(fig); plt.close(fig)
            fig = plt.figure(figsize=(page_w, page_h)); ax = fig.add_axes([0,0,1,1]); ax.axis('off')
            ax.set_xlim(0,1); ax.set_ylim(0,1)
            y = 0.94
            return fig, ax
        fig, ax = newpage()
        LM = 0.10
        for kind, t in B:
            if kind == 'cover':
                ax.text(0.5, 0.70, '블루베리 세그멘테이션', ha='center', fontproperties=BLD, fontsize=26, color=INK)
                ax.text(0.5, 0.645, '백본 × 헤더 조합 벤치마크', ha='center', fontproperties=BLD, fontsize=26, color=INK)
                ax.plot([0.30,0.70],[0.60,0.60], color=BLUE, lw=2)
                ax.text(0.5, 0.55, '연구 개요와 폴더 안내', ha='center', fontproperties=REG, fontsize=15, color=MUTE)
                ax.text(0.5, 0.20, '작성일 2026-07-22    ·    대상: 곽동신', ha='center', fontproperties=REG, fontsize=11, color=MUTE)
                ax.text(0.5, 0.165, '근거: 교수님 0720 미팅 지시 + 서버 실험 결과', ha='center', fontproperties=REG, fontsize=11, color=MUTE)
                continue
            if kind == 'newpage':
                fig, ax = newpage(); continue
            if kind == 'space':
                y -= 0.012 * t; continue
            if y < 0.08:
                fig, ax = newpage()
            if kind == 'h1':
                y -= 0.010
                ax.add_patch(plt.Rectangle((LM-0.015, y-0.004), 0.006, 0.026, color=BLUE, transform=ax.transAxes))
                ax.text(LM, y, t, fontproperties=BLD, fontsize=16, color=INK); y -= 0.040
            elif kind == 'h2':
                y -= 0.006
                ax.text(LM, y, t, fontproperties=BLD, fontsize=12.5, color=BLUE); y -= 0.030
            elif kind == 'body':
                for ln in wrap(t, 46):
                    if y < 0.06: fig, ax = newpage()
                    ax.text(LM, y, ln, fontproperties=REG, fontsize=10.5, color=INK); y -= 0.0225
                y -= 0.004
            elif kind == 'tree':
                if y < 0.06: fig, ax = newpage()
                ax.text(LM+0.02, y, t, fontproperties=MONO, fontsize=9.5, color='#333333'); y -= 0.0215
            elif kind == 'note':
                lines = wrap(t, 50)
                bh = 0.0205*len(lines) + 0.016
                if y-bh < 0.05: fig, ax = newpage()
                ax.add_patch(plt.Rectangle((LM-0.02, y-bh+0.02), 0.84, bh, facecolor='#eef4fc', edgecolor='#cfe0f5', lw=0.8))
                yy = y
                for ln in lines:
                    ax.text(LM, yy, ln, fontproperties=REG, fontsize=9.5, color='#1c5cab'); yy -= 0.0205
                y -= bh + 0.006
        if fig is not None:
            pdf.savefig(fig); plt.close(fig)

render()
print('저장:', OUT.resolve())
print('페이지 크기 A4, 한글 폰트 Noto Sans CJK KR')
