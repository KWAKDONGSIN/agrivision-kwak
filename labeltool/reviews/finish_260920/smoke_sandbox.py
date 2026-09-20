# 운영 반영 사본에서 전환 후 점검 스크립트와 복원 파일을 검증한다.
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, sys
F=Path(__file__).resolve().parent;T=F.parents[2]
sys.path.insert(0,str(T/'tests/lib'))
import sandbox as L
D=F/'smoke_sandbox'
for sub in ('app','export','data'):
 shutil.copytree(T/sub,D/sub,ignore=shutil.ignore_patterns('logs','cache','__pycache__'))
port=L.free_port(5671);pw='finish-local-smoke';p=L.start(port=port,sb=str(D),pw=pw)
def fingerprints():
 return {str(x.relative_to(D/'data')):hashlib.sha256(x.read_bytes()).hexdigest() for x in (D/'data').rglob('*') if x.is_file() and '_status_backup_' not in x.name}
before=fingerprints()
try:
 r=subprocess.run([sys.executable,str(F/'after_restart_smoke.py'),'--url',f'http://127.0.0.1:{port}','--tool-root',str(D)],env=dict(os.environ,LABELTOOL_PASSWORD=pw),capture_output=True,text=True,timeout=180)
 (F/'evidence/smoke.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 out=json.loads(r.stdout);out['data_identical']=before==fingerprints();assert out['data_identical'];out['port']=port;out['pid']=p.pid
finally:L.stop(p)
(F/'evidence/smoke.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
# 사람이 쓰는 cp 명령과 같은 파일 복원. 실행 중인 자기 서버만 이미 종료했다.
for sub in ('app','scripts','export'):
 subprocess.run(['cp','-a',str(T/'_archive/pre_finish_260920'/sub)+'/.',str(D/sub)+'/'],check=True)
old=json.loads((F/'evidence/pre_change_app_sha256.json').read_text())['files']
assert all(hashlib.sha256((D/'app'/r).read_bytes()).hexdigest()==h for r,h in old.items())
p=L.start(port=port,sb=str(D),pw=pw)
try:
 a=L.Api(base=f'http://127.0.0.1:{port}',pw=pw);assert len(a.get('/api/fruits')['fruits'])==4
 out={'at':datetime.datetime.now().isoformat(),'restored_app_hashes':len(old),'port':port,'new_pid':p.pid,'login_fruits':4,'production_restart_executed':False}
finally:L.stop(p)
(F/'evidence/rollback_pre_finish.json').write_text(json.dumps(out,indent=2));print(out)
