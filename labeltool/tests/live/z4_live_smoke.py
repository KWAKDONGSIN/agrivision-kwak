# -*- coding: utf-8 -*-
"""z4 — **실서버 5111 이 지금 디스크의 정적 파일을 그대로 주고 있는가**(읽기만 한다).
작성: 2026-09-21 (편의·안정성 사이클 · Z4)

왜 필요한가
  이 사이클은 «정적 파일(html·css·js)만 고치면 실서버를 다시 띄울 필요가 없다» 를 스물몇 라운드
  내내 전제로 삼았다. 전제는 시험이 아니다 — 여기서 **실서버가 실제로 주는 바이트**를 받아
  디스크와 대어 본다. 서버는 2026-09-21 04:32 에 떴고 이 사이클이 고친 파일들은 그 **뒤에**
  바뀌었으므로, 준 바이트가 지금 디스크와 같으면 «다시 안 띄워도 반영된다» 가 실측으로 선다.

지키는 것 (이 파일은 실서버에 붙는 **유일한** 시험이다)
  · **GET 만 보낸다.** `get()` 말고는 요청을 보내는 길이 없고, POST 는 함수 자체가 없다.
    로그인도 **POST 하지 않는다** — `app/run.sh:23` 이 읽는 `~/.council/labeltool.env` 로
    `core/auth.py:42` 와 **같은 방법으로 쿠키를 직접 서명**한다(틀린 비밀번호를 한 번도 안 넣으므로
    `login_rate_ok()` 의 시도 제한 카운터를 건드리지 않는다).
  · 남의 프로세스를 **안 건드린다.** 5111 을 끄지도 다시 띄우지도 않는다 —
    시험 전후로 PID 와 시작 시각이 같은지 스스로 확인한다.
  · `/thumb` 은 **캐시에 이미 있는 사진**만 부른다(없는 것을 부르면 서버가 jpg 를 새로 만든다
    = 쓰기다 · `api/photos.py:362`). 그래도 «아무것도 안 썼다» 를 `data/`·`app/cache/`
    지문으로 전후 대조한다.

묶음에 안 들어간다
  `tests/run_all.sh` 의 묶음은 `unit/u*.py`·`sim/*.js`·`api/` 이름표·`browser/b*.py` 다.
  이 파일은 `tests/live/` 에 혼자 있으므로 어느 글롭에도 안 걸린다 — **실서버가 떠 있을 때만**
  뜻이 있는 시험이라 회귀에 섞이면 안 된다. 돌리는 법:
      /home/kds0206/.conda/envs/kwak/bin/python -u tests/live/z4_live_smoke.py
"""
import hashlib
import hmac
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import sandbox as L                                                        # noqa: E402

BASE = "http://127.0.0.1:5111"
PORT = 5111
STATIC = os.path.join(L.T, "app", "static")
DATA = os.path.join(L.T, "data")
CACHE = os.path.join(L.T, "app", "cache")
PWFILE = os.path.expanduser(os.environ.get("LABELTOOL_ENV_FILE", "~/.council/labeltool.env"))

REQS = []                       # 보낸 요청 기록 — 끝에서 «전부 GET 이었나» 를 센다


# ───────────────────────── 실서버 찾기 (끄지 않는다 · 보기만) ─────────────────────────
def server_pid():
    """5111 을 듣고 있는 PID. `ss -ltnp` 한 줄에서 읽는다(없으면 None)."""
    try:
        out = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return None
    for ln in out.splitlines():
        if (":%d " % PORT) in ln or ln.rstrip().endswith(":%d" % PORT) or (":%d\t" % PORT) in ln:
            m = re.search(r"pid=(\d+)", ln)
            if m:
                return int(m.group(1))
        m2 = re.search(r"[:\s]%d\s" % PORT, ln)
        if m2:
            m = re.search(r"pid=(\d+)", ln)
            if m:
                return int(m.group(1))
    return None


def proc_started(pid):
    """그 PID 가 언제 떴나 — `/proc/<pid>` 폴더의 만든 시각(초)."""
    try:
        return os.stat("/proc/%d" % pid).st_ctime
    except Exception:
        return None


# ───────────────────────── 쿠키 (POST 하지 않는다) ─────────────────────────
def read_password():
    """`~/.council/labeltool.env` 의 `LABELTOOL_PASSWORD=...` 한 줄. **값은 절대 찍지 않는다.**"""
    if not os.path.exists(PWFILE):
        return ""
    for ln in io.open(PWFILE, encoding="utf-8"):
        ln = ln.strip()
        if ln.startswith("export "):
            ln = ln[7:]
        if ln.startswith("LABELTOOL_PASSWORD="):
            v = ln.split("=", 1)[1].strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            return v
    return ""


def sign_cookie(pw):
    """`core/auth.py:42 make_auth_cookie()` 와 **같은 서명**. 서버에 묻지 않고 여기서 만든다."""
    exp = int(time.time()) + 30 * 86400
    sig = hmac.new(pw.encode("utf-8"), ("labeltool|%d" % exp).encode("utf-8"),
                   hashlib.sha256).hexdigest()
    return "%d.%s" % (exp, sig)


# ───────────────────────── GET (이 파일이 요청을 보내는 유일한 길) ─────────────────────────
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def get(path, cookie=None, headers=None, timeout=60):
    """GET 한 번 → (status, headers, body). 302·304·401·404 도 예외로 안 만들고 그대로 돌려준다."""
    h = dict(headers or {})
    if cookie:
        h["Cookie"] = "labeltool_auth=" + cookie
    REQS.append(("GET", path))
    # 한글 이름 파일(`진행상황.html`·`시연.html`)이 있어 주소를 그대로 보내면 ascii 로 못 담는다.
    # `%` 를 safe 에 넣어 이미 escape 된 주소를 두 번 감싸지 않는다.
    req = urllib.request.Request(BASE + urllib.parse.quote(path, safe="/?&=%:+~"),
                                 headers=h, method="GET")
    try:
        r = _OPENER.open(req, timeout=timeout)
        return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


# ───────────────────────── 쓰기 자리 지문 ─────────────────────────
def fingerprint(root):
    """폴더 하나의 «파일 수 · 합계 바이트 · 가장 늦은 mtime». 내용은 안 읽는다(빠르다)."""
    n = 0
    size = 0
    newest = 0.0
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            try:
                st = os.stat(os.path.join(dirpath, f))
            except OSError:
                continue
            n += 1
            size += st.st_size
            newest = max(newest, st.st_mtime)
    return (n, size, round(newest, 3))


# ───────────────────────── 정적 파일 목록 ─────────────────────────
def static_files():
    """실서버가 주어야 할 정적 파일 전부 — `_backup_*` 는 뺀다(옛 사본이라 화면이 안 쓴다)."""
    out = []
    for dirpath, _dirs, files in os.walk(STATIC):
        for f in sorted(files):
            if f.startswith("_backup_"):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, STATIC).replace(os.sep, "/")
            if rel.startswith("_backup_"):
                continue
            out.append(rel)
    return sorted(out)


def disk_bytes(rel):
    return io.open(os.path.join(STATIC, rel), "rb").read()


# 이 사이클이 남긴 손자국 — 실서버가 주는 **바이트 안에** 있어야 한다
MARKS = [
    ("index.html", "js/backup.js", "S5 임시 백업"),
    ("index.html", "js/dirtymark.js", "U1 저장 안 됨 «*»"),
    ("index.html", 'id="zoompct"', "U2 배율 %"),
    ("index.html", "data-key-table", "U7 단축키 한 장 표"),
    ("style.css", "--chrome", "G1·G2 무채색 토큰"),
    ("style.css", ":focus-visible", "G4 키보드 띠"),
    ("style.css", "#zoompct", "U2 배율 칸 규칙"),
    ("style.css", "min-width", "G5 숫자 칸 자리 잡기"),
    ("mobile.css", "var(--chrome)", "G6 휴대폰 아래 단추 줄"),
    ("js/api.js", "lockWhile", "S6 이중 저장 막기"),
    ("js/api.js", "catch", "S1 네트워크 실패 잡기"),
    ("js/backup.js", "backupNow", "S5"),
    ("js/dirtymark.js", "dirty", "U1"),
    ("js/keys.js", "boxRedo", "U3 상자 다시하기"),
    ("js/keys.js", "F1", "U7"),
    ("js/keys.js", "Backquote", "U9 «원본만» 잠깐 보기"),
    ("js/boxes.js", "drawBoxGuide", "U10 십자 안내선"),
    ("js/view.js", "cursorFor", "U5 도구별 커서"),
    ("js/view.js", "showZoomPct", "U2"),
    ("js/mask.js", "sizeTool", "U8 도구마다 붓 크기"),
    ("js/main.js", "dblclick", "U4 더블클릭 = 맞춤"),
]


def main():
    # ── §0 준비 ────────────────────────────────────────────────────────
    pid0 = server_pid()
    L.chk("실서버 5111 을 듣는 프로세스가 있다", pid0 is not None, "PID %s" % pid0)
    if pid0 is None:
        return L.summary("z4_live_smoke")
    t0 = proc_started(pid0)
    up = (time.time() - t0) / 3600.0 if t0 else -1
    L.chk("그 프로세스가 언제 떴는지 읽었다", t0 is not None,
          "PID %d · %s · %.2f시간째" % (pid0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)), up))

    pw = read_password()
    L.chk("비밀번호 파일을 읽었다(값은 안 찍는다)", bool(pw), "%s · %d글자" % (PWFILE, len(pw)))
    ck = sign_cookie(pw) if pw else None

    # 이 쿠키가 실제로 통하는지 **먼저** 못박는다. 안 통하면 아래 ②③④ 는 전부 302(빈 몸통)를 받고
    # «파일이 디스크와 다르다» 처럼 엉뚱한 말을 한다 — 실제로 처음 돌렸을 때 그렇게 읽혔다.
    stc, _hc, _bc = get("/api/fruits", ck)
    L.chk("⓪ 직접 서명한 쿠키가 받아들여진다(아래 ②③④ 가 문지기에 막히지 않는다)", stc == 200,
          "GET /api/fruits status=%s" % stc)

    fp_data0 = fingerprint(DATA)
    fp_cache0 = fingerprint(CACHE)

    # ── §1 살아 있는가 ─────────────────────────────────────────────────
    st, hd, body = get("/api/health")
    L.chk("① /api/health 가 200 이다", st == 200, "status=%s" % st)
    try:
        j = json.loads(body.decode("utf-8"))
    except Exception:
        j = {}
    L.chk("① health 가 ok:true 를 말한다", j.get("ok") is True, str(j)[:120])
    ht = j.get("time") or ""
    L.chk("① health 시각이 지금과 5분 안이다",
          abs(time.mktime(time.strptime(ht, "%Y-%m-%d %H:%M:%S")) - time.time()) < 300 if ht else False,
          "서버 %s · 지금 %s" % (ht, time.strftime("%Y-%m-%d %H:%M:%S")))
    L.chk("① 로그인 없이도 health 는 열려 있다(S3 감시가 도는 까닭)", st == 200,
          "core/auth.py:29 OPEN_PATHS")

    # ── §2 재시작 없이 반영되는가 ───────────────────────────────────────
    rels = static_files()
    L.chk("② 실서버가 주어야 할 정적 파일을 셌다", len(rels) > 20, "%d개(_backup_* 제외)" % len(rels))

    newer = [r for r in rels
             if t0 and os.path.getmtime(os.path.join(STATIC, r)) > t0]
    L.chk("② 서버가 뜬 **뒤에** 바뀐 정적 파일이 있다(있어야 이 시험이 뜻이 있다)",
          len(newer) > 0, "%d개 · 예: %s" % (len(newer), ", ".join(sorted(newer)[:4])))

    same = 0
    diff = []
    for rel in rels:
        want = disk_bytes(rel)
        # 쿠키를 반드시 준다 — `/static/*` 도 문지기 뒤에 있어(`core/auth.py`) 쿠키 없이 부르면
        # 302 로 `/login` 에 보내고 **빈 몸통**이 온다. 그것을 «파일이 다르다» 로 읽으면 안 된다.
        # (쿠키 **없이** 무엇이 막히는지는 §5 가 따로 센다.)
        st, hd, got = get("/static/" + rel, ck)
        if st != 200:
            diff.append("%s (status=%s)" % (rel, st))
            continue
        if got != want:
            # 자동 라운드가 돌면서 그 사이에 파일이 바뀌었을 수 있다 → 한 번만 다시 읽어 댄다
            want = disk_bytes(rel)
            if got != want:
                diff.append("%s (%d != %d바이트)" % (rel, len(got), len(want)))
                continue
        same += 1
    L.chk("② 실서버가 주는 정적 파일이 **디스크와 한 바이트도 안 다르다**",
          not diff, "%d/%d 같음%s" % (same, len(rels), ("" if not diff else " · 다름: " + "; ".join(diff[:6]))))

    st, hd, got = get("/", ck)
    L.chk("② 첫 화면 `/` 도 지금 index.html 그대로다", got == disk_bytes("index.html"),
          "%d바이트 · 디스크 %d바이트" % (len(got), len(disk_bytes("index.html"))))
    L.chk("② 그 index.html 은 서버가 뜬 뒤에 바뀐 파일이다(= 재시작 없이 반영됐다)",
          bool(t0) and os.path.getmtime(os.path.join(STATIC, "index.html")) > t0,
          "서버 %s · index.html %s" % (
              time.strftime("%H:%M:%S", time.localtime(t0)),
              time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(os.path.join(STATIC, "index.html"))))))

    st, hd, _ = get("/static/js/backup.js", ck)
    cc = (hd.get("Cache-Control") or "")
    L.chk("② 정적 파일에 `Cache-Control: no-cache` 가 붙는다(브라우저가 낡은 사본을 안 쓴다)",
          "no-cache" in cc, "Cache-Control: %s" % cc)
    etag = hd.get("ETag")
    lm = hd.get("Last-Modified")
    L.chk("② ETag·Last-Modified 가 있다(새로고침이 싸다)", bool(etag) and bool(lm),
          "ETag=%s · Last-Modified=%s" % (etag, lm))
    sz = os.path.getsize(os.path.join(STATIC, "js", "backup.js"))
    L.chk("② ETag 가 지금 파일 크기를 말한다", etag is not None and ("-%d-" % sz) in etag,
          "ETag=%s · 파일 %d바이트" % (etag, sz))
    st2, hd2, body2 = get("/static/js/backup.js", ck,
                          headers={"If-None-Match": etag} if etag else None)
    L.chk("② 같은 ETag 를 다시 물으면 304 를 준다(바뀌었을 때만 다시 받는다)",
          st2 == 304 and not body2, "status=%s · %d바이트" % (st2, len(body2)))

    # ── §3 이 사이클의 손자국이 실서버 바이트 안에 있다 ──────────────────
    cache = {}
    for rel, needle, why in MARKS:
        if rel not in cache:
            stx, _h, b = get("/static/" + rel, ck)
            cache[rel] = b.decode("utf-8", "replace") if stx == 200 else ""
        s = cache[rel]
        L.chk("③ 실서버 %s 안에 «%s» 가 있다 — %s" % (rel, needle, why), needle in s,
              "%d글자 중" % len(s))

    # ── §4 읽기 스모크 (GET 전용 주소) ──────────────────────────────────
    st, _h, b = get("/api/fruits", ck)
    j = json.loads(b.decode("utf-8")) if st == 200 else {}
    fr = j.get("fruits") or []
    L.chk("④ /api/fruits 200 · 과일 넷", st == 200 and len(fr) == 4,
          "status=%s · %s" % (st, [x.get("fruit") for x in fr]))
    L.chk("④ 서버가 보고 있는 원본 폴더를 말한다", bool(j.get("data_root")), j.get("data_root"))
    total = sum(x.get("n_images", 0) for x in fr)
    L.chk("④ 사진이 한 장 이상 보인다", total > 0,
          " · ".join("%s %d장" % (x["fruit"], x["n_images"]) for x in fr))

    fruit = next((x["fruit"] for x in fr if x.get("n_images")), "peach")
    st, _h, b = get("/api/list?fruit=%s&page=1&page_size=5" % fruit, ck)
    j = json.loads(b.decode("utf-8")) if st == 200 else {}
    items = j.get("items") or []
    L.chk("④ /api/list 200 · 목록이 온다", st == 200 and len(items) > 0,
          "status=%s · %s %d/%d장" % (st, fruit, len(items), j.get("total", 0)))
    stem = items[0]["stem"] if items else ""

    if stem:
        st, _h, b = get("/api/item?fruit=%s&stem=%s" % (fruit, stem), ck)
        j = json.loads(b.decode("utf-8")) if st == 200 else {}
        L.chk("④ /api/item 200 · 크기를 말한다", st == 200 and j.get("width", 0) > 0,
              "%s/%s %sx%s" % (fruit, stem, j.get("width"), j.get("height")))

        st, _h, b = get("/img?fruit=%s&stem=%s" % (fruit, stem), ck)
        L.chk("④ /img 200 · 진짜 PNG 다", st == 200 and b[:8] == b"\x89PNG\r\n\x1a\n",
              "status=%s · %d바이트" % (st, len(b)))

        st, _h, b = get("/mask?fruit=%s&stem=%s&layer=gt" % (fruit, stem), ck)
        L.chk("④ /mask?layer=gt 200 · 진짜 PNG 다", st == 200 and b[:8] == b"\x89PNG\r\n\x1a\n",
              "status=%s · %d바이트" % (st, len(b)))

        st, _h, b = get("/api/boxes?fruit=%s&stem=%s" % (fruit, stem), ck)
        L.chk("④ /api/boxes 200", st == 200, "status=%s · %d바이트" % (st, len(b)))

        st, _h, b = get("/api/instance_info?fruit=%s&stem=%s" % (fruit, stem), ck)
        L.chk("④ /api/instance_info 200", st == 200, "status=%s" % st)

    # /thumb — **캐시에 이미 있는 것만** 부른다(없는 것을 부르면 서버가 jpg 를 새로 만든다)
    cached = None
    for f in L.FRUITS:
        d = os.path.join(CACHE, "thumbs", f)
        if os.path.isdir(d):
            g = [x for x in sorted(os.listdir(d)) if x.endswith(".jpg")]
            if g:
                cached = (f, g[0][:-4])
                break
    if cached:
        st, _h, b = get("/thumb?fruit=%s&stem=%s" % cached, ck)
        L.chk("④ /thumb 200 · 진짜 JPEG 다(캐시에 이미 있는 사진만 불렀다)",
              st == 200 and b[:2] == b"\xff\xd8", "%s/%s · status=%s · %d바이트" % (cached[0], cached[1], st, len(b)))
    else:
        L.warn("④ 캐시에 썸네일이 하나도 없어 /thumb 은 안 불렀다(부르면 서버가 새로 만든다 = 쓰기)")

    for p, name in [("/api/stats", "현황"), ("/api/boxes_stats?fruit=%s" % fruit, "상자 집계"),
                    ("/api/instance_stats?fruit=%s" % fruit, "번호 집계"),
                    ("/api/export_list", "내보낸 목록")]:
        st, _h, b = get(p, ck)
        L.chk("④ %s (%s) 200" % (p.split("?")[0], name), st == 200, "status=%s · %d바이트" % (st, len(b)))

    st, _h, b = get("/box", ck)
    L.chk("④ /box (상자 전용 화면) 200 · 같은 index.html", st == 200 and b == disk_bytes("index.html"),
          "status=%s · %d바이트" % (st, len(b)))

    for doc in ("help.html", "how_to.html"):
        st, _h, b = get("/static/" + doc, ck)
        L.chk("④ 사용법 %s 200" % doc, st == 200, "status=%s · %d바이트" % (st, len(b)))

    figs = [r for r in rels if r.startswith("help/") and r.endswith(".png")]
    bad = []
    for r in figs:
        st, _h, b = get("/static/" + r, ck)
        if st != 200 or b[:8] != b"\x89PNG\r\n\x1a\n":
            bad.append("%s(status=%s)" % (r, st))
    L.chk("④ 사용법 그림 %d장이 전부 200 · 진짜 PNG 다" % len(figs), not bad,
          "끊긴 그림 %d개%s" % (len(bad), ("" if not bad else " · " + "; ".join(bad[:5]))))

    st, _h, _b = get("/static/없는파일_z4.js", ck)
    L.chk("④ 없는 정적 파일은 404 다(조용히 빈 것을 주지 않는다)", st == 404, "status=%s" % st)

    # ── §5 문지기가 살아 있다 (쿠키 없이 · 틀린 비밀번호를 안 넣는다) ─────
    st, hd, b = get("/api/list?fruit=%s" % fruit)
    L.chk("⑤ 쿠키 없이 /api/list 는 401 JSON 이다", st == 401, "status=%s · %s" % (st, b[:80]))
    st, hd, _b = get("/")
    loc = hd.get("Location") or ""
    L.chk("⑤ 쿠키 없이 / 는 302 로 /login 에 보낸다", st == 302 and loc.startswith("/login"),
          "status=%s · Location=%s" % (st, loc))
    st, _h, _b = get("/img?fruit=%s&stem=%s" % (fruit, stem or "x"))
    L.chk("⑤ 쿠키 없이 /img 도 401 이다", st == 401, "status=%s" % st)

    # ── §6 아무것도 안 썼다 · 아무 프로세스도 안 건드렸다 ────────────────
    methods = sorted(set(m for m, _p in REQS))
    L.chk("⑥ 보낸 요청이 **전부 GET** 이다(POST 를 한 번도 안 썼다)", methods == ["GET"],
          "%d번 · 메서드 %s" % (len(REQS), methods))
    fp_data1 = fingerprint(DATA)
    fp_cache1 = fingerprint(CACHE)
    L.chk("⑥ data/ 가 한 칸도 안 바뀌었다", fp_data0 == fp_data1,
          "전 %s → 후 %s (파일수·바이트·마지막 mtime)" % (fp_data0, fp_data1))
    L.chk("⑥ app/cache/ 가 한 칸도 안 바뀌었다", fp_cache0 == fp_cache1,
          "전 %s → 후 %s" % (fp_cache0, fp_cache1))
    pid1 = server_pid()
    L.chk("⑥ 실서버 PID 가 그대로다(끄지도 다시 띄우지도 않았다)", pid1 == pid0,
          "전 %s → 후 %s" % (pid0, pid1))
    L.chk("⑥ 실서버가 뜬 시각도 그대로다", proc_started(pid1) == t0,
          "%s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)))

    return L.summary("z4_live_smoke")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
