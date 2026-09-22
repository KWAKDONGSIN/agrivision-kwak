/* view — 캔버스 · 확대 · 화면 전환 · 보기 전환
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 64-79·594-606·608-642·644-712·714-719줄 · ui.js 21-147·149-270·631-672·674-694·696-745줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   사진을 그리는 것(draw/fitView/zoomToNote/toImg)과 «어느 화면·어느 작업·어느 보기» 를 맞추는 것. 겹(마스크·상자·번호)은 각 파일이 그리고, draw() 가 차례로 부른다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, escapeHtml = UI.escapeHtml, statusKo = UI.statusKo, TASKWORD = UI.TASKWORD;
const api = API.get, post = API.post;

/* ------------------------------------------------------------ 화면 전환 */
/* 위쪽 탭(사진 목록 · 사진 고치기 · 진행 현황)을 누를 때도 저장 안 한 수정을 알려 준다.
   탭만 바꾸는 것이라 수정이 지워지지는 않으므로 문구가 다르다(confirmLeave("view")). */
function showView(v) {
  $$(".tab").forEach((b) => b.classList.toggle("on", b.dataset.view === v));
  $("#view-list").classList.toggle("hidden", v !== "list");
  $("#view-edit").classList.toggle("hidden", v !== "edit");
  $("#view-dash").classList.toggle("hidden", v !== "dash");
  /* 0918 사이클3: «데이터 정리» 탭. 옛 화면(그 section 이 없는 index.html)에서도 깨지지 않게
     있을 때만 만지고, 내용은 ui.js 가 붙여 주는 window.expOpen() 이 채운다. */
  const ve = $("#view-exp");
  if (ve) ve.classList.toggle("hidden", v !== "exp");
  if (v === "edit") { resizeCanvas(); S.dirty = true; }
  if (v === "dash") UI.loadDash();     // ↓ list.js
  if (v === "exp" && window.expOpen) window.expOpen();
  if (v === "exp" && UI.loadTeamGrape) UI.loadTeamGrape();
}

/* ------------------------------------------------------------- 화면 그리기 */
const cv = $("#cv");
const ctx = cv.getContext("2d");

function resizeCanvas() {
  const w = $("#canvaswrap").clientWidth, h = $("#canvaswrap").clientHeight;
  if (!w || !h) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  cv._dpr = dpr;
  S.dirty = true;
}
new ResizeObserver(resizeCanvas).observe($("#canvaswrap"));

function fitView() {
  if (!S.W) return;
  const dpr = cv._dpr || 1;
  const s = Math.min(cv.width / dpr / S.W, cv.height / dpr / S.H) * 0.97;
  S.view.s = s;
  S.view.tx = (cv.width / dpr - S.W * s) / 2;
  S.view.ty = (cv.height / dpr - S.H * s) / 2;
  S.dirty = true;
}

/* 「노란 점선 후보」 자리로 확대 — 0918 UI사이클4 N7.
   메모 좌표 상자가 화면에서 30×35화소밖에 안 되어(1080×1920 사진을 240px 폭으로 보여 준다)
   확대(휠)를 모르는 사람은 찾지 못했다. 이 함수는 그 상자를 **화면 가운데에** 두고,
   상자가 창 짧은 쪽의 30% 는 되게 확대한다(화면 폭의 10% 이상 — 사이클4 합격선).
   여러 곳이면 누를 때마다 다음 곳으로 돌아간다. 원래 크기는 0 키(fitView). */
function zoomToNote(i) {
  if (!S.img || !S.noteBoxes || !S.noteBoxes.length) { flash("이 사진에는 노란 점선 후보가 없습니다", true); return; }
  S.noteZoomAt = (typeof i === "number") ? i : (S.noteZoomAt + 1) % S.noteBoxes.length;
  const r = S.noteBoxes[S.noteZoomAt].box;
  const dpr = cv._dpr || 1, W = cv.width / dpr, H = cv.height / dpr;
  const bw = Math.max(8, r[2] - r[0]), bh = Math.max(8, r[3] - r[1]);
  // 상자의 **짧은 쪽**이 «캔버스 짧은 쪽의 36%» 는 되게 한다.
  //   긴 쪽 기준(30%)으로 재면 세로로 긴 후보가 폭 129px(화면의 9.4%)밖에 안 나왔다 — 실측.
  //   다만 긴 쪽이 캔버스를 넘지 않게 80% 로 묶고, 16배 이상은 당기지 않는다.
  const short = Math.min(W, H);
  const want = Math.min(short * 0.36 / Math.min(bw, bh), short * 0.80 / Math.max(bw, bh), 16);
  const s = Math.max(Math.min(W / S.W, H / S.H) * 0.97, want);
  S.view.s = s;
  S.view.tx = W / 2 - (r[0] + bw / 2) * s;
  S.view.ty = H / 2 - (r[1] + bh / 2) * s;
  S.dirty = true;
  flash(`후보 ${S.noteZoomAt + 1}/${S.noteBoxes.length} 자리로 확대했습니다 (0 키로 원래 크기)`);
}
window.zoomToNote = zoomToNote;      // ui.js 의 «후보 자리로 확대» 단추가 부른다

/* 0921 U2 — 확대바의 배율 % (그림판 상태줄).
   «지금 몇 배로 보고 있나» 는 지금까지 `#hud` 에만 있었는데, 그 칸은 **쉬움 모드에서 숨고**
   (style.css `body.easy #hud`) 마우스를 움직여야 갱신된다(main.js mousemove). 그래서 확대 단추를
   눌러 놓고도 «내가 얼마나 당겼는지» 를 모른다. 확대 단추 바로 옆에 늘 보이는 숫자를 둔다.
   글자는 `#hud` 와 **같은 식**으로 만든다 — 두 자리가 다른 수를 말하면 안 된다.
   갱신 자리를 확대하는 곳마다(휠·＋－·맞춤·후보 확대·핀치) 붙이지 않고 draw() 한 곳에 둔다.
   배율이 바뀌면 반드시 `S.dirty = true` 가 되어 이 함수가 그 프레임에 돈다(놓치는 길이 없다).
   값이 그대로면 화면을 한 칸도 안 건드린다(이동·붓질로 draw 가 도는 동안 DOM 을 쓰지 않는다). */
let pctLast = null;
function showZoomPct() {
  const el = $("#zoompct");
  if (!el) return;                                   // 이 칸이 없는 쪽(사용법 등)에서는 아무 일도 안 한다
  const t = S.img ? (S.view.s * 100).toFixed(0) + "%" : "";
  if (t === pctLast) return;
  pctLast = t;
  el.textContent = t;
}

function draw() {
  requestAnimationFrame(draw);
  if (!S.dirty) return;
  S.dirty = false;
  showZoomPct();
  applyCursor();                // 0921 U5 — 도구·자리에 맞는 커서(값이 그대로면 아무 일도 안 한다)
  const dpr = cv._dpr || 1;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#2b3138";
  ctx.fillRect(0, 0, cv.width, cv.height);
  // 0918 사이클2 (사이클1 3차 판정 ②-4): 세로 사진 옆 회색 여백이 «사진의 일부» 로 보였다.
  // 그림판처럼 아주 옅은 격자를 깔아 «여기는 사진 밖» 을 눈으로 알려 준다(그림·저장에는 영향 0).
  ctx.strokeStyle = "rgba(255,255,255,.05)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let gx = 16; gx < cv.width; gx += 16) { ctx.moveTo(gx + 0.5, 0); ctx.lineTo(gx + 0.5, cv.height); }
  for (let gy = 16; gy < cv.height; gy += 16) { ctx.moveTo(0, gy + 0.5); ctx.lineTo(cv.width, gy + 0.5); }
  ctx.stroke();
  if (!S.img) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.translate(S.view.tx, S.view.ty);
  ctx.scale(S.view.s, S.view.s);
  ctx.imageSmoothingEnabled = S.view.s < 1;
  ctx.globalAlpha = 1;
  ctx.drawImage(S.img, 0, 0);
  // 0918 «보기 전환»(ui.js 가 S.dim 을 넣는다) — 사진**만** 어둡게 덮어 마스크·번호만 보이게 한다.
  // S.dim 이 0/undefined 면(기본) 아무 일도 하지 않는다 — 그림 순서와 저장에는 영향이 없다.
  if (S.dim) { ctx.globalAlpha = S.dim; ctx.fillStyle = "#000"; ctx.fillRect(0, 0, S.W, S.H); }
  // 0922 «지우개가 안 지워진다»(사용자 보고) — 원본(빨강)·AI(파랑)·내 수정본(하늘색)이 같은 진하기로
  // 겹쳐 있어, 지우개로 수정본을 지워도 그 **밑의 빨강·파랑이 그대로** 보였다(모래상자 실측: 데이터
  // S.ed 는 0 이 됐는데 화면 색은 그대로). 저장되는 것은 수정본 하나뿐이므로 수정본이 켜져 있을 때는
  // 원본·AI 를 참고용으로 흐리게(0.35배) 깐다. 수정본을 끄면 예전처럼 제 진하기로 보인다.
  const edOn = $("#l-ed").checked && S.lay.ed;
  ctx.globalAlpha = edOn ? S.alpha * 0.35 : S.alpha;
  if ($("#l-gt").checked && S.lay.gt) ctx.drawImage(S.lay.gt.cv, 0, 0);
  if ($("#l-ai").checked && S.lay.ai) ctx.drawImage(S.lay.ai.cv, 0, 0);
  ctx.globalAlpha = S.alpha;
  if (edOn) ctx.drawImage(S.lay.ed.cv, 0, 0);
  if ($("#l-diff").checked && S.lay.diff) { ctx.globalAlpha = Math.min(1, S.alpha + 0.35); ctx.drawImage(S.lay.diff.cv, 0, 0); }
  ctx.globalAlpha = 1;
  if (S.inst && S.lay.num && $("#l-num").checked) {
    // 0922: 번호 덩어리(복숭아 등)도 수정본 위에 0.6 으로 덮여 지운 자리를 가렸다. 번호 편집 모드가
    // 아니고 수정본이 켜져 있으면 번호도 참고용으로 흐리게(0.35배). 번호 편집(K)에서는 예전 그대로.
    ctx.globalAlpha = (S.numMode || !edOn) ? S.numAlpha : S.numAlpha * 0.35;
    ctx.drawImage(S.lay.num.cv, 0, 0);
    ctx.globalAlpha = 1;
  }
  UI.drawNumOverlay();          // ↓ instances.js (되돌아 부르는 자리)
  // 0918 사이클2 (사이클1 3차 판정 ②-6): «원본만» 은 «사진만» 이어야 한다 —
  // 검출 팀 빨간 점선·메모의 노란 점선도 같이 감춘다(S.hideBox 는 «원본만» 에서만 켜진다).
  if (!S.hideBox) UI.drawErrBoxes();   // ↓ instances.js
  // 0918 «보기 전환» 의 «원본만» 에서는 필름·상자도 감춘다(S.hideBox 는 ui.js 가 넣는다)
  if (S.boxMode && !S.hideBox) {
    ctx.globalAlpha = S.film;             // 사진 위에 덮는 «투명 필름»
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, S.W, S.H);
    ctx.globalAlpha = 1;
    UI.drawBoxes();                    // ↓ boxes.js
  }
  // 다각형 미리보기
  if (S.poly.length) {
    ctx.beginPath();
    ctx.moveTo(S.poly[0][0], S.poly[0][1]);
    for (let i = 1; i < S.poly.length; i++) ctx.lineTo(S.poly[i][0], S.poly[i][1]);
    ctx.closePath();
    ctx.lineWidth = Math.max(1, 2 / S.view.s);
    ctx.strokeStyle = S.tool === "polysub" ? "#ff5555" : "#ffee55";
    ctx.stroke();
  }
  // 붓 커서
  if (S.cursor && (S.tool === "brush" || S.tool === "erase")) {
    ctx.beginPath();
    ctx.arc(S.cursor[0], S.cursor[1], S.brush / 2, 0, Math.PI * 2);
    ctx.lineWidth = Math.max(1, 1.5 / S.view.s);
    ctx.strokeStyle = S.tool === "erase" ? "#ff8888" : "#ffffff";
    ctx.stroke();
  }
}
requestAnimationFrame(draw);

function toImg(ev) {
  const r = cv.getBoundingClientRect();
  const x = (ev.clientX - r.left - S.view.tx) / S.view.s;
  const y = (ev.clientY - r.top - S.view.ty) / S.view.s;
  return [x, y];
}

/* ══════════════════════════ ① 작업 고르기 (왼쪽 도구 상자 맨 위 3칸) ══════════════════════════
   «지금 무슨 일을 하는지» 하나만 고르게 한다. 기존 #box-mode 체크박스(X)·번호 편집 모드(K)와
   **같은 상태를 공유**한다 — 이 단추는 그 둘을 대신 눌러 줄 뿐, 따로 상태를 들고 있지 않다. */

const TASKNOTE = {
  mask: "① 칠한 영역 검수 — 빨강(원본 라벨)이 열매를 제대로 덮었는지 봅니다. 왼쪽 도구로 고칩니다.",
  box:  "② 상자 그리기 — 빈 곳을 드래그하면 네모가 하나 생깁니다. «초벌» 을 먼저 누르면 훨씬 빠릅니다.",
  // 2026-09-17 2차 검수 정정: 네 가지 모두 «마우스로 고른 뒤 키를 눌러야» 고쳐진다(app.js numKey).
  num:  "③ 열매 번호 — 고른 뒤 키를 누릅니다. 알 클릭→D 지우기 · A·B 클릭→M 합치기 · 선 드래그→X 나누기 · 그린 뒤→N 붙이기."
};
// 0919 «개수 세기» 사이클4 M1: 네 과일 **모두** 번호본이 생겼다(사과 원본 정답 · 블루베리·복숭아
// 박성문 워터셰드 · 포도 CERTH 정답 송이). 그래서 «복숭아·포도는 번호가 없습니다» 는 이제 거짓이다.
const NUM_WHY = "③ 열매 번호는 «번호본이 있는 사진» 에서만 됩니다 (이 사진에는 번호본이 없습니다).";

function curTask() { return S.numMode ? "num" : S.boxMode ? "box" : "mask"; }

function setTask(t) {
  if (t === "num") {
    if (!S.inst) { flash(NUM_WHY, true); return; }
    if (S.boxMode) { $("#box-mode").checked = false; $("#box-mode").onchange(); }
    UI.setNumMode(true);               // ↓ instances.js
  } else if (t === "box") {
    if (S.numMode) UI.setNumMode(false);
    if (!$("#box-mode").checked) { $("#box-mode").checked = true; $("#box-mode").onchange(); }
  } else {
    if (S.numMode) UI.setNumMode(false);
    if ($("#box-mode").checked) { $("#box-mode").checked = false; $("#box-mode").onchange(); }
  }
  tick();
}

/* ─── ②③ 의 «저장» 을 하단 판정 줄의 «저장» 자리로 옮긴다 ───
   새 단추를 만들지 않고 **있는 단추를 그대로 옮긴다** — id·풍선말·app.js 가 붙인 onclick 이 하나도
   안 바뀐다(회귀 시험 modesim.js·boxsim.js 는 app.js 의 함수만 떼어 돌리므로 영향이 없다).
   0918 «그림판»: ①의 «저장»(#btn-save)은 ②③ 에서 **숨는다**. ②③ 에서는 붓질 자체가 막혀 있어
   마스크로 저장할 것이 없고, 하단 줄에 «저장» 이 둘 나란히 있으면 그림판처럼 단순하지 않다.
   (앞 사이클은 회색으로 두었는데, 자리는 그대로이므로 «한 칸에 그 작업의 저장 하나» 가 더 쉽다.) */
const TASKBTN = { box: ["#boxsave"], num: ["#numsave"] };
(function () {
  const slot = $("#taskbtns");
  if (!slot) return;
  Object.keys(TASKBTN).forEach((t) => TASKBTN[t].forEach((s) => {
    const b = $(s);
    if (b) { b.dataset.forTask = t; b.style.display = "none"; slot.appendChild(b); }
  }));
})();

/* 캔버스에 «지금 ② 상자 그리기입니다» 를 한 줄 띄운다(사이클4 N-K).
   상자·번호 모드는 사진을 넘겨도 켜진 채로 남는다(의도된 동작). 그 상태에서 붓질을 하면
   아무 말 없이 아무 일도 안 난다. 글자만 얹는다 — pointer-events:none 이라 조작을 막지 않는다. */
const TASKBADGE = {
  box: "② 상자 그리기 중 — 붓질은 «🎨 칠한 영역» 로",
  num: "③ 번호 편집 중 — 붓·다각형은 잠겨 있습니다"
};
function renderTaskBadge(t) {
  let el = $("#taskbadge");
  if (!el) {
    el = document.createElement("div");
    el.id = "taskbadge";
    const w = $("#canvaswrap");
    if (!w) return;
    w.appendChild(el);
  }
  el.textContent = TASKBADGE[t] || "";
  el.style.display = TASKBADGE[t] ? "" : "none";
}

/* ══ 0918 사이클5(총괄) ① — 목록 맨 위에 «지금 무슨 작업인지» 낱말 하나 ══
   사이클4 2차 §4-4 3번(넘긴 것 ③). 목록의 «☑ 내 큐»·카드의 «✔ 확정/미확정»·테두리 색은
   모두 **지금 고른 작업**의 확정을 본다(app.js loadList 의 mode · renderGrid). 그런데 목록
   화면에는 그 말이 한 글자도 없어서, ▭ 상자를 켜 둔 채 목록으로 오면 «왜 다 미확정이지» 가
   된다(2차 §2 (마) 처음 온 사람 관점). 낱말 하나(마스크·상자·번호 — 4자 이하)만 얹는다.
   새 API·새 상태 없음: curTask() 가 이미 아는 것을 그대로 적는다. */
const TASKICON = { mask: "🎨", box: "▭", num: "＃" };
function renderListTask(t) {
  let el = $("#curtask");
  if (!el) {
    const bar = document.querySelector("#view-list .bar");
    if (!bar) return;                       // 옛 index.html 에서도 조용히 넘어간다
    el = document.createElement("span");
    el.id = "curtask";
    el.className = "pill conf";
    bar.insertBefore(el, bar.firstChild);
  }
  const w = TASKWORD[t] || TASKWORD.mask;
  el.textContent = TASKICON[t] + " " + w;
  el.title = "지금 하는 작업은 «" + w + "» 입니다 — 아래 카드의 «✔ 확정 / 미확정» 과 «☑ 내 큐» 는"
    + " 이 작업의 확정을 봅니다(칠한 영역·상자·번호는 따로 셉니다)."
    + " 바꾸려면 «편집» 화면 왼쪽 맨 위 세 칸에서 고르세요.";
}

/* ══ 0921 U5 — 커서가 «지금 무슨 도구인지» 를 말한다 (그림판·포토샵 관습) ══
   지금까지 커서는 세 가지뿐이었다 — ✋이동만 `grab`, 지우개만 `cell`, **나머지 전부** `crosshair`.
   그래서 붓·다각형·자동채움·상자를 오가도 손끝은 하나도 안 바뀌었고, 특히 상자 «고르기» 는
   풍선말이 «끌어서 옮기거나 모서리로 크기를 바꿉니다» 라고 말만 할 뿐 **모서리가 어디까지인지**
   화면에 아무 표시가 없었다(손잡이 판정 반경은 배율에 따라 변한다 — boxes.js bHandleR).

   커서는 «무슨 손짓인가» 를 말하게 한다 — 도구 이름을 그리는 것이 아니다:
     붓          `crosshair`  정확한 한 점에서 끌어 그린다(원 미리보기가 크기를 같이 말한다)
     지우개      `cell`       네모 지우개 (지금 그대로)
     다각형 둘   `copy`       누르면 점이 하나 «더해진다». 채움/빼기는 **미리보기 선 색**이 이미
                              말한다(노랑=채움 · 빨강=빼기, draw()). 커서에 또 적지 않는다.
     자동채움 둘 `pointer`    끌지 않고 «한 번 누르는» 도구다. 쉬움 모드 기본 도구라서 이 하나로
                              «여기를 누르세요» 가 전해진다.
     이동·Space  `grab`  →  실제로 끄는 동안은 `grabbing` (윈도우·포토샵 손도구)
     상자        boxes.js boxCursor() — 그리기는 십자, 고르기는 상자 위 `move`·모서리 `↘↖`
   ⚠ 커서를 쓰는 자리는 **이 함수 하나뿐**이다. 전에는 두 곳(mask.js setTool · syncTaskUI)이
   각자 써서 규칙이 둘로 갈라져 있었다. 도구를 바꾸는 길은 단추·단축키·모드 전환으로 여럿이고
   그 모두가 `S.dirty = true` 로 끝나므로, U2 의 배율 %처럼 **그림 고리 한 곳**에서 갱신한다.
   같은 값이면 DOM 을 한 글자도 안 건드린다(붓질·이동으로 draw 가 도는 동안 style 을 안 쓴다). */
const MASKCUR = { brush: "crosshair", erase: "cell", polyadd: "copy", polysub: "copy",
                  smartadd: "pointer", smartsub: "pointer", pan: "grab" };
let curShown = null;
function cursorFor() {
  if (S.panning) return "grabbing";                   // 끄는 중이면 어느 작업에서나 쥔 손
  const t = curTask();
  if (S.spaceDown || (t === "mask" && S.panTool)) return "grab";
  if (t === "box") return UI.boxCursor();             // ↓ boxes.js (되돌아 부르는 자리)
  if (t === "num") return "crosshair";                // 번호 편집은 지금 그대로 둔다
  return MASKCUR[S.tool] || "crosshair";
}
function applyCursor() {
  const c = cursorFor();
  if (c === curShown) return;
  curShown = c;
  cv.style.cursor = c;
}

function syncTaskUI() {
  const t = curTask();
  const pan = document.querySelector('.tool[data-tool="pan"]');
  // 0921 U4: 더블클릭 = 화면에 맞춤. 어디서 되는지를 이 풍선말에 적는다(index.html 의 같은 title 은
  // 이 줄이 200ms 안에 덮어쓰므로 HTML 은 건드리지 않았다 — 기준선을 늘리지 않으려고).
  if (pan) { pan.disabled = t !== "mask"; pan.title = t === "mask" ? "사진을 끌어서 이동합니다 — 두 번 누르면 화면에 맞춥니다(0 키와 같습니다)" : "이 작업에서는 Space를 누른 채 사진을 끌어서 이동합니다 — 사진 밖 회색 여백을 두 번 누르면 화면에 맞춥니다"; }
  applyCursor();                            // 0921 U5 — 커서 규칙은 cursorFor() 한 곳에만 있다
  renderListTask(t);                      // 0918 사이클5 ① — 목록 맨 위 낱말
  $$(".task").forEach((b) => {
    const mine = b.dataset.task;
    b.classList.toggle("on", mine === t);
    if (mine === "num") {
      b.disabled = !S.inst;
      b.title = S.inst ? "③ 열매 번호 — 알마다 붙은 번호를 고칩니다(개수 세기용). 단축키 K" : NUM_WHY;
    }
  });
  /* 긴 안내는 화면에 글자로 내지 않는다 — 작업 3칸의 풍선말로만 둔다(#tasknote 는 숨은 원천).
     그림판에는 설명 문단이 없다. 자세한 것은 위쪽 «사용법» 과 «?» 안내에 있다. */
  const note = TASKNOTE[t] + (S.stem && !S.inst ? "\n" + NUM_WHY : "");
  const tn = $("#tasknote");
  if (tn) tn.textContent = note;
  const tb = $("#taskbar");
  if (tb) tb.title = note;
  // 고른 작업의 도구만 보이게 (판정·저장 칸은 어느 작업에서나 쓰는 것이라 늘 보인다)
  $("#toolbox").style.display = t === "mask" ? "" : "none";
  $("#boxpanel").style.display = t === "box" ? "" : "none";
  $("#numpanel").style.display = t === "num" ? "" : "none";
  $("#row-film").style.display = t === "box" ? "" : "none";
  // 판정 줄로 옮겨 둔 ②③ 저장 단추는 그 작업일 때만 보인다
  $$("#taskbtns > button").forEach((b) => { b.style.display = b.dataset.forTask === t ? "" : "none"; });
  // ①의 «저장»(마스크 수정본)은 ②③ 에서 숨는다 — 그 자리에 그 작업의 저장이 들어온다
  const bs = $("#btn-save");
  if (bs) bs.style.display = t === "mask" ? "" : "none";
  // «마스크만» 의 뜻은 작업마다 다르다 → 낱말도 바꾼다
  const vm = document.querySelector('.vsw[data-vm="mask"]');
  if (vm) {
    vm.querySelector(".tw").textContent = VWORD[t];
    vm.title = VTIP[t] + " Q 로 «원본만 → " + VWORD[t] + " → 겹쳐» 를 돌려 가며 봅니다.";
  }
  renderTaskBadge(t);
}

/* ══════════════════════════ ①-2 «보기 전환» 3단 스위치 ══════════════════════════
   그림판의 «보기» 처럼 눌러서 바꾸는 세 칸. 새 레이어를 만들지 않고 **기존 체크박스를 대신
   눌러 줄 뿐**이다 — «겹쳐» 로 돌아오면 사람이 켜 두었던 대로 되돌린다(들어갈 때 적어 둔다).
   사람이 체크박스나 사진 위 칩을 **직접** 만지면 그 순간 «겹쳐» 로 풀린다(거짓말하지 않게).

   app.js 에 넣은 것은 딱 두 줄이다: 사진만 어둡게 덮는 `S.dim` 과, «원본만» 에서 필름·상자를
   쉬게 하는 `S.hideBox`. 둘 다 기본값(0/false)에서는 아무 일도 하지 않는다. */

const VWORD = { mask: "칠한 영역만", box: "상자만", num: "번호만" };
const VTIP = {
  mask: "칠한 영역만 — 사진을 어둡게 덮고 원본 라벨·AI 제안·내 수정본만 봅니다(라벨 모양 확인용).",
  box:  "상자만 — 사진을 흰 필름으로 덮고 네모만 봅니다.",
  num:  "번호만 — 사진을 어둡게 덮고 열매 번호 색·숫자만 봅니다."
};
const VLAYERS = ["l-gt", "l-ai", "l-ed", "l-diff", "l-num", "l-numtext"];
const DIM = 0.78;                 // 사진을 얼마나 어둡게 덮을지(0 = 그대로)
/* 0918 사이클2 (사이클1 3차 판정 ②-5): 번호가 1~2개뿐인 사진의 «번호만» 이 새까만 빈 화면이
   됐다. 번호를 볼 때는 사진을 **30% 밝기**로 남긴다(0.70 을 덮으면 30% 가 남는다). */
const DIM_NUM = 0.70;
const FILM_MAX = 80;              // «상자만» 의 흰 필름 — 슬라이더 최대값

let vmode = "over";
let vsaved = null;                // 「겹쳐」 에서 사람이 켜 두었던 것
let vexpect = null;               // 우리가 만들어 둔 체크 상태(사람이 만졌는지 보는 데 쓴다)
let lastVTask = null, lastVStem = null;

const checkSig = () => VLAYERS.map((id) => { const e = $("#" + id); return e && e.checked ? 1 : 0; }).join("");

function snapshotChecks() {
  const o = { film: $("#film") ? $("#film").value : null,
              alpha: $("#alpha") ? $("#alpha").value : null,
              numalpha: $("#numalpha") ? $("#numalpha").value : null };
  VLAYERS.forEach((id) => { const e = $("#" + id); if (e) o[id] = e.checked; });
  return o;
}
function setChecks(on) {           // on = {id: true/false} · 적지 않은 것은 그대로 둔다
  Object.keys(on).forEach((id) => {
    const e = $("#" + id);
    if (e) e.checked = !!on[id];
  });
  S.dirty = true;
}
function setRange(sel, v) {           // 슬라이더를 «대신 움직인다» — 화면과 그림이 늘 같게
  const f = $(sel);
  if (!f || v == null || f.value === String(v)) return;
  f.value = v;
  if (f.oninput) f.oninput({ target: f });
}
const setFilm = (v) => setRange("#film", v);

function applyVMode() {
  const t = curTask();
  if (vmode === "over") {
    if (vsaved) {
      const o = {};
      VLAYERS.forEach((id) => { if (id in vsaved) o[id] = vsaved[id]; });
      setChecks(o);
      setFilm(vsaved.film);
      setRange("#alpha", vsaved.alpha);
      setRange("#numalpha", vsaved.numalpha);
      vsaved = null;
    }
    S.dim = 0; S.hideBox = false;
  } else {
    if (!vsaved) vsaved = snapshotChecks();
    const OFF = { "l-gt": false, "l-ai": false, "l-ed": false, "l-diff": false,
                  "l-num": false, "l-numtext": false };
    if (vmode === "photo") {
      setChecks(OFF);
      S.dim = 0; S.hideBox = true;
      setFilm(vsaved.film); setRange("#alpha", vsaved.alpha); setRange("#numalpha", vsaved.numalpha);
    } else {                       // "mask" — 뜻이 작업마다 다르다
      S.hideBox = false;
      // 「모양을 보려고」 켜는 것이므로 색을 **진하게** 올린다(겹쳐로 돌아오면 원래 값으로).
      if (t === "box") {
        setChecks(OFF);
        S.dim = 0; setFilm(FILM_MAX);
        setRange("#alpha", vsaved.alpha); setRange("#numalpha", vsaved.numalpha);
      } else if (t === "num") {
        setChecks(Object.assign({}, OFF, { "l-num": true, "l-numtext": true }));
        S.dim = DIM_NUM; setFilm(vsaved.film);
        setRange("#alpha", vsaved.alpha); setRange("#numalpha", 100);
      } else {
        setChecks(Object.assign({}, OFF, { "l-gt": true, "l-ai": true, "l-ed": true }));
        S.dim = DIM; setFilm(vsaved.film);
        setRange("#alpha", 100); setRange("#numalpha", vsaved.numalpha);
      }
    }
  }
  S.dirty = true;
  vexpect = vmode === "over" ? null : checkSig();
  $$(".vsw").forEach((b) => b.classList.toggle("on", b.dataset.vm === vmode));
}

function setVMode(v) { vmode = v; applyVMode(); tick(); }

$$(".vsw").forEach((b) => b.onclick = () => { setVMode(b.dataset.vm); b.blur(); });

/* 사람이 체크박스·칩을 직접 만졌으면 «겹쳐» 로 풀고 지금 상태를 그대로 인정한다. */
function watchVMode() {
  if (vmode === "over") return;
  if (vexpect !== null && checkSig() !== vexpect) {
    vmode = "over"; vsaved = null; S.dim = 0; S.hideBox = false; vexpect = null;
    S.dirty = true;
    $$(".vsw").forEach((b) => b.classList.toggle("on", b.dataset.vm === "over"));
  }
}

// 단축키 Q — 원본만 → 마스크만 → 겹쳐 → 원본만 …
// (V 는 ② 상자의 «고르기», X·K·D·M·N 은 이미 쓰고 있어 겹치지 않는 키로 골랐다)
const VORDER = ["photo", "mask", "over"];
function onViewModeKey(e) {                 // 등록은 keys.js (단축키 한 곳)
  if ($("#view-edit").classList.contains("hidden")) return;
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.key !== "q" && e.key !== "Q") return;
  e.preventDefault();
  setVMode(VORDER[(VORDER.indexOf(vmode) + 1) % VORDER.length]);
}

/* ══ 0921 U9 — `~` 를 **누르고 있는 동안만** «원본만» (포토샵의 «레이어 잠깐 꺼 보기») ══
   «내가 칠한 것 밑에 열매가 정말 있나» 는 검수 내내 가장 자주 하는 확인인데, 지금은 Q 를 눌러
   «원본만» 으로 갔다가 다시 두 번 눌러 «겹쳐» 로 돌아와야 한다(세 번 · 중간에 «칠한 영역만» 을
   지나간다). 포토샵은 눈을 누르고 있는 동안만 끄고 놓으면 저절로 돌아온다 — 손이 기억할 것이 없다.

   새 상태를 만들지 않는다 — 이미 있는 «보기 전환» 을 대신 눌러 줄 뿐이다(setVMode).
   그래서 «무엇을 끄고 어떻게 되돌리나»(vsaved · 필름 · 진하기)가 한 벌로 남는다.
   놓을 때 «원본만» 이 아니면 아무것도 되돌리지 않는다 — 누른 채로 사람이 Q 나 3단 스위치로
   딴 데로 갔다면 그쪽이 사람의 뜻이다.
   창을 떠나면(알트탭) keyup 이 영영 안 온다 → blur 에서도 놓은 것으로 친다.
   ⚠ `e.code === "Backquote"` 로 본다 — 자판 배열과 Shift 에 상관없이 그 한 키다
   (실측: WebDriver 로 «~» 도 «`» 도 code 는 Backquote · shiftKey 는 배열마다 다르다). */
let peekBack = null;                        // 누르기 전에 보던 모드 · null = 지금 안 누르고 있다
function peekOn() {
  if (peekBack !== null) return;            // 누르고 있으면 keydown 이 되풀이된다 — 한 번만 적는다
  if ($("#view-edit").classList.contains("hidden")) return;
  peekBack = vmode;
  if (vmode !== "photo") setVMode("photo");
}
function peekOff() {
  const back = peekBack;
  peekBack = null;
  if (back !== null && back !== "photo" && vmode === "photo") setVMode(back);
}
function onPeekKey(e) {                     // 등록은 keys.js (단축키 한 곳)
  if (e.code !== "Backquote" || e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  e.preventDefault();
  peekOn();
}
function onPeekUp(e) { if (e.code === "Backquote") peekOff(); }
window.addEventListener("blur", peekOff);   // 알트탭 — 키를 쥔 채 창을 떠나면 keyup 이 안 온다

$$(".task").forEach((b) => b.onclick = () => { setTask(b.dataset.task); b.blur(); });

/* ══════════════════════════ ③ 사진 위 레이어 칩 (= 색 범례) ══════════════════════════
   오른쪽 패널을 접어 두어도 여기서 네 겹을 껐다 켤 수 있다. 「빨강이 뭐였더라」도 여기서 풀린다.
   자리는 **오른쪽 위**다 — 왼쪽 위는 붓질을 시작하는 자리라 비워 둔다(사이클4 N8·사이클5 N-I 가
   왼쪽 위에서 붓질이 안 먹는 문제를 끝내 못 없앴다). */

const CHIP = [
  ["l-gt",   "#e8443a", "원본", "빨강 = 원본 라벨(GT). 원래 데이터셋에 있던 것 — 이것이 맞는지 보는 게 검수입니다.", () => true],
  ["l-ai",   "#2f7de1", "AI",   "파랑 = AI 제안. AI 가 1차로 그린 것입니다.", () => !!S.ai],
  ["l-ed",   "#00e5ff", "수정", "하늘색(시안) = 내 수정본. «저장» 을 눌러야 파일로 남습니다.",
    () => !!(S.edDirty || (S.item && S.item.has_fixed))],
  ["l-diff", "linear-gradient(90deg,#ffd400 50%,#ff35d0 50%)", "차이",
    "노랑 = AI 만 찾은 곳(라벨 누락 후보) · 분홍 = 원본에만 있는 곳 (D 키)", () => !!S.ai],
  ["l-num",  "conic-gradient(#e8443a,#f2c11a,#4ad16b,#3d8bff,#c46bff,#e8443a)", "번호",
    "알록달록 = 열매 번호 (J 키)", () => !!S.inst]
];

function renderLegend() {
  const el = $("#legend");
  if (!el) return;
  if (!S.img) { el.style.display = "none"; return; }
  const it = [];
  CHIP.forEach(([id, style, label, tip, when]) => {
    const cb = $("#" + id);
    if (!cb || cb.disabled || !when()) return;
    it.push('<span class="i' + (cb.checked ? "" : " off") + '" data-tgl="' + id
      + '" title="' + escapeHtml(tip + "\n(누르면 이 겹을 껐다 켭니다)") + '">'
      + '<i style="background:' + style + '"></i>' + label + "</span>");
  });
  if (S.boxMode) it.push('<span class="i" title="노란 네모 = 상자 (흰 필름 위)">'
    + '<i style="background:#ffcc33"></i>상자</span>');
  el.style.display = it.length ? "" : "none";
  el.innerHTML = it.join("");
  el.querySelectorAll("[data-tgl]").forEach((b) => b.onclick = () => {
    const cb = $("#" + b.dataset.tgl);
    if (!cb || cb.disabled) return;
    cb.checked = !cb.checked;
    // app.js 가 그 체크박스에 붙여 둔 onchange 를 그대로 부른다(다시 칠하기 규칙을 두 벌로 만들지 않게)
    if (cb.onchange) cb.onchange();
    S.dirty = true;
    tick();
  });
}

/* ══════════════════════════ ④ 오른쪽 패널 접기 (기본 접힘) ══════════════════════════ */

function setSideFold(fold) {
  const s = $("#side");
  if (!s) return;
  s.classList.toggle("fold", !!fold);
  const t = $("#sidetgl");
  if (t) {
    t.textContent = fold ? "▸" : "◂";
    t.title = (fold ? "오른쪽 칸을 펍니다" : "오른쪽 칸을 접습니다")
      + " — 보기(레이어)·이 사진(묶음·점수)·더 보기";
  }
  try { localStorage.setItem("side_fold", fold ? "1" : "0"); } catch (e) {}
}
(function () {
  let fold = true;
  try { fold = localStorage.getItem("side_fold") !== "0"; } catch (e) {}
  setSideFold(fold);
  const t = $("#sidetgl");
  if (t) t.onclick = () => { setSideFold(!$("#side").classList.contains("fold")); t.blur(); };
})();

/* ══════════════════════════ 상태 읽어서 화면 맞추기 (tick) ══════════════════════════ */

let sig = null;
function tick() {
  if (!$("#view-edit")) return;
  // 사진 이름·이전/다음은 편집 화면에서만 쓸모가 있다
  const np = $("#navphoto");
  if (np) np.style.display = $("#view-edit").classList.contains("hidden") ? "none" : "";
  // 도구 상자의 «지금 몇 개» 줄은 두 줄까지만 보인다(CSS) → 전문은 풍선말로 읽게 한다
  $$("#toolrail .railinfo, #dupinfo").forEach((e) => { if (e.title !== e.textContent) e.title = e.textContent; });
  /* «보기 전환» — 작업이나 사진이 바뀌면 다시 맞추고(«마스크만» 의 뜻이 작업마다 다르다),
     그 밖에는 «사람이 체크박스를 직접 만졌는가» 만 본다. */
  const vt = curTask();
  if (vmode !== "over" && (vt !== lastVTask || S.stem !== lastVStem)) {
    lastVTask = vt; lastVStem = S.stem;
    applyVMode();
  } else {
    lastVTask = vt; lastVStem = S.stem;
    watchVMode();
  }
  const chk = ["#l-gt", "#l-ai", "#l-ed", "#l-diff", "#l-num", "#l-inst"]
    .map((s) => { const e = $(s); return e ? (e.checked ? 1 : 0) + (e.disabled ? "d" : "") : "-"; }).join("");
  const m = S.item;
  const s = [S.stem, S.boxMode ? 1 : 0, S.numMode ? 1 : 0, S.inst ? 1 : 0, S.ai ? 1 : 0, S.img ? 1 : 0,
             m && m.status, ((S.errBy && S.errBy[S.stem]) || []).length, chk,
             (S.noteBoxes || []).length, ((m && m.dup_member_status) || []).join(","),
             S.fruit, S.edDirty ? 1 : 0, m && m.has_fixed ? 1 : 0,
             S.errBy ? Object.keys(S.errBy).length : 0,
             m && m.confirmed ? (m.confirmed.status + m.confirmed.at) : "-",
             (S.savedAt && Date.now() - S.savedAt < 6000) ? 1 : 0,
             // 0918 사이클4 — ②③ 의 하단 한 줄이 바뀌는 조건(확정·개수·저장 안 됨)
             m && m.confirmed_boxes ? (m.confirmed_boxes.status + m.confirmed_boxes.at) : "-",
             m && m.confirmed_instances ? (m.confirmed_instances.status + m.confirmed_instances.at) : "-",
             (S.boxes || []).length, S.bDirty ? 1 : 0, S.numDirty ? 1 : 0,
             S.instN == null ? "-" : S.instN,
             m && m.ai_boxes_status === undefined ? "old" : "new"].join("|");
  if (s === sig) return;
  sig = s;
  syncTaskUI();
  if (UI.renderEasyProgress) UI.renderEasyProgress();
  renderLegend();
  UI.renderTodo();                     // ↓ counts.js
  syncInstErrBtn();
}

/* ══════════════ «번호 오류» 빠른 단추는 오류 자료가 있는 과일에서만 ══════════════ */
function syncInstErrBtn() {
  const b = document.querySelector('.qf[data-qf="insterr"]');
  if (!b) return;
  b.classList.toggle("hidden", !(S.errBy && Object.keys(S.errBy).length));
}


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { cv, ctx, resizeCanvas, fitView, zoomToNote, toImg, showView, curTask, setTask, syncTaskUI, renderLegend, setSideFold, setVMode, onViewModeKey, onPeekKey, onPeekUp, tick, NUM_WHY, cursorFor, applyCursor });
})();
