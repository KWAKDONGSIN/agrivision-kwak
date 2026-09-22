/* list — 사진 목록 · 사진 열기 · 진행 현황
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 87-87·90-113·115-273·279-296·403-501·506-551·553-592·1202-1205·1261-1378·1380-1419·2540-2580줄 · ui.js 761-833줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   과일·사진 목록과 카드, 사진 한 장 열기(openItem), 거의 같은 사진 묶음, 빠른 필터, 그리고 «현황»(대시보드) 화면.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, who = UI.who, errMsg = UI.errMsg, escapeHtml = UI.escapeHtml, FRUIT_KO = UI.FRUIT_KO, statusKo = UI.statusKo, COL = UI.COL, showView = UI.showView, fitView = UI.fitView, zoomToNote = UI.zoomToNote, resizeCanvas = UI.resizeCanvas, fetchMaskBits = UI.fetchMaskBits, fetchMaskRaw = UI.fetchMaskRaw, makeLayer = UI.makeLayer, paintLayerFull = UI.paintLayerFull, paintGtLayer = UI.paintGtLayer, paintDiffFull = UI.paintDiffFull, setTool = UI.setTool, confirmLeave = UI.confirmLeave, loadBrush = UI.loadBrush, loadBoxes = UI.loadBoxes, loadInstances = UI.loadInstances, renderErrRows = UI.renderErrRows, ensureErrRows = UI.ensureErrRows, noteBoxes = UI.noteBoxes, renderCntChip = UI.renderCntChip, FLAG_KO = UI.FLAG_KO;
const api = API.get, post = API.post;

/* ------------------------------------------------------------ 과일 목록 */

async function loadFruits() {
  const j = await api("/api/fruits");
  if (!j || !j.fruits) { flash("과일 목록을 불러오지 못했습니다(새로고침 해 보세요)", true); return; }
  const sel = $("#fruit");
  sel.innerHTML = "";
  j.fruits.forEach((f) => {
    const o = document.createElement("option");
    o.value = f.fruit;
    o.textContent = `${FRUIT_KO[f.fruit] || f.fruit} (${f.n_images}장)`;
    sel.appendChild(o);
  });
  S.fruit = localStorage.getItem("fruit") || j.fruits[0].fruit;
  if (!j.fruits.some((f) => f.fruit === S.fruit)) S.fruit = j.fruits[0].fruit;
  sel.value = S.fruit;
  loadBrush();                 // 0918 사이클4: 이 과일에서 마지막으로 쓰던 붓 크기로(브라우저를 새로 열어도)
  loadList();
}

function applyFeatures(f) {
  S.features = f || {};
  $$(".feat-prop").forEach((e) => e.classList.toggle("hidden", !(f.proposals || f.scores)));
  $$(".feat-dup").forEach((e) => e.classList.toggle("hidden", !f.duplicates));
  $$(".feat-insp").forEach((e) => e.classList.toggle("hidden", !f.inspection));
}

/* ------------------------------------------------------------ 사진 목록 */
async function loadList(keepPage) {
  if (!keepPage) S.page = 1;
  if (["insterr", "teamreview"].includes($("#f-sort").value)) { await loadListInstErr(keepPage); return; }
  await ensureErrRows();
  const p = new URLSearchParams({
    fruit: S.fruit, status: $("#f-status").value, sort: $("#f-sort").value,
    q: $("#f-q").value, page: S.page, page_size: 120
  });
  if ($("#f-dup").checked) p.set("dup", "1");
  if ($("#f-suspect").checked) p.set("suspect", "1");
  if ($("#f-prop").checked) p.set("proposal", "1");
  if (S.flag) p.set("flag", S.flag);          // 의심 «종류» 로 거르기 (ui.js 의 종류별 단추)
  if (S.confFilter) p.set("confirmed", S.confFilter);   // «내 큐» = 미확정만 (0918 사이클2)
  if (S.confBy) p.set("by", S.confBy);
  // 0918 사이클4 결정 1: 큐·미확정 거르기는 **지금 하는 작업**의 확정을 본다
  // (① 마스크 / ② 상자 / ③ 번호). 서버가 모르면 무시하므로 옛 서버에서도 안전하다.
  p.set("mode", S.numMode ? "instances" : S.boxMode ? "boxes" : "mask");
  $("#grid").innerHTML = '<div class="muted">불러오는 중…</div>';
  const j = await api("/api/list?" + p.toString());
  if (!j || !j.items) {                       // 로그인이 풀렸거나 서버 오류 — 화면을 깨뜨리지 않는다
    $("#grid").innerHTML = '<div class="muted">목록을 불러오지 못했습니다. 새로고침 해 보세요.</div>';
    if (j) flash(errMsg(j, "목록을 불러오지 못했습니다"), true);
    return;
  }
  applyFeatures(j.features);
  S.items = j.items; S.pages = j.pages; S.listTotal = j.total;
  S.flagCounts = j.flag_counts || {};        // ui.js 가 «종류별» 단추를 만들 때 쓴다
  $("#listinfo").textContent = `조건에 맞는 사진 ${j.total}장`;
  $("#pageinfo").textContent = `${j.page} / ${j.pages} 쪽 (한 쪽에 ${j.page_size}장)`;
  $("#prevpage").disabled = j.page <= 1;
  $("#nextpage").disabled = j.page >= j.pages;
  renderCounts();
  renderGrid();
}

async function renderCounts() {
  const j = await api("/api/fruits");
  if (!j || !j.fruits) return;                // 로그인이 풀렸으면 /login 으로 넘어가는 중
  const f = j.fruits.find((x) => x.fruit === S.fruit);
  if (!f) return;
  S.progressFruit = f;
  if (UI.renderEasyProgress) UI.renderEasyProgress();
  const ko = { unreviewed: "아직 안 봄", ok: "원본 OK", fixed: "수정함", flag: "문제 있음", exclude: "제외" };
  // 0917 UI: 숫자만 보면 «얼마나 남았나» 가 안 와닿아서 막대를 한 줄 붙인다.
  const pct = f.n_images ? (f.reviewed / f.n_images * 100) : 0;
  // 0918 사이클2: 진행률의 기준을 «사람이 확정한 장수» 로 바꾼다(방향 문서 §3-1).
  // AI 제안 다섯 칸은 그대로 두되 «AI 제안» 이라고 이름을 붙인다 — 그것이 진행률이 아니기 때문.
  const nc = f.n_confirmed || 0;
  const cpct = f.n_images ? (nc / f.n_images * 100) : 0;
  const me = who();
  const mine = (f.today_by_person || {})[me] || 0;
  $("#counts").innerHTML = `<span class="pill conf" title="사람이 «맞다» 고 확정한 장수입니다. 이것이 진행률입니다.">`
    + `✔ 확정 ${nc} / 전체 ${f.n_images}</span>`
    + `<span class="pill" title="오늘 «${escapeHtml(me)}» 이름으로 확정한 장수입니다.">오늘 나 ${mine}장</span>`
    + `<span class="prog" title="사람이 확정한 사진의 비율">`
    + `<span class="barbg"><span class="barfill" style="width:${cpct.toFixed(1)}%"></span></span>`
    + `${cpct.toFixed(1)}% 확정 · ${f.n_images - nc}장 남음</span>`
    // 0918 사이클4 결정 1: 확정은 작업마다 따로다 — 진행률 줄에 종류별 장수를 나란히 둔다.
    // (서버가 옛 판이면 이 칸이 없으므로 아무것도 덧붙이지 않는다.)
    + (f.n_confirmed_boxes === undefined ? "" :
        `<span class="pill conf" title="사람이 «상자» 를 확정한 장수입니다(칠한 영역 확정과 따로 셉니다).">`
        + `▭ 상자 ${f.n_confirmed_boxes}</span>`
        + (f.has_instances === false ? "" :
           `<span class="pill conf" title="사람이 «열매 번호» 를 확정한 장수입니다(칠한 영역 확정과 따로 셉니다).">`
           + `＃ 번호 ${f.n_confirmed_instances}</span>`))
    + `<span class="vsep"></span>`
    + Object.keys(ko).map((k) => `<span class="pill ${k}" title="AI 제안(초벌)입니다 — 사람 확정과 다릅니다">${ko[k]} ${f.counts[k]}</span>`).join("")
    + `<span class="pill" title="AI 제안이 채워진 장수(진행률이 아닙니다)">AI 제안 ${f.reviewed} / ${f.n_images}</span>`;
}

/* ═══ 0918 사이클5(총괄) ② — 카드 한 장의 «얼굴»(테두리 색 + 딱지)을 함수로 떼어낸다 ═══
   전에는 이 계산이 renderGrid 안에만 있어서, 확정한 뒤 목록으로 돌아오면 목록을 **다시 읽기
   전까지** 카드가 옛 그림이었다(사이클4 2차 §4-4 4번 · 3차가 사이클5 로 넘긴 것).
   같은 계산을 refreshCard(stem) 도 쓸 수 있게 빼냈다 — **글자·딱지 개수·규칙은 한 글자도
   바뀌지 않았다**(renderGrid 는 이 함수를 부를 뿐이다). */
function cardFace(it) {
  /* 0918 사이클4 **2차 검수**(실측 s1_flow 가-8·나-6·다-5): 카드가 «사람이 확정한 것» 을
     말하지 않았다. ① 딱지가 **마스크 확정만** 봐서 ② 상자·③ 번호를 방금 확정한 장이 «미확정»
     으로 보였고, ② 테두리 색·판정 딱지가 AI 제안이라 «4 제외» 로 확정해도 카드에는 AI 가 적은
     «문제 있음» 이 그대로 있었다(방향 문서 §3-1 «사람이 확정하면 그것이 위에 선다» 에 어긋난다).
     고친 규칙: **지금 고른 작업의** 확정이 있으면 그 판정으로 테두리·글자를 쓰고 AI 제안은
     풍선말로 내린다. 확정이 없으면 예전과 한 글자도 다르지 않다. 딱지 **개수는 그대로**다. */
  /* ⚠ ui.js 는 통째로 IIFE(즉시 실행 함수) 안이라 `curTask()` 가 **전역이 아니다**
     (실측 s5_card 카드-1: `typeof curTask` = undefined). 그래서 같은 뜻을 이 파일의
     상태(S.numMode·S.boxMode — ui.js 의 curTask 와 **같은 두 칸**)로 직접 센다. */
  const ct = S.numMode ? "num" : S.boxMode ? "box" : "mask";
  const ck = ct === "box" ? it.confirmed_boxes : ct === "num" ? it.confirmed_instances : it.confirmed;
  const shown = ck || it.status;
  const tags = [];
  // 상태는 테두리 색 + 흐림으로만 보였다(제외 314장이 깔린 지금 «이게 왜 흐리지» 가 먼저 온다).
  // 글자 딱지를 하나 붙인다 — 테두리 색과 같은 색이라 범례를 두 번 만들지 않는다(0917 사이클3 ④).
  // 0918 사이클2: 카드가 «AI 제안» 인지 «사람이 확정» 한 것인지 한눈에 보이게 딱지를 먼저 붙인다
  const CTKO = { mask: "칠한 영역", box: "상자", num: "번호" };
  const aiWhy = "AI 제안: " + statusKo(it.status)
    + (ct !== "mask" && it.confirmed ? " · 칠한 영역 확정: " + statusKo(it.confirmed) : "");
  tags.push(ck
    ? '<span class="tag conf" title="' + escapeHtml("사람이 " + CTKO[ct] + " 를 확정했습니다: " + statusKo(ck)
        + (ct === "mask" && it.confirmed_by ? " · " + it.confirmed_by : "") + " · " + aiWhy) + '">✔ 확정</span>'
    : '<span class="tag unconf" title="' + escapeHtml("아직 아무도 이 사진의 " + CTKO[ct]
        + " 를 «맞다» 고 확정하지 않았습니다. " + aiWhy) + '">미확정</span>');
  if (shown && shown !== "unreviewed")
    tags.push('<span class="tag st ' + shown + '" title="'
      + escapeHtml(ck ? "사람이 확정한 판정입니다(" + aiWhy + ")" : "AI 제안입니다 — 사람 확정이 아닙니다")
      + '">' + statusKo(shown) + "</span>");
  if (it.n_inst !== null && it.n_inst !== undefined) tags.push('<span class="tag ninst" title="이 사진의 열매 번호 개수(카운팅)">' + it.n_inst + "개</span>");
  if (it.dup_group !== null && it.dup_group !== undefined) tags.push('<span class="tag dup">중복#' + it.dup_group + "</span>");
  if (it.suspect) tags.push('<span class="tag sus">의심</span>');
  if (it.dice !== null && it.dice !== undefined) tags.push('<span class="tag dice">Dice ' + it.dice.toFixed(2) + "</span>");
  if (it.has_fixed) tags.push('<span class="tag">수정본</span>');
  const nerr = ((S.errBy && S.errBy[it.stem]) || []).length;
  if (nerr) tags.push('<span class="tag insterr">번호오류 ' + nerr + "</span>");
  return { cls: "card s-" + shown, tags: tags.join("") };
}

function renderGrid() {
  const g = $("#grid");
  g.innerHTML = "";
  if (!S.items.length) { g.innerHTML = '<div class="muted">조건에 맞는 사진이 없습니다.</div>'; return; }
  const frag = document.createDocumentFragment();
  S.items.forEach((it, i) => {
    const d = document.createElement("div");
    const f = cardFace(it);
    d.className = f.cls;
    d.innerHTML = `<img data-src="/thumb?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(it.stem)}" alt="">
      <div class="cap">${escapeHtml(it.stem)}<div class="tags">${f.tags}</div></div>`;
    d.onclick = () => openItem(i);
    frag.appendChild(d);
  });
  g.appendChild(frag);
  lazyImages(g);
}

/* 0918 사이클5(총괄) ② — 확정·저장·되돌리기 직후 **그 카드 하나만** 다시 그린다.
   목록 전체를 다시 읽지 않는다(2,400장 목록에서 스크롤이 맨 위로 튀기 때문 — 2차가 (나)를
   반대한 이유다). 사진(<img>)은 손대지 않아 썸네일이 다시 내려오지 않고, 테두리 색과 딱지만
   바뀐다. 카드를 못 찾으면(목록을 아직 안 그렸거나 다른 쪽) 조용히 아무 일도 하지 않는다. */
function cardEl(stem) {
  const g = $("#grid");
  if (!g) return null;
  const cards = g.querySelectorAll(".card");
  const isIt = (e) => {
    const cap = e && e.querySelector(".cap");
    return !!(cap && cap.firstChild && cap.firstChild.textContent.trim() === stem);
  };
  const i = S.items.findIndex((x) => x.stem === stem);
  if (i >= 0 && isIt(cards[i])) return cards[i];       // 거의 늘 이 길(목록 순서 = S.items 순서)
  return Array.prototype.find.call(cards, isIt) || null;
}

function refreshCard(stem) {
  const it = S.items.find((x) => x.stem === stem);
  const d = it && cardEl(stem);
  if (!d) return false;
  const f = cardFace(it);
  d.className = f.cls;
  const tg = d.querySelector(".tags");
  if (!tg) return false;
  tg.innerHTML = f.tags;
  return true;
}

/* 썸네일은 화면에 보일 때만 불러온다(2,500장짜리 포도에서 중요) */
let _thumbIO = null;
function lazyImages(root) {
  if (_thumbIO) _thumbIO.disconnect();      // 지난 목록의 관찰자를 정리(오래 켜 두면 쌓인다)
  const io = new IntersectionObserver((ents) => {
    ents.forEach((e) => {
      if (e.isIntersecting) { const im = e.target; im.src = im.dataset.src; io.unobserve(im); }
    });
  }, { rootMargin: "300px" });
  _thumbIO = io;
  root.querySelectorAll("img[data-src]").forEach((im) => io.observe(im));
}

$("#fruit").onchange = () => { if (!confirmLeave()) { $("#fruit").value = S.fruit; return; } showView("list"); S.stem = null; S.item = null; S.img = null; S.ed = null; S.inst = null; S.boxes = []; S.edDirty = false; S.bDirty = false; S.numDirty = false; S.fruit = $("#fruit").value; localStorage.setItem("fruit", S.fruit); loadBrush(); loadList(); };
["#f-status", "#f-sort", "#f-dup", "#f-suspect", "#f-prop"].forEach((s) => $(s).onchange = () => loadList());
$("#f-q").onkeydown = (e) => { if (e.key === "Enter") loadList(); };
$("#prevpage").onclick = () => { if (S.page > 1) { S.page--; loadList(true); } };
$("#nextpage").onclick = () => { if (S.page < S.pages) { S.page++; loadList(true); } };

/* ---------------------------------------------------------- 사진 열기 */
async function openItem(i, force) {
  if (i < 0 || i >= S.items.length) return;
  // 같은 카드를 다시 눌러도 서버에서 다시 읽어 오므로 수정이 사라진다 → 그때도 물어본다
  if (!force && !confirmLeave()) return;
  S.idx = i;
  const it = S.items[i];
  showView("edit");
  $("#loading").classList.remove("hidden");
  S.busy = true;
  try {
    const meta = await api(`/api/item?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(it.stem)}`);
    if (!meta || !meta.stem) { flash(errMsg(meta, "사진 정보를 불러오지 못했습니다"), true); return; }
    S.savedAt = 0; S.item = meta; S.stem = meta.stem; S.W = meta.width; S.H = meta.height;
    $("#stemname").textContent = meta.stem;
    const bits = [];
    bits.push(`${meta.width}×${meta.height}`);
    bits.push("상태: " + statusKo(meta.status));
    if (meta.by) bits.push("검수: " + meta.by + " " + (meta.at || ""));
    if (meta.scores && meta.scores.dice_vs_gt != null) {
      bits.push(`AI Dice ${meta.scores.dice_vs_gt.toFixed(3)}`);
      if (meta.scores.added_frac != null) bits.push(`AI추가 ${(meta.scores.added_frac * 100).toFixed(2)}%`);
      if (meta.scores.missed_frac != null) bits.push(`AI누락 ${(meta.scores.missed_frac * 100).toFixed(2)}%`);
    }
    if (meta.inspection && meta.inspection.suspect_flags) bits.push("의심: " + meta.inspection.suspect_flags);
    S.metaBits = bits;
    $("#meta").innerHTML = bits.map(escapeHtml).join(" · ");
    $("#note").value = meta.note || "";
    // 0918 UI사이클4 N12: 칸이 좁아 «사람 확인 필요: 라벨 안 된 사과 후.» 까지만 보였다.
    // 0918 UI사이클5 N-J: 앞 사이클이 여기에 «칸은 CSS 로 넓혔고» 라고 적었지만 실제로는
    // **넓히지 않았다**(넓히면 판정 줄이 두 겹이 되어 캔버스가 줄었다 — style.css 의 N12 주석).
    // 칸 너비는 그대로 두고, 잘리는 긴 메모는 풍선말로 통째로 읽게 한다(좌표 숫자 포함).
    $("#note").title = meta.note ? "이 사진의 메모 전문:\n" + meta.note : "이 사진에 대해 남길 말이 있으면 적습니다. 판정·저장과 함께 기록됩니다.";
    S.noteBoxes = noteBoxes(meta.note);      // 메모의 «후보 좌표» → 노란 점선 상자(ab사이클2 P4)
    S.noteZoomAt = -1;                       // «후보 자리로 확대» 는 새 사진에서 첫 후보부터(사이클4 N7)
    $("#dupinfo").textContent = meta.dup_members && meta.dup_members.length
      ? `중복 그룹 #${meta.dup_group}: ` + meta.dup_members.join(", ") : "";
    renderDupStrip(meta);
    $("#btn-ai").disabled = !meta.has_proposal;
    $("#fromai").disabled = !meta.has_proposal;

    const q = `fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(S.stem)}`;
    const imgP = new Promise((res, rej) => {
      const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = "/img?" + q;
    });
    const [img, gtRaw, ai, fx, orig] = await Promise.all([
      imgP,
      fetchMaskRaw("/mask?" + q + "&layer=gt_raw", S.W, S.H),
      meta.has_proposal ? fetchMaskBits("/mask?" + q + "&layer=ai", S.W, S.H) : Promise.resolve(null),
      meta.has_fixed ? fetchMaskBits("/mask?" + q + "&layer=fixed", S.W, S.H) : Promise.resolve(null),
      // 0922: 검수 전 진짜 원본(복숭아·포도만 — 서버가 has_orig 로 알려 준다). 옛 서버는 칸이 없어 null.
      meta.has_orig ? fetchMaskBits("/mask?" + q + "&layer=orig", S.W, S.H) : Promise.resolve(null)
    ]);
    S.img = img;
    S.gtRaw = gtRaw || new Uint8Array(S.W * S.H);
    // 값이 1~254 사이면 «인스턴스 라벨 마스크»(사과). 0/255 만 있으면 보통 이진 마스크
    let nLab = 0, seen = new Uint8Array(256);
    for (let i = 0; i < S.gtRaw.length; i++) { const v = S.gtRaw[i]; if (v && !seen[v]) { seen[v] = 1; nLab++; } }
    S.gtIsInstance = nLab > 1 || (nLab === 1 && !seen[255]);
    S.gtNLabels = nLab;
    S.gt = new Uint8Array(S.gtRaw.length);
    for (let i = 0; i < S.gtRaw.length; i++) S.gt[i] = S.gtRaw[i] ? 1 : 0;
    S.ai = ai;
    S.orig = orig || null;
    S.ed = fx ? fx : S.gt.slice();       // 수정본이 없으면 원본 GT 에서 시작
    S.undo = []; S.redo = []; S.edDirty = false;
    S.lay = {};
    makeLayer("gt", S.W, S.H); makeLayer("ed", S.W, S.H); makeLayer("diff", S.W, S.H);
    $("#row-inst").classList.toggle("hidden", !S.gtIsInstance);
    paintGtLayer();
    paintLayerFull("ed", S.ed, COL.ed);
    if (S.ai) { makeLayer("ai", S.W, S.H); paintLayerFull("ai", S.ai, COL.ai); }
    if (S.orig) { makeLayer("orig", S.W, S.H); paintLayerFull("orig", S.orig, COL.orig); }
    if ($("#row-orig")) $("#row-orig").style.display = S.orig ? "" : "none";   // 0922: 있을 때만 칸을 보인다
    paintDiffFull();
    $("#l-ai").disabled = !S.ai;
    // AI 제안이 없으면 «차이 보기» 는 의미가 없다(원본 전체가 삭제 후보로 보임)
    $("#l-diff").disabled = !S.ai;
    if (!S.ai) $("#l-diff").checked = false;
    if (S.gtIsInstance) {
      S.metaBits.push(`원본 라벨 = 열매 번호 ${S.gtNLabels}개(알마다 번호)`);
      $("#meta").innerHTML = S.metaBits.map(escapeHtml).join(" · ");
    }
    fitView();
    /* ─── 0918 사이클4 결정 2-②③ — 사진을 열 때 두 가지를 알아서 맞춘다 ───
       ② «할 일» 자리(노란 점선 = 라벨 빠진 열매 후보)가 있으면 **그 자리로 자동 확대**한다.
          1080×1920 사진을 240px 폭으로 보여 주므로 후보가 30×35화소라 사람이 찾지 못했다
          (0918 UI사이클4 N7 이 🔍 단추를 만들었지만 누르는 사람이 없었다). 없으면 예전대로 맞춤.
       ③ 기본 도구 = «자동채움»(스마트 채우기 F). 붓으로 알 하나를 칠하는 데 수십 번 끄는데,
          AI 제안이 있으면 한 번 눌러 덩어리째 가져오는 것이 제일 빠르다. AI 제안이 없는
          사진에서는 자동채움이 할 일이 없으므로 예전대로 «붓». 토글은 두지 않는다(yagni). */
    if (!S.numMode && !S.boxMode) setTool(S.ai ? "smartadd" : "brush");
    if (S.noteBoxes && S.noteBoxes.length) zoomToNote(0);
    const pBox = loadBoxes();            // 0921 S5: 기다리지는 않는다(전과 같다) — 약속만 붙잡아 둔다
    const pInst = loadInstances();
    renderErrRows();
    if (UI.loadTeamSuspects) UI.loadTeamSuspects();
    if (UI.renderEasyProgress) UI.renderEasyProgress();
    /* 🔴 2026-09-21 S5 — 저장 전 작업의 임시 백업이 있으면 «되돌릴까요» 를 묻는다.
       상자·번호가 **다 읽힌 뒤**에 물어야 한다 — 먼저 되돌리면 뒤늦게 끝난 위 두 함수가
       서버 값으로 덮어쓴다. 그래서 그 둘의 약속을 넘긴다(여기서 기다리지 않으므로
       «불러오는 중» 표시가 늦게 걷히지 않는다). 백업이 없으면 곧바로 돌아온다. */
    if (UI.backupOffer) UI.backupOffer(Promise.all([pBox, pInst]));
  } catch (e) {
    flash("불러오기 실패: " + e, true);
  } finally {
    S.busy = false;
    $("#loading").classList.add("hidden");
    S.dirty = true;
  }
}

/* ═══════════ 거의 같은 사진 묶음 — 썸네일 줄 + «이 묶음 한 번에» (0917 사이클3 ①) ═══════════
   녹취 «거의 똑같은 이미지… 걸러내고» / «일일이 우리가 할 수는 없으니까».
   지금까지는 «묶음 #25 (4장)» 이라는 글자뿐이라, 나머지 세 장을 보려면 파일 이름을 검색해야 했다. */
function renderDupStrip(m) {
  const box = $("#dupbox");
  if (!box) return;
  S.dupDone = null;                       // 방금 이 단추로 제외한 목록(되돌리기 대상)
  S.dupRep = m && m.dup_rep;
  S.dupMem = {};
  const mem = (m && m.dup_members) || [];
  (m && m.dup_member_status || []).forEach((st, i) => { S.dupMem[mem[i]] = st; });
  box.style.display = mem.length ? "" : "none";
  $("#dupundo").classList.add("hidden");
  $("#dupmsg").textContent = "";
  if (!mem.length) return;
  $("#dupttl").textContent = `#${m.dup_group} · ${mem.length}장`;
  drawDupStrip();
}

function drawDupStrip() {
  const mem = Object.keys(S.dupMem);
  // «이 사진에서 할 일» 줄(ui.js)은 /api/item 의 값을 읽는다 — 묶음을 제외한 뒤 그 줄이
  // 옛말을 하지 않게 같은 값을 여기서도 맞춰 둔다(ab사이클2 P3 의 «대표» 문구가 바로 바뀌게).
  if (S.item && S.item.dup_members) S.item.dup_member_status = S.item.dup_members.map((s) => S.dupMem[s]);
  $("#dupstrip").innerHTML = mem.map((s) => {
    const st = S.dupMem[s];
    const me = s === S.stem, rep = s === S.dupRep;
    return `<a class="dupt${me ? " me" : ""}${st === "exclude" ? " gone" : ""}" data-stem="${escapeHtml(s)}"
       title="${escapeHtml(s)} — ${statusKo(st)}${rep ? " (대표)" : ""}\n누르면 이 사진을 엽니다">
      <img src="/thumb?fruit=${encodeURIComponent(S.fruit)}&stem=${encodeURIComponent(s)}" alt="">
      <span class="dc">${rep ? "남김" : statusKo(st)}${me ? " ·지금" : ""}</span></a>`;
  }).join("");
  $$("#dupstrip .dupt").forEach((a) => a.onclick = () => openStem(a.dataset.stem));
}

/* 목록에 없는 사진도 열 수 있게 — **지금 보던 사진 바로 뒤에** 끼워서 연다.
   0918 UI사이클4 N6: 전에는 목록 «끝» 에 붙였다. 그러면 그 사진에서 `.`(다음)이 «마지막 사진입니다»
   로 아무 데도 안 가고, `,`(이전)은 목록의 **맨 앞** 사진으로 뛰었다(실측). 바로 뒤에 끼우면
   `,` 는 보던 사진으로, `.` 는 원래의 다음 사진으로 간다. */
function openStem(stem) {
  const i = S.items.findIndex((x) => x.stem === stem);
  if (i >= 0) return openItem(i);
  const at = Math.min(Math.max(S.idx + 1, 0), S.items.length);
  S.items.splice(at, 0, { stem: stem, status: S.dupMem[stem] || "unreviewed" });
  openItem(at);
}

if ($("#dupexc")) $("#dupexc").onclick = async () => {
  if (!S.stem || !S.dupRep) return;
  const others = Object.keys(S.dupMem).filter((s) => s !== S.dupRep);
  const todo = others.filter((s) => (S.dupMem[s] || "unreviewed") === "unreviewed");
  const keep = others.length - todo.length;
  if (!todo.length) return flash("이 묶음에는 새로 제외할 사진이 없습니다(대표 말고는 이미 다 판정됨)", true);
  if (!confirm(`이 묶음 ${others.length + 1}장 중 대표 «${S.dupRep}» 한 장만 남기고 ${todo.length}장을 «제외» 로 표시합니다.`
    + (keep ? `\n(${keep}장은 사람이 이미 판정해서 그대로 둡니다)` : "")
    + "\n원본 파일은 지우지 않습니다. 진행할까요?")) return;
  const j = await post("/api/exclude_group", { fruit: S.fruit, stem: S.stem, by: who() });
  if (!j || !j.ok) return flash(errMsg(j, "묶음 제외 실패"), true);
  S.dupDone = j.changed || [];
  S.dupDone.forEach((s) => { S.dupMem[s] = "exclude"; });
  if (S.dupMem[S.stem] === "exclude" && S.item) { S.item.status = "exclude"; if (S.items[S.idx]) S.items[S.idx].status = "exclude"; }
  $("#dupundo").classList.toggle("hidden", !S.dupDone.length);
  $("#dupmsg").textContent = `${S.dupDone.length}장을 제외했습니다`
    + ((j.skipped || []).length ? ` · 건너뜀 ${j.skipped.length}장(이미 판정됨·데이터셋 밖)` : "");
  flash(`이 묶음에서 ${S.dupDone.length}장을 제외했습니다`);
  drawDupStrip();
};

if ($("#dupundo")) $("#dupundo").onclick = async () => {
  if (!S.dupDone || !S.dupDone.length) return;
  const j = await post("/api/undo_exclude_group", { fruit: S.fruit, stems: S.dupDone, by: who() });
  if (!j || !j.ok) return flash(errMsg(j, "되돌리기 실패"), true);
  (j.changed || []).forEach((s) => { S.dupMem[s] = "unreviewed"; });
  if (S.dupMem[S.stem] === "unreviewed" && S.item) { S.item.status = "unreviewed"; if (S.items[S.idx]) S.items[S.idx].status = "unreviewed"; }
  // 0918 UI사이클3 2차: 한 장도 안 되돌아왔는데 «되돌렸습니다» 라고 말하고 단추까지 숨겼다.
  // (되돌리기는 «제외할 때 적힌 이름» 과 같을 때만 된다 — 이름을 바꿔 누른 사람은 지워진 줄 안다.)
  const nBack = (j.changed || []).length;
  if (nBack) {
    S.dupDone = null;
    $("#dupundo").classList.add("hidden");
  }
  $("#dupmsg").textContent = `${nBack}장을 되돌렸습니다`
    + ((j.kept || []).length ? ` · ${j.kept.length}장은 다른 사람이 넣은 제외라 그대로 둡니다` : "");
  flash(nBack ? "방금 제외한 것을 되돌렸습니다"
    : `되돌리지 못했습니다 — 제외할 때 적혀 있던 이름으로만 되돌아옵니다 (지금 이름: ${who()})`, !nBack);
  drawDupStrip();
};

function nextItem(force) { if (S.idx + 1 < S.items.length) openItem(S.idx + 1, force); else flash("이 쪽의 마지막 사진입니다 — 목록에서 다음 쪽을 여세요"); }
function prevItem(force) { if (S.idx > 0) openItem(S.idx - 1, force); else flash("이 쪽의 첫 사진입니다"); }
$("#next").onclick = () => nextItem();      // 이벤트 객체가 force 로 들어가지 않게 감싼다
$("#prev").onclick = () => prevItem();

/* ------------------------------------------------------------- 대시보드 */
async function loadDash() {
  const j = await api("/api/stats");
  if (!j || !j.fruits) {                      // 로그인이 풀렸으면 /login 으로 넘어가는 중
    $("#dash").innerHTML = '<p class="muted">진행 현황을 불러오지 못했습니다. 새로고침 해 보세요.</p>';
    return;
  }
  $("#dashtime").textContent = j.generated;
  // 🔴 2026-09-21 S2 검증 중 발견(별건). 여기에 `S.progressFruit = f;` 와
  //   `if (UI.renderEasyProgress) UI.renderEasyProgress();` 두 줄이 있었다. 09-20 «쉬움 모드
  //   진행 막대» 를 넣을 때 위 `renderCounts()` 의 두 줄이 그대로 새어 들어온 것인데, 이 함수에는
  //   `f` 라는 이름이 없다 → `ReferenceError: f is not defined` 로 **현황 탭이 통째로 안 그려졌다**
  //   (실측: #dash 길이 0 · 콘솔 `reject: ReferenceError: f is not defined`).
  //   `S.progressFruit` 는 목록 화면의 `renderCounts()` 가 이미 올바르게 채운다 — 두 줄을 지운다.
  const ko = { unreviewed: "아직 안 봄", ok: "원본 OK", fixed: "수정함", flag: "문제 있음", exclude: "제외" };
  let h = "<h3>과일별 진행</h3><table class='d'><tr><th class='l'>과일</th><th>전체</th>"
    + Object.values(ko).map((k) => `<th>${k}</th>`).join("") + "<th>수정본 파일</th><th class='l'>진행률</th></tr>";
  j.fruits.forEach((f) => {
    const done = f.n_images - f.counts.unreviewed;
    const pct = f.n_images ? (done / f.n_images * 100) : 0;
    h += `<tr><td class='l'>${FRUIT_KO[f.fruit] || f.fruit}</td><td>${f.n_images}</td>`
      + Object.keys(ko).map((k) => `<td>${f.counts[k]}</td>`).join("")
      + `<td>${f.n_fixed}</td><td class='l'><span class="barbg"><span class="barfill" style="width:${pct.toFixed(1)}%"></span></span> ${pct.toFixed(1)}%</td></tr>`;
  });
  h += "</table>";

  // 열매 개수(카운팅) — /api/instance_stats 는 캐시만 읽어 바로 답한다(0917 사이클3 ③)
  h += "<h3>열매 개수(카운팅)</h3><div id='iststat'><span class='muted'>불러오는 중…</span></div>";

  // 근접 중복 일괄 제외
  h += "<h3>근접 중복(거의 같은 사진) 정리</h3>";
  const dupF = j.fruits.filter((f) => f.n_dup_groups > 0);
  if (!dupF.length) {
    h += "<p class='muted'>아직 duplicates.json 이 없습니다. (검수 담당이 만들면 여기에 버튼이 생깁니다)</p>";
  } else {
    h += "<table class='d'><tr><th class='l'>과일</th><th>중복 그룹</th><th>대표 외 장수</th><th>데이터셋 밖</th><th class='l'>작업</th></tr>";
    dupF.forEach((f) => {
      h += `<tr><td class='l'>${FRUIT_KO[f.fruit] || f.fruit}</td><td>${f.n_dup_groups}</td><td>${f.n_dup_extra}</td><td>${f.outside_dataset || 0}</td>
        <td class='l'>
          <button class='dupapply' data-f='${f.fruit}'>중복 그룹 일괄 제외 적용</button>
          <button class='dupundo' data-f='${f.fruit}'>일괄 제외 되돌리기</button>
        </td></tr>`;
    });
    h += "</table><p class='muted small'>«대표 외 장수» 는 <b>지금 데이터셋에 있는 사진만</b> 셉니다(검수자별 표와 같은 규칙). "
      + "«데이터셋 밖» 은 이미 폴더에서 빠진 사진의 기록 수이고, 버튼을 눌러도 그 사진들은 바뀌지 않습니다.</p>"
      + "<p class='muted small'>그룹마다 첫 장(대표)만 남기고 나머지를 «제외» 로 표시합니다. 원본 파일은 건드리지 않고, 편집 화면에서 사진 하나씩 되돌릴 수 있습니다.</p>";
  }

  // 제외 목록 내보내기
  h += "<h3>제외 목록 내보내기</h3><p class='muted small'>data/&lt;과일&gt;/excluded_list.txt 로 저장합니다. 원본을 정말 지우려면 그 목록으로 export/make_delete_script.py 가 스크립트를 만들어 주고, 실행은 사람이 합니다.</p><div class='tools'>";
  j.fruits.forEach((f) => { h += `<button class='expexc' data-f='${f.fruit}'>${FRUIT_KO[f.fruit] || f.fruit} 제외 목록 저장</button>`; });
  h += "</div>";

  const people = Object.keys(j.by_person).sort();
  h += "<h3>검수자별</h3>";
  if (j.outside_dataset) {
    h += `<p class='muted small'>※ 지금 데이터셋에 없는 사진(이미 빼낸 중복 등) ${j.outside_dataset}건의 기록은 이 표에서 뺐습니다.</p>`;
  }
  if (!people.length) h += "<p class='muted'>아직 검수 기록이 없습니다.</p>";
  else {
    h += "<table class='d'><tr><th class='l'>이름</th>" + Object.values(ko).slice(1).map((k) => `<th>${k}</th>`).join("") + "<th>합계</th></tr>";
    people.forEach((p) => {
      const c = j.by_person[p];
      const tot = c.ok + c.fixed + c.flag + c.exclude;
      h += `<tr><td class='l'>${escapeHtml(p)}</td><td>${c.ok}</td><td>${c.fixed}</td><td>${c.flag}</td><td>${c.exclude}</td><td>${tot}</td></tr>`;
    });
    h += "</table>";
  }
  $("#dash").innerHTML = h;

  $$(".dupapply").forEach((b) => b.onclick = async () => {
    const f = b.dataset.f;
    const pv = await api("/api/duplicate_preview?fruit=" + encodeURIComponent(f));
    if (!pv || pv.n_to_exclude === undefined) return flash(errMsg(pv, "미리보기를 불러오지 못했습니다"), true);
    const outMsg = pv.outside_dataset
      ? `\n(중복 목록에는 ${pv.outside_dataset}장이 더 있지만 지금 데이터셋에 없어 건드리지 않습니다)` : "";
    // 「이미 제외됨」·「사람이 이미 판정함」을 빼고 **정말 바뀌는 장수**를 말한다(ab사이클2 P1)
    const willN = (pv.n_will_change !== undefined) ? pv.n_will_change : pv.n_to_exclude;
    if (!confirm(`${FRUIT_KO[f] || f}: 중복 그룹 ${pv.n_groups}개에서 대표를 뺀 ${pv.n_to_exclude}장 중`
      + ` «아직 안 본» ${willN}장을 «제외» 로 표시합니다.`
      + (pv.already_excluded ? `\n(${pv.already_excluded}장은 이미 제외돼 있습니다)` : "")
      + (pv.kept_human ? `\n(${pv.kept_human}장은 사람이 이미 판정해서 건드리지 않습니다)` : "")
      + `${outMsg}\n원본 파일은 지우지 않습니다. 진행할까요?`)) return;
    b.disabled = true;
    const r = await post("/api/apply_duplicate_exclusions", { fruit: f, by: who() });
    b.disabled = false;
    if (!r || !r.ok) return flash(errMsg(r, "실패"), true);
    flash(`${r.changed}장을 제외로 표시했습니다`);
    loadDash();
  });
  $$(".dupundo").forEach((b) => b.onclick = async () => {
    const f = b.dataset.f;
    const pv = await api("/api/duplicate_preview?fruit=" + encodeURIComponent(f));
    if (!pv || pv.n_undoable === undefined) return flash(errMsg(pv, "미리보기를 불러오지 못했습니다"), true);
    // ab사이클2 P1: 전에는 «메모가 중복: 으로 시작하는 제외» 를 전부 되돌려 3차 판정 314장을 지웠다.
    // 이제 이 단추가 넣은 것만 되돌아온다 — 몇 장이 되돌아오고 몇 장은 그대로인지 먼저 말한다.
    if (!pv.n_undoable) {
      alert(`${FRUIT_KO[f] || f}: 이 단추로 넣은 제외가 없습니다 — 되돌릴 것이 없습니다.\n`
        + `(지금 «제외» ${pv.n_other_excludes || 0}장은 AI 판정·사람이 넣은 것이라 이 단추가 건드리지 않습니다)`);
      return;
    }
    if (!confirm(`${FRUIT_KO[f] || f}: 이 단추로 넣은 제외 ${pv.n_undoable}장만 «아직 안 봄» 으로 되돌립니다.\n`
      + `(AI 판정·사람이 넣은 제외 ${pv.n_other_excludes || 0}장은 그대로 둡니다)\n\n`
      + "⚠️ 되돌린 뒤 다시 일괄 제외해도 데이터셋 밖 사진은 복구되지 않습니다.\n"
      + "   (이미 폴더에서 빠진 사진은 «제외» 로 다시 표시할 수 없어서, 누가·왜 뺐는지 기록이 사라집니다)\n\n"
      + "그래도 진행할까요?  (진행하면 status.json 을 먼저 한 벌 복사해 둡니다)")) return;
    b.disabled = true;
    const r = await post("/api/undo_duplicate_exclusions", { fruit: f });
    b.disabled = false;
    if (!r || !r.ok) return flash(errMsg(r, "실패"), true);
    flash(`${r.changed}장을 되돌렸습니다` + (r.kept_other ? ` (다른 출처 제외 ${r.kept_other}장은 그대로)` : ""));
    if (r.backup) alert("되돌리기 전 상태를 여기에 복사해 두었습니다:\n" + r.backup
      + "\n\n잘못 눌렀다면 이 파일을 status.json 으로 덮어쓰면 됩니다(툴 담당자에게 부탁하세요).");
    loadDash();
  });
  loadInstStats();
  $$(".expexc").forEach((b) => b.onclick = async () => {
    const r = await post("/api/export_excluded", { fruit: b.dataset.f });
    if (!r || !r.ok) return flash(errMsg(r, "실패"), true);
    flash(`${r.n}장을 excluded_list.txt 에 저장했습니다`);
    alert("저장 위치:\n" + r.path + "\n\n제외 " + r.n + "장");
  });
}
$("#refresh").onclick = loadDash;

/* ═══════════ 열매 개수(카운팅) 집계 — 0917 사이클3 ③ ═══════════
   한 장을 세는 데 0.4~0.6초라 서버가 디스크 캐시에 적어 둔다. 화면은 캐시를 읽어 바로 보여 주고,
   아직 안 센 사진이 있으면 «지금 세기» 단추로 뒤에서 세게 한 뒤 2초마다 진행을 다시 묻는다. */
async function loadInstStats() {
  const el = $("#iststat");
  if (!el) return;
  const j = await api("/api/instance_stats");
  if (!j || !j.stats) { el.innerHTML = "<p class='muted'>열매 개수를 불러오지 못했습니다.</p>"; return; }
  const run = j.running || {};
  let h = "<table class='d'><tr><th class='l'>과일</th><th>사진</th><th>센 사진</th><th>열매 합계</th>"
    + "<th>장당 평균</th><th>가장 많은 장</th><th class='l'>작업</th></tr>";
  Object.keys(j.stats).forEach((f) => {
    const s = j.stats[f], r = run[f];
    const busy = r ? `세는 중 ${r.done} / ${r.total}장 (${r.sec}초)` : "";
    h += `<tr><td class='l'>${FRUIT_KO[f] || f}</td><td>${s.n_images}</td><td>${s.n_counted}</td>`
      + `<td>${s.n_instances.toLocaleString()}</td><td>${s.avg}</td><td>${s.max}</td><td class='l'>`
      // 0918 UI사이클4 N9: 번호 라벨이 아예 없는 과일(복숭아·포도)에도 «세기» 단추가 보여서,
      // 누르면 2,531장을 8분 세고 결과는 전부 0이었다. has_num 이 false 면 이유를 적고 단추를 감춘다.
      + (s.has_num === false ? "<span class='muted'>번호 라벨이 없는 과일입니다 — 셀 것이 없습니다</span>"
        : busy ? `<span class='muted'>${busy}</span>`
        : s.stale ? `<button class='istrun' data-f='${f}'>아직 안 센 ${s.stale}장 세기</button>`
          : "<span class='muted'>다 셌습니다</span>") + "</td></tr>";
  });
  h += "</table><p class='muted small'>«이진 칠한 영역가 배경인 자리의 번호는 빼고» 센 숫자입니다(편집 화면의 «번호 N개» 와 같은 규칙). "
    + "번호 파일이나 칠한 영역를 고치면 그 사진만 다시 셉니다."
    // 0919 사이클4 M1: 복숭아에 번호본이 생겼다 — «복숭아·포도는 0» 은 이제 거짓이다.
    // 0919 사이클4 2차: 포도는 다시 껐다(교수님 확인 8번 대기) — 포도만 여전히 0 이다.
    + " 포도는 아직 번호본을 켜지 않았습니다(교수님 확인 대기) — 켜면 알이 아니라 <b>송이</b> 수입니다.</p>";
  el.innerHTML = h;
  $$(".istrun").forEach((b) => b.onclick = async () => {
    b.disabled = true;
    await api("/api/instance_stats?start=1&fruit=" + encodeURIComponent(b.dataset.f));
    flash("열매 개수를 세는 중입니다 (사진 한 장에 0.4~0.6초)");
    loadInstStats();
  });
  if (Object.keys(run).length) {
    clearTimeout(loadInstStats._t);
    loadInstStats._t = setTimeout(() => { if (!$("#view-dash").classList.contains("hidden")) loadInstStats(); }, 2000);
  }
}

/* «번호 편집 대상» 정렬 — 서버는 이 정렬을 모르므로(서버 파일은 건드리지 않는다)
   조건에 맞는 목록을 모두 받아 와서 번호오류가 있는 사진을 앞으로 옮긴다. */
async function loadListInstErr(keepPage) {
  await ensureErrRows();
  const base = new URLSearchParams({
    fruit: S.fruit, status: $("#f-status").value, sort: "name",
    q: $("#f-q").value, page_size: 500
  });
  if ($("#f-dup").checked) base.set("dup", "1");
  if ($("#f-suspect").checked) base.set("suspect", "1");
  if ($("#f-prop").checked) base.set("proposal", "1");
  $("#grid").innerHTML = '<div class="muted">번호 편집 대상을 찾는 중…</div>';
  let all = [], page = 1, pages = 1, feat = null;
  do {
    base.set("page", page);
    const j = await api("/api/list?" + base.toString());
    if (!j || !j.items) {
      $("#grid").innerHTML = '<div class="muted">목록을 불러오지 못했습니다. 새로고침 해 보세요.</div>';
      if (j) flash(errMsg(j, "목록을 불러오지 못했습니다"), true);
      return;
    }
    feat = j.features; pages = j.pages;
    all = all.concat(j.items);
    page++;
  } while (page <= pages && page <= 30);
  applyFeatures(feat || {});
  const nerr = (s) => (S.errBy[s] || []).length;
  const team = $("#f-sort").value === "teamreview" && S.fruit === "apple";
  const review = team ? await api("/api/team_review?fruit=apple") : null;
  const queue = review && review.ok ? review.queue : [];
  if (team && !review?.ok) flash("사과 우선 검수 자료를 읽지 못했습니다", true);
  const rank = (stem) => queue.includes(stem) ? queue.indexOf(stem) : queue.length;
  all.sort((a, b) => (team ? rank(a.stem) - rank(b.stem) : 0) || (nerr(b.stem) - nerr(a.stem)) || (a.stem < b.stem ? -1 : a.stem > b.stem ? 1 : 0));
  const ps = 120;
  S.pages = Math.max(1, Math.ceil(all.length / ps));
  if (!keepPage) S.page = 1;
  if (S.page > S.pages) S.page = S.pages;
  S.listTotal = all.length;
  S.items = all.slice((S.page - 1) * ps, S.page * ps);
  const nStems = all.filter((it) => nerr(it.stem)).length;
  $("#listinfo").textContent = team ? `박성문 review_list.csv 순서 · ${queue.length}장 우선 · 전체 ${all.length}장` : `조건에 맞는 사진 ${all.length}장 · 번호오류 ${nStems}장을 앞에 둠`;
  $("#pageinfo").textContent = `${S.page} / ${S.pages} 쪽 (한 쪽에 ${ps}장)`;
  $("#prevpage").disabled = S.page <= 1;
  $("#nextpage").disabled = S.page >= S.pages;
  renderCounts();
  renderGrid();
}

/* ══════════════════════════ ⑤ 목록 — 빠른 필터 «무엇부터 볼까» ══════════════════════════
   새 API 를 만들지 않는다. 위의 select/checkbox 를 **대신 눌러 주고** loadList() 를 부른다. */

function clearFilters() {
  $("#f-status").value = "all";
  $("#f-sort").value = "priority";
  $("#f-dup").checked = false;
  $("#f-suspect").checked = false;
  $("#f-prop").checked = false;
  $("#f-q").value = "";
  S.flag = "";                       // 의심 «종류» 거르기도 함께 지운다
  S.confFilter = ""; S.confBy = "";  // 사람 확정 거르기(«내 큐»)도 함께 지운다 — 0918 사이클2
}

/* ─── 의심 «종류» 별 단추 (0917 사이클3 ②) ───
   그 과일에 **실제로 있는 종류만** 서버가 flag_counts 로 알려 주므로 그것만 단추로 만든다. */
let flagSig = null;
function renderFlagBtns() {
  const el = $("#flagqf");
  if (!el) return;
  const c = S.flagCounts || {};
  const sig = Object.keys(c).sort().map((k) => k + ":" + c[k]).join("|") + "/" + (S.flag || "");
  if (sig === flagSig) return;
  flagSig = sig;
  const names = Object.keys(c).sort((a, b) => c[b] - c[a]);
  el.innerHTML = names.map((n) => {
    const ko = FLAG_KO[n] || [n, n];
    return '<button class="qf fq' + (S.flag === n ? " on" : "") + '" data-flag="' + n + '" title="'
      + escapeHtml("자동 점검이 의심한 종류: " + ko[1] + " (" + n + ")") + '">'
      + escapeHtml(ko[0]) + " " + c[n] + "</button>";
  }).join("");
  el.querySelectorAll(".fq").forEach((b) => b.onclick = () => {
    const want = S.flag === b.dataset.flag ? "" : b.dataset.flag;   // 한 번 더 누르면 해제
    clearFilters();
    S.flag = want;
    $$(".qf").forEach((o) => o.classList.remove("on"));
    loadList();
    b.blur();
  });
}
setInterval(renderFlagBtns, 300);
renderFlagBtns();
const QF = {
  // 0918 사이클2 — «내 큐»: 아직 사람이 확정하지 않은 사진만, 급한 순서로(서버의 sort=queue).
  myqueue: () => { $("#f-sort").value = "queue"; S.confFilter = "0"; },
  unseen:  () => { $("#f-status").value = "unreviewed"; },
  missing: () => { $("#f-sort").value = "added"; $("#f-prop").checked = true; },
  dup:     () => { $("#f-dup").checked = true; },
  insterr: () => { $("#f-sort").value = "insterr"; },
  all:     () => {}
};
$$(".qf").forEach((b) => b.onclick = () => {
  clearFilters();
  QF[b.dataset.qf]();
  $$(".qf").forEach((o) => o.classList.toggle("on", o === b && b.dataset.qf !== "all"));
  loadList();
  b.blur();
});
/* 검색 칸: 치는 대로 걸러 준다 — 한 글자마다 서버를 부르지 않게 300ms 쉬었다 부른다.
   한글 조합(IME)이 끝나기 전에는 아무것도 하지 않는다(사이클2 M6). */
let qt = null;
const fq = $("#f-q");
if (fq) fq.addEventListener("input", (e) => {
  if (e.isComposing) return;
  clearTimeout(qt);
  qt = setTimeout(() => loadList(), 300);
});

// 사람이 위쪽 select/checkbox 를 직접 만지면 빠른 단추의 «켜짐» 표시를 뗀다(거짓말하지 않게)
["#f-status", "#f-sort", "#f-dup", "#f-suspect", "#f-prop", "#f-q", "#fruit"].forEach((s) => {
  const e = $(s);
  if (e) e.addEventListener("change", () => $$(".qf").forEach((o) => o.classList.remove("on")));
});


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { loadFruits, applyFeatures, loadList, renderCounts, renderGrid, refreshCard, cardFace, openItem, openStem, nextItem, prevItem, loadDash, loadInstStats, loadListInstErr, clearFilters, renderFlagBtns });
})();
