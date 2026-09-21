/* 저장 중 단추 잠금 — 진짜 코드(api.js 의 lockWhile)를 떼어 내 가짜 화면에서 돌린다.
   작성: 2026-09-21 (260921 편의·안정성 사이클 · S6)

왜 있나
  «느린 응답 중에 두 번 누르면 요청이 한 번만 가는가» 는 **시간이 걸린 답**이 있어야 잴 수 있다.
  진짜 파이어폭스로는 서버를 느리게 만들어야 하고(b9 가 그렇게 한다), 여기서는 가짜 응답의
  시간을 내 마음대로 잡아 «잠금이 언제 풀리나»·«던져도 풀리나» 까지 한 칸씩 못박는다.
  사본 재구현이 아니다 — `app/static/js/api.js` 의 글자를 그대로 떼어 낸다(backupsim·leavesim 과 같은 방법).

무엇을 못박나
  A. 도는 동안 두 번째 호출은 **아예 들어오지 못한다**(fn 이 한 번만 돈다 · 돌려주는 값은 undefined).
  B. 끝나면 풀린다 — 다시 누르면 또 돈다(영영 잠기지 않는다).
  C. 단추에 `.saving` 딱지가 붙었다가 끝나면 떨어진다. `disabled` 는 **건드리지 않는다.**
  D. fn 이 던지거나 실패해도 풀린다(잠긴 채 남지 않는다).
  E. 인자·돌려주는 값이 그대로 지나간다.
  F. 잠금은 길마다 따로다 — 상자 저장이 도는 동안 번호 저장은 눌린다.
  G. 단추가 화면에 없어도(쉬움 모드에서 숨은 것 등) 깨지지 않는다.
*/
"use strict";
const src = require("./lib/load_bundle.js").simSource();

const HEAD = "function lockWhile(sels, fn) {";
const a = src.indexOf(HEAD);
if (a < 0) throw new Error("api.js 에서 lockWhile 을 못 찾음");
const b = src.indexOf("\n}\n", a);
const CODE = src.slice(a, b + 3);
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (api.js — lockWhile)");

/* ---------------- 가짜 화면 ---------------- */
const els = {};
function mkEl(sel) {
  const cls = new Set();
  return {
    sel, disabled: false,
    classList: { add: (c) => cls.add(c), remove: (c) => cls.delete(c), contains: (c) => cls.has(c) },
    _cls: cls
  };
}
const MISSING = "#없는단추";
const $ = (s) => (s === MISSING ? null : (els[s] = els[s] || mkEl(s)));

const lockWhile = new Function("$", CODE + "\nreturn lockWhile;")($);

let tests = 0, fails = 0;
const ok = (c, n, x) => {
  tests++;
  if (!c) { fails++; console.log("  [실패] " + n + (x !== undefined ? "  " + JSON.stringify(x) : "")); }
  else console.log("  [통과] " + n + (x !== undefined ? "  " + JSON.stringify(x) : ""));
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const saving = (s) => $(s)._cls.has("saving");

(async function () {

/* ============ A. 느린 응답 중에 두 번 누르면 한 번만 간다 ============ */
console.log("\nA. 느린 응답(200ms) 중에 두 번 눌러도 요청은 한 번");
{
  let ran = 0;
  const f = lockWhile(["#boxsave"], async () => { ran++; await sleep(200); return "저장됨"; });
  const p1 = f();                       // 첫 번째 — 200ms 동안 돈다
  const p2 = f();                       // 그 사이에 한 번 더 눌렀다
  const p3 = f();                       // 세 번째
  const r = await Promise.all([p1, p2, p3]);
  ok(ran === 1, "저장 함수가 한 번만 돌았다", { 돈횟수: ran });
  ok(r[0] === "저장됨", "첫 번째는 제 값을 돌려준다", r[0]);
  ok(r[1] === undefined && r[2] === undefined, "두 번째·세 번째는 아무 일도 안 하고 undefined", r);
}
{
  // 키를 누른 채 있는 흉내 — 20번 연타
  let ran = 0;
  const f = lockWhile(["#btn-save"], async () => { ran++; await sleep(150); });
  const ps = [];
  for (let i = 0; i < 20; i++) ps.push(f());
  await Promise.all(ps);
  ok(ran === 1, "Ctrl+S 를 누른 채 있어도(20연타) 한 번만 간다", { 돈횟수: ran });
}

/* ============ B. 끝나면 풀린다 ============ */
console.log("\nB. 다 보내고 나면 다시 눌린다(영영 잠기지 않는다)");
{
  let ran = 0;
  const f = lockWhile(["#boxsave"], async () => { ran++; await sleep(30); });
  await f();
  await f();
  await f();
  ok(ran === 3, "차례로 세 번 누르면 세 번 다 간다", { 돈횟수: ran });
}

/* ============ C. 딱지 ============ */
console.log("\nC. 도는 동안 «.saving» 딱지 · disabled 는 안 건드린다");
{
  const sel = "#numsave";
  $(sel).disabled = false;
  let mid = null, midDis = null;
  const f = lockWhile([sel], async () => { mid = saving(sel); midDis = $(sel).disabled; await sleep(60); });
  const p = f();
  await sleep(10);
  ok(saving(sel) === true, "누르자마자 딱지가 붙는다");
  await p;
  ok(mid === true, "저장 함수가 도는 동안에도 붙어 있다");
  ok(saving(sel) === false, "끝나면 떨어진다");
  ok(midDis === false && $(sel).disabled === false,
    "`disabled` 는 도는 동안에도 끝난 뒤에도 그대로다(다른 규칙의 칸을 뺏지 않는다)",
    { 도는중: midDis, 끝난뒤: $(sel).disabled });
}
{
  // 다른 규칙이 이미 잠가 둔 단추(#btn-ai: AI 제안이 없는 사진) — 저장이 끝나도 그대로여야 한다
  const sel = "#btn-ai";
  $(sel).disabled = true;
  const f = lockWhile([sel], async () => { await sleep(20); });
  await f();
  ok($(sel).disabled === true, "이미 disabled 이던 단추는 저장 뒤에도 disabled 그대로");
  ok(saving(sel) === false, "딱지만 붙었다 떨어진다");
}
{
  // 여러 단추를 한꺼번에 — 판정 다섯 단추
  const five = ["#btn-ok", "#btn-ai", "#btn-save", "#btn-flag", "#btn-exc"];
  const f = lockWhile(five, async () => { await sleep(50); });
  const p = f();
  await sleep(10);
  ok(five.every(saving), "판정 다섯 단추가 한꺼번에 잠긴다", five.map(saving));
  await p;
  ok(five.every((s) => !saving(s)), "끝나면 다섯 다 풀린다", five.map(saving));
}

/* ============ D. 던져도 풀린다 ============ */
console.log("\nD. 저장이 실패하거나 코드가 던져도 잠긴 채 남지 않는다");
{
  let ran = 0;
  const sel = "#boxsave";
  const f = lockWhile([sel], async () => { ran++; await sleep(20); throw new Error("서버가 죽었다"); });
  let caught = null;
  try { await f(); } catch (e) { caught = e.message; }
  ok(caught === "서버가 죽었다", "던진 것은 그대로 바깥으로 나간다", caught);
  ok(saving(sel) === false, "그래도 딱지는 떨어진다");
  await f().catch(() => {});
  ok(ran === 2, "잠금이 풀려서 다시 누를 수 있다", { 돈횟수: ran });
}
{
  // async 가 아닌 함수가 곧바로 던지는 경우도 같다
  const sel = "#numsave";
  const f = lockWhile([sel], () => { throw new Error("곧바로"); });
  await f().catch(() => {});
  ok(saving(sel) === false, "곧바로 던져도 딱지가 안 남는다");
}

/* ============ E. 인자·돌려주는 값 ============ */
console.log("\nE. 인자와 돌려주는 값이 그대로 지나간다");
{
  let got = null;
  const f = lockWhile(["#btn-ok"], async (...args) => { got = args; return args.join("-"); });
  const r = await f("fixed", 2, null);
  ok(JSON.stringify(got) === JSON.stringify(["fixed", 2, null]), "인자 셋이 그대로 갔다", got);
  ok(r === "fixed-2-", "돌려주는 값도 그대로 온다", r);
}
{
  // doAction 처럼 값을 안 돌려주는 것
  const f = lockWhile(["#btn-ok"], async () => {});
  ok((await f()) === undefined, "안 돌려주는 함수는 undefined 그대로");
}

/* ============ F. 길마다 따로 잠근다 ============ */
console.log("\nF. 잠금은 길마다 따로 — 상자 저장 중에도 번호 저장은 눌린다");
{
  let box = 0, num = 0;
  const fb = lockWhile(["#boxsave"], async () => { box++; await sleep(120); });
  const fn = lockWhile(["#numsave"], async () => { num++; await sleep(20); });
  const p = fb();
  await sleep(10);
  await fn();
  ok(num === 1, "상자 저장이 도는 동안 번호 저장이 갔다", { 번호: num });
  ok(saving("#boxsave") === true && saving("#numsave") === false,
    "딱지도 각자 것만 붙어 있다", { 상자: saving("#boxsave"), 번호: saving("#numsave") });
  await p;
  ok(box === 1 && saving("#boxsave") === false, "상자 저장도 제대로 끝났다", { 상자: box });
}

/* ============ G. 단추가 화면에 없어도 ============ */
console.log("\nG. 단추가 화면에 없어도(숨은 모드·사용법 쪽) 깨지지 않는다");
{
  let ran = 0;
  const f = lockWhile([MISSING], async () => { ran++; await sleep(20); });
  const p1 = f(), p2 = f();
  await Promise.all([p1, p2]);
  ok(ran === 1, "요소가 없어도 잠금은 그대로 듣는다", { 돈횟수: ran });
}
{
  let ran = 0;
  const f = lockWhile(null, async () => { ran++; });      // 잠글 단추가 아예 없는 길(키보드 전용)
  await f();
  ok(ran === 1, "잠글 단추 목록이 없어도(null) 그냥 돈다", { 돈횟수: ran });
}

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
})().catch((e) => { console.error("시뮬레이션 오류:", e); process.exit(3); });
