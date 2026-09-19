"""Reject entirely invalid box submissions without deleting a previous human result.
작성: 2026-09-20. Synthetic images and writes are confined to tests/_sandbox.
"""
import os,sys,json
from pathlib import Path
from PIL import Image
import sandbox as L
D=Path(L.SB_ROOT)/'sb_boxes_reject'
L.sync(str(D),data=False)
fixture=D/'fixture'
for fruit in L.FRUITS:
    for sub in ('images','masks'):
        p=fixture/fruit/sub;p.mkdir(parents=True,exist_ok=True)
        Image.new('L',(32,32),255).save(p/'probe.png')
os.environ['LABELTOOL_DATA_ROOT']=str(fixture)
os.environ['LABELTOOL_PASSWORD']=''
sys.path.insert(0,str(D/'app'))
import server
client=server.app.test_client()
base={'fruit':'peach','stem':'probe','by':'상자 보존 시험'}
r=client.post('/api/boxes',json={**base,'boxes':[{'xyxy':[2,2,20,20]}]})
L.chk('유효 상자 HTTP 200',r.status_code==200)
L.chk('유효 상자 1개 저장',r.get_json().get('n_boxes')==1)
box=D/'data/peach/boxes/probe.json';status=D/'data/peach/status.json'
before_box,before_status=box.read_bytes(),status.read_bytes()
for i,boxes in enumerate([[{'xyxy':[1,1,1,1]}],[{'xyxy':['bad']}],[{'xyxy':[1,1,1,1]},{'nope':1}]],1):
    r=client.post('/api/boxes',json={**base,'boxes':boxes})
    L.chk('무효 요청 %s HTTP 400'%i,r.status_code==400)
    L.chk('무효 요청 %s 상자 바이트 보존'%i,box.exists() and box.read_bytes()==before_box)
    L.chk('무효 요청 %s 판정 바이트 보존'%i,status.read_bytes()==before_status)
r=client.post('/api/boxes',json={**base,'boxes':[]})
L.chk('명시한 빈 목록은 되돌리기 성공',r.status_code==200 and r.get_json().get('removed') is True)
L.chk('명시한 빈 목록은 상자 수정본 해제',not box.exists())
L.chk('상자 확정만 해제','confirmed_boxes' not in json.loads(status.read_text())['probe'])
sys.exit(1 if L.summary('t5_boxes_reject') else 0)
