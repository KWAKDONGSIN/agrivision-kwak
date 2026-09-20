# 시연 대본의 실제 클릭을 순서대로 실행하고 화면·저장 결과·시간을 기록한다.
from pathlib import Path
import sys,time,json,io
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent;T=R.parents[2];sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
run=sys.argv[1];base=sys.argv[2] if len(sys.argv)>2 else 'http://127.0.0.1:5791'
out=Path.home()/'ff_shots/demo_260921'/run;out.mkdir(exist_ok=True)
b=L.browser(base=base,login=False);a=L.Api(base);rows=[];start=time.monotonic()
def step(at,say,action,expect,fn):
 if run=='rehearsal2':
  minute,second=map(int,at.split(':'));time.sleep(max(0,minute*60+second-(time.monotonic()-start)))
 fn();time.sleep(.2);n=len(rows)+1;shot=f'{n:02d}.png';b.shot(str(out/shot));rows.append(dict(at=at,say=say,action=action,expect=expect,shot=shot,elapsed=round(time.monotonic()-start,2)));print(n,action,rows[-1]['elapsed'],flush=True)
def sel(f):b.js("const e=document.querySelector('#fruit');e.value=arguments[0];e.dispatchEvent(new Event('change'))",f)
def search(stem):
 b.js("const q=document.querySelector('#f-q');q.value=arguments[0];q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))",stem)
 b.wait_js("return [...document.querySelectorAll('#grid .card')].some(c=>c.querySelector('.cap').firstChild.textContent.trim()===arguments[0])",stem)
def card(stem):
 b.js("[...document.querySelectorAll('#grid .card')].find(c=>c.querySelector('.cap').firstChild.textContent.trim()===arguments[0]).click()",stem)
 b.wait("return document.querySelector('#loading').classList.contains('hidden') && window.eval('S.stem')===arguments[0]".replace('arguments[0]',json.dumps(stem)),60)
def pt(x,y):return L.ev(b,f'[{x}*S.view.s+S.view.tx,{y}*S.view.s+S.view.ty]')
def center(x,y):
 p=pt(x,y);wh=b.js("const r=document.querySelector('#cv').getBoundingClientRect();return [r.width/2,r.height/2]");b.drag('#cv',*p,*wh)
def zoom(n):
 for _ in range(n):b.click('#zoomin')
def draw():b.drag('#cv',*pt(364,470),*pt(357,515))
def q():
 b.js('document.activeElement.blur()');b.key('q')
try:
 # 준비도 실제 로그인 화면으로 검증하고 같은 폴더에 남긴다. 비밀번호는 시험용이며 화면에 노출하지 않는다.
 b.go('/login');b.shot(str(out/'00_login.png'));b.type('input[name=password]',L.PW);b.click('button');b.wait("return !!document.querySelector('#fruit option')");L.close_tour(b)
 start=time.monotonic()
 step('0:00','데이터의 잘못된 표시를 찾아 고치고 확인하는 순서를 보여드리겠습니다. 지금은 원본을 바꾸지 않는 시연 사본입니다.','첫 화면 보기','사진 목록',lambda:None)
 step('0:20','누가 확인했는지 남도록 이름을 적습니다.','내 이름에 곽동신 시연 입력','이름 표시',lambda:b.type('#who','곽동신 시연'))
 step('0:30','포도500번을 열겠습니다.','과일에서 포도 선택','포도 목록',lambda:sel('grape'))
 step('0:40','사진 번호로 바로 찾습니다.','검색에500 입력 후 Enter','500 카드',lambda:search('500'))
 step('0:50','큰 송이 위에 굽은 초록 줄기가 보입니다.','500 카드 클릭','포도500 사진',lambda:card('500'))
 step('1:00','그 줄기를 화면 가운데로 옮기겠습니다.','이동 클릭','손 모양 커서',lambda:b.click('[data-tool=pan]'))
 step('1:05','큰 송이 꼭대기의 굽은 줄기를 가운데로 끕니다.','굽은 줄기에서 화면 중앙까지 드래그','줄기가 화면 중앙',lambda:center(365,490))
 step('1:15','확대해서 열매와 줄기를 구분합니다.','＋확대8번 클릭','굽은 줄기 확대',lambda:zoom(8))
 step('1:30','사진만 보면 이 부분은 초록 줄기입니다.','Q 한 번','원본 사진만',q)
 step('1:40','칠한 영역에는 줄기까지 들어 있습니다.','Q 한 번','칠한 영역만',q)
 step('1:50','겹쳐 놓고 줄기 한 부분을 지워 보겠습니다.','Q 한 번','겹쳐 보기',q)
 step('2:00','지우개를 고릅니다.','지우개 클릭','지우개 선택',lambda:b.click('[data-tool=erase]'))
 step('2:05','열매를 건드리지 않도록 가늘게 맞춥니다.','굵기 슬라이더12로 조절','굵기12',lambda:b.js("const e=document.querySelector('#brush');e.value=12;e.dispatchEvent(new Event('input',{bubbles:true}))"))
 before=L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')
 step('2:10','초록 줄기의 안쪽만 짧게 지웁니다.','줄기 안쪽을 위에서 아래로 짧게 드래그','수정 흔적',draw)
 assert L.ev(b,'S.edDirty') and L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')<before
 step('2:20','실수해도 큰 버튼 하나로 돌아갑니다.','되돌리기 클릭','지우기 취소',lambda:b.click('#undo'));assert L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')==before
 step('2:30','방금 한 수정을 다시 적용합니다.','다시하기 클릭','지우기 다시 적용',lambda:b.click('#redo'))
 expected=L.ev(b,'Array.from(S.ed)');assert sum(expected)<before
 step('2:40','먼저 수정본을 저장합니다. 저장과 확인은 별개입니다.','저장 클릭','저장됨 표시',lambda:b.click('#btn-save'));b.wait("return !window.eval('S.edDirty')")
 w,h=L.ev(b,'[S.W,S.H]');code,png=a.get_bytes('/mask?fruit=grape&stem=500&layer=fixed');saved=np.asarray(Image.open(io.BytesIO(png)))>0
 assert code==200 and np.array_equal(saved,np.array(expected,dtype=bool).reshape(h,w))
 step('2:45','기존 빨간 라벨을 끄면 수정한 모양을 볼 수 있습니다.','사진 위 원본 클릭','원본 표시 꺼짐',lambda:b.click('[data-tgl="l-gt"]'))
 step('2:48','AI 표시도 끄고 내가 고친 그림만 확인합니다.','사진 위 AI 클릭','지운 줄기와 수정본만 표시',lambda:b.click('[data-tgl="l-ai"]'))
 step('2:55','확인 기록이 남는 동작까지 시연합니다. 이것은 사진 전체 검수를 마쳤다는 실적이 아니라 사본 연습입니다.','다 했어요 클릭','확인 기록 후 다음 사진 또는 목록 끝',lambda:b.click('#btn-confirm'));time.sleep(.5)
 assert a.get('/api/item?fruit=grape&stem=500')['confirmed']['status']=='fixed'
 step('3:00','사과에도 확인할 후보가 있습니다.','사진 목록 클릭','사진 목록',lambda:b.click('[data-view=list]'))
 step('3:10','사과를 고릅니다.','과일에서 사과 선택','사과 목록',lambda:sel('apple'))
 stem='20150921_131453_image1161'
 step('3:20','사진 번호는 이 긴 이름 그대로 검색합니다.','검색에 '+stem+' 입력 후 Enter','해당 카드',lambda:search(stem))
 step('3:30','사진 아래쪽의 작은 붉은 사과를 보겠습니다.','해당 카드 클릭','사과 사진',lambda:card(stem))
 step('3:40','위에 잎이 걸친 사과를 가운데로 옮깁니다.','이동 클릭','손 모양 커서',lambda:b.click('[data-tool=pan]'))
 step('3:45','왼쪽에서4분의1, 위에서5분의3 지점입니다.','그 사과를 화면 중앙으로 드래그','사과 중앙',lambda:center(280,1140))
 step('3:50','잎과 칠한 모양이 보이도록 확대합니다.','＋확대10번 클릭','사과와 잎 확대',lambda:zoom(10))
 step('4:05','사진에는 잎이 사과를 가리고 있습니다.','Q 한 번','원본 사진만',q)
 step('4:12','라벨은 잎 자리까지 둥글게 채워져 있습니다.','Q 한 번','둥근 칠한 영역',q)
 step('4:20','가려진 부분을 포함할지는 교수님께 기준을 확인할 항목입니다. 임의로 전체 데이터를 바꾸지 않겠습니다.','Q 한 번','사과 겹쳐 보기',q)
 step('4:30','팀원들은 과일과 사진을 고르고, 확실히 잘못된 곳을 고친 뒤 저장하고 다 했어요를 누르시면 됩니다. 애매한 곳은 문제로 남겨 주세요. 그림 사용법을 보면서 따라 하실 수 있습니다.','사용법 열기','그림 중심 사용법',lambda:b.go('/static/how_to.html'))
 if run=='rehearsal2':time.sleep(max(0,298-(time.monotonic()-start)))
 elapsed=round(time.monotonic()-start,2);assert elapsed<300,elapsed
 result={'run':run,'elapsed_seconds':elapsed,'timing':'실제 클릭·촬영 포함. 2차는 대본 시각 대기와 끝30초 포함. 발화 실측은 아님','rows':rows,'saved_pixels_removed':before-sum(expected),'fixed_png_exact':True,'confirmed':'fixed','sandbox':True,'screenshots':str(out)}
 (R/(run+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print('PASS',elapsed,flush=True)
finally:b.close()
