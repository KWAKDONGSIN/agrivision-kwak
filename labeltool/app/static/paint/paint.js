// 라벨 그림판 동작 — 색(=열매 번호)으로 칠하고, 마스크·번호·상자를 한 번에 저장한다
"use strict";

/* ── 약속 ──────────────────────────────────────────────────────────────
   L[y*W+x] = 그 화소의 열매 번호. 0 = 배경, HOLE = «원본에 칠해져 있지만 번호가 없는 곳»(회색).
   저장할 때: 마스크 = L>0 (회색 포함) · 번호 = L (회색은 0) · 상자 = 번호마다 바깥 네모.
   서버 API 는 옛 툴과 같다(/api/save · /api/save_instances · /api/boxes · /api/status). */
const HOLE = 65535;
const $ = (s) => document.querySelector(s);
const S = {
  fruit: "", stem: "", items: [], W: 0, H: 0, L: null, img: null,
  tool: "brush", cur: 1, size: 12, fillNew: true, protect: true,
  z: 1, ox: 0, oy: 0, alpha: 0.5, showColor: true, showNums: true,
  undo: [], redo: [], dirty: false, busy: false, lastNew: 0, gen: 0,
};
const UNDO_MAX = 40;

/* ── 색: 번호마다 서로 잘 구별되는 색(황금각 색상환) ── */
const LUT = new Uint32Array(65536);
const LUT_CSS = {};
function hsv(h, s, v) {
  const f = (n) => { const k = (n + h * 6) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
  return [f(5), f(3), f(1)].map((x) => Math.round(x * 255));
}
function rgbOf(id) {
  if (id === HOLE) return [150, 150, 150];
  const h = (id * 0.618033988749895) % 1;
  return hsv(h, id % 3 === 0 ? 0.75 : 0.95, id % 2 ? 1 : 0.85);
}
function cssOf(id) {
  if (id === 0) return "#ffffff";
  if (!LUT_CSS[id]) { const [r, g, b] = rgbOf(id); LUT_CSS[id] = `rgb(${r},${g},${b})`; }
  return LUT_CSS[id];
}
function lut(id) {
  if (id === 0) return 0;
  let v = LUT[id];
  if (!v) { const [r, g, b] = rgbOf(id); v = LUT[id] = (255 << 24) | (b << 16) | (g << 8) | r; }
  return v;
}

/* ── 서버 ── */
async function getJSON(url) {
  const r = await fetch(url);
  if (r.status === 401 || r.redirected && r.url.includes("/login")) { location.href = "/login?next=/"; throw new Error("로그인 필요"); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || j.msg || ("서버 오류 " + r.status));
  return j;
}
async function postJSON(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.ok === false) throw new Error(j.error || j.msg || ("서버 오류 " + r.status));
  return j;
}
async function getBytes(url) {
  const r = await fetch(url);
  if (!r.ok) return null;
  return new Uint8Array(await r.arrayBuffer());
}

/* 회색(1채널) PNG 를 «값 그대로» 읽는다 — 16비트 번호를 캔버스로 읽으면 깨지므로 직접 푼다
   (옛 툴 instances.js 의 decodeGrayPng 와 같은 방법) */
async function inflateZlib(u8) {
  const ds = new DecompressionStream("deflate");
  const w = ds.writable.getWriter(); w.write(u8); w.close();
  const buf = await new Response(ds.readable).arrayBuffer();
  return new Uint8Array(buf);
}
async function decodeGrayPng(b) {
  if (!(b[0] === 0x89 && b[1] === 0x50)) throw new Error("PNG 파일이 아닙니다");
  const be32 = (i) => (b[i] * 16777216) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3];
  let off = 8, W = 0, H = 0, bd = 8, ct = 0; const idat = [];
  while (off + 8 <= b.length) {
    const len = be32(off), typ = String.fromCharCode(b[off + 4], b[off + 5], b[off + 6], b[off + 7]), ds = off + 8;
    if (typ === "IHDR") { W = be32(ds); H = be32(ds + 4); bd = b[ds + 8]; ct = b[ds + 9]; if (b[ds + 12]) throw new Error("인터레이스 PNG"); }
    else if (typ === "IDAT") idat.push(b.subarray(ds, ds + len));
    else if (typ === "IEND") break;
    off = ds + len + 4;
  }
  if (ct !== 0 || (bd !== 8 && bd !== 16)) throw new Error("회색 8·16비트 PNG 가 아닙니다");
  let t = 0; idat.forEach((p) => t += p.length);
  const z = new Uint8Array(t); let o = 0; idat.forEach((p) => { z.set(p, o); o += p.length; });
  const raw = await inflateZlib(z);
  const bpp = bd === 16 ? 2 : 1, stride = W * bpp, out = new Uint16Array(W * H);
  let prev = new Uint8Array(stride), cur = new Uint8Array(stride), p = 0;
  for (let y = 0; y < H; y++) {
    const ft = raw[p++]; cur.set(raw.subarray(p, p + stride)); p += stride;
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? cur[i - bpp] : 0, bb = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
      let v = cur[i];
      if (ft === 1) v += a; else if (ft === 2) v += bb; else if (ft === 3) v += (a + bb) >> 1;
      else if (ft === 4) { const pa = Math.abs(bb - c), pb = Math.abs(a - c), pc = Math.abs(a + bb - 2 * c); v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? bb : c); }
      cur[i] = v;
    }
    const ro = y * W;
    if (bd === 16) for (let x = 0; x < W; x++) out[ro + x] = (cur[x * 2] << 8) | cur[x * 2 + 1];
    else for (let x = 0; x < W; x++) out[ro + x] = cur[x];
    const tt = prev; prev = cur; cur = tt;
  }
  return { w: W, h: H, data: out };
}

/* ── 알림 줄 ── */
function say(text, kind) { const m = $("#msg"); m.textContent = text; m.className = kind || ""; }

/* ── 사진 목록 ── */
const who = () => localStorage.getItem("who") || "";
function askWho() {
  let n = prompt("작업자 이름을 적어 주세요 (저장 기록에 남습니다)", who());
  if (n === null) return who();
  n = n.trim();
  if (/^ai/i.test(n)) { alert("«AI» 로 시작하는 이름은 쓸 수 없습니다."); return askWho(); }
  try { localStorage.setItem("who", n); } catch (e) { /* 개인 창 */ }
  $("#who").textContent = "작업자: " + (n || "(이름 없음)");
  return n;
}

async function loadFruits() {
  const j = await getJSON("/api/fruits");
  const names = { apple: "사과", blueberry: "블루베리", grape: "포도", peach: "복숭아" };
  $("#fruit").innerHTML = j.fruits.map((f) => `<option value="${f.fruit}">${names[f.fruit] || f.fruit} (${f.n_images})</option>`).join("");
  const last = localStorage.getItem("paint.fruit");
  if (last && j.fruits.some((f) => f.fruit === last)) $("#fruit").value = last;
}

function itemMark(it) {
  if (it.confirmed === "exclude") return "✕ ";
  if (it.confirmed || it.confirmed_instances) return "✓ ";
  return "　";
}
async function loadList(keepStem) {
  S.fruit = $("#fruit").value;
  try { localStorage.setItem("paint.fruit", S.fruit); } catch (e) { /* 무시 */ }
  const items = [];
  for (let page = 1; ; page++) {
    const j = await getJSON(`/api/list?fruit=${S.fruit}&sort=name&page_size=500&page=${page}`);
    items.push(...j.items);
    if (page >= j.pages) break;
  }
  S.items = items;
  renderList(keepStem);
}
function renderList(keepStem) {
  const q = $("#q").value.trim().toLowerCase();
  const todo = $("#only-todo").checked;
  const shown = S.items.filter((it) => (!q || it.stem.toLowerCase().includes(q)) && (!todo || itemMark(it) === "　"));
  const done = S.items.filter((it) => itemMark(it) === "✓ ").length;
  const sel = $("#photo");
  sel.innerHTML = shown.map((it, i) => `<option value="${it.stem}">${itemMark(it)}${i + 1}. ${it.stem}</option>`).join("");
  sel.title = `전체 ${S.items.length}장 · 저장함 ${done}장 · 지금 목록 ${shown.length}장`;
  const want = keepStem && shown.some((it) => it.stem === keepStem) ? keepStem : (shown[0] || {}).stem;
  if (want) { sel.value = want; if (want !== S.stem || !S.L) openPhoto(want); }
  else say("조건에 맞는 사진이 없습니다.");
}

/* ── 한 장 열기 ── */
const imgC = $("#img"), ovC = $("#ov"), hud = $("#hud"), stage = $("#stage"), world = $("#world");
const ovX = ovC.getContext("2d"), hudX = hud.getContext("2d");
let ovData = null, ovU32 = null;

async function openPhoto(stem, fromOriginal) {
  if (S.busy) return;
  S.gen++;                                   // 이 값이 바뀌면 늦게 온 AI 답은 버린다(다른 사진에 붙지 않게)
  S.busy = true; $("#loading").style.display = "block";
  try {
    const f = S.fruit;
    const item = await getJSON(`/api/item?fruit=${f}&stem=${encodeURIComponent(stem)}`);
    const q = `fruit=${f}&stem=${encodeURIComponent(stem)}`;
    const img = new Image();
    const imgDone = new Promise((ok, bad) => { img.onload = ok; img.onerror = () => bad(new Error("사진을 못 읽었습니다")); });
    img.src = "/img?" + q;
    // 마스크: 사람이 고친 것이 있으면 그것, 없으면 원본. 번호: 서버가 고른 것(고친 것 > 팀 초벌 > 원본 번호)
    const useFixed = item.has_fixed && !fromOriginal;
    const [mb, ib] = await Promise.all([
      getBytes(`/mask?${q}&layer=${useFixed ? "fixed" : "gt"}`),
      getBytes(`/instances?${q}&layer=${fromOriginal ? "gt" : "auto"}`),
    ]);
    await imgDone;
    const W = item.width, H = item.height;
    const bin = mb ? (await decodeGrayPng(mb)).data : new Uint16Array(W * H);
    let L;
    if (ib) {
      L = (await decodeGrayPng(ib)).data;
      // 원본을 다시 부를 때는 번호도 원본 마스크 안으로 자른다(서버는 고친 마스크로 자른다)
      for (let i = 0; i < L.length; i++) { if (!bin[i]) L[i] = 0; else if (!L[i]) L[i] = HOLE; }
    } else {
      L = components(bin, W, H);
    }
    Object.assign(S, { stem, W, H, L, img, undo: [], redo: [], item, draftIds: new Set(), gen: S.gen + 1 });
    S.lastNew = maxId();
    S.cur = S.lastNew + 1;                       // 붓은 «새 열매» 색으로 시작한다
    computeCenters();
    imgC.width = ovC.width = W; imgC.height = ovC.height = H;
    imgC.getContext("2d").drawImage(img, 0, 0);
    ovData = ovX.createImageData(W, H); ovU32 = new Uint32Array(ovData.data.buffer);
    paintRect(0, 0, W, H);
    world.style.width = W + "px"; world.style.height = H + "px";
    fit();
    setDirty(!!fromOriginal);
    $("#t-name").textContent = stem;
    $("#photo").value = stem;
    renderPalette(); renderCount();
    const it = S.items.find((x) => x.stem === stem) || {};
    say(it.confirmed === "exclude" ? "이 사진은 «빼기» 로 표시돼 있습니다. (파일 → 빼기 취소)" :
      fromOriginal ? "원본을 다시 불러왔습니다. 저장해야 반영됩니다." :
      `${stem} 을(를) 열었습니다. 색 하나 = 열매 하나입니다.`, it.confirmed === "exclude" ? "err" : "");
  } catch (e) {
    say("열기 실패: " + e.message, "err");
  } finally {
    S.busy = false; $("#loading").style.display = "none";
  }
}

/* 번호가 아예 없는 사진: 칠해진 덩어리마다 번호를 붙인다(4-연결) */
function components(bin, W, H) {
  const L = new Uint16Array(W * H), stack = new Int32Array(W * H);
  let n = 0;
  for (let s = 0; s < L.length; s++) {
    if (!bin[s] || L[s]) continue;
    n = Math.min(n + 1, HOLE - 1);
    let sp = 0; stack[sp++] = s; L[s] = n;
    while (sp) {
      const i = stack[--sp], x = i % W;
      if (x > 0 && bin[i - 1] && !L[i - 1]) { L[i - 1] = n; stack[sp++] = i - 1; }
      if (x < W - 1 && bin[i + 1] && !L[i + 1]) { L[i + 1] = n; stack[sp++] = i + 1; }
      if (i >= W && bin[i - W] && !L[i - W]) { L[i - W] = n; stack[sp++] = i - W; }
      if (i + W < L.length && bin[i + W] && !L[i + W]) { L[i + W] = n; stack[sp++] = i + W; }
    }
  }
  return L;
}

/* ── 그리기(화면) ── */
function paintRect(x0, y0, w, h) {
  x0 = Math.max(0, x0 | 0); y0 = Math.max(0, y0 | 0);
  const x1 = Math.min(S.W, Math.ceil(x0 + w)), y1 = Math.min(S.H, Math.ceil(y0 + h));
  if (x1 <= x0 || y1 <= y0) return;
  const L = S.L, W = S.W;
  for (let y = y0; y < y1; y++) { const r = y * W; for (let x = x0; x < x1; x++) ovU32[r + x] = lut(L[r + x]); }
  ovX.putImageData(ovData, 0, 0, x0, y0, x1 - x0, y1 - y0);
}
function applyView() {
  world.style.transform = `translate(${S.ox}px,${S.oy}px) scale(${S.z})`;
  const show = S.showColor && !S.peek;         // peek = ` 키를 누르고 있는 동안
  ovC.style.opacity = show ? S.alpha : 0;
  const ob = document.querySelector("#orig");
  if (ob) { ob.classList.toggle("on", !show); ob.textContent = show ? "👁 원본 보기" : "🎨 색 다시 보기"; }
  drawHud();
}
function fit() {
  const r = stage.getBoundingClientRect();
  S.z = Math.min(r.width / S.W, r.height / S.H) * 0.98;
  S.ox = (r.width - S.W * S.z) / 2; S.oy = (r.height - S.H * S.z) / 2;
  applyView();
}
function zoomAt(sx, sy, k) {
  const nz = Math.max(0.05, Math.min(40, S.z * k));
  S.ox = sx - (sx - S.ox) * nz / S.z; S.oy = sy - (sy - S.oy) * nz / S.z; S.z = nz;
  applyView();
}

/* 번호 글자·붓 동그라미·올가미 선 — 화면 크기 캔버스에 그린다 */
let centers = [], mouse = null, lassoPts = null;
function computeCenters() {
  const sx = new Float64Array(65536), sy = new Float64Array(65536), n = new Uint32Array(65536);
  const L = S.L, W = S.W;
  for (let i = 0; i < L.length; i++) { const v = L[i]; if (v && v !== HOLE) { n[v]++; sx[v] += i % W; sy[v] += (i / W) | 0; } }
  centers = [];
  for (let v = 1; v < HOLE; v++) if (n[v]) centers.push([v, sx[v] / n[v], sy[v] / n[v], n[v]]);
}
function drawHud() {
  const r = stage.getBoundingClientRect();
  if (hud.width !== (r.width | 0) || hud.height !== (r.height | 0)) { hud.width = r.width; hud.height = r.height; }
  hudX.clearRect(0, 0, hud.width, hud.height);
  if (!S.L) return;
  if (S.showNums && S.showColor && !S.peek) {
    hudX.font = "bold 13px sans-serif"; hudX.textAlign = "center"; hudX.textBaseline = "middle";
    hudX.lineWidth = 3; hudX.strokeStyle = "#000"; hudX.fillStyle = "#fff";
    for (const [v, cx, cy, n] of centers) {
      const x = S.ox + cx * S.z, y = S.oy + cy * S.z;
      if (x < -20 || y < -20 || x > hud.width + 20 || y > hud.height + 20) continue;
      const dr = S.draftIds && S.draftIds.has(v);
      if (dr) {                                   // 모델 초벌에서 온 열매: 노란 동그라미 + 노란 번호
        hudX.beginPath(); hudX.arc(x, y, Math.max(8, Math.sqrt(n / Math.PI) * S.z + 4), 0, Math.PI * 2);
        hudX.lineWidth = 2; hudX.strokeStyle = "#ffe000"; hudX.stroke(); hudX.lineWidth = 3; hudX.strokeStyle = "#000";
      }
      hudX.fillStyle = dr ? "#ffe000" : "#fff";
      hudX.strokeText(v, x, y); hudX.fillText(v, x, y);
    }
    hudX.fillStyle = "#fff";
  }
  if (lassoPts && lassoPts.length > 1) {
    hudX.beginPath();
    lassoPts.forEach(([x, y], i) => { const X = S.ox + x * S.z, Y = S.oy + y * S.z; i ? hudX.lineTo(X, Y) : hudX.moveTo(X, Y); });
    hudX.setLineDash([5, 4]); hudX.lineWidth = 2; hudX.strokeStyle = lassoPts.erase ? "#fff" : cssOf(S.cur); hudX.stroke(); hudX.setLineDash([]);
  }
  if (drag && drag.kind === "sam" && drag.esx !== undefined && Math.hypot(drag.esx - drag.sx, drag.esy - drag.sy) > 8) {
    hudX.setLineDash([6, 4]); hudX.lineWidth = 2; hudX.strokeStyle = "#ffe000";
    hudX.strokeRect(Math.min(drag.sx, drag.esx), Math.min(drag.sy, drag.esy), Math.abs(drag.esx - drag.sx), Math.abs(drag.esy - drag.sy));
    hudX.setLineDash([]);
  }
  if (mouse && (S.tool === "brush" || S.tool === "eraser")) {
    hudX.beginPath(); hudX.arc(mouse.sx, mouse.sy, Math.max(1, S.size / 2 * S.z), 0, Math.PI * 2);
    hudX.lineWidth = 1; hudX.strokeStyle = "#000"; hudX.stroke();
    hudX.beginPath(); hudX.arc(mouse.sx, mouse.sy, Math.max(1, S.size / 2 * S.z) + 1, 0, Math.PI * 2);
    hudX.strokeStyle = "#fff"; hudX.stroke();
  }
}

/* ── 되돌리기: 바뀐 네모 칸만 기억한다 ── */
function snapshot() { return S.L.slice(); }
function pushUndo(before, x0, y0, x1, y1) {
  x0 = Math.max(0, x0); y0 = Math.max(0, y0); x1 = Math.min(S.W, x1); y1 = Math.min(S.H, y1);
  if (x1 <= x0 || y1 <= y0) return;
  const w = x1 - x0, h = y1 - y0, data = new Uint16Array(w * h);
  let same = true;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y0 + y) * S.W + x0 + x; data[y * w + x] = before[i]; if (before[i] !== S.L[i]) same = false;
  }
  if (same) return;
  S.undo.push({ x0, y0, w, h, data }); if (S.undo.length > UNDO_MAX) S.undo.shift();
  S.redo = [];
  changed();
}
function swapRect(rec) {
  const { x0, y0, w, h, data } = rec;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y0 + y) * S.W + x0 + x, t = S.L[i]; S.L[i] = data[y * w + x]; data[y * w + x] = t;
  }
  paintRect(x0, y0, w, h);
}
function undo() { const r = S.undo.pop(); if (!r) return say("더 되돌릴 것이 없습니다."); swapRect(r); S.redo.push(r); changed(); }
function redo() { const r = S.redo.pop(); if (!r) return say("다시 할 것이 없습니다."); swapRect(r); S.undo.push(r); changed(); }
function changed() { setDirty(true); computeCenters(); renderPalette(); renderCount(); drawHud(); }
function setDirty(d) {
  S.dirty = d; $("#t-dirty").textContent = d ? "● 저장 안 됨" : "";
  $("#save").classList.toggle("dirty", d);
}

/* ── 칠하기 동작 ── */
function canPaint(v, val) { return !S.protect || val === 0 || v === 0 || v === HOLE || v === val; }
function stamp(cx, cy, val, box) {
  const r = S.size / 2, r2 = r * r, L = S.L, W = S.W;
  const x0 = Math.max(0, Math.floor(cx - r)), x1 = Math.min(S.W - 1, Math.ceil(cx + r));
  const y0 = Math.max(0, Math.floor(cy - r)), y1 = Math.min(S.H - 1, Math.ceil(cy + r));
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const dx = x + 0.5 - cx, dy = y + 0.5 - cy;
    if (dx * dx + dy * dy > r2 && !(S.size <= 1.5 && x === Math.floor(cx) && y === Math.floor(cy))) continue;
    const i = y * W + x;
    if (canPaint(L[i], val)) L[i] = val;
  }
  box[0] = Math.min(box[0], x0); box[1] = Math.min(box[1], y0); box[2] = Math.max(box[2], x1 + 1); box[3] = Math.max(box[3], y1 + 1);
  paintRect(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
}
function strokeTo(a, b, val, box) {
  const d = Math.hypot(b[0] - a[0], b[1] - a[1]), step = Math.max(0.5, S.size / 4), n = Math.ceil(d / step);
  for (let k = 1; k <= n; k++) stamp(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, val, box);
}

/* 채우기통: 누른 덩어리(같은 번호로 이어진 곳)를 val 로 바꾼다 */
function fillAt(x, y, val) {
  const W = S.W, L = S.L, s = y * W + x, v = L[s];
  if (v === 0) { say("빈 곳입니다. 칠해진 열매(색이 있는 곳)를 누르세요. 새로 칠하려면 붓·올가미를 쓰세요."); return false; }
  if (v === val) { say(`이미 ${val}번입니다.`); return false; }
  const before = snapshot(), stack = new Int32Array(L.length);
  let sp = 0, bx0 = x, by0 = y, bx1 = x, by1 = y;
  stack[sp++] = s; L[s] = val;
  while (sp) {
    const i = stack[--sp], px = i % W, py = (i / W) | 0;
    if (px < bx0) bx0 = px; if (px > bx1) bx1 = px; if (py < by0) by0 = py; if (py > by1) by1 = py;
    if (px > 0 && L[i - 1] === v) { L[i - 1] = val; stack[sp++] = i - 1; }
    if (px < W - 1 && L[i + 1] === v) { L[i + 1] = val; stack[sp++] = i + 1; }
    if (i >= W && L[i - W] === v) { L[i - W] = val; stack[sp++] = i - W; }
    if (i + W < L.length && L[i + W] === v) { L[i + W] = val; stack[sp++] = i + W; }
  }
  paintRect(bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1);
  pushUndo(before, bx0, by0, bx1 + 1, by1 + 1);
  say(val === 0 ? "그 덩어리를 지웠습니다." : `그 덩어리를 ${val}번으로 칠했습니다.`);
  return true;
}

/* 올가미: 그린 테두리 안을 val 로 */
function fillPolygon(pts, val) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0));
  x1 = Math.min(S.W, Math.ceil(x1) + 1); y1 = Math.min(S.H, Math.ceil(y1) + 1);
  const w = x1 - x0, h = y1 - y0;
  if (w < 2 || h < 2) return;
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d");
  x.beginPath(); pts.forEach(([px, py], i) => (i ? x.lineTo(px - x0, py - y0) : x.moveTo(px - x0, py - y0)));
  x.closePath(); x.fillStyle = "#fff"; x.fill();
  const a = x.getImageData(0, 0, w, h).data, before = snapshot(), L = S.L;
  for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
    if (a[(yy * w + xx) * 4 + 3] < 128) continue;
    const i = (y0 + yy) * S.W + x0 + xx;
    if (canPaint(L[i], val)) L[i] = val;
  }
  paintRect(x0, y0, w, h);
  pushUndo(before, x0, y0, x1, y1);
}

/* 기다리는 동안 사진이 바뀌었으면 true — 늦게 온 답을 새 사진에 붙이지 않는다(검수 1회 지적 1·3) */
const stale = (g) => g !== S.gen;

/* ✨ 클릭 칠하기: 도우미(SAM)가 준 후보 모양을 칠한다. 같은 자리를 또 누르면 다음 후보로 바꾼다 */
let samLast = null;
async function maskFromPng(b64, w, h) {
  const im = new Image(); im.src = "data:image/png;base64," + b64; await im.decode();
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d"); x.drawImage(im, 0, 0);
  return x.getImageData(0, 0, w, h).data;
}
async function applyCand(cd, val, g) {
  const a = await maskFromPng(cd.png, cd.w, cd.h);
  if (g !== undefined && stale(g)) return false;
  const before = snapshot(), L = S.L;
  for (let yy = 0; yy < cd.h; yy++) for (let xx = 0; xx < cd.w; xx++) {
    if (a[(yy * cd.w + xx) * 4] < 128) continue;
    const i = (cd.y0 + yy) * S.W + cd.x0 + xx;
    if (canPaint(L[i], val)) L[i] = val;
  }
  paintRect(cd.x0, cd.y0, cd.w, cd.h);
  const n = S.undo.length;
  pushUndo(before, cd.x0, cd.y0, cd.x0 + cd.w, cd.y0 + cd.h);
  return S.undo.length > n;
}
async function samClick(ix, iy) {
  if (S.samBusy) return;
  const again = samLast && samLast.stem === S.stem && Math.abs(samLast.x - ix) + Math.abs(samLast.y - iy) <= 6;
  if (again) {
    if (samLast.applied) undo();
    samLast.k = (samLast.k + 1) % samLast.cands.length;
    samLast.applied = await applyCand(samLast.cands[samLast.k], samLast.val, S.gen);
    say(`${samLast.k + 1}/${samLast.cands.length}번째 모양입니다. 또 누르면 다음 모양.`);
    return;
  }
  const here = S.L[iy * S.W + ix];
  if (here && here !== HOLE && S.protect) {
    say(`이미 ${here}번 열매입니다. 모양을 바꾸려면 오른쪽 클릭으로 지운 뒤 다시 누르세요.`); return;
  }
  S.samBusy = true; say("✨ 모양 찾는 중…");
  try {
    const crop = Math.max(256, Math.min(1024, Math.round(320 / S.z)));
    const g = S.gen;
    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, x: ix, y: iy, crop });
    if (stale(g)) return;
    if (!j.cands || !j.cands.length) { say("여기서는 열매 모양을 못 찾았습니다. 조금 옆을 누르거나 확대해서 눌러 보세요.", "err"); return; }
    const val = S.fillNew ? Math.max(maxId(), S.lastNew) + 1 : (S.cur || Math.max(maxId(), S.lastNew) + 1);
    samLast = { stem: S.stem, x: ix, y: iy, cands: j.cands, k: 0, val, points: [[ix, iy, 1]], box: null };
    samLast.applied = await applyCand(j.cands[0], val, g);
    if (stale(g)) return;
    if (S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
    say(samLast.applied ? `${val}번으로 칠했습니다 (${j.sec}초). 모양이 이상하면 같은 자리를 다시 누르세요 — 후보 ${j.cands.length}개.`
      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).");
  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
  finally { S.samBusy = false; }
}

/* Shift+클릭 = «여기는 아니다»: 누른 곳의 모양(가장 작은 후보)을 ✨ 로 찾아, 방금 칠한 열매에서 그만큼 잘라 낸다.
   (SAM 의 «빼기 점» 은 한 번으로는 거의 안 먹어서 이렇게 한다 — 붙은 블루베리 옆 알을 떼어 낼 때 쓴다) */
async function samNeg(ix, iy) {
  if (!samLast || samLast.stem !== S.stem) return say("먼저 ✨ 로 열매를 칠한 뒤, 잘못 칠해진 부분을 Shift+클릭하세요.");
  const val = samLast.val;
  if (S.L[iy * S.W + ix] !== val) return say(`거기는 ${val}번이 아닙니다. 방금 칠한 ${val}번 안의 잘못된 부분을 Shift+클릭하세요.`);
  if (S.samBusy) return;
  S.samBusy = true; say("✨ 떼어 낼 부분을 찾는 중…");
  try {
    const g = S.gen;
    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, x: ix, y: iy, crop: Math.max(256, Math.min(1024, Math.round(320 / S.z))) });
    if (stale(g)) return;
    if (!j.cands || !j.cands.length) { say("떼어 낼 부분을 못 찾았습니다. 지우개(E)로 지워 주세요.", "err"); return; }
    const cd = j.cands.reduce((m, c) => (c.w * c.h < m.w * m.h ? c : m));      // 가장 작은 모양
    const a = await maskFromPng(cd.png, cd.w, cd.h);
    if (stale(g)) return;
    const before = snapshot(), L = S.L;
    let n = 0, left = 0;
    for (let yy = 0; yy < cd.h; yy++) for (let xx = 0; xx < cd.w; xx++) {
      if (a[(yy * cd.w + xx) * 4] < 128) continue;
      const i = (cd.y0 + yy) * S.W + cd.x0 + xx;
      if (L[i] === val) { L[i] = 0; n++; }
    }
    for (let i = 0; i < L.length; i++) if (L[i] === val) left++;
    if (!left) { S.L.set(before); paintRect(cd.x0, cd.y0, cd.w, cd.h); return say("그러면 열매가 통째로 사라져서 하지 않았습니다. 오른쪽 클릭으로 지우고 다시 누르세요.", "err"); }
    paintRect(cd.x0, cd.y0, cd.w, cd.h); pushUndo(before, cd.x0, cd.y0, cd.x0 + cd.w, cd.y0 + cd.h);
    samLast.x = samLast.y = -99;                // 이제 «같은 자리 다시 누르기» 로 후보를 바꾸지 않는다
    say(`${val}번에서 ${n}화소를 떼어 냈습니다. 떼어 낸 알은 ✨ 로 눌러 새 번호를 붙일 수 있습니다.`);
  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
  finally { S.samBusy = false; }
}
/* 끌어서 네모 = 그 안의 열매 하나를 칠한다(작은 열매·붙은 열매에 좋다) */
async function samBox(box) {
  if (S.samBusy) return;
  if (box[2] - box[0] < 3 || box[3] - box[1] < 3) return;
  S.samBusy = true; say("✨ 네모 안의 열매를 찾는 중…");
  try {
    const g = S.gen;
    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, box, crop: 256 });
    if (stale(g)) return;
    if (!j.cands || !j.cands.length) { say("네모 안에서 열매를 못 찾았습니다. 조금 크게 그려 보세요.", "err"); return; }
    const val = S.fillNew ? Math.max(maxId(), S.lastNew) + 1 : (S.cur || Math.max(maxId(), S.lastNew) + 1);
    samLast = { stem: S.stem, x: -99, y: -99, cands: j.cands, k: 0, val, points: [], box };
    samLast.applied = await applyCand(j.cands[0], val, g);
    if (stale(g)) return;
    if (S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
    say(samLast.applied ? `네모 안을 ${val}번으로 칠했습니다. 잘못 칠한 곳은 Shift+클릭으로 뺄 수 있습니다.`
      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).");
  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
  finally { S.samBusy = false; }
}

/* 모델 초벌: 미리 만든 번호 마스크(/draft)를 불러온다 — add = 빈 자리의 열매만 더하기, 아니면 전부 바꾸기 */
async function loadDraft(add) {
  if (!S.L) return;
  const g = S.gen;
  const b = await getBytes(`/draft?fruit=${S.fruit}&stem=${encodeURIComponent(S.stem)}`);
  if (stale(g)) return;
  if (!b) return say("이 사진에는 모델 초벌이 아직 없습니다.", "err");
  const D0 = (await decodeGrayPng(b)).data;
  if (stale(g)) return;
  const D = D0, L = S.L, before = snapshot();
  if (!S.draftIds) S.draftIds = new Set();
  if (D.length !== L.length) return say("초벌 크기가 사진과 다릅니다.", "err");
  let added = 0;
  if (!add) {
    for (let i = 0; i < L.length; i++) L[i] = D[i];
    S.draftIds = new Set(idsNow().ids);
    added = idsNow().ids.length;
  } else {
    const tot = new Uint32Array(65536), ov = new Uint32Array(65536);
    for (let i = 0; i < L.length; i++) { const d = D[i]; if (d) { tot[d]++; if (L[i]) ov[d]++; } }
    const map = new Uint16Array(65536); let next = Math.max(maxId(), S.lastNew);
    for (let d = 1; d < 65535; d++) if (tot[d] && ov[d] < 0.3 * tot[d]) { map[d] = ++next; added++; S.draftIds.add(next); }
    for (let i = 0; i < L.length; i++) { const m = map[D[i]]; if (m && !L[i]) L[i] = m; }
    S.lastNew = next;
  }
  paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
  computeCenters(); drawHud();
  say(add ? `모델 초벌에서 빠진 열매 ${added}개를 더했습니다(노란 동그라미). 틀린 건 오른쪽 클릭(채우기통·✨)으로 지운 뒤 저장하세요.`
    : `모델 초벌로 바꿨습니다(열매 ${added}개). 확인하고 고친 뒤 저장하세요. Ctrl+Z 로 되돌릴 수 있습니다.`, "ok");
}

/* 번호만 다시 나누기: 칠한 모양(마스크)은 그대로 두고, 번호를 원본 정답(kind=gt) 또는 모델 초벌로 나눈다.
   참고 번호가 없는 칠한 자리는 원래 번호(회색은 회색)를 그대로 둔다. 번호는 1부터 다시 매긴다. */
async function splitBy(kind) {
  if (!S.L) return;
  const g = S.gen;
  const b = await getBytes(`/draft?fruit=${S.fruit}&stem=${encodeURIComponent(S.stem)}${kind === "gt" ? "&kind=gt" : ""}`);
  if (stale(g)) return;
  if (!b) return say(kind === "gt" ? "이 사진에는 원본 정답 번호가 없습니다(사과는 원래 정답 번호가 기본)." : "이 사진에는 모델 초벌이 없습니다.", "err");
  const D = (await decodeGrayPng(b)).data;
  if (stale(g)) return;
  const L = S.L, before = snapshot();
  if (D.length !== L.length) return say("번호 파일 크기가 사진과 다릅니다.", "err");
  const mapD = new Map(); let next = 0;
  for (let i = 0; i < L.length; i++) {
    const v = L[i]; if (!v) continue;
    const d = D[i];
    if (d) { let m = mapD.get(d); if (!m) mapD.set(d, m = ++next); L[i] = m; }
  }
  // 참고 번호가 없는 칠한 자리: 덩어리(4-연결)로 묶어 큰 것(≥ BIG 화소)은 새 열매, 작은 가장자리 조각은 옆 열매에 붙인다
  const W = S.W, BIG = 300, left = new Int32Array(L.length).fill(-1), stack = new Int32Array(L.length), small = [];
  for (let s = 0; s < L.length; s++) {
    if (!before[s] || D[s] || left[s] >= 0) continue;
    let sp = 0; const comp = []; stack[sp++] = s; left[s] = s;
    while (sp) {
      const i = stack[--sp]; comp.push(i); const x = i % W;
      for (const j of [x > 0 ? i - 1 : -1, x < W - 1 ? i + 1 : -1, i - W, i + W]) {
        if (j < 0 || j >= L.length || left[j] >= 0 || !before[j] || D[j]) continue;
        left[j] = s; stack[sp++] = j;
      }
    }
    if (comp.length >= BIG) { const m = ++next; for (const i of comp) L[i] = m; }
    else for (const i of comp) { L[i] = 0; small.push(i); }
  }
  for (let pass = 0; pass < 30 && small.length; pass++) {       // 작은 조각을 바깥에서부터 옆 번호로 채운다
    const took = [];
    for (let k = small.length - 1; k >= 0; k--) {
      const i = small[k], x = i % W;
      const nb = (x > 0 && L[i - 1]) || (x < W - 1 && L[i + 1]) || (i >= W && L[i - W]) || (i + W < L.length && L[i + W]);
      if (nb && nb !== HOLE) took.push([i, nb]);
    }
    if (!took.length) break;
    const done = new Set(took.map((t) => t[0]));
    for (const [i, nb] of took) L[i] = nb;
    for (let k = small.length - 1; k >= 0; k--) if (done.has(small[k])) small.splice(k, 1);
  }
  for (const i of small) L[i] = HOLE;                        // 어디에도 안 닿는 작은 점은 «번호 없음»(마스크는 유지)
  S.lastNew = next; S.draftIds = new Set();
  paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
  say(`번호를 ${kind === "gt" ? "원본 정답" : "모델 초벌"} 기준으로 다시 나눴습니다 — 열매 ${idsNow().ids.length}개(칠한 모양은 그대로). 확인 뒤 저장하세요.`, "ok");
}

/* ── 번호·팔레트 ── */
function maxId() { let m = 0; const L = S.L; for (let i = 0; i < L.length; i++) { const v = L[i]; if (v !== HOLE && v > m) m = v; } return m; }
function idsNow() {
  const seen = new Uint8Array(65536); let hole = false;
  for (let i = 0; i < S.L.length; i++) { const v = S.L[i]; if (v === HOLE) hole = true; else seen[v] = 1; }
  const ids = []; for (let v = 1; v < HOLE; v++) if (seen[v]) ids.push(v);
  return { ids, hole };
}
function newNumber() {
  S.lastNew = Math.max(maxId(), S.lastNew) + 1;
  setCur(S.lastNew);
  say(`새 번호 ${S.cur}번. 이 색으로 열매 하나를 칠하세요.`);
}
function setCur(v) {
  S.cur = v;
  $("#cur-sw").style.background = cssOf(v);
  $("#cur-txt").textContent = v ? v + "번" : "지우기";
  document.querySelectorAll(".sw").forEach((e) => e.classList.toggle("on", +e.dataset.id === v));
}
function renderPalette() {
  const { ids, hole } = idsNow();
  const box = $("#swatches");
  let h = `<div class="sw erase" data-id="0" title="배경색(지우기). 이 색으로 칠하면 지워집니다">지우기</div>`;
  h += `<div class="sw new" data-act="new" title="새 번호 (N)">＋</div>`;
  if (hole) h += `<div class="sw hole" title="원본에 칠해져 있지만 번호가 없는 곳. 채우기통으로 누르면 번호가 붙습니다">?</div>`;
  if (S.cur && !ids.includes(S.cur)) h += `<div class="sw" data-id="${S.cur}" style="background:${cssOf(S.cur)}" title="${S.cur}번 (아직 안 칠함)">${S.cur}</div>`;
  for (const v of ids) h += `<div class="sw" data-id="${v}" style="background:${cssOf(v)}" title="${v}번">${v}</div>`;
  box.innerHTML = h;
  setCur(S.cur);
}
function renderCount() {
  const { ids, hole } = idsNow();
  $("#count").textContent = `열매 ${ids.length}개` + (hole ? " · 회색(번호 없음) 있음" : "");
}

/* ── 도구·옵션 상자 ── */
const TOOL_KEYS = { b: "brush", e: "eraser", f: "fill", l: "lasso", i: "pick", z: "zoom", h: "hand", s: "sam" };
function setTool(t) {
  S.tool = t;
  document.querySelectorAll("#tools [data-tool]").forEach((b) => b.classList.toggle("on", b.dataset.tool === t));
  const o = $("#options");
  const sizes = [4, 8, 16, 32, 64];
  const sizeHtml = `<div>굵기 <b id="sz">${S.size}</b></div><div class="sizes">` +
    sizes.map((s) => `<button class="optbtn${s === S.size ? " on" : ""}" data-size="${s}">● ${s}</button>`).join("") + `</div>`;
  const protect = `<label><input type="checkbox" id="protect"${S.protect ? " checked" : ""}> 다른 열매 위에는 안 칠함</label>`;
  const help = {
    brush: "왼쪽 = 지금 색으로 칠하기<br>오른쪽 = 지우기" + sizeHtml + protect,
    eraser: "끌어서 지우기(마스크와 번호가 같이 지워짐)" + sizeHtml,
    fill: "칠한 덩어리를 누르면 지금 색이 됩니다.<br>오른쪽 = 덩어리 통째로 지우기" +
      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호 (열매 세기)</label>` +
      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로 (가려진 조각 합치기)</label>`,
    lasso: "열매 테두리를 따라 그리고 손을 떼면 안이 칠해집니다.<br>오른쪽 = 그 안 지우기" + protect,
    pick: "열매를 누르면 그 색(번호)을 집습니다.",
    sam: "열매를 누르면 AI 가 모양대로 칠합니다.<br>같은 자리를 <b>다시 누르면</b> 다른 모양(작게/크게).<br><b>끌어서 네모</b> = 그 안의 열매 하나<br><b>Shift+클릭</b> = 방금 칠한 것에서 «여기는 아님»<br>오른쪽 = 덩어리 지우기" +
      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호</label>` +
      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로</label>` + protect,
    zoom: "왼쪽 = 확대 · 오른쪽 = 축소<br>(휠로도 됩니다)",
    hand: "끌어서 옮깁니다.<br>(다른 도구에서도 스페이스를 누른 채 끌면 됩니다)",
  }[t];
  o.innerHTML = help;
  o.querySelectorAll("[data-size]").forEach((b) => b.onclick = () => { S.size = +b.dataset.size; setTool(S.tool); });
  const p = o.querySelector("#protect"); if (p) p.onchange = () => { S.protect = p.checked; };
  o.querySelectorAll("input[name=fm]").forEach((r) => r.onchange = () => { S.fillNew = r.value === "new"; });
  stage.style.cursor = t === "hand" ? "grab" : t === "zoom" ? "zoom-in" : t === "sam" ? "cell" : "crosshair";
  drawHud();
}

/* ── 마우스 ── */
let drag = null, spaceDown = false;
function toImg(e) {
  const r = stage.getBoundingClientRect(), sx = e.clientX - r.left, sy = e.clientY - r.top;
  return { sx, sy, x: (sx - S.ox) / S.z, y: (sy - S.oy) / S.z };
}
stage.addEventListener("contextmenu", (e) => e.preventDefault());
stage.addEventListener("mousedown", (e) => {
  if (!S.L || S.busy) return;
  const p = toImg(e), right = e.button === 2;
  if (e.button === 1 || spaceDown || S.tool === "hand") { drag = { kind: "pan", sx: p.sx, sy: p.sy, ox: S.ox, oy: S.oy }; stage.style.cursor = "grabbing"; return; }
  const ix = Math.floor(p.x), iy = Math.floor(p.y), inside = ix >= 0 && iy >= 0 && ix < S.W && iy < S.H;
  if (S.tool === "zoom") { zoomAt(p.sx, p.sy, right ? 1 / 1.6 : 1.6); return; }
  if (S.tool === "pick") {
    if (!inside) return;
    const v = S.L[iy * S.W + ix];
    if (v === HOLE) return say("회색(번호 없는 곳)은 집을 수 없습니다. 채우기통으로 번호를 붙이세요.");
    setCur(v); setTool("brush"); say(v ? `${v}번 색을 집었습니다. 붓으로 바뀌었습니다.` : "지우기 색을 집었습니다.");
    return;
  }
  if (S.tool === "fill") {
    if (!inside) return;
    if (right) { fillAt(ix, iy, 0); return; }
    let val = S.cur;
    if (S.fillNew) val = Math.max(maxId(), S.lastNew) + 1;
    if (fillAt(ix, iy, val) && S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
    return;
  }
  if (S.tool === "sam") {
    if (!inside) return;
    if (right) { fillAt(ix, iy, 0); return; }
    drag = { kind: "sam", sx: p.sx, sy: p.sy, x: p.x, y: p.y, ex: p.x, ey: p.y, shift: e.shiftKey };   // 떼는 순간 클릭/네모를 가린다
    return;
  }
  if (S.tool === "lasso") { lassoPts = [[p.x, p.y]]; lassoPts.erase = right; drag = { kind: "lasso" }; return; }
  // 붓·지우개
  const val = S.tool === "eraser" || right ? 0 : S.cur;
  const box = [Infinity, Infinity, -Infinity, -Infinity];
  drag = { kind: "paint", val, last: [p.x, p.y], before: snapshot(), box };
  stamp(p.x, p.y, val, box);
});
window.addEventListener("mousemove", (e) => {
  if (!S.L) return;
  const p = toImg(e);
  const inside = e.target === hud || e.target === stage || stage.contains(e.target);
  mouse = inside ? p : null;
  const ix = Math.floor(p.x), iy = Math.floor(p.y);
  if (ix >= 0 && iy >= 0 && ix < S.W && iy < S.H) {
    const v = S.L[iy * S.W + ix];
    $("#pos").textContent = `${ix}, ${iy}` + (v === HOLE ? " · 번호없음" : v ? ` · ${v}번` : "");
  }
  if (drag && drag.kind === "pan") { S.ox = drag.ox + p.sx - drag.sx; S.oy = drag.oy + p.sy - drag.sy; applyView(); return; }
  if (drag && drag.kind === "paint") { strokeTo(drag.last, [p.x, p.y], drag.val, drag.box); drag.last = [p.x, p.y]; }
  if (drag && drag.kind === "lasso") lassoPts.push([p.x, p.y]);
  if (drag && drag.kind === "sam") { drag.ex = p.x; drag.ey = p.y; drag.esx = p.sx; drag.esy = p.sy; }
  drawHud();
});
window.addEventListener("mouseup", () => {
  if (!drag) return;
  const d = drag; drag = null;
  if (d.kind === "pan") { stage.style.cursor = S.tool === "hand" ? "grab" : "crosshair"; return; }
  if (d.kind === "paint") pushUndo(d.before, d.box[0], d.box[1], d.box[2], d.box[3]);
  if (d.kind === "sam") {
    const moved = d.esx !== undefined && Math.hypot(d.esx - d.sx, d.esy - d.sy) > 8;
    drawHud();
    const cl = (v, m) => Math.max(0, Math.min(m - 1, Math.floor(v)));
    if (moved) samBox([cl(Math.min(d.x, d.ex), S.W), cl(Math.min(d.y, d.ey), S.H), cl(Math.max(d.x, d.ex), S.W), cl(Math.max(d.y, d.ey), S.H)]);
    else if (d.shift) samNeg(cl(d.x, S.W), cl(d.y, S.H));
    else samClick(cl(d.x, S.W), cl(d.y, S.H));
    return;
  }
  if (d.kind === "lasso") {
    const pts = lassoPts; lassoPts = null;
    if (pts.length > 2) fillPolygon(pts, pts.erase ? 0 : S.cur);
    drawHud();
  }
});
stage.addEventListener("wheel", (e) => {
  e.preventDefault(); if (!S.L) return;
  const p = toImg(e); zoomAt(p.sx, p.sy, e.deltaY < 0 ? 1.2 : 1 / 1.2);
}, { passive: false });
stage.addEventListener("mouseleave", () => { mouse = null; drawHud(); });

/* ── 저장 ── */
function encodeBinary() {
  const c = document.createElement("canvas"); c.width = S.W; c.height = S.H;
  const x = c.getContext("2d"), d = x.createImageData(S.W, S.H), u = new Uint32Array(d.data.buffer);
  for (let i = 0; i < S.L.length; i++) u[i] = S.L[i] ? 0xffffffff : 0xff000000;
  x.putImageData(d, 0, 0); return c.toDataURL("image/png");
}
function encodeInstances() {
  // 번호 = R + G*256 (서버 instances.py 가 이 규칙으로 읽는다). 회색(번호 없음)은 0 으로 보낸다.
  const c = document.createElement("canvas"); c.width = S.W; c.height = S.H;
  const x = c.getContext("2d"), d = x.createImageData(S.W, S.H), a = d.data;
  for (let i = 0; i < S.L.length; i++) {
    const v = S.L[i] === HOLE ? 0 : S.L[i];
    a[i * 4] = v & 255; a[i * 4 + 1] = v >> 8; a[i * 4 + 2] = 0; a[i * 4 + 3] = 255;
  }
  x.putImageData(d, 0, 0); return c.toDataURL("image/png");
}
function boxesNow() {
  const W = S.W, b = new Map();
  for (let i = 0; i < S.L.length; i++) {
    const v = S.L[i]; if (!v || v === HOLE) continue;
    const x = i % W, y = (i / W) | 0; let r = b.get(v);
    if (!r) b.set(v, r = [x, y, x, y, 0]);
    if (x < r[0]) r[0] = x; if (x > r[2]) r[2] = x; if (y < r[1]) r[1] = y; if (y > r[3]) r[3] = y; r[4]++;
  }
  return [...b.entries()].sort((p, q) => p[0] - q[0]).filter(([, r]) => r[4] >= 4)
    .map(([, r]) => ({ xyxy: [r[0], r[1], r[2] + 1, r[3] + 1], cls: "fruit", src: "human" }));
}
async function save() {
  if (!S.L || S.busy) return false;
  const by = who() || askWho();
  const { ids, hole } = idsNow();
  if (!ids.length && hole) { say("번호가 하나도 없습니다. 회색 열매를 채우기통으로 눌러 번호를 붙인 뒤 저장하세요.", "err"); return false; }
  S.busy = true; say("저장하는 중…");
  const base = { fruit: S.fruit, stem: S.stem, by };
  try {
    await postJSON("/api/save", { ...base, action: "fixed", png: encodeBinary(), note: "그림판 저장" });
    await postJSON("/api/status", { ...base, status: "fixed", confirm: true, kind: "mask", note: "그림판 저장" });
    if (ids.length) await postJSON("/api/save_instances", { ...base, png: encodeInstances(), counts: {}, note: "그림판 저장" });
    const boxes = boxesNow();
    await postJSON("/api/boxes", { ...base, boxes, note: "그림판 저장(번호마다 상자 하나)" });
    setDirty(false);
    const it = S.items.find((x) => x.stem === S.stem);
    if (it) { it.confirmed = "fixed"; it.confirmed_instances = ids.length ? "fixed" : null; }
    markOption();
    say(`저장했습니다 — 열매 ${ids.length}개 · 상자 ${boxes.length}개.`, "ok");
    return true;
  } catch (e) {
    say("저장 실패: " + e.message, "err"); return false;
  } finally { S.busy = false; }
}
function markOption() {
  const it = S.items.find((x) => x.stem === S.stem), o = $("#photo").selectedOptions[0];
  if (it && o) o.textContent = itemMark(it) + o.textContent.slice(2);
}
async function setExclude(on) {
  if (!S.L || S.busy) return;
  const by = who() || askWho(), base = { fruit: S.fruit, stem: S.stem, by };
  S.busy = true;                               // 기다리는 동안 사진을 못 넘긴다(검수 1회 지적 2)
  try {
    if (on) {
      await postJSON("/api/save", { ...base, action: "exclude", note: "그림판: 이 사진 빼기" });
      await postJSON("/api/status", { ...base, status: "exclude", confirm: true, kind: "mask", note: "그림판: 이 사진 빼기" });
    } else {
      await postJSON("/api/save", { ...base, action: "ok", note: "그림판: 빼기 취소" });
      await postJSON("/api/status", { ...base, status: "ok", confirm: true, kind: "mask", note: "그림판: 빼기 취소" });
    }
    const it = S.items.find((x) => x.stem === base.stem); if (it) it.confirmed = on ? "exclude" : "ok";
    markOption();
    say(on ? "이 사진을 «빼기» 로 표시했습니다. 다음 사진으로 넘어갑니다." : "빼기를 취소했습니다.", "ok");
  } catch (e) { say("실패: " + e.message, "err"); return; }
  finally { S.busy = false; }
  if (on && S.stem === base.stem && !S.dirty) go(1, true);
}

/* ── 사진 넘기기 ── */
async function go(d, skipAsk) {
  const sel = $("#photo"), i = sel.selectedIndex + d;
  if (i < 0 || i >= sel.options.length) return say(d > 0 ? "마지막 사진입니다." : "첫 사진입니다.");
  if (!skipAsk && !(await leaveOk())) return;
  sel.selectedIndex = i; openPhoto(sel.value);
}
async function leaveOk() {
  if (!S.dirty) return true;
  if (confirm("바뀐 것이 있습니다. 저장하고 넘어갈까요?\n(확인 = 저장하고 넘어감 · 취소 = 이 사진에 머무름)")) return await save();
  return false;
}
window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });

/* ── 단추·메뉴·단축키 연결 ── */
const ACTS = {
  save, undo, redo, new: newNumber,
  prev: () => go(-1), next: () => go(1),
  exclude: () => setExclude(true), unexclude: () => setExclude(false),
  "reload-orig": () => { if (confirm("원본(처음 받은 라벨)을 다시 불러올까요? 저장하기 전까지는 파일이 안 바뀝니다.")) openPhoto(S.stem, true); },
  "clear-all": () => {
    if (!S.L || !confirm("이 사진의 칠한 것을 전부 지울까요? (Ctrl+Z 로 되돌릴 수 있음)")) return;
    const before = snapshot(); S.L.fill(0); paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
    say("전부 지웠습니다. 열매가 없는 사진이면 «이 사진 빼기» 가 맞습니다.");
  },
  "toggle-color": () => { S.showColor = !S.showColor; applyView(); },
  orig: () => { S.showColor = !S.showColor; applyView(); },
  "toggle-nums": () => { S.showNums = !S.showNums; drawHud(); },
  fit: () => S.L && fit(),
  "draft-add": () => loadDraft(true),
  "split-gt": () => splitBy("gt"),
  "split-draft": () => splitBy("draft"),
  "draft-replace": () => { if (confirm("지금 칠한 것을 모델 초벌로 전부 바꿀까요? (Ctrl+Z 로 되돌릴 수 있음)")) loadDraft(false); },
};
document.addEventListener("click", (e) => {
  const mb = e.target.closest(".mbtn");
  document.querySelectorAll(".menu").forEach((m) => { if (!mb || m !== mb.parentElement) m.classList.remove("open"); });
  if (mb) { mb.parentElement.classList.toggle("open"); return; }
  const a = e.target.closest("[data-act]");
  if (a) { document.querySelectorAll(".menu").forEach((m) => m.classList.remove("open")); ACTS[a.dataset.act] && ACTS[a.dataset.act](); return; }
  const t = e.target.closest("[data-tool]"); if (t) return setTool(t.dataset.tool);
  const sw = e.target.closest(".sw[data-id]");
  if (sw) { setCur(+sw.dataset.id); if (S.tool === "fill" && S.fillNew) { S.fillNew = false; setTool("fill"); } if (!["brush", "fill", "lasso"].includes(S.tool)) setTool("brush"); }
});
$("#save").onclick = save;
$("#orig").onclick = () => ACTS.orig();
$("#prev").onclick = () => go(-1);
$("#next").onclick = () => go(1);
$("#fruit").onchange = async () => { if (await leaveOk()) { setDirty(false); S.stem = ""; loadList(); } };
$("#photo").onchange = async () => {
  const want = $("#photo").value;
  if (await leaveOk()) openPhoto(want); else $("#photo").value = S.stem;
};
$("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") renderList(S.stem); });
$("#only-todo").onchange = () => renderList(S.stem);
$("#alpha").oninput = () => { S.alpha = $("#alpha").value / 100; applyView(); };
$("#who").onclick = askWho;
window.addEventListener("resize", () => S.L && applyView());
window.addEventListener("blur", () => { if (S.peek) { S.peek = false; applyView(); } });   // 키를 뗀 걸 못 받아도 풀리게

document.addEventListener("keydown", (e) => {
  if (e.target.matches("input, select, textarea")) return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === "s") { e.preventDefault(); save(); return; }
  if ((e.ctrlKey || e.metaKey) && k === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
  if ((e.ctrlKey || e.metaKey) && k === "y") { e.preventDefault(); redo(); return; }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (k === " ") { spaceDown = true; stage.style.cursor = "grab"; e.preventDefault(); return; }
  if (e.key === "`" || e.code === "Backquote") { if (!S.peek) { S.peek = true; applyView(); } return; }
  if (TOOL_KEYS[k]) return setTool(TOOL_KEYS[k]);
  if (k === "n") return newNumber();
  if (k === "[") { S.size = Math.max(1, Math.round(S.size / 1.25)); return setTool(S.tool); }
  if (k === "]") { S.size = Math.min(200, Math.round(S.size * 1.25) + 1); return setTool(S.tool); }
  if (k === "v") return ACTS["toggle-color"]();
  if (k === "t") return ACTS["toggle-nums"]();
  if (k === "0") return ACTS.fit();
  if (k === "a" || e.key === "ArrowLeft") return go(-1);
  if (k === "d" || e.key === "ArrowRight") return go(1);
});
document.addEventListener("keyup", (e) => { if ((e.key === "`" || e.code === "Backquote") && S.peek) { S.peek = false; applyView(); } if (e.key === " ") { spaceDown = false; stage.style.cursor = S.tool === "hand" ? "grab" : "crosshair"; } });

/* ── 시작 ── */
(async function start() {
  $("#who").textContent = "작업자: " + (who() || "(눌러서 이름 적기)");
  setTool("brush");
  try { await loadFruits(); await loadList(); }
  catch (e) { say("시작 실패: " + e.message, "err"); }
})();
