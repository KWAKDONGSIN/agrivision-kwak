/* «저장 안 됨» 표시 — 진짜 코드(dirtymark.js)를 떼어 내 가짜 화면에서 돌린다.
   작성: 2026-09-21 (260921 편의·안정성 사이클 · U1)

왜 있나
  «*» 가 틀리면 제일 나쁜 쪽으로 틀린다 — 저장이 안 됐는데 «*» 가 없으면 사람은 저장한 줄 알고
  다음 장으로 넘어간다. 그래서 더러운 깃발 셋의 **여덟 가지 조합을 하나도 빼지 않고** 본다.
  진짜 파이어폭스로 여덟 가지를 다 만들려면 붓질·상자·번호를 조합해야 해서 오래 걸린다
  (b10 은 그중 실제로 일어나는 세 가지를 진짜로 만들어 잰다).
  사본 재구현이 아니다 — `app/static/js/dirtymark.js` 의 글자를 그대로 떼어 낸다
  (backupsim·locksim·leavesim 과 같은 방법. dirtymark.js 를 고치면 이 시험이 같이 따라간다).

무엇을 못박나
  A. 깃발 여덟 조합 — «*» 가 켜지는가, 그 작업의 «저장» 단추에만 `unsaved` 가 붙는가.
  B. 저장하면(깃발이 내려가면) «*» 도 테두리도 사라진다.
  C. 풍선말에 «무엇이» 저장 안 됐는지 그 작업 이름이 적힌다.
  D. 깨끗할 때는 «*» 요소를 아예 만들지 않는다(화면에 한 칸도 안 는다).
  E. 값이 안 바뀌면 화면을 한 번도 안 건드린다(0.2초마다 도는 것이라 이게 중요하다).
  F. «*» 는 딱 하나만 생긴다(여러 번 불러도 겹쳐 쌓이지 않는다).
  G. `#stemname` 이 없는 쪽에서도 깨지지 않는다.
*/
"use strict";
const src = require("./lib/load_bundle.js").simSource();

const HEAD = "const EVERY = 200;";
const TAIL = "/* ══════════ 여기까지 ══════════ */";
const a = src.indexOf(HEAD), b = src.indexOf(TAIL);
if (a < 0 || b < 0) throw new Error("dirtymark.js 에서 구간을 못 찾음");
const CODE = src.slice(a, b);
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (dirtymark.js — 저장 안 됨 표시)");

/* ---------------- 가짜 화면 ---------------- */
let writes = 0;                                  // 화면을 몇 번 건드렸나(E 가 센다)
function mkEl(id) {
  const cls = new Set();
  return {
    id, title: "", textContent: "", parentNode: null, nextSibling: null,
    classList: {
      toggle: (c, on) => { writes++; if (on) cls.add(c); else cls.delete(c); },
      contains: (c) => cls.has(c)
    },
    _cls: cls
  };
}

let els, made, noStem = false;
const doc = {
  createElement() { made++; return mkEl(""); }
};
const $ = (s) => {
  if (s === "#stemname" && noStem) return null;
  return els[s] || null;
};
const UI = { $, TASKWORD: { mask: "칠한 영역", box: "상자", num: "번호" } };
const S = { edDirty: false, bDirty: false, numDirty: false };

let dirtyMark;
function reset(stem) {
  noStem = (stem === false);
  made = 0; writes = 0;
  S.edDirty = S.bDirty = S.numDirty = false;
  els = {
    "#btn-save": mkEl("btn-save"),
    "#boxsave": mkEl("boxsave"),
    "#numsave": mkEl("numsave")
  };
  if (!noStem) {
    const nm = mkEl("stemname");
    // 진짜 화면의 `#navphoto` 흉내 — 여기에 끼워 넣은 형제가 «*» 다
    nm.parentNode = {
      kids: [nm],
      insertBefore(el, ref) { this.kids.splice(this.kids.indexOf(ref) + 1 || this.kids.length, 0, el);
                              els["#dirtystar"] = el; }
    };
    els["#stemname"] = nm;
  }
  dirtyMark = new Function("S", "UI", "document", CODE + "\nreturn dirtyMark;")(S, UI, doc);
}

let tests = 0, fails = 0;
const ok = (c, n, x) => {
  tests++;
  if (!c) { fails++; console.log("  [실패] " + n + (x !== undefined ? "  " + JSON.stringify(x) : "")); }
  else console.log("  [통과] " + n + (x !== undefined ? "  " + JSON.stringify(x) : ""));
};
const starOn = () => !!(els["#dirtystar"] && els["#dirtystar"]._cls.has("on"));
const unsaved = (s) => els[s]._cls.has("unsaved");
const marks = () => ["#btn-save", "#boxsave", "#numsave"].map(unsaved);

/* ============ A. 깃발 여덟 조합 ============ */
console.log("\nA. 더러운 깃발 여덟 조합 — «*» 와 «저장» 단추 테두리");
for (let n = 0; n < 8; n++) {
  const want = [!!(n & 1), !!(n & 2), !!(n & 4)];
  reset();
  S.edDirty = want[0]; S.bDirty = want[1]; S.numDirty = want[2];
  dirtyMark();
  const name = ["칠한 영역", "상자", "번호"].filter((_, i) => want[i]).join("+") || "(깨끗)";
  ok(starOn() === want.some(Boolean), `${name} → «*» ${want.some(Boolean) ? "보인다" : "안 보인다"}`);
  ok(JSON.stringify(marks()) === JSON.stringify(want),
    `${name} → 그 작업의 «저장» 단추에만 테두리`, { 잰것: marks(), 바란것: want });
}

/* ============ B. 저장하면 사라진다 ============ */
console.log("\nB. 저장하면(깃발이 내려가면) 표시가 사라진다");
for (const [flag, sel, word] of [["edDirty", "#btn-save", "칠한 영역"],
                                 ["bDirty", "#boxsave", "상자"],
                                 ["numDirty", "#numsave", "번호"]]) {
  reset();
  S[flag] = true; dirtyMark();
  const on1 = starOn(), m1 = unsaved(sel);
  S[flag] = false; dirtyMark();                  // ← 저장 성공
  ok(on1 && m1, `${word} 를 고치면 «*» 와 테두리가 뜬다`);
  ok(!starOn() && !unsaved(sel), `${word} 를 저장하면 둘 다 사라진다`,
    { 별: starOn(), 테두리: unsaved(sel) });
}
{
  // 셋 다 더러운 상태에서 하나만 저장하면 «*» 는 남고 그 단추 테두리만 떨어진다
  reset();
  S.edDirty = S.bDirty = S.numDirty = true; dirtyMark();
  S.bDirty = false; dirtyMark();
  ok(starOn() === true, "셋 중 하나만 저장하면 «*» 는 그대로 남는다");
  ok(JSON.stringify(marks()) === JSON.stringify([true, false, true]),
    "저장한 상자 단추의 테두리만 떨어진다", marks());
}

/* ============ C. 풍선말 ============ */
console.log("\nC. 풍선말에 «무엇이» 저장 안 됐는지 적힌다");
{
  reset();
  S.edDirty = true; S.numDirty = true; dirtyMark();
  const t = els["#dirtystar"].title;
  ok(t.indexOf("칠한 영역") >= 0 && t.indexOf("번호") >= 0, "더러운 둘의 이름이 다 적힌다", t);
  ok(t.indexOf("상자") < 0, "깨끗한 것(상자)은 안 적힌다", t);
  ok(t.indexOf("Ctrl+S") >= 0, "어떻게 저장하는지도 적힌다", t);
  S.edDirty = S.numDirty = false; dirtyMark();
  ok(els["#dirtystar"].title === "", "깨끗해지면 풍선말도 비운다", els["#dirtystar"].title);
}

/* ============ D. 깨끗할 때는 요소를 아예 안 만든다 ============ */
console.log("\nD. 깨끗한 동안에는 화면에 한 칸도 안 는다");
{
  reset();
  for (let i = 0; i < 20; i++) dirtyMark();      // 0.2초마다 4초 동안 돈 셈
  ok(made === 0, "«*» 요소를 만들지 않았다", { 만든수: made });
  ok(els["#dirtystar"] === undefined, "화면에도 안 끼웠다");
  ok(writes === 0, "단추 딱지도 한 번도 안 건드렸다", { 건드린수: writes });
}

/* ============ E. 값이 안 바뀌면 화면을 안 건드린다 ============ */
console.log("\nE. 0.2초마다 돌아도 바뀐 것이 없으면 화면을 안 건드린다");
{
  reset();
  S.edDirty = true; dirtyMark();
  const w1 = writes;
  for (let i = 0; i < 50; i++) dirtyMark();      // 10초어치
  ok(writes === w1, "같은 상태로 50번 더 돌아도 화면 건드림이 안 는다", { 처음: w1, 나중: writes });
  ok(starOn() === true, "그래도 «*» 는 그대로 켜져 있다");
  S.bDirty = true; dirtyMark();
  ok(writes > w1, "진짜로 바뀌면 그때 건드린다", { 나중: writes });
}

/* ============ F. «*» 는 하나만 ============ */
console.log("\nF. 여러 번 더러워졌다 깨끗해져도 «*» 는 딱 하나");
{
  reset();
  for (let i = 0; i < 6; i++) { S.edDirty = true; dirtyMark(); S.edDirty = false; dirtyMark(); }
  ok(made === 1, "만든 요소는 하나뿐이다", { 만든수: made });
  ok(els["#stemname"].parentNode.kids.length === 2, "화면에도 하나만 끼워져 있다",
    els["#stemname"].parentNode.kids.length);
  ok(els["#stemname"].parentNode.kids[1] === els["#dirtystar"], "파일 이름 «바로 옆» 자리다");
}

/* ============ G. 그 요소가 없는 쪽 ============ */
console.log("\nG. `#stemname` 이 없는 쪽(사용법 등)에서도 안 깨진다");
{
  reset(false);
  let threw = null;
  try { S.edDirty = true; dirtyMark(); } catch (e) { threw = String(e); }
  ok(threw === null, "던지지 않는다", threw);
  ok(unsaved("#btn-save") === true, "단추 테두리는 그래도 붙는다");
  // 끼울 자리를 먼저 보고 없으면 **만들지도 않는다**(빈 요소가 떠돌지 않는다)
  ok(made === 0 && els["#dirtystar"] === undefined,
    "«*» 는 끼울 자리가 없으니 만들지도 않는다", { 만든수: made });
}

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
