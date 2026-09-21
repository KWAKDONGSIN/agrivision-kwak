/* dirtymark — 저장하지 않은 작업이 있으면 파일 이름 옆에 «*» 를 띄우고 그 «저장» 단추를 노랗게 두른다
   작성: 2026-09-21 (260921 편의·안정성 사이클 · U1)

   왜 있나
     S1~S6 은 «저장이 실패하는 것» 을 막았다. 그래도 제일 흔한 사고가 하나 남는다 —
     **저장을 아예 안 누르고 다음 장으로 가는 것.** 지금 «저장 안 됨» 이 적히는 자리는
     도구 상자의 «작업 정보» 접힌 칸뿐이다(boxes.js boxInfo · instances.js numInfo).
     칠한 영역에는 그 표시조차 없다. 사람은 캔버스를 보고 있으므로 셋 다 눈에 안 들어온다.
     S4(창 닫기 경고)·S5(임시 백업)는 **사고가 난 뒤** 에 쓰는 장치라 이 구멍을 못 막는다.
     → 메모장·포토샵의 관습대로, 저장 전에는 파일 이름 옆에 «*» 를 세워 둔다.

   지킨 것
     · **요소 id 를 하나도 안 바꿨다.** 새로 만드는 것은 `#dirtystar` 하나뿐이고,
       그것도 여기서 화면에 끼운다(index.html 은 script 한 줄만 늘었다).
     · `#stemname` **안** 에 넣지 않는다 — list.js 의 `textContent = meta.stem` 이 매번 자식을
       지우고, mobile.js 의 MutationObserver 가 그때마다 헛돈다. 그래서 **옆에** 형제로 세운다.
     · 저장 단추는 `disabled` 도 배경색도 건드리지 않는다. 노란 테두리(box-shadow)만 두른다 —
       칸 크기가 안 변하고(자리가 안 밀린다), 옆의 «문제»(연주황)와 색이 안 겹친다.
       노란색은 «*» 와 같은 색이다 — 두 표시가 **같은 뜻**임을 색으로 묶는다.
     · S6 의 `.saving` 딱지와 겹쳐도 괜찮다(그쪽은 opacity 만 건드린다).

   왜 0.2초마다 보나
     `S.edDirty`·`S.bDirty`·`S.numDirty` 를 올렸다 내리는 자리가 40군데가 넘는다(붓질·다각형·
     상자 8가지 손질·번호 6가지·세 저장의 성공/실패 갈래·사진 열기·과일 바꾸기…). 그 모두에
     «표시를 갱신하라» 한 줄씩을 더하면 한 자리만 빠뜨려도 **거짓말하는 표시**가 된다 —
     «*» 가 없는데 저장이 안 된 상태가 제일 나쁘다. 그래서 자리마다 붙이지 않고 값을 본다.
     바뀐 것이 없으면 화면을 한 칸도 안 건드린다(아래 `last`).

   의존은 «위에서 아래로» — 이 파일이 맨 마지막이라 UI·S 를 그냥 쓴다.
*/
"use strict";

(function () {

/* ══════════ 여기부터 tests/sim/dirtysim.js 가 글자 그대로 떼어 간다 ══════════ */
const EVERY = 200;                    // 0.2초마다 — 붓을 떼고 나서 표시가 뜨기까지의 시간

/* [깃발, 그 작업의 «저장» 단추, 사람이 읽는 말] — 말은 낱말표(state.js)에서 가져온다 */
const MARK = [
  ["edDirty", "#btn-save", UI.TASKWORD.mask],
  ["bDirty", "#boxsave", UI.TASKWORD.box],
  ["numDirty", "#numsave", UI.TASKWORD.num]
];

/* «*» 는 처음 더러워질 때 만든다(깨끗하게 쓰는 동안에는 화면에 아무것도 안 는다).
   `#stemname` **뒤** 에 형제로 세운다 — 이름이 길어 «…» 로 잘려도 이 별은 안 잘린다. */
function star() {
  let el = UI.$("#dirtystar");
  if (el) return el;
  const nm = UI.$("#stemname");
  if (!nm || !nm.parentNode) return null;        // 이 요소가 없는 쪽(사용법 등)에서는 아무 일도 안 한다
  el = document.createElement("span");
  el.id = "dirtystar";
  el.textContent = "*";
  nm.parentNode.insertBefore(el, nm.nextSibling);
  return el;
}

let last = "";
function dirtyMark() {
  const on = MARK.filter((m) => !!S[m[0]]);
  const key = on.map((m) => m[0]).join(",");
  if (key === last) return;                      // 바뀐 게 없다 — 화면을 안 건드린다
  last = key;
  for (const m of MARK) {
    const b = UI.$(m[1]);
    if (b) b.classList.toggle("unsaved", !!S[m[0]]);
  }
  const el = star();
  if (!el) return;
  el.classList.toggle("on", on.length > 0);
  el.title = on.length
    ? "저장하지 않은 작업이 있습니다 — " + on.map((m) => m[2]).join(" · ") + " (Ctrl+S 로 저장)"
    : "";
}
/* ══════════ 여기까지 ══════════ */

setInterval(dirtyMark, EVERY);


/* ── 이 파일이 내놓는 것 (시험이 0.2초를 안 기다리게) ── */
Object.assign(UI, { dirtyMark });
})();
