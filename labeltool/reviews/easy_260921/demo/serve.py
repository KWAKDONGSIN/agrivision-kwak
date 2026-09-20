# 시연 저장을 운영 데이터와 분리하는 연습 서버를 실행한다.
from pathlib import Path
import sys,time
R=Path(__file__).resolve().parent;T=R.parents[2]
sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
assert not (R/'sandbox').exists(), '기존 연습 기록을 보존한 뒤 새 사본을 준비한다'
L.sync(sb=str(R/'sandbox'),src=str(T))
pw=next(l.split('=',1)[1].strip().strip('\"\'') for l in (Path.home()/'.council/labeltool.env').read_text().splitlines() if l.startswith('LABELTOOL_PASSWORD='))
p=L.start(port=5791,sb=str(R/'sandbox'),data_root=L.DR,pw=pw)
try:
 while not (R/'stop').exists():time.sleep(2)
finally:L.stop(p)
