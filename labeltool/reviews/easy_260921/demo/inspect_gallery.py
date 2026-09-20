# 읽기 전용 이미지와 라벨을 Firefox 화면에서 나란히 확인한다.
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parent;T=R.parents[2]
sys.path.insert(0,str(T/'tests/lib'));import sandbox as L
fruit=sys.argv[1];stems=sys.argv[2:];out=Path.home()/'ff_shots/demo_260921';out.mkdir(exist_ok=True)
b=L.browser(base='http://127.0.0.1:5791')
try:
 b._s('POST','/window/rect',{'width':1600,'height':1200})
 b.js('''document.body.innerHTML='<main style="display:grid;grid-template-columns:repeat(3,1fr);gap:5px"></main>';document.body.style='background:white;margin:4px';window.ready=false;
 const main=document.querySelector('main');Promise.all(arguments[1].map(async stem=>{const f=arguments[0],q='fruit='+f+'&stem='+encodeURIComponent(stem);let ims=await Promise.all(['/img?'+q,'/mask?'+q+'&layer=gt'].map(url=>new Promise((res,rej)=>{let i=new Image;i.onload=()=>res(i);i.onerror=rej;i.src=url})));const d=document.createElement('div');d.innerHTML='<b>'+stem+'</b><canvas width="500" height="490"></canvas>';main.append(d);const c=d.querySelector('canvas'),x=c.getContext('2d'),i=ims[0],m=ims[1];let s=Math.min(500/i.width,490/i.height),w=i.width*s,h=i.height*s;x.drawImage(i,0,0,w,h);const a=document.createElement('canvas');a.width=i.width;a.height=i.height;let ac=a.getContext('2d');ac.drawImage(m,0,0);let z=ac.getImageData(0,0,a.width,a.height);for(let n=0;n<z.data.length;n+=4){let on=z.data[n]>0;z.data[n]=255;z.data[n+1]=0;z.data[n+2]=0;z.data[n+3]=on?95:0}ac.putImageData(z,0,0);x.drawImage(a,0,0,w,h)})).then(()=>window.ready=true);''',fruit,stems)
 b.wait('return window.ready',60);path=out/(fruit+'_'+stems[0]+'.png');b.shot(str(path));print(path)
finally:b.close()
