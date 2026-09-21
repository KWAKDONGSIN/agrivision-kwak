/* 붓 굵기를 «도구마다» 기억하나 — 진짜 코드(mask.js 의 setTool·brushKey·saveBrush·loadBrush)를
   떼어 내 가짜 화면에서 돌린다.  작성: 2026-09-21 (260921 편의·안정성 사이클 · U8)

왜 있나
  «붓 30 · 지우개 40 을 따로 기억한다» 는 **오가는 순서**가 전부다 — 붓에서 지우개로, 다시 붓으로,
  과일을 바꿔서, 번호 편집을 켠 채로… 이 길을 진짜 파이어폭스로 한 번에 하나씩 재면 오래 걸린다.
  여기서는 localStorage 를 손에 쥔 채 칸 이름과 값을 한 글자씩 들여다본다(b17 이 사람 손으로 다시 잰다).
  사본 재구현이 아니다 — `app/static/js/mask.js` 의 글자를 그대로 떼어 낸다(locksim·backupsim 과 같은 방법).

무엇을 못박나
  A. 칸 이름 — 붓은 `brush:<과일>`(옛 이름 그대로) · 지우개만 뒤에 `:erase`
  B. 붓 30 / 지우개 40 을 따로 — 도구를 몇 번 왕복해도 각자 제 값으로 돌아온다
  C. 처음 지우개를 고르면 **쓰던 붓 굵기를 물려받는다**(없는 기본값을 지어내지 않는다)
  D. 과일마다도 따로다 (사과 지우개 40 · 복숭아 지우개 12)
  E. 굵기를 안 쓰는 도구(다각형·자동채움·✋)는 붓 칸에 같이 있다 — 오가도 값이 안 흔들린다
  F. 번호 편집 모드에서는 도구가 안 바뀌니 칸도 그대로다
  G. localStorage 가 막힌 브라우저(사생활 모드)에서도 안 깨진다
  H. 0918부터 쌓인 옛 값(`brush:apple`)이 옮겨 심기 없이 그대로 «붓 굵기» 로 살아난다
  I. 슬라이더(와 [ ] 키)를 움직이면 **지금 도구 칸**에 적힌다 · 화면 숫자도 따라온다
*/
"use strict";
const src = require("./lib/load_bundle.js").simSource();

const HEAD = "function setTool(t) {";
const TAIL = '\n$("#alpha").oninput';
const a = src.indexOf(HEAD);
if (a < 0) throw new Error("mask.js 에서 setTool 을 못 찾음");
const b = src.indexOf(TAIL, a);
if (b < 0) throw new Error("mask.js 에서 붓 굵기 구간의 끝을 못 찾음");
const CODE = src.slice(a, b);
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (mask.js — setTool·brushKey·saveBrush·loadBrush·#brush)");

/* ---------------- 가짜 화면 ---------------- */
function mkStore(broken) {
  const m = new Map();
  return {
    _m: m,
    getItem(k) { if (broken) throw new Error("사생활 모드"); return m.has(k) ? m.get(k) : null; },
    setItem(k, v) { if (broken) throw new Error("사생활 모드"); m.set(k, String(v)); },
    dump() { return Object.fromEntries([...m.entries()].filter(([k]) => k.startsWith("brush:"))); }
  };
}

/** 가짜 화면 한 벌을 새로 차린다(브라우저를 새로 연 것과 같다). */
function mount(opts) {
  opts = opts || {};
  const store = opts.store || mkStore(false);
  const S = { fruit: opts.fruit || "apple", tool: "brush", brush: 30, panTool: false,
              poly: [], numMode: false, dirty: false };
  const el = {
    "#brush": { value: "30" },
    "#brushv": { textContent: "30" }
  };
  const flashed = [];
  const $ = (s) => el[s] || (el[s] = { value: "", textContent: "" });
  const tools = ["brush", "erase", "polyadd", "polysub", "smartadd", "smartsub"].map((t) => ({
    dataset: { tool: t }, _on: false,
    classList: { toggle: function (c, v) { if (c === "on") this._o._on = !!v; } }
  }));
  tools.forEach((t) => { t.classList._o = t; });
  const $$ = () => tools;
  const flash = (m, bad) => flashed.push([m, !!bad]);
  const api = new Function("S", "$", "$$", "flash", "localStorage",
    CODE + "\nreturn { setTool, sizeTool, brushKey, saveBrush, loadBrush, brushEl: $('#brush') };")(
    S, $, $$, flash, store);
  /* 슬라이더를 움직였을 때(사람 손 · [ ] 키가 부르는 길과 **똑같다**) */
  api.slide = (n) => { $("#brush").value = String(n); $("#brush").oninput({ target: $("#brush") }); };
  return Object.assign(api, { S, store, el, flashed, $ });
}

let tests = 0, fails = 0;
const ok = (c, n, x) => {
  tests++;
  if (!c) { fails++; console.log("  [실패] " + n + (x !== undefined ? "  " + JSON.stringify(x) : "")); }
  else console.log("  [통과] " + n + (x !== undefined ? "  " + JSON.stringify(x) : ""));
};
/** 화면에 보이는 것까지 한꺼번에 — [S.brush, 슬라이더, 옆 숫자] */
const shown = (m) => [m.S.brush, +m.el["#brush"].value, +m.el["#brushv"].textContent];
const same = (m, n) => shown(m).every((v) => v === n);

/* ============ A. 칸 이름 ============ */
console.log("\nA. 칸 이름 — 붓은 옛 이름 그대로, 지우개만 «:erase»");
{
  const m = mount({ fruit: "apple" });
  ok(m.brushKey() === "brush:apple", "붓일 때는 `brush:apple` (0918부터 쓰던 이름 그대로)", m.brushKey());
  m.setTool("erase");
  ok(m.brushKey() === "brush:apple:erase", "지우개일 때는 `brush:apple:erase`", m.brushKey());
  m.setTool("polyadd");
  ok(m.brushKey() === "brush:apple", "다각형은 붓 칸에 같이 있다", m.brushKey());
  m.S.fruit = null;
  ok(m.brushKey() === "brush:-", "과일을 아직 안 골랐으면 `brush:-`", m.brushKey());
  m.S.fruit = "apple";
  ok(m.brushKey("erase") === "brush:apple:erase" && m.brushKey("brush") === "brush:apple",
    "칸 이름을 손으로 집어 줄 수도 있다(건너가기 전 칸에 넣을 때 쓴다)",
    [m.brushKey("brush"), m.brushKey("erase")]);
}

/* ============ B. 붓 30 / 지우개 40 을 따로 ============ */
console.log("\nB. 붓 30 · 지우개 40 — 왕복해도 각자 제 값");
{
  const m = mount();
  m.slide(30);
  ok(same(m, 30), "붓을 30 으로 놓았다", shown(m));
  m.setTool("erase");
  m.slide(40);
  ok(same(m, 40), "지우개를 40 으로 놓았다", shown(m));
  m.setTool("brush");
  ok(same(m, 30), "붓으로 돌아오면 **30**(지우개 40 을 물려받지 않는다)", shown(m));
  m.setTool("erase");
  ok(same(m, 40), "다시 지우개로 가면 40", shown(m));
  for (let i = 0; i < 5; i++) { m.setTool("brush"); m.setTool("erase"); }
  ok(m.S.brush === 40, "다섯 번 왕복해도 지우개는 40", m.S.brush);
  m.setTool("brush");
  ok(m.S.brush === 30, "그 뒤 붓도 30 그대로", m.S.brush);
  ok(JSON.stringify(m.store.dump()) === JSON.stringify({ "brush:apple": "30", "brush:apple:erase": "40" }),
    "브라우저에 적힌 것도 칸 둘뿐이다", m.store.dump());
}
{
  // 붓이 지우개보다 큰 반대 경우도 같다 (숫자를 바꿔 넣어도 규칙이 같은가)
  const m = mount();
  m.slide(120);
  m.setTool("erase"); m.slide(6);
  m.setTool("brush");
  ok(m.S.brush === 120, "붓 120 · 지우개 6 도 마찬가지", m.S.brush);
  m.setTool("erase");
  ok(m.S.brush === 6, "지우개 6 그대로", m.S.brush);
}

/* ============ C. 처음 지우개는 붓 굵기를 물려받는다 ============ */
console.log("\nC. 처음 지우개를 고르면 쓰던 붓 굵기 그대로(없는 기본값을 지어내지 않는다)");
{
  const m = mount();
  m.slide(18);
  m.setTool("erase");
  ok(same(m, 18), "지우개 칸이 비어 있으니 18 그대로다", shown(m));
  ok(m.store._m.get("brush:apple") === "18", "건너가면서 붓 칸에 18 을 적어 두었다", m.store.dump());
  m.setTool("brush");
  ok(same(m, 18), "돌아와도 18", shown(m));
  m.setTool("erase"); m.slide(52); m.setTool("brush");
  ok(m.S.brush === 18 && m.store._m.get("brush:apple:erase") === "52",
    "지우개에서 굵기를 바꾼 그때부터 칸이 따로 산다", [m.S.brush, m.store.dump()]);
}

/* ============ D. 과일마다도 따로 ============ */
console.log("\nD. 과일이 다르면 칸도 다르다 (사과 지우개 40 · 복숭아 지우개 12)");
{
  const store = mkStore(false);
  const m1 = mount({ store, fruit: "apple" });
  m1.slide(30); m1.setTool("erase"); m1.slide(40);
  const m2 = mount({ store, fruit: "peach" });
  m2.slide(8); m2.setTool("erase"); m2.slide(12);
  ok(m2.S.brush === 12, "복숭아 지우개는 12", m2.S.brush);
  m2.setTool("brush");
  ok(m2.S.brush === 8, "복숭아 붓은 8", m2.S.brush);
  const m3 = mount({ store, fruit: "apple" });     // 사과를 다시 연다(브라우저를 새로 연 것과 같다)
  m3.loadBrush();
  ok(m3.S.brush === 30, "사과를 다시 열면 붓은 30", m3.S.brush);
  m3.setTool("erase");
  ok(m3.S.brush === 40, "사과 지우개는 40 그대로 — 복숭아 12 에 안 덮였다", m3.S.brush);
  ok(Object.keys(store.dump()).sort().join(",")
     === "brush:apple,brush:apple:erase,brush:peach,brush:peach:erase",
    "칸은 과일×도구 넷", Object.keys(store.dump()).sort());
}

/* ============ E. 굵기를 안 쓰는 도구는 붓 칸에 같이 ============ */
console.log("\nE. 다각형·자동채움·✋ 는 굵기를 안 쓴다 — 붓 칸에 같이 두고 값을 안 흔든다");
{
  const m = mount();
  m.slide(24);
  ["polyadd", "polysub", "smartadd", "smartsub", "pan", "brush"].forEach((t) => m.setTool(t));
  ok(same(m, 24), "여섯 도구를 돌아도 붓은 24 그대로", shown(m));
  ok(m.store._m.get("brush:apple:erase") === undefined,
    "지우개 칸은 아직 안 생겼다(안 쓴 칸을 미리 만들지 않는다)", m.store.dump());
  m.setTool("erase"); m.slide(70);
  m.setTool("polyadd");
  ok(m.S.brush === 24, "지우개에서 다각형으로 가면 붓 칸(24)으로 돌아온다", m.S.brush);
  m.slide(26);                                   // 다각형에서 슬라이더를 움직이면
  m.setTool("brush");
  ok(m.S.brush === 26 && m.store._m.get("brush:apple") === "26",
    "그 값은 붓 칸에 적힌다(다각형 전용 칸을 만들지 않는다)", [m.S.brush, m.store.dump()]);
  m.setTool("erase");
  ok(m.S.brush === 70, "지우개 70 은 그 사이에도 안 흔들렸다", m.S.brush);
}

/* ============ F. 번호 편집 모드 ============ */
console.log("\nF. 번호 편집 모드에서는 도구가 잠겨 있다 — 칸도 그대로");
{
  const m = mount();
  m.slide(30);
  m.setTool("erase"); m.slide(40);
  m.S.numMode = true;
  const before = m.S.tool, n = m.flashed.length;
  m.setTool("brush");
  ok(m.S.tool === before, "K 로 번호 편집을 켜 두면 B 를 눌러도 도구가 안 바뀐다", m.S.tool);
  ok(m.flashed.length === n + 1 && m.flashed[n][1] === true, "잠겼다고 붉은 알림만 뜬다", m.flashed[n]);
  ok(m.S.brush === 40 && m.store._m.get("brush:apple") === "30",
    "칸도 그대로다(잠긴 채 값이 뒤섞이지 않는다)", [m.S.brush, m.store.dump()]);
}

/* ============ G. localStorage 가 막힌 브라우저 ============ */
console.log("\nG. 사생활 모드(localStorage 가 던지는 브라우저)에서도 안 깨진다");
{
  const m = mount({ store: mkStore(true) });
  let threw = null;
  try { m.slide(44); m.setTool("erase"); m.setTool("brush"); m.loadBrush(); } catch (e) { threw = String(e); }
  ok(threw === null, "적지도 읽지도 못해도 도구 바꾸기가 그냥 된다", threw);
  ok(m.S.brush === 44, "굵기는 지금 쓰던 값 그대로 남는다(기억만 못 할 뿐)", m.S.brush);
  ok(m.S.tool === "brush", "도구도 제대로 바뀌었다", m.S.tool);
}

/* ============ H. 옛 값·이상한 값 ============ */
console.log("\nH. 0918부터 쌓인 옛 값이 그대로 «붓 굵기» 로 살아난다 · 이상한 값은 걸러 낸다");
{
  const store = mkStore(false);
  store.setItem("brush:apple", "77");             // 옛 이름으로만 적혀 있던 값(t2_ui 다-1 이 적는 그것)
  const m = mount({ store, fruit: "apple" });
  m.loadBrush();
  ok(same(m, 77), "옮겨 심지 않아도 77 이 붓 굵기로 온다", shown(m));
  m.setTool("erase");
  ok(m.S.brush === 77, "지우개 칸이 없으니 77 을 물려받는다(옛 사용자가 놀라지 않는다)", m.S.brush);
}
{
  const store = mkStore(false);
  const m = mount({ store, fruit: "apple" });
  store.setItem("brush:apple", "9999"); m.loadBrush();
  ok(m.S.brush === 200, "너무 큰 값은 200 으로 자른다", m.S.brush);
  store.setItem("brush:apple", "1"); m.loadBrush();
  ok(m.S.brush === 2, "너무 작은 값은 2 로 올린다", m.S.brush);
  const keep = m.S.brush;
  store.setItem("brush:apple", "이상한글자"); m.loadBrush();
  ok(m.S.brush === keep, "글자가 적혀 있으면 그냥 두고 넘어간다", m.S.brush);
  store.setItem("brush:apple", "0"); m.loadBrush();
  ok(m.S.brush === keep, "0 도 마찬가지(2~200 밖은 안 받는다)", m.S.brush);
}

/* ============ I. 슬라이더·[ ] 키가 지금 도구 칸에 적는다 ============ */
console.log("\nI. 슬라이더와 [ ] 키는 **지금 도구** 칸에 적는다 · 옆 숫자도 따라온다");
{
  const m = mount();
  m.slide(30);
  // ⚠ 진짜 브라우저는 `textContent = 30` 을 글자 "30" 으로 바꿔 넣지만 이 가짜 칸은 **숫자 30 그대로**
  //   받는다(코드가 `$("#brushv").textContent = S.brush` 로 숫자를 넣는다). 자가 틀린 것이지
  //   코드가 틀린 것이 아니다 → 숫자로 견준다. 글자로 보이는지는 b17 이 진짜 화면에서 잰다.
  ok(+m.el["#brushv"].textContent === 30 && m.S.dirty === true,
    "옆 숫자와 다시 그리기 요청이 따라온다", [m.el["#brushv"].textContent, m.S.dirty]);
  m.setTool("erase");
  // [ ] 키가 하는 것과 **글자 그대로 같은 길**: 슬라이더 값을 ±4 하고 oninput 을 부른다
  m.el["#brush"].value = String(Math.min(200, m.S.brush + 4));
  m.el["#brush"].oninput({ target: m.el["#brush"] });
  ok(m.S.brush === 34 && m.store._m.get("brush:apple:erase") === "34",
    "지우개에서 ] 를 누르면 34 가 **지우개 칸**에 적힌다", [m.S.brush, m.store.dump()]);
  ok(m.store._m.get("brush:apple") === "30", "붓 칸 30 은 안 건드렸다", m.store.dump());
  m.setTool("brush");
  ok(same(m, 30), "붓으로 돌아오면 화면 숫자까지 30 으로 돌아온다", shown(m));
}

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
