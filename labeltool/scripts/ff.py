# -*- coding: utf-8 -*-
"""진짜 브라우저(파이어폭스 headless)로 툴 화면을 열고 누르고 찍는 아주 작은 도구. 작성: 2026-09-17
selenium 없이 geckodriver 의 WebDriver HTTP 를 urllib 로 직접 부른다(새 패키지 설치 0).

    from ff import Browser
    with Browser() as b:                 # geckodriver + firefox 를 띄우고 끝나면 끈다
        b.login()                        # ~/.council/labeltool.env 의 비밀번호로 로그인
        b.js("return document.title")
        b.key("k"); b.click("#btn-ok"); b.shot("/home/kds0206/ff_shots/a.png")

주의: 파이어폭스가 snap 이라 **스크린샷은 홈 폴더 아래(숨김 폴더 제외)** 에만 쓸 수 있다 → 기본 ~/ff_shots/.
⛔ 판정·저장 단추를 누르면 공용 data/ 가 실제로 바뀐다. 눈 확인용으로는 보기·모드 전환만 하고, 저장 시험은 모래상자 서버에서.
"""
import base64, json, os, socket, subprocess, time, urllib.request

BASE = os.environ.get("LABELTOOL_URL", "").strip()
SHOTS = os.path.expanduser("~/ff_shots")
ELEM = "element-6066-11e4-a52e-4f735466cecf"


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Browser:
    def __init__(self, w=1500, h=950):
        if not BASE:
            raise RuntimeError("브라우저 대상이 없습니다. LABELTOOL_URL에 모래상자 주소를 명시하세요.")
        self.port = _free_port()
        self.proc = subprocess.Popen(["geckodriver", "--port", str(self.port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try: self._req("GET", "/status"); break
            except OSError: time.sleep(0.2)
        caps = {"capabilities": {"alwaysMatch": {"moz:firefoxOptions": {"args": ["-headless", "--width=%d" % w, "--height=%d" % h]}}}}
        self.sid = self._req("POST", "/session", caps)["sessionId"]
        os.makedirs(SHOTS, exist_ok=True)

    def _req(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), data=data, method=method,
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=120) as f:
                return json.load(f)["value"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(json.load(e)["value"].get("message", "webdriver error")) from None

    def _s(self, method, path, body=None): return self._req(method, "/session/%s%s" % (self.sid, path), body)
    def go(self, path): self._s("POST", "/url", {"url": path if path.startswith("http") else BASE + path})
    def js(self, script, *args): return self._s("POST", "/execute/sync", {"script": script, "args": list(args)})
    def find(self, css): return self._s("POST", "/element", {"using": "css selector", "value": css})[ELEM]
    def click(self, css): self._s("POST", "/element/%s/click" % self.find(css), {})
    def type(self, css, text): self._s("POST", "/element/%s/value" % self.find(css), {"text": text})
    def alert_text(self): return self._s("GET", "/alert/text")
    def alert_ok(self): self._s("POST", "/alert/accept", {})
    def alert_cancel(self): self._s("POST", "/alert/dismiss", {})

    def key(self, k):
        """본문에 키 하나를 보낸다(단축키 시험). 특수키는 WebDriver 코드(예: Delete='\\ue017')."""
        self._s("POST", "/actions", {"actions": [{"type": "key", "id": "kb", "actions": [{"type": "keyDown", "value": k}, {"type": "keyUp", "value": k}]}]})

    def drag(self, css, x0, y0, x1, y1):
        """요소의 왼쪽 위 기준 화소 좌표로 마우스 드래그(캔버스에 상자·브러시 그리기)."""
        r = self.js("const r=document.querySelector(arguments[0]).getBoundingClientRect();return [r.left,r.top]", css)
        P = lambda x, y, d=0: {"type": "pointerMove", "duration": d, "x": int(r[0] + x), "y": int(r[1] + y)}
        self._s("POST", "/actions", {"actions": [{"type": "pointer", "id": "m", "parameters": {"pointerType": "mouse"},
                "actions": [P(x0, y0), {"type": "pointerDown", "button": 0}, P((x0 + x1) / 2, (y0 + y1) / 2, 60), P(x1, y1, 60), {"type": "pointerUp", "button": 0}]}]})

    def wait(self, script, timeout=30):
        t = time.time()
        while time.time() - t < timeout:
            if self.js(script): return True
            time.sleep(0.3)
        raise TimeoutError(script)

    def wait_js(self, script, *args, timeout=30):
        t = time.time()
        while time.time() - t < timeout:
            if self.js(script, *args): return True
            time.sleep(0.3)
        raise TimeoutError(script)

    def login(self):
        pw = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.council/labeltool.env")) if l.startswith("LABELTOOL_PASSWORD=")][0]
        self.go("/login"); self.type("input[name=password]", pw); self.click("button, input[type=submit]")
        self.wait("return !!document.querySelector('#fruit option')")

    def open_photo(self, fruit, stem=None, index=0):
        """목록에서 과일을 고르고 사진 한 장을 연다(stem 을 주면 검색해서 첫 카드)."""
        self.js("const s=document.querySelector('#fruit');s.value=arguments[0];s.dispatchEvent(new Event('change'))", fruit)
        if stem:
            # 검색 칸은 Enter 에서만 목록을 다시 읽는다(app.js) — 값만 넣으면 엉뚱한 사진이 열린다(UI 사이클1 2차가 발견)
            self.js("const q=document.querySelector('#f-q');q.value=arguments[0];q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))", stem)
        if stem:    # 검색은 부분 일치 + 디바운스라, 이름이 «정확히» 같은 카드가 뜰 때까지 기다렸다가 그 카드를 누른다
            pick = "const c=[...document.querySelectorAll('#grid .card')].find(c=>c.querySelector('.cap').firstChild.textContent.trim()===arguments[0]);"
            self.wait_js(pick + "return !!c", stem); self.js(pick + "c.click()", stem)
        else:
            time.sleep(1.0); self.wait("return document.querySelectorAll('#grid .card').length>0")
            self.js("document.querySelectorAll('#grid .card')[arguments[0]].click()", index)
        self.wait("return document.querySelector('#loading').classList.contains('hidden') && document.querySelector('#stemname').textContent!=='사진을 고르세요'", 60)
        time.sleep(0.8)

    def shot(self, path):
        path = path if os.path.isabs(path) else os.path.join(SHOTS, path)
        open(path, "wb").write(base64.b64decode(self._s("GET", "/screenshot"))); return path

    def close(self):
        try: self._s("DELETE", "")
        finally: self.proc.terminate()

    def __enter__(self): return self
    def __exit__(self, *a): self.close()


if __name__ == "__main__":      # 자체 점검: 로그인 → 사과 한 장 → 번호 개수 읽기 → 화면 찍기
    with Browser() as b:
        b.login(); print("title:", b.js("return document.title"))
        b.open_photo("apple", "20150919_174151_image1")
        assert b.js("return document.querySelector('#stemname').textContent") == "20150919_174151_image1"
        print("meta:", b.js("return document.querySelector('#meta').textContent"))
        print("numinfo:", b.js("return document.querySelector('#numinfo').textContent"))
        print("shot:", b.shot("selfcheck_apple.png"))
