# -*- coding: utf-8 -*-
"""진행 상황 보고서 PDF (교수님·팀 공유용). 결과 그림 포함."""
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
OUT = Path('reports/진행상황_보고서.pdf')
FIG = Path('reports/figures')
INK, MUTE, BLUE, GOOD, WARN, BAD = '#111111', '#555555', '#1c5cab', '#0a7d33', '#b8860b', '#b23b3b'

B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def tree(t): B.append(('tree', t))
def note(t): B.append(('note', t))
def sp(n=1): B.append(('space', n))
def newpage(): B.append(('newpage', None))
def image(path, cap): B.append(('image', (path, cap)))
def table(headers, rows, cw): B.append(('table', (headers, rows, cw)))
def status(rows): B.append(('status', rows))  # rows: (mark, text)

# ===== COVER =====
B.append(('cover', None))
newpage()

# ===== 요약 =====
h1('한 장 요약')
body('공개 블루베리 데이터(AgriVision DB-1)에서 백본×헤더 32개 조합을 6-fold 교차검증으로 '
     '공정 비교하는 벤치마크를 수행 중이다. 논문 뼈대는 0720 미팅에서 채택한 위장관 '
     '세그멘테이션 벤치마크 논문 구조를 따른다.')
sp()
h2('지금까지 한 일 (완료)')
tree('· 32조합 × 6-fold = 191런 학습 완료 (실패 0건, 약 157 GPU-시간)')
tree('· 결과 자동 집계 → 성능표(IoU·Dice·Precision·Recall) 작성')
tree('· 통계 검정 (대응표본 t-검정 + Friedman 검정)')
tree('· 결과 그림 5종 제작 (Loss곡선·데이터예시·바차트·히트맵·박스플롯)')
tree('· 재현성 확보 (사전학습 가중치 로컬화, md5 검증)')
sp()
h2('핵심 결과')
tree('· 최고 조합:  UPerNet + ConvNeXt-T  (fg-IoU 0.8900 ± 0.0132)')
tree('· 백본이 헤더보다 성능을 크게 좌우 (ResNet-50이 뚜렷이 최하위)')
tree('· 헤더 차이는 작음 — 통계 방법에 따라 유의성 결론이 갈림 (본문 참고)')
sp()
note('다음 단계: Top5 조합 고도화 실험(초기화·모델크기·옵티마이저)과 GPU 메모리 측정, '
     '정성분석. 상세 계획은 마지막 장 참고.')

newpage()
# ===== 실험 개요 =====
h1('1. 실험 개요')
h2('비교 대상 (32조합)')
body('· 백본 8종: ConvNeXt-T, MiT-B2, PVTv2-B2, UniFormer-S, PoolFormer-S36, Swin-T, '
     'ResNetD-50, ResNet-50')
body('· 헤더 4종: CCASeg, Mask2Former, OneFormer, UPerNet')
sp()
h2('실험 조건')
tree('· 데이터: AgriVision DB-1, 약 1,195장 (train 797 / val 199 / test 199)')
tree('· 검증: 6-fold 교차검증 (cv1~cv6)')
tree('· 손실: BCE-Dice   ·   옵티마이저: AdamW   ·   입력: 512×512')
tree('· 지표: Precision, Recall, Dice, IoU (블루베리 픽셀 기준)')
sp()
h2('학습 규모')
table(['항목','값'],
      [['총 학습 런','191 (실패 0)'],['체크포인트','193개 (.pth)'],
       ['소요','약 157 GPU-시간'],['GPU','Tesla V100 32GB × 8']],
      [0.34,0.34])

newpage()
# ===== 결과 =====
h1('2. 핵심 결과')
h2('지표별 최고 조합 (교수님 지시 순서: Precision → Recall → Dice → IoU)')
table(['지표','최고 조합','값'],
      [['Precision','CCASeg + PVTv2-B2','0.9440'],
       ['Recall','UPerNet + MiT-B2','0.9433'],
       ['Dice','UPerNet + ConvNeXt-T','0.9417'],
       ['IoU','UPerNet + ConvNeXt-T','0.8900']],
      [0.18,0.42,0.16])
sp()
h2('종합 Top 5 조합 (fg-IoU 기준)')
table(['순위','조합','fg-IoU'],
      [['1','UPerNet + ConvNeXt-T','0.8900 ± 0.0132'],
       ['2','UPerNet + MiT-B2','0.8880 ± 0.0172'],
       ['3','CCASeg + ConvNeXt-T','0.8830 ± 0.0137'],
       ['4','CCASeg + MiT-B2','0.8795 ± 0.0186'],
       ['5','Mask2Former + PVTv2-B2','0.8774 ± 0.0174']],
      [0.12,0.44,0.22])
sp()
h2('헤더 순위 — Friedman 검정')
body('IoU·Dice·Precision·Recall 모두 p<0.05 → 헤더 간 차이 통계적으로 유의. '
     'CCASeg가 IoU/Dice/Precision 1위, UPerNet이 Recall 1위.')
note('통계 주의: 헤더 평균끼리의 대응표본 t-검정은 "차이 없음"이나, 교수님이 지시한 Friedman '
     '검정은 "차이 있음". 논문에는 참조논문이 쓴 방법(해바라기=t검정)을 기준으로 삼는다.')

newpage()
# ===== 그림들 =====
h1('3. 결과 그림')
image(FIG/'fig_loss_curves.png', '그림 1. 학습 수렴 곡선 (대표 3조합) — 모든 조합 안정적 수렴')
image(FIG/'fig_dataset_examples.png', '그림 2. 데이터셋 예시 (위 원본 / 아래 정답 마스크)')
newpage()
image(FIG/'fig_backbone_bars.png', '그림 3. 백본별 성능 — ResNet-50이 뚜렷이 최하위')
image(FIG/'fig_head_backbone_heatmap.png', '그림 4. 헤더×백본 IoU 히트맵 (검은 테두리=최고 조합)')
newpage()
image(FIG/'fig_variance_box.png', '그림 5. fold별 분산 — (좌) 헤더는 겹침, (우) fold가 큰 변동 요인')

newpage()
# ===== 진행률 =====
h1('4. 교수님 0720 지시 대비 진행률')
status([
 ('done','데이터셋 예시 그림 [A-2]'),
 ('done','Loss 수렴 그래프 [B-①]'),
 ('done','Precision / Recall 표 [B-②]'),
 ('done','Dice / IoU 표 [B-③]'),
 ('done','Friedman 검정 검토 [G]'),
 ('done','6-fold 교차검증 (실험 절차 [E]의 본실험)'),
 ('part','조합 선정 기준 문서 [D] — 초안 작성, 확정 필요'),
 ('part','학습시간 + GPU 메모리 [B-④] — 시간 O, GPU메모리 미측정'),
 ('todo','전체 파이프라인 그림 [A-1]'),
 ('todo','최고 조합 모델 구조도 [A-3]'),
 ('todo','Top5 고도화: 초기화·모델크기·옵티마이저 [C]'),
 ('todo','정성분석 GT+Top5+최적화 7열, TP/FP/FN 색구분 [B-⑤]'),
 ('todo','FLOPs 대비 Dice 그래프 [H]'),
 ('todo','농업 공개 데이터셋 추가 확보 (목표 3개) [I]'),
])

newpage()
# ===== 다음 계획 =====
h1('5. 다음 계획')
h2('바로 가능 (GPU 불필요)')
tree('· 조합 선정 기준 확정·문서화 [D]  ← 다음 미팅 안건')
tree('· 파이프라인 그림 + 최고조합 구조도 [A-1, A-3]')
tree('· FLOPs 측정 → FLOPs 대비 Dice 그래프 [H]')
sp()
h2('GPU 필요')
tree('· Top5 고도화 실험 [C]')
tree('    - 1 fold 스크리닝: 약 25런 → 반나절~하루')
tree('    - 6 fold 완전판: 약 150런 → 2~3일')
tree('· GPU 메모리 측정 [B-④],  정성분석 7열 [B-⑤]')
sp()
h2('조사')
tree('· 농업·수확량 공개 데이터셋 추가 확보 (목표 3개) [I]')
tree('· 연구 배경(휴머노이드 스마트팜) 서술 [F]')
sp()
note('상세 현황·체크리스트: reports/00_연구현황_종합요약.md   ·   '
     '연구 개요·폴더 안내: reports/연구개요_및_폴더안내.pdf')


# ---------- render ----------
def wrap(t,n):
    out=[]
    for p in t.split('\n'): out += textwrap.wrap(p,n) or ['']
    return out
MARK={'done':('✓',GOOD),'part':('◐',WARN),'todo':('○',BAD)}

def render():
    with PdfPages(OUT) as pdf:
        pw,ph=8.27,11.69; LM=0.10; fig=ax=None; y=[0]
        def npage():
            nonlocal fig,ax
            if fig is not None: pdf.savefig(fig); plt.close(fig)
            fig=plt.figure(figsize=(pw,ph)); ax=fig.add_axes([0,0,1,1]); ax.axis('off')
            ax.set_xlim(0,1); ax.set_ylim(0,1); y[0]=0.94
        npage()
        for kind,t in B:
            if kind=='cover':
                ax.add_patch(plt.Rectangle((0,0.78),1,0.005,color=BLUE))
                ax.text(0.5,0.62,'블루베리 세그멘테이션 벤치마크',ha='center',fontproperties=BLD,fontsize=22,color=INK)
                ax.text(0.5,0.565,'진행 상황 보고서',ha='center',fontproperties=BLD,fontsize=22,color=BLUE)
                ax.plot([0.32,0.68],[0.52,0.52],color=BLUE,lw=1.5)
                ax.text(0.5,0.47,'교수님·팀 공유용',ha='center',fontproperties=REG,fontsize=13,color=MUTE)
                ax.text(0.5,0.17,'2026-07-22   ·   곽동신',ha='center',fontproperties=REG,fontsize=11,color=MUTE)
                ax.text(0.5,0.135,'32조합 × 6-fold · 191런 완료',ha='center',fontproperties=REG,fontsize=11,color=MUTE)
                continue
            if kind=='newpage': npage(); continue
            if kind=='space': y[0]-=0.012*t; continue
            if y[0]<0.09 and kind not in ('image',): npage()
            if kind=='h1':
                y[0]-=0.006
                ax.add_patch(plt.Rectangle((LM-0.015,y[0]-0.004),0.006,0.028,color=BLUE))
                ax.text(LM,y[0],t,fontproperties=BLD,fontsize=16,color=INK); y[0]-=0.044
            elif kind=='h2':
                y[0]-=0.006; ax.text(LM,y[0],t,fontproperties=BLD,fontsize=12,color=BLUE); y[0]-=0.030
            elif kind=='body':
                for ln in wrap(t,48):
                    if y[0]<0.06: npage()
                    ax.text(LM,y[0],ln,fontproperties=REG,fontsize=10.5,color=INK); y[0]-=0.0225
                y[0]-=0.004
            elif kind=='tree':
                if y[0]<0.06: npage()
                ax.text(LM+0.01,y[0],t,fontproperties=REG,fontsize=10,color='#333333'); y[0]-=0.0225
            elif kind=='note':
                ls=wrap(t,54); bh=0.0205*len(ls)+0.016
                if y[0]-bh<0.05: npage()
                ax.add_patch(plt.Rectangle((LM-0.02,y[0]-bh+0.02),0.84,bh,facecolor='#eef4fc',edgecolor='#cfe0f5',lw=0.8))
                yy=y[0]
                for ln in ls: ax.text(LM,yy,ln,fontproperties=REG,fontsize=9.5,color=BLUE); yy-=0.0205
                y[0]-=bh+0.006
            elif kind=='table':
                heads,rows,cw=t
                if y[0]-0.03*(len(rows)+1)<0.06: npage()
                x0=LM
                # header
                xx=x0
                for i,hh in enumerate(heads):
                    ax.text(xx,y[0],hh,fontproperties=BLD,fontsize=10,color=INK); xx+=cw[i] if i<len(cw) else 0.2
                y[0]-=0.006; ax.plot([x0,x0+sum(cw)+0.2],[y[0],y[0]],color='#bbbbbb',lw=0.8); y[0]-=0.022
                for row in rows:
                    xx=x0
                    for i,c in enumerate(row):
                        ax.text(xx,y[0],c,fontproperties=REG,fontsize=9.5,color='#222222'); xx+=cw[i] if i<len(cw) else 0.2
                    y[0]-=0.024
                y[0]-=0.006
            elif kind=='status':
                for mark,txt in t:
                    if y[0]<0.06: npage()
                    sym,col=MARK[mark]
                    ax.text(LM,y[0],sym,fontproperties=BLD,fontsize=11,color=col)
                    ax.text(LM+0.03,y[0],txt,fontproperties=REG,fontsize=10,color=INK); y[0]-=0.028
                y[0]-=0.006
                ax.text(LM,y[0],'✓ 완료    ◐ 부분    ○ 예정',fontproperties=REG,fontsize=9,color=MUTE); y[0]-=0.02
            elif kind=='image':
                path,cap=t
                img=mpimg.imread(str(path)); ih,iw=img.shape[0],img.shape[1]
                disp_w=0.80; disp_h=disp_w*(ih/iw)*(pw/ph)
                if y[0]-disp_h-0.03<0.05: npage()
                iax=fig.add_axes([LM-0.02,y[0]-disp_h,disp_w,disp_h]); iax.imshow(img); iax.axis('off')
                y[0]-=disp_h+0.022
                ax.text(LM-0.02,y[0],cap,fontproperties=BLD,fontsize=9.5,color=INK); y[0]-=0.032
        if fig is not None: pdf.savefig(fig); plt.close(fig)

render()
print('저장:', OUT.resolve())
