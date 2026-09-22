/* state — 상태 하나(S)와 공용 낱말표
   작성: 2026-09-20 (구조 정리 5사이클 · 사이클 3 «화면 분리» — 동작 무변경)
   옮겨 온 곳: app.js 15-26·11-13·1431-1433·1778-1785·88-88·502-504줄 · ui.js 361-363줄 — **글자를 고치지 않고** 옮겼다(고친 곳은 아래 주석에 남긴다).

   화면 전체가 함께 쓰는 상태 `S` 와, 전역 셋(`S`·`API`·`UI`)을 여기서 만든다. 여기 말고 다른 파일은 전역을 만들지 않는다.

   의존은 «위에서 아래로» 만 — 이 파일이 쓰는 이름은 모두 **먼저 오는 파일**이 만든 것이다.
   되돌아 부르는 자리(예: draw() → 상자·번호)는 `UI.이름()` 으로 적어 눈에 보이게 한다.
*/
"use strict";

const S = {
  fruit: null, items: [], idx: -1, page: 1, pages: 1, features: {},
  W: 0, H: 0, stem: null, item: null,
  img: null,
  gt: null, ai: null, ed: null,               // Uint8Array (0/1), 길이 W*H
  lay: {},                                    // 레이어별 {cv, ctx, pix(ImageData)}
  undo: [], redo: [],
  view: { s: 1, tx: 0, ty: 0 },
  tool: "brush", brush: 30, alpha: 0.45,
  drawing: false, panning: false, poly: [], lastPt: null,
  dirty: true, busy: false
};

/* 🔴 전역은 이 셋뿐이다 — `S`(상태) · `API`(서버 부르기) · `UI`(화면 함수·낱말).
   다른 파일은 모두 IIFE(즉시 실행 함수) 안이고, 필요한 것만 여기서 꺼내 쓴다.
   (2026-09-20 구조 사이클3 전: app.js 최상위 이름 152개가 전부 전역이었다(ui.js 는 이미 IIFE 였다).)
   `S` 는 위 리터럴 그대로다(app.js 15-26줄). 아래 둘은 이 사이클이 새로 만든 «주머니» 다:
     API = 서버 부르기(get·post) · UI = 화면 함수와 낱말표.
   이 파일 말고는 어느 파일도 최상위에 이름을 만들지 않는다(전부 IIFE 안). */
const API = {};
const UI = {};

(function () {

// 0919 사용자: «잎이 초록이라 마킹이 안 보인다» → 내 수정본(ed) 초록 → 시안(하늘색). 잎·과일·빨강 원본·파랑 AI 어느 것과도 겹치지 않는 색.
const COL = { gt: [232, 68, 58], ai: [47, 125, 225], ed: [0, 229, 255],
              orig: [255, 140, 0],          // 0922: 검수 전 원본(주황) — 복숭아·포도만 있다
              add: [255, 212, 0], del: [255, 53, 208] };

Object.assign(S, { boxMode: false, film: 0.25, boxes: [], bsel: -1,
                   btool: "draw", bundo: [], bredo: [], bDirty: false, drag: null,
                   bpick: null });                   // bpick: 마지막으로 고른 자리(겹친 상자 순환용)
                   // 0921 U3: bredo = 되돌린 상자 모습을 담아 두는 칸(Ctrl+Y). 마스크의 `redo`·번호의
                   // `numRedoStack` 과 같은 뜻이고, 담는 것은 `bundo` 와 똑같은 «JSON 글자» 다.

Object.assign(S, {
  inst: null, instOrig: null, instSrc: null, instMax: 0, instN: 0,
  numMode: false, ntool: "click", numAlpha: 0.6, numSel: [],
  numUndoStack: [], numRedoStack: [], numDirty: false,
  numCounts: { erase: 0, merge: 0, split: 0, add: 0 },
  numLine: null, numPoly: [], numBrushPx: null, numBrushPath: null, numCents: null,
  errBy: {}, errRows: [], errFruit: null
});

const FRUIT_KO = { apple: "사과", blueberry: "블루베리", grape: "포도", peach: "복숭아" };

function statusKo(s) {
  return { unreviewed: "아직 안 봄", ok: "원본 그대로 OK", fixed: "수정함", flag: "문제 있음", exclude: "제외" }[s] || s;
}

const TASKWORD = { mask: "칠한 영역", box: "상자", num: "번호" };
const TASKKIND = { mask: "mask", box: "boxes", num: "instances" };
const TASKFIELD = { box: "confirmed_boxes", num: "confirmed_instances" };

/* 「노란 점선 후보 자리로 확대」가 **몇 번째 후보를 봤나**. 쪼개기 전에는 app.js 의
   파일 지역 `let noteZoomAt = -1` 이었는데, 그 값을 새 사진마다 되돌리는 곳(list.js
   openItem)과 쓰는 곳(view.js zoomToNote)이 **다른 파일**이 됐다 → 상태는 S 하나에 둔다.
   처음 값(-1)·뜻·동작은 그대로다. */
Object.assign(S, { noteZoomAt: -1 });


/* ── 이 파일이 내놓는 것 (다음 파일들이 쓴다) ── */
Object.assign(UI, { COL, FRUIT_KO, statusKo, TASKWORD, TASKKIND, TASKFIELD });
})();
