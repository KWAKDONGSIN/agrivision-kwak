/* api — 서버 부르기 · 요소 찾기 · 알림
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 8-10·28-40·42-62·275-277줄 · ui.js 914-927·932-937줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   `API.get`/`API.post`(서버), `UI.$`/`UI.$$`(요소 찾기), `UI.flash`(아래쪽 알림), `UI.who`(내 이름), `UI.errMsg`(서버 오류 문장), `UI.escapeHtml`.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {

/* ------------------------------------------------------------------ 공통 */
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

/* 글자만 갈아 끼운다 — 켜 둔 시계를 끄고, 「확인」 단추가 붙어 있었다면 그것까지 지운다.
   (`textContent` 을 넣으면 자식 요소가 함께 사라진다.) */
function paintFlash(msg, bad) {
  const el = $("#saveflash");
  clearTimeout(flash._t);
  el.textContent = msg;
  el.style.color = bad ? "#ffb3b3" : "#7ee2a8";
  el.classList.remove("flashbad");
  return el;
}
function clearFlash() { paintFlash("", false); }

/* 🔴 2026-09-21 편의·안정성 S2 — **실패 알림은 저절로 사라지지 않는다.**
   전에는 성공이든 실패든 3초 뒤에 지웠다. 저장이 실패한 순간에 사람은 보통 캔버스를 보고
   있어서, 상단 바 구석에 3초만 떴다 사라지는 붉은 글씨를 **놓친다.** 그러고는 저장된 줄 알고
   다음 장으로 넘어간다 — S1 로 «조용히 씹히는» 것은 막았지만, 말해 줘도 못 보면 결과가 같다.
   → 실패는 «확인» 을 누를 때까지 남는다(윈도우 오류 창의 관습).
   왜 자리를 옮기나 — `#topbar` 는 `height:40px · overflow:hidden` 이라 긴 문장과 «확인» 단추가
     잘려 나가 누를 수가 없다. 그래서 실패일 때만 `.flashbad` 로 상단 바 아래 띠가 된다(style.css).
   성공 알림은 자리도 시간(3초)도 그대로다 — 잘 되고 있는 일까지 손으로 지우게 하지 않는다. */
function flash(msg, bad) {
  const el = paintFlash(msg, bad);
  if (!bad) { flash._t = setTimeout(clearFlash, 3000); return; }
  el.classList.add("flashbad");
  const b = document.createElement("button");
  b.type = "button";
  b.className = "flashok";
  b.textContent = "확인";
  b.title = "이 알림을 지웁니다";
  b.addEventListener("click", clearFlash);
  el.appendChild(b);
}

/* 실패가 아니라 **안내**인 것(«사진 밖입니다» 같은)은 1초 뒤 스스로 사라진다 — 띠도 안 띄운다.
   2026-09-21 S2 전에는 부르는 쪽마다 `flash()` 뒤에 `flash._t` 를 1초로 바꿔 끼우는 두 줄이
   붙어 있었다(main.js 2곳·counts.js·instances.js). 그 두 줄을 여기 한 곳으로 모았다 —
   보이는 동작은 전과 똑같고, 대신 «확인» 단추가 1초짜리 힌트에는 붙지 않는다. */
function flashBrief(msg, bad) {
  paintFlash(msg, bad);
  flash._t = setTimeout(clearFlash, 1000);
}
/* ══════════════ 🔴 2026-09-21 편의·안정성 S6 — 저장 중에는 그 단추를 잠근다 ══════════════
   지금까지 «저장» 은 몇 번이든 눌리는 단추였다. 1664×1248 마스크 한 장은 PNG 로 접어 올리는 데
   1~2초가 걸리는데(S5 에서 실측), 그동안 화면은 «저장 중…» 한 줄뿐이라 아무 일도 안 일어나는
   것처럼 보인다 → 사람은 한 번 더 누른다. 그러면 **같은 것을 두 번 올린다**:
     · 상자 — 두 번째 응답이 늦게 와서 첫 번째가 덮어쓴 화면을 다시 덮는다(id 가 두 번 다시 붙는다)
     · 판정 — `doAction` 끝의 `nextItem()` 이 두 번 돌아 **사진 한 장을 건너뛴다**(보지도 않고 넘어감)
     · Ctrl+S 를 누른 채 있으면 키 반복으로 초당 수십 번이 그대로 서버로 간다
   → 그 길이 도는 동안 같은 길로 다시 들어오지 못하게 막고(`busy`), 단추에는 «지금 하는 중» 딱지를
     붙인다(`.saving` — style.css).
   왜 `disabled` 를 쓰지 않나 — `#btn-ai`·`#btn-save` 는 다른 규칙(AI 제안 유무·번호 편집 모드)이
     이미 `disabled` 를 켰다 껐다 한다(instances.js setNumMode · list.js openItem). 저장이 끝난 뒤
     «내가 잠그기 전 값» 으로 되돌리면, 그 사이에 사진이 바뀌어 규칙이 정한 값을 **덮어쓴다.**
     딱지는 되돌릴 값이 없다 — 붙였다 떼면 그만이다. 못 누르게 하는 것은 `.saving` 의
     `pointer-events:none` 이 하고, 키보드(Ctrl+S)는 `busy` 가 막는다.
   왜 저장 함수 **안** 이 아니라 바깥에서 감싸나 — `boxsim.js` 가 `saveBoxes()` 의 글자를 그대로
     떼어 내 node 에서 돌린다. 함수 안에 새 이름을 넣으면 그 시뮬 50여 항목이 통째로 죽는다. */
function lockWhile(sels, fn) {
  let busy = false;
  return async function () {
    if (busy) return;                                   // 이미 도는 중 — 두 번째 누름은 버린다
    busy = true;
    const els = (sels || []).map((s) => $(s)).filter(Boolean);
    els.forEach((e) => e.classList.add("saving"));
    try {
      return await fn.apply(this, arguments);
    } finally {                                         // 실패해도·던져도 반드시 풀린다
      busy = false;
      els.forEach((e) => e.classList.remove("saving"));
    }
  };
}

const who = () => ($("#who").value || "").trim() || "익명";

/* 서버가 보낸 오류 문장(쉬운 한국어)을 꺼낸다. 응답 자체가 없으면(=401) 기본 문장. */
function errMsg(j, dflt) {
  return (j && (j.error || j.msg)) || dflt || "실패했습니다";
}

/* 응답을 JSON 으로 돌려준다. **로그인이 풀렸으면 null** 을 돌려주므로
   부르는 쪽은 반드시 `if (!j) return;` 로 먼저 막아야 한다(그래야 화면이 안 깨진다). */
function api(url, opt) {
  return fetch(url, opt).then(async (r) => {
    setNet(true);                      // 답이 왔다 = 서버에 닿았다 (S3 — 붉은 띠를 걷는다)
    if (r.status === 401) {            // 비밀번호 쿠키가 만료됐거나 지워짐
      location.href = "/login?next=" + encodeURIComponent(location.pathname || "/");
      return null;
    }
    const t = await r.text();
    let j = null;
    // 서버가 JSON 이 아닌 것(HTML 오류 쪽 등)을 보내면 그 글자를 그대로 띄우지 않는다
    try { j = JSON.parse(t); } catch (e) {
      j = { ok: false, error: "서버가 예상 밖의 답을 보냈습니다(오류 " + r.status + "). 새로고침 해 보세요." };
    }
    if (!r.ok && j && j.error === undefined && j.msg === undefined) j.error = "서버 오류 " + r.status;
    return j;
  }).catch(() => {
    /* 🔴 2026-09-21 편의·안정성 S1 — **서버에 닿지도 못한** 경우.
       와이파이가 끊겼거나 서버가 다시 켜지는 중이면 `fetch` 자체가 깨진다(Promise reject).
       그때까지 이 함수는 깨진 약속을 그대로 넘겼고, 부르는 쪽의 `await` 가 거기서 멈춰서
       **아무 말도 없이 클릭이 씹혔다**(콘솔에만 unhandled rejection). 저장 한 번을 잃는 길이다.
       → 다른 오류와 **똑같은 모양**(`{ok:false, error}`)으로 돌려준다. 부르는 쪽은 이미
       `if (!j || !j.ok) return flash(errMsg(j, …), true)` 를 하고 있으므로 고칠 곳이 없다 —
       그 자리에서 붉은 알림이 뜬다. 401 은 위에서 이미 `null` 로 빠져나가므로 여기 오지 않는다. */
    setNet(false);                     // 닿지 못했다 = 지금 끊겼다 (S3 — 붉은 띠를 곧바로 깐다)
    netSchedule();
    return { ok: false, error: "서버에 닿지 못했습니다. 인터넷이 끊겼거나 서버가 다시 켜지는 중입니다."
                             + " 잠시 뒤 다시 눌러 주세요(한 일은 그대로 남아 있습니다)." };
  });
}
const post = (url, body) => api(url, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
});

/* ══════════════════ 🔴 2026-09-21 편의·안정성 S3 — 서버 연결 감시 ══════════════════
   S1·S2 로 «누른 것이 조용히 씹히는 것»·«실패를 못 보고 넘어가는 것» 은 막았다. 그래도 구멍이
   하나 남는다 — 사람이 아무것도 안 누르고 30분을 칠하는 동안 서버가 죽어 있으면 **아무도
   말해 주지 않는다.** 그러다 «저장» 을 눌러서야 붉은 띠를 보게 되는데, 그 30분은 못 되돌린다.
   → 30초마다 `/api/health` 를 한 번 두드려 «지금 닿는가» 를 늘 알고, 안 닿으면 화면 맨 위에
     붉은 띠를 깐다. 다시 닿으면 저절로 사라진다(사람이 지울 것이 없다).
   왜 `api()` 를 안 쓰나 — `api()` 는 실패하면 «확인» 을 눌러야 지워지는 붉은 알림을 띄운다(S2).
     감시는 사람이 누른 적이 없는 일이라 알림을 띄우면 안 된다. 그래서 맨 `fetch` 를 쓴다.
   왜 새 주소를 안 만드나 — `/api/health` 가 이미 있고 **로그인 없이 열려 있다**(core/auth.py
     OPEN_PATHS). 파이썬을 한 줄도 안 고치므로 실서버(5111) 재시작이 필요 없다.
   끊긴 뒤에는 5초마다 본다 — 서버 재시작은 보통 몇 초라서, 30초를 더 기다리게 하면
     «다 고쳐졌는데도 빨간 줄» 이 남아 사람이 괜히 새로고침을 하게 된다. */
const NET_EVERY = 30000;              // 잘 닿는 동안
const NET_EVERY_DOWN = 5000;          // 끊긴 뒤 — 돌아왔는지 빨리 본다
let netDown = false, netTimer = null, netBusy = false;

/* 붉은 띠는 **처음 끊길 때** 만든다(잘 도는 동안에는 화면에 아무것도 늘지 않는다).
   `#topbar` **앞**에 끼워 제자리를 차지하게 한다 — 겹쳐 띄우면 탭·과일 고르개를 덮어 버린다. */
function netBanner() {
  let el = $("#netdown");
  if (!el) {
    el = document.createElement("div");
    el.id = "netdown";
    el.textContent = "⚠ 서버에 연결되지 않습니다 — 지금은 저장되지 않습니다. 창을 닫지 마세요.";
    el.title = "인터넷이 끊겼거나 서버가 다시 켜지는 중입니다. 지금까지 한 일은 화면에 그대로"
             + " 있습니다. 연결되면 이 줄이 저절로 사라집니다 — 그때 다시 «저장» 을 누르세요.";
    document.body.insertBefore(el, document.body.firstChild);
  }
  return el;
}

function setNet(ok) {
  if (ok === !netDown) return;                          // 바뀐 게 없으면 화면을 안 건드린다
  netDown = !ok;
  netBanner().classList.toggle("on", netDown);
  document.body.classList.toggle("netdown", netDown);   // 실패 띠(.flashbad)를 그만큼 내린다
}

/* 한 번 두드려 본다. 답이 **무엇이든** 오면 «닿았다» 로 본다 — 500 이어도 서버는 살아 있고,
   이 띠가 말하는 것은 «닿느냐» 이지 «서버가 건강하냐» 가 아니다. */
function netProbe() {
  if (netBusy) return Promise.resolve(!netDown);
  netBusy = true;
  return fetch("/api/health", { cache: "no-store" }).then(() => true, () => false)
    .then((ok) => { netBusy = false; setNet(ok); netSchedule(); return ok; });
}

function netSchedule() {
  clearTimeout(netTimer);
  netTimer = setTimeout(netProbe, netDown ? NET_EVERY_DOWN : NET_EVERY);
}
netSchedule();

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ══════════════════════════ ⑦ «내 이름» 을 첫 판정 때 한 번만 묻기 ══════════════════════════
   이름을 안 적어도 아무도 막지 않아 검수 기록이 전부 by:"익명" 으로 쌓였다(2차 검수 §4-8).
   판정·저장을 처음 할 때 딱 한 번 물어보고, 답을 안 해도 그대로 진행한다(일을 막지 않는다). */
let askedWho = false;
function ensureWho() {
  if (askedWho) return;
  askedWho = true;
  if (($("#who").value || "").trim()) return;
  const n = prompt("검수 기록에 남길 «내 이름» 을 적어 주세요.\n(비워 두면 «익명» 으로 남습니다. 이 물음은 한 번뿐입니다.)", "");
  if (n && n.trim()) {
    $("#who").value = n.trim();
    try { localStorage.setItem("who", n.trim()); } catch (e) {}
  }
}

function onWhoKey(e) {                      // 등록은 keys.js (가로채기 단계)
  if ($("#view-edit").classList.contains("hidden")) return;
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  if ("1234".indexOf(e.key) >= 0 || ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S"))) ensureWho();
}


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { $, $$, flash, flashBrief, clearFlash, who, errMsg, escapeHtml, ensureWho, onWhoKey,
                    netProbe,      // 0921 S3: «지금 당장 한 번 확인» — 시험이 30초를 안 기다리게
                    lockWhile });  // 0921 S6: 저장 중 단추 잠금
API.get = api;
API.post = post;

})();
