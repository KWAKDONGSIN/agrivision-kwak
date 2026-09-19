/* counts — 사람 확정 · 판정 · 하단 한 줄 · 개수 칸
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 1013-1112·1114-1201줄 · ui.js 272-360·364-617·619-629·939-1023·1025-1044줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   «확정» 을 쓰는 곳은 여기 하나다(confirmVerdict → /api/status confirm:true). 판정 단추(1~4·저장)와 Enter 확정, 사진 아래 «상태 한 줄»·«개수» 칸도 여기서 그린다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, who = UI.who, errMsg = UI.errMsg, escapeHtml = UI.escapeHtml, statusKo = UI.statusKo, TASKWORD = UI.TASKWORD, TASKKIND = UI.TASKKIND, TASKFIELD = UI.TASKFIELD, curTask = UI.curTask, setSideFold = UI.setSideFold, NUM_WHY = UI.NUM_WHY, confirmLeave = UI.confirmLeave, edToPngDataUrl = UI.edToPngDataUrl, saveBoxes = UI.saveBoxes, hasPendingRegion = UI.hasPendingRegion;
const api = API.get, post = API.post;
/* ↓ 아래에 오는 파일(뒤에 실리는 것)을 되돌아 부른다 — 부를 때 찾는다.
   (`typeof cntSet === "function"` 같은 옛 가드가 그대로 살아 있어야 해서 이름을 둔다:
    node 시뮬은 이 줄을 떼어 가지 않으므로 예전처럼 «없으면 건너뛴다» 가 된다.) */
const refreshCard = (...a) => UI.refreshCard(...a);
const renderCounts = (...a) => UI.renderCounts(...a);
const nextItem = (...a) => UI.nextItem(...a);
const openItem = (...a) => UI.openItem(...a);

/* ═════════ 사람 확정(confirmed) — 0918 사이클2 ═════════
   방향 문서 §3-1: AI 제안은 «미리 채워 둔 것» 이고, 사람이 누르는 순간 그것이 **확정**된다.
   서버에는 칸이 따로 있어(status.json 의 confirmed) AI 제안을 덮지 않는다.
   부르는 곳: ① 판정 단추·1~4 (doAction 끝) ② Enter = «AI 제안 그대로»(ui.js) ③ 묶음째(ui.js).
   «저장»(Ctrl+S)·«번호 저장»·«되돌리기» 는 확정하지 않는다 — 고친 것을 눈으로 본 뒤 사람이 누른다. */
async function confirmVerdict(status, stems, kind) {
  if (!S.stem) return null;
  kind = kind || "mask";
  // ⚠ 정적 파일(이 파일)은 서버를 다시 켜지 않아도 바로 나가지만, «확정» 을 받는 서버 쪽은
  // 다시 켜야 산다. 옛 서버에 confirm:true 를 보내면 그것을 무시하고 **AI 제안 status 를 덮어쓴다.**
  // 새 서버만 보내 주는 칸(`ai_status`)이 없으면 아무것도 쓰지 않고 사람에게 알린다.
  if (!S.item || S.item.ai_status === undefined) {
    flash("서버가 아직 «확정» 을 모릅니다 — 담당자가 서버를 다시 켠 뒤에 쓰세요(아무것도 저장하지 않았습니다)", true);
    return null;
  }
  // 0918 사이클4: 상자·번호 확정은 **새 서버만** 아는 칸이다. 옛 서버는 `kind` 를 통째로 무시하고
  // 마스크 확정에 써 버리므로(= 남의 칸을 덮는다), 새 서버가 주는 표식(ai_boxes_status)이
  // 없으면 아무것도 보내지 않는다. 사이클2 가드와 같은 층이고, 다음 사진으로도 안 넘어간다.
  if (kind !== "mask" && S.item.ai_boxes_status === undefined) {
    flash("서버가 아직 «상자·번호 확정» 을 모릅니다 — 담당자가 서버를 다시 켠 뒤에 쓰세요"
        + "(아무것도 저장하지 않았습니다)", true);
    return null;
  }
  const body = { fruit: S.fruit, stem: S.stem, status, by: who(), note: $("#note").value, confirm: true };
  if (stems && stems.length) body.stems = stems;
  if (kind !== "mask") body.kind = kind;
  const j = await post("/api/status", body);
  if (!j || !j.ok) { flash(errMsg(j, "확정을 저장하지 못했습니다"), true); return null; }
  const me = who(), at = (j.confirmed[S.stem] || {}).at || "";
  const ik = { mask: "confirmed", boxes: "confirmed_boxes", instances: "confirmed_instances" }[kind];
  if (S.item && S.item.stem === S.stem) S.item[ik] = { status, by: me, at, note: "" };
  Object.keys(j.confirmed).forEach((k) => {
    const it = S.items.find((x) => x.stem === k);
    if (it) { it[ik] = j.confirmed[k].status; if (kind === "mask") it.confirmed_by = me; }
    refreshCard(k);              // 0918 사이클5 ② — 묶음째 확정이면 그 묶음 카드가 다 바뀐다
  });
  S.confDone = (S.confDone || 0) + j.n;       // 이 화면에서 내가 확정한 장수(진행률을 바로 보여주려고)
  renderCounts();
  return j;
}

/* 0918 사이클4 — «저장 = 그 작업의 확정(수정함)» 을 화면 쪽에도 곧바로 반영한다.
   실제로 쓰는 것은 서버(boxes.py·instances.py)다. 여기서는 방금 저장한 사진의 칸만 맞춘다. */
function markTaskConfirmed(kind) {
  const ik = kind === "boxes" ? "confirmed_boxes" : "confirmed_instances";
  const me = who(), at = "";
  if (S.item && S.item.stem === S.stem) S.item[ik] = { status: "fixed", by: me, at, note: "" };
  const it = S.items.find((x) => x.stem === S.stem);
  if (it) it[ik] = "fixed";
  refreshCard(S.stem);                       // 0918 사이클5 ②
  S.confDone = (S.confDone || 0) + 1;
  renderCounts();
  if (typeof cntReload === "function") cntReload();   // 2차 검수 D-1 — 확정이 생겼으니 개수 칸도
}

/* 0919 «개수 세기» 사이클1 — 저장 직후 하단 «개수» 칸의 그 숫자만 사실에 맞춘다(/api/item 을 다시
   부르지 않는다). 사람 확정 개수(counts.human·source·conflict)는 **서버가 정한다** — 유도 규칙을
   화면에도 또 적으면 두 규칙이 갈라진다(app/boxes.py human_count 하나뿐). 다음에 이 사진을 열면
   서버 값으로 맞춰진다. (boxsim.js·modesim.js 는 저장 함수만 떼어 내 돌리므로 없을 수 있다.) */
function cntSet(key, n) {
  if (!S.item || S.item.stem !== S.stem || !S.item.counts) return;
  S.item.counts[key] = n;
  if (typeof renderCntChip === "function") renderCntChip();
}

/* 🔴 0919 개수 사이클1 **2차 검수 즉시 수정 D-1**(실측 `cycles/260919_count/cycle_1/stage2/a3_ui.py`
   [가]·[나] · 스크린샷 `~/ff_shots/cnt1/stage2/cnt_after_{save,zero}.png`):
   저장·되돌리기는 **확정을 바꾸므로 사람 확정 개수도 바뀐다.** 그런데 화면은 `cntSet()` 으로
   숫자 한 칸만 고쳤기 때문에
     · 상자를 저장한 직후 — 방금 «수정함» 으로 확정됐는데 칸이 회색이고 풍선말이
       «사람 확정 개수: 아직 없습니다» 라고 말했다(사실과 반대).
     · 🧹 전부 지워 저장(= 파일 삭제 + 확정 풀림)한 직후 — 칸이 **초록**인 채
       «사람 확정 개수: 2개 (상자 확정에서 나왔습니다)» 라고 말했다. 그 확정은 이미 없다.
   유도 규칙을 화면에 옮겨 적으면 네 번째 구현이 되므로(§2-1), **서버에게 그 한 장만 다시 묻는다**
   (이미 있는 `/api/item` · 답에서 `counts` 만 가져다 쓴다 · 새 글자 0자). */
async function cntReload() {
  if (!S.stem || typeof api !== "function") return;         // 시뮬(node)에는 api 가 없다
  const stem = S.stem;
  const j = await api(`/api/item?fruit=${encodeURIComponent(S.fruit)}`
                      + `&stem=${encodeURIComponent(stem)}`);
  if (!j || !j.counts || !S.item || S.stem !== stem) return;  // 그 사이 사진을 바꿨으면 그대로 둔다
  S.item.counts = j.counts;
  if (typeof renderCntChip === "function") renderCntChip();
}

/* 0918 사이클4 «3차 판정 전 소수정» 총괄 결정 1 — 되돌리기가 서버에서 그 종류의 확정을 지웠으면
   (응답 `confirmed_cleared`) 화면 쪽 칸도 비우고 **1초 힌트**로 «다시 확정하세요» 를 말한다.
   markTaskConfirmed 의 반대짝이다. 목록 카드는 이 칸(confirmed·confirmed_boxes·confirmed_instances)
   으로 테두리 색·판정 딱지를 그리므로(renderGrid), 비우지 않으면 «확정» 이라고 계속 적혀 있다. */
function clearTaskConfirmed(kind) {
  const ik = kind === "boxes" ? "confirmed_boxes"
           : kind === "instances" ? "confirmed_instances" : "confirmed";
  if (S.item && S.item.stem === S.stem) S.item[ik] = null;
  const it = S.items.find((x) => x.stem === S.stem);
  if (it) it[ik] = null;
  refreshCard(S.stem);                       // 0918 사이클5 ② — 카드가 «미확정» 으로 돌아온다
  if (typeof cntReload === "function") cntReload();   // 2차 검수 D-1 — 확정이 없어졌으니 개수 칸도
  flash("확정이 풀렸습니다 — 다시 확정하세요");
  clearTimeout(flash._t); flash._t = setTimeout(() => { $("#saveflash").textContent = ""; }, 1000);
}

async function doAction(action) {
  if (!S.stem) return flash("사진을 먼저 고르세요", true);
  // «원본 OK»·«문제 있음»·«제외» 는 브러시로 고친 것을 **저장하지 않는다**(그대로 다음 장으로 넘어감).
  // 그래서 저장 안 한 수정이 있으면 누르기 «전에» 물어본다.
  const discards = (action === "ok" || action === "flag" || action === "exclude");
  const wasDirty = S.edDirty;
  if (discards && !confirmLeave()) return;
  /* ─── 0918 사이클4 (사이클2 2차 설계안 (나) · s5_live_guard C-2·C-4) ───
     «1 원본 OK»·«3 문제»·«4 제외» 는 **그림을 하나도 쓰지 않는** 판정이다. 그런데 지금까지는
     /api/save 로 가서 `status`·`by`·`note` 를 사람 것으로 **덮어썼다** — AI 3회 검수가 적어 둔
     판정과 검수자 이름이 그 자리에서 사라졌다(실측 C-2 «AI 제안 exclude → ok» · C-4 «AI 3회
     검수 → 사람둘»). 방향 문서 §3-1 은 «AI 제안» 과 «사람 확정» 이 **다른 칸**이라고 말한다.
     → 이 셋은 이제 `confirmed` 칸만 쓴다. AI 제안(status·by·note)은 그대로 남는다.
     «2 AI로 교체»·«Ctrl+S 저장» 은 실제로 마스크를 쓰므로 예전 그대로 /api/save 로 간다. */
  if (discards) {
    const j = await confirmVerdict(action);
    if (!j) return;                       // 가드(옛 서버)에 막혔으면 다음 사진으로 넘어가지 않는다
    flash({ ok: "확정: 원본 그대로 OK", flag: "확정: 문제 있음", exclude: "확정: 제외" }[action]
          + " (" + who() + ")");
    if (action === "ok" && S.item && S.item.has_fixed) {
      alert("«원본 그대로 OK» 로 확정했지만, 이 사진에는 예전에 저장한 수정본이 남아 있습니다.\n"
          + "수정판 데이터셋을 만들면 원본이 아니라 그 수정본이 쓰입니다.\n"
          + "원본을 쓰려면 사진 바로 아래 «수정본 되돌리기» 를 눌러 주세요.");
    }
    nextItem(wasDirty);
    return;
  }
  const body = { fruit: S.fruit, stem: S.stem, action, by: who(), note: $("#note").value };
  if (action === "fixed") {
    flash("저장 중…");
    body.png = edToPngDataUrl();
  }
  const j = await post("/api/save", body);
  if (!j || !j.ok) return flash(errMsg(j, "저장 실패"), true);
  // 마스크를 실제로 저장한 것은 «수정본 저장»(fixed) 과 «AI 제안으로 교체»(ai) 뿐이다.
  // 그 두 가지가 성공했을 때만 «저장 안 한 수정» 표시를 지운다.
  if (action === "fixed" || action === "ai") S.edDirty = false;
  flash({ ok: "원본 그대로 OK 로 저장", ai: "AI 제안으로 교체 저장", fixed: "수정본 저장 완료",
          flag: "문제 있음 표시", exclude: "제외 표시" }[action]);
  // 0918 UI사이클5 N-C: «제외» 사진에 마스크를 저장해도 판정은 «제외» 로 남는다(서버가 정한다).
  // 그 말을 하지 않으면 사람은 «수정함» 이 된 줄 알고 넘어간다 — 되살리는 방법까지 같이 적는다.
  if (j.kept_exclude) {
    flash("저장했지만 판정은 «제외» 그대로입니다", true);
    alert("그림은 저장했습니다. 다만 이 사진의 판정은 «제외» 그대로입니다.\n"
        + "(제외는 «이 사진을 쓸지» 에 대한 판정이라, 그림을 고쳐도 저절로 풀리지 않습니다.)\n\n"
        + "이 사진을 다시 쓰려면 «1 원본 그대로 OK» 를 누르거나 다른 판정으로 바꿔 주세요.");
  }
  if (action === "ok" && j.has_fixed) {
    alert("«원본 그대로 OK» 로 표시했지만, 이 사진에는 예전에 저장한 수정본이 남아 있습니다.\n"
        + "수정판 데이터셋을 만들면 원본이 아니라 그 수정본이 쓰입니다.\n"
        + "원본을 쓰려면 사진 바로 아래 «수정본 되돌리기» 를 눌러 주세요.");
  }
  if (S.items[S.idx]) {
    S.items[S.idx].status = j.status.status;
    S.items[S.idx].ai_status = j.status.status;
    S.items[S.idx].has_fixed = S.items[S.idx].has_fixed || !!j.wrote_mask;
    refreshCard(S.items[S.idx].stem);        // 0918 사이클5 ② — «수정본» 딱지·판정이 바로 보인다
  }
  // 열려 있는 사진 자체의 상태도 같이 고친다. 이게 없으면 «Ctrl+S» 뒤에 옆의 «상태: 수정함» 과
  // 위의 「이 사진에서 할 일」 줄이 서로 다른 말을 한다(UI 사이클 1 의 N9).
  if (S.item) {
    S.item.status = j.status.status; S.item.by = j.status.by; S.item.at = j.status.at;
    // 0918 사이클2: 하단 상태 줄과 Enter 확정이 보는 «지금 판정» 도 같이 맞춘다
    S.item.ai_status = j.status.status; S.item.src = "human";
    S.item.has_fixed = S.item.has_fixed || !!j.wrote_mask;
  }
  $("#meta").innerHTML = escapeHtml(`${S.W}×${S.H} · 상태: ${statusKo(j.status.status)} · 검수: ${j.status.by} ${j.status.at}`);
  // 0918 사이클2: «원본 OK»·«AI로 교체»·«문제»·«제외» 는 사람이 직접 고른 판정이므로 **곧 확정**이다.
  // «저장»(fixed) 만 확정하지 않는다 — 고친 그림을 눈으로 확인한 뒤 Enter·1~4 로 확정한다.
  if (action !== "fixed") await confirmVerdict(j.status.status);
  else S.savedAt = Date.now();               // 하단 상태 줄의 «저장됨 — . 로 다음» 안내(ui.js)
  // 방금 «버리고 넘어가겠다» 고 답했으면 다음 장으로 갈 때 또 묻지 않는다(두 번 묻지 않기)
  if (action !== "fixed") nextItem(discards && wasDirty);
}
$("#btn-ok").onclick = () => doAction("ok");
$("#btn-ai").onclick = () => doAction("ai");
$("#btn-save").onclick = () => doAction("fixed");
$("#btn-flag").onclick = () => doAction("flag");
$("#btn-exc").onclick = () => doAction("exclude");
$("#btn-revert").onclick = async () => {
  if (!S.stem) return;
  const j = await post("/api/revert", { fruit: S.fruit, stem: S.stem, by: who() });
  if (!j || !j.ok) return flash(errMsg(j, "실패"), true);
  flash("수정본을 지우고 원본으로 되돌렸습니다");
  if (j.confirmed_cleared) clearTaskConfirmed(j.confirmed_cleared);   // 총괄 결정 1
  S.edDirty = false;
  openItem(S.idx, true);
};

/* ══════════════════════════ ② 하단 «상태 한 줄» ══════════════════════════
   40자 이내 한 문장. 그 사진에서 제일 급한 것 하나만 말하고, 나머지는 전부 풍선말(title)로.
   (전에는 이 자리에 세 마디를 «·» 로 이어 붙여 200자 가까이 찍었다 — 아무도 읽지 않았다.) */

const K = (k) => '<span class="k">' + k + "</span>";

/* 문턱값 — 2026-09-17 실측(cycles/260917_ui/cycle_2/stage1/thresholds.py).
   과일마다 «그 과일의 20%» 만 걸리는 값. 늘 켜져 있는 경고는 경고가 아니기 때문. */
const TH = {
  peach:     { dice: 0.786, added: 0.0067 },
  grape:     { dice: 0.900, added: 0.0126 },
  apple:     { dice: 0.674, added: 0.0058 },
  blueberry: { dice: 0.820, added: 0.0054 }
};
const TH_ASOF = "2026-09-17 · 4,727장으로 계산";
const TH_DEFAULT = { dice: 0.75, added: 0.01 };
const warnedTH = {};
function thOf(fruit) {
  if (TH[fruit]) return TH[fruit];
  if (fruit && !warnedTH[fruit]) {
    warnedTH[fruit] = 1;
    console.warn("[라벨링툴] «" + fruit + "» 는 경고 문턱을 아직 재지 않았습니다 — 옛 기본값("
      + TH_DEFAULT.dice + " / " + TH_DEFAULT.added + ")을 씁니다. 문턱표 기준: " + TH_ASOF);
  }
  return TH_DEFAULT;
}
/* merged_blob·filled_blob 은 «원본 라벨이 알끼리 붙어 그려졌다» 는 **표시 방식** 이야기다
   (사과 833장 = 83%). 사진이 잘못됐다는 뜻이 아니므로 경고에서 뺀다. */
const DISPLAY_FLAGS = ["merged_blob", "filled_blob"];
const splitFlags = (s) => String(s || "").replace(/;/g, "|").split("|").map((x) => x.trim()).filter(Boolean);

/* ─── 자동 점검이 붙인 영어 이름 → 한국어 (0917 사이클3 ②) ─── */
const FLAG_KO = {
  merged_blob:       ["알끼리 붙음", "여러 알이 한 덩어리로 칠해져 있습니다(표시 방식 — 틀린 것이 아닐 수 있습니다)"],
  filled_blob:       ["속이 찬 동그라미", "알 속을 통째로 채운 동그라미로 칠해져 있습니다"],
  fg_too_low:        ["마스크가 거의 빔", "칠한 넓이가 너무 작습니다 — 라벨이 빠졌을 수 있습니다"],
  fg_too_high:       ["너무 넓게 칠함", "칠한 넓이가 너무 큽니다 — 배경까지 칠했을 수 있습니다"],
  single_convex_blob:["통째로 한 덩어리", "사진 전체가 덩어리 하나로 칠해져 있습니다"],
  many_tiny:         ["자잘한 조각 많음", "아주 작은 조각이 많습니다 — 잡티일 수 있습니다"]
};
const flagKo = (f) => (FLAG_KO[f] ? FLAG_KO[f][0] : f);

/* ─── 사람 확정(0918 사이클2) ───
   방향 문서 §3-1: 모든 사진은 사람이 확정하기 전까지 «미확정» 이고, AI 제안은 미리 채워져 있다.
   그래서 하단 한 줄은 **«AI 제안: 제외(중복: X) — 맞으면 Enter»** 처럼 «지금 제안» 과 «확정 여부»
   를 한 문장으로 말한다. 확정된 사진은 «✔ 확정(이름·시각)». 이 줄이 Enter 의 설명서다. */
/* 0919 사이클5 2차 — 메모를 14자로 자르는 규칙 한 곳.
   ① 자른 자리에는 «…» 를 붙이고 ② 닫히지 않은 여는 괄호는 «)» 로 닫는다(1차 §1-3 ⑤). */
function cutNote(nt) {
  let w = String(nt).split("·")[0].trim();
  if (w.length > 14) w = w.slice(0, 14) + "…";
  const open = (w.match(/\(/g) || []).length - (w.match(/\)/g) || []).length;
  return open > 0 ? w + ")".repeat(open) : w;
}

/* 0919 사이클5 2차 — 조사 «(으)로». 앞말에 받침이 있으면 «으로», 없으면 «로».
   영문·숫자로 끝나는 말(«원본 OK»)은 «로» 다(1차 §1-3 ④: «원본 그대로 OK 으로 확정» 오기). */
function euroRo(w) {
  const ch = String(w).trim().slice(-1);
  const code = ch.charCodeAt(0);
  const hangul = code >= 0xac00 && code <= 0xd7a3;
  const jong = hangul ? (code - 0xac00) % 28 : 0;
  return (hangul && jong && jong !== 8) ? w + "으로" : w + "로";   // 받침 ㄹ(8)도 «로»
}

function confLine(m) {
  const c = m.confirmed;
  if (c) return { cls: "todo done", head: "✔ 확정 — " + statusKo(c.status)
    + " (" + (c.by || "익명") + " · " + String(c.at || "").slice(5, 16) + ")" };
  const ai = m.ai_status || m.status || "unreviewed";
  const who = (m.src === "ai") ? "AI 제안" : (ai === "unreviewed" ? "아직 판정 없음" : "지금 판정");
  // 0919 사이클5 2차 — 메모를 14자로 자르는 한 곳(위 why). 함수로 떼어 두 군데서 같은 규칙을 쓴다.
  if (ai === "unreviewed")
    return { cls: "todo go", head: "미확정 — 보고 " + K("1") + "~" + K("4") + " 로 확정" };
  // 0918 사이클2 **2차 검수**: 14자로 자르면 «중복: 20150919_1» 처럼 **반쪽 사진 이름**이 나온다
  // (실측 s5_live_guard C-0′ · 원래 메모는 «중복: 20150919_174151_image96»). §8 규칙 9 =
  // «사진 이름은 전체 이름으로». 이름이 들어가는 메모는 자르지 않고 낱말만 남긴다 —
  // 전문은 이 줄의 풍선말과 오른쪽 «이 사진» 칸에 그대로 있다.
  const nt = String(m.note || "");
  /* 0919 사이클5 **2차 검수**(1차 §1-3 ⑤): 14자에서 자를 때 **여는 괄호 안에서** 잘려
     «누락 복숭아 1개 추가(A — 맞으면 Enter» 처럼 괄호가 닫히지 않은 채 화면에 남았다
     (실측 1차 10단계). 자른 표는 «…» 로, 남은 여는 괄호는 «)» 로 닫는다(늘어나는 글자 ≤2자). */
  const why = !nt ? "" : (/^중복\s*:/.test(nt) ? "(중복)" : "(" + cutNote(nt) + ")");
  return { cls: "todo go", head: who + ": " + statusKo(ai) + why + " — 맞으면 " + K("Enter") };
}

/* ─── 0918 사이클4 결정 1: ② 상자 · ③ 번호도 «맞다/틀리다/고침» 을 가진다 ───
   그 작업의 하단 한 줄은 «AI 초벌이 몇 개인가 · 확정했나 · Enter 가 맞다» 세 가지만 말한다.
   나머지(왜·어떻게)는 전부 풍선말과 사용법 페이지에 있다 — 글자 예산을 지키기 위해서다. */


function taskCount(t) {
  if (t === "box") return (S.boxes || []).length;
  return (S.instN != null ? S.instN : (S.item && S.item.n_inst));
}

function taskConfLine(t, m) {
  const w = TASKWORD[t];
  const c = m[TASKFIELD[t]];
  if (c && c.status) {
    return { cls: "todo done",
             head: "✔ " + w + " 확정 — " + statusKo(c.status) + " (" + (c.by || "익명") + ")",
             tip: "이 사진의 " + w + " 는 사람이 확정했습니다: " + statusKo(c.status)
                + " · " + (c.by || "익명") + " " + (c.at || "")
                + ". 다시 확정하려면 Enter(맞다), 고쳤으면 저장(Ctrl+S)하면 «수정함» 으로 덮어씁니다."
                + " 마스크 확정과는 **따로** 셉니다." };
  }
  const n = taskCount(t);
  const seed = (t === "box" && m.ai_boxes_status !== "saved");
  const what = (n === null || n === undefined) ? "없음" : (n + "개");
  /* 0918 사이클4 **2차 검수**(실측 s1_flow 마-1·마-2): 상자가 **0개**인 사진에서도 «맞으면 Enter»
     라고 적혀 있었는데, 그 Enter 는 확정하지 않고 «초벌을 누르라» 는 안내만 띄운다. 처음 온 사람은
     «Enter 를 눌렀는데 아무 일도 안 난다» 고 읽는다. 0개일 때만 순서를 말한다(글자는 두 자 줄었다). */
  if (t === "box" && !n)
    return { cls: "todo go",
             head: w + " 0개 — «초벌» 을 누른 뒤 " + K("Enter"),
             tip: "이 사진에는 상자가 아직 하나도 없습니다. 왼쪽 «✨ 초벌» 로 마스크에서 네모를"
                + " 자동으로 만들거나(저장 전) 직접 드래그해 그린 뒤 Enter 를 누르면"
                + " «원본 OK» 로 확정됩니다. 지금 Enter 를 누르면 확정하지 않고 이 안내만 뜹니다." };
  /* 🔴 0919 «개수 세기» **사이클5**(사이클4 2차 §9-3 · 3차 §3): 사과의 ③ 번호는 **AI 가 만든 것이
     아니다** — 원본 마스크에 들어 있는 **정답 번호**를 그대로 보여 준다(`seed_source=gt_numbers`).
     그런데 이 줄이 «AI 초벌 번호 95개» 라고 적어 정답 라벨을 AI 산출물이라고 불렀다. 사람이
     «AI 가 만든 것이니 내가 고쳐야겠다» 고 읽으면 정답을 건드리게 된다.
     서버가 준 `seed_source` 가 `gt_numbers` 일 때만 낱말을 바꾼다(지어내지 않는다 · 옛 서버는
     그 칸이 없으므로 예전 문장 그대로). 글자 예산은 **그대로**다 —
     «AI 초벌 »(6자) ↔ «원본 정답 »(6자). */
  const gtNum = (t === "num" && m.counts && m.counts.seed_source === "gt_numbers");
  return { cls: "todo go",
           head: (gtNum ? "원본 정답 " : "AI 초벌 ") + w + " " + what + " — 맞으면 " + K("Enter"),
           /* 0919 사이클5 **2차**: 풍선말은 `title` 속성이라 마크다운이 그대로 «**» 로 보인다.
              화면 다른 풍선말과 같이 «» 로 감싼다(2자 줄었다 · 뜻은 그대로). */
           tip: (gtNum ? "이 " + w + " 는 AI 가 만든 것이 아니라 «원본 마스크에 들어 있는 정답"
                       + " 번호»입니다(고칠 일이 거의 없습니다). " : "")
              + "아직 이 사진의 " + w + " 는 «미확정» 입니다. 화면에 있는 "
              + (seed ? "초벌(저장 전)" : "저장된") + " " + w + " 가 맞으면 Enter 를 누르세요"
              + "(확정 = 원본 OK · 다음 사진으로 넘어갑니다). 틀리면 고쳐서 Ctrl+S 로 저장하면"
              + " 저장과 동시에 «수정함» 으로 확정됩니다." };
}

/* ─── 0919 «개수 세기» 사이클1 (지시서 §1-1) — 하단 «개수» 칸 ───
   글자는 «개수 16·15·20» 열한 자뿐이다(상자·번호·팀원 초벌). 상자와 번호가 다르면 가운뎃점을 «≠»
   로 바꾸고 — 사람이 «어느 쪽이 맞나» 를 보게 하는 것이 전부이고, 툴이 골라 주지 않는다(§1-2).
   🔴 0919 3차 전 **총괄 결정 4**(색 우선순위): **사람 확정 개수가 있으면 초록이 이기고** 어긋남은
      «≠» 글자로만 말한다. 전에는 노랑이 초록을 덮어서 «확정했는데도 초록이 아닌» 칸이 있었고,
      색 하나가 두 가지를 뜻했다(2차 검수 §4-4). 둘 다 확정해 **어긋난** 사진은 총괄 결정 1 로
      사람 확정 개수가 **비므로**(`source="conflict"`) 초록이 아니라 노랑 + «≠» 가 된다.
   나머지 설명(네 숫자가 각각 무엇인지·사람 확정 개수가 어디서 나왔는지)은 풍선말에.
   ⛔ 서버가 `counts` 를 모르면(옛 서버) «개수 ?·?·?» 로 둔다 — 정적 파일이 서버보다 먼저 나가는
      규칙(§8-10) 때문이다. 화면이 없는 숫자를 지어내면 안 된다. 물음표는 **«서버가 모른다»** 이고,
      «상자·번호·팀원이 다 없는 사진» 의 «개수 -·-·-» 와 구별된다(총괄 결정 4 · 글자 수는 같다).
   보이는 숫자는 **저장·확정된 값**이다. 지금 그리는 중인 상자는 저장(Ctrl+S) 뒤에 센다. */
const CNTSRC = { instances: "번호 확정", boxes: "상자 확정" };

function cntTip(c) {
  const n = (v) => (v === null || v === undefined ? "없음" : v + "개");
  const t = ["이 사진의 열매 개수 — 저장·확정된 값입니다(지금 그리는 중인 상자는 저장 뒤에 셉니다).",
             "상자(내가 저장한 것): " + n(c.boxes),
             // 0919 사이클2 논문대조 1차 ③ → **사이클4 M1 에서 사실을 갱신**: 전에는 «초벌은 늘
             // 4-연결» 이라고 적었는데, M1 뒤로 초벌은 박성문 님 워터셰드 번호본(블루베리·복숭아) ·
             // CERTH 정답 송이(포도) · 원본 정답 번호(사과) 를 **먼저** 쓰고 4-연결 CC 는 그것이
             // 없을 때만 쓰는 폴백이다. 그래서 화면이 단정하지 않고 **서버가 준 `seed_source`** 를
             // 그대로 말한다(옛 서버는 그 칸이 없으므로 그 때만 예전 문장을 쓴다 — 지어내지 않는다).
             c.seed_source
               ? "※ «✨ 초벌» 이 쓰는 것: " + (window.seedSrcKo ? window.seedSrcKo(c.seed_source) : c.seed_source)
                 + (c.seed_source === "cc4"
                    ? " — 검출 팀 도구(8-연결)와 다를 수 있습니다"
                    : " — 이 사진에 그 파일이 없으면 4-연결 CC 로 물러섭니다")
               : "※ «✨ 초벌» 이 마스크에서 센 개수는 4-연결 덩어리 기준입니다 —"
                 + " 검출 팀 도구(8-연결)와 다를 수 있습니다(번호가 있는 사과·블루베리는 번호 수를 씁니다)",
             "번호(열매 번호 라벨): " + n(c.instances) + " — «없음» 은 아직 세지 않았거나 번호본이 없는 사진입니다",
             "검출 팀 초벌 — 박성문 " + n(c.team_park) + " · 임성후 " + n(c.team_im)
               + " (읽기 전용 참고 값. 사람 확정 개수로는 쓰지 않습니다)"];
  if (c.conflict)                                  // 총괄 결정 1 — 어긋나면 확정 개수를 비운다
    t.push("사람 확정 개수: 비워 둡니다 — 상자와 번호를 둘 다 확정했는데 개수가 다릅니다."
           + " 툴은 고르지 않습니다(둘 중 틀린 쪽을 고쳐 다시 저장하면 «수정함» 으로 확정됩니다)."
           + " 고칠 때까지 이 사진은 counts.csv 의 «사람 확정만» 과 카운팅 지표에서 빠집니다.");
  else if (c.human === null || c.human === undefined)
    t.push("사람 확정 개수: 아직 없습니다 — 상자나 번호를 Enter 로 확정하면 그 개수가 곧 확정 개수입니다"
           + "(개수만 따로 치는 칸은 두지 않습니다).");
  else
    t.push("사람 확정 개수: " + c.human + "개 (" + (CNTSRC[c.source] || c.source) + "에서 나왔습니다)");
  return t.join("\n");
}

function renderCntChip() {
  const el = $("#cnts");
  if (!el) return;
  const m = S.item;
  const c = m && m.counts;
  if (!c) {                                  // 사진을 안 골랐거나 옛 서버 — 지어내지 않는다
    el.className = "cnts";
    // 총괄 결정 4: 옛 서버는 «?»(모른다) · 사진을 안 골랐으면 «-» — 글자 수는 둘 다 같다
    el.textContent = m ? "개수 ?·?·?" : "개수 -·-·-";
    el.title = m ? "서버가 아직 «개수» 를 모릅니다(담당자가 서버를 다시 켜면 나옵니다). 물음표는"
                 + " «서버가 모른다» 이고, «-» 는 «그 값이 없는 사진» 입니다."
                 : "목록에서 사진을 고르면 이 사진의 열매 개수가 나옵니다.";
    return;
  }
  const v = (x) => (x === null || x === undefined ? "-" : String(x));
  const team = c.team_park !== null && c.team_park !== undefined ? c.team_park : c.team_im;
  const ne = c.boxes !== null && c.boxes !== undefined
             && c.instances !== null && c.instances !== undefined && c.boxes !== c.instances;
  // 총괄 결정 4 — 사람 확정 개수가 있으면 **초록이 이긴다**(어긋남은 «≠» 글자로만 말한다)
  const hum = c.human !== null && c.human !== undefined;
  el.className = "cnts" + (hum ? " hum" : (ne ? " ne" : ""));
  el.textContent = "개수 " + v(c.boxes) + (ne ? "≠" : "·") + v(c.instances) + "·" + v(team);
  el.title = cntTip(c);
}
window.renderCntChip = renderCntChip;

function renderTodo() {
  renderCntChip();        // 어느 작업(마스크·상자·번호)에서도 **늘** 보이는 칸이라 맨 앞에서 그린다
  const el = $("#todo");
  if (!el) return;
  const m = S.item;
  if (!S.stem || !m) {
    el.className = "todo"; el.innerHTML = "목록에서 사진을 고르세요"; el.title = "";
    return;
  }
  // ②③ 에서는 그 작업의 줄만 보여 준다(마스크 판정 이야기는 ① 에서 한다) — 0918 사이클4
  const curT = curTask();
  if (curT !== "mask") {
    if (m.ai_boxes_status === undefined) {          // 옛 서버 — 새 칸을 모른다
      el.className = "todo warn";
      el.innerHTML = "서버가 아직 상자 확정을 모릅니다";
      el.title = "화면(정적 파일)은 새 판인데 서버가 옛 판입니다. 담당자가 서버를 다시 켠 뒤에"
               + " 쓰세요 — 지금 Enter 를 눌러도 아무것도 저장되지 않고 사진도 넘어가지 않습니다.";
      return;
    }
    const c = taskConfLine(curT, m);
    el.className = c.cls;
    el.innerHTML = c.head;
    el.title = c.tip;
    return;
  }
  // 0918 사이클2 (사이클1 3차 판정 ②-3): «저장»(Ctrl+S) 만 다음 장으로 안 넘어가는데 어디에도
  // 안 적혀 있었다. 저장 직후 6초 동안 이 줄이 알려 준다.
  if (S.savedAt && Date.now() - S.savedAt < 6000) {
    el.className = "todo done";
    el.innerHTML = "✅ 저장됨 — " + K(".") + " 로 다음 사진 · 맞으면 " + K("Enter") + " 로 확정";
    el.title = "수정본을 파일로 저장했습니다. 판정은 아직 «확정» 이 아닙니다 — Enter 나 1~4 를 누르면 확정됩니다.";
    return;
  }

  const nerr = ((S.errBy && S.errBy[S.stem]) || []).length;
  const sc = m.scores || {};
  const dice = sc.dice_vs_gt, added = sc.added_frac, missed = sc.missed_frac;
  const done = m.status && m.status !== "unreviewed";
  const th = thOf(S.fruit);
  const flags = splitFlags(m.inspection && m.inspection.suspect_flags);
  const real = flags.filter((f) => DISPLAY_FLAGS.indexOf(f) < 0);

  // 묶음(거의 같은 사진) 사정
  let dupN = 0, iAmRep = false, tidy = false, isDup = false;
  if (m.dup_group !== null && m.dup_group !== undefined) {
    isDup = true;
    const mem = m.dup_members || [], mst = m.dup_member_status || [];
    const others = mem.filter((s) => s !== m.dup_rep);
    const nEx = others.filter((s) => mst[mem.indexOf(s)] === "exclude").length;
    dupN = mem.length;
    iAmRep = !!(m.dup_rep && m.dup_rep === m.stem);
    tidy = others.length > 0 && nEx === others.length;      // 나머지가 전부 제외 = 정리 끝
  }

  /* 풍선말에 들어가는 «전문» — 화면에서 뺀 말은 전부 여기 남는다(잃지 않는다) */
  const full = [];
  if (m.confirmed) full.push("사람이 확정한 사진입니다 — " + statusKo(m.confirmed.status)
    + " · " + (m.confirmed.by || "익명") + " " + (m.confirmed.at || "")
    + ". 다시 확정하려면 1~4 나 Enter 를 누르세요(덮어씁니다).");
  else full.push("아직 «미확정» 입니다. 화면의 " + (m.src === "ai" ? "AI 제안" : "판정")
    + " 이 맞으면 Enter, 틀리면 1~4 를 누르세요. Enter·1~4 를 누른 것만 «확정» 으로 쌓입니다.");
  if (done) full.push("이미 판정된 사진입니다 — " + statusKo(m.status)
    + (m.status === "flag" && m.note ? " (" + String(m.note).slice(0, 80) + ")" : "")
    + ". 그대로 두려면 «.» 로 다음 사진.");
  if (S.noteBoxes && S.noteBoxes.length) full.push("노란 점선 = 라벨 안 된 열매 후보 "
    + S.noteBoxes.length + "곳 — 🔍 로 그 자리를 크게 본 뒤 붓으로 칠하고 N 으로 번호를 붙이세요 (0 = 원래 크기).");
  if (nerr) full.push("검출 팀이 찾은 번호 오류 " + nerr + "개 — «＃ 번호»(K) 에서 고치세요.");
  if (isDup && iAmRep && tidy) full.push("이 묶음의 대표(남길 장)입니다 — 나머지는 이미 제외됐습니다. 마스크만 보시면 됩니다.");
  else if (isDup) full.push("거의 같은 사진 묶음 #" + m.dup_group + " (" + dupN + "장)"
    + (done ? "" : " — 대표 한 장만 남기고 나머지는 4 제외. ▸ 로 오른쪽 «이 사진» 칸으로."));
  if (added != null && added > th.added) full.push("AI 가 라벨에 없는 열매를 찾았습니다 (AI추가 "
    + (added * 100).toFixed(1) + "%) — D 로 노랑을 확인하세요.");
  else if (dice != null && dice < th.dice) full.push("이 과일에서 AI 와 차이가 큰 편입니다 (Dice "
    + dice.toFixed(2) + ((missed != null && missed * 100 >= 0.1) ? " · AI누락 " + (missed * 100).toFixed(1) + "%" : "")
    + ") — D 로 차이를 보세요.");
  if (real.length) full.push("자동 점검이 의심: " + real.map(flagKo).join(", ")
    + " (영문 " + real.join(", ") + ") — 눈으로 확인하세요.");
  else if (flags.length && (S.gtIsInstance || S.inst)) full.push("원본 라벨이 알끼리 붙어 보입니다 — I 로 알마다 다른 색으로 보세요.");

  /* ─── 화면에는 제일 급한 것 하나만 (40자 이내) ─── */
  let cls = "todo go", head = "", btn = "";
  if (nerr) {
    cls = "todo warn";
    head = "⚠ 번호 오류 " + nerr + "개 — ＃ 번호에서 고치기";
  } else if (S.noteBoxes && S.noteBoxes.length) {
    cls = "todo warn";
    head = "⚠ 라벨 빠진 열매 후보 " + S.noteBoxes.length + "곳";
    btn = '<button class="todobtn" id="zoomnote" title="노란 점선 후보를 화면 가운데에 크게 띄웁니다(여러 곳이면 누를 때마다 다음 곳). 0 키로 원래 크기.">🔍</button>';
  } else if (isDup && !(iAmRep && tidy) && !done) {
    cls = "todo";
    head = "⧉ 묶음 " + dupN + "장 — 대표만 남기고 제외";
    btn = '<button class="todobtn" id="godup" title="오른쪽 «이 사진» 칸을 펴서 묶음 사진들과 «대표만 남기고 제외» 단추를 보여 줍니다.">▸</button>';
  } else if (m.confirmed) {
    const c = confLine(m); cls = c.cls; head = c.head;      // 0918 사이클2: 확정이 제일 센 말이다
  } else if (done) {
    const c = confLine(m); cls = c.cls; head = c.head;      // «AI 제안: 제외 — 맞으면 Enter»
  } else if (added != null && added > th.added) {
    cls = "todo warn";
    head = "⚠ AI 가 라벨에 없는 열매를 찾음 (D)";
  } else if (dice != null && dice < th.dice) {
    cls = "todo warn";
    head = "⚠ AI 와 차이가 큰 편 — D 로 확인";
  } else if (real.length) {
    cls = "todo warn";
    head = "⚠ " + flagKo(real[0]) + (real.length > 1 ? " 외 " + (real.length - 1) + "가지" : "");
  } else if (isDup && iAmRep && tidy) {
    cls = "todo done";
    head = "✅ 이 묶음의 대표 — 마스크만 보세요";
  } else {
    head = "빨강이 맞으면 " + K("1") + " · 고쳤으면 " + K("Ctrl") + "+" + K("S");
  }

  // 0918 사이클2: 급한 경고(번호 오류·누락 후보·묶음 …)가 있으면 그것이 머리말을 차지한다.
  // 그래도 **«확정했나 · Enter 가 맞다»** 는 늘 이 줄에 있어야 한다(그게 이 줄의 첫 임무다).
  if (!/확정|Enter/.test(head)) {
    head += m.confirmed
      ? ' <span class="cf on" title="' + escapeHtml("사람이 확정했습니다: " + statusKo(m.confirmed.status)
          + " · " + (m.confirmed.by || "익명") + " " + (m.confirmed.at || "")) + '">✔ 확정</span>'
      : ' <span class="cf" title="' + escapeHtml("아직 미확정입니다. " + (m.src === "ai" ? "AI 제안" : "지금 판정")
          + "(" + statusKo(m.ai_status || m.status || "unreviewed") + ")이 맞으면 Enter, 틀리면 1~4.")
        + '">미확정 · ' + K("Enter") + "=맞다</span>";
  }
  el.className = cls;
  el.innerHTML = head + btn;
  // 위에서 심어 둔 단추를 잇는다. innerHTML 을 다시 쓸 때마다 새로 잇는다.
  const gd = el.querySelector("#godup");
  if (gd) gd.onclick = () => { showDupBox(); gd.blur(); };
  const zn = el.querySelector("#zoomnote");
  if (zn) zn.onclick = () => { if (window.zoomToNote) window.zoomToNote(); zn.blur(); };
  // 화면에서 뺀 말은 전부 풍선말에 남긴다(경고 문턱이 언제 것인지도 — 데이터가 바뀌면 낡는 숫자다)
  el.title = full.join("\n")
    + ((cls === "todo warn" || (dice != null && added != null))
       ? "\n(경고 문턱 기준: " + TH_ASOF + (TH[S.fruit] ? "" : " · 이 과일은 아직 안 잼") + ")" : "");
}

/* 오른쪽 패널을 펴고 「이 사진」 칸의 묶음으로 데려가 2초쯤 노랗게 강조한다. */
function showDupBox() {
  const b = $("#dupbox");
  if (!b || b.style.display === "none") { flash("이 사진은 «거의 같은 사진 묶음» 에 들어 있지 않습니다", true); return; }
  setSideFold(false);
  const sec = $("#sec-item");
  if (sec) sec.open = true;
  b.scrollIntoView({ block: "nearest" });
  b.classList.add("hi");
  setTimeout(() => b.classList.remove("hi"), 2000);
}

/* ══════════════════════════ ⑧ Enter = «맞다» (사람 확정) ══════════════════════════
   방향 문서 §3-1 «AI 제안은 미리 채워져 Enter 한 번(맞다)으로 확정». 가드는 N1 과 같은 층이다:
     · 편집 화면이 아닐 때 · 입력칸(메모·이름·검색) 포커스 · Ctrl/Alt/Meta/Shift 와 함께
     · 안내 창이 열려 있을 때(위 ⑥ 의 capture 가로채기가 이미 멈춘다 — 여기서 한 번 더 본다)
     · 다각형(테두리 채움/빼기) 도구가 켜져 있을 때 → 그 Enter 는 app.js 의 «다각형 마침» 이다
     · ③ 번호 편집 모드일 때 → 그 Enter 는 app.js numKey 의 «붙이기» 다
     · 확인창(confirm/alert)이 떠 있는 동안에는 브라우저가 JS 를 멈춰 이 손잡이가 아예 안 불린다
   확정을 쓰는 곳은 app.js 의 confirmVerdict() 하나뿐이다(서버도 /api/status confirm:true 하나뿐). */
async function enterConfirm() {
  const m = S.item;
  if (!m || !S.stem || S.busy) return;
  // 0918 사이클4 결정 1: ② 상자 · ③ 번호에서는 Enter 가 **그 작업의** 확정이다.
  const curT = curTask();
  if (curT !== "mask") return enterConfirmTask(curT, m);
  if (S.edDirty && !confirmLeave()) return;      // 저장 안 한 붓질이 있으면 먼저 물어본다
  const mem = m.dup_members || [];
  const others = mem.filter((x) => x !== m.stem);
  if (m.dup_rep === m.stem && others.length) {
    // 묶음째 확정 — 확인창 **한 번**. 대표는 «자기 AI 제안 그대로», 나머지는 «제외» 로 확정한다.
    // 0918 «3차 판정 전 소수정»(N5): 전에는 AI 가 «문제 있음»(flag) 이라고 한 대표까지 «원본 OK» 로
    // 확정해 버려(실측 s3_guards 가드9), 사람이 보지도 않은 «문제 없음» 이 찍혔다. 한 장짜리 길
    // (아래 else)에서 Enter 는 «AI 제안 그대로» 이므로 묶음 길도 같은 뜻이어야 한다 —
    // flag 면 flag 로 확정하고(그 사진은 큐에 «고칠 것» 으로 남는다), 사람이 방금 고쳐 저장한
    // 사진이면 «수정함» 을 지켜 준다. 판정이 없는 사진(아직 안 봄)만 «쓴다(원본 OK)» 로 본다.
    const repv = ["ok", "fixed", "flag", "exclude"].indexOf(m.ai_status) >= 0 ? m.ai_status : "ok";
    // 0918 사이클2 **2차 검수**: 사람이 **이미 확정한** 구성원까지 «제외» 로 덮었다
    // (실측 s3_guards 가드10: 먼저 «원본 OK» 로 확정해 둔 장이 «제외» 가 됐다).
    // 서버가 주는 dup_member_confirmed 로 그 장들은 **건드리지 않고 건너뛴다** —
    // 기존 「묶음 제외」 단추(server.py api_exclude_group)가 «사람이 판정한 사진은 건너뛴다» 는
    // 것과 같은 규칙이다. 확인창도 몇 장을 건너뛰는지 말한다.
    const memConf = m.dup_member_confirmed || [];
    const keep = others.filter((x) => memConf[mem.indexOf(x)]);
    const todo = others.filter((x) => !memConf[mem.indexOf(x)]);
    if (!confirm("거의 같은 사진 묶음 " + mem.length + "장을 한 번에 확정합니다.\n\n"
        + "· 대표: " + euroRo(statusKo(repv)) + " 확정\n"    // 0919 사이클5 2차: «OK 으로» → «OK로»
        + "· 나머지 " + todo.length + "장: 제외로 확정\n"
        + (keep.length ? "· 그중 " + keep.length + "장은 사람이 이미 확정해서 그대로 둡니다\n" : "")
        + "\n원본 파일은 지워지지 않습니다. 계속할까요?")) return;
    const j = await confirmVerdict(repv, todo.map((x) => ({ stem: x, status: "exclude" })));
    if (!j) return;            // 0918 소수정(가드): 확정이 안 됐으면 **다음 사진으로 넘어가지 않는다**
    flash("묶음 " + mem.length + "장을 확정했습니다 (대표 1장 " + statusKo(repv) + " · "
          + todo.length + "장 제외"
          + (keep.length ? " · 이미 확정된 " + keep.length + "장은 그대로" : "") + ")");
  } else {
    const ai = m.ai_status || m.status || "unreviewed";
    if (ai === "unreviewed") { flash("이 사진에는 아직 판정이 없습니다 — 1~4 로 직접 고르세요", true); return; }
    const j = await confirmVerdict(ai);
    // 0918 «3차 판정 전 소수정»(가드): 전에는 확정이 **안 됐어도** 아래 nextItem() 이 돌아
    // 다음 사진으로 넘어갔다 — 옛 서버에서 Enter 를 열 번 누르면 열 장이 넘어가는데 확정은 0 이라
    // 사람이 «다 했다» 고 오해했다(실측 stage2/s8_guard_advance.py). 그 자리에 머문다.
    if (!j) return;
    flash("확정: " + statusKo(ai) + " (" + who() + ")");
  }
  nextItem(true);            // 확정이 **된** 때만 다음 장이 자동으로 뜬다(붓질을 버리지 않으므로 안 묻는다)
}

/* ②③ 의 Enter — «AI 초벌이 맞다» = 그 작업을 **원본 OK** 로 확정하고 다음 사진.
   고쳐서 저장하면 서버가 «수정함» 으로 확정한다(boxes.py·instances.py). 그래서 여기서 쓰는 값은
   `ok` 하나뿐이다. 저장 안 한 것이 있으면 확정하지 않는다 — 화면과 파일이 다른 채로 «맞다» 고
   찍으면 나중에 무엇을 확정한 것인지 알 수 없다. */
async function enterConfirmTask(t, m) {
  if (t === "num" && !S.inst) { flash(NUM_WHY, true); return; }
  if (t === "num" && S.numDirty) {
    flash("저장 안 한 번호 수정이 있습니다 — Ctrl+S 로 저장하면 «수정함» 으로 확정됩니다", true);
    return;
  }
  /* ② 상자에서 «맞다» 는 **화면에 있는 초벌을 그대로 쓰겠다** 는 뜻이다. 초벌은 파일이 아니라
     화면에만 있으므로(boxes_seed 는 저장하지 않는다 — 사이클1 규칙), 먼저 저장하지 않으면
     확정만 남고 내보낼 상자가 없다(실측 t1_api 라-2). 그래서 저장 → 확정(원본 OK) 순서다.
     서버는 저장할 때 «수정함» 으로 확정하지만 바로 뒤 «원본 OK» 가 덮는다 — 사람이 고친 것이
     아니라 초벌을 그대로 받은 것이므로 «원본 OK» 가 맞다.
     ③ 번호는 초벌이 이미 파일(원본 번호 마스크)이라 저장할 것이 없다 — 확정만 한다. */
  if (t === "box") {
    if (!(S.boxes || []).length) {
      flash("상자가 하나도 없습니다 — «초벌» 을 누르거나 직접 그린 뒤 Enter 를 누르세요", true);
      return;
    }
    if (typeof saveBoxes === "function") await saveBoxes();
    if (S.bDirty) return;                 // 저장이 실패했으면 확정하지 않는다
  }
  const j = await confirmVerdict("ok", null, TASKKIND[t]);
  if (!j) return;                       // 가드(옛 서버)·실패면 **다음 사진으로 넘어가지 않는다**
  flash(TASKWORD[t] + " 확정: 맞다 (" + who() + ")");
  nextItem(true);
}

function onEnterKey(e) {                    // 등록은 keys.js
  if (e.key !== "Enter") return;
  if ($("#view-edit").classList.contains("hidden")) return;
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
  const tour = $("#tour");
  if (tour && !tour.classList.contains("hidden")) return;
  if (S.tool === "polyadd" || S.tool === "polysub") return;    // 다각형 마침이 먼저다
  // 0918 사이클2 **2차 검수**는 ②③ 에서 Enter 를 아예 막았다 — 네모를 그리는 중에 Enter 를
  // 누르면 사람이 보지도 않은 **마스크** 판정이 확정으로 찍혔기 때문이다(s3_guards 가드3).
  // 0918 사이클4 결정 1: 이제 ②③ 의 Enter 는 **그 작업의** 확정이라 그 사고가 날 수 없다.
  // 다만 그 모드가 이미 Enter 를 쓰는 동안에는 그쪽이 먼저다:
  //   ③ 번호 — 그리다 만 영역이 있으면 Enter = «붙이기»(app.js numKey)
  //   ② 상자 — 드래그 중이면 그 네모를 마치는 중이다
  if (S.numMode && typeof hasPendingRegion === "function" && hasPendingRegion()) return;
  if (S.boxMode && S.drag) return;
  e.preventDefault();
  enterConfirm();
}


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { confirmVerdict, markTaskConfirmed, clearTaskConfirmed, cntSet, cntReload, doAction, renderTodo, renderCntChip, showDupBox, enterConfirm, FLAG_KO, onEnterKey });
})();
