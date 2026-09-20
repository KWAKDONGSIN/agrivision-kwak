# 후보의 원본·라벨·겹침을 같은 좌표에서 실제 브라우저로 비교한다.
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent;T=R.parents[2];sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
rows=json.loads(Path(sys.argv[1]).read_text());out=Path.home()/'ff_shots/demo_260921';b=L.browser(base='http://127.0.0.1:5791')
try:
 b._s('POST','/window/rect',{'width':1300,'height':1400})
 b.js('''document.body.innerHTML='<main></main>';document.body.style='background:white;color:black;margin:8px';window.ready=false;
 Promise.all(arguments[0].map(async r=>{const [fruit,stem,box]=r,q='fruit='+fruit+'&stem='+encodeURIComponent(stem),d=document.createElement('div');document.querySelector('main').append(d);d.innerHTML='<b>'+stem+' '+box.join(',')+'</b><div style="display:flex"></div>';const ims=await Promise.all(['/img?'+q,'/mask?'+q+'&layer=gt'].map(url=>new Promise((res,rej)=>{let i=new Image;i.onload=()=>res(i);i.onerror=rej;i.src=url})));let [x0,y0,x1,y1]=box;
 const a=document.createElement('canvas');a.width=ims[0].width;a.height=ims[0].height;let ac=a.getContext('2d');ac.drawImage(ims[1],0,0);let z=ac.getImageData(0,0,a.width,a.height);for(let n=0;n<z.data.length;n+=4){let on=z.data[n]>0;z.data[n]=255;z.data[n+1]=0;z.data[n+2]=0;z.data[n+3]=on?90:0}ac.putImageData(z,0,0);
 for(let k=0;k<3;k++){let c=document.createElement('canvas');c.width=400;c.height=380;d.lastChild.append(c);let ctx=c.getContext('2d');ctx.drawImage(ims[k===1?1:0],x0,y0,x1-x0,y1-y0,0,0,400,380);if(k===2)ctx.drawImage(a,x0,y0,x1-x0,y1-y0,0,0,400,380)}
 })).then(()=>window.ready=true);''',rows)
 b.wait('return window.ready',60);p=out/(Path(sys.argv[1]).stem+'.png');b.shot(str(p));print(p)
finally:b.close()
