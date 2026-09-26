# /api/worklog 가 NaN·Infinity 숫자를 0 으로 바꿔 표준 JSON 한 줄만 적는지 검증한다(0925 C24).
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from PIL import Image

T = Path(__file__).resolve().parents[2]
D = Path(tempfile.mkdtemp(prefix='worklog_', dir=T/'tests/_sandbox'))
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
wl = D/'app'/'logs'/'worklog.jsonl'
base = {'fruit': 'peach', 'stem': 'probe', 'action': 'save', 'by': '기록시험'}
n = 0
for bad in ('NaN', 'nan', 'Infinity', '-Infinity', 'inf'):
    r = c.post('/api/worklog', json={**base, 'active_s': bad, 'edits': bad})
    assert r.status_code == 200, (bad, r.status_code, r.data[:200])
    line = wl.read_text(encoding='utf-8').splitlines()[-1]
    row = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    assert row['active_s'] == 0 and row['edits'] == 0, (bad, row)
    n += 1
r = c.post('/api/worklog', json={**base, 'active_s': 12.34, 'edits': '3', 'sam': -5, 'wall_s': 9e9})
row = json.loads(wl.read_text(encoding='utf-8').splitlines()[-1])
assert r.status_code == 200 and row['active_s'] == 12.3 and row['edits'] == 3 and row['sam'] == 0 and row['wall_s'] == 1e6, row
n += 1
print(f'통과 {n} / 실패 0')
