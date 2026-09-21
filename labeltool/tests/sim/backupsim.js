/* 저장 전 작업의 «임시 백업·복구» — 진짜 코드(backup.js)를 떼어 내 가짜 브라우저에서 돌린다.
   작성: 2026-09-21 (260921 편의·안정성 사이클 · S5)

왜 있나
  백업은 **브라우저가 죽은 뒤** 에만 쓸모가 있는 장치다. 진짜 파이어폭스로는 그 순간을 만들 수 없고
  (탭을 죽이면 시험도 같이 죽는다), «자리가 없을 때 조용히 포기하는지» 는 5MB 를 채워야 볼 수 있다.
  그래서 `app/static/js/backup.js` 의 코드를 **글자 그대로 떼어 내** 가짜 localStorage 위에서 돌린다
  (사본 재구현이 아니다 — backup.js 를 고치면 이 시험이 같이 따라간다. leavesim·modesim 과 같은 방법).

무엇을 못박나
  A. 접기·펴기(런렝스)가 **한 화소도 안 틀리고** 되돌아온다. 깨진 글자는 null(반쯤 채운 배열 금지).
  B. 1분마다 적는 것 — 저장 안 한 것만, 없으면 지난 백업까지 지운다.
  C. 다시 열 때 «되돌릴까요» — 상자·번호 불러오기가 **끝난 뒤**에 되돌린다.
  D. «취소» 를 누르면 지우고 다시 묻지 않는다.
  E. 자리가 없거나 너무 크면 **조용히** 포기한다(붉은 알림을 띄우지 않는다).
*/
"use strict";
const src = require("./lib/load_bundle.js").simSource();

const HEAD = 'const KEY = "backup_260921";';
const TAIL = "setInterval(backupNow, EVERY);";
const a = src.indexOf(HEAD), b = src.indexOf(TAIL);
if (a < 0 || b < 0) throw new Error("backup.js 에서 구간을 못 찾음");
const CODE = src.slice(a, b + TAIL.length);
console.log("떼어 낸 코드 " + CODE.split("\n").length + "줄 (backup.js — 백업·복구)");

/* ---------------- 가짜 브라우저 ---------------- */
const LS = {
  d: {}, fail: false,
  getItem(k) { return k in this.d ? this.d[k] : null; },
  setItem(k, v) {
    if (this.fail) { const e = new Error("자리가 없습니다"); e.name = "QuotaExceededError"; throw e; }
    this.d[k] = String(v);
  },
  removeItem(k) { delete this.d[k]; }
};
const S = { fruit: "peach", stem: "210629-t1-01", W: 4, H: 4,
            ed: null, edDirty: false, boxes: [], bDirty: false, inst: null, numDirty: false,
            bsel: 0, dirty: false };
const called = [];                             // UI.* 를 누가 불렀나
const flashed = [];
const asked = [];
let answer = true;
const UI = {
  flash: (m, bad) => flashed.push([m, !!bad]),
  pushUndo: () => { called.push("pushUndo"); S.edDirty = true; },
  applyBits: (bits) => { called.push("applyBits"); S.ed = bits; },
  bpush: () => { called.push("bpush"); S.bDirty = true; },
  boxInfo: (m) => called.push("boxInfo:" + m),
  repaintNum: () => called.push("repaintNum")
};
const timers = [];
new Function("S", "UI", "flash", "localStorage", "confirm", "setInterval",
  CODE + "\n;global.__X = { backupNow, backupOffer, packRuns, unpackRuns, boxSig, KEY, LIMIT, EVERY };")(
  S, UI, UI.flash, LS, (m) => { asked.push(m); return answer; },
  (f, ms) => { timers.push([f, ms]); return timers.length; });
const X = global.__X;

let tests = 0, fails = 0;
const ok = (c, n, x) => { tests++; if (!c) { fails++; console.log("  [실패] " + n + (x ? "  " + x : "")); }
                          else console.log("  [통과] " + n + (x ? "  " + x : "")); };

function reset(f) {
  LS.d = {}; LS.fail = false;
  S.fruit = "peach"; S.stem = "210629-t1-01"; S.W = 4; S.H = 4;
  S.ed = null; S.edDirty = false; S.boxes = []; S.bDirty = false; S.inst = null; S.numDirty = false;
  S.bsel = 0; S.dirty = false;
  Object.assign(S, f || {});
  called.length = 0; flashed.length = 0; asked.length = 0; answer = true;
}
const bits = (arr) => Uint8Array.from(arr);
const u16 = (arr) => Uint16Array.from(arr);
const eq = (x, y) => x && y && x.length === y.length && Array.prototype.every.call(x, (v, i) => v === y[i]);

(async function () {

/* ── A. 접기·펴기 ───────────────────────────────────────────────── */
console.log("\nA. 런렝스로 접고 펴기 — 한 화소도 안 틀린다");
{
  const m = new Uint8Array(16);
  m[5] = 1; m[6] = 1; m[7] = 1; m[15] = 1;
  const p = X.packRuns(m);
  ok(eq(X.unpackRuns(p, 16, Uint8Array), m), "마스크 16칸이 그대로 돌아온다", p);
  ok(p.length < 30, "같은 값이 이어지면 짧아진다", p.length + "글자");

  const big = new Uint8Array(200000);           // 2,000칸짜리 덩어리 100개 = 실제 마스크에 가까운 모양
  for (let i = 0; i < 100; i++) big.fill(1, i * 2000, i * 2000 + 700);
  const pb = X.packRuns(big);
  ok(eq(X.unpackRuns(pb, big.length, Uint8Array), big), "20만 칸도 그대로 돌아온다",
     `${big.length}칸 → ${pb.length}글자`);
  ok(pb.length < big.length / 100, "20만 칸이 100분의 1 밑으로 접힌다", pb.length + "글자");

  const n = u16([0, 0, 3, 3, 3, 7, 0, 260]);    // 번호는 255 보다 큰 값도 있다(Uint16)
  ok(eq(X.unpackRuns(X.packRuns(n), 8, Uint16Array), n), "번호 배열(255 넘는 값)도 그대로 돌아온다",
     X.packRuns(n));

  ok(X.unpackRuns("1,3", 16, Uint8Array) === null, "길이가 모자라면 null (반쯤 채운 배열을 안 준다)");
  ok(X.unpackRuns("1,99", 16, Uint8Array) === null, "길이가 넘치면 null");
  ok(X.unpackRuns("깨진글자", 16, Uint8Array) === null, "깨진 글자는 null");
  ok(eq(X.unpackRuns(X.packRuns(new Uint8Array(16)), 16, Uint8Array), new Uint8Array(16)),
     "전부 0 인 것도 되돌아온다");
}

/* ── B. 1분마다 적기 ───────────────────────────────────────────── */
console.log("\nB. 1분마다 — 저장 안 한 것만 적는다");
ok(timers.length === 1 && timers[0][1] === X.EVERY && X.EVERY === 60000,
   "백업을 1분(60,000ms)마다 걸어 두었다", `${timers.length}개 · ${timers[0] && timers[0][1]}ms`);

reset({ ed: bits([0, 1, 1, 0]), edDirty: false });
ok(X.backupNow() === 0 && LS.getItem(X.KEY) === null,
   "저장 안 한 것이 없으면 적지 않는다");

reset({ ed: bits([0, 1, 1, 0]), edDirty: false });
LS.d[X.KEY] = "{\"v\":1}";
ok(X.backupNow() === 0 && LS.getItem(X.KEY) === null,
   "저장 안 한 것이 없어지면 **지난 백업도 지운다**(다 저장한 사진에 되돌리기를 권하지 않게)");

reset({ ed: bits([0, 1, 1, 0]), edDirty: true, inst: u16([0, 5, 5, 0]), numDirty: false });
const n1 = X.backupNow();
const o1 = JSON.parse(LS.getItem(X.KEY));
ok(n1 > 0, "마스크가 더러우면 적는다", n1 + "글자");
ok(o1.fruit === "peach" && o1.stem === "210629-t1-01" && o1.W === 4 && o1.H === 4,
   "어느 과일·어느 사진·어떤 크기인지 함께 적는다");
ok(typeof o1.at === "number" && Math.abs(Date.now() - o1.at) < 5000, "적은 시각도 함께 적는다");
ok(o1.ed !== undefined && o1.inst === undefined && o1.boxes === undefined,
   "**저장 안 한 것만** 적는다(번호는 깨끗하므로 안 적는다)", Object.keys(o1).join(","));
ok(flashed.length === 0, "백업은 화면에 아무 말도 하지 않는다(사람 일을 막지 않는다)");

reset({ boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4] }], bDirty: true });
const o2 = (X.backupNow(), JSON.parse(LS.getItem(X.KEY)));
ok(o2.boxes && o2.boxes.length === 1 && o2.boxes[0].xyxy[3] === 4, "상자는 그대로(좌표·종류) 적는다");

reset({ inst: u16([0, 3, 3, 9]), numDirty: true });
const o3 = (X.backupNow(), JSON.parse(LS.getItem(X.KEY)));
ok(o3.inst !== undefined && o3.ed === undefined, "번호만 더러우면 번호만 적는다");

reset({ stem: null, ed: bits([1, 1]), edDirty: true });
ok(X.backupNow() === 0, "사진을 아직 안 열었으면 적을 것이 없다");

/* ── C. 다시 열 때 되돌리기 ─────────────────────────────────────── */
console.log("\nC. 같은 사진을 다시 열면 «되돌릴까요»");
const ED = bits([0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1]);   // 4×4 = 16칸

function put(extra) {                          // 백업 한 벌 만들어 넣는다
  return LS.d[X.KEY] = JSON.stringify(Object.assign(
    { v: 1, fruit: "peach", stem: "210629-t1-01", W: 4, H: 4, at: Date.now() - 90000 }, extra));
}

reset({ ed: new Uint8Array(16) });             // 서버에서 읽은 것 = 전부 0
put({ ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === true, "백업이 있으면 되돌린다");
ok(asked.length === 1, "딱 한 번 묻는다", asked.length + "번");
ok(asked[0].indexOf("저장하지 않은 작업") >= 0 && asked[0].indexOf("칠한 영역") >= 0,
   "무엇이 남아 있는지 말한다", (asked[0] || "").split("\n")[0]);
ok(/\d+월 \d+일 \d\d:\d\d/.test(asked[0]), "언제 적어 둔 것인지 말한다",
   (asked[0].match(/\d+월 \d+일 \d\d:\d\d/) || [])[0]);
ok(eq(S.ed, ED), "마스크가 백업 값으로 되돌아왔다");
ok(called.indexOf("pushUndo") === 0 && called.indexOf("applyBits") === 1,
   "**되돌리기를 쌓은 뒤** 칠한다 → Ctrl+Z 로 서버 값으로 되돌아갈 수 있다", called.join(" → "));
ok(S.edDirty === true, "되돌린 것은 «저장 안 됨» 이다(사람이 Ctrl+S 를 눌러야 한다)");
ok(flashed.length === 1 && flashed[0][1] === false && flashed[0][0].indexOf("Ctrl+S") >= 0,
   "무엇을 되돌렸고 다음에 무엇을 할지 알려 준다", flashed[0] && flashed[0][0]);

reset({ boxes: [{ cls: "peach", xyxy: [9, 9, 10, 10] }] });
put({ boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4] }, { cls: "peach", xyxy: [5, 6, 7, 8] }] });
ok(await X.backupOffer(null) === true && S.boxes.length === 2 && S.boxes[1].xyxy[0] === 5,
   "상자도 되돌아온다", S.boxes.length + "개");
ok(called[0] === "bpush" && S.bDirty === true && S.bsel === -1,
   "상자도 Ctrl+Z 로 되돌아가게 쌓고, 고른 상자는 푼다", called.join(" → "));

reset({ inst: u16(new Array(16).fill(0)) });
put({ inst: X.packRuns(u16([0, 0, 2, 2, 0, 0, 2, 2, 0, 0, 0, 0, 7, 7, 0, 0])) });
ok(await X.backupOffer(null) === true && S.inst[2] === 2 && S.inst[12] === 7,
   "번호도 되돌아온다");
ok(S.numDirty === true && called.indexOf("repaintNum") >= 0,
   "번호는 «저장 안 됨» 으로 두고 화면을 다시 칠한다", called.join(" → "));

console.log("\nC-2. 묻지 **않아야** 하는 자리");
reset({ ed: new Uint8Array(16) });
put({ stem: "다른사진", ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === false && asked.length === 0, "다른 사진의 백업이면 묻지 않는다");
ok(LS.getItem(X.KEY) !== null, "그리고 그 백업을 **지우지 않는다**(그 사진을 열면 되돌릴 수 있게)");

reset({ ed: new Uint8Array(16) });
put({ fruit: "apple", ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === false && asked.length === 0, "다른 과일의 백업이면 묻지 않는다");

reset({ ed: new Uint8Array(16) });
put({ W: 8, H: 8, ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === false && asked.length === 0 && LS.getItem(X.KEY) === null,
   "사진 크기가 달라졌으면 묻지 않고 지운다(못 믿는 백업)");

reset({ ed: ED.slice() });                     // 서버에서 읽은 것이 백업과 **같다** = 이미 저장했다
put({ ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === false && asked.length === 0 && LS.getItem(X.KEY) === null,
   "저장한 뒤 다시 열면 묻지 않고 지운다(«저장이 안 됐나» 하고 놀라지 않게)");

reset({ boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4], id: 1, src: "auto" }] });
put({ boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4] }] });
ok(await X.backupOffer(null) === false && asked.length === 0,
   "상자는 서버가 번호(id)를 다시 붙여도 «같은 상자» 로 본다");

reset({ ed: new Uint8Array(16) });
ok(await X.backupOffer(null) === false && asked.length === 0, "백업이 아예 없으면 묻지 않는다");
LS.d[X.KEY] = "{깨진 JSON";
ok(await X.backupOffer(null) === false && asked.length === 0, "백업이 깨졌으면 묻지 않는다");
LS.d[X.KEY] = JSON.stringify({ v: 99, fruit: "peach", stem: "210629-t1-01", W: 4, H: 4, ed: "0,16" });
ok(await X.backupOffer(null) === false && asked.length === 0, "모르는 판(v) 이면 묻지 않는다");

console.log("\nC-3. 상자·번호 불러오기가 **끝난 뒤**에 되돌린다");
reset({ ed: new Uint8Array(16), boxes: [] });
put({ boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4] }] });
let go;
const ready = new Promise((r) => { go = r; });
const running = X.backupOffer(ready);
await Promise.resolve();
ok(asked.length === 0, "불러오기가 끝나기 전에는 묻지 않는다");
S.boxes = [{ cls: "peach", xyxy: [9, 9, 9, 9], id: 1 }];      // 늦게 끝난 loadBoxes() 가 서버 값을 넣는다
go();
ok(await running === true && S.boxes.length === 1 && S.boxes[0].xyxy[0] === 1,
   "불러오기가 끝난 뒤에 되돌리므로 서버 값에 덮이지 않는다", JSON.stringify(S.boxes[0].xyxy));

reset({ ed: new Uint8Array(16) });
put({ ed: X.packRuns(ED) });
ok(await X.backupOffer(Promise.reject(new Error("불러오기 실패"))) === true,
   "불러오기가 실패해도(약속이 깨져도) 되돌리기는 묻는다");

/* ── D. 거절 ─────────────────────────────────────────────────── */
console.log("\nD. «취소» 를 누르면");
reset({ ed: new Uint8Array(16) });
answer = false;
put({ ed: X.packRuns(ED) });
ok(await X.backupOffer(null) === false, "되돌리지 않는다");
ok(eq(S.ed, new Uint8Array(16)) && called.length === 0 && S.edDirty === false,
   "화면을 한 칸도 건드리지 않는다");
ok(LS.getItem(X.KEY) === null, "백업을 지운다 — 같은 사진을 또 열어도 **다시 묻지 않는다**");
ok(flashed.length === 0, "거절에는 알림도 띄우지 않는다");

/* ── E. 자리가 없을 때 — 조용히 포기 ───────────────────────────── */
console.log("\nE. 자리가 없거나 너무 클 때 — 조용히 포기한다");
reset({ ed: bits([0, 1, 1, 0]), edDirty: true });
LS.fail = true;
ok(X.backupNow() === 0, "localStorage 가 «자리 없음» 을 던지면 0 을 돌려준다(터지지 않는다)");
ok(LS.getItem(X.KEY) === null, "반쯤 적힌 것을 남기지 않는다");
ok(flashed.length === 0 && asked.length === 0,
   "**조용히** 포기한다 — 붉은 알림도, 확인창도 없다(백업은 덤이다)");

reset({ ed: bits([0, 1, 1, 0]), edDirty: true });
LS.d[X.KEY] = "{\"v\":1,\"지난\":\"백업\"}";
LS.fail = true;
ok(X.backupNow() === 0 && LS.getItem(X.KEY) === null,
   "자리가 없으면 지난 백업도 지운다(옛 것이 새 것인 척하지 않게)");

{
  reset({ edDirty: true });
  const noisy = new Uint8Array(3000000);       // 한 칸씩 0/1 이 엇갈리는 최악 — 접어도 안 줄어든다
  for (let i = 0; i < noisy.length; i++) noisy[i] = i & 1;
  S.ed = noisy; S.W = 1000; S.H = 3000;
  ok(X.packRuns(noisy) === null, "접어도 안 줄어드는 것은 **세다 말고** 포기한다(null)");
  const t0 = Date.now();
  const r = X.backupNow();
  const ms = Date.now() - t0;
  ok(r === 0, "그런 사진은 적지 않는다", `${noisy.length.toLocaleString()}칸 · ${ms}ms`);
  ok(ms < 400, "포기가 **빨라야** 한다 — 1분마다 화면이 멈추면 붓질이 끊긴다", ms + "ms");
  ok(LS.getItem(X.KEY) === null && flashed.length === 0, "이때도 조용하다");

  reset({ edDirty: true, bDirty: true, boxes: [{ cls: "peach", xyxy: [1, 2, 3, 4] }] });
  S.ed = noisy; S.W = 1000; S.H = 3000;
  const o = (X.backupNow(), JSON.parse(LS.getItem(X.KEY) || "null"));
  ok(o && o.ed === undefined && o.boxes.length === 1,
     "마스크를 포기해도 **상자는 적는다**(적을 수 있는 것은 적는다)");
}

{
  reset({ edDirty: true });                    // 현실적인 큰 사진 하나 — 시간과 크기를 재 둔다
  const m = new Uint8Array(1080 * 1920);
  for (let y = 300; y < 1500; y++) for (let x = 200; x < 900; x++) m[y * 1080 + x] = 1;
  S.ed = m; S.W = 1080; S.H = 1920;
  const t0 = Date.now();
  const r = X.backupNow();
  ok(r > 0 && r < X.LIMIT, "1080×1920 사진(둥근 덩어리)은 상한 안에 든다",
     `${r.toLocaleString()}글자 · ${Date.now() - t0}ms`);
}

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
})();
