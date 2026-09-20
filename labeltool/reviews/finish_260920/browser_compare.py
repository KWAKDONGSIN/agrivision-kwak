# 옛 화면과 반영된 화면의 실제 12장 스크린샷과 36상태를 다시 비교한다.
from pathlib import Path
import sys, shutil, json, time, hashlib, datetime
F=Path(__file__).resolve().parent;T=F.parents[2]
sys.path.insert(0,str(T/'tests/lib'))
import sandbox as L
stems=json.loads((T/'tests/fixtures/baseline_260920/stems.json').read_text())
result={'at':datetime.datetime.now().isoformat(),'old_source':'codex_resume/browser12/old','new_source':'operating files','screenshots':{},'states':{}}
for tag,source in [('old',T/'cycles/260920_structure/codex_resume/browser12/old'),('new',T)]:
 D=F/('browser_confirmed_'+tag)
 for sub in ('app','export'):
  shutil.copytree(source/sub,D/sub,ignore=shutil.ignore_patterns('cache','logs','__pycache__','_backup*'))
 shutil.copytree(T/'data',D/'data')
 port=L.free_port(5651);p=L.start(port=port,sb=str(D));b=None
 try:
  b=L.browser(w=1366,h=768,base=f'http://127.0.0.1:{port}')
  result['screenshots'][tag]={};result['states'][tag]={}
  for fruit,ss in stems.items():
   for i,stem in enumerate(ss):
    b.open_photo(fruit,stem);time.sleep(.5)
    b.js("window.__codexErrors=[];window.onerror=m=>window.__codexErrors.push(String(m));window.onunhandledrejection=e=>window.__codexErrors.push(String(e.reason))")
    for mode,key in [('mask',None),('box','x'),('num','k')]:
     if key:b.key(key)
     time.sleep(.5)
     state=L.ev(b,"({stem:S.stem,fruit:S.fruit,box:!!S.boxMode,num:!!S.numMode,nBoxes:(S.boxes||[]).length,numN:S.instN||null,counts:document.querySelector('#cnts').textContent,info:document.querySelector('#boxinfo').textContent,errors:window.__codexErrors,canvas:[document.querySelector('#cv').width,document.querySelector('#cv').height]})")
     assert not state['errors'];result['states'][tag][fruit+'/'+stem+'/'+mode]=state
    shot=Path.home()/'ff_shots/finish_260920_confirmed'/tag/(fruit+'_'+str(i)+'.png');shot.parent.mkdir(parents=True,exist_ok=True);b.shot(str(shot));result['screenshots'][tag][fruit+'/'+str(i)]=hashlib.sha256(shot.read_bytes()).hexdigest()
    b.go('/');b.wait("return !!document.querySelector('#fruit option')")
 finally:
  if b:b.close()
  L.stop(p)
 (F/'evidence/browser12_progress.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
result['screenshots_equal']=result['screenshots']['old']==result['screenshots']['new'];result['states_equal']=result['states']['old']==result['states']['new']
(F/'evidence/browser12.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert result['screenshots_equal'] and result['states_equal'], '화면 차이 발생'
print('12장 스크린샷 바이트 동일·36상태 동일·콘솔오류0')
