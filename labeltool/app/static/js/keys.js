/* keys — 단축키 — 표 한 장과 손잡이 전부
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 1207-1259줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   키→동작 표(KEYS)가 이 툴의 단축키 «한 곳» 이고, keydown/keyup 손잡이도 전부 여기서 등록한다. 도움말(help.html)의 «단축키 한 장» 과 어긋나면 tests/unit/u7_keys_doc.py 가 잡는다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

(function () {
const KEYS = [
  { key: "Enter", ko: "다 했어요 — 화면 아래 줄에 적힌 제안이 맞다(다음 사진으로)", at: "counts.js",
    src: 'if (e.key !== "Enter") return;' },
  { key: ",", ko: "이전 사진", at: "keys.js", src: 'case ",":' },
  { key: ".", ko: "다음 사진", at: "keys.js", src: 'case ".":' },
  { key: "1", ko: "원본 그대로 OK", at: "keys.js", src: 'case "1":' },
  { key: "2", ko: "AI 제안으로 교체", at: "keys.js", src: 'case "2":' },
  { key: "3", ko: "문제 있음", at: "keys.js", src: 'case "3":' },
  { key: "4", ko: "제외", at: "keys.js", src: 'case "4":' },
  { key: "Ctrl+S", ko: "지금 하는 일의 저장(칠한 영역 수정본 · 상자 · 번호)", at: "keys.js",
    src: 'e.key === "s" || e.key === "S"' },
  { key: "Ctrl+Z", ko: "되돌리기(칠한 영역 · 상자 · 번호)", at: "keys.js", src: 'e.key === "z" || e.key === "Z"' },
  { key: "Ctrl+Y", ko: "다시 실행(칠한 영역 · 번호 — 상자에는 없다)", at: "keys.js", src: 'e.key === "y" || e.key === "Y"' },
  { key: "B", ko: "붓", at: "keys.js", src: 'case "b":' },
  { key: "E", ko: "지우개", at: "keys.js", src: 'case "e":' },
  { key: "P", ko: "다각형 채우기", at: "keys.js", src: 'case "p":' },
  { key: "O", ko: "다각형 빼기", at: "keys.js", src: 'case "o":' },
  { key: "F", ko: "스마트 채우기", at: "keys.js", src: 'case "f":' },
  { key: "G", ko: "스마트 삭제", at: "keys.js", src: 'case "g":' },
  { key: "[", ko: "붓 작게", at: "keys.js", src: 'case "[":' },
  { key: "]", ko: "붓 크게", at: "keys.js", src: 'case "]":' },
  { key: "I", ko: "알마다 다른 색(사과)", at: "keys.js", src: 'case "i":' },
  { key: "D", ko: "차이 보기 (번호 편집 모드에서는 지우기)", at: "keys.js", src: 'case "d":' },
  { key: "X", ko: "상자 모드 켜고 끄기 (번호 편집 모드에서는 나누기)", at: "keys.js", src: 'case "x":' },
  { key: "V", ko: "상자 고르기", at: "keys.js", src: 'case "v":' },
  { key: "Del", ko: "고른 상자 삭제", at: "keys.js", src: 'case "Delete":' },
  { key: "K", ko: "열매 번호 편집 켜고 끄기", at: "keys.js", src: 'case "k":' },
  { key: "J", ko: "번호 레이어 켜고 끄기", at: "keys.js", src: 'case "j":' },
  { key: "0", ko: "화면에 맞춤", at: "keys.js", src: 'case "0":' },
  { key: "Esc", ko: "다각형 취소 · 안내 창 닫기", at: "keys.js", src: 'case "Escape":' },
  { key: "Space", ko: "누른 채 드래그 = 화면 이동", at: "keys.js", src: 'e.code === "Space"' },
  { key: "Q", ko: "보기 전환 — 원본만 → 칠한 영역만 → 겹쳐", at: "view.js", src: 'e.key !== "q" && e.key !== "Q"' },
  { key: "?", ko: "안내와 단축키 표 보기", at: "tour.js", src: 'e.key === "?"' },
  { key: "M", ko: "번호 합치기(고른 뒤)", at: "instances.js", src: 'if (k === "m") {' },
  { key: "N", ko: "번호 새로 붙이기(그린 뒤)", at: "instances.js", src: 'if (k === "n") {' }
];
function renderKeyTable(root) {
  root.innerHTML = '<table><thead><tr><th>키</th><th>하는 일</th></tr></thead><tbody>'
    + KEYS.map(r => '<tr><td>' + r.key.split('+').map(k => '<kbd>' + k + '</kbd>').join('+')
      + '</td><td>' + r.ko + '</td></tr>').join('') + '</tbody></table>';
}
document.querySelectorAll('[data-key-table]').forEach(renderKeyTable);
if (typeof UI === "undefined") return; // 사용법에서도 같은 표만 읽는다.

/* ── 먼저 온 파일에서 가져오는 것 (위에서 아래로) ── */
const $ = UI.$, $$ = UI.$$, flash = UI.flash, ensureWho = UI.ensureWho, onWhoKey = UI.onWhoKey, fitView = UI.fitView, onViewModeKey = UI.onViewModeKey, setTool = UI.setTool, applyPolygon = UI.applyPolygon, paintGtLayer = UI.paintGtLayer, boxUndo = UI.boxUndo, saveBoxes = UI.saveBoxes, delSelBox = UI.delSelBox, setBTool = UI.setBTool, numKey = UI.numKey, numUndo = UI.numUndo, numRedo = UI.numRedo, saveInstances = UI.saveInstances, setNumMode = UI.setNumMode, doAction = UI.doAction, enterConfirm = UI.enterConfirm, onEnterKey = UI.onEnterKey, prevItem = UI.prevItem, nextItem = UI.nextItem, onTourCaptureKey = UI.onTourCaptureKey, onTourKey = UI.onTourKey;
const api = API.get, post = API.post;

/* ------------------------------------------------------------- 단축키 */
window.addEventListener("keydown", (e) => {
  if (e.code === "Space") { S.spaceDown = true; }
  const t = e.target.tagName;
  if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA") return;
  // 0918 사이클3 **2차 검수**(화면-7-C): 이 줄이 **Ctrl 갈래 아래**에 있어서, 편집 화면이 아닌
  // 곳(목록·진행 현황·새 «데이터 정리» 탭)에서 Ctrl+S 를 눌러도 doAction("fixed") 가 돌았다 —
  // 마지막에 열었던 사진에 마스크와 판정이 **말없이** 저장됐다(실측: 210629-t1-04 의 판정이
  // «문제 있음» → «수정함» 으로 바뀌고 AI 3회 검수 기록이 prev 로 밀렸다). «데이터 정리» 탭은
  // 하는 일이 «저장» 이라 Ctrl+S 를 누르기 아주 쉽다. 편집 화면에서만 듣게 한 줄을 올린다.
  if ($("#view-edit").classList.contains("hidden")) return;
  if (e.ctrlKey || e.metaKey) {
    if (e.key === "z" || e.key === "Z") { e.preventDefault(); if (S.numMode) numUndo(); else if (S.boxMode) boxUndo(); else $("#undo").click(); }
    else if (e.key === "y" || e.key === "Y") { e.preventDefault(); if (S.numMode) numRedo(); else if (S.boxMode) flash("상자에는 다시 실행이 없습니다", true); else $("#redo").click(); }
    else if (e.key === "s" || e.key === "S") { e.preventDefault(); if (S.numMode) saveInstances(); else if (S.boxMode) saveBoxes(); else doAction("fixed"); }
    return;
  }
  if (S.numMode && numKey(e)) return;        // 모드가 켜져 있을 때만 X = 나누기 (상자 모드 토글과의 충돌 해결)
  switch (e.key) {
    case "[": $("#brush").value = Math.max(2, S.brush - 4); $("#brush").oninput({ target: $("#brush") }); break;
    case "]": $("#brush").value = Math.min(200, S.brush + 4); $("#brush").oninput({ target: $("#brush") }); break;
    case ",": prevItem(); break;
    case ".": nextItem(); break;
    case "b": case "B": setTool("brush"); break;
    case "e": case "E": setTool("erase"); break;
    case "p": case "P": setTool("polyadd"); break;
    case "o": case "O": setTool("polysub"); break;
    case "f": case "F": setTool("smartadd"); break;
    case "g": case "G": setTool("smartsub"); break;
    case "i": case "I":
      if (S.gtIsInstance) { $("#l-inst").checked = !$("#l-inst").checked; paintGtLayer(); S.dirty = true; }
      break;
    case "d": case "D": if (!$("#l-diff").disabled) { $("#l-diff").checked = !$("#l-diff").checked; S.dirty = true; } break;
    case "x": case "X":
      if (S.numMode) break;                  // 번호 편집 모드에서는 위 numKey() 가 «나누기» 로 가져간다
      $("#box-mode").checked = !$("#box-mode").checked; $("#box-mode").onchange(); break;
    case "j": case "J":
      if (S.inst) { $("#l-num").checked = !$("#l-num").checked; S.dirty = true; } break;
    case "k": case "K": if (S.inst) setNumMode(!S.numMode); break;
    case "v": case "V": if (S.boxMode) setBTool("pick"); break;
    case "Delete": case "Backspace": if (S.boxMode) { delSelBox(); e.preventDefault(); } break;
    case "0": fitView(); break;
    case "1": doAction("ok"); break;
    case "2": if (!$("#btn-ai").disabled) doAction("ai"); break;
    case "3": doAction("flag"); break;
    case "4": doAction("exclude"); break;
    case "Enter":
      if (S.tool === "polyadd" || S.tool === "polysub") applyPolygon(S.poly, S.tool === "polyadd" ? 1 : 0);
      break;
    case "Escape": S.poly = []; S.dirty = true; break;
  }
});
window.addEventListener("keyup", (e) => { if (e.code === "Space") S.spaceDown = false; });


/* ══════════════════════════ §1. 단축키 표 — 이 표가 «한 곳» 이다 ══════════════════════════
   키를 더하거나 뺄 때는 **이 표와 아래 손잡이를 같이** 고친다. 어긋나면 시험이 잡는다:
     · tests/unit/u7_keys_doc.py — 이 표 ↔ 도움말(help.html «단축키 한 장») ↔ 손잡이 코드 대조
     · tests/sim/modesim.js 31항목 — 손잡이가 모드마다 제 갈래로 가는지(글자를 떼어 내 돌린다)
   칸: key = 화면·도움말에 적는 키 · ko = 뜻(도움말과 같은 말) · at = 손잡이가 있는 파일 ·
       src = 그 파일에 **반드시 있는 글자**(u7 이 이것으로 «표와 코드가 같은가» 를 본다)
   ⚠ 손잡이 자체는 아래 §2 에 쪼개기 **전 글자 그대로** 있다(동작 무변경). 이 표는 «무엇이 있나» 를
     한 장으로 보여 주고, 도움말·코드와 어긋나지 않게 묶어 두는 것이 일이다.                   */


/* ══════════════════ §2. 다른 파일에 있는 키 손잡이도 여기서 등록한다 ══════════════════
   쪼개기 전 순서 그대로다(app.js 의 keydown·keyup 이 먼저, 그다음 ui.js 순서: Q → 안내 가로채기
   → ?·Esc → 이름 묻기 → Enter). 가로채기(capture) 단계가 먼저 도는 것은 브라우저가 정한다. */
window.addEventListener("keydown", onViewModeKey);              // Q — 보기 전환      (view.js)
window.addEventListener("keydown", onTourCaptureKey, true);     // 안내 창이 열려 있으면 키를 멈춘다 (tour.js)
window.addEventListener("keydown", onTourKey);                  // ? · Esc            (tour.js)
window.addEventListener("keydown", onWhoKey, true);             // 첫 판정 때 이름 묻기 (api.js)
window.addEventListener("keydown", onEnterKey);                 // Enter = 확정        (counts.js)


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { KEYS });
})();
