# 무효·비유한 상자 요청의 거절과 기존 저장 파일 보존을 검증한다.
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from PIL import Image

T = Path(__file__).resolve().parents[2]
D = Path(tempfile.mkdtemp(prefix='finite_', dir=T/'tests/_sandbox'))
shutil.copytree(T/'app', D/'app', ignore=shutil.ignore_patterns('logs', 'cache', '__pycache__'))
for fruit in ('peach', 'grape', 'apple', 'blueberry'):
    p = D/'fixture'/fruit/'images'
    p.mkdir(parents=True)
    Image.new('RGB', (32, 32)).save(p/'probe.png')
os.environ['LABELTOOL_DATA_ROOT'] = str(D/'fixture')
os.environ['LABELTOOL_PASSWORD'] = ''
sys.path.insert(0, str(D/'app'))
import server
c = server.app.test_client()
base = {'fruit': 'peach', 'stem': 'probe', 'by': '보호시험'}
good = {'xyxy': [2, 2, 20, 20]}
r = c.post('/api/boxes', json={**base, 'boxes': [good]})
assert r.status_code == 200 and r.json['n_boxes'] == 1
paths = [D/'data/peach/boxes/probe.json', D/'data/peach/status.json']
before = [p.read_bytes() for p in paths]
n = 1
bad = [[None], [3], [{'xyxy': [1, 1, 1, 1]}]]
for value in (float('inf'), float('-inf'), float('nan'), 'Infinity', 'NaN'):
    for axis in range(4):
        xy = [2, 2, 20, 20]
        xy[axis] = value
        bad.extend([[{'xyxy': xy}], [good, {'xyxy': xy}]])
for boxes in bad:
    r = c.post('/api/boxes', json={**base, 'boxes': boxes})
    assert r.status_code == 400 and r.json['error'], r.data
    assert [p.read_bytes() for p in paths] == before
    n += 2
r = c.post('/api/boxes', json={**base, 'boxes': [None, good, {'xyxy': ['bad']}]})
assert r.status_code == 200 and r.json['n_boxes'] == 1 and r.json['dropped'] == 2
n += 1
r = c.post('/api/boxes', json={**base, 'boxes': [{'xyxy': [20.4, 20.4, -1, -1]}]})
assert r.status_code == 200 and r.json['boxes'][0]['xyxy'] == [0, 0, 20, 20]
n += 1
r = c.post('/api/boxes', json={**base, 'boxes': []})
assert r.status_code == 200 and r.json['removed'] and not paths[0].exists()
assert 'confirmed_boxes' not in json.loads(paths[1].read_text())['probe']
n += 2
print(f'통과 {n} / 실패 0')
