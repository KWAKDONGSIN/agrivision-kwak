# 새 사본과 새 포트에서 실제 마우스로 배율2/3 상자 이동·크기조절을 검증한다.
from pathlib import Path
import sys,json,time
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
sb=str(C/'sandbox_scale');L.sync(sb=sb);port=L.free_port(5771);p=L.start(port=port,sb=sb);b=None;result=[]
try:
 b=L.browser(base=f'http://127.0.0.1:{port}');b.open_photo('grape','740');b.click('[data-task=box]')
 for scale in [2,3]:
  L.run(b,f'S.boxes=[];S.bsel=-1;S.bDirty=false;S.btool="draw";S.view={{s:{scale},tx:0,ty:0}};S.dirty=true;');time.sleep(.3)
  b.drag('#cv',200,160,440,340);before=L.ev(b,'S.boxes[0].xyxy.slice()');b.click('[data-btool=pick]')
  b.drag('#cv',310,245,340,266);after=L.ev(b,'S.boxes[0].xyxy.slice()');want=[before[0]+30/scale,before[1]+21/scale,before[2]+30/scale,before[3]+21/scale]
  error=max(abs(x-y) for x,y in zip(after,want));L.chk(f'{scale}배 이동 오차≤0.5화소',error<=.51,{'before':before,'after':after,'expected':want,'error':error})
  x,y=after[2]*scale,after[3]*scale;b.drag('#cv',x,y,x+24,y+18);resized=L.ev(b,'S.boxes[0].xyxy.slice()');L.chk(f'{scale}배 크기조절',abs(resized[2]-after[2]-24/scale)<=.51 and abs(resized[3]-after[3]-18/scale)<=.51)
  result.append(dict(scale=scale,before=before,after=after,want=want,error=error,resized=resized))
  L.run(b,'S.bDirty=false')
finally:
 if b:b.close()
 L.stop(p)
(C/'evidence/scale.json').write_text(json.dumps(result,indent=2));sys.exit(bool(L.summary('scale')))
