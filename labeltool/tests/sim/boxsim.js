/* 상자 화면(D3·D4·손잡이 상한·겹친 상자 순환) — 함수 단위 시뮬레이션
   중요: 손으로 옮겨 적은 사본이 아니라 «지금 배포되는 app.js 의 함수 자체» 를 떼어 내 돌린다.
   (cycle_1/stage2/verify_resize_real.js 와 같은 방식)          사용법: node boxsim.js        */
"use strict";
const fs = require("fs"), path = require("path");
/* 2026-09-20 구조 사이클3: 화면 코드가 `static/js/*.js` 로 쪼개졌다 → `index.html` 의 <script>
   순서대로 이어 붙인 «한 덩어리» 에서 예전과 **똑같은** 문구 자르기를 한다(load_bundle.js).
   옛 로더로 돌리려면 `SIM_SRC=appjs node boxsim.js` (app.js 한 파일만 읽는다). */
const src = require("./lib/load_bundle.js").simSource();
function cut(a, b) {
  const i = src.indexOf(a), j = src.indexOf(b);
  if (i < 0 || j < 0 || j <= i) throw new Error("app.js 에서 구간을 못 찾음: " + a);
  return src.slice(i, j);
}
const CODE = cut("function bpush()", "function boxInfo(extra)")      // bpush, boxUndo
           + cut("function boxInfo(extra)", "function drawBoxes()")  // boxInfo
           + cut("const norm = (a, b, c, d)", "function delSelBox()")// 판정·마우스·bcommit·bHandleR
           + cut("async function saveBoxes()", "async function seedBoxes()");
const make = new Function("S", "HANDLE", "BKO", "flash", "$", "post", "errMsg", "who",
  CODE + "\nreturn {bpush,boxUndo,boxRedo,boxInfo,hitBox,hitBoxesAt,hitHandle,bHandleR,bcommit,"
       + "boxMouseDown,boxMouseMove,boxMouseUp,saveBoxes,PICKTOL};");

function mkEnv(o) {
  o = o || {};
  const S = { W: 1248, H: 1664, fruit: "peach", stem: o.stem || "210629-t4-17",
              view: { s: o.s || 1, tx: 0, ty: 0 },
              boxes: JSON.parse(JSON.stringify(o.boxes || [])),
              bsel: o.bsel === undefined ? -1 : o.bsel, btool: o.btool || "pick",
              bundo: [], bredo: [], bDirty: false, drag: null, bpick: null, dirty: false };
                                                            // bredo: 0921 U3 (state.js 와 같은 칸)
  const els = { "#boxinfo": { textContent: "" }, "#boxcls": { value: "fruit" }, "#note": { value: "" } };
  const env = { S: S, flashes: [], posts: [], els: els, resp: null, onPost: null };
  const F = make(S, 7, { fruit: "과실·알", bunch: "송이", other: "기타" },
    (m, bad) => env.flashes.push({ m: m, bad: !!bad }),
    (sel) => (els[sel] || (els[sel] = { value: "", textContent: "" })),
    (url, body) => { env.posts.push({ url: url, body: body }); if (env.onPost) env.onPost(); return Promise.resolve(env.resp); },
    (j, d) => (j && j.error) || d, () => "sim");
  env.F = F; env.info = () => els["#boxinfo"].textContent;
  return env;
}
const click = (env, x, y) => { env.F.boxMouseDown({ button: 0 }, x, y); env.F.boxMouseUp(); };
const drag = (env, x0, y0, pts) => {
  env.F.boxMouseDown({ button: 0 }, x0, y0);
  pts.forEach((p) => env.F.boxMouseMove(p[0], p[1]));
  env.F.boxMouseUp();
};
let tests = 0, fails = 0;
function ok(cond, name, extra) {
  tests++;
  if (!cond) { fails++; console.log("  [실패] " + name + (extra ? "   " + extra : "")); }
  else console.log("  [통과] " + name + (extra ? "   " + extra : ""));
}
const BIGSMALL = [{ cls: "fruit", src: "human", xyxy: [0, 0, 400, 400] },
                  { cls: "bunch", src: "human", xyxy: [100, 100, 150, 150] }];

(async () => {
/* ============ 1. D4 — 단순 클릭이 «저장 안 됨» 을 띄우지 않는가 ============ */
console.log("\n1. D4 — 되돌리기·«저장 안 됨» 은 상자가 실제로 바뀐 때만");
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  for (let k = 0; k < 100; k++) click(e, k % 2 ? 300 : 125, k % 2 ? 300 : 125);
  ok(e.S.bundo.length === 0 && e.S.bDirty === false,
    "고르기만 100회 → 되돌리기 0칸, 저장 안 됨 안 뜸", `bundo=${e.S.bundo.length} bDirty=${e.S.bDirty}`);
  ok(e.info().indexOf("저장 안 됨") < 0, "안내 글에 «저장 안 됨» 이 없다", `"${e.info()}"`);
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "draw" });
  for (let k = 0; k < 50; k++) click(e, 600, 600);           // 그리기 모드 제자리 클릭
  ok(e.S.bundo.length === 0 && e.S.bDirty === false && e.S.boxes.length === 2,
    "그리기 모드 제자리 클릭 50회 → 상자 안 생기고 기록도 없음", `bundo=${e.S.bundo.length} bDirty=${e.S.bDirty}`);
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "draw" });
  drag(e, 600, 600, [[601, 601]]);                            // 2px 미만
  ok(e.S.boxes.length === 2 && e.S.bundo.length === 0 && e.S.bDirty === false,
    "2px 미만 드래그 → 상자 안 생기고 기록도 없음");
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  drag(e, 125, 125, [[165, 165]]);                            // 작은 상자를 정말 옮김
  ok(e.S.bundo.length === 1 && e.S.bDirty === true &&
     JSON.stringify(e.S.boxes[1].xyxy) === JSON.stringify([140, 140, 190, 190]),
    "정말 옮기면 → 되돌리기 1칸 + 저장 안 됨", JSON.stringify(e.S.boxes[1].xyxy));
  e.F.boxUndo();
  ok(JSON.stringify(e.S.boxes[1].xyxy) === JSON.stringify([100, 100, 150, 150]) && e.S.bundo.length === 0,
    "그 한 칸을 되돌리면 처음 자리로");
}
{
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], bsel: 0, btool: "pick" });
  drag(e, 300, 300, [[350, 350]]);                            // se 모서리 크기조절
  ok(e.S.bundo.length === 1 && e.S.bDirty === true &&
     JSON.stringify(e.S.boxes[0].xyxy) === JSON.stringify([100, 100, 350, 350]),
    "정말 크기조절하면 → 되돌리기 1칸 + 저장 안 됨", JSON.stringify(e.S.boxes[0].xyxy));
}
{
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], bsel: 0, btool: "pick" });
  drag(e, 300, 300, [[350, 350], [300, 300]]);                // 끌었다가 제자리로 되돌려 놓음
  ok(e.S.bundo.length === 0 && e.S.bDirty === false,
    "끌었다가 제자리로 돌려놓으면 → 아무 기록도 안 남음");
}
{
  const e = mkEnv({ boxes: [], btool: "draw" });
  drag(e, 100, 100, [[200, 200]]);
  ok(e.S.boxes.length === 1 && e.S.bundo.length === 1 && e.S.bDirty === true && e.S.bsel === 0,
    "새 상자를 그리면 → 상자 1개 + 되돌리기 1칸 + 저장 안 됨");
}

/* ============ 2. 손잡이 반경 상한 ============ */
console.log("\n2. 손잡이 판정 반경 상한 (많이 축소하면 손잡이가 상자보다 커졌다)");
{
  const box = [100, 100, 200, 200];
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: box }], bsel: 0, btool: "pick", s: 0.03 });
  const rOld = 7 / 0.03, rNew = e.F.bHandleR(100, 100, 200, 200);
  console.log(`   배율 0.03x · 100x100 상자 : 예전 반경 ${rOld.toFixed(1)} 이미지px → 이제 ${rNew.toFixed(1)}`);
  ok(rOld > 200 && rNew <= 100 / 3 + 1e-9, "반경이 짧은 변의 1/3 로 묶였다", `${rNew.toFixed(2)} ≤ 33.33`);
  ok(e.F.hitHandle(0, 150, 150) === null, "상자 «가운데» 는 더 이상 모서리로 잡히지 않는다");
  e.F.boxMouseDown({ button: 0 }, 150, 150);
  ok(e.S.drag && e.S.drag.mode === "move", "그래서 축소 상태에서도 «옮기기» 가 된다",
    "mode=" + (e.S.drag && e.S.drag.mode));
  e.F.boxMouseUp();
}
{
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], bsel: 0, btool: "pick" });
  ok(e.F.hitHandle(0, 300, 300) === "se" && e.F.hitHandle(0, 100, 100) === "nw" &&
     e.F.hitHandle(0, 300, 100) === "ne" && e.F.hitHandle(0, 100, 300) === "sw",
    "배율 1x 보통 상자: 네 모서리가 전과 같이 잡힌다(회귀)");
  ok(e.F.hitHandle(0, 294, 294) === "se", "모서리에서 6px 안쪽도 잡힌다(반경 7 그대로)");
  ok(e.F.hitHandle(0, 200, 200) === null, "가운데는 안 잡힌다");
}
{
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 110, 110] }], bsel: 0, btool: "pick" });
  ok(e.F.hitHandle(0, 110, 110) === "se", "10px 짜리 작은 상자도 모서리는 잡힌다");
  ok(e.F.hitHandle(0, 105, 105) === null, "10px 상자의 가운데는 안 잡힌다(전에는 반경 7 이라 잡혔다)");
}
{
  let clean = true, worst = "";
  for (const s of [0.03, 0.1, 0.25, 1, 3, 30]) for (const L of [3, 6, 10, 50, 200, 1000]) {
    const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 100 + L, 100 + L] }], bsel: 0, btool: "pick", s: s });
    if (e.F.hitHandle(0, 100 + L / 2, 100 + L / 2) !== null) { clean = false; worst = `배율 ${s} 변 ${L}`; }
  }
  ok(clean, "배율 6가지 × 상자 크기 6가지 = 36가지에서 «가운데» 가 모서리로 안 잡힌다", worst && "깨진 곳 " + worst);
}

/* ============ 3. 겹친 상자 고르기 순환 ============ */
console.log("\n3. 겹친 상자 — 같은 자리를 다시 누르면 아래 상자로");
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  const seq = [];
  for (let k = 0; k < 5; k++) { click(e, 125, 125); seq.push(e.S.bsel); }
  ok(JSON.stringify(seq) === JSON.stringify([1, 0, 1, 0, 1]),
    "작은 상자(위) → 큰 상자(아래) → 다시 위 … 로 순환", "고른 순서 " + JSON.stringify(seq));
  ok(e.S.bundo.length === 0 && e.S.bDirty === false, "순환해도 «저장 안 됨» 은 안 뜬다");
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  click(e, 125, 125); ok(e.S.bsel === 1, "첫 클릭은 맨 위(작은) 상자");
  click(e, 300, 300); ok(e.S.bsel === 0, "다른 자리를 누르면 그 자리의 상자");
  click(e, 125, 125); ok(e.S.bsel === 1, "다시 겹친 자리를 처음 누르면 맨 위부터(순환 초기화)");
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  click(e, 125, 125); click(e, 126, 126);
  ok(e.S.bsel === 0, "손이 1px 떨린 정도(≤3화면px)는 «같은 자리» 로 보고 순환한다", "bsel=" + e.S.bsel);
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  click(e, 125, 125); click(e, 145, 145);
  ok(e.S.bsel === 1, "20px 떨어진 자리는 다른 자리 → 맨 위 상자", "bsel=" + e.S.bsel);
}
{
  const three = [{ cls: "fruit", src: "human", xyxy: [0, 0, 400, 400] },
                 { cls: "fruit", src: "human", xyxy: [50, 50, 300, 300] },
                 { cls: "bunch", src: "human", xyxy: [100, 100, 150, 150] }];
  const e = mkEnv({ boxes: three, btool: "pick" });
  const seq = [];
  for (let k = 0; k < 4; k++) { click(e, 125, 125); seq.push(e.S.bsel); }
  ok(JSON.stringify(seq) === JSON.stringify([2, 1, 0, 2]), "3겹도 2→1→0→2 로 순환", JSON.stringify(seq));
}
{
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  click(e, 600, 600);
  ok(e.S.bsel === -1, "빈 곳을 누르면 고른 것이 없어진다(전과 같음)");
  ok(e.S.bundo.length === 0 && e.S.bDirty === false, "그것도 «저장 안 됨» 을 안 띄운다");
}

/* ============ 4. D3 — 저장 응답으로 화면 덮어쓰기 ============ */
console.log("\n4. D3 — 저장 응답의 목록으로 화면을 덮어쓴다");
const REAL = path.join(__dirname, "resp_save_real.json");
if (fs.existsSync(REAL)) {
  const resp = JSON.parse(fs.readFileSync(REAL, "utf8"));
  const sent = JSON.parse(fs.readFileSync(path.join(__dirname, "body_five.json"), "utf8")).boxes;
  console.log(`   살아 있는 서버의 실제 응답: n_boxes=${resp.n_boxes} dropped=${resp.dropped} over=${resp.over} boxes 길이=${resp.boxes.length}`);
  const e = mkEnv({ boxes: sent, btool: "pick", bsel: 3 });
  e.resp = resp;
  await e.F.saveBoxes();
  ok(e.S.boxes.length === 3, "보낸 5개 중 서버가 남긴 3개로 화면이 바뀐다 (3차 판정 ③ 의 검사)",
    `${sent.length} → ${e.S.boxes.length}`);
  ok(e.S.bDirty === false, "덮어쓴 뒤 bDirty === false (bpush 뒤에 내렸다)");
  ok(e.S.bsel === -1, "고른 상자 번호는 -1 (서버가 id 를 1부터 다시 붙인다)");
  ok(e.S.bundo.length === 1, "버린 것이 있으므로 되돌리기 1칸");
  ok(JSON.stringify(e.S.boxes) === JSON.stringify(resp.boxes), "화면 목록이 응답과 «글자까지» 같다");
  ok(e.S.boxes.every((b) => b.id >= 1), "서버가 붙인 id 가 1부터 들어 있다",
    "id=" + e.S.boxes.map((b) => b.id).join(","));
  ok(e.info().indexOf("화면에서도 지웠음") >= 0, "안내 글이 «화면에서도 지웠음» 을 알린다", `"${e.info()}"`);
  ok(e.info().indexOf("저장 안 됨") < 0, "안내 글에 «저장 안 됨» 이 없다");
  const f = e.flashes[e.flashes.length - 1];
  ok(f && f.bad === true, "버린 것이 있으니 경고색 flash", `"${f && f.m}"`);
  e.F.boxUndo();
  ok(e.S.boxes.length === 5, "Ctrl+Z 로 «무엇이 사라졌나» 를 다시 볼 수 있다", `${e.S.boxes.length}개`);
  // 되읽기와 같은지
  const g = JSON.parse(fs.readFileSync(path.join(__dirname, "resp_get_real.json"), "utf8"));
  ok(JSON.stringify(resp.boxes) === JSON.stringify(g.boxes),
    "저장 응답 boxes == 되읽기(GET) boxes → «화면 = 파일» 이 선다");
} else { console.log("   resp_save_real.json 이 없어 실제 응답 검사를 건너뜀"); }
{
  const over = path.join(__dirname, "resp_over_real.json");
  if (fs.existsSync(over)) {
    const resp = JSON.parse(fs.readFileSync(over, "utf8"));
    const e = mkEnv({ boxes: new Array(3005).fill(0).map((_, i) => ({ cls: "fruit", src: "human", xyxy: [0, 0, 30, 30] })), btool: "pick" });
    e.resp = resp;
    await e.F.saveBoxes();
    ok(e.S.boxes.length === 3000 && e.S.bundo.length === 1 && e.S.bDirty === false,
      "3,005개 → 화면도 3,000개로 줄고 되돌리기 1칸", `over=${resp.over}`);
    const f = e.flashes[e.flashes.length - 1];
    ok(f && f.bad === true, "초과(over)도 경고색으로 띄운다", `"${f && f.m}"`);
    ok(e.info().indexOf("3,000개가 넘어 버린 것") >= 0, "안내 글이 초과 개수를 알린다");
  }
}
{ // 버린 것이 없으면 되돌리기 기록을 남기지 않는다
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] },
                            { cls: "bunch", src: "human", xyxy: [10, 10, 60, 80] }], btool: "pick", bsel: 1 });
  e.resp = { ok: true, n_boxes: 2, dropped: 0, over: 0, at: "2026-09-17 15:00",
             boxes: [{ id: 1, cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] },
                     { id: 2, cls: "bunch", src: "human", xyxy: [10, 10, 60, 80] }] };
  await e.F.saveBoxes();
  ok(e.S.bundo.length === 0, "버린 것이 없으면 되돌리기 기록을 남기지 않는다");
  ok(e.S.bDirty === false && e.S.bsel === -1 && e.S.boxes[0].id === 1, "그래도 목록은 덮어쓰고 bDirty=false");
  ok(e.info().indexOf("화면에서도 지웠음") < 0, "경고 문구도 안 붙는다", `"${e.info()}"`);
  const f = e.flashes[e.flashes.length - 1];
  ok(f && f.bad === false, "경고색이 아닌 보통 flash", `"${f && f.m}"`);
}
{ // 저장 도중에 사진을 바꿨다
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], btool: "pick" });
  e.resp = { ok: true, n_boxes: 0, dropped: 1, over: 0, at: "x", boxes: [] };
  e.onPost = () => { e.S.stem = "다른사진"; };      // 응답이 오기 전에 사람이 다음 사진으로 넘어갔다
  const keep = JSON.stringify(e.S.boxes);
  await e.F.saveBoxes();
  ok(JSON.stringify(e.S.boxes) === keep && e.S.bundo.length === 0,
    "stem 이 달라졌으면 화면을 건드리지 않는다");
  const f = e.flashes[e.flashes.length - 1];
  ok(f && /사진을 바꿔/.test(f.m), "그 사실을 flash 로 알린다", `"${f && f.m}"`);
}
{ // 0917 사이클3: «예전 서버는 boxes 를 안 준다» 방어 분기를 지웠다(ponytail −3줄).
  // 서버는 D3 계약대로 항상 boxes 를 준다 — 사이클2 2차가 실서버로 확인했고 사이클3 1차가 재확인했다.
  // 그래서 «Array.isArray 가 아니면 덮어쓰지 않는다» 시험은 지웠고, 새 계약만 남긴다.
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], btool: "pick" });
  e.resp = { ok: true, n_boxes: 0, dropped: 0, over: 0, at: "x", boxes: [] };
  await e.F.saveBoxes();
  ok(e.S.boxes.length === 0 && e.S.bDirty === false && e.S.bundo.length === 0,
    "서버가 «상자 0개» 를 주면 화면도 0개가 된다 (방어 분기 없이 그대로 덮어쓴다)");
}
{ // 저장 실패
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], btool: "pick" });
  e.S.bDirty = true;
  const keep = JSON.stringify(e.S.boxes);
  e.resp = { ok: false, error: "권한 없음" };
  await e.F.saveBoxes();
  ok(JSON.stringify(e.S.boxes) === keep && e.S.bDirty === true,
    "저장이 실패하면 화면을 덮어쓰지 않고 «저장 안 됨» 도 그대로 둔다");
}
/* ============ 5. U3 — 상자 «다시하기»(Ctrl+Y) ============
   2026-09-21 U3 로 새로 생겼다. 마스크·번호에만 있던 다시하기를 상자에도 붙였다.
   여기서 못박는 것: ① 그리기→Ctrl+Z→Ctrl+Y 가 돌아온다 ② 되돌리기와 다시하기가 서로의
   **정확한 반대**다(글자까지) ③ 새로 손대면 다시하기 갈래를 버린다 ④ bDirty 를 건드리지 않는다. */
console.log("\n5. U3 — 상자 다시하기(Ctrl+Y)");
{ // 체크리스트에 적힌 그 검증: 상자 그리기 → Ctrl+Z → Ctrl+Y
  const e = mkEnv({ boxes: [], btool: "draw" });
  drag(e, 100, 100, [[200, 200]]);
  const made = JSON.stringify(e.S.boxes);
  ok(e.S.boxes.length === 1 && e.S.bredo.length === 0, "새로 그리면 상자 1개 · 다시하기 0칸");
  e.F.boxUndo();
  ok(e.S.boxes.length === 0 && e.S.bundo.length === 0 && e.S.bredo.length === 1,
    "Ctrl+Z → 상자 0개 · 되돌리기 0칸 · 다시하기 1칸");
  e.F.boxRedo();
  ok(JSON.stringify(e.S.boxes) === made && e.S.bundo.length === 1 && e.S.bredo.length === 0,
    "Ctrl+Y → 그렸던 상자가 «글자까지» 그대로 돌아온다", made);
}
{ // 다시할 것이 없을 때
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  const keep = JSON.stringify(e.S.boxes);
  e.F.boxRedo();
  const f = e.flashes[e.flashes.length - 1];
  ok(JSON.stringify(e.S.boxes) === keep && e.S.bundo.length === 0,
    "다시할 것이 없으면 상자를 건드리지 않는다");
  ok(f && f.bad === true && /다시 실행할 상자 작업이 없습니다/.test(f.m),
    "«다시 실행할 상자 작업이 없습니다» 를 경고색으로 알린다", `"${f && f.m}"`);
  e.F.boxUndo();
  const g = e.flashes[e.flashes.length - 1];
  ok(g && g.bad === true && /되돌릴 상자 작업이 없습니다/.test(g.m),
    "되돌리기 쪽 안내는 예전 글자 그대로다(회귀)", `"${g && g.m}"`);
}
{ // 세 단계를 다 되돌렸다가 다 다시 실행하면 글자까지 원래대로
  const e = mkEnv({ boxes: [], btool: "draw" });
  const snap = [JSON.stringify(e.S.boxes)];
  for (const d of [[100, 100, 200, 200], [300, 300, 400, 400], [500, 500, 700, 700]]) {
    drag(e, d[0], d[1], [[d[2], d[3]]]);
    snap.push(JSON.stringify(e.S.boxes));
  }
  ok(e.S.boxes.length === 3 && e.S.bundo.length === 3, "세 번 그려서 되돌리기 3칸");
  let good = true;
  for (let k = 2; k >= 0; k--) { e.F.boxUndo(); if (JSON.stringify(e.S.boxes) !== snap[k]) good = false; }
  ok(good && e.S.bundo.length === 0 && e.S.bredo.length === 3,
    "세 번 되돌리면 한 칸씩 정확히 뒤로 간다 · 다시하기 3칸");
  good = true;
  for (let k = 1; k <= 3; k++) { e.F.boxRedo(); if (JSON.stringify(e.S.boxes) !== snap[k]) good = false; }
  ok(good && e.S.bredo.length === 0 && e.S.bundo.length === 3,
    "세 번 다시 실행하면 한 칸씩 정확히 앞으로 간다 · 마지막이 처음 그린 것과 같다");
}
{ // 되돌린 뒤 «새 작업» 을 하면 다시하기 갈래는 버린다 (그림판·포토샵과 같은 규칙)
  const e = mkEnv({ boxes: [], btool: "draw" });
  drag(e, 100, 100, [[200, 200]]);
  e.F.boxUndo();
  ok(e.S.bredo.length === 1, "되돌려서 다시하기 1칸");
  drag(e, 600, 600, [[700, 700]]);                            // 다른 것을 새로 그렸다
  ok(e.S.bredo.length === 0 && e.S.boxes.length === 1 &&
     JSON.stringify(e.S.boxes[0].xyxy) === JSON.stringify([600, 600, 700, 700]),
    "새로 그리면(bcommit) 다시하기 갈래를 버린다 — 옛 갈래가 되살아나지 않는다");
  e.F.boxRedo();
  ok(e.S.boxes.length === 1, "그 뒤 Ctrl+Y 를 눌러도 아무 일도 없다");
}
{ // bpush() 로 남기는 작업(전부 지우기·초벌·백업 되돌리기)도 갈래를 버린다
  const e = mkEnv({ boxes: BIGSMALL, btool: "pick" });
  drag(e, 125, 125, [[165, 165]]);
  e.F.boxUndo();
  ok(e.S.bredo.length === 1, "옮겼다 되돌려서 다시하기 1칸");
  e.F.bpush(); e.S.boxes = [];                                 // «전부 지우기» 와 같은 길
  ok(e.S.bredo.length === 0, "bpush() 를 쓰는 작업도 다시하기 갈래를 버린다");
}
{ // 되돌리기·다시하기는 bDirty 를 건드리지 않는다 (U1 의 «*» 가 흔들리지 않게)
  const e = mkEnv({ boxes: [], btool: "draw" });
  drag(e, 100, 100, [[200, 200]]);
  const was = e.S.bDirty;
  e.F.boxUndo(); const afterUndo = e.S.bDirty;
  e.F.boxRedo(); const afterRedo = e.S.bDirty;
  ok(was === true && afterUndo === true && afterRedo === true,
    "되돌리기·다시하기가 «저장 안 됨» 딱지를 바꾸지 않는다(둘이 서로의 반대)",
    `${was} → ${afterUndo} → ${afterRedo}`);
}
{ // 30칸 상한 — bundo 와 같은 수
  const e = mkEnv({ boxes: [], btool: "draw" });
  for (let k = 0; k < 40; k++) drag(e, 10 + k, 10, [[110 + k, 110]]);
  ok(e.S.bundo.length === 30, "되돌리기는 30칸에서 멈춘다(회귀)", `bundo=${e.S.bundo.length}`);
  for (let k = 0; k < 40; k++) e.F.boxUndo();
  ok(e.S.bredo.length === 30, "다시하기도 30칸을 넘지 않는다", `bredo=${e.S.bredo.length}`);
}
{ // 저장이 무엇을 버렸을 때(bpush) 다시하기 갈래가 남아 있으면 안 된다
  const e = mkEnv({ boxes: [{ cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }], btool: "draw" });
  drag(e, 500, 500, [[600, 600]]);
  e.F.boxUndo();
  ok(e.S.bredo.length === 1, "저장 전 되돌려서 다시하기 1칸");
  e.resp = { ok: true, n_boxes: 1, dropped: 1, over: 0, at: "x",
             boxes: [{ id: 1, cls: "fruit", src: "human", xyxy: [100, 100, 300, 300] }] };
  await e.F.saveBoxes();
  ok(e.S.bredo.length === 0 && e.S.bundo.length === 1,
    "저장하면(버린 것이 있어 bpush) 다시하기 갈래를 버린다 — 파일에 없는 상자가 Ctrl+Y 로 되살아나지 않는다");
}

console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
})().catch((e) => { console.error("시뮬레이션 오류:", e); process.exit(3); });
