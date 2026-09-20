# 별도 검수 사본에서 운영 데이터셋의 제외 사진과 분리 의심 두 번호를 확인한다.
from pathlib import Path
import sys,json,time
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
sb=str(C/'sandbox_team');L.sync(sb=sb);port=L.free_port(5781);p=L.start(port=port,sb=sb);b=None
try:
 a=L.Api(f'http://127.0.0.1:{port}')
 rows=a.get('/api/team_review?fruit=apple&stem=dataset1_back_901')['rows']
 L.chk('분리 의심 두 번호 보존',any(r['source']=='suspects_split.csv' and r['inst_ids']=='24/25' for r in rows))
 b=L.browser(base=f'http://127.0.0.1:{port}');b.click('[data-view=exp]');b.click('#team-grape summary');b.wait("return document.querySelectorAll('#team-grape-list button').length===202")
 b.js("[...document.querySelectorAll('#team-grape-list button')].find(b=>b.textContent==='8').click()")
 b.wait("return location.pathname==='/team_photo/grape/8'")
 L.chk('운영 검수판에서 제외된8번 원본 보기',b.js("return document.querySelector('img').complete && document.querySelector('img').naturalWidth>0"))
 b.go('/');b.wait("return !!document.querySelector('#fruit option')");L.close_tour(b);b.open_photo('grape','741')
 b.click('[data-tool=pan]');v=L.ev(b,'({...S.view})');b.drag('#cv',330,230,360,250);after=L.ev(b,'({...S.view})');L.chk('이동 단추 드래그',abs(after['tx']-v['tx']-30)<1 and abs(after['ty']-v['ty']-20)<1)
 b.click('[data-task=box]');time.sleep(.4);L.chk('상자에서는 잘못된 이동 도구 비활성·커서',b.js("return document.querySelector('[data-tool=pan]').disabled && document.querySelector('#cv').style.cursor==='crosshair'"))
finally:
 if b:b.close()
 L.stop(p)
(C/'evidence/team_independent.json').write_text(json.dumps({'passed':L.OK,'failed':L.BAD},ensure_ascii=False,indent=2));sys.exit(bool(L.summary('team_independent')))
