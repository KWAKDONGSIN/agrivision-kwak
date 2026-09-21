/* 창을 닫을 때 «저장 안 한 것» 셋(마스크·상자·번호)을 다 보고 막는지 — 진짜 코드를 떼어 내 돌린다.
   작성: 2026-09-21 (260921 편의·안정성 사이클 · S4)

왜 있나
  `beforeunload` 는 **사람이 일을 잃는 마지막 문턱**이다. 브라우저 시험으로는 잴 수 없다 —
  파이어폭스가 띄우는 «이 페이지를 나가시겠습니까» 는 운영체제 창이라 marionette 가 못 읽는다.
  그래서 `mask.js` 의 그 처리기와 `confirmLeave()` 를 **글자 그대로 떼어 내** 가짜 창 위에서 돌린다
  (사본 재구현이 아니다 — modesim.js·boxsim.js 와 같은 방법).

무엇을 못박나
  A. 더러운 조합 8가지 전수 — 셋 다 깨끗할 때만 안 막고, 하나라도 더러우면 막는다.
  B. 옛 브라우저용 `returnValue` 도 같이 세운다(preventDefault 만으로는 안 뜨는 판이 있다).
  C. `confirmLeave()` 가 셋을 **각각** 묻고, «취소» 를 누르면 넘어가지 않는다.
*/
"use strict";
const src = require("./lib/load_bundle.js").simSource();

function fn(head) {                            // 최상위 함수 한 개를 그대로 떼어 낸다
  const a = src.indexOf(head);
  if (a < 0) throw new Error("못 찾음: " + head);
  const b = src.indexOf("\n}\n", a);
  return src.slice(a, b + 3);
}
function stmt(head, end) {                     // 최상위 문장 한 개
  const a = src.indexOf(head);
  if (a < 0) throw new Error("못 찾음: " + head);
  const b = src.indexOf(end, a);
  return src.slice(a, b + end.length);
}

const HEAD_LEAVE = "function confirmLeave(kind) {";
const HEAD_UNLOAD = 'window.addEventListener("beforeunload", (e) => {';
const CODE = [fn(HEAD_LEAVE), stmt(HEAD_UNLOAD, "\n});\n")].join("\n");
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (confirmLeave · beforeunload)");

/* ---------------- 가짜 창 ---------------- */
const H = {};
const win = { addEventListener: (ev, f) => { H[ev] = f; } };
const S = { edDirty: false, bDirty: false, numDirty: false };
const asked = [];
let answer = true;                             // confirm() 이 돌려줄 답
const confirmStub = (m) => { asked.push(m); return answer; };

new Function("window", "S", "confirm",
  CODE + "\n;global.__X = { confirmLeave };")(win, S, confirmStub);
const X = global.__X;

let tests = 0, fails = 0;
const ok = (c, n, x) => { tests++; if (!c) { fails++; console.log("  [실패] " + n + (x ? "  " + x : "")); }
                          else console.log("  [통과] " + n + (x ? "  " + x : "")); };

const NAME = { edDirty: "마스크", bDirty: "상자", numDirty: "번호" };
function setDirty(f) { S.edDirty = !!f.edDirty; S.bDirty = !!f.bDirty; S.numDirty = !!f.numDirty; }
function unload() {                            // 창 닫기 한 번 — 막았나?
  const e = { returnValue: undefined, prevented: false, preventDefault() { this.prevented = true; } };
  H.beforeunload(e);
  return e;
}

/* ── A. 더러운 조합 8가지 전수 ───────────────────────────────────── */
console.log("\nA. 창 닫기 — 셋 중 하나라도 저장 안 했으면 막는다");
ok(typeof H.beforeunload === "function", "beforeunload 처리기가 붙어 있다");
for (let m = 0; m < 8; m++) {
  const f = { edDirty: !!(m & 1), bDirty: !!(m & 2), numDirty: !!(m & 4) };
  const on = Object.keys(NAME).filter((k) => f[k]).map((k) => NAME[k]);
  setDirty(f);
  const e = unload();
  const want = on.length > 0;
  ok(e.prevented === want,
     `${on.length ? on.join("+") : "셋 다 깨끗"} → ${want ? "막는다" : "안 막는다"}`,
     `prevented=${e.prevented}`);
}

/* ── B. 옛 브라우저용 returnValue ────────────────────────────────── */
console.log("\nB. 옛 브라우저용 returnValue");
["edDirty", "bDirty", "numDirty"].forEach((k) => {
  setDirty({ [k]: true });
  const e = unload();
  ok(e.returnValue === "", `${NAME[k]} 하나만 더러워도 returnValue 를 세운다`, `returnValue=${JSON.stringify(e.returnValue)}`);
});
setDirty({});
ok(unload().returnValue === undefined, "셋 다 깨끗하면 returnValue 를 건드리지 않는다");

/* ── C. confirmLeave() — 셋을 각각 묻는다 ───────────────────────── */
console.log("\nC. 다른 사진으로 넘어갈 때 — 셋을 각각 묻는다");
const WORD = { edDirty: "수정", bDirty: "상자", numDirty: "번호" };
["edDirty", "bDirty", "numDirty"].forEach((k) => {
  setDirty({ [k]: true }); asked.length = 0; answer = true;
  const r = X.confirmLeave();
  ok(r === true && asked.length === 1, `${NAME[k]} 가 더러우면 한 번 묻고, «예» 면 넘어간다`, `물음 ${asked.length}개`);
  ok(asked.length === 1 && asked[0].indexOf(WORD[k]) >= 0, `그 물음이 «${WORD[k]}» 를 말한다`, asked[0] && asked[0].split("\n")[0]);

  setDirty({ [k]: true }); asked.length = 0; answer = false;
  ok(X.confirmLeave() === false, `${NAME[k]} — «취소» 를 누르면 넘어가지 않는다`);
});
setDirty({}); asked.length = 0; answer = false;
ok(X.confirmLeave() === true && asked.length === 0, "셋 다 깨끗하면 묻지 않고 그냥 넘어간다");

setDirty({ edDirty: true }); asked.length = 0; answer = true;
X.confirmLeave("view");
ok(asked.length === 1 && asked[0].indexOf("그대로 남아 있습니다") >= 0,
   "탭만 바꾸는 것(view)은 «수정은 그대로 남아 있다» 고 말한다", asked[0] && asked[0].split("\n")[1]);

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
