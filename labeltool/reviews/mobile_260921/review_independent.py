# 별도 검수는 실제 포인터 클릭과 긴 목록·전문가 화면 경로로 폰 사용성을 점검한다.
from pathlib import Path
import sys,json,time
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
b=L.browser(w=900,h=1000,base='http://127.0.0.1:5812');rows=[]
try:
 b.js("document.body.innerHTML='<iframe id=phone src=/box style=\"width:360px;height:740px;border:0\"></iframe>'")
 fid=b.find('#phone');b._s('POST','/frame',{'id':{'element-6066-11e4-a52e-4f735466cecf':fid}})
 b.wait("return !!document.querySelector('#fruit option')");L.close_tour(b)
 b.wait("return document.querySelectorAll('#grid .card').length>20")
 b.click('#grid .card:nth-child(20)');b.wait("return document.querySelector('#loading').classList.contains('hidden')");time.sleep(2)
 rows.append(b.js("return {at:'목록20번째실제클릭',scrollY,canvas:document.querySelector('#cv').getBoundingClientRect().top,width:innerWidth,scroll:document.documentElement.scrollWidth}"))
 L.chk('목록 아래 사진을 열어도 사진부터 보임',rows[-1]['scrollY']==0,rows[-1])
 b.click('#mobile-next');time.sleep(2);L.chk('고정바 실제 다음 클릭',L.ev(b,'!!S.stem'))
 b.click('#mobile-prev');time.sleep(2)
 b.js("localStorage.setItem('easy','0')")
 # 전문가 전환은 숨겨진 기존 단추의 실제 기존 처리로 켠다.
 b.js("if(document.body.classList.contains('easy'))document.querySelector('#easytgl').click()")
 for tab in ['list','edit','dash','exp']:
  b.click('[data-view='+tab+']');time.sleep(2)
  r=b.js("return {at:arguments[0],width:innerWidth,scroll:document.documentElement.scrollWidth}",tab);rows.append(r);L.chk('전문가360 '+tab+' 가로넘침없음',r['scroll']<=360,r)
 b.click('#btn-tour');time.sleep(.3)
 r=b.js("const c=document.querySelector('.tourcard').getBoundingClientRect();return {left:c.left,right:c.right,top:c.top,bottom:c.bottom}")
 L.chk('폰 첫 안내가 화면 안',r['left']>=0 and r['right']<=360 and r['top']>=0 and r['bottom']<=740,r)
finally:b.close()
(C/'evidence/independent.json').write_text(json.dumps({'passed':L.OK,'failed':L.BAD,'rows':rows},ensure_ascii=False,indent=2));sys.exit(bool(L.summary('independent')))
