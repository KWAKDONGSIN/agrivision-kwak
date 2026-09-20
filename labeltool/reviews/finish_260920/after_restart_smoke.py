# 재시작 뒤 로그인·사진·상자 저장과 복원을 로컬 서버에서 점검한다.
import argparse
import datetime
import getpass
import http.cookiejar
import json
import os
from pathlib import Path
import shutil
import urllib.error
import urllib.parse
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:5111')
    ap.add_argument('--tool-root', type=Path, default=Path(__file__).resolve().parents[3])
    ap.add_argument('--read-only', action='store_true')
    args = ap.parse_args()
    assert urllib.parse.urlparse(args.url).hostname in ('127.0.0.1', 'localhost'), '서버 안에서 실행하세요.'
    root = args.tool_root.resolve()
    assert (root/'app/server.py').is_file() and (root/'data').is_dir()
    pw = os.environ.get('LABELTOOL_PASSWORD')
    if not pw:
        envfile = Path.home()/'.council/labeltool.env'
        if envfile.exists():
            for line in envfile.read_text().splitlines():
                if line.startswith('LABELTOOL_PASSWORD='):
                    pw = line.split('=', 1)[1].strip().strip('\"\'')
    if not pw:
        pw = getpass.getpass('툴 비밀번호. ')
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def request(path, data=None):
        if data is not None:
            req = urllib.request.Request(args.url+path, json.dumps(data).encode(), {'Content-Type': 'application/json'})
        else:
            req = args.url+path
        try:
            with op.open(req, timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
    def get(path):
        code, body = request(path)
        assert code == 200, (path, code)
        return json.loads(body)
    assert request('/api/fruits')[0] == 401, '비로그인 API가 401이어야 합니다.'
    op.open(args.url+'/login', urllib.parse.urlencode({'password': pw}).encode(), timeout=30).read()
    health = get('/api/health')
    assert Path(health['out_dir']).resolve() == (root/'data').resolve(), '접속 서버와 복원 자료 경로가 다릅니다.'
    fruits = get('/api/fruits')['fruits']
    assert {x['fruit'] for x in fruits} == {'peach', 'grape', 'apple', 'blueberry'}
    out = {'at': datetime.datetime.now().astimezone().isoformat(), 'anonymous': 401, 'fruits': 4, 'photos': []}
    for f in fruits:
        fruit = f['fruit']; stem = get('/api/list?fruit='+fruit+'&page_size=20')['items'][0]['stem']
        q = urllib.parse.urlencode({'fruit': fruit, 'stem': stem})
        assert get('/api/item?'+q)['stem'] == stem
        assert get('/api/boxes?'+q)['stem'] == stem
        code, body = request('/img?'+q)
        assert code == 200 and body.startswith(b'\x89PNG\r\n\x1a\n')
        out['photos'].append({'fruit': fruit, 'stem': stem, 'image_http': code, 'png': True})
    code, html = request('/')
    assert code == 200 and b'id="view-exp"' in html
    out['export_guide'] = True
    if not args.read_only:
        # 전환 직후 다른 사람이 접속하기 전에만 쓴다. 원본 파일을 먼저 보관한다.
        fruit = out['photos'][0]['fruit']; stem = out['photos'][0]['stem']
        box = root/'data'/fruit/'boxes'/(stem+'.json'); status = root/'data'/fruit/'status.json'
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup = root/'_archive'/('smoke_'+stamp); backup.mkdir(parents=True)
        before = {p: p.read_bytes() if p.exists() else None for p in (box, status)}
        for p, content in before.items():
            if content is not None:
                (backup/p.name).write_bytes(content)
        original = json.loads(before[status]) if before[status] else {}
        base = {'fruit': fruit, 'stem': stem, 'by': '전환점검'}
        try:
            code, body = request('/api/boxes', {**base, 'boxes': [{'xyxy': [2, 2, 20, 20]}]})
            assert code == 200 and json.loads(body)['n_boxes'] == 1
            code, body = request('/api/boxes', {**base, 'boxes': []})
            assert code == 200 and json.loads(body)['removed']
            out['save_and_revert'] = True
        finally:
            # 상자와 판정의 원래 바이트를 복구한다. 다른 사진 판정은 덮어쓰지 않는다.
            current = json.loads(status.read_bytes()) if status.exists() else {}
            untouched = {k: v for k, v in current.items() if k != stem}
            prior_others = {k: v for k, v in original.items() if k != stem}
            if untouched != prior_others:
                if stem in original:
                    current[stem] = original[stem]
                else:
                    current.pop(stem, None)
                before[status] = json.dumps(current, ensure_ascii=False, indent=1).encode()
                out['concurrent_other_photos_preserved'] = True
            for p, content in before.items():
                if content is None:
                    if p.exists():
                        shutil.move(str(p), str(backup/('generated_'+p.name)))
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    temp = p.with_name(p.name+'.smoke_restore_'+stamp)
                    temp.write_bytes(content); os.replace(temp, p)
            assert all((p.read_bytes() if p.exists() else None) == content for p, content in before.items())
        out['restored_bytes'] = True
        out['backup'] = str(backup)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == '__main__':
    main()
