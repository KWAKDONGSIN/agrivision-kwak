/* instances — 열매 번호(인스턴스) 편집
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 1768-1777·1787-2018·2020-2039·2041-2334·2336-2364·2366-2434·2436-2511·2513-2538·2582-2650·2652-2664줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   16비트 번호 PNG 를 직접 풀어 읽고, 지우기·합치기·나누기·붙이기로 고치고 저장한다. 위쪽 «순수 함수» 칸(INSTCORE)은 DOM 을 쓰지 않아 node 로도 시험할 수 있다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, who = UI.who, errMsg = UI.errMsg, escapeHtml = UI.escapeHtml, makeLayer = UI.makeLayer, scratch = UI.scratch, sctx = UI.sctx, cv = UI.cv, ctx = UI.ctx;
const api = API.get, post = API.post;
/* ↓ 아래에 오는 파일(뒤에 실리는 것)을 되돌아 부른다 — 부를 때 찾는다.
   (`typeof cntSet === "function"` 같은 옛 가드가 그대로 살아 있어야 해서 이름을 둔다:
    node 시뮬은 이 줄을 떼어 가지 않으므로 예전처럼 «없으면 건너뛴다» 가 된다.) */
const cntSet = (...a) => UI.cntSet(...a);
const markTaskConfirmed = (...a) => UI.markTaskConfirmed(...a);
const clearTaskConfirmed = (...a) => UI.clearTaskConfirmed(...a);

/* =====================================================================
   열매 번호(인스턴스 ID) 편집 — 0917 검출 팀 지시서 §3-1·§3-2·§3-4
   서버: instances.py (GET /instances, /api/instance_info,
         POST /api/save_instances, /api/revert_instances, GET /api/instance_errors)

   왜 PNG 를 직접 푸는가: /instances 는 «16비트 회색 PNG» 를 그대로 준다.
   이것을 캔버스에 그려 읽으면 브라우저가 16비트를 8비트로 줄이면서 **상위 바이트만** 남긴다.
   사과 번호는 1~95 이므로 전부 0 이 되어 버린다. 그래서 zlib 풀기(DecompressionStream)로
   PNG 를 직접 해독한다. 저장은 반대로 RGBA(번호 = R + G*256)로 보낸다(서버가 둘 다 받는다).
   ===================================================================== */

/* ===INSTCORE_BEGIN=== 여기부터 «순수 함수» — DOM 을 쓰지 않는다.
   cycles/.../stage1/sim.js 가 이 블록을 그대로 떼어 node 에서 돌려 검증한다.
   (다시 구현한 사본이 아니라 실제로 배포되는 코드를 시험한다) */

/* zlib(deflate) 풀기 — 브라우저·node 에 둘 다 있는 표준 API */
async function inflateZlib(u8) {
  const ds = new DecompressionStream("deflate");
  const w = ds.writable.getWriter();
  w.write(u8); w.close();
  const rd = ds.readable.getReader();
  const parts = []; let total = 0;
  for (;;) {
    const { done, value } = await rd.read();
    if (done) break;
    parts.push(value); total += value.length;
  }
  const out = new Uint8Array(total); let o = 0;
  parts.forEach((p) => { out.set(p, o); o += p.length; });
  return out;
}

/* 회색(1채널) PNG 를 «값 그대로» 읽는다. 8비트·16비트, 필터 0~4, 인터레이스 없음. */
async function decodeGrayPng(bytes) {
  const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  if (!(b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47)) throw new Error("PNG 파일이 아닙니다");
  const be32 = (i) => (b[i] * 16777216) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3];
  let off = 8, W = 0, H = 0, bd = 8, ct = 0, inter = 0;
  const idat = [];
  while (off + 8 <= b.length) {
    const len = be32(off);
    const typ = String.fromCharCode(b[off + 4], b[off + 5], b[off + 6], b[off + 7]);
    const ds = off + 8;
    if (typ === "IHDR") { W = be32(ds); H = be32(ds + 4); bd = b[ds + 8]; ct = b[ds + 9]; inter = b[ds + 12]; }
    else if (typ === "IDAT") idat.push(b.subarray(ds, ds + len));
    else if (typ === "IEND") break;
    off = ds + len + 4;
  }
  if (!W || !H) throw new Error("PNG 머리(IHDR)를 읽지 못했습니다");
  if (inter) throw new Error("인터레이스 PNG 는 지원하지 않습니다");
  if (ct !== 0) throw new Error("회색 1채널 PNG 가 아닙니다(color type " + ct + ")");
  if (bd !== 8 && bd !== 16) throw new Error("8·16비트 PNG 만 지원합니다(bit depth " + bd + ")");
  let z;
  if (idat.length === 1) z = idat[0];
  else {
    let t = 0; idat.forEach((p) => t += p.length);
    z = new Uint8Array(t); let o = 0;
    idat.forEach((p) => { z.set(p, o); o += p.length; });
  }
  const raw = await inflateZlib(z);
  const bpp = bd === 16 ? 2 : 1;
  const stride = W * bpp;
  if (raw.length < H * (1 + stride)) throw new Error("PNG 안의 그림 자료가 모자랍니다");
  const out = new Uint16Array(W * H);
  let prev = new Uint8Array(stride), cur = new Uint8Array(stride);
  let p = 0;
  for (let y = 0; y < H; y++) {
    const ft = raw[p++];
    cur.set(raw.subarray(p, p + stride)); p += stride;
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0;
      const bb = prev[i];
      const c = i >= bpp ? prev[i - bpp] : 0;
      let v = cur[i];
      if (ft === 1) v += a;
      else if (ft === 2) v += bb;
      else if (ft === 3) v += (a + bb) >> 1;
      else if (ft === 4) {
        const pa = Math.abs(bb - c), pb = Math.abs(a - c), pc = Math.abs(a + bb - 2 * c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? bb : c);
      }
      cur[i] = v;                         // Uint8Array 라 자동으로 256 으로 나눈 나머지가 된다
    }
    const ro = y * W;
    if (bd === 16) for (let x = 0; x < W; x++) out[ro + x] = (cur[x * 2] << 8) | cur[x * 2 + 1];
    else for (let x = 0; x < W; x++) out[ro + x] = cur[x];
    const t = prev; prev = cur; cur = t;
  }
  return { w: W, h: H, data: out };
}

/* 번호 개수·최댓값·번호별 화소 수 */
function instStats(inst) {
  let maxId = 0;
  for (let i = 0; i < inst.length; i++) if (inst[i] > maxId) maxId = inst[i];
  const counts = new Uint32Array(maxId + 1);
  let fg = 0;
  for (let i = 0; i < inst.length; i++) { const v = inst[i]; if (v) { counts[v]++; fg++; } }
  let n = 0;
  for (let v = 1; v <= maxId; v++) if (counts[v]) n++;
  return { n: n, maxId: maxId, fg: fg, counts: counts };
}

/* 번호 글자를 어디에 쓸지 — 번호마다 무게중심 */
function instCentroids(inst, W, H) {
  const st = instStats(inst), m = st.maxId;
  const sx = new Float64Array(m + 1), sy = new Float64Array(m + 1);
  for (let y = 0, i = 0; y < H; y++) for (let x = 0; x < W; x++, i++) {
    const v = inst[i];
    if (v) { sx[v] += x; sy[v] += y; }
  }
  const out = [];
  for (let v = 1; v <= m; v++) if (st.counts[v]) out.push({ id: v, x: sx[v] / st.counts[v], y: sy[v] / st.counts[v], n: st.counts[v] });
  return out;
}

/* 같은 번호의 «붙어 있는 조각» 들 (4-이웃).
   사과는 잎에 가려 한 알이 여러 조각으로 떨어져 있는 것이 정상이라 조각 수를 세는 것이 중요하다. */
function componentsOfId(inst, W, H, id) {
  const vis = new Uint8Array(inst.length);
  const comps = [], stack = [];
  for (let s = 0; s < inst.length; s++) {
    if (inst[s] !== id || vis[s]) continue;
    const px = []; stack.length = 0; stack.push(s); vis[s] = 1;
    while (stack.length) {
      const i = stack.pop(); px.push(i);
      const x = i % W, y = (i - x) / W;
      if (x > 0 && inst[i - 1] === id && !vis[i - 1]) { vis[i - 1] = 1; stack.push(i - 1); }
      if (x < W - 1 && inst[i + 1] === id && !vis[i + 1]) { vis[i + 1] = 1; stack.push(i + 1); }
      if (y > 0 && inst[i - W] === id && !vis[i - W]) { vis[i - W] = 1; stack.push(i - W); }
      if (y < H - 1 && inst[i + W] === id && !vis[i + W]) { vis[i + W] = 1; stack.push(i + W); }
    }
    let sx = 0, sy = 0;
    for (let k = 0; k < px.length; k++) { const x = px[k] % W; sx += x; sy += (px[k] - x) / W; }
    comps.push({ px: px, n: px.length, cx: sx / px.length, cy: sy / px.length });
  }
  return comps;
}

/* 되돌리기용 «바뀐 화소만» 기록 (사진 한 장 통째로 복사하지 않으므로 수십 단계도 가볍다) */
function mkChanges() { return { idx: [], prev: [], next: [] }; }
function chSet(ch, inst, i, val) {
  if (inst[i] === val) return false;
  ch.idx.push(i); ch.prev.push(inst[i]); ch.next.push(val);
  inst[i] = val;
  return true;
}
function instApply(inst, ch, back) {
  if (back) { for (let k = ch.idx.length - 1; k >= 0; k--) inst[ch.idx[k]] = ch.prev[k]; }
  else { for (let k = 0; k < ch.idx.length; k++) inst[ch.idx[k]] = ch.next[k]; }
}

/* 지우기 — 그 번호의 화소 전부 배경(0) */
function opErase(inst, id) {
  if (!id) return { ok: false, reason: "지울 열매를 먼저 클릭하세요" };
  const ch = mkChanges();
  for (let i = 0; i < inst.length; i++) if (inst[i] === id) chSet(ch, inst, i, 0);
  if (!ch.idx.length) return { ok: false, reason: "그 번호의 화소가 없습니다" };
  return { ok: true, ch: ch, n: ch.idx.length, id: id };
}

/* 합치기 — B 의 화소를 A 번호로 */
function opMerge(inst, a, b) {
  if (!a || !b) return { ok: false, reason: "합칠 열매 A·B 를 차례로 클릭하세요" };
  if (a === b) return { ok: false, reason: "같은 번호끼리는 합칠 수 없습니다" };
  const ch = mkChanges();
  for (let i = 0; i < inst.length; i++) if (inst[i] === b) chSet(ch, inst, i, a);
  if (!ch.idx.length) return { ok: false, reason: "두 번째로 고른 번호의 화소가 없습니다" };
  return { ok: true, ch: ch, n: ch.idx.length, a: a, b: b };
}

/* 새로 붙이기 — 그린 영역에 새 번호. 기존 번호와 겹친 화소는 덮지 않고 뺀다. */
function opAdd(inst, pxIdx, newId) {
  const ch = mkChanges();
  let skipped = 0;
  for (let k = 0; k < pxIdx.length; k++) {
    const i = pxIdx[k];
    if (i < 0 || i >= inst.length) continue;
    if (inst[i] !== 0) { skipped++; continue; }
    chSet(ch, inst, i, newId);
  }
  if (!ch.idx.length) return { ok: false, reason: "그린 영역이 모두 기존 번호와 겹칩니다(겹친 화소는 덮지 않습니다)", skipped: skipped };
  return { ok: true, ch: ch, n: ch.idx.length, skipped: skipped, newId: newId };
}

/* 굵기 wid(1~3)px 선이 지나는 화소 번호들 */
function rasterLineIdx(x0, y0, x1, y1, wid, W, H) {
  const set = new Set();
  const r = Math.max(1, wid) / 2;
  const dist = Math.hypot(x1 - x0, y1 - y0);
  const steps = Math.max(1, Math.ceil(dist * 2));
  for (let s = 0; s <= steps; s++) {
    const cx = x0 + (x1 - x0) * s / steps, cy = y0 + (y1 - y0) * s / steps;
    const ix0 = Math.max(0, Math.floor(cx - r)), ix1 = Math.min(W - 1, Math.ceil(cx + r));
    const iy0 = Math.max(0, Math.floor(cy - r)), iy1 = Math.min(H - 1, Math.ceil(cy + r));
    for (let y = iy0; y <= iy1; y++) for (let x = ix0; x <= ix1; x++) {
      if (Math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r + 0.5) set.add(y * W + x);
    }
  }
  return set;
}

/* 나누기 — 선을 마스크에서 빼서 조각을 늘리고, 선의 한쪽 조각들에 새 번호(최대+1).
   두 조각으로 안 나뉘면 **아무것도 바꾸지 않고** 이유만 돌려준다(지시서 §3-2). */
function opSplit(inst, W, H, x0, y0, x1, y1, wid, maxId) {
  const line = rasterLineIdx(x0, y0, x1, y1, wid, W, H);
  const cnt = new Map();
  line.forEach((i) => { const v = inst[i]; if (v) cnt.set(v, (cnt.get(v) || 0) + 1); });
  if (!cnt.size) return { ok: false, reason: "선이 열매 위를 지나지 않았습니다. 열매를 가로지르게 그어 주세요" };
  let id = 0, best = 0;
  cnt.forEach((c, v) => { if (c > best) { best = c; id = v; } });
  const before = componentsOfId(inst, W, H, id).length;
  const ch = mkChanges();
  line.forEach((i) => { if (inst[i] === id) chSet(ch, inst, i, 0); });
  const comps = componentsOfId(inst, W, H, id);
  const fail = (reason) => { instApply(inst, ch, true); return { ok: false, reason: reason, id: id }; };
  if (comps.length < before + 1) {
    return fail("선이 열매를 두 조각으로 나누지 못했습니다(선을 열매 밖까지 그어 주세요). 아무것도 바꾸지 않았습니다");
  }
  const dx = x1 - x0, dy = y1 - y0;
  const sideOf = (c) => (dx * (c.cy - y0) - dy * (c.cx - x0)) >= 0 ? 1 : -1;
  const pos = [], neg = [];
  comps.forEach((c) => (sideOf(c) > 0 ? pos : neg).push(c));
  if (!pos.length || !neg.length) {
    return fail("선 한쪽에만 조각이 남아 나누지 못했습니다. 아무것도 바꾸지 않았습니다");
  }
  const newId = maxId + 1;
  let nNew = 0;
  neg.forEach((c) => c.px.forEach((i) => { if (chSet(ch, inst, i, newId)) nNew++; }));
  return { ok: true, ch: ch, id: id, newId: newId, nBefore: before, nAfter: comps.length,
           nNew: nNew, nCut: line.size };
}

/* 저장용 — 번호를 RGBA 에 담는다(번호 = R + G*256). 서버 instances.py 가 이 규칙으로 읽는다. */
function instToRGBA(inst) {
  const d = new Uint8ClampedArray(inst.length * 4);
  for (let i = 0, p = 0; i < inst.length; i++, p += 4) {
    const v = inst[i];
    d[p] = v & 255; d[p + 1] = (v >> 8) & 255; d[p + 2] = 0; d[p + 3] = 255;
  }
  return d;
}
/* ===INSTCORE_END=== 여기까지 순수 함수 */

/* ------------------------------------------------- 번호마다 다른 색 (255번을 넘어도 됨) */
const NUMCOL = new Map();
function instColor(v) {
  let c = NUMCOL.get(v);
  if (c) return c;
  const h = (v * 137.508) % 360, sat = 0.80, li = 0.55;
  const cc = (1 - Math.abs(2 * li - 1)) * sat;
  const x = cc * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = li - cc / 2;
  let r, g, b;
  if (h < 60) { r = cc; g = x; b = 0; }
  else if (h < 120) { r = x; g = cc; b = 0; }
  else if (h < 180) { r = 0; g = cc; b = x; }
  else if (h < 240) { r = 0; g = x; b = cc; }
  else if (h < 300) { r = x; g = 0; b = cc; }
  else { r = cc; g = 0; b = x; }
  c = [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
  NUMCOL.set(v, c);
  return c;
}

/* ------------------------------------------------------------- 불러오기 */
function showNumRows(on) {
  ["#row-num", "#row-numtext", "#row-numalpha", "#numpanel"].forEach((s) => {
    const el = $(s); if (el) el.style.display = on ? "" : "none";
  });
}

async function loadInstances() {
  S.inst = null; S.instOrig = null; S.instSrc = null; S.instMax = 0; S.instN = 0;
  S.numSel = []; S.numUndoStack = []; S.numRedoStack = []; S.numDirty = false;
  S.numCounts = { erase: 0, merge: 0, split: 0, add: 0 };
  S.numLine = null; S.numPoly = []; S.numBrushPx = null; S.numBrushPath = null; S.numCents = null;
  if (S.lay.num) delete S.lay.num;
  setNumMode(false, true);
  showNumRows(false);
  numInfo();
  if (!S.stem) return;
  const q = `fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(S.stem)}`;
  const info = await api("/api/instance_info?" + q);
  if (!info) return;                          // 로그인이 풀렸다
  if (!info.ok || !info.has) { S.dirty = true; return; }   // 번호가 없는 과일 — 화면은 전과 똑같다
  try {
    const r = await fetch("/instances?" + q);
    if (!r.ok) throw new Error("서버가 번호 칠한 영역를 주지 않았습니다(" + r.status + ")");
    const src = r.headers.get("X-Instance-Source") || info.source;
    const dec = await decodeGrayPng(new Uint8Array(await r.arrayBuffer()));
    if (dec.w !== S.W || dec.h !== S.H) {
      throw new Error(`번호 칠한 영역 크기(${dec.w}×${dec.h})가 사진(${S.W}×${S.H})과 다릅니다`);
    }
    S.inst = dec.data;
    S.instOrig = dec.data.slice();
    S.instSrc = src;
    const st = instStats(S.inst);
    S.instMax = st.maxId; S.instN = st.n;
    showNumRows(true);
    paintNumLayer();
  } catch (e) {
    S.inst = null;
    flash("열매 번호를 불러오지 못했습니다: " + (e && e.message ? e.message : e), true);
  }
  numInfo();
  S.dirty = true;
}

function paintNumLayer() {
  if (!S.inst) return;
  const L = S.lay.num || makeLayer("num", S.W, S.H);
  const d = L.pix.data, inst = S.inst;
  for (let i = 0, p = 0; i < inst.length; i++, p += 4) {
    const v = inst[i];
    if (v) { const c = instColor(v); d[p] = c[0]; d[p + 1] = c[1]; d[p + 2] = c[2]; d[p + 3] = 255; }
    else d[p + 3] = 0;
  }
  L.ctx.putImageData(L.pix, 0, 0);
}

function repaintNum() {
  paintNumLayer();
  S.numCents = null;
  const st = instStats(S.inst);
  S.instN = st.n;
  if (st.maxId > S.instMax) S.instMax = st.maxId;
  numInfo();
  S.dirty = true;
}

function numInfo(extra) {
  const el = $("#numinfo");
  if (!el) return;
  const srcEl = $("#numsrc");
  if (!S.inst) {
    el.textContent = "";
    if (srcEl) srcEl.textContent = "";
    return;
  }
  const srcKo = { fixed: "사람이 고친 번호", seed: "검출팀 초벌(블루베리·복숭아 워터셰드)", gt: "원본 번호 칠한 영역" }[S.instSrc] || S.instSrc || "";
  if (srcEl) srcEl.textContent = "— " + srcKo;
  const c = S.numCounts;
  const sel = S.numSel.length ? ` · 고른 번호 ${S.numSel.join(" → ")}` : "";
  el.textContent = `번호 ${S.instN}개 (최대 ${S.instMax}) · 지움 ${c.erase} 합침 ${c.merge} 나눔 ${c.split} 추가 ${c.add}`
    + ` · 되돌리기 ${S.numUndoStack.length}단계` + (S.numDirty ? " · 저장 안 됨" : "") + sel
    + (extra ? " · " + extra : "");
}

/* ------------------------------------------------------------- 모드·도구 */
function setNumMode(on, silent) {
  if (on && !S.inst) {
    if (!silent) flash("이 사진에는 열매 번호가 없습니다", true);
    const cb = $("#num-mode"); if (cb) cb.checked = false;
    return;
  }
  if (on && S.boxMode) { $("#box-mode").checked = false; $("#box-mode").onchange(); }
  S.numMode = !!on;
  const cb = $("#num-mode"); if (cb) cb.checked = S.numMode;
  const lock = S.numMode;
  // 0/255 브러시 편집과 번호 편집이 섞이면 저장 규칙이 꼬인다 → 모드가 켜져 있으면 잠근다(§3-1)
  $$(".tool").forEach((b) => { b.disabled = lock; b.classList.toggle("locked", lock); });
  $("#box-mode").disabled = lock;
  $("#fromgt").disabled = lock;
  $("#clearall").disabled = lock;
  $("#btn-save").disabled = lock;
  const hasProp = !!(S.item && S.item.has_proposal);
  $("#fromai").disabled = lock || !hasProp;
  $("#btn-ai").disabled = lock || !hasProp;
  const np = $("#numpanel"); if (np) np.classList.toggle("numlock", lock);
  if (lock) { S.poly = []; }
  S.numSel = []; clearPending();
  if (!silent) {
    flash(lock ? "번호 편집 모드 — 브러시·다각형·수정본 저장이 잠깁니다 (K 로 끄기)"
               : "번호 편집 모드를 껐습니다 — 브러시를 다시 쓸 수 있습니다");
  }
  numInfo();
  S.dirty = true;
}

function setNTool(t) {
  S.ntool = t;
  $$(".ntool").forEach((b) => b.classList.toggle("on", b.dataset.ntool === t));
  clearPending();
  S.dirty = true;
}

function clearPending() {
  S.numLine = null; S.numPoly = []; S.numBrushPx = null; S.numBrushPath = null;
  S.dirty = true;
}
function hasPendingRegion() {
  return (S.numPoly && S.numPoly.length >= 3) || (S.numBrushPx && S.numBrushPx.size > 0);
}

/* ------------------------------------------------------------- 편집 동작 */
function idAt(x, y) {
  if (!S.inst) return 0;
  const xi = Math.floor(x), yi = Math.floor(y);
  if (xi < 0 || yi < 0 || xi >= S.W || yi >= S.H) return 0;
  return S.inst[yi * S.W + xi];
}

function pushNumUndo(ch, kind) {
  S.numUndoStack.push({ ch: ch, kind: kind });
  if (S.numUndoStack.length > 40) S.numUndoStack.shift();   // 지시서 요구 10단계 이상
  S.numRedoStack.length = 0;
  S.numDirty = true;
}
function numUndo() {
  if (!S.numUndoStack.length) return flash("되돌릴 번호 편집이 없습니다", true);
  const u = S.numUndoStack.pop();
  instApply(S.inst, u.ch, true);
  S.numRedoStack.push(u);
  if (u.kind && S.numCounts[u.kind] > 0) S.numCounts[u.kind]--;
  S.numDirty = S.numUndoStack.length > 0;
  repaintNum();
  flash("번호 편집을 한 단계 되돌렸습니다 (남은 단계 " + S.numUndoStack.length + ")");
}
function numRedo() {
  if (!S.numRedoStack.length) return flash("다시 실행할 번호 편집이 없습니다", true);
  const u = S.numRedoStack.pop();
  instApply(S.inst, u.ch, false);
  S.numUndoStack.push(u);
  if (u.kind) S.numCounts[u.kind] = (S.numCounts[u.kind] || 0) + 1;
  S.numDirty = true;
  repaintNum();
  flash("번호 편집을 다시 실행했습니다");
}

function runNumOp(res, kind, msg) {
  if (!res || !res.ok) { flash((res && res.reason) || "할 수 없습니다", true); return false; }
  pushNumUndo(res.ch, kind);
  if (res.newId && res.newId > S.instMax) S.instMax = res.newId;
  S.numCounts[kind] = (S.numCounts[kind] || 0) + 1;
  repaintNum();
  flash(msg);
  return true;
}

function doErase(id) {
  const r = opErase(S.inst, id);
  if (runNumOp(r, "erase", `번호 ${id} 을(를) 지웠습니다 (${(r.n || 0).toLocaleString()} 화소)`)) S.numSel = [];
  numInfo();
}
function doMerge(a, b) {
  const r = opMerge(S.inst, a, b);
  if (runNumOp(r, "merge", `번호 ${b} 를 번호 ${a} 로 합쳤습니다 (${(r.n || 0).toLocaleString()} 화소)`)) S.numSel = [a];
  numInfo();
}
function doSplit() {
  const L = S.numLine;
  if (!L) return flash("나눌 열매 위에 선을 드래그한 뒤 X 를 누르세요", true);
  if (Math.hypot(L.x1 - L.x0, L.y1 - L.y0) < 3) { S.numLine = null; return flash("선이 너무 짧습니다", true); }
  const wid = +($("#numline") ? $("#numline").value : 2);
  const r = opSplit(S.inst, S.W, S.H, L.x0, L.y0, L.x1, L.y1, wid, S.instMax);
  runNumOp(r, "split", r && r.ok
    ? `번호 ${r.id} 를 나눠 새 번호 ${r.newId} 를 붙였습니다 (조각 ${r.nBefore}→${r.nAfter}, 새 쪽 ${r.nNew.toLocaleString()} 화소)`
    : "");
  S.numLine = null;
  S.dirty = true;
}
function polyRegionPx(pts) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  pts.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); });
  x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0));
  x1 = Math.min(S.W - 1, Math.ceil(x1)); y1 = Math.min(S.H - 1, Math.ceil(y1));
  const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
  if (bw < 1 || bh < 1) return [];
  scratch.width = bw; scratch.height = bh;
  sctx.clearRect(0, 0, bw, bh);
  sctx.beginPath();
  sctx.moveTo(pts[0][0] - x0, pts[0][1] - y0);
  for (let i = 1; i < pts.length; i++) sctx.lineTo(pts[i][0] - x0, pts[i][1] - y0);
  sctx.closePath(); sctx.fillStyle = "#fff"; sctx.fill();
  const pd = sctx.getImageData(0, 0, bw, bh).data;
  const out = [];
  for (let yy = 0; yy < bh; yy++) for (let xx = 0; xx < bw; xx++) {
    if (pd[(yy * bw + xx) * 4 + 3] >= 128) out.push((y0 + yy) * S.W + (x0 + xx));
  }
  return out;
}
function doAdd() {
  let px = null;
  if (S.numBrushPx && S.numBrushPx.size) px = Array.from(S.numBrushPx);
  else if (S.numPoly.length >= 3) px = polyRegionPx(S.numPoly);
  if (!px || !px.length) return flash("먼저 다각형(클릭) 이나 브러시(드래그) 로 영역을 그리세요", true);
  const r = opAdd(S.inst, px, S.instMax + 1);
  runNumOp(r, "add", r && r.ok
    ? `새 번호 ${r.newId} 를 붙였습니다 (${r.n.toLocaleString()} 화소, 기존 번호와 겹쳐 뺀 화소 ${r.skipped.toLocaleString()})`
    : "");
  clearPending();
}

/* ------------------------------------------------------------- 마우스 (번호 편집 모드) */
function numMouseDown(e, x, y) {
  if (!S.inst) return;
  if (S.ntool === "split") {
    if (e.button !== 0) return;
    S.numLine = { x0: x, y0: y, x1: x, y1: y, drag: true };
    S.dirty = true;
    return;
  }
  if (S.ntool === "add") {
    const shape = $("#numshape") ? $("#numshape").value : "poly";
    if (shape === "poly") {
      if (e.button === 2) { doAdd(); return; }     // 오른쪽 버튼 = 다각형 마치기
      S.numPoly.push([x, y]); S.dirty = true;
      return;
    }
    if (e.button !== 0) return;
    if (!S.numBrushPx) { S.numBrushPx = new Set(); S.numBrushPath = []; }
    S.numBrushing = true;
    numBrushTo(x, y);
    return;
  }
  // 지우기·합치기 — 클릭은 «고르기» 만 하고 실제 편집은 D·M 키로 한다(지시서 §3-2 의 조작 순서)
  if (e.button !== 0) return;
  const id = idAt(x, y);
  if (!id) { flash("번호가 있는 열매를 클릭하세요", true); return; }
  if (S.ntool === "merge") {
    if (S.numSel.length >= 2) S.numSel = [];
    if (S.numSel.length === 1 && S.numSel[0] === id) { flash("다른 열매를 클릭하세요(같은 번호입니다)", true); return; }
    S.numSel.push(id);
    flash(S.numSel.length === 1 ? `A = 번호 ${id} · 이제 합칠 B 를 클릭하세요` : `B = 번호 ${id} · M 을 누르면 ${S.numSel[0]} 로 합칩니다`);
  } else {
    S.numSel = [id];
    flash(`번호 ${id} 를 골랐습니다 · D 를 누르면 지웁니다`);
  }
  numInfo();
  S.dirty = true;
}
function numBrushTo(x, y) {
  const r = Math.max(1, S.brush / 2);
  const ix0 = Math.max(0, Math.floor(x - r)), ix1 = Math.min(S.W - 1, Math.ceil(x + r));
  const iy0 = Math.max(0, Math.floor(y - r)), iy1 = Math.min(S.H - 1, Math.ceil(y + r));
  for (let yy = iy0; yy <= iy1; yy++) for (let xx = ix0; xx <= ix1; xx++) {
    if (Math.hypot(xx + 0.5 - x, yy + 0.5 - y) <= r) S.numBrushPx.add(yy * S.W + xx);
  }
  S.numBrushPath.push([x, y]);
  S.dirty = true;
}
function numMouseMove(x, y) {
  if (S.numLine && S.numLine.drag) { S.numLine.x1 = x; S.numLine.y1 = y; S.dirty = true; return; }
  if (S.numBrushing && S.numBrushPx) { numBrushTo(x, y); return; }
  S.dirty = true;
}
function numMouseUp() {
  if (S.numLine && S.numLine.drag) {
    S.numLine.drag = false;
    if (Math.hypot(S.numLine.x1 - S.numLine.x0, S.numLine.y1 - S.numLine.y0) < 3) S.numLine = null;
    else flash("X 를 누르면 이 선을 경계로 나눕니다 (Esc = 취소)");
  }
  if (S.numBrushing) {
    S.numBrushing = false;
    if (S.numBrushPx && S.numBrushPx.size) flash("N 을 누르면 그린 영역에 새 번호를 붙입니다 (Esc = 취소)");
  }
  S.dirty = true;
}

/* ------------------------------------------------------------- 단축키 (모드가 켜져 있을 때만) */
function numKey(e) {
  const k = (e.key || "").toLowerCase();
  if (k === "d") {
    if (S.numSel.length) doErase(S.numSel[S.numSel.length - 1]);
    else { setNTool("erase"); flash("지울 열매를 클릭한 뒤 다시 D 를 누르세요"); }
    return true;
  }
  if (k === "m") {
    if (S.numSel.length >= 2) doMerge(S.numSel[0], S.numSel[1]);
    else { setNTool("merge"); flash("합칠 A 를 클릭하고 B 를 클릭한 뒤 M 을 누르세요"); }
    return true;
  }
  if (k === "x") {                       // 번호 편집 모드에서만 «나누기» (상자 모드 토글과의 충돌 해결)
    if (S.numLine) doSplit();
    else { setNTool("split"); flash("나눌 열매 위에 선을 드래그한 뒤 X 를 누르세요"); }
    return true;
  }
  if (k === "n") {
    if (hasPendingRegion()) doAdd();
    else { setNTool("add"); flash("새 열매 영역을 다각형(클릭)·브러시(드래그)로 그린 뒤 N 을 누르세요"); }
    return true;
  }
  if (k === "k") { setNumMode(false); return true; }
  if (k === "j") { $("#l-num").checked = !$("#l-num").checked; S.dirty = true; return true; }
  if (e.key === "Escape") { clearPending(); S.numSel = []; numInfo(); flash("그리던 것을 취소했습니다"); return true; }
  if (e.key === "Enter") { if (hasPendingRegion()) doAdd(); return true; }
  return false;
}

/* ------------------------------------------------------------- 화면에 겹쳐 그리기 */
function drawNumOverlay() {
  if (!S.inst) return;
  const s = S.view.s;
  // 번호 글자
  if ($("#l-num").checked && $("#l-numtext").checked) {
    if (!S.numCents) S.numCents = instCentroids(S.inst, S.W, S.H);
    const dpr = cv._dpr || 1;
    const vx0 = -S.view.tx / s, vy0 = -S.view.ty / s;
    const vx1 = (cv.width / dpr - S.view.tx) / s, vy1 = (cv.height / dpr - S.view.ty) / s;
    const fs = Math.max(7, 13 / s);
    ctx.font = `bold ${fs}px sans-serif`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.lineWidth = Math.max(0.6, 2.5 / s);
    ctx.strokeStyle = "rgba(0,0,0,.85)";
    ctx.fillStyle = "#ffffff";
    S.numCents.forEach((c) => {
      if (c.x < vx0 || c.x > vx1 || c.y < vy0 || c.y > vy1) return;
      const t = String(c.id);
      ctx.strokeText(t, c.x, c.y);
      ctx.fillText(t, c.x, c.y);
    });
    ctx.textAlign = "start"; ctx.textBaseline = "alphabetic";
  }
  // 고른 번호 표시
  if (S.numSel.length && S.numCents) {
    ctx.lineWidth = Math.max(1, 2.5 / s);
    S.numSel.forEach((id, k) => {
      const c = S.numCents.find((z) => z.id === id);
      if (!c) return;
      ctx.beginPath();
      ctx.arc(c.x, c.y, Math.max(6, 16 / s), 0, Math.PI * 2);
      ctx.strokeStyle = k === 0 ? "#ffffff" : "#ffe14d";
      ctx.stroke();
    });
  }
  if (!S.numMode) return;
  // 나누는 선
  if (S.numLine) {
    ctx.beginPath();
    ctx.moveTo(S.numLine.x0, S.numLine.y0);
    ctx.lineTo(S.numLine.x1, S.numLine.y1);
    ctx.lineWidth = Math.max(1, (+($("#numline") ? $("#numline").value : 2)) );
    ctx.strokeStyle = "#ff3b3b";
    ctx.stroke();
  }
  // 새로 붙이기 미리보기
  if (S.numPoly.length) {
    ctx.beginPath();
    ctx.moveTo(S.numPoly[0][0], S.numPoly[0][1]);
    for (let i = 1; i < S.numPoly.length; i++) ctx.lineTo(S.numPoly[i][0], S.numPoly[i][1]);
    ctx.closePath();
    ctx.lineWidth = Math.max(1, 2 / s);
    ctx.strokeStyle = "#00e5ff";
    ctx.stroke();
  }
  if (S.numBrushPath && S.numBrushPath.length) {
    ctx.fillStyle = "rgba(0,229,255,.45)";
    const r = Math.max(1, S.brush / 2);
    S.numBrushPath.forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); });
  }
  if (S.cursor && S.ntool === "add" && $("#numshape") && $("#numshape").value === "brush") {
    ctx.beginPath();
    ctx.arc(S.cursor[0], S.cursor[1], S.brush / 2, 0, Math.PI * 2);
    ctx.lineWidth = Math.max(1, 1.5 / s);
    ctx.strokeStyle = "#00e5ff";
    ctx.stroke();
  }
}

/* 검출 팀이 확인한 «번호 오류» 상자를 점선으로 (지시서 §3-4) */
const VERDICT_KO = {
  ok_one_apple: "한 알 맞음", unclear: "사람 확인 필요",
  duplicate_polygon: "다각형 겹침 띠 → 지우기",
  border_artifact: "가장자리 잡티 → 지우기",
  one_apple_two_ids: "한 알이 두 번호 → 합치기",
  two_apples_one_id: "한 번호에 두 알 → 나누기"
};
const VERDICT_SHORT = {
  ok_one_apple: "한 알 맞음", unclear: "미판정",
  duplicate_polygon: "겹침띠", border_artifact: "잡티",
  one_apple_two_ids: "두번호", two_apples_one_id: "두알"
};
/* 「문제 있음」 메모 안의 후보 좌표를 상자로 (0917 ab사이클2 P4).
   3차 판정이 남긴 메모 형식: «… 라벨 안 된 사과 후보 1개(x1,y1,x2,y2: 774,1418,826,1487) — …»
   (여러 개면 `/` 로 이어진다). 사진이 1080×1920 인데 화면에서는 350px 라, 52×69px 짜리 후보를
   좌표만 보고 눈으로 찾는 것은 사실상 불가능했다. 아래 drawErrBoxes 가 노란 점선으로 그린다. */
function noteBoxes(note) {
  const m = String(note || "").match(/x1\s*,\s*y1\s*,\s*x2\s*,\s*y2\s*:\s*([0-9,\s/]+)/);
  if (!m) return [];
  return m[1].split("/").map((p) => p.trim().split(/\s*,\s*/).map(Number))
    .filter((a) => a.length === 4 && a.every((v) => isFinite(v)))
    .map((a, i) => ({ box: a, label: "후보 " + (i + 1) }));
}

function drawErrBoxes() {
  drawNoteBoxes();
  const rows = (S.errRows || []).concat($("#team-suspect")?.checked ? (S.teamSuspects || []) : []);
  if (!rows.length) return;
  const s = S.view.s;
  const fs = Math.max(8, 12 / s);
  ctx.save();
  ctx.setLineDash([7 / s, 5 / s]);
  ctx.lineWidth = Math.max(1, 2 / s);
  ctx.strokeStyle = "#ff2f2f";
  ctx.font = `bold ${fs}px sans-serif`;
  ctx.textBaseline = "bottom";
  rows.forEach((r) => {
    if (!r.box) return;
    const pad = Math.max(4, 8 / s);
    const x0 = r.box[0] - pad, y0 = r.box[1] - pad;
    const w = (r.box[2] - r.box[0]) + 2 * pad, h = (r.box[3] - r.box[1]) + 2 * pad;
    ctx.strokeRect(x0, y0, w, h);
    const t = `${r.source ? "의심 · " : ""}${VERDICT_SHORT[r.verdict] || r.verdict || ""} #${r.inst_ids || ""}`;
    const tw = ctx.measureText(t).width;
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(0,0,0,.65)";
    ctx.fillRect(x0, y0 - fs * 1.35, tw + 6 / s, fs * 1.35);
    ctx.fillStyle = "#fff";
    ctx.fillText(t, x0 + 3 / s, y0 - fs * 0.2);
    ctx.setLineDash([7 / s, 5 / s]);
  });
  ctx.restore();
}

/* 위 noteBoxes() 가 찾은 «라벨 안 된 열매 후보» — 검출 팀 CSV 상자(빨강)와 구분되게 노랑으로.
   그리는 방법은 위와 같다(점선 + 검은 바탕에 글자). */
function drawNoteBoxes() {
  if (!S.noteBoxes || !S.noteBoxes.length) return;
  const s = S.view.s, fs = Math.max(8, 12 / s), pad = Math.max(4, 8 / s);
  ctx.save();
  ctx.setLineDash([7 / s, 5 / s]);
  ctx.lineWidth = Math.max(1, 2 / s);
  ctx.strokeStyle = "#ffd400";
  ctx.font = `bold ${fs}px sans-serif`;
  ctx.textBaseline = "bottom";
  S.noteBoxes.forEach((r) => {
    const x0 = r.box[0] - pad, y0 = r.box[1] - pad;
    ctx.strokeRect(x0, y0, (r.box[2] - r.box[0]) + 2 * pad, (r.box[3] - r.box[1]) + 2 * pad);
    ctx.setLineDash([]);
    const tw = ctx.measureText(r.label).width;
    ctx.fillStyle = "rgba(0,0,0,.65)";
    ctx.fillRect(x0, y0 - fs * 1.35, tw + 6 / s, fs * 1.35);
    ctx.fillStyle = "#ffd400";
    ctx.fillText(r.label, x0 + 3 / s, y0 - fs * 0.2);
    ctx.setLineDash([7 / s, 5 / s]);
  });
  ctx.restore();
}

/* ------------------------------------------------------------- 오류 CSV */
async function ensureErrRows() {
  if (S.errFruit === S.fruit) return S.errBy;
  const j = await api("/api/instance_errors?fruit=" + encodeURIComponent(S.fruit));
  S.errBy = (j && j.ok && j.by_stem) || {};
  S.errFruit = S.fruit;
  return S.errBy;
}
async function renderErrRows() {
  const el = $("#numerr");
  S.errRows = [];
  if (el) el.innerHTML = "";
  if (!S.stem) return;
  await ensureErrRows();
  const rows = S.errBy[S.stem] || [];
  S.errRows = rows;
  if (el && rows.length) {
    el.innerHTML = `<b>검출 팀이 확인한 번호 오류 ${rows.length}건</b>` + rows.map((r) =>
      `<div class="er"><b>${escapeHtml(VERDICT_KO[r.verdict] || r.verdict || "")}</b>`
      + ` · 번호 <span class="ids">${escapeHtml(r.inst_ids || "")}</span>`
      + (r.box ? ` · 상자 (${r.box.join(", ")})` : "")
      + (r.note ? `<br><span class="muted">${escapeHtml(r.note)}</span>` : "")
      + `</div>`).join("");
  }
  S.dirty = true;
}

/* ------------------------------------------------------------- 저장·되돌리기 */
async function saveInstances() {
  if (!S.inst) return flash("이 사진에는 열매 번호가 없습니다", true);
  /* 0919 사이클5 **2차 검수**(1차 열린 문제 22 · 실측 r1_risks B-2·B-3·B-5): 번호를 **0개로**
     지우고 저장하면 화면이 아무 말도 하지 않은 채 ① 번호가 «수정함» 으로 확정되고 ② 서버가
     이진 마스크(masks_fixed)까지 **비운다**(실측: 전경 1,180화소 → 0화소) ③ 마스크를 «원본 OK»
     로 확정해 둔 사진이면 «사람 확정만» 내보내기에 **빈 마스크**가 그대로 나간다.
     ⛔ 확인창은 **쓰지 않습니다**: 사이클4 2차의 회귀 시험 `s1_flow` 나-4·나-5 가
     «번호 1개를 지워 0개로 만들고 저장하면 confirmed_instances=fixed» 를 **정상 동작으로 못박고**
     있어서(실측: 확인창을 넣자 그 묶음이 26/0 → 25/1 + 시험 중단) 화면에서 물어볼 수 없었습니다.
     → **0919 사이클5 3차 결정 1**: 막는 것은 **서버**(`instances.py api_save_instances` 가 400 ·
     이진 전경이 있는데 번호가 0개면) 이고, 화면은 그 문구를 1초 힌트로만 보여 줍니다(아래 오류 갈래).
     기대값 나-4·나-5 는 그 결정의 주석과 함께 갱신했습니다. */
  const c = document.createElement("canvas");
  c.width = S.W; c.height = S.H;
  const cx = c.getContext("2d");
  const im = cx.createImageData(S.W, S.H);
  im.data.set(instToRGBA(S.inst));
  cx.putImageData(im, 0, 0);
  flash("번호 저장 중…");
  const j = await post("/api/save_instances", {
    fruit: S.fruit, stem: S.stem, png: c.toDataURL("image/png"),
    by: who(), counts: S.numCounts,
    note: $("#note").value                  // 0918 사이클2: 세 저장 중 번호 저장만 메모를 안 보냈다
  });
  if (!j || !j.ok) {
    flash(errMsg(j, "번호 저장 실패"), true);
    // 0919 사이클5 3차 결정 1: 서버가 «번호 0개 저장» 을 막으면(blocked) 그 문구를 «사진 밖» 힌트와
    // 같은 **1초짜리 하단 힌트**로 보여 준다(다른 저장 실패는 그대로 3초 — 새 글자 0자).
    if (j && j.blocked) {
      clearTimeout(flash._t); flash._t = setTimeout(() => { $("#saveflash").textContent = ""; }, 1000);
    }
    return;
  }
  S.numDirty = false;
  S.instOrig = S.inst.slice();
  S.instSrc = "fixed";
  if (S.items[S.idx]) {
    if (j.status && j.status.status) S.items[S.idx].status = j.status.status;
    S.items[S.idx].has_fixed = true;
  }
  // 0918 사이클4 결정 1: 저장 = «번호 확정(수정함)». (modesim.js 도 떼어 내 돌리므로 있을 때만)
  if (typeof markTaskConfirmed === "function") markTaskConfirmed("instances");
  if (typeof cntSet === "function") cntSet("instances", j.n_instances);   // 0919 «개수 세기»
  flash(`번호 ${j.n_instances}개 저장 완료 (최대 ${j.max_id})`);
  numInfo(`저장됨 · 서버가 센 번호 ${j.n_instances}개 · 앞면 화소 ${(j.fg_pixels || 0).toLocaleString()}`);
}

async function revertInstances() {
  if (!S.stem) return;
  if (!confirm("고친 열매 번호를 지우고 처음 상태로 되돌립니다.\n"
    + "instances_fixed/ 와 masks_fixed/ 의 이 사진 파일이 삭제됩니다.\n진행할까요?")) return;
  const j = await post("/api/revert_instances", { fruit: S.fruit, stem: S.stem, by: who() });
  if (!j || !j.ok) return flash(errMsg(j, "되돌리기 실패"), true);
  S.numDirty = false;
  flash("번호를 되돌렸습니다 (" + (j.removed || []).join(", ") + ")");
  if (j.confirmed_cleared) clearTaskConfirmed(j.confirmed_cleared);   // 총괄 결정 1
  UI.openItem(S.idx, true);            // ↓ list.js
}

function numReload() {
  if (!S.inst || !S.instOrig) return;
  const ch = mkChanges();
  for (let i = 0; i < S.inst.length; i++) chSet(ch, S.inst, i, S.instOrig[i]);
  if (!ch.idx.length) return flash("처음 번호와 같습니다(바뀐 것이 없습니다)");
  pushNumUndo(ch, null);
  repaintNum();
  flash("처음 번호로 되돌렸습니다 (아직 저장 전)");
}

/* ------------------------------------------------------------- UI 연결 */
if ($("#num-mode")) {
  $("#num-mode").onchange = () => setNumMode($("#num-mode").checked);
  $$(".ntool").forEach((b) => b.onclick = () => setNTool(b.dataset.ntool));
  $("#numalpha").oninput = (e) => { S.numAlpha = +e.target.value / 100; $("#numalphav").textContent = e.target.value + "%"; S.dirty = true; };
  $("#numline").oninput = (e) => { $("#numlinev").textContent = e.target.value; S.dirty = true; };
  ["#l-num", "#l-numtext"].forEach((s) => $(s).onchange = () => { S.dirty = true; });
  $("#numundo").onclick = numUndo;
  $("#numreload").onclick = numReload;
  $("#numsave").onclick = saveInstances;
  $("#numrevert").onclick = revertInstances;
  $("#numshape").onchange = () => { clearPending(); };
}


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { loadInstances, setNumMode, setNTool, numKey, numUndo, numRedo, saveInstances, revertInstances, numReload, drawNumOverlay, drawErrBoxes, drawNoteBoxes, noteBoxes, ensureErrRows, renderErrRows, hasPendingRegion, clearPending, numMouseDown, numMouseMove, numMouseUp, instStats, VERDICT_KO });
})();
