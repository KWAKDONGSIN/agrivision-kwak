# 실제 Firefox의 폰 폭·버튼·터치 입력과 저장 보호를 검증한다.
from pathlib import Path
import sys,json,time,base64
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
OUT=Path.home()/'ff_shots/mobile_260921';OUT.mkdir(exist_ok=True)
base='http://127.0.0.1:5812';b=L.browser(w=900,h=1000,base=base);rows=[]
def frame(width,height,path='/'):
 b._s('POST','/frame',{'id':None});b.go('/')
 b.js("document.body.innerHTML='';document.body.style='margin:0;display:block';let f=document.createElement('iframe');f.id='phone';f.style=`width:${arguments[0]}px;height:${arguments[1]}px;border:0`;f.src=arguments[2];document.body.append(f)",width,height,path)
 fid=b.find('#phone');b._s('POST','/frame',{'id':{'element-6066-11e4-a52e-4f735466cecf':fid}})
 if path=='/':b.wait("return !!document.querySelector('#fruit option')");L.close_tour(b)
 else:b.wait("return !!document.querySelector('input[name=password]')")
 return fid
def shot(name,fid):
 b._s('POST','/frame',{'id':None});(OUT/(name+'.png')).write_bytes(base64.b64decode(b._s('GET',f'/element/{fid}/screenshot')));b._s('POST','/frame',{'id':{'element-6066-11e4-a52e-4f735466cecf':fid}})
def metric(name):
 r=b.js("""const visible=e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
 const controls=[...document.querySelectorAll('button,input:not([type=hidden]),select,a,summary,#legend .i')].filter(visible);
 return {name:arguments[0],width:innerWidth,height:innerHeight,scroll:document.documentElement.scrollWidth,
 small:controls.filter(e=>e.getBoundingClientRect().width<43.9||e.getBoundingClientRect().height<43.9).map(e=>({id:e.id,text:e.textContent.slice(0,30),w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height})),
 overflow:controls.filter(e=>e.getBoundingClientRect().left<0||e.getBoundingClientRect().right>innerWidth+.1).map(e=>e.id||e.textContent.slice(0,25)),
 fonts:[...document.querySelectorAll('body *')].filter(visible).filter(e=>parseFloat(getComputedStyle(e).fontSize)<16).map(e=>e.id||e.tagName)}""",name)
 rows.append(r);L.chk(name+' 가로넘침 0',r['scroll']<=r['width'] and not r['overflow'],r);L.chk(name+' 터치44·글자16',not r['small'] and not r['fonts']);return r
try:
 for width,height in [(390,844),(360,740)]:
  fid=frame(width,height,'/login');metric(f'login{width}');shot(f'after_login_{width}',fid)
  fid=frame(width,height)
  b.wait("return document.querySelectorAll('#grid .card').length>0");metric(f'list{width}')
  b.open_photo('apple','20150919_174151_image1')
  metric(f'mask{width}');shot(f'check_mask_{width}',fid)
  r=L.ev(b,"(()=>{const r=UI.cv.getBoundingClientRect();return {left:r.left,right:r.right,fit:S.W*S.view.s<=r.width&&S.H*S.view.s<=r.height,bar:document.querySelector('#mobile-bar').getBoundingClientRect().bottom,canvas:r.bottom,tools:document.querySelector('#toolrail').getBoundingClientRect().top,verdict:document.querySelector('#verdictbar').getBoundingClientRect().top}})()")
  L.chk(f'{width} 여백16·사진맞춤·고정바·순서',abs(r['left']-16)<.1 and r['right']<=width-16 and r['fit'] and r['bar']==height and r['canvas']<=r['tools']<r['verdict'],r)
  for mode in ['box','num']:
   b.js("document.querySelector('[data-task='+arguments[0]+']').click()",mode);time.sleep(1);metric(f'{mode}{width}')
  for tab in ['dash','exp']:
   b.js("document.querySelector('[data-view='+arguments[0]+']').click()",tab);time.sleep(2);metric(f'{tab}{width}');shot(f'check_{tab}_{width}',fid)
finally:b.close()
(C/'evidence/mobile_layout.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));sys.exit(bool(L.summary('mobile-layout')))
