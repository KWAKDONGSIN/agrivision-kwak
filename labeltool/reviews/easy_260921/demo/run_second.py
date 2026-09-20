# 새 사본에서 최종 대본을 재실행하고 문서 검증용 서버를 유지한다.
from pathlib import Path
import sys,subprocess,shutil,time
R=Path(__file__).resolve().parent;T=R.parents[2];sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
sb=R/'sandbox2';assert not sb.exists(),'이전 실행 증거를 덮지 않는다'
L.sync(sb=str(sb),src=str(T));shutil.copytree(R/'static',sb/'app/static',dirs_exist_ok=True)
shots=sb/'app/static/help/demo_260921';shots.mkdir(parents=True,exist_ok=True);first=Path.home()/'ff_shots/demo_260921/rehearsal1'
for p in first.glob('*.png'):shutil.copy2(p,shots/p.name)
shutil.copy2(first/'18.png',shots/'20.png');shutil.copy2(first/'29.png',shots/'31.png')
p=L.start(port=5792,sb=str(sb),data_root=L.DR)
try:
 r=subprocess.run([sys.executable,'-u',str(R/'rehearse.py'),'rehearsal2','http://127.0.0.1:5792']);(R/'rehearsal2.rc').write_text(str(r.returncode))
 while not (R/'stop2').exists():time.sleep(2)
finally:L.stop(p)
