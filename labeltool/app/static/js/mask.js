/* mask — 마스크(그림) 읽기·칠하기·저장 모양 만들기
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 298-401·721-758·760-890·969-996·998-1011줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   겹(레이어) 캔버스 만들기·칠하기, 붓·지우개·다각형·자동채움, 되돌리기(20단계), «저장 안 한 수정» 묻기, 저장용 PNG 만들기.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, errMsg = UI.errMsg, COL = UI.COL;
const api = API.get, post = API.post;

/* ------------------------------------------------------ 마스크 불러오기 */
const scratch = document.createElement("canvas");
const sctx = scratch.getContext("2d", { willReadFrequently: true });

async function fetchMaskBits(url, W, H) {
  const r = await fetch(url);
  if (!r.ok) return null;
  const blob = await r.blob();
  const bm = await createImageBitmap(blob);
  scratch.width = W; scratch.height = H;
  sctx.clearRect(0, 0, W, H);
  sctx.drawImage(bm, 0, 0);
  bm.close && bm.close();
  const d = sctx.getImageData(0, 0, W, H).data;
  const out = new Uint8Array(W * H);
  for (let i = 0, p = 0; i < out.length; i++, p += 4) out[i] = d[p] > 127 ? 1 : 0;
  return out;
}

/* 인스턴스 라벨(1,2,3,...)마다 다른 색. 황금각으로 색상을 돌려 붙은 알이 서로 구분되게 한다.
   사과 마스크는 0/255 가 아니라 «알 하나에 번호 하나»(값 1~95)라서 한 색으로 칠하면
   붙어 있는 알들이 한 덩어리로 보인다 — 교수님이 «동그랗게 채워 라벨됐다»고 보신 원인. */
const INST_PAL = (function () {
  const p = new Uint8Array(256 * 3);
  for (let v = 1; v < 256; v++) {
    const h = (v * 137.508) % 360, sat = 0.78, li = 0.56;
    const c = (1 - Math.abs(2 * li - 1)) * sat;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = li - c / 2;
    let r, g, b;
    if (h < 60) { r = c; g = x; b = 0; }
    else if (h < 120) { r = x; g = c; b = 0; }
    else if (h < 180) { r = 0; g = c; b = x; }
    else if (h < 240) { r = 0; g = x; b = c; }
    else if (h < 300) { r = x; g = 0; b = c; }
    else { r = c; g = 0; b = x; }
    p[v * 3] = Math.round((r + m) * 255);
    p[v * 3 + 1] = Math.round((g + m) * 255);
    p[v * 3 + 2] = Math.round((b + m) * 255);
  }
  return p;
})();

/* 마스크를 «원본 값 그대로» 읽는다(이진화 안 함) */
async function fetchMaskRaw(url, W, H) {
  const r = await fetch(url);
  if (!r.ok) return null;
  const bm = await createImageBitmap(await r.blob());
  scratch.width = W; scratch.height = H;
  sctx.clearRect(0, 0, W, H);
  sctx.drawImage(bm, 0, 0);
  bm.close && bm.close();
  const d = sctx.getImageData(0, 0, W, H).data;
  const out = new Uint8Array(W * H);
  for (let i = 0, p = 0; i < out.length; i++, p += 4) out[i] = d[p];
  return out;
}

function makeLayer(name, W, H) {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d", { willReadFrequently: false });
  const pix = ctx.createImageData(W, H);
  S.lay[name] = { cv, ctx, pix };
  return S.lay[name];
}

function paintLayerFull(name, bits, color) {
  const L = S.lay[name]; if (!L) return;
  const d = L.pix.data;
  const [r, g, b] = color;
  for (let i = 0, p = 0; i < bits.length; i++, p += 4) {
    if (bits[i]) { d[p] = r; d[p + 1] = g; d[p + 2] = b; d[p + 3] = 255; }
    else { d[p + 3] = 0; }
  }
  L.ctx.putImageData(L.pix, 0, 0);
}

/* 원본 GT 레이어 그리기 — 인스턴스 모드면 값마다 다른 색, 아니면 빨강 한 색 */
function paintGtLayer() {
  const L = S.lay.gt; if (!L) return;
  const inst = S.gtIsInstance && $("#l-inst").checked;
  if (!inst) { paintLayerFull("gt", S.gt, COL.gt); return; }
  const d = L.pix.data, raw = S.gtRaw;
  for (let i = 0, p = 0; i < raw.length; i++, p += 4) {
    const v = raw[i];
    if (v) { d[p] = INST_PAL[v * 3]; d[p + 1] = INST_PAL[v * 3 + 1]; d[p + 2] = INST_PAL[v * 3 + 2]; d[p + 3] = 255; }
    else d[p + 3] = 0;
  }
  L.ctx.putImageData(L.pix, 0, 0);
}

function paintDiffFull() {
  const L = S.lay.diff; if (!L) return;
  const d = L.pix.data, gt = S.gt, ai = S.ai;
  const [ar, ag, ab] = COL.add, [dr, dg, db] = COL.del;
  for (let i = 0, p = 0; i < d.length / 4; i++, p += 4) {
    const a = ai ? ai[i] : 0, g0 = gt ? gt[i] : 0;
    if (a && !g0) { d[p] = ar; d[p + 1] = ag; d[p + 2] = ab; d[p + 3] = 255; }
    else if (!a && g0) { d[p] = dr; d[p + 1] = dg; d[p + 2] = db; d[p + 3] = 255; }
    else d[p + 3] = 0;
  }
  L.ctx.putImageData(L.pix, 0, 0);
}

/* ------------------------------------------------------------- 편집 연산 */
function pushUndo() {
  if (!S.ed) return;
  S.undo.push(S.ed.slice());
  if (S.undo.length > 20) S.undo.shift();
  S.redo.length = 0;
  S.edDirty = true;              // 아직 저장 안 한 수정이 있다
}
/* 저장 안 한 수정이 있으면 물어본다.
   kind="view" = 탭만 바꾸는 것(수정은 편집 화면에 그대로 남는다)
   그 밖   = 다른 사진으로 넘어가기·같은 사진 다시 열기·판정 버튼(수정이 **사라진다**) */
function confirmLeave(kind) {
  if (S.numDirty && !confirm("저장하지 않은 «열매 번호» 편집이 있습니다.\n버리고 넘어갈까요?  (남기려면 «취소» → Ctrl+S)")) return false;
  if (S.bDirty && !confirm("저장하지 않은 상자가 있습니다.\n버리고 넘어갈까요?  (남기려면 «취소» → Ctrl+S)")) return false;
  if (!S.edDirty) return true;
  if (kind === "view") {
    return confirm("저장하지 않은 수정이 있습니다.\n그래도 다른 화면으로 갈까요?"
      + "\n(수정은 «사진 고치기» 화면에 그대로 남아 있습니다. 저장은 Ctrl+S)");
  }
  return confirm("저장하지 않은 수정이 있습니다.\n버리고 넘어갈까요?  (남기려면 «취소» → Ctrl+S 로 저장)");
}
window.addEventListener("beforeunload", (e) => {
  if (!S.edDirty && !S.numDirty) return;
  e.preventDefault(); e.returnValue = "";
});
function applyBits(bits) {
  S.ed = bits;
  paintLayerFull("ed", S.ed, COL.ed);
  S.dirty = true;
}
$("#undo").onclick = () => {
  if (!S.undo.length) return flash("되돌릴 게 없습니다", true);
  S.redo.push(S.ed.slice()); applyBits(S.undo.pop());
};
$("#redo").onclick = () => {
  if (!S.redo.length) return flash("다시 실행할 게 없습니다", true);
  S.undo.push(S.ed.slice()); applyBits(S.redo.pop());
};

let dirtyBox = null;
function markDirty(x0, y0, x1, y1) {
  if (!dirtyBox) dirtyBox = [x0, y0, x1, y1];
  else {
    dirtyBox[0] = Math.min(dirtyBox[0], x0); dirtyBox[1] = Math.min(dirtyBox[1], y0);
    dirtyBox[2] = Math.max(dirtyBox[2], x1); dirtyBox[3] = Math.max(dirtyBox[3], y1);
  }
}
function flushDirty() {
  if (!dirtyBox) return;
  const L = S.lay.ed;
  const [x0, y0, x1, y1] = dirtyBox;
  L.ctx.putImageData(L.pix, 0, 0, x0, y0, Math.max(1, x1 - x0 + 1), Math.max(1, y1 - y0 + 1));
  dirtyBox = null;
  S.dirty = true;
}

/* 원(붓) 한 번 찍기 — 바뀐 부분만 픽셀 배열에 반영 */
/* 0918 2차 검수: «진짜 한 화소라도 바뀌었나» 를 돌려준다(touched). 부르는 쪽이
   «저장 안 한 수정» 딱지를 헛되게 켜지 않으려고 쓴다 — 아래 strokeTo·mousedown 참고. */
function stamp(cx, cy, r, val) {
  const W = S.W, H = S.H, d = S.lay.ed.pix.data, ed = S.ed;
  const [cr, cg, cb] = COL.ed;
  const y0 = Math.max(0, Math.floor(cy - r)), y1 = Math.min(H - 1, Math.ceil(cy + r));
  const r2 = r * r;
  let bx0 = W, by0 = H, bx1 = 0, by1 = 0, touched = false;
  for (let y = y0; y <= y1; y++) {
    const dy = y - cy, w = Math.sqrt(Math.max(0, r2 - dy * dy));
    const x0 = Math.max(0, Math.floor(cx - w)), x1 = Math.min(W - 1, Math.ceil(cx + w));
    for (let x = x0; x <= x1; x++) {
      const i = y * W + x;
      if (ed[i] === val) continue;
      ed[i] = val;
      const p = i * 4;
      if (val) { d[p] = cr; d[p + 1] = cg; d[p + 2] = cb; d[p + 3] = 255; } else d[p + 3] = 0;
      touched = true;
      if (x < bx0) bx0 = x; if (x > bx1) bx1 = x;
      if (y < by0) by0 = y; if (y > by1) by1 = y;
    }
  }
  if (touched) markDirty(bx0, by0, bx1, by1);
  return touched;
}

function strokeTo(x, y, val) {
  const r = S.brush / 2;
  let touched = false;
  if (S.lastPt) {
    const [px, py] = S.lastPt;
    const dist = Math.hypot(x - px, y - py);
    const step = Math.max(1, r * 0.4);
    const n = Math.ceil(dist / step);
    for (let i = 1; i <= n; i++) {
      if (stamp(px + (x - px) * i / n, py + (y - py) * i / n, r, val)) touched = true;
    }
  } else if (stamp(x, y, r, val)) touched = true;
  S.lastPt = [x, y];
  return touched;                 // 0918 2차 검수: 진짜 바뀐 것이 있을 때만 참
}

/* 다각형 채우기/빼기 — 임시 캔버스에 폴리곤을 그려 bbox 만 읽어온다 */
function applyPolygon(pts, val) {
  if (pts.length < 3) { S.poly = []; S.dirty = true; return; }
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  pts.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); });
  x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0));
  x1 = Math.min(S.W - 1, Math.ceil(x1)); y1 = Math.min(S.H - 1, Math.ceil(y1));
  const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
  if (bw < 1 || bh < 1) { S.poly = []; return; }
  pushUndo();
  scratch.width = bw; scratch.height = bh;
  sctx.clearRect(0, 0, bw, bh);
  sctx.beginPath();
  sctx.moveTo(pts[0][0] - x0, pts[0][1] - y0);
  for (let i = 1; i < pts.length; i++) sctx.lineTo(pts[i][0] - x0, pts[i][1] - y0);
  sctx.closePath(); sctx.fillStyle = "#fff"; sctx.fill();
  const pd = sctx.getImageData(0, 0, bw, bh).data;
  const d = S.lay.ed.pix.data, ed = S.ed;
  const [cr, cg, cb] = COL.ed;
  for (let yy = 0; yy < bh; yy++) {
    for (let xx = 0; xx < bw; xx++) {
      if (pd[(yy * bw + xx) * 4 + 3] < 128) continue;
      const i = (y0 + yy) * S.W + (x0 + xx);
      if (ed[i] === val) continue;
      ed[i] = val;
      const p = i * 4;
      if (val) { d[p] = cr; d[p + 1] = cg; d[p + 2] = cb; d[p + 3] = 255; } else d[p + 3] = 0;
    }
  }
  markDirty(x0, y0, x1, y1); flushDirty();
  S.poly = [];
}

/* 스마트 채우기 — 서버가 연결성분을 PNG 로 돌려준다 */
async function smart(x, y, val) {
  const src = $("#smartsrc").value;
  flash("연결된 덩어리 찾는 중…");
  const j = await post("/api/component", {
    fruit: S.fruit, stem: S.stem, source: src, x: Math.round(x), y: Math.round(y)
  });
  if (!j || !j.ok) return flash(errMsg(j, "실패"), true);
  const bits = await pngToBits(j.png);
  pushUndo();
  const d = S.lay.ed.pix.data, ed = S.ed;
  const [cr, cg, cb] = COL.ed;
  for (let i = 0; i < bits.length; i++) {
    if (!bits[i] || ed[i] === val) continue;
    ed[i] = val;
    const p = i * 4;
    if (val) { d[p] = cr; d[p + 1] = cg; d[p + 2] = cb; d[p + 3] = 255; } else d[p + 3] = 0;
  }
  S.lay.ed.ctx.putImageData(S.lay.ed.pix, 0, 0);
  S.dirty = true;
  flash(`${val ? "추가" : "삭제"} 완료 (${j.n_pixels.toLocaleString()} 화소)`);
}
function pngToBits(dataurl) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => {
      scratch.width = S.W; scratch.height = S.H;
      sctx.clearRect(0, 0, S.W, S.H);
      sctx.drawImage(im, 0, 0);
      const d = sctx.getImageData(0, 0, S.W, S.H).data;
      const out = new Uint8Array(S.W * S.H);
      for (let i = 0, p = 0; i < out.length; i++, p += 4) out[i] = d[p] > 127 ? 1 : 0;
      res(out);
    };
    im.onerror = rej;
    im.src = dataurl;
  });
}

/* ------------------------------------------------------------- 도구 UI */
$$(".tool").forEach((b) => b.onclick = () => setTool(b.dataset.tool));
function setTool(t) {
  // 번호 편집과 0/255 브러시가 섞이면 저장 규칙이 꼬인다(지시서 §3-1) → 모드가 켜져 있으면 막는다
  if (S.numMode) { flash("번호 편집 모드가 켜져 있어 브러시·다각형이 잠겨 있습니다 (K 로 끄기)", true); return; }
  S.tool = t; S.poly = [];
  $$(".tool").forEach((b) => b.classList.toggle("on", b.dataset.tool === t));
  S.dirty = true;
}
/* ─── 0918 사이클4 결정 2-① «붓 크기 기억»(과일별) ───
   사과는 알이 작아 붓 6, 복숭아는 크게 — 사진을 바꿀 때마다 [ ] 를 열 번씩 두드리고 있었다.
   과일마다 마지막 값을 localStorage 에 적어 두고, 과일을 고를 때 되돌린다. 끄는 토글은 없다(yagni). */
function brushKey() { return "brush:" + (S.fruit || "-"); }
function saveBrush() { try { localStorage.setItem(brushKey(), String(S.brush)); } catch (e) {} }
function loadBrush() {
  let v = null;
  try { v = localStorage.getItem(brushKey()); } catch (e) {}
  const n = Math.max(2, Math.min(200, +v || 0));
  if (!v || !n) return;
  S.brush = n; $("#brush").value = n; $("#brushv").textContent = n; S.dirty = true;
}
$("#brush").oninput = (e) => { S.brush = +e.target.value; $("#brushv").textContent = S.brush; S.dirty = true; saveBrush(); };
$("#alpha").oninput = (e) => { S.alpha = +e.target.value / 100; $("#alphav").textContent = e.target.value + "%"; S.dirty = true; };
["#l-gt", "#l-ai", "#l-ed", "#l-diff"].forEach((s) => $(s).onchange = () => { S.dirty = true; });
$("#l-inst").onchange = () => { paintGtLayer(); S.dirty = true; };
$("#fromgt").onclick = () => { if (!S.gt) return; pushUndo(); applyBits(S.gt.slice()); flash("원본 GT 를 수정본으로 복사"); };
$("#fromai").onclick = () => { if (!S.ai) return; pushUndo(); applyBits(S.ai.slice()); flash("AI 제안을 수정본으로 복사"); };
$("#clearall").onclick = () => { if (!S.ed) return; pushUndo(); applyBits(new Uint8Array(S.W * S.H)); flash("수정본을 전부 지웠습니다"); };

/* ------------------------------------------------------------- 저장 */
function edToPngDataUrl() {
  const c = document.createElement("canvas");
  c.width = S.W; c.height = S.H;
  const cx = c.getContext("2d");
  const im = cx.createImageData(S.W, S.H);
  const d = im.data, ed = S.ed;
  for (let i = 0, p = 0; i < ed.length; i++, p += 4) {
    const v = ed[i] ? 255 : 0;
    d[p] = v; d[p + 1] = v; d[p + 2] = v; d[p + 3] = 255;
  }
  cx.putImageData(im, 0, 0);
  return c.toDataURL("image/png");
}


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { fetchMaskBits, fetchMaskRaw, makeLayer, paintLayerFull, paintGtLayer, paintDiffFull, scratch, sctx, pushUndo, confirmLeave, applyBits, flushDirty, strokeTo, applyPolygon, smart, setTool, loadBrush, edToPngDataUrl });
})();
