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
  z: 1, ox: 0, oy: 0, alpha: 0.5, showColor: true, showNums: true, showCrop: false,
  undo: [], redo: [], dirty: false, busy: false, lastNew: 0, gen: 0, sim: null, sus: [], wl: null,
  ver: 0,                                          // 칠이 바뀐 횟수 — 저장하는 동안 또 바뀌었는지 본다(C22)
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
function say(text, kind) {
  const m = $("#msg");
  m.setAttribute("aria-live", kind === "err" ? "assertive" : "polite");   // 실패는 스크린리더가 바로 끊고 읽게(C09)
  m.textContent = text; m.className = kind || "";
  m.title = text;                          // 좁은 화면에서 잘려도 마우스를 올리면 전체가 보이게(C12)
}

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
  S.sample = sampleOf(S.fruit, items);
  // 초벌 헷갈림(ai_helper/draft/uncertainty.py 가 만든 것) — 없으면 빈 것(헷갈리는 순은 개수 차이만 본다)
  try { S.unc = await getJSON(`/static/paint/unc/${S.fruit}.json`); } catch (e) { S.unc = {}; }
  renderRule();
  renderList(keepStem);
  loadExports();
}
/* 과일별 규칙 한 줄(녹취 09-15 G78). 교수님 답이 나오기 전이라 «미정» 만 적는다 — 답이 나오면 이 글만 고치면 된다
   (근거: kds0206/문서/260917_교수님확인_7건.md 1·3·9·10번). 규칙이 정해진 과일은 줄을 숨긴다. */
const RULES = {
  apple: "사과 규칙 미정(교수님 답 대기) — 잎에 가려진 부분까지 칠할지(지금은 출처마다 다름) · 떨어진 사과·뒷줄 나무 사과를 셀지. 정해질 때까지 원본 모양은 그대로 둡니다.",
  grape: "포도 규칙 미정(교수님 답 대기) — 송이 단위인지 알 단위인지 · 지주대는 어떻게 할지. 지금은 송이 하나 = 색 하나로 칠합니다.",
};
function renderRule() {
  const r = $("#rule"), t = RULES[S.fruit] || "";
  r.textContent = t; r.title = t; r.hidden = !t;
}
/* 카운팅 표본(녹취 09-08 G74): 과일마다 «과일|이름» 의 해시가 작은 100장. 목록 순서·누가 여는지와 상관없이 늘 같은 100장이다.
   (사진이 새로 들어오면 해시가 더 작은 사진이 끼어들 수 있으니, 벤치마크를 확정할 때 목록을 따로 적어 둔다)
   FNV 만 쓰면 끝 글자만 다른 이름(1214·1215…= 이웃한 영상 장면)이 붙어서 뽑히므로 murmur3 마무리로 한 번 더 섞는다. */
const SAMPLE_N = 100;
function hash32(s) {
  let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35); h ^= h >>> 16;
  return h >>> 0;
}
function sampleOf(fruit, items) {
  const keyed = items.map((it) => [hash32(`count100|${fruit}|${it.stem}`), it.stem]);
  keyed.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : 1));
  return new Set(keyed.slice(0, SAMPLE_N).map((k) => k[1]));
}
/* «헷갈리는 순»(C15, 리서치 2위): 사람 미확정 사진을 앞에, 그 안에서 점수가 큰 순. 확정(✓·✕)한 사진은 뒤에 이름 순.
   점수 = (개수 차이 비율 + 초벌 헷갈림 unc) 의 평균, 있는 것만. 개수 차이 비율 = |초벌 확신 열매 수 − 라벨 열매 수| ÷ 둘 중 큰 수.
   초벌 확신 열매 수는 unc.sure(점수 0.5 이상), 라벨 열매 수는 목록의 n_inst(번호 개수 캐시). 둘 다 없으면 -1(미확정 중 맨 뒤).
   목록을 다시 그릴 때만 정렬한다 — 저장해도 순서가 그 자리에서 바뀌지 않아 «다음 사진» 이 그대로 이어진다. */
function uncScore(it) {
  const u = (S.unc || {})[it.stem], parts = [];
  if (u && it.n_inst != null) parts.push(Math.abs(u.sure - it.n_inst) / Math.max(u.sure, it.n_inst, 1));
  if (u && u.unc != null) parts.push(u.unc);
  return parts.length ? parts.reduce((a, b) => a + b, 0) / parts.length : -1;
}
function renderList(keepStem) {
  const q = $("#q").value.trim().toLowerCase();
  const todo = $("#only-todo").checked, samp = $("#only-sample").checked, byUnc = $("#sort").value === "unc";
  // 안 저장한 지금 사진은 조건에 안 맞아도 남긴다(C21) — 빠지면 첫 사진이 열려(openPhoto 는 dirty 를 안 봄) 칠한 것이 사라진다
  const keep = S.dirty ? S.stem : "";
  let shown = S.items.filter((it) => it.stem === keep || ((!q || it.stem.toLowerCase().includes(q)) && (!todo || itemMark(it) === "　") && (!samp || S.sample.has(it.stem))));
  const sc = new Map();
  if (byUnc) {
    shown.forEach((it) => sc.set(it.stem, itemMark(it) === "　" ? uncScore(it) : -2));
    shown = shown.slice().sort((a, b) => sc.get(b.stem) - sc.get(a.stem) || (a.stem < b.stem ? -1 : 1));
  }
  const tag = (it) => sc.get(it.stem) >= 0 ? ` · 헷갈림 ${sc.get(it.stem).toFixed(2)}` : "";
  const done = S.items.filter((it) => itemMark(it) === "✓ ").length;
  const sel = $("#photo");
  sel.innerHTML = shown.map((it, i) => `<option value="${it.stem}">${itemMark(it)}${i + 1}. ${it.stem}${tag(it)}</option>`).join("");
  sel.title = `전체 ${S.items.length}장 · 저장함 ${done}장 · 지금 목록 ${shown.length}장`;
  renderProgress();
  const want = keepStem && shown.some((it) => it.stem === keepStem) ? keepStem : (shown[0] || {}).stem;
  if (want) { sel.value = want; if (want !== S.stem || !S.L) openPhoto(want); }
  else { clearPhoto(); say("조건에 맞는 사진이 없습니다. «이름 찾기» 칸을 비우거나 «안 한 것만»·«표본 100장만» 을 끄세요."); }
}
/* 보여 줄 사진이 없으면 그림판을 비운다 — 다른 과일의 사진이 남아 있으면 그 위에 칠하고 엉뚱한 곳에 저장하려 하게 된다 */
function clearPhoto() {
  S.gen++;
  Object.assign(S, { stem: "", L: null, img: null, undo: [], redo: [], idsCache: null, draftIds: new Set(), sim: null, sus: [], wl: null });
  imgC.width = ovC.width = 0; world.style.width = world.style.height = "0px";
  centers = []; setDirty(false); drawHud();
  $("#t-name").textContent = "사진을 고르세요"; document.title = "라벨 그림판"; $("#swatches").innerHTML = ""; $("#count").textContent = "";
  $("#dupmenu").hidden = true;
}

/* ── 한 장 열기 ── */
const imgC = $("#img"), ovC = $("#ov"), hud = $("#hud"), stage = $("#stage"), world = $("#world");
const ovX = ovC.getContext("2d"), hudX = hud.getContext("2d");
let ovData = null, ovU32 = null;

/* 한 장에 필요한 것(상세·사진·번호 L)을 받아 푼다. item 을 주면 상세는 다시 안 받는다 */
async function loadBundle(f, stem, fromOriginal, item) {
  item = item || await getJSON(`/api/item?fruit=${f}&stem=${encodeURIComponent(stem)}`);
  const q = `fruit=${f}&stem=${encodeURIComponent(stem)}`;
  const img = new Image();
  img.src = "/img?" + q;
  const imgDone = img.decode().catch(() => { throw new Error("사진을 못 읽었습니다"); });
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
  return { item, img, L };
}

/* 미리 받기(C06): 한 장을 열면 목록의 앞·뒤 사진을 미리 받아 풀어 둔다 → 넘길 때 기다림이 거의 없다.
   낡은 번호로 덮어쓰지 않게(두번째의견 §2-1) — 넘길 때 /api/item 을 새로 받아 «상태 지문» 이 미리 받을 때와 같을 때만 쓴다
   (남이 그새 저장·확정·되돌리기를 했으면 지문이 달라져 새로 받는다). 원본 다시 불러오기는 미리 받은 것을 안 쓴다.
   내가 저장·빼기를 하면 그 사진 항목을 지운다. 10분 넘은 것은 버린다. */
const PF = new Map(), PF_TTL = 10 * 60e3;       // "과일|이름" → { t, p: Promise<{item,img,L}> }
// file_sig(C19) = 서버가 stat 으로 잰 번호·이진 마스크 파일 지문 — 같은 초에 두 번 저장해 at 이 같아도 잡는다
const itemSig = (it) => JSON.stringify([it.width, it.height, it.has_fixed, it.status, it.at, it.confirmed, it.confirmed_instances, it.counts, it.file_sig]);
function prefetchAround() {
  const sel = $("#photo"), i = sel.selectedIndex, want = new Map();
  if (i >= 0 && sel.value === S.stem) for (const d of [1, -1]) { const o = sel.options[i + d]; if (o) want.set(`${S.fruit}|${o.value}`, o.value); }
  for (const k of PF.keys()) if (!want.has(k)) PF.delete(k);
  for (const [k, stem] of want) {
    if (PF.has(k)) continue;
    const e = { t: Date.now(), p: loadBundle(S.fruit, stem, false) };
    e.p.catch(() => { if (PF.get(k) === e) PF.delete(k); });
    PF.set(k, e);
  }
}

async function openPhoto(stem, fromOriginal) {
  if (S.busy) { if (S.opening) S.pendingOpen = [stem, fromOriginal]; return; }   // 여는 중에 또 넘기면 마지막 것만 기억
  S.gen++;                                   // 이 값이 바뀌면 늦게 온 AI 답은 버린다(다른 사진에 붙지 않게)
  S.busy = S.opening = true; $("#loading").style.display = "block"; stage.setAttribute("aria-busy", "true");
  try {
    const f = S.fruit, key = `${f}|${stem}`, pf = !fromOriginal && PF.get(key);
    PF.delete(key);                          // 열고 나면 칠해서 바뀌므로 이 사진 항목은 남기지 않는다
    let b = null;
    if (pf && Date.now() - pf.t < PF_TTL) {
      const [item, got] = await Promise.all([getJSON(`/api/item?fruit=${f}&stem=${encodeURIComponent(stem)}`), pf.p.catch(() => null)]);
      b = got && itemSig(got.item) === itemSig(item) ? { ...got, item } : await loadBundle(f, stem, false, item);
      S.lastPrefetchHit = !!got && b.L === got.L;  // 시험용: 미리 받은 것을 썼나
    } else S.lastPrefetchHit = false;
    if (!b) b = await loadBundle(f, stem, fromOriginal);
    const { item, img, L } = b, W = item.width, H = item.height;
    Object.assign(S, { stem, W, H, L, img, undo: [], redo: [], item, draftIds: new Set(), gen: S.gen + 1, sim: null, sus: [] });
    if (S.tool === "sam") setTool("sam");     // 앞 사진의 «비슷한 열매» 단추를 지운다
    S.lastNew = maxId();
    S.cur = S.lastNew + 1;                       // 붓은 «새 열매» 색으로 시작한다
    computeCenters(); wlReset(centers.length);
    imgC.width = ovC.width = W; imgC.height = ovC.height = H;
    imgC.getContext("2d").drawImage(img, 0, 0);
    ovData = ovX.createImageData(W, H); ovU32 = new Uint32Array(ovData.data.buffer);
    paintRect(0, 0, W, H);
    world.style.width = W + "px"; world.style.height = H + "px";
    fit();
    setDirty(!!fromOriginal);
    $("#t-name").textContent = stem; document.title = `${stem} - 라벨 그림판`;   // 탭 제목에도 사진 이름(C09)
    $("#photo").value = stem;
    renderPalette(); renderCount(); renderDup();
    const it = S.items.find((x) => x.stem === stem) || {};
    const notRep = item.dup_rep && item.dup_rep !== stem && !it.confirmed;
    say(it.confirmed === "exclude" ? "이 사진은 «빼기» 로 표시돼 있습니다. (파일 → 빼기 취소)" :
      fromOriginal ? "원본을 다시 불러왔습니다. 저장해야 반영됩니다." :
      notRep ? `닮은 사진 묶음의 대표가 아닙니다(대표 ${item.dup_rep}). 위 «🔁 닮은 사진» 에서 «대표만 남기기» 를 누르세요.` :
      `${stem} 을(를) 열었습니다. 색 하나 = 열매 하나입니다.`, it.confirmed === "exclude" ? "err" : "");
    setTimeout(prefetchAround, 100);            // 이 사진이 먼저 그려지게 조금 뒤에
  } catch (e) {
    say("열기 실패: " + e.message, "err");
  } finally {
    S.busy = S.opening = false; $("#loading").style.display = "none"; stage.setAttribute("aria-busy", "false");
  }
  const p = S.pendingOpen; S.pendingOpen = null;
  if (p && p[0] !== S.stem) { if (S.dirty) $("#photo").value = S.stem; else openPhoto(...p); }
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
  $("#zpct").textContent = Math.round(S.z * 100) + "%";
  const show = S.showColor && !S.peek;         // peek = ` 키를 누르고 있는 동안
  ovC.style.opacity = show ? S.alpha : 0;
  const ob = document.querySelector("#orig");
  if (ob) { ob.classList.toggle("on", !show); ob.setAttribute("aria-pressed", String(!show)); ob.textContent = show ? "👁 원본 보기" : "🎨 색 다시 보기"; }
  drawHud();
}
/* 확대·옮기기는 «목표» 로 부드럽게 다가간다(약 0.15초). 목표가 없으면 지금 값이 목표다.
   연달아 휠을 굴리면 목표에 이어서 쌓이므로 빨리 굴려도 끊기지 않는다. */
let anim = null;
function viewTarget() { return anim ? anim.to : { z: S.z, ox: S.ox, oy: S.oy }; }
function stopAnim() { if (anim) { cancelAnimationFrame(anim.raf); anim = null; } }
function animateTo(to, smooth) {
  stopAnim();
  if (!smooth || matchMedia("(prefers-reduced-motion: reduce)").matches) { Object.assign(S, to); applyView(); return; }
  const from = { z: S.z, ox: S.ox, oy: S.oy }, t0 = performance.now(), dur = 150;
  anim = { to };
  const step = (now) => {
    const t = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - t, 3);      // 끝에서 천천히 멈춤
    // 확대율은 곱셈으로 섞어야 가까이 갈수록 속도가 고르다
    const z = from.z * Math.pow(to.z / from.z, e);
    // 화면에서 한 점이 제자리에 머물도록 ox 는 확대율에 맞춰 섞는다
    const k = to.z === from.z ? e : (z - from.z) / (to.z - from.z);
    S.z = z; S.ox = from.ox + (to.ox - from.ox) * k; S.oy = from.oy + (to.oy - from.oy) * k;
    applyView();
    if (t < 1) anim.raf = requestAnimationFrame(step); else anim = null;
  };
  anim.raf = requestAnimationFrame(step);
}
function fitView() {
  const r = stage.getBoundingClientRect(), z = Math.min(r.width / S.W, r.height / S.H) * 0.98;
  return { z, ox: (r.width - S.W * z) / 2, oy: (r.height - S.H * z) / 2 };
}
function fit(smooth) { animateTo(fitView(), smooth); }
function zoomAt(sx, sy, k) {
  const t = viewTarget(), nz = Math.max(0.05, Math.min(40, t.z * k));
  animateTo({ z: nz, ox: sx - (sx - t.ox) * nz / t.z, oy: sy - (sy - t.oy) * nz / t.z }, true);
}
/* 화면 가운데를 기준으로 확대·축소(단추·+/- 키) */
function zoomCenter(k) { const r = stage.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, k); }

/* 번호 글자·붓 동그라미·올가미 선 — 화면 크기 캔버스에 그린다 */
let centers = [], mouse = null, lassoPts = null;
const CROP = 512;
/* 번호마다 화소 수·x 합·y 합. 사진을 열 때 한 번 다 훑고, 그 뒤로는 바뀐 화소만 더하고 뺀다(C13 — 손 뗄 때 사진 전체를 훑던 12~30ms 를 없앰) */
const CN = new Uint32Array(65536), CX = new Float64Array(65536), CY = new Float64Array(65536);
function tally(i, from, to) {
  const x = i % S.W, y = (i / S.W) | 0;
  if (from) { CN[from]--; CX[from] -= x; CY[from] -= y; }
  if (to) { CN[to]++; CX[to] += x; CY[to] += y; }
}
function computeCenters() {
  CN.fill(0); CX.fill(0); CY.fill(0);
  const L = S.L, W = S.W, H = S.H;
  for (let y = 0, i = 0; y < H; y++) for (let x = 0; x < W; x++, i++) {
    const v = L[i]; if (!v) continue;
    CN[v]++; CX[v] += x; CY[v] += y;
  }
  buildCenters();
}
function buildCenters() {                          // 합에서 가운데·번호 목록·회색 여부를 만든다(65536 칸만 돈다)
  centers = []; const ids = [];
  for (let v = 1; v < HOLE; v++) if (CN[v]) { centers.push([v, CX[v] / CN[v], CY[v] / CN[v], CN[v]]); ids.push(v); }
  S.idsCache = { ids, hole: CN[HOLE] > 0 };
}
/* 저장 뒤 의심 열매(C16, 리서치 3위): 넓이·둥근 정도·맞닿음·떨어진 조각이 튀는 번호를 빨간 점선 동그라미로 보인다. 저장은 막지 않는다.
   기준값은 원본·초벌 번호 마스크 3,322개(사과·블루베리·복숭아 각 40장)에서 열매의 2~3% 만 걸리게 골랐다(tests/sim/c16_suspect_calib.py).
   둥근 정도 = 4π·넓이÷테두리² 를 원(π²/8, 화소 테두리 기준)으로 나눈 값. 맞닿음 = 테두리 중 다른 번호와 닿은 비율. */
const SUS = { small: 0.12, large: 6, round: 0.25, touch: 0.6, minN: 5 };
function suspects() {
  const L = S.L, W = S.W, N = L.length, P = new Uint32Array(65536), T = new Uint32Array(65536);
  const seen = new Uint8Array(N), stack = new Int32Array(N), parts = new Map();
  for (let i = 0; i < N; i++) {
    const v = L[i]; if (!v || v === HOLE) continue;
    const x = i % W; let edge = false, touch = false;
    for (const j of [x > 0 ? i - 1 : -1, x < W - 1 ? i + 1 : -1, i - W, i + W]) {
      if (j < 0 || j >= N) continue;
      const u = L[j]; if (u !== v) { edge = true; if (u && u !== HOLE) touch = true; }
    }
    if (edge) P[v]++; if (touch) T[v]++;
    if (seen[i]) continue;
    let sp = 0, n = 0; stack[sp++] = i; seen[i] = 1;              // 같은 번호로 이어진 조각(4-연결)의 크기
    while (sp) {
      const k = stack[--sp], kx = k % W; n++;
      if (kx > 0 && !seen[k - 1] && L[k - 1] === v) { seen[k - 1] = 1; stack[sp++] = k - 1; }
      if (kx < W - 1 && !seen[k + 1] && L[k + 1] === v) { seen[k + 1] = 1; stack[sp++] = k + 1; }
      if (k >= W && !seen[k - W] && L[k - W] === v) { seen[k - W] = 1; stack[sp++] = k - W; }
      if (k + W < N && !seen[k + W] && L[k + W] === v) { seen[k + W] = 1; stack[sp++] = k + W; }
    }
    (parts.get(v) || parts.set(v, []).get(v)).push(n);
  }
  const ids = [...parts.keys()].sort((a, b) => a - b), areas = ids.map((v) => CN[v]).sort((a, b) => a - b);
  const med = areas[areas.length >> 1] || 1, out = [];
  for (const v of ids) {
    const a = CN[v], why = [], rel = a / med;
    if (ids.length >= SUS.minN && rel < SUS.small) why.push(`넓이가 보통의 ${rel.toFixed(2)}배`);
    if (ids.length >= SUS.minN && rel > SUS.large) why.push(`넓이가 보통의 ${rel.toFixed(1)}배`);
    const rnd = Math.min(1, 4 * Math.PI * a / Math.max(P[v], 1) ** 2 / (Math.PI ** 2 / 8));
    if (rnd < SUS.round) why.push(`둥근 정도 ${rnd.toFixed(2)}`);
    if (T[v] / Math.max(P[v], 1) > SUS.touch) why.push("다른 열매에 둘러싸임");
    const ps = parts.get(v).sort((p, q) => q - p), extra = ps.slice(1).filter((n) => n >= Math.max(20, 0.1 * a)).length;
    if (extra) why.push(`떨어진 조각 ${extra + 1}개`);
    if (why.length) out.push({ v, why });
  }
  return out;
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
  if (S.sus && S.sus.length && S.showColor && !S.peek) {      // C16 의심 열매: 빨간 점선 동그라미(지운 번호는 건너뜀)
    hudX.setLineDash([5, 4]); hudX.lineWidth = 2; hudX.strokeStyle = "#ff2020";
    for (const { v } of S.sus) {
      if (!CN[v] || v === HOLE) continue;
      hudX.beginPath(); hudX.arc(S.ox + CX[v] / CN[v] * S.z, S.oy + CY[v] / CN[v] * S.z, Math.max(10, Math.sqrt(CN[v] / Math.PI) * S.z + 7), 0, Math.PI * 2);
      hudX.stroke();
    }
    hudX.setLineDash([]); hudX.strokeStyle = "#000";
  }
  if (S.showCrop) {                              // 512 크롭(녹취 08-10 G42): AI 가 한 번에 보는 크기. 학습은 아무 자리, 평가는 이 가운데 자리
    const cw = Math.min(CROP, S.W), ch = Math.min(CROP, S.H);
    const x = S.ox + Math.floor((S.W - cw) / 2) * S.z, y = S.oy + Math.floor((S.H - ch) / 2) * S.z;
    hudX.lineWidth = 2; hudX.strokeStyle = "#ff2020"; hudX.strokeRect(x, y, cw * S.z, ch * S.z);
    hudX.font = "bold 12px sans-serif"; hudX.textAlign = "left"; hudX.textBaseline = "bottom";
    hudX.lineWidth = 3; hudX.strokeStyle = "#000"; hudX.fillStyle = "#ff4040";
    hudX.strokeText(`${CROP}×${CROP}`, x + 2, y - 2); hudX.fillText(`${CROP}×${CROP}`, x + 2, y - 2);
    hudX.fillStyle = "#fff";
  }
  if (S.sim && simC) {                           // C14 비슷한 열매 후보(노란 테두리) — 화면에 보이는 부분만 옮겨 그린다
    const sx0 = Math.max(0, Math.floor(-S.ox / S.z)), sy0 = Math.max(0, Math.floor(-S.oy / S.z));
    const sx1 = Math.min(S.W, Math.ceil((hud.width - S.ox) / S.z)), sy1 = Math.min(S.H, Math.ceil((hud.height - S.oy) / S.z));
    if (sx1 > sx0 && sy1 > sy0) {
      hudX.imageSmoothingEnabled = false;
      hudX.drawImage(simC, sx0, sy0, sx1 - sx0, sy1 - sy0, S.ox + sx0 * S.z, S.oy + sy0 * S.z, (sx1 - sx0) * S.z, (sy1 - sy0) * S.z);
      hudX.imageSmoothingEnabled = true;
    }
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
    const i = (y0 + y) * S.W + x0 + x; data[y * w + x] = before[i];
    if (before[i] !== S.L[i]) { same = false; tally(i, before[i], S.L[i]); }
  }
  if (same) return;
  if (S.wl) S.wl.edits++;
  S.undo.push({ x0, y0, w, h, data }); if (S.undo.length > UNDO_MAX) S.undo.shift();
  // 전체 사진 크기 기록(초벌·나누기·전부 지우기)이 쌓여도 약 120MB 를 넘지 않게 오래된 것부터 버린다
  let bytes = 0; for (const r of S.undo) bytes += r.data.byteLength;
  while (bytes > 120e6 && S.undo.length > 1) bytes -= S.undo.shift().data.byteLength;
  S.redo = [];
  changed();
}
function swapRect(rec) {
  const { x0, y0, w, h, data } = rec;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y0 + y) * S.W + x0 + x, t = S.L[i]; S.L[i] = data[y * w + x]; data[y * w + x] = t;
    if (t !== S.L[i]) tally(i, t, S.L[i]);
  }
  paintRect(x0, y0, w, h);
}
function undo(auto) { if (auto !== true && waitBusy()) return; const r = S.undo.pop(); if (!r) return say("더 되돌릴 것이 없습니다."); swapRect(r); S.redo.push(r); if (S.wl && auto !== true) S.wl.undos++; changed(); }
function redo() { if (waitBusy()) return; const r = S.redo.pop(); if (!r) return say("다시 할 것이 없습니다."); swapRect(r); S.undo.push(r); if (S.wl) S.wl.redos++; changed(); }
function changed() { S.ver++; setDirty(true); buildCenters(); renderPalette(); renderCount(); drawHud(); }
/* 저장·사진 열기를 기다리는 동안(S.busy)에는 칠을 바꾸는 단추·단축키를 안 받는다(C22) — 붓·채우기는 mousedown 에서 이미 막는다 */
function waitBusy() { if (S.busy) say("저장·사진 열기가 끝난 뒤 다시 하세요."); return S.busy; }
function setDirty(d) {
  S.dirty = d; $("#t-dirty").textContent = d ? "● 저장 안 됨" : "";
  $("#save").classList.toggle("dirty", d);
}

/* ── 작업 기록(C18): 사진당 작업 시간·수정 횟수 → 저장·빼기 때 서버 app/logs/worklog.jsonl 에 한 줄 ──
   active = 마우스·키 입력 사이 간격의 합(한 간격은 WL_IDLE 까지만 — 자리를 비운 시간은 안 센다). wall = 열고 나서 흐른 시간.
   edits = 칠이 실제로 바뀐 동작 수(붓 한 번·채우기·✨ 하나…), sam = ✨ 도우미 부른 수. 저장하면 0 부터 다시 센다(두 번째 저장은 더 한 일만). */
const WL_IDLE = 60e3;
function wlReset(n) { const t = Date.now(); S.wl = { t0: t, last: t, active: 0, edits: 0, undos: 0, redos: 0, sam: 0, n0: n }; }
function wlTick() { if (!S.wl) return; const t = Date.now(); S.wl.active += Math.min(t - S.wl.last, WL_IDLE); S.wl.last = t; }
function wlSend(action, base, n) {
  const w = S.wl; if (!w) return;
  const body = { ...base, action, active_s: w.active / 1e3, wall_s: (Date.now() - w.t0) / 1e3, edits: w.edits, undos: w.undos,
    redos: w.redos, sam: w.sam, n_open: w.n0, n_save: n };
  S.lastWork = body;                               // 시험용
  postJSON("/api/worklog", body).catch(() => {});   // 기록이 안 돼도 저장은 이미 끝났다 — 사람에게 알리지 않는다
  wlReset(n);
}
for (const ev of ["pointerdown", "pointerup", "keydown", "wheel"]) document.addEventListener(ev, wlTick, { capture: true, passive: true });
// 누른 채 끄는 동안(붓·올가미·옮기기)도 활동이다(C25) — 안 세면 60초 넘게 끈 붓질이 60초로 잘렸다. 100ms 에 한 번만 세도 간격은 다음 tick 이 다 더하므로 빠지는 시간이 없다
document.addEventListener("pointermove", (e) => { if (e.buttons && S.wl && Date.now() - S.wl.last >= 100) wlTick(); }, { capture: true, passive: true });

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

/* ✨ 오른쪽 클릭: 누른 열매 번호를 통째로(떨어진 조각까지) 지운다. 회색·빈 곳은 채우기통과 같이 덩어리만 */
function eraseId(x, y) {
  const v = S.L[y * S.W + x];
  if (v === 0 || v === HOLE) return fillAt(x, y, 0);
  const L = S.L, W = S.W, before = snapshot();
  let x0 = W, y0 = S.H, x1 = -1, y1 = -1;
  for (let i = 0; i < L.length; i++) if (L[i] === v) {
    L[i] = 0; const px = i % W, py = (i / W) | 0;
    if (px < x0) x0 = px; if (px > x1) x1 = px; if (py < y0) y0 = py; if (py > y1) y1 = py;
  }
  paintRect(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
  pushUndo(before, x0, y0, x1 + 1, y1 + 1);
  say(`${v}번 열매를 통째로 지웠습니다. (Ctrl+Z 로 되돌리기)`);
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
/* ✨ 계산 중에는 그림 위 커서를 «기다림(progress)» 으로(C13) — 원격에서 1~2초 걸리면 «눌렸나?» 싶지 않게 */
function samBusy(on) { S.samBusy = on; stage.classList.toggle("sambusy", on); if (on && S.wl) S.wl.sam++; }   // ✨ 요청마다 한 번 = 도우미 부른 횟수(C18)
async function maskFromPng(b64, w, h) {
  const im = new Image(); im.src = "data:image/png;base64," + b64; await im.decode();
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d"); x.drawImage(im, 0, 0);
  return x.getImageData(0, 0, w, h).data;
}
/* ✨ 결과가 잎·가지처럼 길쭉하거나 너무 크면 경고(C17, 리서치 4위). 칠하기는 그대로 하고 알림 줄에 빨간 글씨로만 알린다.
   기준값은 원본·초벌 번호 마스크 3,321개에서 열매의 1% 미만만 걸리게 골랐다(tests/sim/c17_sam_shape_calib.py → tests/_out/c17/calib.tsv).
   길쭉함 = 긴 축÷짧은 축(화소 분포의 2차 모멘트), 둥근 정도는 C16 과 같은 계산. 넓이 = 사진 대비, 또는 다른 열매 가운데값 대비(SUS.large). */
const SAMW = { elong: 3.5, round: 0.2, img: 0.1 };
function samShapeWarn(a, cd, val) {
  const w = cd.w, h = cd.h, on = (x, y) => x >= 0 && y >= 0 && x < w && y < h && a[(y * w + x) * 4] >= 128;
  let n = 0, sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0, p = 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (!on(x, y)) continue;
    n++; sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y;
    if (!on(x - 1, y) || !on(x + 1, y) || !on(x, y - 1) || !on(x, y + 1)) p++;
  }
  if (n < 30) return "";
  const mx = sx / n, my = sy / n, cxx = sxx / n - mx * mx, cyy = syy / n - my * my, cxy = sxy / n - mx * my;
  const t = (cxx + cyy) / 2, d = Math.sqrt(((cxx - cyy) / 2) ** 2 + cxy ** 2);
  const el = Math.sqrt((t + d + 1 / 12) / (t - d + 1 / 12));
  const rnd = Math.min(1, 4 * Math.PI * n / Math.max(p, 1) ** 2 / (Math.PI ** 2 / 8));
  const why = [];
  if (el > SAMW.elong) why.push(`길쭉함(${el.toFixed(1)}배)`);
  else if (rnd < SAMW.round) why.push(`둥근 정도 ${rnd.toFixed(2)}`);
  const areas = [];
  for (let v = 1; v < HOLE; v++) if (CN[v] && v !== val) areas.push(CN[v]);
  areas.sort((x, y) => x - y);
  const rel = areas.length >= SUS.minN ? n / areas[areas.length >> 1] : 0;
  if (n / S.L.length > SAMW.img) why.push(`사진의 ${Math.round(n / S.L.length * 100)}%`);
  else if (rel > SUS.large) why.push(`다른 열매의 ${rel.toFixed(1)}배 크기`);
  return why.length ? ` ⚠ 잎·가지·배경일 수 있습니다 — ${why.join(", ")}.` : "";
}
async function applyCand(cd, val, g) {
  const a = await maskFromPng(cd.png, cd.w, cd.h);
  if (g !== undefined && stale(g)) return false;
  if (cd.warn === undefined) cd.warn = samShapeWarn(a, cd, val);
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
    if (samLast.applied) undo(true);          // ✨ 다음 후보로 바꾸기 — 사람의 되돌리기로 세지 않는다(C18)
    samLast.k = (samLast.k + 1) % samLast.cands.length;
    samLast.applied = await applyCand(samLast.cands[samLast.k], samLast.val, S.gen);
    const cw = samLast.applied ? samLast.cands[samLast.k].warn || "" : "";
    say(`${samLast.k + 1}/${samLast.cands.length}번째 모양입니다. 또 누르면 다음 모양.${cw}`, cw ? "err" : undefined);
    return;
  }
  const here = S.L[iy * S.W + ix];
  if (here && here !== HOLE && S.protect) {
    say(`이미 ${here}번 열매입니다. 모양을 바꾸려면 오른쪽 클릭으로 지운 뒤 다시 누르세요.`); return;
  }
  samBusy(true); say("✨ 모양 찾는 중…");
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
    const cw = samLast.applied ? j.cands[0].warn || "" : "";
    say(samLast.applied ? `${val}번으로 칠했습니다 (${j.sec}초). 모양이 이상하면 같은 자리를 다시 누르세요 — 후보 ${j.cands.length}개.${cw}`
      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).", cw ? "err" : undefined);
  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
  finally { samBusy(false); }
}

/* Shift+클릭 = «여기는 아니다»: 누른 곳의 모양(가장 작은 후보)을 ✨ 로 찾아, 방금 칠한 열매에서 그만큼 잘라 낸다.
   (SAM 의 «빼기 점» 은 한 번으로는 거의 안 먹어서 이렇게 한다 — 붙은 블루베리 옆 알을 떼어 낼 때 쓴다) */
async function samNeg(ix, iy) {
  if (!samLast || samLast.stem !== S.stem) return say("먼저 ✨ 로 열매를 칠한 뒤, 잘못 칠해진 부분을 Shift+클릭하세요.");
  const val = samLast.val;
  if (S.L[iy * S.W + ix] !== val) return say(`거기는 ${val}번이 아닙니다. 방금 칠한 ${val}번 안의 잘못된 부분을 Shift+클릭하세요.`);
  if (S.samBusy) return;
  samBusy(true); say("✨ 떼어 낼 부분을 찾는 중…");
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
  finally { samBusy(false); }
}
/* 끌어서 네모 = 그 안의 열매 하나를 칠한다(작은 열매·붙은 열매에 좋다) */
async function samBox(box) {
  if (S.samBusy) return;
  if (box[2] - box[0] < 3 || box[3] - box[1] < 3) return;
  samBusy(true); say("✨ 네모 안의 열매를 찾는 중…");
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
    const cw = samLast.applied ? j.cands[0].warn || "" : "";
    say(samLast.applied ? `네모 안을 ${val}번으로 칠했습니다. 잘못 칠한 곳은 Shift+클릭으로 뺄 수 있습니다.${cw}`
      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).", cw ? "err" : undefined);
  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
  finally { samBusy(false); }
}

/* ✨ 비슷한 열매 한꺼번에 찾기(C14, 리서치 1위): 지금 색(번호)의 열매를 본보기로 도우미가 사진 전체에서 크기·둥근 정도·색·SAM 특징이
   비슷한 모양을 찾아 노란 테두리 후보로 보인다. 후보를 누르면 뺌(빨간 테두리)/다시 넣음, «모두 받기»(Enter) = 남은 후보마다 새 번호, Esc = 취소.
   이미 칠한 곳과 30% 넘게 겹치는 후보는 처음부터 뺀다. 받을 때도 빈 곳(회색 포함)에만 칠하고, 반도 못 칠하는 후보는 건너뛴다. */
let simC = null, simD = null;
function exemplarOf(v) {                           // v 번 열매의 바깥 네모와 0/255 PNG(도우미 /sam 후보와 같은 꼴)
  const L = S.L, W = S.W;
  let x0 = W, y0 = S.H, x1 = -1, y1 = -1;
  for (let i = 0; i < L.length; i++) if (L[i] === v) {
    const x = i % W, y = (i / W) | 0;
    if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  const w = x1 - x0 + 1, h = y1 - y0 + 1, c = document.createElement("canvas"); c.width = w; c.height = h;
  const cx = c.getContext("2d"), d = cx.createImageData(w, h), u = new Uint32Array(d.data.buffer);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) u[y * w + x] = L[(y0 + y) * W + x0 + x] === v ? 0xffffffff : 0xff000000;
  cx.putImageData(d, 0, 0);
  return { x0, y0, png: c.toDataURL("image/png").split(",")[1] };
}
function simPaint(c) {                             // 후보 하나를 simC 에 그린다: 넣음 = 노란 칠 + 노란 테두리, 뺌 = 빨간 테두리만
  const u = new Uint32Array(simD.data.buffer), W = S.W, { x0, y0, w, h, m } = c;
  const fill = c.on ? 0x5000e0ff : 0, edge = c.on ? 0xff00e0ff : 0xff2020ff;    // ABGR
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const k = y * w + x; if (!m[k]) continue;
    const e = x === 0 || y === 0 || x === w - 1 || y === h - 1 || !m[k - 1] || !m[k + 1] || !m[k - w] || !m[k + w];
    u[(y0 + y) * W + x0 + x] = e ? edge : fill;
  }
  simC.getContext("2d").putImageData(simD, 0, 0, x0, y0, w, h);
}
function simClear(msg) {
  const had = !!S.sim;
  S.sim = null;
  if (S.tool === "sam") setTool("sam"); else drawHud();
  if (had && msg) say("비슷한 열매 후보를 버렸습니다.");
}
async function samSimilar() {
  if (!S.L || S.busy || S.samBusy) return;
  const v = S.cur;
  if (!v || v === HOLE || !CN[v]) return say("본보기로 쓸 열매가 없습니다. ✨ 로 열매 하나를 칠하거나 팔레트에서 그 열매 색을 고른 뒤 G 를 누르세요.", "err");
  simClear();
  if (S.tool !== "sam") setTool("sam");
  samBusy(true); say(`✨ ${v}번과 비슷한 열매를 사진 전체에서 찾는 중… (몇 초 걸립니다)`);
  const g = S.gen;
  try {
    const j = await postJSON("/api/sam_similar", { fruit: S.fruit, stem: S.stem, ex: exemplarOf(v) });
    if (stale(g)) return;
    const cands = [], L = S.L;
    for (const cd of j.cands || []) {
      const a = await maskFromPng(cd.png, cd.w, cd.h);
      if (stale(g)) return;
      const m = new Uint8Array(cd.w * cd.h);
      let n = 0, busy = 0;
      for (let yy = 0; yy < cd.h; yy++) for (let xx = 0; xx < cd.w; xx++) {
        const k = yy * cd.w + xx; if (a[k * 4] < 128) continue;
        m[k] = 1; n++;
        const l = L[(cd.y0 + yy) * S.W + cd.x0 + xx]; if (l && l !== HOLE) busy++;
      }
      if (n && busy <= 0.3 * n) cands.push({ x0: cd.x0, y0: cd.y0, w: cd.w, h: cd.h, m, n, on: true });
    }
    if (!cands.length) return say(`${v}번과 비슷한 열매를 더 찾지 못했습니다(${j.sec}초). 다른 열매를 본보기로 골라 보세요.`);
    if (!simC || simC.width !== S.W || simC.height !== S.H) { simC = document.createElement("canvas"); simC.width = S.W; simC.height = S.H; }
    simD = simC.getContext("2d").createImageData(S.W, S.H);
    simC.getContext("2d").clearRect(0, 0, S.W, S.H);
    S.sim = { gen: S.gen, v, cands };
    cands.forEach(simPaint);
    setTool("sam");
    say(`비슷한 열매 후보 ${cands.length}개(노란 테두리, ${j.sec}초). 틀린 후보는 눌러서 빼고 «모두 받기»(Enter). 취소 = Esc.`, "ok");
  } catch (e) { say("비슷한 열매 찾기 실패: " + e.message, "err"); }
  finally { samBusy(false); }
}
function simToggleAt(ix, iy) {                     // 누른 자리의 후보를 뺌↔넣음. 후보가 아니면 false
  const sm = S.sim; if (!sm) return false;
  const c = sm.cands.find((c) => ix >= c.x0 && iy >= c.y0 && ix < c.x0 + c.w && iy < c.y0 + c.h && c.m[(iy - c.y0) * c.w + ix - c.x0]);
  if (!c) return false;
  c.on = !c.on; simPaint(c); setTool("sam");
  const n = sm.cands.filter((c) => c.on).length;
  say(`${c.on ? "다시 넣었습니다" : "뺐습니다"} — 받을 후보 ${n}/${sm.cands.length}개. «모두 받기»(Enter).`);
  return true;
}
function simAccept() {
  const sm = S.sim;
  if (!sm || !S.L) return say("받을 후보가 없습니다. G 로 먼저 찾으세요.");
  if (waitBusy()) return;
  const before = snapshot(), L = S.L, W = S.W;
  let next = Math.max(maxId(), S.lastNew), got = 0, skip = 0, bx0 = W, by0 = S.H, bx1 = 0, by1 = 0;
  for (const c of sm.cands) {
    if (!c.on) continue;
    let free = 0;
    for (let yy = 0; yy < c.h; yy++) for (let xx = 0; xx < c.w; xx++) {
      if (!c.m[yy * c.w + xx]) continue;
      const l = L[(c.y0 + yy) * W + c.x0 + xx]; if (!l || l === HOLE) free++;
    }
    if (free < 0.5 * c.n) { skip++; continue; }      // 그새 다른 열매로 칠한 자리
    const v = ++next; got++; S.draftIds.add(v);
    for (let yy = 0; yy < c.h; yy++) for (let xx = 0; xx < c.w; xx++) {
      if (!c.m[yy * c.w + xx]) continue;
      const i = (c.y0 + yy) * W + c.x0 + xx; if (!L[i] || L[i] === HOLE) L[i] = v;
    }
    bx0 = Math.min(bx0, c.x0); by0 = Math.min(by0, c.y0); bx1 = Math.max(bx1, c.x0 + c.w); by1 = Math.max(by1, c.y0 + c.h);
  }
  S.sim = null;
  if (got) { S.lastNew = next; paintRect(bx0, by0, bx1 - bx0, by1 - by0); pushUndo(before, bx0, by0, bx1, by1); }
  setTool(S.tool);
  say(got ? `비슷한 열매 ${got}개를 새 번호로 칠했습니다(노란 동그라미)` + (skip ? ` · ${skip}개는 그새 칠한 자리라 건너뜀` : "") + ". Ctrl+Z 로 한 번에 되돌립니다."
    : "받을 후보가 없었습니다(모두 뺐거나 이미 칠한 자리).", got ? "ok" : "");
}

/* 모델 초벌: 미리 만든 번호 마스크(/draft)를 불러온다 — add = 빈 자리의 열매만 더하기, 아니면 전부 바꾸기 */
async function loadDraft(add) {
  if (!S.L || waitBusy()) return;
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
  if (!S.L || waitBusy()) return;
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
  if (!S.L || waitBusy()) return;
  S.lastNew = Math.max(maxId(), S.lastNew) + 1;
  setCur(S.lastNew);
  say(`새 번호 ${S.cur}번. 이 색으로 열매 하나를 칠하세요.`);
}
function setCur(v) {
  S.cur = v;
  $("#cur-sw").style.background = cssOf(v);
  $("#cur-txt").textContent = v ? v + "번" : "지우기";
  document.querySelectorAll(".sw[data-id]").forEach((e) => { const on = +e.dataset.id === v; e.classList.toggle("on", on); e.setAttribute("aria-pressed", on); });
}
const HOLE_TIP = "원본에 칠해져 있지만 번호가 없는 곳. 채우기통으로 누르면 번호가 붙습니다";
function renderPalette() {
  const { ids, hole } = S.idsCache || idsNow();
  const box = $("#swatches");
  // 색 칸은 Tab 으로 가서 Enter·스페이스로 고른다(C08) — role=button 이면 아래 keydown 이 click 으로 바꿔 준다
  const B = `role="button" tabindex="0"`;
  let h = `<div class="sw erase" ${B} data-id="0" title="배경색(지우기). 이 색으로 칠하면 지워집니다">지우기</div>`;
  h += `<div class="sw new" ${B} data-act="new" title="새 번호 (N)">＋</div>`;
  if (hole) h += `<div class="sw hole" ${B} data-act="hole-info" title="${HOLE_TIP}">?</div>`;
  if (S.cur && !ids.includes(S.cur)) h += `<div class="sw" ${B} data-id="${S.cur}" style="background:${cssOf(S.cur)}" title="${S.cur}번 (아직 안 칠함)">${S.cur}</div>`;
  for (const v of ids) h += `<div class="sw" ${B} data-id="${v}" style="background:${cssOf(v)}" title="${v}번">${v}</div>`;
  box.innerHTML = h;
  setCur(S.cur);
}
function renderCount() {
  const { ids, hole } = S.idsCache || idsNow();
  $("#count").textContent = `열매 ${ids.length}개` + (hole ? " · 회색(번호 없음) 있음" : "");
}
/* 진행: 이 과일에서 저장(✓)·뺌(✕)한 사진 수 + 카운팅 표본 중 저장(✓)한 수(뺀 사진은 개수 정답이 아니므로 따로) */
function renderProgress() {
  const n = S.items.length, done = S.items.filter((it) => itemMark(it) !== "　").length;
  const sm = S.items.filter((it) => S.sample && S.sample.has(it.stem));
  const sOk = sm.filter((it) => itemMark(it) === "✓ ").length, sEx = sm.filter((it) => itemMark(it) === "✕ ").length;
  $("#prog").textContent = n ? `진행 ${done}/${n} (${Math.round(done * 100 / n)}%) · 표본 ${sOk}/${sm.length} 확정` + (sEx ? ` (뺌 ${sEx})` : "") : "";
  renderExport();
}
/* 재학습 고리의 첫 단계(녹취 09-08 G73): 사람 확정(✓) 수 + 이 과일을 마지막으로 내보낸 시각 + 옛 툴 «데이터 정리» 탭 링크.
   실제 재학습은 GPU 스크립트라 툴은 여기까지만. 내보내기는 다른 창(옛 툴)에서 하므로 이 창으로 돌아오면(focus) 다시 읽는다. */
S.exports = null;                                  // /api/export_list 의 items (새것이 앞) · null = 못 읽음
async function loadExports() {
  try { S.exports = (await getJSON("/api/export_list")).items || []; } catch (e) { S.exports = null; }
  renderExport();
}
function renderExport() {
  const ok = S.items.filter((it) => itemMark(it) === "✓ ").length;
  const last = (S.exports || []).find((x) => x.fruit === S.fruit && x.state === "done" && !x.empty);
  const t = S.exports === null ? "내보내기 기록을 못 읽음"
    : last ? `마지막 내보내기 ${String(last.finished || "").slice(5, 16)} (${last.n_images || 0}장)` : "아직 내보낸 적 없음";
  $("#exp-txt").textContent = S.fruit ? `사람 확정 ${ok}장 · ${t}` : "";
  $("#exp-link").href = "/old#exp=" + S.fruit;
}

/* ── 도구·옵션 상자 ── */
const TOOL_KEYS = { b: "brush", e: "eraser", f: "fill", l: "lasso", i: "pick", z: "zoom", h: "hand", s: "sam" };
const SMALL = matchMedia("(max-width: 1024px), (max-height: 640px)");   // paint.css 의 작은 화면 규칙과 같은 기준
let tipOpen = false;                     // 작은 화면에서 사람이 «설명» 을 펼쳤는지(도구를 바꿔도 유지)
SMALL.addEventListener("change", () => { $("#options").innerHTML = ""; tipOpen = false; setTool(S.tool); });   // 화면 크기가 바뀌면 기본값(작으면 접힘)으로
function setTool(t) {
  S.tool = t;
  document.querySelectorAll("#tools [data-tool]").forEach((b) => { b.classList.toggle("on", b.dataset.tool === t); b.setAttribute("aria-pressed", String(b.dataset.tool === t)); });
  const o = $("#options");
  const sizes = [4, 8, 16, 32, 64];
  const sizeHtml = `<div>굵기 <b id="sz">${S.size}</b></div><div class="sizes">` +
    sizes.map((s) => `<button class="optbtn${s === S.size ? " on" : ""}" data-size="${s}">● ${s}</button>`).join("") + `</div>`;
  const protect = `<label><input type="checkbox" id="protect"${S.protect ? " checked" : ""}> 다른 열매 위에는 안 칠함</label>`;
  // [설명, 조절 칸] — 작은 화면(1024×640 이하)에서는 설명만 접는다(C12)
  const help = {
    brush: ["왼쪽 = 지금 색으로 칠하기<br>오른쪽 = 지우기", sizeHtml + protect],
    eraser: ["끌어서 지우기(마스크와 번호가 같이 지워짐)", sizeHtml],
    fill: ["칠한 덩어리를 누르면 지금 색이 됩니다.<br>오른쪽 = 덩어리 통째로 지우기",
      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호 (열매 세기)</label>` +
      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로 (가려진 조각 합치기)</label>`],
    lasso: ["열매 테두리를 따라 그리고 손을 떼면 안이 칠해집니다.<br>오른쪽 = 그 안 지우기", protect],
    pick: ["열매를 누르면 그 색(번호)을 집습니다.", ""],
    sam: ["열매를 누르면 AI 가 모양대로 칠합니다.<br>같은 자리를 <b>다시 누르면</b> 다른 모양(작게/크게).<br><b>끌어서 네모</b> = 그 안의 열매 하나<br><b>Shift+클릭</b> = 방금 칠한 것에서 «여기는 아님»<br>오른쪽 = 그 열매 통째로 지우기<br><b>G</b> = 지금 색 열매와 비슷한 것 한꺼번에 찾기",
      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호</label>` +
      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로</label>` + protect + simHtml()],
    zoom: ["왼쪽 = 확대 · 오른쪽 = 축소<br>(휠로도 됩니다)", ""],
    hand: ["끌어서 옮깁니다.<br>(다른 도구에서도 스페이스를 누른 채 끌면 됩니다)", ""],
  }[t];
  const prev = o.querySelector(".tip");
  if (prev && SMALL.matches) tipOpen = prev.open;    // toggle 이벤트는 늦게 와서, 다시 그리기 직전에 지금 상태를 직접 읽는다
  const open = !SMALL.matches || tipOpen;
  o.innerHTML = `<details class="tip"${open ? " open" : ""}><summary>설명</summary>${help[0]}</details>` + help[1];
  o.querySelectorAll("[data-size]").forEach((b) => b.onclick = () => { S.size = +b.dataset.size; setTool(S.tool); });
  const p = o.querySelector("#protect"); if (p) p.onchange = () => { S.protect = p.checked; };
  o.querySelectorAll("input[name=fm]").forEach((r) => r.onchange = () => { S.fillNew = r.value === "new"; });
  stage.style.cursor = t === "hand" ? "grab" : t === "zoom" ? "zoom-in" : t === "sam" ? "cell" : "crosshair";
  drawHud();
}

function simHtml() {                               // ✨ 옵션 칸 아래: 찾기 단추, 후보가 있으면 받기·취소
  if (!S.sim) return `<div class="sizes"><button class="optbtn" data-act="sim-find" title="지금 색(번호) 열매를 본보기로 사진 전체에서 비슷한 열매를 찾습니다 (G)">🔍 비슷한 열매 찾기 (G)</button></div>`;
  const n = S.sim.cands.filter((c) => c.on).length;
  return `<div>후보 <b id="sim-n">${n}/${S.sim.cands.length}</b>개 · 눌러서 빼기</div><div class="sizes">` +
    `<button class="optbtn on" data-act="sim-accept" title="남은 후보마다 새 번호로 칠합니다 (Enter)">✔ 모두 받기 (Enter)</button>` +
    `<button class="optbtn" data-act="sim-cancel" title="후보를 버립니다 (Esc)">✕ 취소 (Esc)</button></div>`;
}

/* ── 마우스 ── */
let drag = null, spaceDown = false;
function toImg(e) {
  const r = stage.getBoundingClientRect(), sx = e.clientX - r.left, sy = e.clientY - r.top;
  return { sx, sy, x: (sx - S.ox) / S.z, y: (sy - S.oy) / S.z };
}
stage.addEventListener("contextmenu", (e) => e.preventDefault());
stage.addEventListener("mousedown", (e) => {
  if (!S.L || S.busy || e.target.closest("#zoombar")) return;      // 확대 단추를 누를 때 그림에 칠해지지 않게
  const p = toImg(e), right = e.button === 2;
  if (e.button === 1 || spaceDown || S.tool === "hand") { stopAnim(); drag = { kind: "pan", sx: p.sx, sy: p.sy, ox: S.ox, oy: S.oy }; stage.style.cursor = "grabbing"; return; }
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
    if (right) { eraseId(ix, iy); return; }
    if (!e.shiftKey && simToggleAt(ix, iy)) return;     // C14 후보를 누르면 뺌↔넣음
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
  const dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1);
  const p = toImg(e); zoomAt(p.sx, p.sy, Math.exp(-Math.max(-300, Math.min(300, dy)) * 0.0014));
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
  // 세 파일(이진·번호·상자)을 같은 순간의 칠로 만든다 — 기다리는 사이 ✨ 답이 와서 칠이 바뀌어도 서로 어긋나지 않게(C22)
  const ver = S.ver, bin = encodeBinary(), inst = ids.length ? encodeInstances() : null, boxes = boxesNow();
  try {
    await postJSON("/api/save", { ...base, action: "fixed", png: bin, note: "그림판 저장" });
    await postJSON("/api/status", { ...base, status: "fixed", confirm: true, kind: "mask", note: "그림판 저장" });
    if (inst) await postJSON("/api/save_instances", { ...base, png: inst, counts: {}, note: "그림판 저장" });
    await postJSON("/api/boxes", { ...base, boxes, note: "그림판 저장(번호마다 상자 하나)" });
    const later = S.ver !== ver;                   // 저장하는 사이 바뀐 칠은 «저장 안 됨» 으로 남긴다
    setDirty(later); PF.delete(`${S.fruit}|${S.stem}`);
    wlSend("save", base, ids.length);
    const it = S.items.find((x) => x.stem === S.stem);
    if (it) { it.confirmed = "fixed"; it.confirmed_instances = ids.length ? "fixed" : null; }
    markOption();
    S.sus = suspects(); drawHud();
    const sus = S.sus.slice(0, 3).map((s) => `${s.v}번 ${s.why.join("·")}`).join(", ") + (S.sus.length > 3 ? " …" : "");
    say(`저장했습니다 — 열매 ${ids.length}개 · 상자 ${boxes.length}개.` + (later ? " 저장하는 사이 바뀐 칠은 아직 저장 안 됐습니다." : "") + (S.sus.length ? ` 한 번 볼 열매 ${S.sus.length}개(빨간 점선): ${sus}` : ""), "ok");
    return true;
  } catch (e) {
    say("저장 실패: " + e.message, "err"); return false;
  } finally { S.busy = false; }
}
/* 목록 한 줄의 앞 표시(✓·✕·빈칸)만 바꾼다 — 빈칸 «　» 은 한 글자라 slice(2) 로 자르면 번호 첫 자리가 잘렸다 */
function relabel(o, it) { o.textContent = itemMark(it) + o.textContent.replace(/^(✕ |✓ |　)/, ""); }
function markOption() {
  const it = S.items.find((x) => x.stem === S.stem), o = $("#photo").selectedOptions[0];
  if (it && o) relabel(o, it);
  renderProgress();
}

/* ── 닮은 사진 묶음(녹취 09-15 G78 «연속 스냅샷 걸러내기») ──
   /api/item 이 묶음(dup_members)·대표(dup_rep)·구성원의 사람 확정을 이미 준다(옛 툴과 같은 값·같은 대표 규칙).
   «대표만 남기기» = 대표가 아닌 구성원 중 사람이 아직 확정 안 한 장을 «빼기» 로 사람 확정 — /api/status 묶음째 확정 한 번.
   AI 판정(status)은 건드리지 않으므로 대표가 바뀌지 않고, 그새 남이 확정한 장은 서버가 건너뛴다. */
function dupTodo(item) {
  const conf = item.dup_member_confirmed || [];
  return (item.dup_members || []).filter((s, i) => s !== item.dup_rep && !conf[i]);
}
function renderDup() {
  const item = S.item || {}, mem = item.dup_members || [], box = $("#dupmenu");
  box.hidden = !S.L || mem.length < 2;
  if (box.hidden) return;
  const isRep = item.dup_rep === S.stem, todo = dupTodo(item);
  const conf = item.dup_member_confirmed || [], ai = item.dup_member_status || [];
  const tag = (s, i) => s === item.dup_rep ? "★ 대표" : conf[i] === "exclude" ? "✕ 뺌" : conf[i] ? "✓ 사람 확정" :
    ai[i] === "exclude" ? "AI 가 뺌(미확정)" : "안 봄";
  $("#dupbtn").textContent = `🔁 닮은 사진 ${mem.length}장` + (isRep ? " · 대표" : "");
  $("#dupbtn").classList.toggle("notrep", !isRep);
  $("#dupdrop").innerHTML =
    `<div class="info">거의 같은 사진(연속 스냅샷) 묶음입니다. 데이터셋에는 대표 한 장만 씁니다.<br>` +
    (isRep ? "지금 사진이 <b>대표</b>입니다." : "지금 사진은 <b>대표가 아닙니다</b> — 칠하지 말고 빼면 됩니다.") + `</div><hr>` +
    mem.map((s, i) => `<button data-dupopen="${s}"${s === S.stem ? ' class="cur"' : ""}><span>${s}</span><span>${tag(s, i)}</span></button>`).join("") +
    `<hr><button data-act="dup-keep-rep"${todo.length ? "" : " disabled"}><span>대표만 남기기 (나머지 ${todo.length}장 빼기)</span></button>`;
}
async function dupKeepRep() {
  const item = S.item;
  if (!S.L || S.busy || !item) return;
  const rep = item.dup_rep, todo = dupTodo(item);
  if (!todo.length) return say("더 뺄 사진이 없습니다. 대표가 아닌 사진은 모두 사람이 이미 확정했습니다.");
  if (!confirm(`이 묶음 ${item.dup_members.length}장 중 대표 «${rep}» 만 남기고 ${todo.length}장을 «빼기» 로 확정합니다.\n` +
    "원본 파일은 지우지 않습니다. 하나씩 되돌리려면 그 사진을 열고 파일 → 빼기 취소.\n진행할까요?")) return;
  const by = who() || askWho(), stem0 = S.stem;
  let done = [];
  S.busy = true;
  try {
    const j = await postJSON("/api/status", {
      fruit: S.fruit, stem: todo[0], by, status: "exclude", confirm: true, kind: "mask",
      note: `그림판: 닮은 사진 — 대표 ${rep} 만 남김`, stems: todo.slice(1).map((s) => ({ stem: s, status: "exclude" })) });
    done = Object.keys(j.confirmed || {});
    for (const s of done) {
      PF.delete(`${S.fruit}|${s}`);
      const it = S.items.find((x) => x.stem === s); if (it) it.confirmed = "exclude";
      item.dup_member_confirmed[item.dup_members.indexOf(s)] = "exclude";
    }
    for (const o of $("#photo").options) if (done.includes(o.value)) relabel(o, { confirmed: "exclude" });
    renderProgress(); renderDup();
    const sk = (j.skipped || []).length;
    say(`닮은 사진 ${done.length}장을 뺐습니다(대표 ${rep} 만 남김)` + (sk ? ` · ${sk}장은 그새 다른 사람이 확정해서 그대로 뒀습니다` : "") + ".", "ok");
  } catch (e) { say("실패: " + e.message, "err"); return; }
  finally { S.busy = false; }
  if (done.includes(stem0) && S.stem === stem0 && !S.dirty) go(1, true);     // 지금 사진을 뺐으면 «이 사진 빼기» 처럼 다음으로
}
async function dupOpen(stem) {
  if (stem === S.stem || !(await leaveOk())) return;
  openPhoto(stem);
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
    PF.delete(`${base.fruit}|${base.stem}`);
    if (on && S.stem === base.stem) wlSend("exclude", base, 0);
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
  if (confirm("바뀐 것이 있습니다. 저장하고 넘어갈까요?\n(확인 = 저장하고 넘어감 · 취소 = 이 사진에 머무름)")) return (await save()) && !S.dirty;   // 저장 사이 또 바뀌었으면 머문다(C22)
  return false;
}
window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });

/* ── 단추·메뉴·단축키 연결 ── */
const ACTS = {
  save, undo, redo, new: newNumber,
  "save-next": async () => { if (await save()) go(1, !S.dirty); },   // 저장 사이 또 바뀌었으면 넘기기 전에 다시 묻는다(C22)
  prev: () => go(-1), next: () => go(1),
  exclude: () => setExclude(true), unexclude: () => setExclude(false),
  "reload-orig": () => { if (confirm("원본(처음 받은 라벨)을 다시 불러올까요? 저장하기 전까지는 파일이 안 바뀝니다.")) openPhoto(S.stem, true); },
  "clear-all": () => {
    if (!S.L || waitBusy() || !confirm("이 사진의 칠한 것을 전부 지울까요? (Ctrl+Z 로 되돌릴 수 있음)")) return;
    const before = snapshot(); S.L.fill(0); paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
    say("전부 지웠습니다. 열매가 없는 사진이면 «이 사진 빼기» 가 맞습니다.");
  },
  "toggle-color": () => { S.showColor = !S.showColor; applyView(); },
  orig: () => { S.showColor = !S.showColor; applyView(); },
  "toggle-nums": () => { S.showNums = !S.showNums; drawHud(); },
  "toggle-crop": () => {
    S.showCrop = !S.showCrop; drawHud();
    say(S.showCrop ? `빨간 네모 = AI 가 한 번에 보는 ${CROP}×${CROP} 크기(평가 때 자르는 가운데 자리). 사진 화소 기준입니다.` : "크롭 네모를 숨겼습니다.");
  },
  fit: () => S.L && fit(true),
  "zoom-in": () => S.L && zoomCenter(1.25),
  "zoom-out": () => S.L && zoomCenter(1 / 1.25),
  "zoom-100": () => S.L && zoomCenter(1 / viewTarget().z),
  "draft-add": () => loadDraft(true),
  "split-gt": () => splitBy("gt"),
  "split-draft": () => splitBy("draft"),
  "dup-keep-rep": dupKeepRep,
  "sim-find": samSimilar, "sim-accept": simAccept, "sim-cancel": () => simClear(true),
  "hole-info": () => say(HOLE_TIP + "."),
  "draft-replace": () => { if (confirm("지금 칠한 것을 모델 초벌로 전부 바꿀까요? (Ctrl+Z 로 되돌릴 수 있음)")) loadDraft(false); },
};
document.addEventListener("click", (e) => {
  const mb = e.target.closest(".mbtn");
  document.querySelectorAll(".menu").forEach((m) => { if (!mb || m !== mb.parentElement) m.classList.remove("open"); });
  if (mb) { mb.parentElement.classList.toggle("open"); return; }
  const pick = e.target.closest(".drop [data-dupopen], .drop [data-act]");   // 메뉴에서 고른 뒤 초점은 그 메뉴 단추로(C10, 전엔 body 로 사라짐)
  if (pick) pick.closest(".menu").querySelector(".mbtn").focus();
  const dop = e.target.closest("[data-dupopen]");
  if (dop) { document.querySelectorAll(".menu").forEach((m) => m.classList.remove("open")); dupOpen(dop.dataset.dupopen); return; }
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
$("#fruit").onchange = async () => {
  if (await leaveOk()) { setDirty(false); S.stem = ""; loadList(); }
  else $("#fruit").value = S.fruit;              // 취소하면 목록 표시도 지금 과일로 되돌린다
};
$("#photo").onchange = async () => {
  const want = $("#photo").value;
  if (await leaveOk()) openPhoto(want); else $("#photo").value = S.stem;
};
$("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") renderList(S.stem); });
$("#only-todo").onchange = () => renderList(S.stem);
if (localStorage.getItem("paint.sort") === "unc") $("#sort").value = "unc";      // 안 저장한 지금 사진은 renderList 가 목록에 남기므로(C21) 저장 확인이 필요 없다
$("#sort").onchange = () => { try { localStorage.setItem("paint.sort", $("#sort").value); } catch (e) { /* 개인 창 */ } renderList(S.stem); };
$("#only-sample").onchange = async (e) => {    // 지금 사진이 표본 밖이면 다른 사진이 열리므로 칠한 것부터 챙긴다
  if (await leaveOk()) renderList(S.stem); else e.target.checked = !e.target.checked;
};
$("#alpha").oninput = () => { S.alpha = $("#alpha").value / 100; applyView(); };
$("#who").onclick = askWho;
$("#curbox").onclick = () => {                   // 지금 색 = 팔레트의 그 칸으로 초점을 옮긴다(색이 많아 칸이 옆으로 넘칠 때)
  const e = document.querySelector(".sw.on");
  if (e) { e.focus(); e.scrollIntoView({ block: "nearest", inline: "nearest" }); }
  say(S.cur ? `지금 색은 ${S.cur}번입니다.` : "지금 색은 지우기입니다.");
};
window.addEventListener("resize", () => S.L && applyView());
window.addEventListener("blur", () => { if (S.peek) { S.peek = false; applyView(); } });   // 키를 뗀 걸 못 받아도 풀리게
window.addEventListener("focus", () => { if (S.fruit) loadExports(); });                  // 옛 툴 창에서 내보내고 돌아왔을 때

/* 메뉴가 열리고 닫히는 곳이 여럿이라, class 가 바뀔 때마다 단추의 aria-expanded 를 맞춘다(C09) */
document.querySelectorAll(".menu").forEach((m) => {
  const b = m.querySelector(".mbtn");
  new MutationObserver(() => b.setAttribute("aria-expanded", String(m.classList.contains("open")))).observe(m, { attributes: true, attributeFilter: ["class"] });
});

let viaMouse = false;                            // 마지막 초점 이동이 마우스였나(C08 스페이스 구분)
document.addEventListener("mousedown", () => { viaMouse = true; }, true);
document.addEventListener("keydown", (e) => {
  // 메뉴 ↑↓(C10): 열린 메뉴의 항목 사이를 돌고, 닫힌 메뉴 단추에서 ↓ 는 열고 첫 항목으로
  if ((e.key === "ArrowDown" || e.key === "ArrowUp") && !e.ctrlKey && !e.metaKey && !e.altKey) {
    let m = document.querySelector(".menu.open");
    if (!m && e.key === "ArrowDown" && e.target.matches(".mbtn")) { m = e.target.parentElement; m.classList.add("open"); }
    const items = m ? [...m.querySelectorAll(".drop button:not(:disabled), .drop a, .drop input")] : [];
    if (items.length) {
      e.preventDefault();
      const i = items.indexOf(document.activeElement), n = items.length, down = e.key === "ArrowDown";
      items[i < 0 ? (down ? 0 : n - 1) : (i + (down ? 1 : n - 1)) % n].focus();
      return;
    }
  }
  if (e.key === "Escape") {
    const m = document.querySelector(".menu.open");   // 초점이 메뉴 안(또는 갈 곳 없음)이었으면 그 메뉴 단추로 되돌린다(C10)
    if (m && (m.contains(document.activeElement) || document.activeElement === document.body)) m.querySelector(".mbtn").focus();
    document.querySelectorAll(".menu.open").forEach((m) => m.classList.remove("open"));
    if (drag && (drag.kind === "lasso" || drag.kind === "sam")) { drag = null; lassoPts = null; drawHud(); say("취소했습니다."); }
    else if (S.sim && !m) simClear(true);         // C14 후보 버리기(메뉴가 열려 있었으면 메뉴만 닫는다)
    return;
  }
  // role=button(팔레트 색 칸·지금 색·작업자)은 Enter = 누르기, Tab 으로 왔으면 스페이스도 누르기(C08).
  // 마우스로 누른 뒤(초점이 칸에 남음) 스페이스는 예전처럼 «끌어서 옮기기» 다 — 크로미움은 이때도 :focus-visible 이라 직접 기억한다
  if (e.key === "Tab") viaMouse = false;
  // ✨ 후보가 떠 있으면 색 칸·지금 색에서의 Enter 도 «모두 받기»(C20) — 색을 고른 뒤 G→Enter 가 색 칸을 다시 누르지 않게
  if (e.key === "Enter" && S.sim && e.target.matches(".sw, #curbox")) { e.preventDefault(); if (!e.repeat) simAccept(); return; }
  if (e.target.matches('[role="button"]') && (e.key === "Enter" || (e.key === " " && !viaMouse))) { e.preventDefault(); if (!e.repeat) e.target.click(); return; }
  if (e.target.matches("input, select, textarea")) return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === "s") { e.preventDefault(); save(); return; }
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); ACTS["save-next"](); return; }
  if ((e.ctrlKey || e.metaKey) && k === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
  if ((e.ctrlKey || e.metaKey) && k === "y") { e.preventDefault(); redo(); return; }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (k === " ") { spaceDown = true; stage.style.cursor = "grab"; e.preventDefault(); return; }
  if (e.key === "`" || e.code === "Backquote") { if (!S.peek) { S.peek = true; applyView(); } return; }
  if (TOOL_KEYS[k]) return setTool(TOOL_KEYS[k]);
  if (k === "n") return newNumber();
  if (k === "g") return samSimilar();
  if (e.key === "Enter" && S.sim && !e.target.closest("button, a")) { e.preventDefault(); return simAccept(); }
  if (k === "[") { S.size = Math.max(1, Math.round(S.size / 1.25)); return setTool(S.tool); }
  if (k === "]") { S.size = Math.min(200, Math.round(S.size * 1.25) + 1); return setTool(S.tool); }
  if (k === "v") return ACTS["toggle-color"]();
  if (k === "t") return ACTS["toggle-nums"]();
  if (k === "c") return ACTS["toggle-crop"]();
  if (k === "0") return ACTS.fit();
  if (e.key === "+" || e.key === "=") return ACTS["zoom-in"]();
  if (e.key === "-" || e.key === "_") return ACTS["zoom-out"]();
  if (k === "1") return ACTS["zoom-100"]();
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
