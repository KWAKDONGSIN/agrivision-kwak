# 사본에서 실제 클릭·저장·안전장치와 팀원 읽기 자료를 검증한다.
from pathlib import Path
import sys,json,time,csv
C=Path(__file__).resolve().parent
sys.path.insert(0,str(C/'candidate/tests/lib'));import sandbox as L
L.SHOTS='/home/kds0206/ff_shots/easy_260921';Path(L.SHOTS).mkdir(exist_ok=True)
base='http://127.0.0.1:5761';a=L.Api(base);j=a.get('/api/team_review?fruit=grape');L.chk('202장과 출처99/103',j['n']==202 and [len(g['stems']) for g in j['groups']]==[99,103])
L.chk('잘못된 과일400',a.get2('/api/team_review?fruit=none')[0]==400)
L.chk('제외 사진 원본 보기',a.get_bytes('/team_photo/grape/8?image=1')[1][:8]==b'\x89PNG\r\n\x1a\n')
L.chk('원본 보기 경로 방어',a.get2('/team_photo/grape/not-a-number')[0]==404)
ap=a.get('/api/team_review?fruit=apple');source=list(csv.DictReader(open('/data/project/2026summer/platform/work/park_seongmoon/apple_check/review_list.csv')));expected=list(dict.fromkeys(r['stem'] for r in source));L.chk('검수 목록 원문 순서 동일',ap['queue']==expected)
b=L.browser(base=base)
try:
 b.js("document.querySelector('#who').value='Codex 사본 시험'")
 b.shot('01_list.png');b.open_photo('grape','740');b.shot('02_edit.png')
 L.chk('사진과 안내·진행·슬라이더',L.ev(b,"S.stem==='740' && document.querySelector('#edit-progress').textContent.includes('번째') && document.querySelector('#brush').type==='range'"))
 b.key('?');L.chk('물음표로 자동표32개',b.js("return document.querySelector('.shortcut-panel').open && document.querySelectorAll('[data-key-table] tbody tr').length===32"));b.shot('03_keys.png');b.click('#tour-x')
 b.click('[data-tool=erase]');L.chk('선택과 커서',b.js("return document.querySelector('[data-tool=erase]').classList.contains('on') && document.querySelector('#cv').style.cursor==='cell'"))
 before=L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)');pt=L.ev(b,"(()=>{const i=S.ed.findIndex(x=>x);return [(i%S.W)*S.view.s+S.view.tx,Math.floor(i/S.W)*S.view.s+S.view.ty]})()")
 b.drag('#cv',*pt,pt[0]+2,pt[1]+2);L.chk('지우개 실제 변경',L.ev(b,'S.edDirty') and L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')<before)
 b.click('#undo');L.chk('되돌리기 화소 복원',L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')==before)
 b.click('#redo');L.chk('다시하기',L.ev(b,'Array.from(S.ed).reduce((a,x)=>a+x,0)')<before)
 # 과일 변경 취소 시 상태 그대로.
 b.js("document.querySelector('#fruit').value='apple';document.querySelector('#fruit').dispatchEvent(new Event('change'))")
 L.chk('과일 변경 경고',bool(b.alert_text()));b.alert_cancel();L.chk('과일 변경 취소 보존',L.ev(b,"S.fruit==='grape' && document.querySelector('#fruit').value==='grape' && S.edDirty"))
 b.click('#btn-save');b.wait("return !window.eval('S.edDirty')");b.shot('04_saved.png')
 L.chk('저장과 확정 구분',not L.ev(b,'!!S.item.confirmed'))
 b.click('#btn-confirm');time.sleep(1)
 stored=a.get('/api/item?fruit=grape&stem=740');L.chk('다 했어요가 수정함 확인 기록',stored['confirmed']['status']=='fixed')
 b.shot('05_confirmed.png')
 b.click('[data-view=exp]');b.click('#team-grape summary');b.wait("return document.querySelectorAll('#team-grape-list button').length===202");b.shot('06_team_grape.png')
 b.open_photo('apple',expected[0]);b.wait("return window.eval('S.teamSuspects && S.teamSuspects.length>0')");b.click('#team-suspect');b.shot('07_team_apple.png');L.chk('의심 개체 켜기',L.ev(b,"S.teamSuspects.length>0 && document.querySelector('#team-suspect').checked"))
 b.click('[data-view=list]');b.js("document.querySelector('#f-q').value='';document.querySelector('#f-sort').value='teamreview';document.querySelector('#f-sort').dispatchEvent(new Event('change'))")
 b.wait("return document.querySelector('#listinfo').textContent.includes('review_list')");L.chk('첫 우선 사진 일치',L.ev(b,'S.items[0].stem')==expected[0]);b.shot('08_priority.png')
finally:b.close()
(C/'evidence/check_easy.json').write_text(json.dumps({'passed':L.OK,'failed':L.BAD},ensure_ascii=False,indent=2))
sys.exit(bool(L.summary('easy_browser')))
