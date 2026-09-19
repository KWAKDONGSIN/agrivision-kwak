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

function flash(msg, bad) {
  const el = $("#saveflash");
  el.textContent = msg;
  el.style.color = bad ? "#ffb3b3" : "#7ee2a8";
  clearTimeout(flash._t);
  flash._t = setTimeout(() => { el.textContent = ""; }, 3000);
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
  });
}
const post = (url, body) => api(url, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
});

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
Object.assign(UI, { $, $$, flash, who, errMsg, escapeHtml, ensureWho, onWhoKey });
API.get = api;
API.post = post;

})();
