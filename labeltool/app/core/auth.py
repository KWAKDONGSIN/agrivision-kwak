# -*- coding: utf-8 -*-
"""팀 공용 비밀번호 한 개짜리 문지기 — `/login` 과 모든 요청 앞의 검사.

구조 사이클 2(2026-09-20): `server.py` 에 있던 것을 그대로 옮기고, 라우트 두 개를
`register(app, ctx)` 안으로 들여썼다(동작·문구·쿠키·잠금 규칙 전부 그대로).
"""

from __future__ import annotations
from typing import Any
import os
import threading
import time

from domain.rules import LOGIN_FAIL_SLEEP

from flask import Response, jsonify, request
from urllib.parse import quote


# ---------------------------------------------------------------- 비밀번호 게이트
# 환경변수 LABELTOOL_PASSWORD 가 비어 있으면 게이트가 아예 없습니다(예전과 똑같이 동작).
# 값이 있으면 /login 에서 한 번 비밀번호를 넣어야 하고, 서명된 쿠키가 30일 유지됩니다.
# 팀 공용 비밀번호 하나만 씁니다(계정·가입 없음). 비밀번호는 app/run.sh 가
# ~/.council/labeltool.env 에서 읽어 넘깁니다.
LABELTOOL_PASSWORD = os.environ.get("LABELTOOL_PASSWORD", "").strip()
AUTH_COOKIE = "labeltool_auth"
AUTH_DAYS = 30
# 인증 없이 열어 두는 곳: 서버가 살아 있는지 보는 health 와 로그인 화면 자체
OPEN_PATHS = {"/api/health", "/login"}
# 쿠키가 없을 때 302(로그인 화면) 대신 401(JSON)로 답할 경로들
API_PREFIXES = ("/api/",)
API_PATHS = {"/img", "/mask", "/thumb"}


def _auth_sign(exp):
    import hmac
    import hashlib
    msg = ("labeltool|%d" % exp).encode("utf-8")
    return hmac.new(LABELTOOL_PASSWORD.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def make_auth_cookie() -> str:
    """현재 비밀번호에 서명된 로그인 쿠키 값을 만든다."""
    exp = int(time.time()) + AUTH_DAYS * 86400
    return "%d.%s" % (exp, _auth_sign(exp))


def auth_cookie_ok(value: Any) -> bool:
    """로그인 쿠키의 서명과 만료 시각을 검사한다."""
    import hmac
    if not value or "." not in value:
        return False
    exp_s, sig = value.split(".", 1)
    try:
        exp = int(exp_s)
    except ValueError:
        return False
    if exp < time.time():
        return False
    return hmac.compare_digest(sig, _auth_sign(exp))


LOGIN_HTML = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>라벨링 툴 — 비밀번호</title>
<style>
 body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
      background:#fbfaf8;color:#1d1b18;font:15px/1.6 system-ui,-apple-system,"Malgun Gothic",sans-serif}
 .box{width:min(92vw,360px);background:#fff;border:1px solid #e2ddd6;border-radius:12px;padding:28px 26px}
 h1{font-size:18px;margin:0 0 6px} p{color:#6b6560;font-size:13px;margin:0 0 18px}
 input{width:100%;box-sizing:border-box;padding:10px 12px;font-size:15px;
       border:1px solid #cfc8c0;border-radius:8px;margin-bottom:12px}
 button{width:100%;padding:10px;font-size:15px;border:0;border-radius:8px;
        background:#7a2f3a;color:#fff;cursor:pointer}
 .err{color:#8a3030;font-size:13px;margin:0 0 12px}
@media (max-width:820px) {
 *{box-sizing:border-box}
 .box{width:calc(100% - 32px);max-width:360px;padding:24px}
 body,p,input,button,.err{font-size:16px}
 input,button{min-height:44px}
}
</style></head><body>
<form class="box" method="post" action="/login">
  <h1>라벨링 툴</h1>
  <p>팀 공용 비밀번호를 넣어 주세요. 한 번 넣으면 30일 동안 기억합니다.<br>비밀번호는 팀 카톡으로 받으세요.</p>
  __ERR__
  <input type="hidden" name="next" value="__NEXT__">
  <input type="password" name="password" autofocus autocomplete="current-password" placeholder="비밀번호">
  <button type="submit">들어가기</button>
</form></body></html>"""



def safe_next(nxt: Any) -> str:
    """로그인 뒤 돌아갈 주소. 우리 서버 안의 경로만 허용한다.
    - 제어문자(탭·줄바꿈·널 등 0x00~0x1F, 0x7F)는 **먼저 전부 지운다**.
      (지우지 않고 검사만 하면 '/<TAB>/<TAB>evil.com' 이 통과하는데, 브라우저에 나갈 때
       Werkzeug 가 탭을 지워 '//evil.com' 이 되어 «다른 사이트» 로 튕긴다 — 오픈 리다이렉트)
    - 지운 뒤 '/' 로 시작하지 않으면 '/'
    - '//evil.com' · '/\\evil.com' 은 브라우저가 «다른 사이트» 로 읽으므로 막는다"""
    nxt = (nxt or "/")
    nxt = "".join(ch for ch in nxt if not (ord(ch) < 0x20 or ord(ch) == 0x7F))
    nxt = nxt.strip()
    if not nxt.startswith("/") or nxt.startswith("//") or nxt.startswith("/\\"):
        return "/"
    return nxt[:300]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def _login_page(err="", nxt="/"):
    body = LOGIN_HTML.replace("__ERR__", '<p class="err">%s</p>' % _esc(err) if err else "")
    return body.replace("__NEXT__", _esc(safe_next(nxt)))


# ---- 로그인 시도 제한: 같은 IP 가 1분에 10번 넘게 시도하면 잠시 막는다(메모리 카운터).
LOGIN_TRY_LIMIT = 10
LOGIN_TRY_WINDOW = 60          # 초
_login_tries = {}              # {ip: [시도시각, ...]}
_login_guard = threading.Lock()


def login_rate_ok(ip: str) -> Any:
    """True 면 시도해도 된다. False 면 1분 안에 **틀린** 비밀번호를 너무 많이 넣은 것.

    0918 UI사이클5 2차(N-M): 전에는 여기서 «시도» 를 세었다 — 비밀번호가 **맞은** 로그인까지
    셌기 때문에, 한 사무실 IP 에서 1분에 11번째 로그인은 비밀번호가 맞아도 429 로 막혔다
    (실측: 네 사람이 동시에 로그인하니 한 사람이 튕겨 나갔다 — cycle_5/stage1_work.md §⑥).
    이제 세는 것은 login_fail() 이 하고, 이 함수는 **읽기만** 한다.
    무차별 대입 막기는 그대로다 — 틀린 시도는 여전히 1분에 10번이면 막힌다.
    """
    now = time.time()
    with _login_guard:
        if len(_login_tries) > 2000:            # 메모리가 무한정 늘지 않게 가끔 청소
            for k in [k for k, v in _login_tries.items() if not v or v[-1] < now - LOGIN_TRY_WINDOW]:
                _login_tries.pop(k, None)
        q = [t for t in _login_tries.get(ip, []) if t > now - LOGIN_TRY_WINDOW]
        _login_tries[ip] = q
        return len(q) < LOGIN_TRY_LIMIT


def login_fail(ip: str) -> Any:
    """비밀번호가 **틀린** 시도 한 번을 센다(0918 UI사이클5 2차 · N-M)."""
    now = time.time()
    with _login_guard:
        q = [t for t in _login_tries.get(ip, []) if t > now - LOGIN_TRY_WINDOW]
        q.append(now)
        _login_tries[ip] = q

def register(app: Any, ctx: Any=None) -> None:
    """`/login` 과 `before_request` 검사를 붙인다."""


    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not LABELTOOL_PASSWORD:
            return Response("", status=302, headers={"Location": "/"})
        if request.method == "GET":
            nxt = safe_next(request.args.get("next", "/"))
            return Response(_login_page(nxt=nxt), mimetype="text/html; charset=utf-8")
        import hmac
        nxt = safe_next(request.form.get("next"))
        if not login_rate_ok(request.remote_addr or "?"):
            return Response(_login_page(err="비밀번호를 너무 여러 번 넣었습니다. 1분 뒤에 다시 해 주세요.", nxt=nxt),
                            status=429, mimetype="text/html; charset=utf-8")
        pw = (request.form.get("password") or "").strip()
        # 한글 등 ASCII 가 아닌 글자를 넣으면 compare_digest 가 TypeError(500) 를 내므로 바이트로 비교한다
        if hmac.compare_digest(pw.encode("utf-8"), LABELTOOL_PASSWORD.encode("utf-8")):
            r = Response("", status=302, headers={"Location": nxt})
            r.set_cookie(AUTH_COOKIE, make_auth_cookie(), max_age=AUTH_DAYS * 86400,
                         httponly=True, samesite="Lax", path="/")
            return r
        login_fail(request.remote_addr or "?")   # 0918 2차 N-M: 틀린 시도만 센다
        time.sleep(LOGIN_FAIL_SLEEP)   # 무차별 대입 속도만 늦춥니다
        return Response(_login_page(err="비밀번호가 다릅니다.", nxt=nxt),
                        status=401, mimetype="text/html; charset=utf-8")


    @app.before_request
    def require_password():
        if not LABELTOOL_PASSWORD:
            return None
        p = request.path
        if p in OPEN_PATHS:
            return None
        if auth_cookie_ok(request.cookies.get(AUTH_COOKIE)):
            return None
        if p.startswith(API_PREFIXES) or p in API_PATHS:
            return jsonify({"ok": False, "error": "로그인이 필요합니다. /login 에서 비밀번호를 넣어 주세요."}), 401
        return Response("", status=302,
                        headers={"Location": "/login?next=%s" % quote(safe_next(p), safe="/")})
