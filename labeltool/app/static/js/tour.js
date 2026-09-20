/* tour — 첫 방문 안내 3장
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: ui.js 835-891·892-912줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   처음 온 사람에게 «그림판이라고 생각하세요» 3장을 보여 준다. 다시 보기는 ? 키·위쪽 «?».

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$;
const api = API.get, post = API.post;

/* ══════════════════════════ ⑥ 첫 방문 안내 — 3장 (그림판 비유) ══════════════════════════ */

/* 0918 «그림판» 재배치: 화면이 통째로 바뀌었으므로 키를 올려 모두에게 **한 번만** 다시 띄운다.
   0920 «쉬움 모드»: 단추가 줄고 오른쪽 버튼·확대 단추가 생겼다 → 키를 다시 올린다. */
const TOUR_KEY = "tour_seen_260920_easy";
const SW = (c) => '<span class="sw" style="background:' + c + '"></span>';
const KY = (k) => '<span class="key">' + k + "</span>";
const STEPS = [
  ["1. 그림판이라고 생각하세요",
   "<p>사진마다 «열매를 칠한 그림(칠한 영역)» 이 맞는지 보고, 틀렸으면 고치는 툴입니다. 한 장에 보통 10~30초입니다.</p>"
   + "<ul><li><b>왼쪽 = 도구 상자</b> — 붓·지우개·다각형. 맨 위 세 칸에서 <b>무슨 일을 할지</b> 고릅니다"
   + " (🎨 칠한 영역 · ▭ 상자 · ＃ 번호).</li>"
   + "<li><b>가운데 = 사진</b> — 휠 또는 오른쪽 아래 " + KY("＋") + KY("－") + KY("맞춤") + " 단추로 확대, "
   + KY("Space") + "+드래그로 이동.</li>"
   + "<li><b>아래 = 판정</b> — 한 줄 상태와 단추 다섯 개. 늘 화면 안에 있습니다.</li>"
   + "<li><b>오른쪽 = 접힌 칸</b> — " + KY("▸") + " 를 누르면 겹(레이어)·이 사진의 정보·자주 안 쓰는 단추가 나옵니다.</li></ul>"
   + "<p><b>지금은 «🙂 쉬움 모드» 입니다</b> — 꼭 필요한 단추만 보입니다. 위쪽 오른쪽의 그 단추를 누르면 "
   + "<b>«🛠 전문가 모드»</b> 가 되어 테두리 채움·초벌 출처·AI로 교체 같은 칸이 다시 나옵니다. "
   + "그림판과 같게 <b>마우스 오른쪽 버튼으로 끌면 지우개</b>입니다(자동채움일 때는 자동지움).</p>"
   + "<p><b>원본은 절대 안 바뀝니다.</b> 팀 표준 데이터셋은 <b>읽기만</b> 하고, 고친 것은 전부 다른 폴더에 쌓입니다. "
   + "먼저 오른쪽 위 <b>«내 이름»</b> 칸에 이름을 한 번 적어 주세요.</p>"],
  ["2. 색 읽는 법 — 사진 오른쪽 위의 칩",
   "<p>사진 <b>오른쪽 위</b>에 지금 켜져 있는 겹이 작은 칩으로 있습니다. <b>칩을 누르면 그 색이 꺼지고 켜집니다.</b></p>"
   + "<ul><li>" + SW("#e8443a") + "<b>원본</b> — 원래 데이터셋에 있던 라벨. 이게 맞는지 보는 게 검수입니다.</li>"
   + "<li>" + SW("#2f7de1") + "<b>AI</b> — AI 가 1차로 그린 것.</li>"
   + "<li>" + SW("#2fb562") + "<b>수정</b> — 내가 고친 것.</li>"
   + "<li>" + SW("linear-gradient(90deg,#ffd400 50%,#ff35d0 50%)") + "<b>차이</b> (" + KY("D") + ") — "
   + "노랑은 AI 만 찾은 곳 = <b>라벨이 빠졌을 후보</b>입니다.</li></ul>"
   + "<p>사진 <b>왼쪽 위</b>는 비워 두었습니다 — 거기서도 붓질을 시작할 수 있게. "
   + "② 상자·③ 번호가 켜져 있으면 거기에 «… 중» 이라고 적히고, 그때는 붓질이 안 됩니다.</p>"],
  ["3. 다 봤으면 — " + KY("Enter") + " 가 «맞다» 입니다",
   "<p>사진 <b>바로 아래</b>에 상태 한 줄과 판정 단추가 있습니다. 노트북 화면에서도 스크롤 없이 늘 보입니다.</p>"
   + "<ul><li>" + KY("1") + " <b>원본 OK</b> — 빨강이 잘 맞을 때</li>"
   + "<li>" + KY("2") + " <b>AI로 교체</b> — 파랑이 확실히 나을 때</li>"
   + "<li>" + KY("Ctrl") + "+" + KY("S") + " <b>저장</b> — 내가 고친 하늘색을 저장. "
   + "② 상자·③ 번호를 고르면 이 칸이 그대로 <b>«상자 저장»·«번호 저장»</b> 이 됩니다.</li>"
   + "<li>" + KY("3") + " <b>문제</b> — 이상한데 내가 못 고치겠을 때</li>"
   + "<li>" + KY("4") + " <b>제외</b> — 안 쓸 사진(거의 같은 사진 등)</li></ul>"
   + "<p>사진 넘기기는 " + KY(",") + " 와 " + KY(".") + " · 이 안내 다시 보기 " + KY("?") + " 또는 위쪽 «?».</p>"
   + "<p>«제외» 로 판정한 사진은 그림을 고쳐 저장해도 <b>«제외» 그대로</b>입니다. "
   + "다시 쓰려면 " + KY("1") + " <b>원본 OK</b> 를 누르세요. 더 자세한 것은 아래 «사용법» 을 보세요.</p>"]
];

let ti = 0;
function tourShow(i) {
  ti = Math.max(0, Math.min(STEPS.length - 1, i));
  $("#tour-t").textContent = STEPS[ti][0];
  $("#tour-b").innerHTML = STEPS[ti][1];
  $("#tour-n").textContent = (ti + 1) + " / " + STEPS.length;
  $("#tour-prev").disabled = ti === 0;
  $("#tour-next").textContent = ti === STEPS.length - 1 ? "다 봤어요 ✓" : "다음 ▶";
}
function tourOpen() { $("#tour").classList.remove("hidden"); tourShow(0); }
function tourClose() {
  $("#tour").classList.add("hidden");
  try { if ($("#tour-never").checked) localStorage.setItem(TOUR_KEY, "1"); } catch (e) {}
}
$("#tour-x").onclick = tourClose;
$("#tour-prev").onclick = () => tourShow(ti - 1);
$("#tour-next").onclick = () => { if (ti === STEPS.length - 1) tourClose(); else tourShow(ti + 1); };
$("#tour").onclick = (e) => { if (e.target === $("#tour")) tourClose(); };
$("#btn-tour").onclick = () => { tourOpen(); $("#btn-tour").blur(); };


// 2026-09-17 2차 검수에서 찾은 버그: 안내 창이 편집 화면 «위에» 떠 있어도 app.js 의 단축키가
// 그대로 살아 있어, 안내를 읽다가 1 을 누르면 뒤의 사진에 진짜 판정이 나갔다.
// → 안내 창이 열려 있는 동안에는 «가로채기(capture)» 단계에서 키를 멈춘다. Esc·? 만 통과시킨다.
function onTourCaptureKey(e) {              // 등록은 keys.js (가로채기 단계)
  const tour = $("#tour");
  if (tour && !tour.classList.contains("hidden") && e.key !== "Escape" && e.key !== "?") {
    e.stopImmediatePropagation();
  }
}

function onTourKey(e) {                     // 등록은 keys.js
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  if (e.key === "?") { e.preventDefault(); tourOpen(); $(".shortcut-panel").open = true; }
  else if (e.key === "Escape" && !$("#tour").classList.contains("hidden")) tourClose();
}

let seen = "1";
try { seen = localStorage.getItem(TOUR_KEY); } catch (e) {}
if (!seen) tourOpen();


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { tourOpen, tourClose, onTourCaptureKey, onTourKey });
})();
