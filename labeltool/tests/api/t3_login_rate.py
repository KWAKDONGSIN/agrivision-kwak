# -*- coding: utf-8 -*-
"""t3 — `/login` 의 **429**(1분에 틀린 비밀번호 10번) 갈래. 작성: 2026-09-20

왜 따로 떼어 놓았나 (사이클 1 2차 검수 §10-4)
  이 갈래를 기준선 ⑤ 에 넣으면 잠금 창(IP 별 카운터)이 **뒤 실행을 오염**시킨다 — 같은 모래상자
  서버에 대고 다른 시험이 로그인하려다 429 로 튕긴다. 그래서 **자기 서버 하나만** 띄워서
  잠그고 끝낸다(그 서버는 이 시험이 끝날 때 함께 죽는다).

무엇을 못박나 (`app/core/auth.py` — 0918 UI사이클5 2차 N-M 의 규칙)
  ① `GET /login` 은 200
  ② 틀린 비밀번호는 401 이고, 1분에 **10번까지**는 401 이다
  ③ 11번째부터 429 («1분 뒤에 다시») — 무차별 대입 막기
  ④ 그 뒤 **맞는 비밀번호도 429** 다(잠금 창 안이라 비교조차 하지 않는다 — 코드 그대로)
  ⑤ 세는 것은 **틀린 시도만**이다: 맞는 비밀번호로 12번 이어 들어가도 429 가 없다
     (전에는 «시도» 를 세어 한 사무실에서 11번째 사람이 튕겨 나갔다 — 그 회귀를 막는다)
  ⑥ 로그인 없이 `/api/fruits` 는 401(JSON) · 화면 주소는 302(로그인 화면)
"""
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sandbox as L                                   # tests/lib/sandbox.py

LIMIT = 10          # app/core/auth.py LOGIN_TRY_LIMIT 과 같은 수(여기에 손으로 적는 유일한 곳)


def post_login(base, pw):
    d = urllib.parse.urlencode({"password": pw}).encode()
    req = urllib.request.Request(base + "/login", data=d, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as f:
            return f.status
    except urllib.error.HTTPError as e:
        e.read()
        return e.code


def get_code(base, path):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(NoRedirect)
    try:
        with op.open(base + path, timeout=60) as f:
            return f.status
    except urllib.error.HTTPError as e:
        e.read()
        return e.code


def main():
    L.sync()
    # ⑤ 부터 본다 — «맞는 비밀번호는 세지 않는다» 를 잠그기 **전** 에 확인해야 한다
    p = L.start()
    base = "http://127.0.0.1:%d" % L.PORT
    try:
        L.chk("t3-1 GET /login 은 200", get_code(base, "/login") == 200, get_code(base, "/login"))
        L.chk("t3-6a 로그인 없이 /api/fruits 는 401", get_code(base, "/api/fruits") == 401)
        L.chk("t3-6b 로그인 없이 화면 주소는 302(로그인 화면으로)", get_code(base, "/") == 302)
        # 맞으면 서버는 302 를 주고 urlopen 이 그것을 **따라가므로** 마지막 코드는 200 이다
        # (쿠키를 들고 가지 않아 `/` 가 다시 `/login` 으로 보내 200 — 어느 쪽이든 429 가 아니면 된다).
        ok = [post_login(base, L.PW) for _ in range(LIMIT + 2)]
        L.chk("t3-5 맞는 비밀번호는 %d번을 이어 넣어도 429 가 없다(틀린 시도만 센다)" % len(ok),
              all(c != 429 for c in ok), ok)
        wrong = [post_login(base, "틀림%d" % i) for i in range(LIMIT)]
        L.chk("t3-2 틀린 비밀번호 %d번까지는 401" % LIMIT, all(c == 401 for c in wrong), wrong)
        L.chk("t3-3 %d+1 번째 틀린 시도는 429" % LIMIT,
              post_login(base, "틀림끝") == 429)
        L.chk("t3-4 잠긴 뒤에는 **맞는 비밀번호도** 429 다(잠금 창 안)",
              post_login(base, L.PW) == 429)
    finally:
        L.stop(p)
    return L.summary("t3_login_rate")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
