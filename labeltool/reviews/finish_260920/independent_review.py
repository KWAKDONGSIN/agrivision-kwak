# 새 사본·새 포트로 후보 반영과 좌표 보호 및 원래 기준선 보존을 독립 검수한다.
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, sys, urllib.parse
F=Path(__file__).resolve().parent;T=F.parents[2];C=T/'cycles/260920_structure/codex_resume/candidate'
sys.path.insert(0,str(T/'tests/lib'))
import sandbox as L
out={'at':datetime.datetime.now().isoformat(),'candidate_files':{}}
for name in ['boxes','counts','dashboard','dupes','export','instances','masks','photos']:
 rel=Path('app/api')/(name+'.py');actual=(T/rel).read_text();expected=(C/rel).read_text()
 if name=='boxes':
  actual=actual.replace('        try:\n            boxes, dropped, over = clean(raw, w, h)\n        except ValueError as e:\n            return err_json(str(e), 400)','        boxes, dropped, over = clean(raw, w, h)').replace('                try:\n                    boxes, _, _ = clean(tb, w, h)\n                except ValueError as e:\n                    return err_json(str(e), 400)','                boxes, _, _ = clean(tb, w, h)')
 assert actual==expected,str(rel);out['candidate_files'][str(rel)]='identical except approved finite guard' if name=='boxes' else 'identical'
for path in (C/'app').rglob('*.py'):
 if '__pycache__' in path.parts: continue
 rel=path.relative_to(C/'app');actual=(T/'app'/rel).read_text();expected=path.read_text()
 if str(rel)=='api/boxes.py':continue
 if str(rel)=='domain/rules.py':
  actual=actual.replace('import math\n\n','').replace('        if not all(math.isfinite(v) for v in (x1, y1, x2, y2)):\n            raise ValueError("상자 좌표에는 유한한 숫자만 사용할 수 있습니다.")\n','')
 assert actual==expected,str(rel)
 out['candidate_files'][str(rel)]='identical except authorized finite guard' if str(rel)=='domain/rules.py' else 'identical'
assert (T/'scripts/ff.py').read_bytes()==(C/'scripts/ff.py').read_bytes()
assert (T/'app/README.md').read_bytes()==(C/'app/README.md').read_bytes()
old=T/'_archive/pre_finish_260920/tests/fixtures/baseline_260920';preserved=T/'tests/fixtures/baseline_260920_pre_split'
oldmap={str(p.relative_to(old)):hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
newmap={str(p.relative_to(preserved)):hashlib.sha256(p.read_bytes()).hexdigest() for p in preserved.rglob('*') if p.is_file()}
assert oldmap==newmap;out['old_baseline_files_preserved']=len(oldmap)
assert json.loads((old/'bundles.json').read_text())==json.loads((T/'tests/fixtures/baseline_260920/bundles.json').read_text())
D=F/'review_fresh_final'
for sub in ('app','export','data'):
 shutil.copytree(T/sub,D/sub,ignore=shutil.ignore_patterns('logs','cache','__pycache__'))
port=L.free_port(5721);pw='independent-finish-review';p=L.start(port=port,sb=str(D),pw=pw);out.update(port=port,pid=p.pid)
try:
 a=L.Api(base=f'http://127.0.0.1:{port}',pw=pw);fruit='peach';stem=a.get('/api/list?fruit=peach')['items'][0]['stem'];base={'fruit':fruit,'stem':stem,'by':'별도검수'}
 paths=[D/'data/peach/boxes'/(stem+'.json'),D/'data/peach/status.json']
 good={'xyxy':[25.6,27.2,-4,2.1]}
 code,r=a.post('/api/boxes',{**base,'boxes':[good]});assert code==200 and r['boxes'][0]['xyxy']==[0,2,26,27]
 before=[x.read_bytes() for x in paths];checks=[]
 for boxes in [[None],[3],[{'xyxy':['not-a-coordinate']}],[{'xyxy':[0,0,float('nan'),25]}],[good,{'xyxy':[0,float('inf'),20,25]}]]:
  code,r=a.post('/api/boxes',{**base,'boxes':boxes});assert code==400 and r['error'];assert [x.read_bytes() for x in paths]==before;checks.append({'http':code,'box_and_status_unchanged':True})
 code,r=a.post('/api/boxes',{**base,'boxes':[None,good]});assert code==200 and r['n_boxes']==1 and r['dropped']==1
 code,r=a.post('/api/boxes',{**base,'boxes':[]});assert code==200 and r['removed'] and not paths[0].exists()
 out['boundary_requests']=checks;out['normal_clipped_rounded']=True;out['mixed_valid']=True;out['empty_revert']=True
 r=subprocess.run([sys.executable,str(F/'after_restart_smoke.py'),'--url',f'http://127.0.0.1:{port}','--tool-root',str(D)],env=dict(os.environ,LABELTOOL_PASSWORD=pw),capture_output=True,text=True,timeout=180)
 (F/'evidence/review_smoke_final.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr;out['fresh_smoke']=json.loads(r.stdout)
finally:L.stop(p)
# 사용자에게 제공한 복원 한 줄의 cp 부분을 그대로 새 경로에 대입한다.
subprocess.run(['cp','-a',str(T/'_archive/pre_finish_260920')+'/.',str(D)+'/'],check=True)
pre=json.loads((F/'evidence/pre_change_app_sha256.json').read_text())['files'];assert all(hashlib.sha256((D/'app'/r).read_bytes()).hexdigest()==h for r,h in pre.items())
p=L.start(port=port,sb=str(D),pw=pw)
try:
 a=L.Api(base=f'http://127.0.0.1:{port}',pw=pw);assert len(a.get('/api/fruits')['fruits'])==4;out['exact_cp_restore_boot']={'files':len(pre),'pid':p.pid,'fruits':4}
finally:L.stop(p)
(F/'evidence/independent_review_final.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
