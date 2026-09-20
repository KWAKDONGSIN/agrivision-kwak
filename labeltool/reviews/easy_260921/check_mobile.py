# 폰390px 문서의 글자·가로 넘침·인증을 실제 브라우저에서 검증한다.
from pathlib import Path
import sys,json,urllib.request,urllib.error
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
base='http://127.0.0.1:5761';b=L.browser(base=base);out=[]
try:
 for name in ['how_to.html','easy_done.html']:
  path='/static/'+name
  try:urllib.request.build_opener(NoRedirect).open(base+path);code=200
  except urllib.error.HTTPError as e:code=e.code
  L.chk(name+' 비로그인302',code==302)
  L.chk(name+' 로그인200',L.Api(base).get_bytes(path)[0]==200)
  b.go(path);b.js("const f=document.createElement('iframe');f.id='phone';f.style='width:390px;height:780px;border:0';f.src=location.href;document.body.replaceChildren(f)")
  b.wait("const f=document.querySelector('#phone');return f.contentDocument.readyState==='complete' && !!f.contentDocument.querySelector('main')")
  r=b.js("const f=document.querySelector('#phone'),w=f.contentWindow,d=f.contentDocument;return {width:w.innerWidth,scroll:d.documentElement.scrollWidth,font:parseFloat(w.getComputedStyle(d.body).fontSize),images:[...d.images].every(i=>i.complete && i.naturalWidth>0)}")
  L.chk(name+' 폰390·17px·넘침없음·사진정상',r['width']==390 and r['scroll']<=390 and r['font']>=17 and r['images'],r);out.append(dict(page=name,**r));b.shot('/home/kds0206/ff_shots/easy_260921/phone_'+name+'.png')
finally:b.close()
(C/'evidence/mobile.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(bool(L.summary('mobile')))
