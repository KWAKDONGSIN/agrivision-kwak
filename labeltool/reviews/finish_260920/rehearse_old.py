# 옛 서버 복원 사본을 실행해 되돌릴 길을 확인한다.
from pathlib import Path
import sys, shutil, json, datetime, urllib.parse
F=Path(__file__).resolve().parent; T=F.parents[2]
sys.path.insert(0,str(T/'tests/lib'))
import sandbox as L
D=F/'rollback_old_sandbox_retry'
shutil.copytree(T/'app',D/'app',ignore=shutil.ignore_patterns('cache','logs','__pycache__'))
for sub in ('app','export'):
 shutil.copytree(T/'_archive/pre_refactor_260920'/sub,D/sub,dirs_exist_ok=True,ignore=shutil.ignore_patterns('cache','logs','__pycache__'))
shutil.copytree(T/'data',D/'data')
port=L.free_port(5601);p=L.start(port=port,sb=str(D));out={'at':datetime.datetime.now().isoformat(),'port':port,'pid':p.pid}
try:
 a=L.Api(base=f'http://127.0.0.1:{port}');fruits=a.get('/api/fruits')['fruits'];assert len(fruits)==4
 for f in fruits:
  fruit=f['fruit'];s=a.get('/api/list?fruit='+fruit)['items'][0]['stem'];assert a.get('/api/item?'+urllib.parse.urlencode({'fruit':fruit,'stem':s}))['stem']==s
 out['fruits']=4;out['item_checks']=4;out['restored_server_identical']=(D/'app/server.py').read_bytes()==(T/'_archive/pre_refactor_260920/app/server.py').read_bytes();assert out['restored_server_identical']
finally:L.stop(p)
(F/'evidence/rollback_old.json').write_text(json.dumps(out,indent=2));print(out)
