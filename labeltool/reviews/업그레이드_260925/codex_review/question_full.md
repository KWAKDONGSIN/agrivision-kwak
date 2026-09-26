너는 코드 검토자다. 한국어로 답한다. 코드는 아래에 모두 붙여 두었다. 도구를 쓰지 말고 아래 내용만 보고 판단한다.
대상: 라벨링 웹툴 «그림판» — app/static/paint/{index.html,paint.js,paint.css}, app/server.py 와 app/*.py(그림판 API 부분), ai_helper/sam_server.py(✨ SAM 클릭 칠하기 도우미).
_backup_* 파일은 무시한다.

찾을 것(심각한 것부터):
1. 실제 버그 — 저장 데이터가 틀어지거나(마스크·번호·상자 불일치), 다른 사진에 저장되거나, 되돌리기가 깨지거나, 예외로 멈추는 경우.
2. 여러 사람이 동시에 쓸 때 생기는 문제(덮어쓰기, 경쟁 상태).
3. 서버 보안 문제(경로 조작 등).
4. 라벨링 속도를 크게 올릴 수 있는 개선 3개까지(근거 코드 위치와 함께).

출력(마크다운): 결론 한 줄 → 문제마다 «파일:줄 · 무엇이 틀렸나 · 어떤 상황에서 깨지나 · 고치는 법(짧게)». 확실하지 않으면 «추정». 스타일 지적 금지.

===== app/static/paint/index.html =====
     1	<!doctype html>
     2	<!-- 그림판 모양 라벨링 화면 — 색 하나 = 열매 번호 하나 (2026-09-23 새로 만듦) -->
     3	<html lang="ko">
     4	<head>
     5	<meta charset="utf-8">
     6	<title>라벨 그림판</title>
     7	<meta name="viewport" content="width=device-width, initial-scale=1">
     8	<link rel="stylesheet" href="/static/paint/paint.css">
     9	<link rel="icon" href="data:,">
    10	</head>
    11	<body>
    12	<div id="win">
    13	  <div id="title"><span id="t-name">사진을 고르세요</span> - 라벨 그림판<span id="t-dirty"></span></div>
    14	
    15	  <div id="menubar">
    16	    <div class="menu"><button class="mbtn">파일</button>
    17	      <div class="drop">
    18	        <button data-act="save">저장 <kbd>Ctrl+S</kbd></button>
    19	        <button data-act="save-next">저장하고 다음 사진 <kbd>Ctrl+Enter</kbd></button>
    20	        <button data-act="prev">이전 사진 <kbd>A</kbd></button>
    21	        <button data-act="next">다음 사진 <kbd>D</kbd></button>
    22	        <hr>
    23	        <button data-act="exclude">이 사진 빼기 (흐림·근접·열매 없음)</button>
    24	        <button data-act="unexclude">빼기 취소</button>
    25	        <hr>
    26	        <button data-act="draft-add">모델 초벌: 빠진 열매만 더하기</button>
    27	        <button data-act="draft-replace">모델 초벌로 전부 바꾸기</button>
    28	        <button data-act="split-gt">번호만 원본 정답으로 나누기 (칠한 모양 그대로)</button>
    29	        <button data-act="split-draft">번호만 모델 초벌로 나누기 (칠한 모양 그대로)</button>
    30	        <hr>
    31	        <button data-act="reload-orig">원본 다시 불러오기 (저장 전까지는 안전)</button>
    32	        <a href="/old" target="_blank">옛 툴 열기 (데이터 정리·내보내기)</a>
    33	      </div>
    34	    </div>
    35	    <div class="menu"><button class="mbtn">편집</button>
    36	      <div class="drop">
    37	        <button data-act="undo">되돌리기 <kbd>Ctrl+Z</kbd></button>
    38	        <button data-act="redo">다시 하기 <kbd>Ctrl+Y</kbd></button>
    39	        <hr>
    40	        <button data-act="clear-all">전부 지우기</button>
    41	      </div>
    42	    </div>
    43	    <div class="menu"><button class="mbtn">보기</button>
    44	      <div class="drop">
    45	        <button data-act="toggle-color">원본 보기(색 숨기기/보이기) <kbd>V</kbd></button>
    46	        <button data-act="toggle-nums">번호 글자 숨기기/보이기 <kbd>T</kbd></button>
    47	        <button data-act="zoom-in">확대 <kbd>+</kbd></button>
    48	        <button data-act="zoom-out">축소 <kbd>-</kbd></button>
    49	        <button data-act="zoom-100">실제 크기(100%) <kbd>1</kbd></button>
    50	        <button data-act="fit">가운데로 원래대로(화면에 맞추기) <kbd>0</kbd></button>
    51	        <label class="row">색 진하기 <input id="alpha" type="range" min="10" max="90" value="50"></label>
    52	      </div>
    53	    </div>
    54	    <div class="menu"><button class="mbtn">도움말</button>
    55	      <div class="drop wide" id="help">
    56	        <b>기본 규칙</b>
    57	        <p>색 하나 = 열매 하나. 같은 열매는 같은 색으로 칠합니다.<br>
    58	        잎에 가려 두 조각이 된 열매도 <b>같은 색</b>으로 칠하면 상자는 하나로 저장됩니다.</p>
    59	        <b>도구</b>
    60	        <p><kbd>B</kbd> 붓 · <kbd>E</kbd> 지우개 · <kbd>F</kbd> 채우기통(칠한 덩어리 클릭 → 지금 색) ·
    61	        <kbd>L</kbd> 올가미(테두리를 그리면 안을 칠함) · <kbd>I</kbd> 스포이트(색 집기) ·
    62	        <kbd>Z</kbd> 돋보기 · <kbd>H</kbd> 손(끌어서 옮기기) ·
    63	        <kbd>S</kbd> ✨클릭 칠하기(열매를 누르면 AI 가 모양대로 칠함 · 같은 자리를 다시 누르면 다른 모양 · 끌어서 네모 = 그 안의 열매 · Shift+클릭 = 여기는 아님)</p>
    64	        <p><b>원본 보기</b> = 위 «👁 원본 보기» 단추 또는 <kbd>V</kbd> · <kbd>`</kbd>(1 왼쪽) 을 누르고 있는 동안만 사진만 보기</p>
    65	        <p>오른쪽 클릭 = 지우기(붓·올가미·채우기통 모두) · 마우스 휠·<kbd>+</kbd><kbd>-</kbd> = 확대/축소 · <kbd>0</kbd> 또는 오른쪽 아래 «⤢ 가운데로» = 사진 전체를 가운데로 · 스페이스를 누른 채 끌기 = 옮기기</p>
    66	        <p><kbd>N</kbd> 새 번호 · <kbd>[</kbd> <kbd>]</kbd> 붓 크기 · <kbd>Ctrl+Z</kbd> 되돌리기 · <kbd>Ctrl+S</kbd> 저장 · <kbd>Ctrl+Enter</kbd> 저장하고 다음 · <kbd>Esc</kbd> 메뉴 닫기·올가미 취소 · <kbd>A</kbd>/<kbd>D</kbd> 이전/다음 사진</p>
    67	        <b>회색</b>
    68	        <p>원본에 칠해져 있지만 번호가 없는 곳입니다. 채우기통으로 누르면 번호가 붙습니다.</p>
    69	      </div>
    70	    </div>
    71	    <div id="nav">
    72	      <select id="fruit" title="과일"></select>
    73	      <button id="prev" title="이전 사진 (A)">◀</button>
    74	      <select id="photo" title="사진"></select>
    75	      <button id="next" title="다음 사진 (D)">▶</button>
    76	      <input id="q" placeholder="이름 찾기" size="10">
    77	      <label class="chk"><input type="checkbox" id="only-todo"> 안 한 것만</label>
    78	      <button id="orig" title="원본 보기: 색·번호를 숨기고 사진만 봅니다 (` 키를 누르고 있는 동안만 보기도 됩니다)">👁 원본 보기</button>
    79	      <button id="save" class="primary" title="Ctrl+S">저장</button>
    80	    </div>
    81	  </div>
    82	
    83	  <div id="body">
    84	    <div id="toolbox">
    85	      <div id="tools">
    86	        <button data-tool="lasso" title="올가미 (L): 테두리를 그리면 안을 칠함">➰<span>올가미</span></button>
    87	        <button data-tool="zoom" title="돋보기 (Z): 클릭 확대 · 오른쪽 클릭 축소">🔍<span>돋보기</span></button>
    88	        <button data-tool="eraser" title="지우개 (E)">🧽<span>지우개</span></button>
    89	        <button data-tool="fill" title="채우기통 (F): 칠한 덩어리를 누르면 지금 색이 됨">🪣<span>채우기</span></button>
    90	        <button data-tool="pick" title="스포이트 (I): 누른 열매의 색을 집음">💧<span>스포이트</span></button>
    91	        <button data-tool="hand" title="손 (H): 끌어서 옮기기">✋<span>손</span></button>
    92	        <button data-tool="brush" title="붓 (B)">🖌️<span>붓</span></button>
    93	        <button data-act="new" title="새 번호 (N)">＋<span>새 번호</span></button>
    94	        <button data-tool="sam" class="wide" title="클릭 칠하기 (S): 열매를 누르면 모양대로 칠함 · 같은 자리를 다시 누르면 다른 모양">✨<span>클릭 칠하기</span></button>
    95	      </div>
    96	      <div id="options"></div>
    97	    </div>
    98	    <div id="stage">
    99	      <div id="world"><canvas id="img"></canvas><canvas id="ov"></canvas></div>
   100	      <canvas id="hud"></canvas>
   101	      <div id="loading">불러오는 중…</div>
   102	      <div id="zoombar">
   103	        <button data-act="zoom-out" title="축소 (- 키 · 휠 아래로)">－</button>
   104	        <button data-act="zoom-100" id="zpct" title="눌러서 실제 크기(100%) · 1 키">100%</button>
   105	        <button data-act="zoom-in" title="확대 (+ 키 · 휠 위로)">＋</button>
   106	        <button data-act="fit" class="fitbtn" title="사진 전체를 가운데에 맞추기 (0 키)">⤢ 가운데로</button>
   107	      </div>
   108	    </div>
   109	  </div>
   110	
   111	  <div id="palette">
   112	    <div id="curbox" title="지금 색"><div id="cur-sw"></div><div id="cur-txt"></div></div>
   113	    <div id="swatches"></div>
   114	  </div>
   115	
   116	  <div id="statusbar">
   117	    <div id="msg">도움말은 위 «도움말» 을 누르세요.</div>
   118	    <div id="prog" title="이 과일에서 저장(✓)하거나 뺀(✕) 사진 수"></div>
   119	    <div id="count"></div>
   120	    <div id="pos"></div>
   121	    <div id="who" title="눌러서 이름 바꾸기"></div>
   122	  </div>
   123	</div>
   124	<script src="/static/paint/paint.js"></script>
   125	</body>
   126	</html>

===== app/static/paint/paint.js =====
     1	// 라벨 그림판 동작 — 색(=열매 번호)으로 칠하고, 마스크·번호·상자를 한 번에 저장한다
     2	"use strict";
     3	
     4	/* ── 약속 ──────────────────────────────────────────────────────────────
     5	   L[y*W+x] = 그 화소의 열매 번호. 0 = 배경, HOLE = «원본에 칠해져 있지만 번호가 없는 곳»(회색).
     6	   저장할 때: 마스크 = L>0 (회색 포함) · 번호 = L (회색은 0) · 상자 = 번호마다 바깥 네모.
     7	   서버 API 는 옛 툴과 같다(/api/save · /api/save_instances · /api/boxes · /api/status). */
     8	const HOLE = 65535;
     9	const $ = (s) => document.querySelector(s);
    10	const S = {
    11	  fruit: "", stem: "", items: [], W: 0, H: 0, L: null, img: null,
    12	  tool: "brush", cur: 1, size: 12, fillNew: true, protect: true,
    13	  z: 1, ox: 0, oy: 0, alpha: 0.5, showColor: true, showNums: true,
    14	  undo: [], redo: [], dirty: false, busy: false, lastNew: 0, gen: 0,
    15	};
    16	const UNDO_MAX = 40;
    17	
    18	/* ── 색: 번호마다 서로 잘 구별되는 색(황금각 색상환) ── */
    19	const LUT = new Uint32Array(65536);
    20	const LUT_CSS = {};
    21	function hsv(h, s, v) {
    22	  const f = (n) => { const k = (n + h * 6) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
    23	  return [f(5), f(3), f(1)].map((x) => Math.round(x * 255));
    24	}
    25	function rgbOf(id) {
    26	  if (id === HOLE) return [150, 150, 150];
    27	  const h = (id * 0.618033988749895) % 1;
    28	  return hsv(h, id % 3 === 0 ? 0.75 : 0.95, id % 2 ? 1 : 0.85);
    29	}
    30	function cssOf(id) {
    31	  if (id === 0) return "#ffffff";
    32	  if (!LUT_CSS[id]) { const [r, g, b] = rgbOf(id); LUT_CSS[id] = `rgb(${r},${g},${b})`; }
    33	  return LUT_CSS[id];
    34	}
    35	function lut(id) {
    36	  if (id === 0) return 0;
    37	  let v = LUT[id];
    38	  if (!v) { const [r, g, b] = rgbOf(id); v = LUT[id] = (255 << 24) | (b << 16) | (g << 8) | r; }
    39	  return v;
    40	}
    41	
    42	/* ── 서버 ── */
    43	async function getJSON(url) {
    44	  const r = await fetch(url);
    45	  if (r.status === 401 || r.redirected && r.url.includes("/login")) { location.href = "/login?next=/"; throw new Error("로그인 필요"); }
    46	  const j = await r.json().catch(() => ({}));
    47	  if (!r.ok) throw new Error(j.error || j.msg || ("서버 오류 " + r.status));
    48	  return j;
    49	}
    50	async function postJSON(url, body) {
    51	  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    52	  const j = await r.json().catch(() => ({}));
    53	  if (!r.ok || j.ok === false) throw new Error(j.error || j.msg || ("서버 오류 " + r.status));
    54	  return j;
    55	}
    56	async function getBytes(url) {
    57	  const r = await fetch(url);
    58	  if (!r.ok) return null;
    59	  return new Uint8Array(await r.arrayBuffer());
    60	}
    61	
    62	/* 회색(1채널) PNG 를 «값 그대로» 읽는다 — 16비트 번호를 캔버스로 읽으면 깨지므로 직접 푼다
    63	   (옛 툴 instances.js 의 decodeGrayPng 와 같은 방법) */
    64	async function inflateZlib(u8) {
    65	  const ds = new DecompressionStream("deflate");
    66	  const w = ds.writable.getWriter(); w.write(u8); w.close();
    67	  const buf = await new Response(ds.readable).arrayBuffer();
    68	  return new Uint8Array(buf);
    69	}
    70	async function decodeGrayPng(b) {
    71	  if (!(b[0] === 0x89 && b[1] === 0x50)) throw new Error("PNG 파일이 아닙니다");
    72	  const be32 = (i) => (b[i] * 16777216) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3];
    73	  let off = 8, W = 0, H = 0, bd = 8, ct = 0; const idat = [];
    74	  while (off + 8 <= b.length) {
    75	    const len = be32(off), typ = String.fromCharCode(b[off + 4], b[off + 5], b[off + 6], b[off + 7]), ds = off + 8;
    76	    if (typ === "IHDR") { W = be32(ds); H = be32(ds + 4); bd = b[ds + 8]; ct = b[ds + 9]; if (b[ds + 12]) throw new Error("인터레이스 PNG"); }
    77	    else if (typ === "IDAT") idat.push(b.subarray(ds, ds + len));
    78	    else if (typ === "IEND") break;
    79	    off = ds + len + 4;
    80	  }
    81	  if (ct !== 0 || (bd !== 8 && bd !== 16)) throw new Error("회색 8·16비트 PNG 가 아닙니다");
    82	  let t = 0; idat.forEach((p) => t += p.length);
    83	  const z = new Uint8Array(t); let o = 0; idat.forEach((p) => { z.set(p, o); o += p.length; });
    84	  const raw = await inflateZlib(z);
    85	  const bpp = bd === 16 ? 2 : 1, stride = W * bpp, out = new Uint16Array(W * H);
    86	  let prev = new Uint8Array(stride), cur = new Uint8Array(stride), p = 0;
    87	  for (let y = 0; y < H; y++) {
    88	    const ft = raw[p++]; cur.set(raw.subarray(p, p + stride)); p += stride;
    89	    for (let i = 0; i < stride; i++) {
    90	      const a = i >= bpp ? cur[i - bpp] : 0, bb = prev[i], c = i >= bpp ? prev[i - bpp] : 0;
    91	      let v = cur[i];
    92	      if (ft === 1) v += a; else if (ft === 2) v += bb; else if (ft === 3) v += (a + bb) >> 1;
    93	      else if (ft === 4) { const pa = Math.abs(bb - c), pb = Math.abs(a - c), pc = Math.abs(a + bb - 2 * c); v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? bb : c); }
    94	      cur[i] = v;
    95	    }
    96	    const ro = y * W;
    97	    if (bd === 16) for (let x = 0; x < W; x++) out[ro + x] = (cur[x * 2] << 8) | cur[x * 2 + 1];
    98	    else for (let x = 0; x < W; x++) out[ro + x] = cur[x];
    99	    const tt = prev; prev = cur; cur = tt;
   100	  }
   101	  return { w: W, h: H, data: out };
   102	}
   103	
   104	/* ── 알림 줄 ── */
   105	function say(text, kind) { const m = $("#msg"); m.textContent = text; m.className = kind || ""; }
   106	
   107	/* ── 사진 목록 ── */
   108	const who = () => localStorage.getItem("who") || "";
   109	function askWho() {
   110	  let n = prompt("작업자 이름을 적어 주세요 (저장 기록에 남습니다)", who());
   111	  if (n === null) return who();
   112	  n = n.trim();
   113	  if (/^ai/i.test(n)) { alert("«AI» 로 시작하는 이름은 쓸 수 없습니다."); return askWho(); }
   114	  try { localStorage.setItem("who", n); } catch (e) { /* 개인 창 */ }
   115	  $("#who").textContent = "작업자: " + (n || "(이름 없음)");
   116	  return n;
   117	}
   118	
   119	async function loadFruits() {
   120	  const j = await getJSON("/api/fruits");
   121	  const names = { apple: "사과", blueberry: "블루베리", grape: "포도", peach: "복숭아" };
   122	  $("#fruit").innerHTML = j.fruits.map((f) => `<option value="${f.fruit}">${names[f.fruit] || f.fruit} (${f.n_images})</option>`).join("");
   123	  const last = localStorage.getItem("paint.fruit");
   124	  if (last && j.fruits.some((f) => f.fruit === last)) $("#fruit").value = last;
   125	}
   126	
   127	function itemMark(it) {
   128	  if (it.confirmed === "exclude") return "✕ ";
   129	  if (it.confirmed || it.confirmed_instances) return "✓ ";
   130	  return "　";
   131	}
   132	async function loadList(keepStem) {
   133	  S.fruit = $("#fruit").value;
   134	  try { localStorage.setItem("paint.fruit", S.fruit); } catch (e) { /* 무시 */ }
   135	  const items = [];
   136	  for (let page = 1; ; page++) {
   137	    const j = await getJSON(`/api/list?fruit=${S.fruit}&sort=name&page_size=500&page=${page}`);
   138	    items.push(...j.items);
   139	    if (page >= j.pages) break;
   140	  }
   141	  S.items = items;
   142	  renderList(keepStem);
   143	}
   144	function renderList(keepStem) {
   145	  const q = $("#q").value.trim().toLowerCase();
   146	  const todo = $("#only-todo").checked;
   147	  const shown = S.items.filter((it) => (!q || it.stem.toLowerCase().includes(q)) && (!todo || itemMark(it) === "　"));
   148	  const done = S.items.filter((it) => itemMark(it) === "✓ ").length;
   149	  const sel = $("#photo");
   150	  sel.innerHTML = shown.map((it, i) => `<option value="${it.stem}">${itemMark(it)}${i + 1}. ${it.stem}</option>`).join("");
   151	  sel.title = `전체 ${S.items.length}장 · 저장함 ${done}장 · 지금 목록 ${shown.length}장`;
   152	  renderProgress();
   153	  const want = keepStem && shown.some((it) => it.stem === keepStem) ? keepStem : (shown[0] || {}).stem;
   154	  if (want) { sel.value = want; if (want !== S.stem || !S.L) openPhoto(want); }
   155	  else { clearPhoto(); say("조건에 맞는 사진이 없습니다. «이름 찾기» 칸을 비우거나 «안 한 것만» 을 끄세요."); }
   156	}
   157	/* 보여 줄 사진이 없으면 그림판을 비운다 — 다른 과일의 사진이 남아 있으면 그 위에 칠하고 엉뚱한 곳에 저장하려 하게 된다 */
   158	function clearPhoto() {
   159	  S.gen++;
   160	  Object.assign(S, { stem: "", L: null, img: null, undo: [], redo: [], idsCache: null, draftIds: new Set() });
   161	  imgC.width = ovC.width = 0; world.style.width = world.style.height = "0px";
   162	  centers = []; setDirty(false); drawHud();
   163	  $("#t-name").textContent = "사진을 고르세요"; $("#swatches").innerHTML = ""; $("#count").textContent = "";
   164	}
   165	
   166	/* ── 한 장 열기 ── */
   167	const imgC = $("#img"), ovC = $("#ov"), hud = $("#hud"), stage = $("#stage"), world = $("#world");
   168	const ovX = ovC.getContext("2d"), hudX = hud.getContext("2d");
   169	let ovData = null, ovU32 = null;
   170	
   171	async function openPhoto(stem, fromOriginal) {
   172	  if (S.busy) return;
   173	  S.gen++;                                   // 이 값이 바뀌면 늦게 온 AI 답은 버린다(다른 사진에 붙지 않게)
   174	  S.busy = true; $("#loading").style.display = "block";
   175	  try {
   176	    const f = S.fruit;
   177	    const item = await getJSON(`/api/item?fruit=${f}&stem=${encodeURIComponent(stem)}`);
   178	    const q = `fruit=${f}&stem=${encodeURIComponent(stem)}`;
   179	    const img = new Image();
   180	    const imgDone = new Promise((ok, bad) => { img.onload = ok; img.onerror = () => bad(new Error("사진을 못 읽었습니다")); });
   181	    img.src = "/img?" + q;
   182	    // 마스크: 사람이 고친 것이 있으면 그것, 없으면 원본. 번호: 서버가 고른 것(고친 것 > 팀 초벌 > 원본 번호)
   183	    const useFixed = item.has_fixed && !fromOriginal;
   184	    const [mb, ib] = await Promise.all([
   185	      getBytes(`/mask?${q}&layer=${useFixed ? "fixed" : "gt"}`),
   186	      getBytes(`/instances?${q}&layer=${fromOriginal ? "gt" : "auto"}`),
   187	    ]);
   188	    await imgDone;
   189	    const W = item.width, H = item.height;
   190	    const bin = mb ? (await decodeGrayPng(mb)).data : new Uint16Array(W * H);
   191	    let L;
   192	    if (ib) {
   193	      L = (await decodeGrayPng(ib)).data;
   194	      // 원본을 다시 부를 때는 번호도 원본 마스크 안으로 자른다(서버는 고친 마스크로 자른다)
   195	      for (let i = 0; i < L.length; i++) { if (!bin[i]) L[i] = 0; else if (!L[i]) L[i] = HOLE; }
   196	    } else {
   197	      L = components(bin, W, H);
   198	    }
   199	    Object.assign(S, { stem, W, H, L, img, undo: [], redo: [], item, draftIds: new Set(), gen: S.gen + 1 });
   200	    S.lastNew = maxId();
   201	    S.cur = S.lastNew + 1;                       // 붓은 «새 열매» 색으로 시작한다
   202	    computeCenters();
   203	    imgC.width = ovC.width = W; imgC.height = ovC.height = H;
   204	    imgC.getContext("2d").drawImage(img, 0, 0);
   205	    ovData = ovX.createImageData(W, H); ovU32 = new Uint32Array(ovData.data.buffer);
   206	    paintRect(0, 0, W, H);
   207	    world.style.width = W + "px"; world.style.height = H + "px";
   208	    fit();
   209	    setDirty(!!fromOriginal);
   210	    $("#t-name").textContent = stem;
   211	    $("#photo").value = stem;
   212	    renderPalette(); renderCount();
   213	    const it = S.items.find((x) => x.stem === stem) || {};
   214	    say(it.confirmed === "exclude" ? "이 사진은 «빼기» 로 표시돼 있습니다. (파일 → 빼기 취소)" :
   215	      fromOriginal ? "원본을 다시 불러왔습니다. 저장해야 반영됩니다." :
   216	      `${stem} 을(를) 열었습니다. 색 하나 = 열매 하나입니다.`, it.confirmed === "exclude" ? "err" : "");
   217	  } catch (e) {
   218	    say("열기 실패: " + e.message, "err");
   219	  } finally {
   220	    S.busy = false; $("#loading").style.display = "none";
   221	  }
   222	}
   223	
   224	/* 번호가 아예 없는 사진: 칠해진 덩어리마다 번호를 붙인다(4-연결) */
   225	function components(bin, W, H) {
   226	  const L = new Uint16Array(W * H), stack = new Int32Array(W * H);
   227	  let n = 0;
   228	  for (let s = 0; s < L.length; s++) {
   229	    if (!bin[s] || L[s]) continue;
   230	    n = Math.min(n + 1, HOLE - 1);
   231	    let sp = 0; stack[sp++] = s; L[s] = n;
   232	    while (sp) {
   233	      const i = stack[--sp], x = i % W;
   234	      if (x > 0 && bin[i - 1] && !L[i - 1]) { L[i - 1] = n; stack[sp++] = i - 1; }
   235	      if (x < W - 1 && bin[i + 1] && !L[i + 1]) { L[i + 1] = n; stack[sp++] = i + 1; }
   236	      if (i >= W && bin[i - W] && !L[i - W]) { L[i - W] = n; stack[sp++] = i - W; }
   237	      if (i + W < L.length && bin[i + W] && !L[i + W]) { L[i + W] = n; stack[sp++] = i + W; }
   238	    }
   239	  }
   240	  return L;
   241	}
   242	
   243	/* ── 그리기(화면) ── */
   244	function paintRect(x0, y0, w, h) {
   245	  x0 = Math.max(0, x0 | 0); y0 = Math.max(0, y0 | 0);
   246	  const x1 = Math.min(S.W, Math.ceil(x0 + w)), y1 = Math.min(S.H, Math.ceil(y0 + h));
   247	  if (x1 <= x0 || y1 <= y0) return;
   248	  const L = S.L, W = S.W;
   249	  for (let y = y0; y < y1; y++) { const r = y * W; for (let x = x0; x < x1; x++) ovU32[r + x] = lut(L[r + x]); }
   250	  ovX.putImageData(ovData, 0, 0, x0, y0, x1 - x0, y1 - y0);
   251	}
   252	function applyView() {
   253	  world.style.transform = `translate(${S.ox}px,${S.oy}px) scale(${S.z})`;
   254	  $("#zpct").textContent = Math.round(S.z * 100) + "%";
   255	  const show = S.showColor && !S.peek;         // peek = ` 키를 누르고 있는 동안
   256	  ovC.style.opacity = show ? S.alpha : 0;
   257	  const ob = document.querySelector("#orig");
   258	  if (ob) { ob.classList.toggle("on", !show); ob.textContent = show ? "👁 원본 보기" : "🎨 색 다시 보기"; }
   259	  drawHud();
   260	}
   261	/* 확대·옮기기는 «목표» 로 부드럽게 다가간다(약 0.15초). 목표가 없으면 지금 값이 목표다.
   262	   연달아 휠을 굴리면 목표에 이어서 쌓이므로 빨리 굴려도 끊기지 않는다. */
   263	let anim = null;
   264	function viewTarget() { return anim ? anim.to : { z: S.z, ox: S.ox, oy: S.oy }; }
   265	function stopAnim() { if (anim) { cancelAnimationFrame(anim.raf); anim = null; } }
   266	function animateTo(to, smooth) {
   267	  stopAnim();
   268	  if (!smooth || matchMedia("(prefers-reduced-motion: reduce)").matches) { Object.assign(S, to); applyView(); return; }
   269	  const from = { z: S.z, ox: S.ox, oy: S.oy }, t0 = performance.now(), dur = 150;
   270	  anim = { to };
   271	  const step = (now) => {
   272	    const t = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - t, 3);      // 끝에서 천천히 멈춤
   273	    // 확대율은 곱셈으로 섞어야 가까이 갈수록 속도가 고르다
   274	    const z = from.z * Math.pow(to.z / from.z, e);
   275	    // 화면에서 한 점이 제자리에 머물도록 ox 는 확대율에 맞춰 섞는다
   276	    const k = to.z === from.z ? e : (z - from.z) / (to.z - from.z);
   277	    S.z = z; S.ox = from.ox + (to.ox - from.ox) * k; S.oy = from.oy + (to.oy - from.oy) * k;
   278	    applyView();
   279	    if (t < 1) anim.raf = requestAnimationFrame(step); else anim = null;
   280	  };
   281	  anim.raf = requestAnimationFrame(step);
   282	}
   283	function fitView() {
   284	  const r = stage.getBoundingClientRect(), z = Math.min(r.width / S.W, r.height / S.H) * 0.98;
   285	  return { z, ox: (r.width - S.W * z) / 2, oy: (r.height - S.H * z) / 2 };
   286	}
   287	function fit(smooth) { animateTo(fitView(), smooth); }
   288	function zoomAt(sx, sy, k) {
   289	  const t = viewTarget(), nz = Math.max(0.05, Math.min(40, t.z * k));
   290	  animateTo({ z: nz, ox: sx - (sx - t.ox) * nz / t.z, oy: sy - (sy - t.oy) * nz / t.z }, true);
   291	}
   292	/* 화면 가운데를 기준으로 확대·축소(단추·+/- 키) */
   293	function zoomCenter(k) { const r = stage.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, k); }
   294	
   295	/* 번호 글자·붓 동그라미·올가미 선 — 화면 크기 캔버스에 그린다 */
   296	let centers = [], mouse = null, lassoPts = null;
   297	function computeCenters() {
   298	  // 한 번 훑어서 가운데·번호 목록·회색 여부를 같이 구한다(칠할 때마다 사진 전체를 여러 번 훑던 것을 한 번으로)
   299	  const sx = new Float64Array(65536), sy = new Float64Array(65536), n = new Uint32Array(65536);
   300	  const L = S.L, W = S.W, H = S.H;
   301	  let hole = false;
   302	  for (let y = 0, i = 0; y < H; y++) for (let x = 0; x < W; x++, i++) {
   303	    const v = L[i]; if (!v) continue;
   304	    if (v === HOLE) { hole = true; continue; }
   305	    n[v]++; sx[v] += x; sy[v] += y;
   306	  }
   307	  centers = []; const ids = [];
   308	  for (let v = 1; v < HOLE; v++) if (n[v]) { centers.push([v, sx[v] / n[v], sy[v] / n[v], n[v]]); ids.push(v); }
   309	  S.idsCache = { ids, hole };
   310	}
   311	function drawHud() {
   312	  const r = stage.getBoundingClientRect();
   313	  if (hud.width !== (r.width | 0) || hud.height !== (r.height | 0)) { hud.width = r.width; hud.height = r.height; }
   314	  hudX.clearRect(0, 0, hud.width, hud.height);
   315	  if (!S.L) return;
   316	  if (S.showNums && S.showColor && !S.peek) {
   317	    hudX.font = "bold 13px sans-serif"; hudX.textAlign = "center"; hudX.textBaseline = "middle";
   318	    hudX.lineWidth = 3; hudX.strokeStyle = "#000"; hudX.fillStyle = "#fff";
   319	    for (const [v, cx, cy, n] of centers) {
   320	      const x = S.ox + cx * S.z, y = S.oy + cy * S.z;
   321	      if (x < -20 || y < -20 || x > hud.width + 20 || y > hud.height + 20) continue;
   322	      const dr = S.draftIds && S.draftIds.has(v);
   323	      if (dr) {                                   // 모델 초벌에서 온 열매: 노란 동그라미 + 노란 번호
   324	        hudX.beginPath(); hudX.arc(x, y, Math.max(8, Math.sqrt(n / Math.PI) * S.z + 4), 0, Math.PI * 2);
   325	        hudX.lineWidth = 2; hudX.strokeStyle = "#ffe000"; hudX.stroke(); hudX.lineWidth = 3; hudX.strokeStyle = "#000";
   326	      }
   327	      hudX.fillStyle = dr ? "#ffe000" : "#fff";
   328	      hudX.strokeText(v, x, y); hudX.fillText(v, x, y);
   329	    }
   330	    hudX.fillStyle = "#fff";
   331	  }
   332	  if (lassoPts && lassoPts.length > 1) {
   333	    hudX.beginPath();
   334	    lassoPts.forEach(([x, y], i) => { const X = S.ox + x * S.z, Y = S.oy + y * S.z; i ? hudX.lineTo(X, Y) : hudX.moveTo(X, Y); });
   335	    hudX.setLineDash([5, 4]); hudX.lineWidth = 2; hudX.strokeStyle = lassoPts.erase ? "#fff" : cssOf(S.cur); hudX.stroke(); hudX.setLineDash([]);
   336	  }
   337	  if (drag && drag.kind === "sam" && drag.esx !== undefined && Math.hypot(drag.esx - drag.sx, drag.esy - drag.sy) > 8) {
   338	    hudX.setLineDash([6, 4]); hudX.lineWidth = 2; hudX.strokeStyle = "#ffe000";
   339	    hudX.strokeRect(Math.min(drag.sx, drag.esx), Math.min(drag.sy, drag.esy), Math.abs(drag.esx - drag.sx), Math.abs(drag.esy - drag.sy));
   340	    hudX.setLineDash([]);
   341	  }
   342	  if (mouse && (S.tool === "brush" || S.tool === "eraser")) {
   343	    hudX.beginPath(); hudX.arc(mouse.sx, mouse.sy, Math.max(1, S.size / 2 * S.z), 0, Math.PI * 2);
   344	    hudX.lineWidth = 1; hudX.strokeStyle = "#000"; hudX.stroke();
   345	    hudX.beginPath(); hudX.arc(mouse.sx, mouse.sy, Math.max(1, S.size / 2 * S.z) + 1, 0, Math.PI * 2);
   346	    hudX.strokeStyle = "#fff"; hudX.stroke();
   347	  }
   348	}
   349	
   350	/* ── 되돌리기: 바뀐 네모 칸만 기억한다 ── */
   351	function snapshot() { return S.L.slice(); }
   352	function pushUndo(before, x0, y0, x1, y1) {
   353	  x0 = Math.max(0, x0); y0 = Math.max(0, y0); x1 = Math.min(S.W, x1); y1 = Math.min(S.H, y1);
   354	  if (x1 <= x0 || y1 <= y0) return;
   355	  const w = x1 - x0, h = y1 - y0, data = new Uint16Array(w * h);
   356	  let same = true;
   357	  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
   358	    const i = (y0 + y) * S.W + x0 + x; data[y * w + x] = before[i]; if (before[i] !== S.L[i]) same = false;
   359	  }
   360	  if (same) return;
   361	  S.undo.push({ x0, y0, w, h, data }); if (S.undo.length > UNDO_MAX) S.undo.shift();
   362	  // 전체 사진 크기 기록(초벌·나누기·전부 지우기)이 쌓여도 약 120MB 를 넘지 않게 오래된 것부터 버린다
   363	  let bytes = 0; for (const r of S.undo) bytes += r.data.byteLength;
   364	  while (bytes > 120e6 && S.undo.length > 1) bytes -= S.undo.shift().data.byteLength;
   365	  S.redo = [];
   366	  changed();
   367	}
   368	function swapRect(rec) {
   369	  const { x0, y0, w, h, data } = rec;
   370	  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
   371	    const i = (y0 + y) * S.W + x0 + x, t = S.L[i]; S.L[i] = data[y * w + x]; data[y * w + x] = t;
   372	  }
   373	  paintRect(x0, y0, w, h);
   374	}
   375	function undo() { const r = S.undo.pop(); if (!r) return say("더 되돌릴 것이 없습니다."); swapRect(r); S.redo.push(r); changed(); }
   376	function redo() { const r = S.redo.pop(); if (!r) return say("다시 할 것이 없습니다."); swapRect(r); S.undo.push(r); changed(); }
   377	function changed() { setDirty(true); computeCenters(); renderPalette(); renderCount(); drawHud(); }
   378	function setDirty(d) {
   379	  S.dirty = d; $("#t-dirty").textContent = d ? "● 저장 안 됨" : "";
   380	  $("#save").classList.toggle("dirty", d);
   381	}
   382	
   383	/* ── 칠하기 동작 ── */
   384	function canPaint(v, val) { return !S.protect || val === 0 || v === 0 || v === HOLE || v === val; }
   385	function stamp(cx, cy, val, box) {
   386	  const r = S.size / 2, r2 = r * r, L = S.L, W = S.W;
   387	  const x0 = Math.max(0, Math.floor(cx - r)), x1 = Math.min(S.W - 1, Math.ceil(cx + r));
   388	  const y0 = Math.max(0, Math.floor(cy - r)), y1 = Math.min(S.H - 1, Math.ceil(cy + r));
   389	  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
   390	    const dx = x + 0.5 - cx, dy = y + 0.5 - cy;
   391	    if (dx * dx + dy * dy > r2 && !(S.size <= 1.5 && x === Math.floor(cx) && y === Math.floor(cy))) continue;
   392	    const i = y * W + x;
   393	    if (canPaint(L[i], val)) L[i] = val;
   394	  }
   395	  box[0] = Math.min(box[0], x0); box[1] = Math.min(box[1], y0); box[2] = Math.max(box[2], x1 + 1); box[3] = Math.max(box[3], y1 + 1);
   396	  paintRect(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
   397	}
   398	function strokeTo(a, b, val, box) {
   399	  const d = Math.hypot(b[0] - a[0], b[1] - a[1]), step = Math.max(0.5, S.size / 4), n = Math.ceil(d / step);
   400	  for (let k = 1; k <= n; k++) stamp(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n, val, box);
   401	}
   402	
   403	/* 채우기통: 누른 덩어리(같은 번호로 이어진 곳)를 val 로 바꾼다 */
   404	function fillAt(x, y, val) {
   405	  const W = S.W, L = S.L, s = y * W + x, v = L[s];
   406	  if (v === 0) { say("빈 곳입니다. 칠해진 열매(색이 있는 곳)를 누르세요. 새로 칠하려면 붓·올가미를 쓰세요."); return false; }
   407	  if (v === val) { say(`이미 ${val}번입니다.`); return false; }
   408	  const before = snapshot(), stack = new Int32Array(L.length);
   409	  let sp = 0, bx0 = x, by0 = y, bx1 = x, by1 = y;
   410	  stack[sp++] = s; L[s] = val;
   411	  while (sp) {
   412	    const i = stack[--sp], px = i % W, py = (i / W) | 0;
   413	    if (px < bx0) bx0 = px; if (px > bx1) bx1 = px; if (py < by0) by0 = py; if (py > by1) by1 = py;
   414	    if (px > 0 && L[i - 1] === v) { L[i - 1] = val; stack[sp++] = i - 1; }
   415	    if (px < W - 1 && L[i + 1] === v) { L[i + 1] = val; stack[sp++] = i + 1; }
   416	    if (i >= W && L[i - W] === v) { L[i - W] = val; stack[sp++] = i - W; }
   417	    if (i + W < L.length && L[i + W] === v) { L[i + W] = val; stack[sp++] = i + W; }
   418	  }
   419	  paintRect(bx0, by0, bx1 - bx0 + 1, by1 - by0 + 1);
   420	  pushUndo(before, bx0, by0, bx1 + 1, by1 + 1);
   421	  say(val === 0 ? "그 덩어리를 지웠습니다." : `그 덩어리를 ${val}번으로 칠했습니다.`);
   422	  return true;
   423	}
   424	
   425	/* ✨ 오른쪽 클릭: 누른 열매 번호를 통째로(떨어진 조각까지) 지운다. 회색·빈 곳은 채우기통과 같이 덩어리만 */
   426	function eraseId(x, y) {
   427	  const v = S.L[y * S.W + x];
   428	  if (v === 0 || v === HOLE) return fillAt(x, y, 0);
   429	  const L = S.L, W = S.W, before = snapshot();
   430	  let x0 = W, y0 = S.H, x1 = -1, y1 = -1;
   431	  for (let i = 0; i < L.length; i++) if (L[i] === v) {
   432	    L[i] = 0; const px = i % W, py = (i / W) | 0;
   433	    if (px < x0) x0 = px; if (px > x1) x1 = px; if (py < y0) y0 = py; if (py > y1) y1 = py;
   434	  }
   435	  paintRect(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
   436	  pushUndo(before, x0, y0, x1 + 1, y1 + 1);
   437	  say(`${v}번 열매를 통째로 지웠습니다. (Ctrl+Z 로 되돌리기)`);
   438	  return true;
   439	}
   440	
   441	/* 올가미: 그린 테두리 안을 val 로 */
   442	function fillPolygon(pts, val) {
   443	  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
   444	  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
   445	  x0 = Math.max(0, Math.floor(x0)); y0 = Math.max(0, Math.floor(y0));
   446	  x1 = Math.min(S.W, Math.ceil(x1) + 1); y1 = Math.min(S.H, Math.ceil(y1) + 1);
   447	  const w = x1 - x0, h = y1 - y0;
   448	  if (w < 2 || h < 2) return;
   449	  const c = document.createElement("canvas"); c.width = w; c.height = h;
   450	  const x = c.getContext("2d");
   451	  x.beginPath(); pts.forEach(([px, py], i) => (i ? x.lineTo(px - x0, py - y0) : x.moveTo(px - x0, py - y0)));
   452	  x.closePath(); x.fillStyle = "#fff"; x.fill();
   453	  const a = x.getImageData(0, 0, w, h).data, before = snapshot(), L = S.L;
   454	  for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
   455	    if (a[(yy * w + xx) * 4 + 3] < 128) continue;
   456	    const i = (y0 + yy) * S.W + x0 + xx;
   457	    if (canPaint(L[i], val)) L[i] = val;
   458	  }
   459	  paintRect(x0, y0, w, h);
   460	  pushUndo(before, x0, y0, x1, y1);
   461	}
   462	
   463	/* 기다리는 동안 사진이 바뀌었으면 true — 늦게 온 답을 새 사진에 붙이지 않는다(검수 1회 지적 1·3) */
   464	const stale = (g) => g !== S.gen;
   465	
   466	/* ✨ 클릭 칠하기: 도우미(SAM)가 준 후보 모양을 칠한다. 같은 자리를 또 누르면 다음 후보로 바꾼다 */
   467	let samLast = null;
   468	async function maskFromPng(b64, w, h) {
   469	  const im = new Image(); im.src = "data:image/png;base64," + b64; await im.decode();
   470	  const c = document.createElement("canvas"); c.width = w; c.height = h;
   471	  const x = c.getContext("2d"); x.drawImage(im, 0, 0);
   472	  return x.getImageData(0, 0, w, h).data;
   473	}
   474	async function applyCand(cd, val, g) {
   475	  const a = await maskFromPng(cd.png, cd.w, cd.h);
   476	  if (g !== undefined && stale(g)) return false;
   477	  const before = snapshot(), L = S.L;
   478	  for (let yy = 0; yy < cd.h; yy++) for (let xx = 0; xx < cd.w; xx++) {
   479	    if (a[(yy * cd.w + xx) * 4] < 128) continue;
   480	    const i = (cd.y0 + yy) * S.W + cd.x0 + xx;
   481	    if (canPaint(L[i], val)) L[i] = val;
   482	  }
   483	  paintRect(cd.x0, cd.y0, cd.w, cd.h);
   484	  const n = S.undo.length;
   485	  pushUndo(before, cd.x0, cd.y0, cd.x0 + cd.w, cd.y0 + cd.h);
   486	  return S.undo.length > n;
   487	}
   488	async function samClick(ix, iy) {
   489	  if (S.samBusy) return;
   490	  const again = samLast && samLast.stem === S.stem && Math.abs(samLast.x - ix) + Math.abs(samLast.y - iy) <= 6;
   491	  if (again) {
   492	    if (samLast.applied) undo();
   493	    samLast.k = (samLast.k + 1) % samLast.cands.length;
   494	    samLast.applied = await applyCand(samLast.cands[samLast.k], samLast.val, S.gen);
   495	    say(`${samLast.k + 1}/${samLast.cands.length}번째 모양입니다. 또 누르면 다음 모양.`);
   496	    return;
   497	  }
   498	  const here = S.L[iy * S.W + ix];
   499	  if (here && here !== HOLE && S.protect) {
   500	    say(`이미 ${here}번 열매입니다. 모양을 바꾸려면 오른쪽 클릭으로 지운 뒤 다시 누르세요.`); return;
   501	  }
   502	  S.samBusy = true; say("✨ 모양 찾는 중…");
   503	  try {
   504	    const crop = Math.max(256, Math.min(1024, Math.round(320 / S.z)));
   505	    const g = S.gen;
   506	    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, x: ix, y: iy, crop });
   507	    if (stale(g)) return;
   508	    if (!j.cands || !j.cands.length) { say("여기서는 열매 모양을 못 찾았습니다. 조금 옆을 누르거나 확대해서 눌러 보세요.", "err"); return; }
   509	    const val = S.fillNew ? Math.max(maxId(), S.lastNew) + 1 : (S.cur || Math.max(maxId(), S.lastNew) + 1);
   510	    samLast = { stem: S.stem, x: ix, y: iy, cands: j.cands, k: 0, val, points: [[ix, iy, 1]], box: null };
   511	    samLast.applied = await applyCand(j.cands[0], val, g);
   512	    if (stale(g)) return;
   513	    if (S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
   514	    say(samLast.applied ? `${val}번으로 칠했습니다 (${j.sec}초). 모양이 이상하면 같은 자리를 다시 누르세요 — 후보 ${j.cands.length}개.`
   515	      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).");
   516	  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
   517	  finally { S.samBusy = false; }
   518	}
   519	
   520	/* Shift+클릭 = «여기는 아니다»: 누른 곳의 모양(가장 작은 후보)을 ✨ 로 찾아, 방금 칠한 열매에서 그만큼 잘라 낸다.
   521	   (SAM 의 «빼기 점» 은 한 번으로는 거의 안 먹어서 이렇게 한다 — 붙은 블루베리 옆 알을 떼어 낼 때 쓴다) */
   522	async function samNeg(ix, iy) {
   523	  if (!samLast || samLast.stem !== S.stem) return say("먼저 ✨ 로 열매를 칠한 뒤, 잘못 칠해진 부분을 Shift+클릭하세요.");
   524	  const val = samLast.val;
   525	  if (S.L[iy * S.W + ix] !== val) return say(`거기는 ${val}번이 아닙니다. 방금 칠한 ${val}번 안의 잘못된 부분을 Shift+클릭하세요.`);
   526	  if (S.samBusy) return;
   527	  S.samBusy = true; say("✨ 떼어 낼 부분을 찾는 중…");
   528	  try {
   529	    const g = S.gen;
   530	    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, x: ix, y: iy, crop: Math.max(256, Math.min(1024, Math.round(320 / S.z))) });
   531	    if (stale(g)) return;
   532	    if (!j.cands || !j.cands.length) { say("떼어 낼 부분을 못 찾았습니다. 지우개(E)로 지워 주세요.", "err"); return; }
   533	    const cd = j.cands.reduce((m, c) => (c.w * c.h < m.w * m.h ? c : m));      // 가장 작은 모양
   534	    const a = await maskFromPng(cd.png, cd.w, cd.h);
   535	    if (stale(g)) return;
   536	    const before = snapshot(), L = S.L;
   537	    let n = 0, left = 0;
   538	    for (let yy = 0; yy < cd.h; yy++) for (let xx = 0; xx < cd.w; xx++) {
   539	      if (a[(yy * cd.w + xx) * 4] < 128) continue;
   540	      const i = (cd.y0 + yy) * S.W + cd.x0 + xx;
   541	      if (L[i] === val) { L[i] = 0; n++; }
   542	    }
   543	    for (let i = 0; i < L.length; i++) if (L[i] === val) left++;
   544	    if (!left) { S.L.set(before); paintRect(cd.x0, cd.y0, cd.w, cd.h); return say("그러면 열매가 통째로 사라져서 하지 않았습니다. 오른쪽 클릭으로 지우고 다시 누르세요.", "err"); }
   545	    paintRect(cd.x0, cd.y0, cd.w, cd.h); pushUndo(before, cd.x0, cd.y0, cd.x0 + cd.w, cd.y0 + cd.h);
   546	    samLast.x = samLast.y = -99;                // 이제 «같은 자리 다시 누르기» 로 후보를 바꾸지 않는다
   547	    say(`${val}번에서 ${n}화소를 떼어 냈습니다. 떼어 낸 알은 ✨ 로 눌러 새 번호를 붙일 수 있습니다.`);
   548	  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
   549	  finally { S.samBusy = false; }
   550	}
   551	/* 끌어서 네모 = 그 안의 열매 하나를 칠한다(작은 열매·붙은 열매에 좋다) */
   552	async function samBox(box) {
   553	  if (S.samBusy) return;
   554	  if (box[2] - box[0] < 3 || box[3] - box[1] < 3) return;
   555	  S.samBusy = true; say("✨ 네모 안의 열매를 찾는 중…");
   556	  try {
   557	    const g = S.gen;
   558	    const j = await postJSON("/api/sam", { fruit: S.fruit, stem: S.stem, box, crop: 256 });
   559	    if (stale(g)) return;
   560	    if (!j.cands || !j.cands.length) { say("네모 안에서 열매를 못 찾았습니다. 조금 크게 그려 보세요.", "err"); return; }
   561	    const val = S.fillNew ? Math.max(maxId(), S.lastNew) + 1 : (S.cur || Math.max(maxId(), S.lastNew) + 1);
   562	    samLast = { stem: S.stem, x: -99, y: -99, cands: j.cands, k: 0, val, points: [], box };
   563	    samLast.applied = await applyCand(j.cands[0], val, g);
   564	    if (stale(g)) return;
   565	    if (S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
   566	    say(samLast.applied ? `네모 안을 ${val}번으로 칠했습니다. 잘못 칠한 곳은 Shift+클릭으로 뺄 수 있습니다.`
   567	      : "이미 다른 열매가 칠해진 곳이라 칠하지 않았습니다(«다른 열매 위에는 안 칠함» 켜짐).");
   568	  } catch (e) { say("클릭 칠하기 실패: " + e.message, "err"); }
   569	  finally { S.samBusy = false; }
   570	}
   571	
   572	/* 모델 초벌: 미리 만든 번호 마스크(/draft)를 불러온다 — add = 빈 자리의 열매만 더하기, 아니면 전부 바꾸기 */
   573	async function loadDraft(add) {
   574	  if (!S.L) return;
   575	  const g = S.gen;
   576	  const b = await getBytes(`/draft?fruit=${S.fruit}&stem=${encodeURIComponent(S.stem)}`);
   577	  if (stale(g)) return;
   578	  if (!b) return say("이 사진에는 모델 초벌이 아직 없습니다.", "err");
   579	  const D0 = (await decodeGrayPng(b)).data;
   580	  if (stale(g)) return;
   581	  const D = D0, L = S.L, before = snapshot();
   582	  if (!S.draftIds) S.draftIds = new Set();
   583	  if (D.length !== L.length) return say("초벌 크기가 사진과 다릅니다.", "err");
   584	  let added = 0;
   585	  if (!add) {
   586	    for (let i = 0; i < L.length; i++) L[i] = D[i];
   587	    S.draftIds = new Set(idsNow().ids);
   588	    added = idsNow().ids.length;
   589	  } else {
   590	    const tot = new Uint32Array(65536), ov = new Uint32Array(65536);
   591	    for (let i = 0; i < L.length; i++) { const d = D[i]; if (d) { tot[d]++; if (L[i]) ov[d]++; } }
   592	    const map = new Uint16Array(65536); let next = Math.max(maxId(), S.lastNew);
   593	    for (let d = 1; d < 65535; d++) if (tot[d] && ov[d] < 0.3 * tot[d]) { map[d] = ++next; added++; S.draftIds.add(next); }
   594	    for (let i = 0; i < L.length; i++) { const m = map[D[i]]; if (m && !L[i]) L[i] = m; }
   595	    S.lastNew = next;
   596	  }
   597	  paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
   598	  computeCenters(); drawHud();
   599	  say(add ? `모델 초벌에서 빠진 열매 ${added}개를 더했습니다(노란 동그라미). 틀린 건 오른쪽 클릭(채우기통·✨)으로 지운 뒤 저장하세요.`
   600	    : `모델 초벌로 바꿨습니다(열매 ${added}개). 확인하고 고친 뒤 저장하세요. Ctrl+Z 로 되돌릴 수 있습니다.`, "ok");
   601	}
   602	
   603	/* 번호만 다시 나누기: 칠한 모양(마스크)은 그대로 두고, 번호를 원본 정답(kind=gt) 또는 모델 초벌로 나눈다.
   604	   참고 번호가 없는 칠한 자리는 원래 번호(회색은 회색)를 그대로 둔다. 번호는 1부터 다시 매긴다. */
   605	async function splitBy(kind) {
   606	  if (!S.L) return;
   607	  const g = S.gen;
   608	  const b = await getBytes(`/draft?fruit=${S.fruit}&stem=${encodeURIComponent(S.stem)}${kind === "gt" ? "&kind=gt" : ""}`);
   609	  if (stale(g)) return;
   610	  if (!b) return say(kind === "gt" ? "이 사진에는 원본 정답 번호가 없습니다(사과는 원래 정답 번호가 기본)." : "이 사진에는 모델 초벌이 없습니다.", "err");
   611	  const D = (await decodeGrayPng(b)).data;
   612	  if (stale(g)) return;
   613	  const L = S.L, before = snapshot();
   614	  if (D.length !== L.length) return say("번호 파일 크기가 사진과 다릅니다.", "err");
   615	  const mapD = new Map(); let next = 0;
   616	  for (let i = 0; i < L.length; i++) {
   617	    const v = L[i]; if (!v) continue;
   618	    const d = D[i];
   619	    if (d) { let m = mapD.get(d); if (!m) mapD.set(d, m = ++next); L[i] = m; }
   620	  }
   621	  // 참고 번호가 없는 칠한 자리: 덩어리(4-연결)로 묶어 큰 것(≥ BIG 화소)은 새 열매, 작은 가장자리 조각은 옆 열매에 붙인다
   622	  const W = S.W, BIG = 300, left = new Int32Array(L.length).fill(-1), stack = new Int32Array(L.length), small = [];
   623	  for (let s = 0; s < L.length; s++) {
   624	    if (!before[s] || D[s] || left[s] >= 0) continue;
   625	    let sp = 0; const comp = []; stack[sp++] = s; left[s] = s;
   626	    while (sp) {
   627	      const i = stack[--sp]; comp.push(i); const x = i % W;
   628	      for (const j of [x > 0 ? i - 1 : -1, x < W - 1 ? i + 1 : -1, i - W, i + W]) {
   629	        if (j < 0 || j >= L.length || left[j] >= 0 || !before[j] || D[j]) continue;
   630	        left[j] = s; stack[sp++] = j;
   631	      }
   632	    }
   633	    if (comp.length >= BIG) { const m = ++next; for (const i of comp) L[i] = m; }
   634	    else for (const i of comp) { L[i] = 0; small.push(i); }
   635	  }
   636	  for (let pass = 0; pass < 30 && small.length; pass++) {       // 작은 조각을 바깥에서부터 옆 번호로 채운다
   637	    const took = [];
   638	    for (let k = small.length - 1; k >= 0; k--) {
   639	      const i = small[k], x = i % W;
   640	      const nb = (x > 0 && L[i - 1]) || (x < W - 1 && L[i + 1]) || (i >= W && L[i - W]) || (i + W < L.length && L[i + W]);
   641	      if (nb && nb !== HOLE) took.push([i, nb]);
   642	    }
   643	    if (!took.length) break;
   644	    const done = new Set(took.map((t) => t[0]));
   645	    for (const [i, nb] of took) L[i] = nb;
   646	    for (let k = small.length - 1; k >= 0; k--) if (done.has(small[k])) small.splice(k, 1);
   647	  }
   648	  for (const i of small) L[i] = HOLE;                        // 어디에도 안 닿는 작은 점은 «번호 없음»(마스크는 유지)
   649	  S.lastNew = next; S.draftIds = new Set();
   650	  paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
   651	  say(`번호를 ${kind === "gt" ? "원본 정답" : "모델 초벌"} 기준으로 다시 나눴습니다 — 열매 ${idsNow().ids.length}개(칠한 모양은 그대로). 확인 뒤 저장하세요.`, "ok");
   652	}
   653	
   654	/* ── 번호·팔레트 ── */
   655	function maxId() { let m = 0; const L = S.L; for (let i = 0; i < L.length; i++) { const v = L[i]; if (v !== HOLE && v > m) m = v; } return m; }
   656	function idsNow() {
   657	  const seen = new Uint8Array(65536); let hole = false;
   658	  for (let i = 0; i < S.L.length; i++) { const v = S.L[i]; if (v === HOLE) hole = true; else seen[v] = 1; }
   659	  const ids = []; for (let v = 1; v < HOLE; v++) if (seen[v]) ids.push(v);
   660	  return { ids, hole };
   661	}
   662	function newNumber() {
   663	  if (!S.L) return;
   664	  S.lastNew = Math.max(maxId(), S.lastNew) + 1;
   665	  setCur(S.lastNew);
   666	  say(`새 번호 ${S.cur}번. 이 색으로 열매 하나를 칠하세요.`);
   667	}
   668	function setCur(v) {
   669	  S.cur = v;
   670	  $("#cur-sw").style.background = cssOf(v);
   671	  $("#cur-txt").textContent = v ? v + "번" : "지우기";
   672	  document.querySelectorAll(".sw").forEach((e) => e.classList.toggle("on", +e.dataset.id === v));
   673	}
   674	function renderPalette() {
   675	  const { ids, hole } = S.idsCache || idsNow();
   676	  const box = $("#swatches");
   677	  let h = `<div class="sw erase" data-id="0" title="배경색(지우기). 이 색으로 칠하면 지워집니다">지우기</div>`;
   678	  h += `<div class="sw new" data-act="new" title="새 번호 (N)">＋</div>`;
   679	  if (hole) h += `<div class="sw hole" title="원본에 칠해져 있지만 번호가 없는 곳. 채우기통으로 누르면 번호가 붙습니다">?</div>`;
   680	  if (S.cur && !ids.includes(S.cur)) h += `<div class="sw" data-id="${S.cur}" style="background:${cssOf(S.cur)}" title="${S.cur}번 (아직 안 칠함)">${S.cur}</div>`;
   681	  for (const v of ids) h += `<div class="sw" data-id="${v}" style="background:${cssOf(v)}" title="${v}번">${v}</div>`;
   682	  box.innerHTML = h;
   683	  setCur(S.cur);
   684	}
   685	function renderCount() {
   686	  const { ids, hole } = S.idsCache || idsNow();
   687	  $("#count").textContent = `열매 ${ids.length}개` + (hole ? " · 회색(번호 없음) 있음" : "");
   688	}
   689	/* 진행: 이 과일에서 저장(✓)·뺌(✕)한 사진 수 */
   690	function renderProgress() {
   691	  const n = S.items.length, done = S.items.filter((it) => itemMark(it) !== "　").length;
   692	  $("#prog").textContent = n ? `진행 ${done}/${n} (${Math.round(done * 100 / n)}%)` : "";
   693	}
   694	
   695	/* ── 도구·옵션 상자 ── */
   696	const TOOL_KEYS = { b: "brush", e: "eraser", f: "fill", l: "lasso", i: "pick", z: "zoom", h: "hand", s: "sam" };
   697	function setTool(t) {
   698	  S.tool = t;
   699	  document.querySelectorAll("#tools [data-tool]").forEach((b) => b.classList.toggle("on", b.dataset.tool === t));
   700	  const o = $("#options");
   701	  const sizes = [4, 8, 16, 32, 64];
   702	  const sizeHtml = `<div>굵기 <b id="sz">${S.size}</b></div><div class="sizes">` +
   703	    sizes.map((s) => `<button class="optbtn${s === S.size ? " on" : ""}" data-size="${s}">● ${s}</button>`).join("") + `</div>`;
   704	  const protect = `<label><input type="checkbox" id="protect"${S.protect ? " checked" : ""}> 다른 열매 위에는 안 칠함</label>`;
   705	  const help = {
   706	    brush: "왼쪽 = 지금 색으로 칠하기<br>오른쪽 = 지우기" + sizeHtml + protect,
   707	    eraser: "끌어서 지우기(마스크와 번호가 같이 지워짐)" + sizeHtml,
   708	    fill: "칠한 덩어리를 누르면 지금 색이 됩니다.<br>오른쪽 = 덩어리 통째로 지우기" +
   709	      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호 (열매 세기)</label>` +
   710	      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로 (가려진 조각 합치기)</label>`,
   711	    lasso: "열매 테두리를 따라 그리고 손을 떼면 안이 칠해집니다.<br>오른쪽 = 그 안 지우기" + protect,
   712	    pick: "열매를 누르면 그 색(번호)을 집습니다.",
   713	    sam: "열매를 누르면 AI 가 모양대로 칠합니다.<br>같은 자리를 <b>다시 누르면</b> 다른 모양(작게/크게).<br><b>끌어서 네모</b> = 그 안의 열매 하나<br><b>Shift+클릭</b> = 방금 칠한 것에서 «여기는 아님»<br>오른쪽 = 그 열매 통째로 지우기" +
   714	      `<label><input type="radio" name="fm" value="new"${S.fillNew ? " checked" : ""}> 누를 때마다 새 번호</label>` +
   715	      `<label><input type="radio" name="fm" value="same"${S.fillNew ? "" : " checked"}> 지금 색 그대로</label>` + protect,
   716	    zoom: "왼쪽 = 확대 · 오른쪽 = 축소<br>(휠로도 됩니다)",
   717	    hand: "끌어서 옮깁니다.<br>(다른 도구에서도 스페이스를 누른 채 끌면 됩니다)",
   718	  }[t];
   719	  o.innerHTML = help;
   720	  o.querySelectorAll("[data-size]").forEach((b) => b.onclick = () => { S.size = +b.dataset.size; setTool(S.tool); });
   721	  const p = o.querySelector("#protect"); if (p) p.onchange = () => { S.protect = p.checked; };
   722	  o.querySelectorAll("input[name=fm]").forEach((r) => r.onchange = () => { S.fillNew = r.value === "new"; });
   723	  stage.style.cursor = t === "hand" ? "grab" : t === "zoom" ? "zoom-in" : t === "sam" ? "cell" : "crosshair";
   724	  drawHud();
   725	}
   726	
   727	/* ── 마우스 ── */
   728	let drag = null, spaceDown = false;
   729	function toImg(e) {
   730	  const r = stage.getBoundingClientRect(), sx = e.clientX - r.left, sy = e.clientY - r.top;
   731	  return { sx, sy, x: (sx - S.ox) / S.z, y: (sy - S.oy) / S.z };
   732	}
   733	stage.addEventListener("contextmenu", (e) => e.preventDefault());
   734	stage.addEventListener("mousedown", (e) => {
   735	  if (!S.L || S.busy || e.target.closest("#zoombar")) return;      // 확대 단추를 누를 때 그림에 칠해지지 않게
   736	  const p = toImg(e), right = e.button === 2;
   737	  if (e.button === 1 || spaceDown || S.tool === "hand") { stopAnim(); drag = { kind: "pan", sx: p.sx, sy: p.sy, ox: S.ox, oy: S.oy }; stage.style.cursor = "grabbing"; return; }
   738	  const ix = Math.floor(p.x), iy = Math.floor(p.y), inside = ix >= 0 && iy >= 0 && ix < S.W && iy < S.H;
   739	  if (S.tool === "zoom") { zoomAt(p.sx, p.sy, right ? 1 / 1.6 : 1.6); return; }
   740	  if (S.tool === "pick") {
   741	    if (!inside) return;
   742	    const v = S.L[iy * S.W + ix];
   743	    if (v === HOLE) return say("회색(번호 없는 곳)은 집을 수 없습니다. 채우기통으로 번호를 붙이세요.");
   744	    setCur(v); setTool("brush"); say(v ? `${v}번 색을 집었습니다. 붓으로 바뀌었습니다.` : "지우기 색을 집었습니다.");
   745	    return;
   746	  }
   747	  if (S.tool === "fill") {
   748	    if (!inside) return;
   749	    if (right) { fillAt(ix, iy, 0); return; }
   750	    let val = S.cur;
   751	    if (S.fillNew) val = Math.max(maxId(), S.lastNew) + 1;
   752	    if (fillAt(ix, iy, val) && S.fillNew) { S.lastNew = val; setCur(val); renderPalette(); }
   753	    return;
   754	  }
   755	  if (S.tool === "sam") {
   756	    if (!inside) return;
   757	    if (right) { eraseId(ix, iy); return; }
   758	    drag = { kind: "sam", sx: p.sx, sy: p.sy, x: p.x, y: p.y, ex: p.x, ey: p.y, shift: e.shiftKey };   // 떼는 순간 클릭/네모를 가린다
   759	    return;
   760	  }
   761	  if (S.tool === "lasso") { lassoPts = [[p.x, p.y]]; lassoPts.erase = right; drag = { kind: "lasso" }; return; }
   762	  // 붓·지우개
   763	  const val = S.tool === "eraser" || right ? 0 : S.cur;
   764	  const box = [Infinity, Infinity, -Infinity, -Infinity];
   765	  drag = { kind: "paint", val, last: [p.x, p.y], before: snapshot(), box };
   766	  stamp(p.x, p.y, val, box);
   767	});
   768	window.addEventListener("mousemove", (e) => {
   769	  if (!S.L) return;
   770	  const p = toImg(e);
   771	  const inside = e.target === hud || e.target === stage || stage.contains(e.target);
   772	  mouse = inside ? p : null;
   773	  const ix = Math.floor(p.x), iy = Math.floor(p.y);
   774	  if (ix >= 0 && iy >= 0 && ix < S.W && iy < S.H) {
   775	    const v = S.L[iy * S.W + ix];
   776	    $("#pos").textContent = `${ix}, ${iy}` + (v === HOLE ? " · 번호없음" : v ? ` · ${v}번` : "");
   777	  }
   778	  if (drag && drag.kind === "pan") { S.ox = drag.ox + p.sx - drag.sx; S.oy = drag.oy + p.sy - drag.sy; applyView(); return; }
   779	  if (drag && drag.kind === "paint") { strokeTo(drag.last, [p.x, p.y], drag.val, drag.box); drag.last = [p.x, p.y]; }
   780	  if (drag && drag.kind === "lasso") lassoPts.push([p.x, p.y]);
   781	  if (drag && drag.kind === "sam") { drag.ex = p.x; drag.ey = p.y; drag.esx = p.sx; drag.esy = p.sy; }
   782	  drawHud();
   783	});
   784	window.addEventListener("mouseup", () => {
   785	  if (!drag) return;
   786	  const d = drag; drag = null;
   787	  if (d.kind === "pan") { stage.style.cursor = S.tool === "hand" ? "grab" : "crosshair"; return; }
   788	  if (d.kind === "paint") pushUndo(d.before, d.box[0], d.box[1], d.box[2], d.box[3]);
   789	  if (d.kind === "sam") {
   790	    const moved = d.esx !== undefined && Math.hypot(d.esx - d.sx, d.esy - d.sy) > 8;
   791	    drawHud();
   792	    const cl = (v, m) => Math.max(0, Math.min(m - 1, Math.floor(v)));
   793	    if (moved) samBox([cl(Math.min(d.x, d.ex), S.W), cl(Math.min(d.y, d.ey), S.H), cl(Math.max(d.x, d.ex), S.W), cl(Math.max(d.y, d.ey), S.H)]);
   794	    else if (d.shift) samNeg(cl(d.x, S.W), cl(d.y, S.H));
   795	    else samClick(cl(d.x, S.W), cl(d.y, S.H));
   796	    return;
   797	  }
   798	  if (d.kind === "lasso") {
   799	    const pts = lassoPts; lassoPts = null;
   800	    if (pts.length > 2) fillPolygon(pts, pts.erase ? 0 : S.cur);
   801	    drawHud();
   802	  }
   803	});
   804	stage.addEventListener("wheel", (e) => {
   805	  e.preventDefault(); if (!S.L) return;
   806	  const dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1);
   807	  const p = toImg(e); zoomAt(p.sx, p.sy, Math.exp(-Math.max(-300, Math.min(300, dy)) * 0.0014));
   808	}, { passive: false });
   809	stage.addEventListener("mouseleave", () => { mouse = null; drawHud(); });
   810	
   811	/* ── 저장 ── */
   812	function encodeBinary() {
   813	  const c = document.createElement("canvas"); c.width = S.W; c.height = S.H;
   814	  const x = c.getContext("2d"), d = x.createImageData(S.W, S.H), u = new Uint32Array(d.data.buffer);
   815	  for (let i = 0; i < S.L.length; i++) u[i] = S.L[i] ? 0xffffffff : 0xff000000;
   816	  x.putImageData(d, 0, 0); return c.toDataURL("image/png");
   817	}
   818	function encodeInstances() {
   819	  // 번호 = R + G*256 (서버 instances.py 가 이 규칙으로 읽는다). 회색(번호 없음)은 0 으로 보낸다.
   820	  const c = document.createElement("canvas"); c.width = S.W; c.height = S.H;
   821	  const x = c.getContext("2d"), d = x.createImageData(S.W, S.H), a = d.data;
   822	  for (let i = 0; i < S.L.length; i++) {
   823	    const v = S.L[i] === HOLE ? 0 : S.L[i];
   824	    a[i * 4] = v & 255; a[i * 4 + 1] = v >> 8; a[i * 4 + 2] = 0; a[i * 4 + 3] = 255;
   825	  }
   826	  x.putImageData(d, 0, 0); return c.toDataURL("image/png");
   827	}
   828	function boxesNow() {
   829	  const W = S.W, b = new Map();
   830	  for (let i = 0; i < S.L.length; i++) {
   831	    const v = S.L[i]; if (!v || v === HOLE) continue;
   832	    const x = i % W, y = (i / W) | 0; let r = b.get(v);
   833	    if (!r) b.set(v, r = [x, y, x, y, 0]);
   834	    if (x < r[0]) r[0] = x; if (x > r[2]) r[2] = x; if (y < r[1]) r[1] = y; if (y > r[3]) r[3] = y; r[4]++;
   835	  }
   836	  return [...b.entries()].sort((p, q) => p[0] - q[0]).filter(([, r]) => r[4] >= 4)
   837	    .map(([, r]) => ({ xyxy: [r[0], r[1], r[2] + 1, r[3] + 1], cls: "fruit", src: "human" }));
   838	}
   839	async function save() {
   840	  if (!S.L || S.busy) return false;
   841	  const by = who() || askWho();
   842	  const { ids, hole } = idsNow();
   843	  if (!ids.length && hole) { say("번호가 하나도 없습니다. 회색 열매를 채우기통으로 눌러 번호를 붙인 뒤 저장하세요.", "err"); return false; }
   844	  S.busy = true; say("저장하는 중…");
   845	  const base = { fruit: S.fruit, stem: S.stem, by };
   846	  try {
   847	    await postJSON("/api/save", { ...base, action: "fixed", png: encodeBinary(), note: "그림판 저장" });
   848	    await postJSON("/api/status", { ...base, status: "fixed", confirm: true, kind: "mask", note: "그림판 저장" });
   849	    if (ids.length) await postJSON("/api/save_instances", { ...base, png: encodeInstances(), counts: {}, note: "그림판 저장" });
   850	    const boxes = boxesNow();
   851	    await postJSON("/api/boxes", { ...base, boxes, note: "그림판 저장(번호마다 상자 하나)" });
   852	    setDirty(false);
   853	    const it = S.items.find((x) => x.stem === S.stem);
   854	    if (it) { it.confirmed = "fixed"; it.confirmed_instances = ids.length ? "fixed" : null; }
   855	    markOption();
   856	    say(`저장했습니다 — 열매 ${ids.length}개 · 상자 ${boxes.length}개.`, "ok");
   857	    return true;
   858	  } catch (e) {
   859	    say("저장 실패: " + e.message, "err"); return false;
   860	  } finally { S.busy = false; }
   861	}
   862	function markOption() {
   863	  const it = S.items.find((x) => x.stem === S.stem), o = $("#photo").selectedOptions[0];
   864	  if (it && o) o.textContent = itemMark(it) + o.textContent.slice(2);
   865	  renderProgress();
   866	}
   867	async function setExclude(on) {
   868	  if (!S.L || S.busy) return;
   869	  const by = who() || askWho(), base = { fruit: S.fruit, stem: S.stem, by };
   870	  S.busy = true;                               // 기다리는 동안 사진을 못 넘긴다(검수 1회 지적 2)
   871	  try {
   872	    if (on) {
   873	      await postJSON("/api/save", { ...base, action: "exclude", note: "그림판: 이 사진 빼기" });
   874	      await postJSON("/api/status", { ...base, status: "exclude", confirm: true, kind: "mask", note: "그림판: 이 사진 빼기" });
   875	    } else {
   876	      await postJSON("/api/save", { ...base, action: "ok", note: "그림판: 빼기 취소" });
   877	      await postJSON("/api/status", { ...base, status: "ok", confirm: true, kind: "mask", note: "그림판: 빼기 취소" });
   878	    }
   879	    const it = S.items.find((x) => x.stem === base.stem); if (it) it.confirmed = on ? "exclude" : "ok";
   880	    markOption();
   881	    say(on ? "이 사진을 «빼기» 로 표시했습니다. 다음 사진으로 넘어갑니다." : "빼기를 취소했습니다.", "ok");
   882	  } catch (e) { say("실패: " + e.message, "err"); return; }
   883	  finally { S.busy = false; }
   884	  if (on && S.stem === base.stem && !S.dirty) go(1, true);
   885	}
   886	
   887	/* ── 사진 넘기기 ── */
   888	async function go(d, skipAsk) {
   889	  const sel = $("#photo"), i = sel.selectedIndex + d;
   890	  if (i < 0 || i >= sel.options.length) return say(d > 0 ? "마지막 사진입니다." : "첫 사진입니다.");
   891	  if (!skipAsk && !(await leaveOk())) return;
   892	  sel.selectedIndex = i; openPhoto(sel.value);
   893	}
   894	async function leaveOk() {
   895	  if (!S.dirty) return true;
   896	  if (confirm("바뀐 것이 있습니다. 저장하고 넘어갈까요?\n(확인 = 저장하고 넘어감 · 취소 = 이 사진에 머무름)")) return await save();
   897	  return false;
   898	}
   899	window.addEventListener("beforeunload", (e) => { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
   900	
   901	/* ── 단추·메뉴·단축키 연결 ── */
   902	const ACTS = {
   903	  save, undo, redo, new: newNumber,
   904	  "save-next": async () => { if (await save()) go(1, true); },
   905	  prev: () => go(-1), next: () => go(1),
   906	  exclude: () => setExclude(true), unexclude: () => setExclude(false),
   907	  "reload-orig": () => { if (confirm("원본(처음 받은 라벨)을 다시 불러올까요? 저장하기 전까지는 파일이 안 바뀝니다.")) openPhoto(S.stem, true); },
   908	  "clear-all": () => {
   909	    if (!S.L || !confirm("이 사진의 칠한 것을 전부 지울까요? (Ctrl+Z 로 되돌릴 수 있음)")) return;
   910	    const before = snapshot(); S.L.fill(0); paintRect(0, 0, S.W, S.H); pushUndo(before, 0, 0, S.W, S.H);
   911	    say("전부 지웠습니다. 열매가 없는 사진이면 «이 사진 빼기» 가 맞습니다.");
   912	  },
   913	  "toggle-color": () => { S.showColor = !S.showColor; applyView(); },
   914	  orig: () => { S.showColor = !S.showColor; applyView(); },
   915	  "toggle-nums": () => { S.showNums = !S.showNums; drawHud(); },
   916	  fit: () => S.L && fit(true),
   917	  "zoom-in": () => S.L && zoomCenter(1.25),
   918	  "zoom-out": () => S.L && zoomCenter(1 / 1.25),
   919	  "zoom-100": () => S.L && zoomCenter(1 / viewTarget().z),
   920	  "draft-add": () => loadDraft(true),
   921	  "split-gt": () => splitBy("gt"),
   922	  "split-draft": () => splitBy("draft"),
   923	  "draft-replace": () => { if (confirm("지금 칠한 것을 모델 초벌로 전부 바꿀까요? (Ctrl+Z 로 되돌릴 수 있음)")) loadDraft(false); },
   924	};
   925	document.addEventListener("click", (e) => {
   926	  const mb = e.target.closest(".mbtn");
   927	  document.querySelectorAll(".menu").forEach((m) => { if (!mb || m !== mb.parentElement) m.classList.remove("open"); });
   928	  if (mb) { mb.parentElement.classList.toggle("open"); return; }
   929	  const a = e.target.closest("[data-act]");
   930	  if (a) { document.querySelectorAll(".menu").forEach((m) => m.classList.remove("open")); ACTS[a.dataset.act] && ACTS[a.dataset.act](); return; }
   931	  const t = e.target.closest("[data-tool]"); if (t) return setTool(t.dataset.tool);
   932	  const sw = e.target.closest(".sw[data-id]");
   933	  if (sw) { setCur(+sw.dataset.id); if (S.tool === "fill" && S.fillNew) { S.fillNew = false; setTool("fill"); } if (!["brush", "fill", "lasso"].includes(S.tool)) setTool("brush"); }
   934	});
   935	$("#save").onclick = save;
   936	$("#orig").onclick = () => ACTS.orig();
   937	$("#prev").onclick = () => go(-1);
   938	$("#next").onclick = () => go(1);
   939	$("#fruit").onchange = async () => {
   940	  if (await leaveOk()) { setDirty(false); S.stem = ""; loadList(); }
   941	  else $("#fruit").value = S.fruit;              // 취소하면 목록 표시도 지금 과일로 되돌린다
   942	};
   943	$("#photo").onchange = async () => {
   944	  const want = $("#photo").value;
   945	  if (await leaveOk()) openPhoto(want); else $("#photo").value = S.stem;
   946	};
   947	$("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") renderList(S.stem); });
   948	$("#only-todo").onchange = () => renderList(S.stem);
   949	$("#alpha").oninput = () => { S.alpha = $("#alpha").value / 100; applyView(); };
   950	$("#who").onclick = askWho;
   951	window.addEventListener("resize", () => S.L && applyView());
   952	window.addEventListener("blur", () => { if (S.peek) { S.peek = false; applyView(); } });   // 키를 뗀 걸 못 받아도 풀리게
   953	
   954	document.addEventListener("keydown", (e) => {
   955	  if (e.key === "Escape") {
   956	    document.querySelectorAll(".menu.open").forEach((m) => m.classList.remove("open"));
   957	    if (drag && (drag.kind === "lasso" || drag.kind === "sam")) { drag = null; lassoPts = null; drawHud(); say("취소했습니다."); }
   958	    return;
   959	  }
   960	  if (e.target.matches("input, select, textarea")) return;
   961	  const k = e.key.toLowerCase();
   962	  if ((e.ctrlKey || e.metaKey) && k === "s") { e.preventDefault(); save(); return; }
   963	  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); ACTS["save-next"](); return; }
   964	  if ((e.ctrlKey || e.metaKey) && k === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
   965	  if ((e.ctrlKey || e.metaKey) && k === "y") { e.preventDefault(); redo(); return; }
   966	  if (e.ctrlKey || e.metaKey || e.altKey) return;
   967	  if (k === " ") { spaceDown = true; stage.style.cursor = "grab"; e.preventDefault(); return; }
   968	  if (e.key === "`" || e.code === "Backquote") { if (!S.peek) { S.peek = true; applyView(); } return; }
   969	  if (TOOL_KEYS[k]) return setTool(TOOL_KEYS[k]);
   970	  if (k === "n") return newNumber();
   971	  if (k === "[") { S.size = Math.max(1, Math.round(S.size / 1.25)); return setTool(S.tool); }
   972	  if (k === "]") { S.size = Math.min(200, Math.round(S.size * 1.25) + 1); return setTool(S.tool); }
   973	  if (k === "v") return ACTS["toggle-color"]();
   974	  if (k === "t") return ACTS["toggle-nums"]();
   975	  if (k === "0") return ACTS.fit();
   976	  if (e.key === "+" || e.key === "=") return ACTS["zoom-in"]();
   977	  if (e.key === "-" || e.key === "_") return ACTS["zoom-out"]();
   978	  if (k === "1") return ACTS["zoom-100"]();
   979	  if (k === "a" || e.key === "ArrowLeft") return go(-1);
   980	  if (k === "d" || e.key === "ArrowRight") return go(1);
   981	});
   982	document.addEventListener("keyup", (e) => { if ((e.key === "`" || e.code === "Backquote") && S.peek) { S.peek = false; applyView(); } if (e.key === " ") { spaceDown = false; stage.style.cursor = S.tool === "hand" ? "grab" : "crosshair"; } });
   983	
   984	/* ── 시작 ── */
   985	(async function start() {
   986	  $("#who").textContent = "작업자: " + (who() || "(눌러서 이름 적기)");
   987	  setTool("brush");
   988	  try { await loadFruits(); await loadList(); }
   989	  catch (e) { say("시작 실패: " + e.message, "err"); }
   990	})();

===== app/static/paint/paint.css =====
     1	/* 라벨 그림판 화면 모양 — 윈도 그림판(레퍼런스1·2)을 본뜬 회색 창 */
     2	:root {
     3	  --face: #c0c0c0; --hi: #ffffff; --lo: #808080; --dk: #000000;
     4	  --title: #000080; --title2: #1084d0; --sel: #000080;
     5	}
     6	* { box-sizing: border-box; }
     7	html, body { margin: 0; height: 100%; background: #008080; font: 14px "Malgun Gothic", "Apple SD Gothic Neo", sans-serif; }
     8	#win { position: fixed; inset: 0; display: flex; flex-direction: column; background: var(--face); }
     9	kbd { font: 12px monospace; background: #fff; border: 1px solid var(--lo); padding: 0 3px; }
    10	
    11	/* 제목 줄 */
    12	#title { background: linear-gradient(90deg, var(--title), var(--title2)); color: #fff; font-weight: bold; padding: 4px 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    13	#t-dirty { color: #ffd84a; margin-left: 8px; }
    14	
    15	/* 메뉴 줄 */
    16	#menubar { display: flex; align-items: center; gap: 2px; padding: 2px 4px; border-bottom: 1px solid var(--lo); flex-wrap: wrap; }
    17	.menu { position: relative; }
    18	.mbtn { background: none; border: 1px solid transparent; padding: 3px 10px; font: inherit; cursor: pointer; }
    19	.mbtn:hover, .menu.open .mbtn { border-color: var(--hi) var(--lo) var(--lo) var(--hi); }
    20	.drop { display: none; position: absolute; top: 100%; left: 0; z-index: 50; min-width: 260px; background: var(--face);
    21	  border: 2px solid; border-color: var(--hi) var(--dk) var(--dk) var(--hi); padding: 3px; box-shadow: 2px 2px 0 rgba(0,0,0,.3); }
    22	.drop.wide { width: 440px; padding: 8px 12px; line-height: 1.5; }
    23	.drop.wide p { margin: 2px 0 8px; }
    24	.menu.open .drop { display: block; }
    25	.drop button, .drop a { display: flex; justify-content: space-between; gap: 16px; width: 100%; text-align: left; background: none; border: 0;
    26	  padding: 5px 10px; font: inherit; cursor: pointer; color: #000; text-decoration: none; }
    27	.drop button:hover, .drop a:hover { background: var(--sel); color: #fff; }
    28	.drop hr { border: 0; border-top: 1px solid var(--lo); border-bottom: 1px solid var(--hi); margin: 3px 0; }
    29	.drop .row { display: flex; gap: 8px; align-items: center; padding: 5px 10px; }
    30	
    31	#nav { display: flex; align-items: center; gap: 4px; margin-left: auto; flex-wrap: wrap; }
    32	#nav select, #nav input, #nav button { font: inherit; }
    33	#photo { max-width: 340px; }
    34	.chk { display: flex; align-items: center; gap: 2px; }
    35	button.w95, #nav button, #tools button, .optbtn { background: var(--face); border: 2px solid; border-color: var(--hi) var(--dk) var(--dk) var(--hi); cursor: pointer; }
    36	#nav button:active, #tools button:active { border-color: var(--dk) var(--hi) var(--hi) var(--dk); }
    37	#nav button.primary { font-weight: bold; padding: 3px 16px; }
    38	#nav button.primary.dirty { background: #ffe680; }
    39	
    40	/* 가운데: 도구 상자 + 그림 */
    41	#body { flex: 1; display: flex; min-height: 0; }
    42	#toolbox { width: 132px; padding: 4px; border-right: 1px solid var(--lo); display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
    43	#tools { display: grid; grid-template-columns: 1fr 1fr; gap: 2px; }
    44	#tools button { height: 54px; font-size: 22px; line-height: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 0; }
    45	#tools button span { font-size: 11px; }
    46	#tools button.wide { grid-column: span 2; height: 44px; flex-direction: row; gap: 6px; }
    47	#tools button.wide span { font-size: 13px; font-weight: bold; }
    48	#tools button.on { border-color: var(--dk) var(--hi) var(--hi) var(--dk); background: #dcdcdc repeating-conic-gradient(#c0c0c0 0 25%, #e8e8e8 0 50%) 0 0/4px 4px; }
    49	#options { border: 2px solid; border-color: var(--lo) var(--hi) var(--hi) var(--lo); padding: 6px; font-size: 12px; line-height: 1.4; min-height: 90px; }
    50	#options .sizes { display: flex; flex-direction: column; gap: 3px; margin: 4px 0; }
    51	.optbtn { font: inherit; padding: 3px; text-align: left; }
    52	.optbtn.on { background: var(--sel); color: #fff; }
    53	#options label { display: flex; gap: 4px; align-items: flex-start; margin: 3px 0; }
    54	
    55	#stage { position: relative; flex: 1; overflow: hidden; background: var(--lo); cursor: crosshair; }
    56	#world { position: absolute; left: 0; top: 0; transform-origin: 0 0; box-shadow: 0 0 0 1px #000; }
    57	#world canvas { position: absolute; left: 0; top: 0; }
    58	#ov { image-rendering: pixelated; }           /* 색 칸은 또렷하게, 사진은 부드럽게 확대 */
    59	#nav button#orig.on { background: #000080; color: #fff; }
    60	#ov { opacity: .5; }
    61	#hud { position: absolute; inset: 0; pointer-events: none; }
    62	#loading { position: absolute; left: 50%; top: 40%; transform: translate(-50%, -50%); background: #ffffe1; border: 1px solid #000; padding: 10px 20px; display: none; }
    63	
    64	/* 아래: 팔레트 */
    65	#palette { display: flex; gap: 6px; padding: 4px; border-top: 1px solid var(--hi); align-items: center; }
    66	#curbox { width: 72px; height: 44px; border: 2px solid; border-color: var(--lo) var(--hi) var(--hi) var(--lo); display: flex; align-items: center; gap: 4px; padding: 3px; background: #fff; }
    67	#cur-sw { width: 30px; height: 30px; border: 1px solid #000; }
    68	#cur-txt { font-weight: bold; font-size: 13px; }
    69	#swatches { flex: 1; display: flex; gap: 2px; overflow-x: auto; padding-bottom: 2px; }
    70	.sw { flex: 0 0 auto; width: 34px; height: 44px; border: 2px solid; border-color: var(--lo) var(--hi) var(--hi) var(--lo); cursor: pointer; font: bold 12px sans-serif;
    71	  display: flex; align-items: flex-end; justify-content: center; padding-bottom: 2px; color: #fff; text-shadow: 0 0 2px #000, 0 0 2px #000; }
    72	.sw.on { outline: 2px solid #000; outline-offset: -5px; }
    73	.sw.erase { background: #fff; color: #000; text-shadow: none; width: 44px; }
    74	.sw.new { background: var(--face); color: #000; text-shadow: none; font-size: 18px; align-items: center; width: 44px; }
    75	.sw.hole { background: #9a9a9a; cursor: default; }
    76	
    77	/* 맨 아래: 상태 줄 */
    78	#statusbar { display: flex; gap: 4px; padding: 2px 4px 4px; }
    79	#statusbar > div { border: 1px solid; border-color: var(--lo) var(--hi) var(--hi) var(--lo); padding: 3px 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    80	#msg { flex: 1; }
    81	#msg.err { color: #b00000; font-weight: bold; }
    82	#msg.ok { color: #006000; font-weight: bold; }
    83	#prog { width: 150px; }
    84	#count { width: 220px; }
    85	#prog, #count, #pos, .sw { font-variant-numeric: tabular-nums; }
    86	/* 키보드로 옮겨 다닐 때만 보이는 테두리(마우스 클릭에는 안 보임) */
    87	button:focus-visible, select:focus-visible, input:focus-visible, a:focus-visible { outline: 2px dotted #000; outline-offset: -4px; }
    88	#pos { width: 120px; }
    89	#who { width: 130px; cursor: pointer; }
    90	
    91	/* 오른쪽 아래 확대 단추 */
    92	#zoombar { position: absolute; right: 8px; bottom: 8px; display: flex; gap: 2px; padding: 2px; background: var(--face);
    93	  border: 2px solid; border-color: var(--hi) var(--dk) var(--dk) var(--hi); cursor: default; z-index: 5; }
    94	#zoombar button { min-width: 36px; height: 32px; font: inherit; font-weight: bold; background: var(--face); cursor: pointer;
    95	  border: 2px solid; border-color: var(--hi) var(--dk) var(--dk) var(--hi); font-variant-numeric: tabular-nums; }
    96	#zoombar button:active { border-color: var(--dk) var(--hi) var(--hi) var(--dk); }
    97	#zoombar #zpct { min-width: 60px; font-weight: normal; }
    98	#zoombar .fitbtn { padding: 0 10px; }

===== app/server.py =====
     1	# -*- coding: utf-8 -*-
     2	"""라벨링·검수 웹툴 서버 — **앱을 만들고 기능 묶음을 붙이는 것만** 한다.
     3	작성: 2026-09-16 · 구조 정리: 2026-09-20 (사이클 2)
     4	
     5	어디에 무엇이 있나 (처음 온 사람이 여기부터 본다)
     6	  core/paths.py         경로·과일 목록·데이터셋 폴더 (상수는 여기)
     7	  core/util.py          시각·자물쇠·오류 응답·로그
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
     9	  core/status_store.py  `status.json` **쓰는 길 하나** (판정·사람 확정)
    10	  domain/maskio.py      마스크 PNG(0/255·uint16) 파일 형식
    11	  domain/statusfmt.py   status 항목의 꼴 · 작업자 B·C 산출물 읽기
    12	  domain/rules.py       데이터 규칙(이름 있는 함수) — 규칙표가 여기를 가리킨다
    13	  domain/dupes.py       근접 중복 묶음
    14	  api/*.py              주소(라우트). 각 파일이 `register(app, ctx)` 하나를 갖는다
    15	
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    17	- 팀 표준 데이터셋은 **읽기 전용**. 사람이 고친 마스크는 data/<fruit>/masks_fixed/ 에만 쓴다.
    18	- 작업자 B(inspection.csv, duplicates.json) / 작업자 C(proposals/, proposal_scores.csv) 산출물은
    19	  있으면 읽고, 없으면 해당 기능을 숨긴다.
    20	실행: bash app/run.sh
    21	"""
    22	import os
    23	
    24	from flask import Flask
    25	from PIL import Image
    26	
    27	from api import ai as api_ai
    28	from api import boxes as api_boxes
    29	from api import counts as api_counts
    30	from api import dashboard as api_dashboard
    31	from api import dupes as api_dupes
    32	from api import export as api_export
    33	from api import instances as api_instances
    34	from api import masks as api_masks
    35	from api import photos as api_photos
    36	from api import team_review as api_team_review
    37	from core import auth, paths, status_store, util
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    39	from core.paths import (CACHE_DIR, DATASET, DATA_DIR, FRUITS, MAX_UPLOAD_BYTES, check,
    40	                        fixed_path, gt_path, img_path, proposal_path, stems_of)
    41	from core.util import err_json, lock_for, now_str
    42	from domain import dupes as DUP
    43	from domain.maskio import save_mask_atomic
    44	from domain.statusfmt import STATUSES
    45	
    46	Image.MAX_IMAGE_PIXELS = None
    47	
    48	app = Flask(__name__, static_folder=None)
    49	# 한 번에 받을 수 있는 요청 크기 상한(수정본 PNG 는 2MP 기준 수백 KB). 너무 큰 요청은 413.
    50	app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    51	
    52	# api 묶음이 서로 이름을 직접 부르지 않게 «넘겨주는 꾸러미» 하나로 모은다.
    53	# (0917 부터 boxes.py·instances.py 가 쓰던 방식 그대로 — 키 이름을 바꾸지 않는다)
    54	CTX = {
    55	    "check": check, "DATA_DIR": DATA_DIR, "DATASET": DATASET, "FRUITS": FRUITS,
    56	    "STATUSES": STATUSES, "img_path": img_path, "gt_path": gt_path,
    57	    "fixed_path": fixed_path, "proposal_path": proposal_path, "stems_of": stems_of,
    58	    "lock_for": lock_for, "err_json": err_json, "now_str": now_str,
    59	    "labeled": api_masks.labeled, "save_mask_atomic": save_mask_atomic,
    60	    "read_status": status_store.read_status, "write_status": status_store.write_status,
    61	    "update_status": status_store.update_status,
    62	    "write_status_entry": status_store.write_status_entry,
    63	    "backup_status": status_store.backup_status,
    64	    # 0918 사이클4: 상자·번호를 저장하면 그 작업의 확정이 «수정함» 으로 찍힌다
    65	    "confirm_status": status_store.confirm_status,
    66	    # 0918 사이클4 3차 전 소수정(총괄 결정 1) · 0919 사이클5 2차: 되돌리기·0개 저장은 확정을 벗긴다
    67	    "clear_confirm": status_store.clear_confirm,
    68	}
    69	
    70	# 순서: 문지기 → 오류 응답 → 기능 묶음. 주소가 서로 겹치지 않으므로 묶음 사이 순서는 상관없다.
    71	auth.register(app, CTX)
    72	util.register_errors(app)
    73	for _mod in (api_photos, api_masks, api_boxes, api_instances, api_counts,
    74	             api_dupes, api_export, api_dashboard, api_team_review, api_ai):
    75	    _mod.register(app, CTX)
    76	
    77	
    78	
    79	
    80	if __name__ == "__main__":
    81	    print("[라벨링툴] 원본 데이터 폴더(LABELTOOL_DATA_ROOT): %s" % DATASET, flush=True)
    82	    if DATASET != DUP.DEFAULT_DATASET:
    83	        print("[라벨링툴] ※ 기본값이 아닌 폴더를 보고 있습니다(기본: %s)" % DUP.DEFAULT_DATASET, flush=True)
    84	    for f in FRUITS:
    85	        os.makedirs(os.path.join(DATA_DIR, f, "masks_fixed"), exist_ok=True)
    86	        d = os.path.join(DATASET, f, "images")
    87	        print("[라벨링툴]   %-10s %s (%s)" % (
    88	            f, d, ("%d장" % len(stems_of(f))) if os.path.isdir(d) else "폴더 없음 — 이 과일은 비어 보입니다"),
    89	            flush=True)
    90	    port = int(os.environ.get("PORT", "5111"))
보안 관련 값·설정 세부는 공개본에서 생략했습니다.
    92	          flush=True)
    93	    # 0918 사이클2: 모래상자는 «127.0.0.1 만» 열어야 한다(남이 실수로 들어오지 못하게).
    94	    # 환경변수 HOST 를 주지 않으면 예전과 똑같이 0.0.0.0 이다 — 실서버 동작은 안 바뀐다.
    95	    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=port, threaded=True, debug=False)

===== app/boxes.py =====
     1	# -*- coding: utf-8 -*-
     2	"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.
     3	
     4	작성: 2026-09-20 (구조 정리 사이클 2)
     5	실제 코드는 `app/api/boxes.py (라우트·팀원 상자·내보내기) · app/domain/rules.py (상자 정리 규칙)` 에 있다. 이 파일에는 코드가 없다.
     6	
     7	왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
     8	  · `semantic-segmentation/tools/build_merged_dataset.py` (`import boxes` → `export_boxes_to`)
     9	  · `export/export_dataset.py` (`from boxes import human_count, team_count`)
    10	  · 지난 사이클 시험들(`tests/unit/u1_boxes_selftest.py` 등)
    11	그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
    12	(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
    13	공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
    14	"""
    15	from api.boxes import *        # noqa: F401,F403
    16	from api.boxes import (CLASSES, MAX_BOXES, MIN_SIDE, TEAM_BOX_DIRS, TEAM_CLS,
    17	                       boxes_of, clean, demo, export_boxes_to, human_count,
    18	                       read_team_boxes, register, team_box_path, team_count)  # noqa: F401
    19	

===== app/instances.py =====
     1	# -*- coding: utf-8 -*-
     2	"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.
     3	
     4	작성: 2026-09-20 (구조 정리 사이클 2)
     5	실제 코드는 `app/api/instances.py (번호본 읽기·쓰기·라우트) · app/domain/maskio.py (uint16 PNG) · app/api/counts.py (`/api/instance_stats`)` 에 있다. 이 파일에는 코드가 없다.
     6	
     7	왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
     8	  · `export/export_dataset.py` (`from instances import source_of, load_inst, …`)
     9	  · `semantic-segmentation/tools/tests_merged_260918/counts/test_counts.py:158` (`import instances`)
    10	  · 지난 사이클 시험들(`tests/unit/u3_instances_u16.py` 등)
    11	그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
    12	(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
    13	공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
    14	"""
    15	from api.instances import *    # noqa: F401,F403
    16	from api.instances import (CACHE_DIR, CC4, ERROR_CSV, KIND_SOURCE, NO_NUM, PARK,
    17	                           SEED_DIRS, SEED_SOURCE, cache_file, cached_counts,
    18	                           count_fresh, count_now, count_one, has_numbers, ids_of,
    19	                           inst_fixed_path, load_counts, load_inst, mask_path_of,
    20	                           png_u16_bytes, read_u16, recount, register, save_counts,
    21	                           seed_source_of, sig_of, source_name, source_of,
    22	                           stale_stems, start_count, summary, write_u16_atomic)  # noqa: F401
    23	

===== app/maskio.py =====
     1	# -*- coding: utf-8 -*-
     2	"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.
     3	
     4	작성: 2026-09-20 (구조 정리 사이클 2)
     5	실제 코드는 `app/domain/maskio.py` 에 있다. 이 파일에는 코드가 없다.
     6	
     7	왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
     8	  · `export/export_dataset.py` (`from maskio import load_mask_bool, save_mask_atomic`)
     9	  · 지난 사이클 시험들(`tests/unit/u2_maskio.py` 등)
    10	그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
    11	(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
    12	공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
    13	"""
    14	from domain.maskio import *    # noqa: F401,F403
    15	from domain.maskio import (bool_to_png_bytes, ids_of, load_mask_bool, load_mask_raw,
    16	                           mask_value_report, png_u16_bytes, raw_to_png_bytes,
    17	                           read_u16, save_mask_atomic, write_u16_atomic)  # noqa: F401
    18	

===== app/dupes.py =====
     1	# -*- coding: utf-8 -*-
     2	"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.
     3	
     4	작성: 2026-09-20 (구조 정리 사이클 2)
     5	실제 코드는 `app/domain/dupes.py (묶음 읽기·제외 목록) · app/core/paths.py (경로) · app/domain/rules.py (대표 고르기) · app/core/status_store.py (status.json)` 에 있다. 이 파일에는 코드가 없다.
     6	
     7	왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
     8	  · `export/export_dataset.py`·`export/make_delete_script.py` (`from dupes import …`)
     9	  · `app/api/instances.py` (`DUP.read_status`·`DUP.DATA_DIR`)
    10	그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
    11	(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
    12	공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
    13	"""
    14	from domain.dupes import *     # noqa: F401,F403
    15	from domain.dupes import (APP_DIR, DATASET, DATA_DIR, DEFAULT_DATASET, FRUITS, ROOT,
    16	                          dataset_for, duplicate_exclusions, excluded_stems,
    17	                          load_duplicate_groups, pick_representative,
    18	                          read_status, representative_map)  # noqa: F401
    19	

===== ai_helper/sam_server.py =====
     1	# -*- coding: utf-8 -*-
     2	# 그림판 «클릭 칠하기» 도우미 — GPU 에 SAM2.1 을 올려 두고, 누른 점 주변의 열매 모양 후보를 돌려준다
     3	"""작성: 2026-09-23
     4	
     5	- 127.0.0.1:5112 에서만 듣는다(밖에서 못 들어온다). 라벨링 툴(5111)의 /api/sam 이 대신 부른다.
     6	- 요청: POST /sam {"img": 사진 경로, "x": .., "y": .., "crop": 384}
     7	  또는 {"img", "points": [[x, y, 1|0], ...], "box": [x0, y0, x1, y1]} — 0 = 빼기 점(여기는 아님), box = 네모 범위
     8	- 답: {"ok": true, "cands": [{"x0","y0","w","h","score","png"(자른 칸 크기의 0/255 PNG, base64)}...]}
     9	  점수 높은 순. 잘라 낸 칸의 40% 넘게 덮는 후보(배경)는 뺀다.
    10	  1등 후보가 자른 칸 가장자리에 닿으면(열매가 칸보다 큼) 칸을 두 배로 키워 한 번 더 한다.
    11	실행: ai_helper/run_helper.sh (GPU 는 비어 있는 것을 고른다)
    12	"""
    13	import base64, io, os, threading, time
    14	
    15	import cv2
    16	import numpy as np
    17	from flask import Flask, jsonify, request
    18	from PIL import Image
    19	from ultralytics.models.sam import SAM2Predictor
    20	
    21	HERE = os.path.dirname(os.path.abspath(__file__))
    22	PRED = SAM2Predictor(overrides=dict(model=os.path.join(HERE, "weights", "sam2.1_b.pt"), device=0,
    23	                                    conf=0.0, verbose=False, save=False))
    24	LOCK = threading.Lock()
    25	_img_cache = {"path": None, "im": None}
    26	app = Flask(__name__)
    27	
    28	
    29	def _image(path):
    30	    if _img_cache["path"] != path:
    31	        im = cv2.imread(path, cv2.IMREAD_COLOR)
    32	        if im is None:
    33	            raise ValueError("사진을 읽지 못했습니다: %s" % path)
    34	        _img_cache.update(path=path, im=im)
    35	    return _img_cache["im"]
    36	
    37	
    38	def _png(mask):
    39	    buf = io.BytesIO()
    40	    Image.fromarray(mask.astype(np.uint8) * 255).save(buf, "PNG")
    41	    return base64.b64encode(buf.getvalue()).decode("ascii")
    42	
    43	
    44	def _run(im, pts, box, cs):
    45	    """pts = [[x, y, 1(포함)|0(빼기)], ...] · box = [x0, y0, x1, y1] 또는 None (둘 다 사진 좌표)."""
    46	    H, W = im.shape[:2]
    47	    if box:
    48	        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    49	        cs = max(cs, int(1.4 * max(box[2] - box[0], box[3] - box[1])))
    50	    else:                                   # 점이 여럿이면 점들의 가운데
    51	        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) // 2
    52	        cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) // 2
    53	    if pts:
    54	        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    55	        cs = max(cs, int(1.4 * max(max(xs) - min(xs), max(ys) - min(ys))))
    56	    cs = int(min(cs, W, H))
    57	    x0 = max(0, min(W - cs, cx - cs // 2))
    58	    y0 = max(0, min(H - cs, cy - cs // 2))
    59	    crop = im[y0:y0 + cs, x0:x0 + cs]
    60	    PRED.set_image(crop)
    61	    kw = {"multimask_output": not (box or len(pts) > 1)}
    62	    if pts:
    63	        kw["points"] = [[p[0] - x0, p[1] - y0] for p in pts]; kw["labels"] = [int(p[2]) for p in pts]
    64	    if box:
    65	        kw["bboxes"] = [[box[0] - x0, box[1] - y0, box[2] - x0, box[3] - y0]]
    66	    r = PRED(**kw)[0]
    67	    if r.masks is None:
    68	        return [], x0, y0, cs
    69	    masks = r.masks.data.cpu().numpy() > 0
    70	    scores = r.boxes.conf.cpu().numpy()
    71	    first_pos = next(((p[0] - x0, p[1] - y0) for p in pts if int(p[2]) == 1), None)
    72	    out = []
    73	    for j in np.argsort(-scores):
    74	        m = masks[j]
    75	        n = int(m.sum())
    76	        if n < 9 or (n > 0.4 * m.size and not box):
    77	            continue
    78	        if first_pos and not m[first_pos[1], first_pos[0]]:
    79	            continue
    80	        out.append((m, float(scores[j])))
    81	    return out, x0, y0, cs
    82	
    83	
    84	@app.route("/health")
    85	def health():
    86	    return jsonify({"ok": True})
    87	
    88	
    89	@app.route("/sam", methods=["POST"])
    90	def sam():
    91	    d = request.get_json(force=True, silent=True) or {}
    92	    try:
    93	        cs = max(128, min(2048, int(d.get("crop") or 384)))
    94	        if "points" in d:
    95	            pts = [[int(p[0]), int(p[1]), 1 if int(p[2]) else 0] for p in d["points"]][:20]
    96	        elif "x" in d:
    97	            pts = [[int(d["x"]), int(d["y"]), 1]]
    98	        else:
    99	            pts = []
   100	        box = [int(v) for v in d["box"]][:4] if d.get("box") else None
   101	        if box:
   102	            box = [min(box[0], box[2]), min(box[1], box[3]), max(box[0], box[2]), max(box[1], box[3])]
   103	        if not pts and not box:
   104	            raise ValueError("점이나 네모가 필요합니다")
   105	        with LOCK:
   106	            t = time.time()
   107	            im = _image(d["img"])
   108	            cands, x0, y0, cs = _run(im, pts, box, cs)
   109	            # 1등이 칸 가장자리에 닿으면 열매가 칸보다 크다 → 칸을 키워 다시 (네모가 있으면 칸은 이미 넉넉)
   110	            if cands and not box:
   111	                m = cands[0][0]
   112	                if (m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()) and cs < min(im.shape[:2]):
   113	                    cands, x0, y0, cs = _run(im, pts, box, cs * 2)
   114	            dt = time.time() - t
   115	    except (KeyError, ValueError, TypeError, IndexError) as e:
   116	        return jsonify({"ok": False, "error": str(e)}), 400
   117	    except Exception as e:                  # GPU 메모리 부족 등 — 화면이 이유를 읽을 수 있게 늘 JSON 으로
   118	        return jsonify({"ok": False, "error": "도우미 오류: %s" % e}), 500
   119	    res = []
   120	    for m, sc in cands:
   121	        ys, xs = np.nonzero(m)
   122	        a, b, c, e = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
   123	        res.append({"x0": x0 + a, "y0": y0 + b, "w": c - a, "h": e - b, "score": round(sc, 3),
   124	                    "png": _png(m[b:e, a:c])})
   125	    return jsonify({"ok": True, "cands": res, "crop": cs, "sec": round(dt, 3)})
   126	
   127	
   128	if __name__ == "__main__":
   129	    app.run(host="127.0.0.1", port=int(os.environ.get("SAM_PORT", "5112")), threaded=True)
