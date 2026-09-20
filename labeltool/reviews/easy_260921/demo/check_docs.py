# 폰 문서의 실제 렌더링·체크 저장·인증과96×172mm PDF 인쇄를 검증한다.
from pathlib import Path
import sys,json,base64,urllib.request,urllib.error
R=Path(__file__).resolve().parent;T=R.parents[2];W=Path('/data/project/2026summer/kds0206');sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
base='http://127.0.0.1:5792';b=L.browser(base=base);out=[]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
try:
 for name in ['how_to.html','시연.html']:
  from urllib.parse import quote
  path='/static/'+quote(name)
  try:urllib.request.build_opener(NoRedirect).open(base+path);code=200
  except urllib.error.HTTPError as e:code=e.code
  assert code==302
  b.go(path);b.js("const f=document.createElement('iframe');f.id='phone';f.style='width:390px;height:780px;border:0';f.src=location.href;document.body.replaceChildren(f)")
  b.wait("const f=document.querySelector('#phone');return f.contentDocument.readyState==='complete' && !!f.contentDocument.querySelector('main')")
  r=b.js("const f=document.querySelector('#phone'),w=f.contentWindow,d=f.contentDocument;return {width:w.innerWidth,scroll:d.documentElement.scrollWidth,font:parseFloat(w.getComputedStyle(d.body).fontSize),action:d.querySelector('article label')?parseFloat(w.getComputedStyle(d.querySelector('article label')).fontSize):null,images:[...d.images].every(i=>i.complete && i.naturalWidth>0)}")
  assert r['width']==390 and r['scroll']<=390 and r['font']>=17 and r['images'],r
  if name=='시연.html':assert r['action']>=20
  b.shot(str(Path.home()/'ff_shots/demo_260921'/('phone_'+name+'.png')));out.append(dict(page=name,anonymous=code,**r))
 b.go('/static/'+quote('시연.html'));b.click('[data-step="0"]');b.go('/static/'+quote('시연.html'));assert b.js('return document.querySelector("[data-step=\\"0\\"]").checked');b.click('[data-step="0"]')
 b.go('/static/'+quote('시연_PDF원문.html'))
 pdf=b._s('POST','/print',{'background':True,'orientation':'portrait','page':{'width':9.6,'height':17.2},'margin':{'top':.7,'bottom':.8,'left':.6,'right':.6},'shrinkToFit':False})
 target=W/'문서/260921_랩미팅_시연대본.pdf';target.write_bytes(base64.b64decode(pdf));assert target.read_bytes().startswith(b'%PDF-')
 (R/'document_checks.json').write_text(json.dumps({'mobile':out,'checkbox_persisted':True,'pdf':str(target)},ensure_ascii=False,indent=2));print('폰390·17/23px·가로넘침0·인증·체크저장·PDF 인쇄 통과')
finally:b.close()
