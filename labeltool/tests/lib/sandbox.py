# -*- coding: utf-8 -*-
"""tests/ 공용 도구 — 모래상자 만들기 · 서버 띄우기 · API 부르기 · 단정.
작성: 2026-09-19

흩어져 있던 사이클 시험들이 각자 가지고 있던 `lib_c4.py`·`lib_cnt4.py`·`lib_cnt4b.py` 를
**한 군데로 모은 것**이다. 경로·포트·비밀번호 하드코딩은 전부 이 파일에만 있다.
원본 위치는 `tests/ORIGIN.md` 에 적어 두었다.

지키는 것
  · 쓰기는 `tests/_sandbox/` 안에서만. 공용 `T/data`·`T/exports`·데이터셋·팀원 폴더는 **읽기만**.
  · 서버는 **빈 포트**를 스스로 찾아 127.0.0.1 로만 띄우고, 끝나면 **내가 띄운 PID 만** 끈다.
    실서버 5111 · 교수님 5100·5101·5105 · 주피터 5101 에는 붙지도 끄지도 않는다.
  · `pkill` 을 쓰지 않는다.
"""
import hashlib
import http.cookiejar
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ───────────────────────── 경로 (하드코딩은 여기만) ─────────────────────────
LIB_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(LIB_DIR)                      # …/260916_라벨링툴/tests
T = os.path.dirname(TESTS)                            # …/260916_라벨링툴
ARCHIVE = os.path.join(T, "_archive", "backups_260920")
SB_ROOT = os.path.join(TESTS, "_sandbox")
OUT_DIR = os.path.join(TESTS, "_out")
FIX = os.path.join(TESTS, "fixtures")
HERE = OUT_DIR                                        # 베껴 온 시험들이 결과 json 을 쓰는 곳

PY = os.environ.get("TESTS_PY", "/home/kds0206/.conda/envs/kwak/bin/python")
NODE = os.environ.get("TESTS_NODE", "/home/kds0206/.local/node22/bin/node")

# 원본 사진·마스크 폴더(읽기 전용). 실서버가 보고 있는 것과 같은 기본값.
DR = (os.environ.get("TESTS_DATA_ROOT", "").strip()
      or "/data/project/2026summer/kds0206/datasets_reviewed_260916")
DR_DEFAULT = "/data/project/2026summer/kds0206/datasets_resized_2mp"

FRUITS = ["peach", "grape", "apple", "blueberry"]
FKO = {"peach": "복숭아", "grape": "포도", "apple": "사과", "blueberry": "블루베리"}
PW = os.environ.get("TESTS_PW", "tests260920")
SHOTS = os.path.expanduser(os.environ.get("TESTS_SHOTS", "~/ff_shots/tests_260920"))

# 베껴 온 시험이 «이 사이클 직전 서버» 를 재현할 때 되돌리는 파일들
OLDFILES = [("app", "server.py"), ("app", "boxes.py"), ("app", "instances.py"),
            ("export", "export_dataset.py")]
OLD_TAG = os.environ.get("TESTS_OLD_TAG", "_backup_260918_c4_")

for _d in (SB_ROOT, OUT_DIR, FIX, SHOTS):
    os.makedirs(_d, exist_ok=True)
sys.path.insert(0, os.path.join(T, "scripts"))         # ff.py


# ───────────────────────── 빈 포트 ─────────────────────────
KEEP_OUT = {5100, 5101, 5102, 5104, 5105, 5111}        # 남의 것 — 절대 쓰지 않는다


def used_ports():
    try:
        out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        out = ""
    got = set()
    for ln in out.splitlines()[1:]:
        for tok in ln.split():
            if ":" in tok:
                tail = tok.rsplit(":", 1)[-1]
                if tail.isdigit():
                    got.add(int(tail))
    return got


def free_port(start=5401, span=120):
    """빈 포트 하나. 남의 포트(KEEP_OUT)는 건너뛴다."""
    busy = used_ports() | KEEP_OUT
    for p in range(start, start + span):
        if p not in busy:
            return p
    raise SystemExit("빈 포트를 못 찾았습니다(%d~%d)." % (start, start + span))


PORT = free_port(5401)
OLD_PORT = free_port(PORT + 1)
BASE = "http://127.0.0.1:%d" % PORT
SB = os.path.join(SB_ROOT, "sb_main")
SB_OLD = os.path.join(SB_ROOT, "sb_old")
SB_REG = os.path.join(SB_ROOT, "sb_reg")


# ───────────────────────── 단정 ─────────────────────────
OK = []
BAD = []
WARN = []


def chk(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ((" | " + str(detail)) if detail else ""),
          flush=True)
    return bool(cond)


def warn(name, detail=""):
    WARN.append(name)
    print("  warn " + name + ((" | " + str(detail)) if detail else ""), flush=True)


def summary(tag):
    print("\n[%s] 통과 %d / 실패 %d / 경고 %d" % (tag, len(OK), len(BAD), len(WARN)), flush=True)
    if BAD:
        print("  실패 목록: " + " / ".join(BAD), flush=True)
    if WARN:
        print("  경고 목록: " + " / ".join(WARN), flush=True)
    return len(BAD)


# ───────────────────────── 모래상자 ─────────────────────────
def backup_src(sub, name):
    """`_backup_*` 파일을 찾는다 — 먼저 원래 자리, 없으면 `_archive/backups_260920/`.
    (2026-09-19 22:00 에 백업 205개를 아카이브로 옮겼기 때문에 두 군데를 다 본다.)"""
    a = os.path.join(T, sub, name)
    if os.path.exists(a):
        return a
    b = os.path.join(ARCHIVE, sub, name)
    if os.path.exists(b):
        return b
    return None


def sync(sb=None, old=False, data=True, src=None):
    """`T/app`·`T/export`·`T/data` 를 모래상자로 **실복사**(하드링크 0).
    old=True 면 서버 파이썬 4개만 `OLD_TAG` 판으로 되돌린다(정적 파일은 새 판).

    src= 로 **다른 툴 폴더**를 줄 수 있다(예: `_archive/pre_refactor_260920`) — 그러면
    «되돌린 판으로 전체 시험» 이 한 줄이 된다(2026-09-19 2차 검수 §6-3 · §10-5).
    자료(`data/`)는 늘 지금 것(`T/data`)을 쓴다 — 옛 코드에 옛 자료를 붙이려는 것이 아니라
    «옛 코드가 지금 자료로 같은 답을 내나» 를 보는 것이다.
    """
    sb = sb or SB
    src = src or T
    for sub in ("app", "export"):
        os.makedirs(os.path.join(sb, sub), exist_ok=True)
    subprocess.run(["rsync", "-a", "--delete", "--exclude", "logs", "--exclude", "cache",
                    "--exclude", "__pycache__", src + "/app/", sb + "/app/"], check=True)
    subprocess.run(["rsync", "-a", "--delete", "--exclude", "__pycache__",
                    src + "/export/", sb + "/export/"], check=True)
    if data:
        os.makedirs(os.path.join(sb, "data"), exist_ok=True)
        subprocess.run(["rsync", "-a", "--delete", T + "/data/", sb + "/data/"], check=True)
    if old:
        for d, fn in OLDFILES:
            src = backup_src(d, OLD_TAG + fn)
            if src:
                shutil.copy(src, os.path.join(sb, d, fn))
    os.makedirs(os.path.join(sb, "app", "logs"), exist_ok=True)
    return sb


def reset_status(sb=None, fruits=None):
    """**내** 모래상자의 status/duplicates 만 공용 `T/data` 것(=지금 실제 자료)으로 되돌린다."""
    sb = sb or SB
    for f in (fruits or FRUITS):
        d = os.path.join(sb, "data", f)
        os.makedirs(d, exist_ok=True)
        for fn in ("status.json", "duplicates.json"):
            p = os.path.join(T, "data", f, fn)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(d, fn))


def clear_exports(sb=None):
    d = os.path.join(sb or SB, "exports")
    if os.path.isdir(d):
        shutil.rmtree(d)


def sample_dataset(stems_by_fruit, out=None):
    """고정 표본만 담은 **작은 원본 폴더**를 만든다 → `<out>/<fruit>/{images,masks}/<stem>.png`.
    네 과일 모두 만든다(그래야 `dupes.dataset_for` 가 이 폴더 하나만 본다).
    복사는 실복사 — 하드링크·심볼릭 링크를 쓰지 않는다(원본을 건드릴 위험을 0 으로)."""
    out = out or os.path.join(SB_ROOT, "dataset_sample")
    if os.path.isdir(out):
        shutil.rmtree(out)
    for fruit, stems in stems_by_fruit.items():
        src = source_root(fruit)
        for sub in ("images", "masks"):
            os.makedirs(os.path.join(out, fruit, sub), exist_ok=True)
            for s in stems:
                p = os.path.join(src, fruit, sub, s + ".png")
                if os.path.exists(p):
                    shutil.copy2(p, os.path.join(out, fruit, sub, s + ".png"))
    return out


def source_root(fruit):
    """그 과일의 원본 폴더 — 서버(`dupes.dataset_for`)와 **같은 규칙**."""
    if os.path.isdir(os.path.join(DR, fruit, "images")):
        return DR
    return DR_DEFAULT


def images_of(fruit, root=None):
    d = os.path.join(root or source_root(fruit), fruit, "images")
    return sorted(n[:-4] for n in os.listdir(d) if n.lower().endswith(".png"))


def status_of(fruit, sb=None):
    p = os.path.join(sb or SB, "data", fruit, "status.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


# ───────────────────────── 서버 ─────────────────────────
def start(port=None, sb=None, pw=None, log=None, data_root=None):
    """모래상자 서버를 띄운다. 포트가 이미 쓰이고 있으면 **멈춘다**(남의 것일 수 있다)."""
    port = port or PORT
    sb = sb or SB
    pw = PW if pw is None else pw
    if port in KEEP_OUT:
        raise SystemExit("포트 %d 는 남의 것입니다 — 띄우지 않습니다." % port)
    if port in used_ports():
        raise SystemExit("포트 %d 가 이미 쓰이고 있습니다 — 남의 서버일 수 있으니 멈춥니다." % port)
    os.makedirs(os.path.join(sb, "app", "logs"), exist_ok=True)
    log = log or os.path.join(sb, "app", "logs", "server%d.log" % port)
    env = dict(os.environ, PORT=str(port), LABELTOOL_DATA_ROOT=(data_root or DR),
               LABELTOOL_PASSWORD=pw, HOST="127.0.0.1", PYTHONDONTWRITEBYTECODE="1")
    f = open(log, "ab")
    p = subprocess.Popen([PY, "-u", "server.py"], cwd=os.path.join(sb, "app"),
                         stdout=f, stderr=f, env=env)
    for _ in range(180):
        if p.poll() is not None:
            raise SystemExit("모래상자 서버가 바로 죽었습니다 — 로그: %s" % log)
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/login" % port, timeout=5).read()
            break
        except Exception:
            time.sleep(0.5)
    print("[모래상자] 포트 %d · PID %d · %s" % (port, p.pid, log), flush=True)
    return p


def stop(p):
    """내가 띄운 PID 만 끈다(남의 5100·5101·5105·5111 은 절대 건드리지 않는다)."""
    if p is None:
        return
    p.terminate()
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    print("[모래상자] PID %d 껐습니다 (내 PID 만)" % p.pid, flush=True)


class Api:
    def __init__(self, base=None, pw=None):
        self.base = base or BASE
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.login(PW if pw is None else pw)

    def login(self, pw):
        d = urllib.parse.urlencode({"password": pw}).encode()
        try:
            self.op.open(self.base + "/login", d, timeout=30).read()
        except urllib.error.HTTPError as e:
            e.read()

    def get(self, path):
        with self.op.open(self.base + path, timeout=900) as f:
            return json.loads(f.read().decode())

    def get_raw(self, path):
        try:
            with self.op.open(self.base + path, timeout=900) as f:
                return f.status, f.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")

    def get_bytes(self, path):
        try:
            with self.op.open(self.base + path, timeout=900) as f:
                return f.status, f.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def get2(self, path):
        c, raw = self.get_raw(path)
        try:
            return c, json.loads(raw)
        except Exception:
            return c, {"_raw": raw[:300]}

    def post(self, path, obj):
        r = urllib.request.Request(self.base + path, data=json.dumps(obj).encode(),
                                   headers={"Content-Type": "application/json"}, method="POST")
        try:
            with self.op.open(r, timeout=900) as f:
                return f.status, json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, {"_raw": raw[:400]}


# ───────────────────────── 지문 ─────────────────────────
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def md5_tree(root, exts=None):
    out = {}
    for d, _, fns in os.walk(root):
        for fn in sorted(fns):
            p = os.path.join(d, fn)
            rel = os.path.relpath(p, root)
            if exts and not fn.lower().endswith(exts):
                continue
            out[rel] = ("->" + os.path.realpath(p)) if os.path.islink(p) else md5(p)
    return out


def sha256_tree(root):
    out = {}
    for d, _, fns in os.walk(root):
        for fn in sorted(fns):
            p = os.path.join(d, fn)
            out[os.path.relpath(p, root)] = sha256(p)
    return out


def manifest(out_dir):
    import csv
    p = os.path.join(out_dir, "manifest.csv")
    if not os.path.exists(p):
        return [], []
    rows = list(csv.reader(open(p, encoding="utf-8")))
    return rows[0], rows[1:]


def dataset_for(fruit, sb=None):
    """서버와 같은 규칙으로 원본 폴더를 고른다(베껴 온 시험이 부른다)."""
    return source_root(fruit)


# ───────────────────────── 진짜 브라우저 (scripts/ff.py) ─────────────────────────
def browser(w=1366, h=768, base=None, pw=None, skip_tour=True, login=True):
    os.environ["LABELTOOL_URL"] = base or BASE
    import importlib
    import ff
    importlib.reload(ff)
    ff.SHOTS = SHOTS
    b = ff.Browser(w=w, h=h)
    if login:
        b.go("/login")
        b.type("input[name=password]", PW if pw is None else pw)
        b.click("button, input[type=submit]")
        b.go("/old")          # 0923: 첫 화면(/)은 새 그림판 — 옛 툴 시험은 /old 에서
        if not b.js("return !!document.querySelector('#fruit')"):
            b.go("/")         # /old 가 없는 옛 판 코드(보관본 비교 시험)는 / 가 옛 툴이다
        b.wait("return !!document.querySelector('#fruit option')")
        if skip_tour:
            close_tour(b)
    return b


def close_tour(b):
    time.sleep(0.6)
    b.js("const t=document.querySelector('#tour');"
         "if(t && !t.classList.contains('hidden')) document.querySelector('#tour-x').click();")
    time.sleep(0.3)
    return b.js("return document.querySelector('#tour').classList.contains('hidden')")


def ev(b, expr):
    return json.loads(b.js("return JSON.stringify(window.eval(arguments[0]))", "(" + expr + ")"))


def run(b, stmt):
    b.js("window.eval(arguments[0])", stmt)


def eat_alert(b):
    try:
        t = b.alert_text()
    except Exception:
        return None
    try:
        b.alert_ok()
    except Exception:
        pass
    return t


COUNT_TEXT = r"""
(function(root){
  const el = document.querySelector(root);
  if (!el) return null;
  let n = 0, items = [];
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode: function(t){
      const s = (t.nodeValue||'').replace(/\s+/g,' ').trim();
      if (!s) return NodeFilter.FILTER_REJECT;
      let p = t.parentElement;
      if (!p) return NodeFilter.FILTER_REJECT;
      for (let q = p; q && q !== document.body; q = q.parentElement) {
        const cs = getComputedStyle(q);
        if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return NodeFilter.FILTER_REJECT;
        if (q.tagName === 'DETAILS' && !q.open) {
          let inSummary = false;
          for (let r = p; r && r !== q; r = r.parentElement) if (r.tagName === 'SUMMARY') inSummary = true;
          if (!inSummary) return NodeFilter.FILTER_REJECT;
        }
      }
      const r = p.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  let t;
  while ((t = w.nextNode())) {
    const s = t.nodeValue.replace(/\s+/g,' ').trim();
    n += s.length;
    items.push([ (t.parentElement.id || t.parentElement.className || t.parentElement.tagName), s.length, s.slice(0,40) ]);
  }
  items.sort(function(a,b){return b[1]-a[1];});
  return {chars: n, nodes: items.length, top: items.slice(0, 25)};
})(arguments[0])
"""


def count_text(b, root="#view-edit"):
    return b.js("return " + COUNT_TEXT.strip(), root)


# `lib_cnt4` 처럼 «M.L» 로 자기 자신을 가리키던 것을 그대로 받아 준다
L = sys.modules[__name__]


def grape_seeded():
    """`app/instances.py` 의 `SEED_DIRS` 에 **포도가 켜져 있나**.

    포도 번호본(CERTH 정답 송이)은 «교수님 확인 8번» 을 기다리며 주석으로 꺼 두었다
    (2026-09-19 «개수 세기» 사이클4 2차). 켜지면 포도 초벌 출처가 `cc4` → `certh_gt` 로 바뀌고
    ③ 번호 단추도 열린다. 시험이 그 기대값을 **손으로 적어 두면 늘 낡는다** → 코드에서 읽는다.
    """
    import re
    # 2026-09-20 구조 사이클 2: `SEED_DIRS` 가 `app/api/instances.py` 로 옮겨 갔다.
    #   두 자리를 다 보므로 옛 판(한 파일이던 때)에서도 돈다.
    src = ""
    for rel in (("app", "api", "instances.py"), ("app", "instances.py")):
        p = os.path.join(T, *rel)
        if os.path.exists(p):
            src = io.open(p, encoding="utf-8").read()
            if "SEED_DIRS" in src:
                break
    m = re.search(r"^SEED_DIRS\s*=\s*\{(.*?)\}", src, re.S | re.M)
    return bool(m and '"grape"' in m.group(1))
