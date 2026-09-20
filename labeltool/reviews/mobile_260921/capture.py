# 같은 자료로 PC 열두 화면과 실제 폰 폭 iframe의 원본 화면을 저장한다.
from pathlib import Path
import sys,json,time,base64
C=Path(__file__).resolve().parent
sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
kind=sys.argv[1];out=Path.home()/'ff_shots/mobile_260921';out.mkdir(exist_ok=True)
b=L.browser(base='http://127.0.0.1:'+('5811' if kind=='before' else '5812'))
rows=[]
try:
 for fruit in L.FRUITS:
  b.go('/');L.close_tour(b)
  stem=L.images_of(fruit,root=L.DR_DEFAULT)[0]
  b.open_photo(fruit,stem)
  for mode in ['mask','box','num']:
   b.js("document.querySelector('[data-task='+arguments[0]+']').click()",mode)
   time.sleep(2)
   b.js("document.activeElement.blur()")
   path=out/f'{kind}_pc_{fruit}_{mode}.png';b.shot(str(path))
   rows.append(dict(fruit=fruit,stem=stem,mode=mode,actual=L.ev(b,'UI.curTask()'),path=str(path),viewport=b.js('return [innerWidth,innerHeight]')))
 for width,height in [(390,844),(360,740)]:
  b.go('/');L.close_tour(b)
  rect=b._s('POST','/window/rect',dict(width=width,height=height))
  actual=b.js('return [innerWidth,innerHeight]')
  b._s('POST','/window/rect',dict(width=900,height=1000))
  b.js("document.body.innerHTML='';document.body.style='margin:0;display:block';const f=document.createElement('iframe');f.id='phone';f.style=`width:${arguments[0]}px;height:${arguments[1]}px;border:0`;f.src='/';document.body.append(f)",width,height)
  fid=b.find('#phone');b._s('POST','/frame',{'id':{'element-6066-11e4-a52e-4f735466cecf':fid}})
  b.wait("return !!document.querySelector('#fruit option')");L.close_tour(b)
  b.open_photo('apple',L.images_of('apple',root=L.DR_DEFAULT)[0]);time.sleep(1)
  metric=b.js('return {width:innerWidth,height:innerHeight,scroll:document.documentElement.scrollWidth}')
  b._s('POST','/frame',{'id':None})
  path=out/f'{kind}_phone_{width}.png'
  path.write_bytes(base64.b64decode(b._s('GET',f'/element/{fid}/screenshot')))
  rows.append(dict(phone=width,requested=[width,height],outer_actual=actual,iframe=metric,path=str(path)))
finally:b.close()
(C/f'evidence/{kind}_screens.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print(rows,flush=True)
