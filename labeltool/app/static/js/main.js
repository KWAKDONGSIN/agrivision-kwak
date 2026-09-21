/* main — 연결과 시작
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 80-85·892-967·1421-1424줄 · ui.js 746-747·749-759·928-931줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   여러 파일을 가로지르는 손잡이(캔버스 마우스·위쪽 탭·이름 묻기·200ms tick)를 붙이고 맨 마지막에 loadFruits() 로 시작한다. 한 파일 안에서만 쓰는 손잡이는 그 파일 끝에 있다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, flashBrief = UI.flashBrief, ensureWho = UI.ensureWho, cv = UI.cv, showView = UI.showView, toImg = UI.toImg, resizeCanvas = UI.resizeCanvas, fitView = UI.fitView, tick = UI.tick, setTask = UI.setTask, confirmLeave = UI.confirmLeave, pushUndo = UI.pushUndo, strokeTo = UI.strokeTo, flushDirty = UI.flushDirty, applyPolygon = UI.applyPolygon, smart = UI.smart, boxMouseDown = UI.boxMouseDown, boxMouseMove = UI.boxMouseMove, boxMouseUp = UI.boxMouseUp, numMouseDown = UI.numMouseDown, numMouseMove = UI.numMouseMove, numMouseUp = UI.numMouseUp, loadFruits = UI.loadFruits;
const api = API.get, post = API.post;

$$(".tab").forEach((b) => b.onclick = () => {
  const cur = $$(".tab").find((t) => t.classList.contains("on"));
  const leavingEdit = cur && cur.dataset.view === "edit" && b.dataset.view !== "edit";
  if (leavingEdit && !confirmLeave("view")) return;
  showView(b.dataset.view);
});

/* ------------------------------------------------------------- 마우스 */
cv.addEventListener("contextmenu", (e) => e.preventDefault());
cv.addEventListener("mousedown", (e) => {
  if (!S.img) return;
  const [x, y] = toImg(e);
  if (e.button === 1 || S.spaceDown || (S.panTool && !S.numMode && !S.boxMode)) { S.panning = [e.clientX, e.clientY]; e.preventDefault(); return; }
  if (S.numMode) { numMouseDown(e, x, y); return; }
  if (S.boxMode) { boxMouseDown(e, x, y); return; }
  if (S.tool === "polyadd" || S.tool === "polysub") {
    if (e.button === 2) { applyPolygon(S.poly, S.tool === "polyadd" ? 1 : 0); return; }
    S.poly.push([x, y]); S.dirty = true; return;
  }
  // 0918 사이클4: «사진 밖» 힌트를 **스마트 채우기/삭제에도** 붙인다. 이 사이클이 기본 도구를
  // «자동채움» 으로 바꿨는데(결정 2-③), 여백을 누르면 그 클릭이 그대로 서버까지 가서
  // 400 «클릭한 곳이 사진 밖입니다.» 를 받아 왔다(실측 t4_paint8 ②-4). 붓과 같은 자리에서,
  // 같은 문구로, 같은 1초짜리 힌트로 막는다 — 서버에 갈 일이 아니다.
  if ((S.tool === "smartadd" || S.tool === "smartsub")
      && (x < 0 || y < 0 || x >= S.W || y >= S.H)) {
    flashBrief("사진 밖입니다 — 격자 무늬 밖으로는 칠할 수 없습니다", true);   // 0921 S2: 1초 힌트는 api.js 로 모았다
    return;
  }
  // 0920 «그림판처럼»: 오른쪽 버튼은 «반대로». 자동채움에서 오른쪽 = 자동지움,
  // 붓에서 오른쪽 = 지우개. (그림판의 «오른쪽 버튼은 배경색» 과 같은 버릇 — 쉬움 모드에서
  // 숨긴 자동지움·지우개를 단추 없이도 쓸 수 있게 한다. 전문가 모드에서도 똑같이 된다.)
  if (S.tool === "smartadd") { smart(x, y, e.button === 2 ? 0 : 1); return; }
  if (S.tool === "smartsub") { smart(x, y, e.button === 2 ? 1 : 0); return; }
  const rightErase = (e.button === 2 && (S.tool === "brush" || S.tool === "erase"));
  if (e.button !== 0 && !rightErase) return;
  // 0918 2차 검수(새 결함): 세로 사진은 캔버스 가로의 74.6%(1366×768 실측)가 회색 여백이다.
  // 거기서 누르면 한 화소도 안 바뀌는데 pushUndo() 가 S.edDirty 를 켜서, 다음 «원본 OK» 에
  // «저장하지 않은 수정이 있습니다» 확인창이 떴다(고친 것이 하나도 없는데도).
  // → 되돌리기는 그대로 쌓되(붓질이 여백에서 시작해 사진으로 들어오는 것을 막지 않으려고),
  //   딱지는 **진짜 한 화소라도 바뀐 뒤**에만 켠다.
  // 0918 사이클2 (사이클1 3차 판정 ②-4): 여백을 눌러도 아무 일이 없으니 «왜 안 칠해지지» 가 된다.
  // 1초짜리 힌트를 띄운다(딱지·되돌리기 규칙은 그대로 — 위 주석의 N1 수정 그대로).
  if (x < 0 || y < 0 || x >= S.W || y >= S.H) {
    flashBrief("사진 밖입니다 — 격자 무늬 밖으로는 칠할 수 없습니다", true);   // 0921 S2: 위와 같은 1초 힌트
  }
  const wasDirty = S.edDirty;
  pushUndo();
  S.drawing = true; S.lastPt = null;
  S.rightErase = rightErase;                       // 0920: 오른쪽 버튼으로 시작한 붓질은 지우개
  if (!strokeTo(x, y, (S.tool === "erase" || rightErase) ? 0 : 1)) S.edDirty = wasDirty;
  flushDirty();
});
window.addEventListener("mousemove", (e) => {
  if (S.panning) {
    S.view.tx += e.clientX - S.panning[0];
    S.view.ty += e.clientY - S.panning[1];
    S.panning = [e.clientX, e.clientY]; S.dirty = true; return;
  }
  if (!S.img) return;
  const [x, y] = toImg(e);
  S.cursor = [x, y];
  $("#hud").textContent = `(${Math.round(x)}, ${Math.round(y)})  배율 ${(S.view.s * 100).toFixed(0)}%  붓 ${S.brush}`;
  if (S.numMode) { numMouseMove(x, y); return; }
  if (S.boxMode) { boxMouseMove(x, y); return; }
  // 0918 2차 검수: 여백에서 시작해 사진 안으로 끌고 들어오면 그때 딱지를 켠다
  // (mousedown 에서 켜지 않았으므로 여기서 켜야 «저장 안 한 수정» 을 놓치지 않는다).
  if (S.drawing) { if (strokeTo(x, y, (S.tool === "erase" || S.rightErase) ? 0 : 1)) S.edDirty = true; flushDirty(); }
  else S.dirty = true;
});
window.addEventListener("mouseup", () => { numMouseUp(); boxMouseUp(); S.drawing = false; S.rightErase = false; S.panning = false; S.lastPt = null; flushDirty(); });
cv.addEventListener("wheel", (e) => {
  e.preventDefault();
  if (!S.img) return;
  const r = cv.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;
  // 0919 사용자: «휠로 확대·축소하면 크기 변화가 너무 심하다» → 이벤트당 1.15배 고정을 버리고 굴린 양에 비례.
  // 한 칸(100px) ≈ 1.06배, 한 이벤트 최대 1.12배. 터치패드처럼 작은 이벤트가 잇달아 오면 그만큼만 부드럽게 움직인다.
  // Firefox 는 줄(deltaMode 1)·쪽(2) 단위로 올 수 있어 px 로 환산.
  let d = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 800 : 1);
  d = Math.max(-200, Math.min(200, d));
  const k = Math.pow(1.06, -d / 100);
  const ns = Math.max(0.03, Math.min(30, S.view.s * k));
  S.view.tx = mx - (mx - S.view.tx) * (ns / S.view.s);
  S.view.ty = my - (my - S.view.ty) * (ns / S.view.s);
  S.view.s = ns; S.dirty = true;
}, { passive: false });

/* ══ 0921 U4 — 더블클릭 = 화면에 맞춤 (윈도우 사진 뷰어·포토샵 손도구 관습) ══
   휠로 당겨 놓고 **되돌아오는 길**을 모르는 사람이 많다(0 키도 «맞춤» 단추도 눈에 안 띈다).
   그래서 «두 번 누르면 처음 크기» 라는 관습을 얹는다 — 하는 일은 0 키·«맞춤» 단추와 똑같은
   `fitView()` 하나다(세 번째 확대 방식을 만들지 않는다).

   ⚠ **사진 위에서는 그리기가 먼저다.** 캔버스 어디서나 맞춤을 걸면, 자동채움을 두 번 눌러
   본 사람(응답이 1~2초라 흔하다)·붓으로 점을 두 개 콕콕 찍은 사람의 **확대가 말없이 풀린다**.
   plan.md 의 «새 기능은 있어도 방해 안 되는 것만» 에 어긋난다. 그래서 «지금 그리는 중이 아님»
   이 글자 그대로 보장되는 두 자리에서만 듣는다:
     ① 사진 **밖**(회색 격자) — 어느 작업·어느 도구에서나. 거기는 오늘도 아무것도 안 그려진다.
     ② ✋이동 도구나 Space — 보기만 하는 손짓이다(쉬움 모드에도 ✋ 는 그대로 있다).
   다각형을 찍는 중(마스크·번호)이거나 상자를 끌던 중이면 손대지 않는다 — 그 두 가지는 사진
   밖에서도 점이 찍히고(main.js·instances.js), 화면이 갑자기 움직이면 찍던 자리를 잃는다.
   휴대폰은 touchstart 가 `preventDefault()` 를 불러 dblclick 자체가 안 온다(mobile.js) —
   두 손가락 확대와 겹칠 일이 없다. */
cv.addEventListener("dblclick", (e) => {
  if (!S.img) return;
  const [x, y] = toImg(e);
  const outside = x < 0 || y < 0 || x >= S.W || y >= S.H;
  const viewing = S.spaceDown || (S.panTool && !S.numMode && !S.boxMode);
  if (!outside && !viewing) return;
  if (S.poly.length || (S.numPoly && S.numPoly.length) || S.drag) return;
  fitView();
  flashBrief("화면에 맞췄습니다 (0 키와 같습니다)");
});

/* ------------------------------------------------------------- 시작 */
$("#who").value = localStorage.getItem("who") || "";
$("#who").onchange = () => localStorage.setItem("who", $("#who").value);
loadFruits();

setInterval(tick, 200);
tick();

/* ══ 0919 사용자 «상자 툴을 따로» — 주소 /box 로 열면 상자 전용 화면 ══
   새 화면을 만들지 않는다. 같은 index.html 을 ▭ 상자 작업으로 켜고, 마스크·번호 작업 단추를 숨긴다
   (body.boxonly — style.css). 사진을 열 때마다 app.js 가 상자 모드를 끄지 않으므로 한 번 켜면 유지된다.
   저장·확정·데이터 정리 규칙은 / 와 완전히 같다 — 같은 파일(data/<fruit>/boxes/)에 쓴다. */
if (location.pathname === "/box") {
  document.body.classList.add("boxonly");
  document.title = "상자(바운딩 박스) 툴";
  if (!S.boxMode) setTask("box");
  // X 키(상자 모드 토글)로 실수로 꺼지면 되돌려 둔다 — 이 화면은 상자만 한다
  setInterval(() => { if (!S.boxMode && !S.numMode) setTask("box"); }, 300);
}

const SAVEBTNS = "#btn-ok,#btn-ai,#btn-save,#btn-flag,#btn-exc,#numsave,#boxsave";
document.addEventListener("click", (e) => {
  if (e.target && e.target.closest && e.target.closest(SAVEBTNS)) ensureWho();
}, true);

})();
