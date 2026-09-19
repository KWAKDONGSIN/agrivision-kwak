/* export — «데이터 정리» 탭 (데이터셋 내보내기)
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: ui.js 1046-1336줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   고른 과일·종류·조건으로 서버 폴더에 데이터셋을 만든다. 서버가 이 기능을 모르면 탭 안을 감추고 안내 한 줄만 보여 준다(만들기/켜기 분리 규칙).

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, escapeHtml = UI.escapeHtml, who = UI.who, ensureWho = UI.ensureWho, FRUIT_KO = UI.FRUIT_KO;
const api = API.get, post = API.post;

/* ══════════════════════════ ⑨ «데이터 정리» 탭 — 서버에 데이터셋 저장 (사이클 3) ══════════════════════════
   방향 문서 §4 사이클3 «데이터셋을 확실히 만든 다음에 실험» · 설계 사이클2 2차 §12-2 · 정책 3차 §4.
   ⛔ 규칙 §8-10(만들기/켜기 분리): 정적 파일은 서버 재시작 없이 바로 나가므로 **화면이 서버보다 먼저 온다.**
      서버가 이 기능을 모르면(/api/export_list → 404) 탭 안을 통째로 감추고 안내 한 줄만 보여 준다.
   화면 글자는 최소로 — 이유·설명은 전부 풍선말(title)과 /static/help.html 에 있다. */
const EXPK = { mask: "세그 마스크", instances: "열매 번호", boxes: "상자 YOLO",
               counts: "개수(counts.csv)" };      // 0919 «개수 세기» 사이클1 (지시서 §1-3)
const EXPM = { conf: "사람 확정만", ai: "AI 제안 포함" };
const EXP = { caps: null, fruit: null, mode: "conf",
              kinds: { mask: true, instances: false, boxes: false, counts: false },
              n: null, job: null, timer: null, ready: false, dir: "exports" };

/* api() 는 404 와 «서버가 이 기능을 모른다» 를 구별해 주지 않으므로(둘 다 오류 문장) 여기서만 상태를 본다 */
async function expFetch(url, opt) {
  let r;
  try { r = await fetch(url, opt); } catch (e) { return { status: 0, j: null }; }
  let j = null;
  try { j = JSON.parse(await r.text()); } catch (e) { j = null; }
  return { status: r.status, j: j };
}

function expLock(on) {
  EXP.ready = !on;
  $("#expguard").classList.toggle("hidden", !on);
  $("#expbody").classList.toggle("hidden", on);
}

async function expOpen() {
  const r = await expFetch("/api/export_list");
  if (r.status === 401) { location.href = "/login?next=/"; return; }
  if (!r.j || !r.j.ok) { expLock(true); return; }          // 404 = 옛 서버 · 그 밖의 오류도 잠근다
  expLock(false);
  EXP.caps = r.j.fruits || {};
  EXP.dir = r.j.dir || "exports";
  const fs = Object.keys(EXP.caps);
  if (!EXP.fruit || !EXP.caps[EXP.fruit]) EXP.fruit = (fs.indexOf(S.fruit) >= 0 ? S.fruit : fs[0]);
  expDraw();
  expTable(r.j.items || []);
  await expPlan();
  const run = (r.j.running || [])[0];
  if (run && !EXP.timer) { EXP.job = run.job; expPoll(); }  // 남이 돌리고 있으면 그것을 따라 보여 준다
}
window.expOpen = expOpen;

function expDraw() {
  const c = (EXP.caps || {})[EXP.fruit] || {};
  $("#exp-fruits").innerHTML = Object.keys(EXP.caps).map((f) => {
    const n = (EXP.caps[f] || {}).n_images || 0;
    return `<label class="chk" title="${escapeHtml(FRUIT_KO[f] || f)} ${n}장"><input type="radio" name="expf"`
      + ` value="${f}"${f === EXP.fruit ? " checked" : ""}> ${escapeHtml(FRUIT_KO[f] || f)}</label>`;
  }).join("");
  $$("#exp-fruits input").forEach((e) => {
    e.onchange = () => { EXP.fruit = e.value; expDraw(); expPlan(); };
  });

  /* 그 과일에 그 자료가 없으면 **비활성 + 이유**(풍선말). 없는 것은 체크도 풀어 둔다. */
  const why = { mask: c.has_mask ? "" : "이 과일은 마스크 폴더가 없습니다",
                instances: c.has_instances ? "" : "이 과일에는 열매 번호 라벨이 없습니다",
                boxes: c.n_box_images ? "" : "아직 저장된 상자가 없습니다(② 상자 그리기로 만듭니다)",
                // 개수 표는 늘 만들 수 있다 — 상자도 번호도 없으면 빈 표가 나오고 그것도 사실이다
                counts: "" };
  $("#exp-kinds").innerHTML = Object.keys(EXPK).map((k) => {
    const off = !!why[k];
    if (off) EXP.kinds[k] = false;
    const tip = off ? why[k] : { mask: "열매를 칠한 그림을 0/255 PNG 로 내보냅니다",
                                 instances: "알마다 번호가 붙은 uint16 PNG 를 내보냅니다(세그 마스크와 함께 나갑니다)",
                                 boxes: "네모를 YOLO txt 로 내보냅니다",
                                 counts: "사진마다 «열매가 몇 개인가» 를 counts.csv 한 장으로 내보냅니다"
                                       + " — 상자 수 · 번호 수 · 검출 팀 초벌 수 · 사람 확정 개수"
                                       + "(상자 확정이나 번호 확정에서 유도합니다)" }[k];
    return `<label class="chk${off ? " off" : ""}" title="${escapeHtml(tip)}"><input type="checkbox"`
      + ` data-k="${k}"${EXP.kinds[k] ? " checked" : ""}${off ? " disabled" : ""}> ${EXPK[k]}`
      + (off ? " (없음)" : "") + "</label>";
  }).join("");
  $$("#exp-kinds input").forEach((e) => {
    e.onchange = () => {
      EXP.kinds[e.dataset.k] = e.checked;
      if (e.dataset.k === "instances" && e.checked) EXP.kinds.mask = true;   // 번호는 마스크와 함께 나간다
      expDraw();
      expPlan();       // 0918 사이클4: «확정 장수» 줄이 종류별이라 고른 종류가 바뀌면 다시 센다
    };
  });

  $("#exp-mode").innerHTML = Object.keys(EXPM).map((m) => {
    const tip = m === "conf" ? "사람이 «맞다»(Enter)로 확정한 사진만 내보냅니다. 확정한 «문제 있음» 은 아직 고칠 것이라 빠집니다."
                             : "사람이 확정하지 않은 사진도 AI 제안(제외·근접중복)을 그대로 적용해 내보냅니다.";
    return `<label class="chk" title="${escapeHtml(tip)}"><input type="radio" name="expm" value="${m}"`
      + `${EXP.mode === m ? " checked" : ""}> ${EXPM[m]}</label>`;
  }).join("");
  $$("#exp-mode input").forEach((e) => {
    e.onchange = () => { EXP.mode = e.value; expPlan(); };
  });
}

/* «지금 확정된 사진 N장» 은 늘 보여 준다(3차 결정 1 — 경고가 아니라 상시 표시).
   0918 사이클4 결정 1: 확정은 **종류마다 따로**다 → 고른 종류의 숫자를 나란히 적는다.
   (옛 서버는 종류별 칸을 주지 않으므로 그때는 세그 마스크 하나만 — 예전과 같은 문장이 된다.) */
function expConfText(c) {
  const parts = [];
  if (EXP.kinds.mask) parts.push("세그 " + (c.n_confirmed_out || 0));
  if (EXP.kinds.instances && c.n_confirmed_instances_out !== undefined)
    parts.push("번호 " + c.n_confirmed_instances_out);
  if (EXP.kinds.boxes && c.n_confirmed_boxes_out !== undefined)
    parts.push("상자 " + c.n_confirmed_boxes_out);
  // 개수는 **상자 확정 또는 번호 확정에서 유도**하므로 «개수만 확정한 장수» 라는 것이 없다 —
  // 두 숫자를 그대로 보여 준다(따로 세지 않는다). 종류를 개수만 골랐을 때 0장이라고 말하지 않게.
  if (EXP.kinds.counts && !EXP.kinds.boxes && c.n_confirmed_boxes_out !== undefined)
    parts.push("개수 " + (c.n_confirmed_instances_out || 0) + "+" + c.n_confirmed_boxes_out);
  if (!parts.length) parts.push("세그 " + (c.n_confirmed_out || 0));
  return "지금 확정된 사진 " + parts.join(" · ") + "장";
}

/* 0918 사이클4 **2차 검수**(실측 s1_flow 가-9): «상자 YOLO» 만 골랐을 때 이 줄이 «지금 조건으로
   나갈 사진 0장» 이라고 말하면서 실제로는 상자 txt 2장을 내보냈다(확인창만 «상자 2장» 이라고 했다).
   `/api/export_plan` 의 `n_out` 은 **사진(마스크·번호)** 장수라서 상자만 고르면 늘 0 이다.
   상자만 고른 때는 세는 것이 «상자를 확정한 사진» 이므로 그 숫자를 말한다(글자 수는 같다). */
function expOutText(c) {
  if (EXP.kinds.counts && !EXP.kinds.mask && !EXP.kinds.instances && !EXP.kinds.boxes)
    return "개수 표 한 장이 나갑니다";
  if (EXP.kinds.boxes && !EXP.kinds.mask && !EXP.kinds.instances) {
    const n = EXP.mode === "conf" ? (c.n_confirmed_boxes_out || 0) : (c.n_box_images || 0);
    return "지금 조건으로 나갈 상자 " + n + "장";
  }
  return "지금 조건으로 나갈 사진 " + (EXP.n === null ? "?" : EXP.n) + "장";
}

async function expPlan() {
  const c = (EXP.caps || {})[EXP.fruit] || {};
  $("#exp-count").textContent = expConfText(c) + " — 0장이면 아무것도 나가지 않습니다. "
    + "AI 제안까지 포함하려면 위에서 고르세요. (세는 중…)";
  const r = await expFetch(`/api/export_plan?fruit=${encodeURIComponent(EXP.fruit)}`
                           + `&confirmed_only=${EXP.mode === "conf" ? 1 : 0}`);
  EXP.n = (r.j && r.j.ok) ? r.j.n_out : null;
  if (r.j && r.j.caps) EXP.caps[EXP.fruit] = r.j.caps;
  const c2 = (EXP.caps || {})[EXP.fruit] || {};
  /* 🔴 0919 «개수 세기» **사이클5**(사이클4 2차 §6-8·§9-4 · 3차 §3): «사람 확정만 + 개수» 는
     규칙대로 **마스크 확정**을 따르므로(0919 사이클1 총괄 결정 2 — counts.csv 는 그 job 이 나간
     사진만 담고 manifest «포함» 과 한 줄도 다르지 않다) 상자만 확정한 사람은 **빈 표**를 받는다.
     사이클4 2차의 사용자 시나리오가 여기서 한 번 막혔다(«나갈 상자 1장» 이라 적고 표는 0줄).
     규칙은 그대로 두고 **미리 말해** 준다 — 받은 뒤에 놀라지 않게. «AI 제안 포함» 에서는
     마스크 확정을 보지 않으므로 이 줄을 띄우지 않는다. */
  const cntWarn = (EXP.kinds.counts && EXP.mode === "conf")
    ? "개수 csv 는 마스크를 확정한 사진만 담깁니다 — 상자만 확정하면 빈 표" : "";
  $("#exp-count").innerHTML = escapeHtml(expConfText(c2) + " — 0장이면 아무것도 나가지 않습니다. "
    + "AI 제안까지 포함하려면 위에서 고르세요. · " + expOutText(c2))
    + (cntWarn ? "<br>" + escapeHtml(cntWarn) : "");
}

function expKinds() {
  const ks = Object.keys(EXPK).filter((k) => EXP.kinds[k]);
  if (ks.indexOf("instances") >= 0 && ks.indexOf("mask") < 0) ks.unshift("mask");
  return ks;
}

/* 0918 사이클3 3차 전 소수정(2차 §4-7): 409 문구가 과일을 영어로 말했다(«지금 peach 를 …»).
   서버 문구는 그대로 두고, 서버가 같이 주는 fruit 칸을 화면이 FRUIT_KO 로 바꿔 쓴다. */
function expErrMsg(j) {
  let m = (j && (j.error || j.msg)) || "저장하지 못했습니다.";
  const ko = j && j.fruit && FRUIT_KO[j.fruit];
  if (ko) m = m.split(j.fruit).join(ko);
  return m;
}

async function expGo() {
  if (!EXP.ready) return;
  ensureWho();                                        // 이름 칸이 비었으면 이름부터 묻는다(기존 장치)
  const ks = expKinds();
  if (!ks.length) { $("#exp-msg").textContent = "무엇을 내보낼지 하나 이상 고르세요."; return; }
  const onlyBox = ks.length === 1 && ks[0] === "boxes";
  /* 0918 사이클4 2차 검수: 여기에 «상자도 0장이면 막는다» 가드를 걸어 봤다가 **되돌렸다** —
     사이클3 2차가 못박은 «상자만 골라도 저장이 된다»(a5b_ui 화면-4-A)를 깨뜨린다.
     화면은 이제 «지금 조건으로 나갈 상자 N장» 이라고 먼저 말하므로(expOutText) 사람은 0 을 보고 누른다.
     빈 날짜 폴더가 하나 생기는 것을 막을지는 3차 판단으로 넘긴다(stage2_review §4-4 7번). */
  /* 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**(§6 사용자 시나리오 7단계 — 진짜 브라우저 실측):
     처음 온 사람이 복숭아 `/box` 에서 초벌을 Enter 로 **상자 확정**한 뒤 «개수 + 상자 YOLO ·
     사람 확정만» 을 고르면, 바로 위 줄이 «지금 조건으로 나갈 상자 **1장**» 이라고 적어 놓고도
     이 가드가 «0장 — 나갈 것이 없습니다» 로 **막아 버렸다**(EXP.n 은 «마스크» 확정 장수뿐이라서다).
     한 화면이 같은 순간에 서로 다른 말을 했고, 안내문은 방금 누른 Enter 를 또 누르라고 했다.
     → 막는 기준을 «고른 종류가 **사진(마스크·번호)**을 필요로 할 때» 로 좁힌다. 상자·개수만
       고른 경우는 사진 줄이 필요 없으므로 그대로 내보낸다(상자는 «상자 확정» 을, 개수 표는
       총괄 결정 2 대로 «마스크 확정» 을 각각 따른다 — counts.csv 가 0줄이 될 수 있고 그것은 규칙이다).
     0918 사이클3 2차의 «상자만 골라도 저장이 된다» 를 넓힌 것이고 좁히지 않았다. */
  const needPhoto = ks.indexOf("mask") >= 0 || ks.indexOf("instances") >= 0;
  if (EXP.n === 0 && !onlyBox && needPhoto) {
    /* 🔴 0919 «개수 세기» 사이클5 **2차**(시나리오 실측 23:35): «세그 마스크» 는 **기본으로 켜져
       있다.** 그래서 상자만 확정한 처음 온 사람이 «개수 + 상자» 를 더 고르면 마스크가 그대로 켜진
       채라 여기서 막히고, 안내문은 **방금 누른 Enter 를 또 누르라고** 한다(사이클4 2차가 지적한 그
       자리의 남은 반쪽이다). 규칙은 그대로 두고 **무엇을 빼면 되는지** 한 마디 덧붙인다. */
    const off = [];
    if (ks.indexOf("mask") >= 0) off.push("«세그 마스크»");
    if (ks.indexOf("instances") >= 0) off.push("«열매 번호»");
    const alsoBC = ks.indexOf("boxes") >= 0 || ks.indexOf("counts") >= 0;
    $("#exp-msg").textContent = "0장 — 나갈 것이 없습니다. 편집 화면에서 Enter 로 확정하거나 «AI 제안 포함» 을 고르세요."
      + (alsoBC ? " " + off.join("·") + " 의 확정이 0장이어서 막았습니다 — 그 체크를 빼면 상자·개수만 나갑니다." : "");
    return;
  }
  /* 0918 사이클3 2차 검수(화면-4): 상자만 골랐는데 «나갈 사진: 0장» 이라고만 물었다(그러고는
     상자 1장을 내보냈다). 마스크·번호를 안 골랐으면 사진 줄을 아예 빼고, 상자를 골랐으면
     상자는 «사람 확정» 을 가리지 않는다는 것까지 적는다(export_boxes_to 는 저장된 상자 전부를 낸다). */
  const nbox = ((EXP.caps || {})[EXP.fruit] || {}).n_box_images || 0;
  const ncbox = ((EXP.caps || {})[EXP.fruit] || {}).n_confirmed_boxes_out || 0;
  const t = `${FRUIT_KO[EXP.fruit] || EXP.fruit} · ${ks.map((k) => EXPK[k]).join(" + ")}`
    + `\n조건: ${EXPM[EXP.mode]}`
    + (onlyBox ? "" : `\n나갈 사진: ${EXP.n === null ? "?" : EXP.n}장`)
    // 0918 사이클4 결정 1: 상자도 «사람 확정만» 을 가린다(사이클3 2차 §2 중간 5 의 구멍을 메웠다).
    + (ks.indexOf("boxes") >= 0
        ? `\n상자: ${EXP.mode === "conf" ? ncbox + "장(상자를 확정한 사진만)" : nbox + "장(저장된 전부)"}`
        : "")
    + `\n\n서버 폴더(${EXP.dir}/)에 저장할까요?`;
  if (!confirm(t)) return;
  $("#exp-msg").textContent = "";
  $("#exp-out").classList.add("hidden");
  const r = await expFetch("/api/export_start", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fruit: EXP.fruit, kinds: ks, confirmed_only: EXP.mode === "conf", by: who() })
  });
  if (!r.j || !r.j.ok) { $("#exp-msg").textContent = expErrMsg(r.j); return; }
  EXP.job = r.j.job;
  $("#exp-go").disabled = true;
  $("#exp-msg").textContent = "저장하는 중…";
  expPoll();
}

function expPoll() {
  clearTimeout(EXP.timer);
  EXP.timer = setTimeout(expTick, 1000);              // 1초 폴링(WebSocket 은 쓰지 않는다)
}

async function expTick() {
  EXP.timer = null;
  if (!EXP.job) return;
  const r = await expFetch(`/api/export_status?job=${encodeURIComponent(EXP.job)}`);
  const j = r.j;
  if (!j || !j.ok) { $("#exp-msg").textContent = "진행 상황을 읽지 못했습니다."; $("#exp-go").disabled = false; return; }
  const pct = j.total ? Math.round(j.done / j.total * 100) : (j.state === "done" ? 100 : 0);
  $("#exp-bar").style.width = pct + "%";
  $("#exp-prog").textContent = `${pct}% ${j.msg || ""}`;
  if (j.state === "running") { expPoll(); return; }
  $("#exp-go").disabled = false;
  $("#exp-msg").textContent = "";
  const box = $("#exp-out");
  box.classList.remove("hidden");
  if (j.state === "error") {
    box.innerHTML = `<b>실패했습니다</b> — ${escapeHtml(j.msg || "")}`;
  } else {
    box.innerHTML = `<b>저장했습니다</b> <code>${escapeHtml(j.out || "")}</code>`
      + `<br>사진 ${j.n_images || 0}장 · 제외 ${j.n_dropped || 0}장`
      + (j.n_instances ? ` · 번호 ${j.n_instances}장` : "")
      + (j.n_box_images ? ` · 상자 ${j.n_box_images}장(${j.n_boxes || 0}개)` : "")
      + (j.n_counts ? ` · 개수 ${j.n_counts}줄` : "")
      + (j.n_images ? "" : " — 나간 사진이 없습니다(manifest 만 있습니다)");
  }
  const lst = await expFetch("/api/export_list");
  if (lst.j && lst.j.ok) {
    EXP.caps = lst.j.fruits || EXP.caps;
    expTable(lst.j.items || []);
    expDraw();
    expPlan();
  }
}

function expTable(items) {
  const el = $("#exp-list");
  if (!items.length) { el.innerHTML = '<p class="muted small">아직 내보낸 것이 없습니다.</p>'; return; }
  const show = items.slice(0, 10);
  /* 0918 사이클3 2차 검수(화면-3): 실패한 작업(반쪽 폴더)이 끝난 것과 **똑같이** 보였다.
     끝난 줄에는 글자를 한 자도 더하지 않고, 끝나지 않은 줄에만 앞에 표를 붙인다. */
  /* 0918 사이클3 3차 전 소수정(2차 §4-4): 서버가 죽어 «도는 중» 인 채 남은 폴더는 stale 로 온다 */
  /* 0918 사이클5(총괄) ③ — 아무것도 나가지 않은 «빈 날짜 폴더» 를 그 줄에서 말한다
     (사이클4 2차 §4-4 7번 · 3차가 사이클5 로 넘긴 것). 폴더를 지우지도, 만들기를 막지도 않는다 —
     «상자만 골라도 저장이 된다»(사이클3 2차 a5b_ui 화면-4-A)를 깨지 않는 가장 작은 쪽이다.
     서버가 `empty` 를 주지 않는 옛 판에서는 아무 글자도 붙지 않는다. */
  const bad = (it) => (it.state && it.state !== "done")
    ? (it.state === "running" ? (it.stale ? "도는 중(중단됐을 수 있음) " : "도는 중 ") : "실패 ")
    : (it.empty ? "빈 폴더 " : "");
  el.innerHTML = '<table class="d"><tr><th class="l">폴더</th><th class="l">종류</th><th class="l">조건</th>'
    + '<th>사진</th><th>제외</th><th class="l">누가</th></tr>'
    + show.map((it) => `<tr><td class="l" title="${escapeHtml((it.started || "") + (bad(it) ? " · " + (it.msg || "") : ""))}">`
        + `<b>${bad(it)}</b>${escapeHtml(it.out || it.job || "")}</td>`
        + `<td class="l">${(it.kinds || []).map((k) => EXPK[k] || k).join(" + ")}</td>`
        + `<td class="l">${it.confirmed_only === false ? EXPM.ai : EXPM.conf}</td>`
        + `<td>${it.n_images || 0}</td><td>${it.n_dropped || 0}</td>`
        + `<td class="l">${escapeHtml(it.by || "")}</td></tr>`).join("")
    + "</table>"
    + (items.length > show.length ? `<p class="muted small">최근 ${show.length}개만 보여 줍니다(전체 ${items.length}개).</p>` : "");
}

/* 옛 index.html(그 단추가 없는 판)에서도 조용히 넘어간다 */
const expBtn = $("#exp-go");
if (expBtn) expBtn.onclick = expGo;



/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { expOpen });
})();
