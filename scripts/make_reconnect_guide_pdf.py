# -*- coding: utf-8 -*-
"""서버 재접속 안내서 PDF (초보자용, 컴퓨터를 껐다 켰을 때)."""
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties

REG = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BLD = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
OUT = Path('reports/서버_재접속_안내서.pdf')
INK, MUTE, BLUE, GOOD = '#111111', '#555555', '#1c5cab', '#0a7d33'

B = []
def h1(t): B.append(('h1', t))
def h2(t): B.append(('h2', t))
def body(t): B.append(('body', t))
def step(n, t): B.append(('step', (n, t)))
def cmd(t): B.append(('cmd', t))
def note(t): B.append(('note', t))
def sp(n=1): B.append(('space', n))
def newpage(): B.append(('newpage', None))

B.append(('cover', None)); newpage()

# ===== 안심 =====
h1('먼저 — 걱정하지 마세요')
body('컴퓨터를 꺼도 연구 파일·학습 결과·PDF·표는 하나도 사라지지 않습니다.')
body('모든 자료는 내 컴퓨터가 아니라 "연구실 서버"라는 다른 컴퓨터에 저장돼 있고, '
     '그 서버는 항상 켜져 있습니다.')
body('그래서 할 일은 딱 하나 — "다시 접속"하는 것뿐입니다. 평소 쓰던 VS Code로 하면 됩니다.')
sp()
note('핵심 3가지만 기억: (1) VS Code 켜기  (2) 서버 연결  (3) 터미널에 claude 입력')

newpage()
# ===== Part A =====
h1('1. VS Code로 서버에 다시 연결하기')
step('1', '컴퓨터를 켜고 VS Code를 실행한다.')
step('2', 'VS Code 창의 왼쪽 맨 아래 구석을 본다. 파란색 또는 초록색으로')
body('     된 " >< " 모양(꺾쇠 두 개) 버튼이 있다. 그것을 클릭한다.')
step('3', '화면 위쪽 가운데에 메뉴가 뜬다. 그중에서')
body('     "Connect to Host..." (호스트에 연결) 를 고른다.')
step('4', '전에 접속했던 서버 주소가 목록에 보인다.')
body('     <서버주소>  또는  ahnbi3  또는  ahnbi3.suwon.ac.kr')
body('     그것을 클릭한다. (목록에 없으면 "Add New SSH Host"로 추가)')
step('5', '비밀번호를 물어보면 서버 비밀번호를 입력하고 Enter.')
body('     (비밀번호는 화면에 안 보인다. 정상이다.)')
sp()
note('연결이 성공하면 왼쪽 아래 " >< " 옆에 서버 이름(SSH: ...)이 표시된다.')

newpage()
# ===== Part B =====
h1('2. 작업 폴더 열기')
step('1', '위쪽 메뉴에서  File(파일) -> Open Folder(폴더 열기)  를 누른다.')
step('2', '주소 입력칸에 아래 경로를 붙여넣고 OK/확인.')
cmd('/data/project/2026summer/kds0206/semantic-segmentation')
step('3', '왼쪽에 폴더와 파일들이 나타난다.')
body('     reports 폴더를 열면 지금까지 만든 PDF·표가 다 있다.')
sp()
h2('결과물이 있는 곳 (reports 폴더)')
body('· 진행상황_보고서.pdf        (교수님·팀 발표용)')
body('· 연구개요_및_폴더안내.pdf   (연구 개요)')
body('· 00_연구현황_종합요약.md    (상세 현황·할 일)')
body('· 깃허브_서버_비교.md        (저장소 비교)')
body('· 서버_재접속_안내서.pdf     (이 문서)')

newpage()
# ===== Part C =====
h1('3. Claude(클로드)와 다시 대화하기')
step('1', '위쪽 메뉴에서  Terminal(터미널) -> New Terminal(새 터미널)  을 누른다.')
body('     화면 아래쪽에 검은 입력창이 생긴다.')
step('2', '아래 명령을 입력하고 Enter.')
sp()
h2('지금까지 하던 이 대화를 이어서:')
cmd('claude --continue')
h2('완전히 새로 시작하려면:')
cmd('claude')
sp()
body('"claude --continue"를 입력하면, 지금까지 나눈 대화(연구 내용·만든 파일)를 '
     '모두 기억한 상태로 이어집니다.')
sp()
note('명령을 입력할 때 앞에 있는 폴더 경로가 semantic-segmentation 인지 확인하세요. '
     '아니면 먼저  cd /data/project/2026summer/kds0206/semantic-segmentation  입력.')

newpage()
# ===== Part D =====
h1('4. 접속이 안 될 때')
h2('증상: 연결이 자꾸 끊기거나 "Connection closed"가 뜬다')
body('이 서버는 수원대 학교 서버라, 집·외부에서는 접속이 막힐 수 있습니다.')
body('해결:')
body('· 학교 VPN을 켜고 다시 시도한다. (수원대 VPN)')
body('· 또는 학교(연구실) 안의 인터넷에서 접속한다.')
body('· 평소 VS Code로 잘 되던 방식이 있으면 그대로 사용한다.')
sp()
h2('그래도 안 되면')
body('· 같은 팀원이나 서버를 세팅해 준 사람에게 접속 방법(주소·포트·VPN)을 물어본다.')
body('· 서버는 계속 켜져 있으니 파일은 안전하다. 접속만 다시 하면 된다.')
sp()
h2('한 장 요약')
body('VS Code 켜기 -> 왼쪽 아래 " >< " -> Connect to Host -> 서버 선택')
body('-> Open Folder로 semantic-segmentation 열기')
body('-> Terminal 열고  claude --continue  입력')


def wrap(t, n):
    out = []
    for p in t.split('\n'):
        out += textwrap.wrap(p, n) or ['']
    return out

def render():
    with PdfPages(OUT) as pdf:
        pw, ph = 8.27, 11.69; LM = 0.10; fig = ax = None; y = [0]
        def npage():
            nonlocal fig, ax
            if fig is not None: pdf.savefig(fig); plt.close(fig)
            fig = plt.figure(figsize=(pw, ph)); ax = fig.add_axes([0,0,1,1]); ax.axis('off')
            ax.set_xlim(0,1); ax.set_ylim(0,1); y[0] = 0.94
        npage()
        for kind, t in B:
            if kind == 'cover':
                ax.add_patch(plt.Rectangle((0,0.78),1,0.005,color=BLUE))
                ax.text(0.5,0.60,'서버 재접속 안내서',ha='center',fontproperties=BLD,fontsize=26,color=INK)
                ax.plot([0.30,0.70],[0.545,0.545],color=BLUE,lw=1.5)
                ax.text(0.5,0.49,'컴퓨터를 껐다 켰을 때 다시 접속하는 법',ha='center',fontproperties=REG,fontsize=13,color=MUTE)
                ax.text(0.5,0.17,'2026-07-22  ·  곽동신',ha='center',fontproperties=REG,fontsize=11,color=MUTE)
                ax.text(0.5,0.135,'※ 이 파일을 내 컴퓨터/휴대폰에도 저장해 두세요',ha='center',fontproperties=REG,fontsize=10,color=BLUE)
                continue
            if kind == 'newpage': npage(); continue
            if kind == 'space': y[0]-=0.012*t; continue
            if y[0]<0.09: npage()
            if kind == 'h1':
                y[0]-=0.006
                ax.add_patch(plt.Rectangle((LM-0.015,y[0]-0.004),0.006,0.028,color=BLUE))
                ax.text(LM,y[0],t,fontproperties=BLD,fontsize=17,color=INK); y[0]-=0.048
            elif kind == 'h2':
                y[0]-=0.006; ax.text(LM,y[0],t,fontproperties=BLD,fontsize=12.5,color=BLUE); y[0]-=0.032
            elif kind == 'body':
                for ln in wrap(t,46):
                    if y[0]<0.06: npage()
                    ax.text(LM,y[0],ln,fontproperties=REG,fontsize=11,color=INK); y[0]-=0.026
                y[0]-=0.004
            elif kind == 'step':
                n,txt = t
                if y[0]<0.06: npage()
                ax.add_patch(plt.Circle((LM+0.005,y[0]+0.006),0.014,color=BLUE))
                ax.text(LM+0.005,y[0]+0.006,n,ha='center',va='center',fontproperties=BLD,fontsize=10,color='white')
                for i,ln in enumerate(wrap(txt,42)):
                    ax.text(LM+0.035,y[0],ln,fontproperties=REG,fontsize=11,color=INK); 
                    if i<len(wrap(txt,42))-1: y[0]-=0.026
                y[0]-=0.032
            elif kind == 'cmd':
                if y[0]<0.07: npage()
                ax.add_patch(plt.Rectangle((LM,y[0]-0.014),0.80,0.032,facecolor='#1a1a1a',edgecolor='none'))
                ax.text(LM+0.015,y[0],t,fontproperties=REG,fontsize=11,color='#7fd88f'); y[0]-=0.040
            elif kind == 'note':
                ls=wrap(t,50); bh=0.026*len(ls)+0.016
                if y[0]-bh<0.05: npage()
                ax.add_patch(plt.Rectangle((LM-0.02,y[0]-bh+0.02),0.84,bh,facecolor='#eef4fc',edgecolor='#cfe0f5',lw=0.8))
                yy=y[0]
                for ln in ls: ax.text(LM,yy,ln,fontproperties=REG,fontsize=10,color=BLUE); yy-=0.026
                y[0]-=bh+0.006
        if fig is not None: pdf.savefig(fig); plt.close(fig)

render()
print('저장:', OUT.resolve())
