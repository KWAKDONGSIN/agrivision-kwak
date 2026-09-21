/* boxes — 상자(바운딩 박스)
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 1427-1430·1434-1436·1438-1729·1731-1765줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   사진 위 «투명 필름» 에 네모를 치고 고치고 저장한다. 저장 파일은 data/<과일>/boxes/<사진>.json (원본은 건드리지 않는다).

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, who = UI.who, errMsg = UI.errMsg, ctx = UI.ctx;
const api = API.get, post = API.post;
/* ↓ 아래에 오는 파일(뒤에 실리는 것)을 되돌아 부른다 — 부를 때 찾는다.
   (`typeof cntSet === "function"` 같은 옛 가드가 그대로 살아 있어야 해서 이름을 둔다:
    node 시뮬은 이 줄을 떼어 가지 않으므로 예전처럼 «없으면 건너뛴다» 가 된다.) */
const cntSet = (...a) => UI.cntSet(...a);
const markTaskConfirmed = (...a) => UI.markTaskConfirmed(...a);
const clearTaskConfirmed = (...a) => UI.clearTaskConfirmed(...a);

/* =====================================================================
   상자(bbox) 모드 — 사진 위에 «투명 필름» 을 덮고 그 위에 네모를 친다.
   0917 요청. 저장은 data/<과일>/boxes/<파일이름>.json (원본은 안 건드림).
   ===================================================================== */

const BCOL = { fruit: "#ffcc33", bunch: "#33ccff", other: "#ff77cc" };
const BKO = { fruit: "과실·알", bunch: "송이", other: "기타" };
const HANDLE = 7;                                    // 모서리 손잡이 크기(화면 픽셀)

function bpush() { S.bundo.push(JSON.stringify(S.boxes)); if (S.bundo.length > 30) S.bundo.shift(); S.bredo.length = 0; S.bDirty = true; }
function boxUndo() {
  if (!S.bundo.length) return flash("되돌릴 상자 작업이 없습니다", true);
  bredoPush(JSON.stringify(S.boxes));                // 0921 U3: 되돌리기 전 모습을 Ctrl+Y 몫으로 남긴다
  S.boxes = JSON.parse(S.bundo.pop()); S.bsel = -1; S.dirty = true; boxInfo();
}
/* 0921 U3 — 상자 «다시하기»(Ctrl+Y). 마스크(`S.redo`)와 번호(`S.numRedoStack`)에는 있는데
   상자에만 없어서, Ctrl+Z 를 한 번 더 누른 사람은 방금 친 네모를 다시 칠 수밖에 없었다.
   ⚠ 여기서 `bpush()` 를 부르면 **안 된다** — bpush 는 «새 작업» 이라서 다시하기 갈래를 버리고
   `bDirty` 도 올린다. 다시하기는 되돌리기의 거울이므로 두 칸을 그대로 맞바꾸기만 한다
   (`bDirty` 는 양쪽 다 건드리지 않는다 — 되돌리기가 예전부터 그랬고, 둘이 서로의 반대라야 한다). */
function bredoPush(s) { S.bredo.push(s); if (S.bredo.length > 30) S.bredo.shift(); }
function boxRedo() {
  if (!S.bredo.length) return flash("다시 실행할 상자 작업이 없습니다", true);
  S.bundo.push(JSON.stringify(S.boxes)); if (S.bundo.length > 30) S.bundo.shift();
  S.boxes = JSON.parse(S.bredo.pop()); S.bsel = -1; S.dirty = true; boxInfo();
}
function boxInfo(extra) {
  const n = S.boxes.length;
  const byCls = {};
  S.boxes.forEach((b) => byCls[b.cls] = (byCls[b.cls] || 0) + 1);
  const parts = Object.keys(byCls).map((k) => `${BKO[k] || k} ${byCls[k]}`);
  $("#boxinfo").textContent = `상자 ${n}개` + (parts.length ? ` (${parts.join(", ")})` : "")
    + (S.bDirty ? " · 저장 안 됨" : "") + (extra ? " · " + extra : "");
}
function drawBoxes() {
  drawBoxGuide();                                    // 0921 U10 — 십자 안내선은 상자 «밑»에 깔린다
  const lw = Math.max(1, 1.6 / S.view.s);
  S.boxes.forEach((b, i) => {
    const [x1, y1, x2, y2] = b.xyxy;
    ctx.lineWidth = i === S.bsel ? lw * 2 : lw;
    ctx.strokeStyle = i === S.bsel ? "#ffffff" : (BCOL[b.cls] || BCOL.fruit);
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    if (i === S.bsel) {                              // 모서리 손잡이
      // 판정 반경과 «같은» 상한을 쓴다 — 많이 축소했을 때 손잡이가 상자를 삼키지 않게.
      // 그려지는 네모의 «변» = 판정 반경(전과 같은 관계: 전에는 변 HANDLE/s, 반경 HANDLE/s 였다).
      const h = bHandleR(x1, y1, x2, y2);
      ctx.fillStyle = "#ffffff";
      [[x1, y1], [x2, y1], [x1, y2], [x2, y2]].forEach(([hx, hy]) =>
        ctx.fillRect(hx - h / 2, hy - h / 2, h, h));
    }
  });
  if (S.drag && S.drag.mode === "new") {
    const [x1, y1, x2, y2] = norm(S.drag.x0, S.drag.y0, S.drag.x1, S.drag.y1);
    ctx.setLineDash([6 / S.view.s, 4 / S.view.s]);
    ctx.lineWidth = lw; ctx.strokeStyle = BCOL[$("#boxcls").value] || "#fff";
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.setLineDash([]);
  }
}
/* ══ 0921 U10 — 십자 안내선 (그림판의 «눈금»·CAD 의 crosshair) ══
   네모의 **위 변을 옆 네모의 위 변과 맞추는** 일이 상자 작업의 대부분인데, 지금 화면에는 기준선이
   하나도 없다. 커서가 어느 줄·어느 칸에 있는지는 오른쪽 `#hud` 의 «(x, y)» 숫자로만 알 수 있어서
   눈이 사진과 숫자 사이를 오간다. 커서를 지나는 가로·세로 한 줄을 사진 끝까지 그어 두면,
   손을 대기 **전에** 어디에 걸리는지가 눈으로 보인다.

   무엇을 안 했나 — 새 단추·새 단축키·새 상태를 하나도 만들지 않았다(끄고 켜는 칸도 없다).
   방해가 될 만한 자리에서는 아예 안 그리는 쪽을 골랐다:
     · «고르기·옮기기»(`S.btool !== "draw"`)에서는 안 그린다. 거기서는 손이 네모를 잡는 중이라
       선이 보탬이 안 되고, 커서도 U5 에서 `move`·`↘↖` 로 이미 딴말을 하고 있다.
     · 커서가 **사진 밖**이면 안 그린다. 거기에는 상자가 놓일 수 없다(clampX·clampY).
     · «원본만» 보기(`S.hideBox`)·마스크·번호 작업에서는 `drawBoxes()` 자체가 안 불린다(view.js).

   ⚠ 굵기를 `Math.max(1, …)` 로 묶지 않는다. 상자 테두리는 «사진의 1화소» 를 바닥으로 삼지만
   (drawBoxes 의 lw), 안내선을 그렇게 묶으면 30배로 당겼을 때 화면에서 30화소짜리 띠가 되어
   맞추려던 그 변을 덮어 버린다. 배율이 얼마든 **화면에서 늘 1 CSS 화소**가 되게 나눈다.
   ⚠ 자리는 `Math.round()` 한 정수다 — 저장되는 상자 좌표가 정수이므로(boxMouseUp 의 Math.round)
   «안내선이 가리킨 줄» 과 «실제로 놓이는 변» 이 어긋나지 않는다.
   ⚠ 흰 실선 위에 검은 점선을 겹친다. 상자 모드는 흰 필름(기본 25%)이 깔린 밝은 바탕이지만
   필름을 0 으로 내리면 어두운 사진이 그대로 나온다 — 한 색으로는 둘 다 못 이긴다.
   ⚠ 새 다시그리기를 부르지 않는다. 상자 모드는 원래 마우스가 움직일 때마다 다시 그린다
   (main.js mousemove → boxMouseMove 의 `S.dirty = true`) — 이 선은 그 그림에 얹힐 뿐이다.
   커서가 캔버스를 벗어나도 마지막 자리에 남는데, 붓 원형 미리보기(view.js)가 예전부터 그랬다. */
const GUIDEDASH = 5;                                 // 점선 한 칸(화면 CSS 화소)
function drawBoxGuide() {
  if (S.btool !== "draw" || !S.cursor) return;
  const [cx, cy] = S.cursor;
  if (cx < 0 || cy < 0 || cx > S.W || cy > S.H) return;
  const x = Math.round(cx), y = Math.round(cy), px = 1 / S.view.s;
  ctx.beginPath();
  ctx.moveTo(x, 0); ctx.lineTo(x, S.H);
  ctx.moveTo(0, y); ctx.lineTo(S.W, y);
  ctx.lineWidth = px;
  ctx.strokeStyle = "rgba(255,255,255,.55)";         // 어두운 사진(필름 0%)에서 보이는 밑줄
  ctx.stroke();
  ctx.setLineDash([GUIDEDASH * px, GUIDEDASH * px]);
  ctx.strokeStyle = "rgba(0,0,0,.6)";                // 흰 필름·밝은 사진에서 보이는 겉줄
  ctx.stroke();
  ctx.setLineDash([]);                               // 뒤에 오는 그림(상자·다각형)에 점선이 새지 않게
}

const norm = (a, b, c, d) => [Math.min(a, c), Math.min(b, d), Math.max(a, c), Math.max(b, d)];
const clampX = (v) => Math.max(0, Math.min(S.W, v));
const clampY = (v) => Math.max(0, Math.min(S.H, v));

const PICKTOL = 3;                                   // 같은 자리로 볼 최대 차이(화면 픽셀)

// 0917 사이클2: 되돌리기·«저장 안 됨» 은 상자가 «실제로» 바뀐 때만 남긴다(D4).
// mousedown 에서 붙잡아 둔 before 와 지금을 견줘 같으면 아무것도 기록하지 않는다.
function bcommit(before) {
  if (typeof before !== "string" || JSON.stringify(S.boxes) === before) return false;
  S.bundo.push(before);
  if (S.bundo.length > 30) S.bundo.shift();
  S.bredo.length = 0;                                // 0921 U3: 새로 손댔으면 «다시하기» 갈래는 버린다
  S.bDirty = true;
  return true;
}

// 0917 사이클2: 손잡이 판정 반경에 상한. 많이 축소하면(배율 0.03) HANDLE/s 가 233 이미지px 이
// 되어 상자보다 커지고, 상자 «안» 을 눌러도 언제나 크기조절로 잡혀 옮기기가 안 됐다.
// 짧은 변의 1/3 을 넘지 않게 묶는다 — 네 모서리 판정이 서로 겹치지 않는 값이다.
function bHandleR(x1, y1, x2, y2) {
  const lim = Math.min(x2 - x1, y2 - y1) / 3;
  return Math.max(0, Math.min(HANDLE / S.view.s, lim));
}

function hitBoxesAt(x, y) {                          // 이 자리에 걸치는 상자 전부, «위에 있는 것부터»
  const out = [];
  for (let i = S.boxes.length - 1; i >= 0; i--) {
    const [x1, y1, x2, y2] = S.boxes[i].xyxy;
    if (x >= x1 && x <= x2 && y >= y1 && y <= y2) out.push(i);
  }
  return out;
}
// 0917 사이클2: 겹친 상자. 전에는 맨 위 것만 잡혀 큰 상자 안의 작은 상자를 고를 수 없었다.
// «같은 자리» 를 다시 누르면 지금 고른 것 다음(= 한 칸 아래) 상자로 돌아가며 순환한다.
function hitBox(x, y) {
  const hits = hitBoxesAt(x, y);
  if (!hits.length) return -1;
  const p = S.bpick, tol = PICKTOL / S.view.s;
  const same = p && Math.abs(p.x - x) <= tol && Math.abs(p.y - y) <= tol;
  if (same && hits.length > 1) {
    const at = hits.indexOf(S.bsel);
    if (at >= 0) return hits[(at + 1) % hits.length];
  }
  return hits[0];
}
function hitHandle(i, x, y) {
  if (i < 0) return null;
  const [x1, y1, x2, y2] = S.boxes[i].xyxy;
  const r = bHandleR(x1, y1, x2, y2);
  const near = (px, py) => Math.abs(x - px) <= r && Math.abs(y - py) <= r;
  if (near(x1, y1)) return "nw"; if (near(x2, y1)) return "ne";
  if (near(x1, y2)) return "sw"; if (near(x2, y2)) return "se";
  return null;
}
/* 0921 U5 — 상자 모드의 커서. view.js cursorFor() 가 그림 고리에서 부른다.
   «고르기·옮기기» 는 풍선말로만 «모서리로 크기를 바꿉니다» 라고 말할 뿐, 손잡이가 어디까지인지
   화면에 아무 표시가 없었다 — 판정 반경 `bHandleR()` 은 배율과 상자 크기에 따라 변해서 눈으로는
   가늠이 안 된다. 그래서 **판정에 쓰는 바로 그 함수**로 커서를 고른다(둘이 어긋날 수 없다).
   ⚠ 겹친 상자를 도는 `hitBox()` 가 아니라 `hitBoxesAt()` 을 쓴다 — hitBox 는 «같은 자리를 다시
   눌렀나»(S.bpick)를 보는 **고르는 규칙**이고, 여기는 그냥 «상자 위인가» 만 알면 된다.
   자리는 마지막 마우스 자리(`S.cursor`, main.js 가 매 mousemove 에 적는다)를 그대로 쓴다. */
const CORNERCUR = { nw: "nwse-resize", se: "nwse-resize", ne: "nesw-resize", sw: "nesw-resize" };
function boxCursor() {
  if (S.drag) return S.drag.mode === "resize" ? (CORNERCUR[S.drag.corner] || "crosshair")
    : S.drag.mode === "move" ? "move" : "crosshair";
  if (S.btool !== "pick") return "crosshair";          // 그리기 — 빈 곳에서 끌어 네모를 만든다
  if (!S.cursor) return "default";
  const [x, y] = S.cursor;
  const h = hitHandle(S.bsel, x, y);
  if (h) return CORNERCUR[h];
  return hitBoxesAt(x, y).length ? "move" : "default";
}
function boxMouseDown(e, x, y) {
  if (e.button !== 0) return;
  // D4: 여기서는 되돌리기에 «쌓지» 않고 처음 모습만 붙잡아 둔다. 정말 바뀌었는지는
  // boxMouseUp 의 bcommit() 이 견준다 — 그냥 고르기만 한 클릭은 «저장 안 됨» 을 띄우지 않는다.
  const before = JSON.stringify(S.boxes);
  if (S.btool === "pick") {
    const h = hitHandle(S.bsel, x, y);
    if (h) {                                         // 크기조절: 반대쪽 모서리를 «고정점» 으로 붙잡아 둔다
      const [hx1, hy1, hx2, hy2] = S.boxes[S.bsel].xyxy;
      S.drag = { mode: "resize", corner: h, before: before,
                 ax: h.includes("w") ? hx2 : hx1, ay: h.includes("n") ? hy2 : hy1 };
      return;
    }
    const i = hitBox(x, y);
    S.bpick = { x: x, y: y };                        // 같은 자리를 다시 누르면 아래 상자로 순환
    S.bsel = i; S.dirty = true; boxInfo();           // 고르기만 하는 것은 bDirty 를 올리지 않는다
    if (i >= 0) {
      const b0 = S.boxes[i];                         // 옮기기 시작점·처음 위치를 «소수 그대로» 붙잡아 둔다(확대 상태에서 어긋나지 않게)
      S.drag = { mode: "move", px: x, py: y, bx: b0.xyxy[0], by: b0.xyxy[1], before: before,
                 bw: b0.xyxy[2] - b0.xyxy[0], bh: b0.xyxy[3] - b0.xyxy[1] };
    }
    return;
  }
  S.drag = { mode: "new", x0: clampX(x), y0: clampY(y), x1: clampX(x), y1: clampY(y), before: before };
  S.dirty = true;
}
function boxMouseMove(x, y) {
  if (!S.drag) { S.dirty = true; return; }
  if (S.drag.mode === "new") { S.drag.x1 = clampX(x); S.drag.y1 = clampY(y); }
  else if (S.drag.mode === "move" && S.bsel >= 0) {
    // 처음 잡은 위치에서의 «전체» 이동량으로 계산한다. 한 칸마다 반올림해서 더하면
    // 확대해서 볼 때(배율 2배 이상) 소수 이동량이 버려지거나 두 배로 커진다.
    const b = S.boxes[S.bsel], w = S.drag.bw, h = S.drag.bh;
    const nx = Math.round(Math.max(0, Math.min(S.W - w, S.drag.bx + (x - S.drag.px))));
    const ny = Math.round(Math.max(0, Math.min(S.H - h, S.drag.by + (y - S.drag.py))));
    b.xyxy = [nx, ny, nx + w, ny + h];               // 크기는 옮겨도 절대 안 바뀐다
  } else if (S.drag.mode === "resize" && S.bsel >= 0) {
    // 고정점(반대 모서리)과 «지금» 마우스 자리로 매번 다시 만든다. 상자에서 좌표를 다시
    // 읽어 쓰면 반대편으로 뒤집는 순간 norm() 이 순서를 바꿔 고정점을 잃어버린다.
    S.boxes[S.bsel].xyxy = norm(S.drag.ax, S.drag.ay, clampX(x), clampY(y)).map(Math.round);
  }
  S.dirty = true;
}
function boxMouseUp() {
  if (!S.drag) return;
  const before = S.drag.before;
  if (S.drag.mode === "new") {
    const [x1, y1, x2, y2] = norm(S.drag.x0, S.drag.y0, S.drag.x1, S.drag.y1);
    if (x2 - x1 >= 2 && y2 - y1 >= 2) {
      S.boxes.push({ cls: $("#boxcls").value, src: "human",
                     xyxy: [Math.round(x1), Math.round(y1), Math.round(x2), Math.round(y2)] });
      S.bsel = S.boxes.length - 1;
    }
  }
  S.drag = null;
  bcommit(before);                                   // D4: 상자가 정말 바뀐 때만 되돌리기 기록 + «저장 안 됨»
  S.dirty = true; boxInfo();
}
function delSelBox() {
  if (S.bsel < 0) return flash("지울 상자를 먼저 고르세요 (V 로 고르기)", true);
  bpush(); S.boxes.splice(S.bsel, 1); S.bsel = -1; S.dirty = true; boxInfo();
}
function setBTool(t) {
  S.btool = t;
  $$(".btool").forEach((b) => b.classList.toggle("on", b.dataset.btool === t));
  S.dirty = true;
}
// 0919: 이 사진에 팀원 상자가 몇 개 있는지 사람 말로(«박성문 12 · 임성후 11»). 없으면 빈 문자열.
function teamBoxWords(team) {
  const ks = Object.keys(team || {});
  return ks.length ? "팀원 상자 " + ks.map((k) => `${k} ${team[k]}`).join(" · ") : "";
}
function boxSeedSrc() { const e = $("#boxseedsrc"); return e ? e.value : "mask"; }
async function loadBoxes() {
  S.boxes = []; S.bsel = -1; S.bundo = []; S.bredo = []; S.bDirty = false; S.teamBoxes = null;
  if (!S.stem) return;
  const stem = S.stem;
  const j = await api(`/api/boxes?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(S.stem)}`);
  if (S.stem !== stem) return;                       // 기다리는 사이 사진이 바뀌었으면 그 화면은 건드리지 않는다
  if (j && j.ok) { S.boxes = j.boxes || []; S.teamBoxes = j.team || {}; }
  const tw = teamBoxWords(S.teamBoxes);
  if (S.boxes.length) { boxInfo("저장된 상자" + (tw ? " · " + tw : "")); S.dirty = true; return; }
  /* 0919 사용자 «상자를 친 것이 각자 데이터에 있는가»: 있다(검출 팀 자동 상자). 저장된 상자가 없는 사진은
     고른 출처(기본 박성문)의 상자를 **초벌로 미리 깔아 둔다** — 툴 방향(AI·팀 초벌 → 사람이 맞다/고침 → 저장).
     «저장 안 됨» 딱지는 올리지 않는다(사람이 아직 아무것도 안 했으므로 사진을 넘겨도 묻지 않는다). */
  /* 0919 «개수 세기» 사이클4 **M1**: 전에는 «그 사람 상자가 이 사진에 있을 때만»(S.teamBoxes[who])
     초벌을 깔았다. M1 은 «팀원 워터셰드를 우선 쓰고 **없을 때만** CC(4-연결) 폴백» 이므로 파일이
     없는 사진에서도 물어본다 — 서버가 폴백해서 번호·마스크에서 만든 초벌을 준다(`fallback_from`).
     초벌이 **무엇에서** 나왔는지는 서버가 준 `seed_source` 를 그대로 말한다(지어내지 않는다). */
  const src = boxSeedSrc();
  const who = src.startsWith("team:") ? src.slice(5) : null;
  if (who) {
    const t = await api(`/api/boxes_seed?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(S.stem)}&source=${encodeURIComponent(src)}`);
    if (S.stem !== stem) return;
    if (t && t.ok && t.n) {
      const cls = $("#boxcls").value;
      S.boxes = t.boxes.map((b) => ({ cls: b.cls || cls, src: "auto", xyxy: b.xyxy }));
      const fb = t.fallback_from ? `${who} 상자가 이 사진에 없어 대신 ` : "";
      const ss = t.seed_source ? seedSrcKo(t.seed_source) : `${who} 상자`;
      boxInfo(`${fb}${ss} ${t.n}개 초벌(저장 전) — 맞으면 Ctrl+S, 틀리면 고친 뒤 저장` + (tw ? " · " + tw : ""));
      S.dirty = true; return;
    }
  }
  boxInfo(tw);
  S.dirty = true;
}
async function saveBoxes() {
  if (!S.stem) return flash("사진을 먼저 고르세요", true);
  // D3(사이클1 3차 판정 ③): 저장 응답에 «파일에 실제로 들어간» 목록이 실려 온다.
  // 그것으로 화면을 덮어써서 «화면 = 파일» 을 지킨다(서버가 버린 상자가 화면에 남지 않게).
  const stem = S.stem;                               // 저장 중에 사람이 사진을 바꿀 수 있으니 붙잡아 둔다
  const j = await post("/api/boxes", { fruit: S.fruit, stem: S.stem, boxes: S.boxes,
                                       by: who(), note: $("#note").value });
  if (!j || !j.ok) return flash(errMsg(j, "상자 저장 실패"), true);
  if (S.stem !== stem) {                             // 다른 사진을 보고 있다 — 그 화면은 건드리지 않는다
    return flash(`상자 ${j.n_boxes}개 저장 (그 사이 사진을 바꿔 화면은 그대로 둡니다)`);
  }
  const cut = (j.dropped || 0) + (j.over || 0);
  // 0919 사이클5 2차: 0개 저장은 «저장» 이 아니라 지우기다(§5 고침 1) — 그 줄도 사실대로.
  let msg = j.n_boxes === 0 ? `저장된 상자를 지웠습니다 ${j.at} · 확정도 풀림` : `저장됨 ${j.at}`;
  if (j.dropped) msg += ` · 너무 작아 버린 것 ${j.dropped}`;
  if (j.over) msg += ` · 3,000개가 넘어 버린 것 ${j.over}`;
  if (cut) bpush();                                  // 버린 것이 있을 때만 — Ctrl+Z 로 «무엇이 사라졌나» 를 볼 수 있게
  S.boxes = j.boxes; S.bsel = -1; S.bDirty = false;  // 서버가 id 를 1부터 다시 붙이므로 고른 번호는 버린다.
                                                     // bpush() 가 bDirty 를 올리므로 반드시 그 «뒤» 에서 내린다.
  if (cut) msg += " — 화면에서도 지웠음(Ctrl+Z 로 되돌려 볼 수 있음)";
  // 0919 «개수 세기»: 0개 저장은 파일을 지우는 것이라 «없음»(null) 이다 — 0 과 구별한다.
  if (typeof cntSet === "function") cntSet("boxes", j.n_boxes === 0 ? null : j.n_boxes);
  // 0918 사이클4 결정 1: 서버가 저장과 함께 «상자 확정 = 수정함» 을 찍는다. 화면도 곧바로 맞춘다
  // (하단 한 줄이 «✔ 상자 확정» 으로 바뀌고, «내 큐» 에서 이 사진이 뒤로 간다).
  // (회귀 시험 boxsim.js 는 saveBoxes() 만 **떼어 내** node 에서 돌리므로 이 함수가 없다 —
  //  있을 때만 부른다. 브라우저에서는 늘 있다.)
  // 0919 사이클5 2차 검수(열린 문제 7): 0개로 저장하면 서버가 상자 파일을 지우고 **확정을 비운다.**
  // 화면도 사실대로 — 이미 있는 «확정이 풀렸습니다» 장치를 그대로 쓴다(새 글자 0자).
  if (typeof markTaskConfirmed === "function") {
    if (j.n_boxes === 0) clearTaskConfirmed("boxes"); else markTaskConfirmed("boxes");
  }
  boxInfo(msg);
  flash(j.n_boxes === 0 ? "상자를 지웠습니다 — 확정이 풀렸습니다"      // 0919 사이클5 2차(열린 문제 7)
                        : `상자 ${j.n_boxes}개 저장` + (cut ? ` · 버린 것 ${cut}개` : ""), !!cut);
  S.dirty = true;
}
// 서버가 정말로 무엇을 보고 상자를 만들었는지(응답 source)를 사람 말로 바꾼다
const SEEDKO = { "instances:gt": "원본 번호 칠한 영역", "instances:seed": "검출팀 초벌 번호",
                 "instances:fixed": "사람이 고친 번호", ai: "AI 제안", gt: "원본 GT",
                 "team:박성문": "박성문 상자", "team:임성후": "임성후 상자" };
/* 0919 «개수 세기» 사이클4 **M1** — 서버 `seed_source` 다섯 낱말을 사람 말로. `SEEDKO` 와 나누어
   둔 까닭: 위 `source` 는 «어느 주소로 물었나»(옛 이름, 호환용)이고 `seed_source` 는 «그 숫자가 어느
   파일에서 나왔나» 다. 개수 칸 풍선말(ui.js)도 이 표를 쓴다 — 낱말을 두 군데 두지 않는다. */
// ⚠ `team:<이름>` 은 **상자 json 과 번호본 둘 다**에 붙는 이름이다(같은 워터셰드 실행의 두 산출물).
//    그래서 «번호본» 이라고 못 박지 않는다 — 상자 초벌에서도 이 말이 그대로 나온다.
const SEEDSRCKO = { "team:박성문": "박성문 님 워터셰드 산출물(검출 팀)",
                    "team:임성후": "임성후 님 워터셰드 산출물(검출 팀)",
                    certh_gt: "CERTH 정답 송이 번호본(포도)",
                    gt_numbers: "원본 칠한 영역의 정답 번호(사과)",
                    human_fixed: "사람이 고쳐 저장한 번호본",
                    cc4: "이 툴이 이진 칠한 영역를 4-연결로 센 것(폴백)" };
function seedSrcKo(v) { return SEEDSRCKO[v] || v || ""; }
/* ⚠ `window` 를 **가드 없이** 만지지 말 것. 회귀 시험 `boxsim.js` 가 이 파일의 «saveBoxes ~
   seedBoxes» 구간을 글자 그대로 떼어 내 **node 에서** 돌린다(브라우저가 없으니 `window` 도 없다).
   2026-09-19 사이클4 1차가 여기서 `ReferenceError: window is not defined` 로 boxsim 50항목을
   통째로 죽였다 — 같은 실수를 막으려고 이유를 적어 둔다. */
if (typeof window !== "undefined") { window.SEEDSRCKO = SEEDSRCKO; window.seedSrcKo = seedSrcKo; }
async function seedBoxes() {
  if (!S.stem) return flash("사진을 먼저 고르세요", true);
  // 0919: 출처 고르기(#boxseedsrc). 팀원 상자면 그대로, «마스크» 면 예전 규칙(번호 우선 → AI → 원본 GT)
  const pick = boxSeedSrc();
  const src = pick.startsWith("team:") ? pick : (S.inst ? "inst" : (S.ai ? "ai" : "gt"));
  const seed = (s) => api(`/api/boxes_seed?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(S.stem)}&source=${encodeURIComponent(s)}`);
  let j = await seed(src);
  // 0918 UI사이클5 2차(N-L): 번호가 없는 과일에서는 «AI 제안» 을 먼저 쓰는데, AI 제안이 **빈**
  // 사진이 있다(실측: 포도 740 은 ai 0개 · 원본 GT 10개). 그 때 «덩어리가 없다» 고만 말해서
  // 사람은 원본에 열매가 그려져 있는데도 하나하나 드래그해야 했다 → 0개면 원본 GT 로 한 번 더.
  if (j && j.ok && !j.n && src === "ai") j = await seed("gt");
  if (!j || !j.ok) return flash(errMsg(j, "초벌 상자를 만들지 못했습니다"), true);
  if (!j.n) return flash("칠한 영역에 덩어리가 없어 상자를 못 만들었습니다", true);
  bpush();
  const cls = $("#boxcls").value;
  // 팀원 상자는 서버가 과일에 맞는 종류(포도=송이)를 붙여 준다 — 그것을 존중하고, 마스크 계산은 예전대로 고른 종류
  S.boxes = j.boxes.map((b) => ({ cls: (j.source.startsWith("team:") && b.cls) ? b.cls : cls, src: "auto", xyxy: b.xyxy }));
  S.bsel = -1; S.dirty = true;
  // 0919 사이클4 M1: «어느 주소로 물었나»(source) 대신 «어느 파일에서 나왔나»(seed_source)를 말한다.
  // 옛 서버는 seed_source 를 안 주므로 그 때는 예전 문구 그대로다(정적 파일이 서버보다 먼저 나간다).
  const ss = j.seed_source ? seedSrcKo(j.seed_source) : (SEEDKO[j.source] || j.source);
  const fb = j.fallback_from ? `${SEEDKO[j.fallback_from] || j.fallback_from}가 이 사진에 없어 대신 ` : "";
  boxInfo(`${fb}${ss}에서 ${j.n}개 초벌 — 사람이 고친 뒤 저장`);
  flash(`초벌 상자 ${j.n}개 (저장 전)` + (j.fallback_from ? " · 팀원 상자가 없어 칠한 영역에서 만들었습니다" : ""));
}
async function exportBoxes() {
  const j = await post("/api/boxes_export", { fruit: S.fruit });
  if (!j || !j.ok) return flash(errMsg(j, "내보내기 실패"), true);
  const stale = j.stale_txt ? ` · 상자가 없어진 낡은 txt ${j.stale_txt}개(사람이 지울 것)` : "";
  // 0919 사이클4: 2픽셀이 안 되는 상자는 저장 규칙(clean)과 같이 **내보내기에서도** 버린다
  const small = j.dropped_small ? ` · 2픽셀 미만이라 버린 상자 ${j.dropped_small}개` : "";
  // 0919 사이클4: 0줄 txt 는 검출 학습이 «이 사진에는 열매가 없다» 로 읽는다 — 조용히 내보내지 않는다
  // 0919 **사이클5**: 이제 그 사진은 **txt 를 아예 만들지 않고 건너뛴다**(`boxes.py export_boxes_to`).
  //   그래서 문장도 «빈 txt 를 지우세요» 가 아니라 «건너뛰었다» 로 바뀐다(글자 4자 줄었다).
  const empty = j.empty_txt ? ` · ⚠ 상자가 0개여서 건너뛴 사진 ${j.empty_txt}장(${(j.empty_txt_names || []).slice(0, 3).join(", ")})` : "";
  flash(`${j.n_images}장 · 상자 ${j.n_boxes}개 → ${j.yolo_dir}${stale}${small}${empty}`, !!(j.stale_txt || j.empty_txt));
  boxInfo(`내보냄: 사진 ${j.n_images} · 상자 ${j.n_boxes}${stale}${small}${empty}`);
}

$("#box-mode").onchange = () => {
  if (S.numMode && $("#box-mode").checked) {
    $("#box-mode").checked = false;
    flash("번호 편집 모드를 먼저 끄세요 (K)", true);
    return;
  }
  S.boxMode = $("#box-mode").checked;
  $("#boxpanel").style.display = S.boxMode ? "" : "none";
  if (S.boxMode) setBTool("draw");
  flash(S.boxMode ? "상자 모드 — 드래그로 네모, V 로 고르기" : "칠한 영역 모드");
  S.dirty = true;
};
$("#film").oninput = (e) => { S.film = +e.target.value / 100; $("#filmv").textContent = e.target.value + "%"; S.dirty = true; };
$$(".btool").forEach((b) => b.onclick = () => setBTool(b.dataset.btool));
$("#boxseed").onclick = seedBoxes;
// 0919 초벌 출처: 브라우저가 기억하고, 바꾸면(손댄 상자가 없을 때만) 지금 사진의 초벌을 다시 깐다
(function () {
  const e = $("#boxseedsrc"); if (!e) return;
  try { const v = localStorage.getItem("boxseedsrc"); if (v && [...e.options].some((o) => o.value === v)) e.value = v; } catch (err) {}
  e.onchange = () => {
    try { localStorage.setItem("boxseedsrc", e.value); } catch (err) {}
    if (S.bDirty) return flash("손댄 상자가 있어 그대로 둡니다 — 다음 사진부터 새 출처를 씁니다(지금 바꾸려면 ✨ 초벌)");
    loadBoxes();
  };
})();
$("#boxdel").onclick = delSelBox;
$("#boxundo").onclick = boxUndo;
/* 0921 U3: «다시하기» 단추는 만들지 않는다 — 번호 편집도 `#numundo` 하나뿐이고 다시하기는
   Ctrl+Y 로만 한다. 상자만 단추를 더하면 오히려 셋이 서로 다른 모양이 된다. */
/* 🔴 0921 S6 — 상자 저장이 도는 동안 단추를 잠근다. 두 번 보내면 늦게 온 두 번째 응답이
   첫 번째가 맞춰 놓은 화면을 다시 덮어(서버가 id 를 1부터 **또** 붙인다) 고른 상자·되돌리기
   기록이 어긋난다. 감싸는 자리를 `saveBoxes()` 밖에 둔 까닭은 api.js lockWhile 주석에. */
const boxSave = UI.lockWhile(["#boxsave"], saveBoxes);
$("#boxsave").onclick = boxSave;
$("#boxexport").onclick = exportBoxes;
$("#boxclear").onclick = () => { if (!S.boxes.length || !confirm("상자를 전부 지울까요? Ctrl+Z로 되돌릴 수 있습니다.")) return; bpush(); S.boxes = []; S.bsel = -1; S.dirty = true; boxInfo(); };
// D4 와 같은 뜻: 고른 상자의 종류가 «정말» 달라질 때만 기록한다(같은 것을 다시 고르면 아무것도 안 함).
$("#boxcls").onchange = () => {
  const v = $("#boxcls").value;
  if (S.bsel >= 0 && S.boxes[S.bsel].cls !== v) { bpush(); S.boxes[S.bsel].cls = v; S.dirty = true; boxInfo(); }
};


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
/* 0921 S6 — `saveBoxes` 는 **감싼 쪽**(boxSave)을 같은 이름으로 내놓는다. keys.js 의 Ctrl+S 와
   counts.js 의 «상자 Enter 확정»(enterConfirmTask)이 이름으로 찾아 쓰므로 그 둘도 함께 잠긴다. */
Object.assign(UI, { bpush, boxUndo, boxRedo, boxInfo, drawBoxes, delSelBox, setBTool, loadBoxes, saveBoxes: boxSave, seedBoxes, exportBoxes, seedSrcKo, boxMouseDown, boxMouseMove, boxMouseUp, hitBox, hitBoxesAt, hitHandle, bHandleR, bcommit, PICKTOL, boxCursor });
})();
