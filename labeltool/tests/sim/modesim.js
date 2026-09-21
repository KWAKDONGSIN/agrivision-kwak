/* 번호 편집 모드 ↔ 상자 모드가 «동시에» 켜지지 않는지, 키가 서로 먹지 않는지.
   브라우저가 없으므로 app.js 에서 단축키 처리·setNumMode·setTool·#box-mode onchange 를
   «글자 그대로» 떼어 내 가짜 DOM 위에서 돌린다(사본 재구현이 아니다). */
"use strict";
const fs = require("fs");
/* 2026-09-20 구조 사이클3: `index.html` 의 <script> 순서대로 이어 붙인 «한 덩어리» 에서 떼어 낸다
   (load_bundle.js). 옛 로더는 `SIM_SRC=appjs node modesim.js`. */
const src = require("./lib/load_bundle.js").simSource();

function fn(head) {                            // 최상위 함수 한 개를 그대로 떼어 낸다
  const a = src.indexOf(head);
  if (a < 0) throw new Error("못 찾음: " + head);
  const b = src.indexOf("\n}\n", a);
  return src.slice(a, b + 3);
}
function stmt(head, end) {                     // 최상위 대입문 한 개
  const a = src.indexOf(head);
  if (a < 0) throw new Error("못 찾음: " + head);
  const b = src.indexOf(end, a);
  return src.slice(a, b + end.length);
}
const CODE = [
  fn("function setTool(t) {"),
  // 0921 U8: setTool 이 «지금 굵기 칸» 을 묻는다. 한 줄짜리라 fn() 이 못 자른다 → stmt 로 그 줄만.
  //   (여기서 다시 짜 넣으면 사본이 된다. 적는 쪽 saveBrush·loadBrush 는 이 시험 밖이라 빈 손잡이로 준다.)
  stmt("function sizeTool() {", "\n"),
  fn("function setNumMode(on, silent) {"),
  fn("function numKey(e) {"),
  stmt('$("#box-mode").onchange = () => {', "\n};\n"),
  stmt('window.addEventListener("keydown", (e) => {', "\n});\n"),
].join("\n");
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (setTool·setNumMode·numKey·#box-mode onchange·keydown)");

/* ---------------- 가짜 DOM ---------------- */
const log = [];
const els = {};
function mkEl(id) {
  const cls = new Set();
  return {
    id, checked: false, disabled: false, value: "50", textContent: "", innerHTML: "",
    style: {}, dataset: {}, oninput: () => {}, onchange: () => {},
    click() { log.push("click:" + id); },
    classList: {
      add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c),
      toggle: (c, v) => { if (v === undefined) { cls.has(c) ? cls.delete(c) : cls.add(c); } else { v ? cls.add(c) : cls.delete(c); } },
    },
    _cls: cls,
  };
}
const $ = (sel) => (els[sel] = els[sel] || mkEl(sel.replace(/^#/, "")));
const TOOLS = ["brush", "erase", "polyadd", "polysub", "smartadd", "smartsub"].map((t) => { const e = mkEl("tool-" + t); e.dataset.tool = t; return e; });
const NTOOLS = ["erase", "merge", "split", "add"].map((t) => { const e = mkEl("ntool-" + t); e.dataset.ntool = t; return e; });
const $$ = (sel) => (sel === ".tool" ? TOOLS : sel === ".ntool" ? NTOOLS : []);
const flash = (m, warn) => log.push("flash" + (warn ? "!" : "") + ":" + m);
const S = { inst: new Uint16Array(4), boxMode: false, numMode: false, numSel: [], numLine: null,
            poly: [], tool: "brush", brush: 20, dirty: false, item: { has_proposal: false },
            bsel: -1, boxes: [] };
const stub = (name) => (...a) => { log.push(name + (a.length ? "(" + a.join(",") + ")" : "")); return true; };
const H = {};
const win = { addEventListener: (ev, f) => { H[ev] = f; } };

new Function("window", "$", "$$", "S", "flash", "log", "setNTool", "doErase", "doMerge", "doSplit", "doAdd",
  "hasPendingRegion", "clearPending", "numInfo", "prevItem", "nextItem", "paintGtLayer", "setBTool",
  "delSelBox", "fitView", "doAction", "applyPolygon", "numUndo", "numRedo", "boxUndo", "boxRedo", "saveInstances", "saveBoxes",
  "saveBrush", "loadBrush",
  CODE + "\n;global.__X = { setNumMode, setTool, numKey };")(
  win, $, $$, S, flash, log, stub("setNTool"), stub("doErase"), stub("doMerge"), stub("doSplit"), stub("doAdd"),
  () => false, stub("clearPending"), () => {}, stub("prevItem"), stub("nextItem"), stub("paintGtLayer"), stub("setBTool"),
  stub("delSelBox"), stub("fitView"), stub("doAction"), stub("applyPolygon"), stub("numUndo"), stub("numRedo"),
  stub("boxUndo"), stub("boxRedo"), stub("saveInstances"), stub("saveBoxes"),
  () => {}, () => {});                             // 0921 U8: 굵기 적기·읽기는 brushsim 이 본다
const X = global.__X;

let fails = 0, tests = 0;
const ok = (c, n, x) => { tests++; if (!c) { fails++; console.log("  [실패] " + n + (x ? "  " + x : "")); } else console.log("  [통과] " + n + (x ? "  " + x : "")); };
function key(k, mods) {
  log.length = 0;
  H.keydown(Object.assign({ key: k, code: "Key" + k.toUpperCase(), target: { tagName: "BODY" },
    preventDefault() {}, ctrlKey: false, metaKey: false }, mods || {}));
  return log.slice();
}
const both = () => S.numMode && S.boxMode;

console.log("\nA. 두 모드가 동시에 켜지지 않는다");
ok(!S.numMode && !S.boxMode, "처음엔 둘 다 꺼짐");
key("x");
ok(S.boxMode === true && S.numMode === false, "X → 상자 모드만 켜짐 (전과 같음)", `box=${S.boxMode}`);
key("k");
ok(S.numMode === true && S.boxMode === false, "K → 번호 편집 켜지면서 상자 모드가 꺼진다", `num=${S.numMode} box=${S.boxMode}`);
ok($("#box-mode").checked === false, "상자 모드 체크가 풀림");
ok($("#box-mode").disabled === true, "상자 모드 체크박스가 «잠김»");
{
  log.length = 0;
  $("#box-mode").checked = true; $("#box-mode").onchange();       // 잠금을 무시하고 눌러 본 경우
  ok(S.boxMode === false && $("#box-mode").checked === false, "번호 모드 중 상자 모드를 켜려 하면 거절된다");
  ok(log.some((l) => /flash!?:번호 편집 모드를 먼저 끄세요/.test(l)), "«K 로 먼저 끄세요» 안내가 뜬다", log.join(" | "));
}
let seen = false;
/* 🔴 2026-09-19 구조 사이클1 **2차 검수** §4-3: 여기가 `Math.random()` 이었다. 400번을 «마구»
   누르는 시험이 **돌릴 때마다 다른 순서**라서, 한 번 통과한 것이 다음에 깨져도 그 순서를 다시
   만들 수 없었다(관문 명령이 흔들린다). 씨값을 고정한 난수로 바꾼다 — 누르는 순서는 늘 같고,
   순서를 바꿔 보고 싶으면 `MODESIM_SEED=2` 처럼 씨값만 준다. 항목 수·판정 규칙은 그대로다. */
let _seed = (parseInt(process.env.MODESIM_SEED || "260920", 10) >>> 0) || 1;
const rnd = () => { _seed = (_seed * 1103515245 + 12345) >>> 0; return ((_seed >>> 8) & 0xffffff) / 0x1000000; };
const KEYS = ["k", "j", "x", "d", "m", "n", "v", "b", "e", "1", "3", "4", "0", "i", "K", "X", "D"];
for (let t = 0; t < 400; t++) {
  const r = rnd();
  if (r < 0.1) { if (!$("#box-mode").disabled) { $("#box-mode").checked = !$("#box-mode").checked; $("#box-mode").onchange(); } }
  else key(KEYS[(rnd() * KEYS.length) | 0]);
  if (both()) { seen = true; break; }
}
ok(!seen, "키·체크박스를 400번 마구 눌러도 두 모드가 «동시에» 켜진 적 없다");

console.log("\nB. 모드마다 같은 키가 서로 먹지 않는다");
X.setNumMode(false, true); S.boxMode = false; $("#box-mode").checked = false; $("#box-mode").disabled = false;
let L = key("x");
ok(S.boxMode === true, "번호 모드 꺼짐: X = 상자 모드 토글");
key("x"); X.setNumMode(true, true);
L = key("x");
ok(L.some((l) => /doSplit|setNTool\(split\)/.test(l)) && S.boxMode === false,
  "번호 모드 켜짐: X = 나누기 (상자 모드를 건드리지 않는다)", L.join(" | "));
L = key("d");
ok(L.some((l) => /doErase|setNTool\(erase\)/.test(l)), "번호 모드: D = 지우기", L.join(" | "));
L = key("m");
ok(L.some((l) => /doMerge|setNTool\(merge\)/.test(l)), "번호 모드: M = 합치기", L.join(" | "));
L = key("n");
ok(L.some((l) => /doAdd|setNTool\(add\)/.test(l)), "번호 모드: N = 새로 붙이기", L.join(" | "));
const numBefore = $("#l-num").checked;
key("j");
ok($("#l-num").checked !== numBefore, "번호 모드: J = 번호 레이어 토글");
const toolWas = S.tool;                        // 앞의 무작위 시험이 도구를 바꿔 놓았을 수 있다
L = key("b");
ok(L.some((l) => /flash!?:번호 편집 모드가 켜져 있어/.test(l)) && S.tool === toolWas,
  "번호 모드: B(브러시) 는 잠겨 있다고 알리고 도구를 바꾸지 않는다", `도구 ${toolWas} 그대로 · ` + L.join(" | "));
key("k");
ok(S.numMode === false, "번호 모드: K = 모드 끄기");
ok($("#box-mode").disabled === false && $("#btn-save").disabled === false, "모드를 끄면 상자 모드·수정본 저장이 다시 풀린다");
const diffBefore = $("#l-diff").checked;
key("d");
ok($("#l-diff").checked !== diffBefore, "번호 모드 꺼짐: D = 차이 보기 (예전 뜻 그대로)");
L = key("m");
ok(!L.some((l) => /doMerge|setNTool/.test(l)), "번호 모드 꺼짐: M 은 아무 일도 안 한다", L.join(" | ") || "(없음)");
L = key("n");
ok(!L.some((l) => /doAdd|setNTool/.test(l)), "번호 모드 꺼짐: N 은 아무 일도 안 한다", L.join(" | ") || "(없음)");

console.log("\nC. Ctrl+S · Ctrl+Z · Ctrl+Y 가 모드마다 제 갈래로 간다");
X.setNumMode(false, true); S.boxMode = false;
L = key("s", { ctrlKey: true });
ok(L.some((l) => /doAction\(fixed\)/.test(l)), "둘 다 꺼짐: Ctrl+S = 수정본 저장", L.join(" | "));
L = key("z", { ctrlKey: true });
ok(L.some((l) => /click:undo/.test(l)), "둘 다 꺼짐: Ctrl+Z = 마스크 되돌리기", L.join(" | "));
$("#box-mode").checked = true; $("#box-mode").onchange();
L = key("s", { ctrlKey: true });
ok(L.some((l) => /saveBoxes/.test(l)), "상자 모드: Ctrl+S = 상자 저장", L.join(" | "));
L = key("z", { ctrlKey: true });
ok(L.some((l) => /boxUndo/.test(l)), "상자 모드: Ctrl+Z = 상자 되돌리기", L.join(" | "));
/* 2026-09-21 U3: 여기가 «안내만 뜬다» 였다. 상자에도 다시하기가 생겨 `boxRedo` 로 간다.
   «마스크» 다시하기(#redo)를 0회 누르는 것은 사이클3 수정 그대로 지킨다. */
L = key("y", { ctrlKey: true });
ok(!L.some((l) => /click:redo/.test(l)) && L.some((l) => /boxRedo/.test(l)),
  "상자 모드: Ctrl+Y = 상자 다시하기 («마스크» 다시하기 #redo 는 0회)", L.join(" | "));
X.setNumMode(true, true);
L = key("s", { ctrlKey: true });
ok(L.some((l) => /saveInstances/.test(l)), "번호 모드: Ctrl+S = 번호 저장", L.join(" | "));
L = key("z", { ctrlKey: true });
ok(L.some((l) => /numUndo/.test(l)), "번호 모드: Ctrl+Z = 번호 되돌리기", L.join(" | "));
L = key("y", { ctrlKey: true });
ok(L.some((l) => /numRedo/.test(l)), "번호 모드: Ctrl+Y = 번호 다시하기", L.join(" | "));

console.log("\nD. 번호가 없는 과일 · 목록 화면");
X.setNumMode(false, true); S.inst = null;
L = key("k");
ok(S.numMode === false, "번호가 없는 사진(S.inst=null)에서 K 는 모드를 켜지 않는다");
L = key("j");
ok(!L.length, "그때 J 도 아무 일도 안 한다", L.join(" | ") || "(없음)");
S.inst = new Uint16Array(4);
$("#view-edit").classList.add("hidden");
const boxWas = S.boxMode;
L = key("x");
ok(S.boxMode === boxWas, "목록 화면(편집 화면이 숨어 있을 때)에서는 키가 안 먹는다");
$("#view-edit").classList.remove("hidden");

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
