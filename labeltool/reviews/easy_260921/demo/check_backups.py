# 예비 사진 네 장이 실제 편집 화면에서 열리는지 읽기만으로 확인한다.
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent;T=R.parents[2];sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
b=L.browser(base='http://127.0.0.1:5791');rows=[]
try:
 for fruit,stem in [('grape','2000'),('grape','1000'),('apple','20150921_131234_image406'),('apple','20150921_131234_image6')]:
  b.open_photo(fruit,stem);assert L.ev(b,'S.stem')==stem and L.ev(b,'S.img.naturalWidth')>0
  p=Path.home()/'ff_shots/demo_260921'/('backup_'+stem+'.png');b.shot(str(p));rows.append({'fruit':fruit,'stem':stem,'opened':True,'screenshot':str(p)})
finally:b.close()
(R/'backup_checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('예비4장 편집 화면 열기 통과, 저장0')
