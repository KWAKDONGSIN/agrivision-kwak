# 새 완료 버튼의 미완성 편집 보호와 과일 변경 상태 해제를 검증한다.
from pathlib import Path
import sys,time,json,shutil
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
for p in (C/'candidate/app/static/js').glob('*.js'):shutil.copy2(p,C/'sandbox_after/app/static/js'/p.name)
b=L.browser(base='http://127.0.0.1:5761')
try:
 b.open_photo('apple','20150919_174151_image1')
 b.js("window.__posts=[];const old=window.fetch;window.fetch=(u,o)=>{if(o?.method==='POST')window.__posts.push(String(u));return old(u,o)}")
 L.run(b,'S.poly=[[1,1],[2,2],[3,1]]');b.click('#btn-confirm');L.chk('그리는 중 다각형은 확인 요청0',b.js('return window.__posts.length')==0)
 L.run(b,'S.poly=[];S.numMode=true;S.numPoly=[[1,1],[2,2],[3,1]]');b.click('#btn-confirm');L.chk('그리는 중 번호는 확인 요청0',b.js('return window.__posts.length')==0)
 L.run(b,'S.numMode=false;S.numPoly=[];S.edDirty=true')
 b.js("document.querySelector('#fruit').value='grape';document.querySelector('#fruit').dispatchEvent(new Event('change'))");L.chk('미저장 변경 경고',bool(b.alert_text()));b.alert_ok();time.sleep(1)
 L.chk('과일 변경 뒤 옛 사진 상태 해제',L.ev(b,"S.fruit==='grape' && !S.stem && !S.item && !S.ed && !S.inst && !S.edDirty"))
 L.run(b,'S.bDirty=true');L.chk('상자 미저장 새로고침 경고',b.js("const e=new Event('beforeunload',{cancelable:true});window.dispatchEvent(e);return e.defaultPrevented"));L.run(b,'S.bDirty=false')
 L.run(b,'S.savedAt=Date.now()');b.open_photo('grape','741');L.chk('새 사진에 옛 저장안내 없음',L.ev(b,'S.savedAt===0'))
finally:b.close()
(C/'evidence/safety.json').write_text(json.dumps({'passed':L.OK,'failed':L.BAD},ensure_ascii=False,indent=2));sys.exit(bool(L.summary('easy_safety')))
