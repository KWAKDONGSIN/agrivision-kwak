/* easy — «쉬움 모드» 스위치와 사진 확대 단추 (그림판처럼 단순하게)
   작성: 2026-09-20 (요청: 랩미팅 전 «좀 쉽게» · 박성문 «봤는데 어려움»)

   무엇을 하나
     · body 에 `easy` 딱지를 붙였다 뗐다 한다. 숨는 칸은 style.css 의 `body.easy .adv` 한 줄이 정한다.
       → **자바스크립트가 단추를 지우지 않는다.** 전문가 모드로 바꾸면 그대로 다시 나온다.
     · 숨은 도구를 고른 채 쉬움으로 바꾸면 보이는 도구로 옮겨 준다(안 보이는 도구를 쥐고 있지 않게).
     · 사진 위 확대 ＋/－/맞춤 3칸. 휠·0 키를 모르는 사람을 위한 것이고, 계산은 휠과 같다.

   단축키는 쉬움 모드에서도 **전부 그대로** 산다(숨긴 도구도 키로는 쓸 수 있다).
   의존은 «위에서 아래로» — 이 파일이 맨 마지막이라 UI·S 를 그냥 쓴다.
*/
"use strict";

(function () {
const $ = UI.$, $$ = UI.$$, cv = UI.cv;
const KEY = "easy_mode_260920";

/* ══════════════════════════ 쉬움 / 전문가 ══════════════════════════ */
function isEasy() {
  try { return localStorage.getItem(KEY) !== "0"; } catch (e) { return true; }   // 기본 = 쉬움
}

function apply(easy) {
  document.body.classList.toggle("easy", easy);
  const b = $("#easytgl");
  if (b) {
    b.textContent = easy ? "🙂 쉬움 모드" : "🛠 전문가 모드";
    b.title = easy
      ? "지금은 쉬움 모드 — 꼭 필요한 단추만 보입니다. 누르면 전문가 모드(테두리 채움·초벌 출처·AI로 교체 …)로 바뀝니다."
      : "지금은 전문가 모드 — 모든 단추가 보입니다. 누르면 쉬움 모드로 돌아갑니다.";
  }
  if (easy) keepVisibleTool();
  $$(".rail-details").forEach(el => el.open = !easy);
  // 도구 상자 맨 아래 한 줄 — 쉬움에서는 «그림판처럼» 쓰는 법, 전문가에서는 예전 글 그대로
  const rh = $("#railhint");
  if (rh) rh.innerHTML = easy ? "왼쪽=칠하기 · 오른쪽=지우기<br>휠=확대 · 0 맞춤" : "휠 확대 · 0 맞춤";
  UI.resizeCanvas && UI.resizeCanvas();
}

/* 숨은 도구(테두리 채움·빼기·자동지움)를 쥔 채로 쉬움이 되면 보이는 첫 도구로 옮긴다. */
function keepVisibleTool() {
  const cur = document.querySelector(".tool.on");
  if (!cur || !cur.classList.contains("adv")) return;
  const next = $$(".tool").find((t) => !t.classList.contains("adv") && !t.classList.contains("hidden"));
  if (next) next.click();
}

$("#easytgl").onclick = () => {
  const easy = !document.body.classList.contains("easy");
  try { localStorage.setItem(KEY, easy ? "1" : "0"); } catch (e) {}
  apply(easy);
  $("#easytgl").blur();
  UI.flash(easy ? "쉬움 모드 — 자주 쓰는 단추만 보입니다" : "전문가 모드 — 모든 단추가 보입니다");
};

/* ══════════════════════════ 확대 ＋ － 맞춤 ══════════════════════════ */
/* 휠과 같은 계산(view.js 의 wheel 손잡이)이되, 가운데를 기준으로 한 번에 1.25배. */
function zoomBy(k) {
  if (!S.img) return;
  const r = cv.getBoundingClientRect();
  const mx = r.width / 2, my = r.height / 2;
  const ns = Math.max(0.03, Math.min(30, S.view.s * k));
  S.view.tx = mx - (mx - S.view.tx) * (ns / S.view.s);
  S.view.ty = my - (my - S.view.ty) * (ns / S.view.s);
  S.view.s = ns; S.dirty = true;
}

$("#zoomin").onclick = () => { zoomBy(1.25); $("#zoomin").blur(); };
$("#zoomout").onclick = () => { zoomBy(1 / 1.25); $("#zoomout").blur(); };
$("#zoomfit").onclick = () => { UI.fitView(); $("#zoomfit").blur(); };

/* 상자 전용 화면(/box)에서는 «초벌 출처» 가 그 일의 핵심이다 — 쉬움 모드에서도 남겨 둔다.
   (검출 팀 임성후·박성문이 이 화면만 쓴다. 0919 «상자 툴을 따로» 참조) */
if (location.pathname === "/box") {
  const sel = $("#boxseedsrc");
  if (sel) sel.classList.remove("adv");
}

function renderEasyProgress() {
  const f = S.progressFruit;
  if (!f || f.fruit !== S.fruit) { $("#edit-progress").textContent = "진행 상황을 불러오는 중…"; return; }
  const n = S.numMode ? f.n_confirmed_instances : S.boxMode ? f.n_confirmed_boxes : f.n_confirmed;
  $("#edit-progress").textContent = `${UI.FRUIT_KO[S.fruit]} 전체 ${f.n_images}장 · 현재 목록 ${S.listTotal || S.items.length}장 중 ${(S.page - 1) * 120 + S.idx + 1}번째 · 다 본 사진 ${n || 0}장`;
  $("#edit-guide").textContent = S.numMode ? "① 열매 번호를 고치고 → ② 아래 «번호 저장»을 누르세요."
    : S.boxMode ? "① 상자를 고치고 → ② 아래 «상자 저장»을 누르세요."
    : "① 잘못된 부분을 붓/지우개로 고친 뒤 «저장» → ② 아래 «다 했어요»를 누르세요.";
}
async function loadTeamGrape() {
  const el = $("#team-grape-list");
  const j = await API.get("/api/team_review?fruit=grape");
  if (!j?.ok) { el.textContent = "팀원 목록을 읽지 못했습니다."; return; }
  el.replaceChildren();
  j.groups.forEach(g => {
    const h = document.createElement("h3"); h.textContent = `${g.source} · ${g.stems.length}장`; el.append(h);
    g.stems.forEach(stem => {
      const b = document.createElement("button"); b.textContent = stem;
      b.onclick = async () => {
        if (!UI.confirmLeave()) return;
        $("#fruit").value = "grape"; S.fruit = "grape"; UI.loadBrush();
        $("#f-status").value = "all"; $("#f-sort").value = "name"; $("#f-q").value = stem;
        ["#f-dup", "#f-suspect", "#f-prop"].forEach(s => $(s).checked = false);
        S.flag = ""; S.confFilter = ""; S.confBy = "";
        await UI.loadList();
        const i = S.items.findIndex(it => it.stem === stem);
        if (i < 0) { location.href = "/team_photo/grape/" + encodeURIComponent(stem); return; }
        await UI.openItem(i, true);
      };
      el.append(b);
    });
  });
}
async function loadTeamSuspects() {
  const fruit = S.fruit, stem = S.stem;
  $("#team-suspect-control").hidden = fruit !== "apple";
  S.teamSuspects = [];
  if (fruit !== "apple") return;
  const j = await API.get("/api/team_review?fruit=apple&stem=" + encodeURIComponent(stem));
  if (S.fruit !== fruit || S.stem !== stem) return;
  S.teamSuspects = j?.ok ? j.rows : [];
  $("#team-suspect-control").title = S.teamSuspects.map(r => `${r.source} · #${r.inst_ids} · ${UI.VERDICT_KO[r.verdict] || r.verdict}`).join("\n");
  S.dirty = true;
}
$("#btn-confirm").onclick = () => {
  if (S.busy || !S.stem) return;
  if ((S.numMode && UI.hasPendingRegion()) || (S.poly || []).length || S.drag) {
    UI.flash("그리는 중입니다. 먼저 그리기를 마치고 저장하세요.", true); return;
  }
  UI.ensureWho(); UI.enterConfirm();
};
$("#team-suspect").onchange = () => { S.dirty = true; };
Object.assign(UI, { renderEasyProgress, loadTeamGrape, loadTeamSuspects });
apply(isEasy());
})();
