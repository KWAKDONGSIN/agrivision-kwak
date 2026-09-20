# 게시된 문서와 수정 전 발표용 사본을 인증 후 읽기만으로 검증한다.
from pathlib import Path
import sys,json,urllib.request,urllib.error,hashlib,datetime
from urllib.parse import quote
R=Path(__file__).resolve().parent;T=R.parents[2];sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
pw=next(l.split('=',1)[1].strip().strip('\"\'') for l in (Path.home()/'.council/labeltool.env').read_text().splitlines() if l.startswith('LABELTOOL_PASSWORD='))
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
out={'at':datetime.datetime.now().isoformat(),'documents':{}}
a=L.Api('http://127.0.0.1:5111',pw)
for name in ['how_to.html','시연.html','시연대본.pdf','help/demo_260921/index.html']:
 path='/static/'+quote(name)
 try:urllib.request.build_opener(NoRedirect).open('http://127.0.0.1:5111'+path);code=200
 except urllib.error.HTTPError as e:code=e.code
 assert code==302
 code,b=a.get_bytes(path);assert code==200 and b==(T/'app/static'/name).read_bytes();out['documents'][name]={'anonymous':302,'login':200,'sha256':hashlib.sha256(b).hexdigest()}
a=L.Api('http://127.0.0.1:5791',pw);j=a.get('/api/item?fruit=grape&stem=500');assert not j.get('confirmed') and not j.get('has_fixed'),j
for fruit,stem in [('grape','500'),('grape','2000'),('grape','1000'),('apple','20150921_131453_image1161'),('apple','20150921_131234_image406'),('apple','20150921_131234_image6')]:
 code,b=a.get_bytes('/img?fruit='+fruit+'&stem='+stem);assert code==200 and b.startswith(b'\x89PNG')
out['presentation']={'port':5791,'bind':'127.0.0.1','password_source':'~/.council/labeltool.env','grape500_unmodified':True,'six_candidates_open':True}
(R/'published_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('게시 문서4개 인증·바이트 동일, 발표 사본 초기상태·후보6장 통과. 저장0.')
