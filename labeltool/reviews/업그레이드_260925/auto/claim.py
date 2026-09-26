# 체크리스트 항목을 레인끼리 겹치지 않게 잡고·놓고·끝내는 도우미 + 한도 리셋 시각 읽기
import fcntl, re, sys, time
from datetime import datetime, timedelta
from pathlib import Path

C = Path(__file__).resolve().parent.parent
CK = C / 'checklist.md'
LOCK = C / 'auto' / 'checklist.lock'
ITEM = re.compile(r'^- \[( |x|~\w+)\] (\S+) (\S+) ')


def items(lines):
    for i, l in enumerate(lines):
        m = ITEM.match(l)
        if m:
            after = re.search(r'\{after:([^}]*)\}', l)
            yield i, m.group(1), m.group(2), m.group(3), (after.group(1).split(',') if after else [])


def locked(fn):
    with open(LOCK, 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        lines = CK.read_text('utf8').split('\n')
        out, changed = fn(lines)
        if changed:
            CK.write_text('\n'.join(lines), 'utf8')
        return out


def claim(lane, tags):
    def fn(lines):
        its = list(items(lines))
        open_tags = {t for _, s, t, _, _ in its if s != 'x'}
        for tag in tags:
            for i, s, t, iid, after in its:
                if s != ' ' or t != tag:
                    continue
                # 자기 태그는 «자기 말고 다른 항목» 이 열려 있는지로 본다
                blocked = False
                for a in after:
                    a = a.strip()
                    if a == t:
                        blocked = any(s2 != 'x' and t2 == a and i2 != i for i2, s2, t2, _, _ in its)
                    elif a in open_tags:
                        blocked = True
                    if blocked:
                        break
                if blocked:
                    continue
                lines[i] = lines[i].replace('- [ ]', '- [~%s]' % lane, 1)
                return '%s\t%s' % (iid, lines[i]), True
        return '', False
    return locked(fn)


def setstate(lane, iid, new):
    def fn(lines):
        for i, s, t, x, _ in items(lines):
            if x == iid and s == '~' + lane:
                lines[i] = lines[i].replace('- [%s]' % s, '- [%s]' % new, 1)
                return 'ok', True
        return '', False
    return locked(fn)


def state(iid):
    for _, s, _, x, _ in items(CK.read_text('utf8').split('\n')):
        if x == iid:
            return s
    return '?'


def remaining():
    return sum(1 for _, s, _, _, _ in items(CK.read_text('utf8').split('\n')) if s != 'x')


def reset_epoch(logfile):
    """«resets 5:20am» · «resets at 5pm» 같은 문구에서 다음 리셋 시각(초). 없으면 0."""
    txt = Path(logfile).read_text('utf8', 'replace')
    m = re.search(r'resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*([ap]m)', txt, re.I)
    if not m:
        return 0
    h, mi, ap = int(m.group(1)) % 12, int(m.group(2) or 0), m.group(3).lower()
    h += 12 if ap == 'pm' else 0
    now = datetime.now()
    t = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    if t <= now:
        t += timedelta(days=1)
    return int(t.timestamp()) + 120


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'claim':
        print(claim(sys.argv[2], sys.argv[3].split(',')))
    elif cmd == 'release':
        print(setstate(sys.argv[2], sys.argv[3], ' '))
    elif cmd == 'done':
        print(setstate(sys.argv[2], sys.argv[3], 'x'))
    elif cmd == 'state':
        print(state(sys.argv[2]))
    elif cmd == 'remaining':
        print(remaining())
    elif cmd == 'reset':
        print(reset_epoch(sys.argv[2]))
