// 그림판(/) 모든 기능을 실제 마우스·키보드로 눌러 보는 끝-끝 시험 — 파이어폭스·크로미움 둘 다
// 작성: 2026-09-24
// 쓰는 법(모래상자 서버를 먼저 띄운다 — 실서버 5111 에는 절대 쓰지 않는다):
//   node tests/browser/paint_e2e.mjs <base_url> <firefox|chromium> <out_dir>
// 결과: <out_dir>/<browser>_result.json · 스크린샷 · 저장 직전 라벨 L(<browser>_L.bin, uint16 LE) — 디스크 대조는 paint_e2e_check.py
import fs from "node:fs";
import path from "node:path";
import { chromium, firefox } from "/home/kds0206/.local/share/playwright-runtime/node_modules/playwright/index.mjs";

const [BASE, BR = "firefox", OUT = "."] = process.argv.slice(2);
if (!BASE || /:5111\b/.test(BASE)) { console.error("모래상자 주소를 주세요(5111 금지)"); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });
const res = { browser: BR, checks: [], errors: [] };
const ok = (name, cond, detail = "") => { res.checks.push({ name, ok: !!cond, detail: String(detail).slice(0, 300) }); console.log((cond ? "PASS " : "FAIL ") + name + (detail ? "  " + String(detail).slice(0, 160) : "")); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b = await (BR === "chromium" ? chromium : firefox).launch();
const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
const page = await ctx.newPage();
page.on("pageerror", (e) => res.errors.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) res.errors.push("console: " + m.text()); });
// 404 는 주소로 따로 모은다(초벌·번호가 없는 사진의 404 는 정상 — 화면이 «없습니다» 로 안내한다)
res.http404 = []; page.on("response", (r) => { if (r.status() === 404) res.http404.push(r.url().replace(/^https?:\/\/[^/]+/, "")); });
const dialogs = [];                      // 다음 확인창에 줄 답(true=확인)을 차례로
page.on("dialog", async (d) => {
  const ans = dialogs.length ? dialogs.shift() : true;
  res.checks.push({ name: "dialog: " + d.message().slice(0, 60), ok: true, detail: ans ? "확인" : "취소" });
  if (d.type() === "prompt") await d.accept("시험봇"); else if (ans) await d.accept(); else await d.dismiss();
});
const ev = (expr) => page.evaluate((e) => window.eval(e), expr);
const idle = async (ms = 20000) => { const t = Date.now(); while (Date.now() - t < ms) { if (await ev("!S.busy && !S.samBusy && document.querySelector('#loading').style.display!=='block'")) return; await sleep(100); } };
const shot = (n) => page.screenshot({ path: path.join(OUT, `${BR}_${n}.png`) });

// 사진 좌표 → 화면 좌표
async function scr(x, y) {
  return ev(`(()=>{const r=stage.getBoundingClientRect();return [r.left+S.ox+(${x}+0.5)*S.z, r.top+S.oy+(${y}+0.5)*S.z]})()`);
}
// 빈(0) 네모 칸 찾기
const findEmpty = (n) => ev(`(()=>{const n=${n};for(let y=Math.floor(S.H*0.3);y<S.H-n;y+=17)for(let x=Math.floor(S.W*0.3);x<S.W-n;x+=17){let e=true;for(let yy=0;yy<n&&e;yy+=3)for(let xx=0;xx<n;xx+=3)if(S.L[(y+yy)*S.W+x+xx]){e=false;break}if(e)return [x,y]}return null})()`);
const valAt = (x, y) => ev(`S.L[${y}*S.W+${x}]`);
const countVal = (v) => ev(`(()=>{let n=0;for(let i=0;i<S.L.length;i++)if(S.L[i]===${v})n++;return n})()`);
async function dumpL() {
  const b64 = await ev("(()=>{const u=new Uint8Array(S.L.buffer,S.L.byteOffset,S.L.byteLength);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode.apply(null,u.subarray(i,i+32768));return btoa(s)})()");
  fs.writeFileSync(path.join(OUT, `${BR}_L.bin`), Buffer.from(b64, "base64"));
  res.W = await ev("S.W"); res.H = await ev("S.H");
}
async function key(k) { await page.keyboard.press(k); await sleep(80); }

try {
  await page.goto(BASE + "/");
  await page.evaluate(() => localStorage.setItem("who", "시험봇"));
  await page.goto(BASE + "/");
  await page.waitForFunction(() => window.eval("S.L && S.stem"), null, { timeout: 30000 });
  await idle();
  // 복숭아의 첫 사진으로 고정(과일 목록 순서에 기대지 않게)
  await page.selectOption("#fruit", "peach"); await sleep(300);
  await page.waitForFunction(() => window.eval("S.fruit==='peach' && S.L"), null, { timeout: 30000 }); await idle();
  const stem0 = await ev("S.stem");
  res.stem = stem0;
  ok("열림: 사진·라벨", await ev("S.W>0 && S.L.length===S.W*S.H"), stem0);
  ok("진행 표시", /진행 \d+\/\d+/.test(await ev("document.querySelector('#prog').textContent")));
  await shot("01_open");

  // ── 붓: 새 번호로 빈 곳에 긋기
  const E = await findEmpty(120); ok("빈 칸 찾음", E, JSON.stringify(E));
  const [ex, ey] = E;
  await key("b"); await key("n");
  const cur = await ev("S.cur");
  let [sx, sy] = await scr(ex + 20, ey + 20), [tx, ty] = await scr(ex + 100, ey + 20);
  await page.mouse.move(sx, sy); await page.mouse.down(); await page.mouse.move(tx, ty, { steps: 8 }); await page.mouse.up();
  ok("붓: 칠해짐", (await valAt(ex + 60, ey + 20)) === cur, `cur=${cur}`);
  ok("붓: 저장 안 됨 표시", await ev("S.dirty && document.querySelector('#t-dirty').textContent.length>0"));
  // 되돌리기·다시
  await key("Control+z"); ok("Ctrl+Z", (await valAt(ex + 60, ey + 20)) === 0);
  await key("Control+y"); ok("Ctrl+Y", (await valAt(ex + 60, ey + 20)) === cur);
  // 오른쪽 끌기 = 지우기
  await page.mouse.move(sx, sy); await page.mouse.down({ button: "right" }); await page.mouse.move(tx, ty, { steps: 8 }); await page.mouse.up({ button: "right" });
  ok("붓 오른쪽 = 지우기", (await valAt(ex + 60, ey + 20)) === 0);
  await key("Control+z");
  // 지우개
  await key("e");
  await page.mouse.move(sx, sy); await page.mouse.down(); await page.mouse.move(tx, ty, { steps: 8 }); await page.mouse.up();
  ok("지우개", (await valAt(ex + 60, ey + 20)) === 0);
  await key("Control+z");
  // 붓 굵기 [ ]
  const s0 = await ev("S.size"); await key("]"); const s1 = await ev("S.size"); await key("[");
  ok("붓 굵기 ] [", s1 > s0 && (await ev("S.size")) <= s1, `${s0}→${s1}`);

  // ── 올가미: 빈 곳에 세모
  await key("l"); await key("n"); const lc = await ev("S.cur");
  const P = [[ex + 10, ey + 60], [ex + 110, ey + 60], [ex + 60, ey + 115]];
  let p0 = await scr(...P[0]); await page.mouse.move(...p0); await page.mouse.down();
  for (const q of [P[1], P[2], P[0]]) { const s = await scr(...q); await page.mouse.move(...s, { steps: 6 }); }
  await page.mouse.up();
  ok("올가미: 안이 칠해짐", (await valAt(ex + 60, ey + 80)) === lc, `lc=${lc}`);
  // Esc 로 올가미 취소
  p0 = await scr(ex + 5, ey + 5); await page.mouse.move(...p0); await page.mouse.down();
  await page.mouse.move(...(await scr(ex + 40, ey + 5)), { steps: 4 }); await key("Escape"); await page.mouse.up();
  ok("Esc = 올가미 취소", (await ev("lassoPts")) === null && (await valAt(ex + 20, ey + 6)) !== lc);

  // ── 채우기통: 오른쪽 = 덩어리 지우기, 왼쪽 = 새 번호
  await key("f");
  await page.mouse.click(...(await scr(ex + 60, ey + 80)), { button: "right" });
  ok("채우기 오른쪽 = 덩어리 지우기", (await countVal(lc)) === 0);
  await key("Control+z");
  await page.mouse.click(...(await scr(ex + 60, ey + 80)));
  const fv = await valAt(ex + 60, ey + 80);
  ok("채우기 왼쪽 = 새 번호", fv !== lc && fv > 0, `${lc}→${fv}`);

  // ── 스포이트
  await key("i"); await page.mouse.click(...(await scr(ex + 60, ey + 80)));
  ok("스포이트 → 색 집고 붓으로", (await ev("S.cur")) === fv && (await ev("S.tool")) === "brush");

  // ── 보기: 돋보기·손·확대 단추·가운데로·키
  const z0 = await ev("S.z");
  await key("z"); await page.mouse.click(...(await scr(ex, ey))); await sleep(300);
  ok("돋보기 클릭 = 확대", (await ev("S.z")) > z0 * 1.4);
  await key("h"); const ox0 = await ev("S.ox");
  await page.mouse.move(700, 400); await page.mouse.down(); await page.mouse.move(600, 350, { steps: 5 }); await page.mouse.up();
  ok("손 = 옮기기", Math.abs((await ev("S.ox")) - ox0 + 100) < 2);
  await page.click("#zoombar .fitbtn"); await sleep(300);
  ok("⤢ 가운데로", await ev("(()=>{const f=fitView();return Math.abs(S.z-f.z)<1e-6&&Math.abs(S.ox-f.ox)<1e-6&&Math.abs(S.oy-f.oy)<1e-6})()"));
  const dirtyBefore = await ev("S.undo.length");
  await page.click("#zoombar [data-act=zoom-in]"); await sleep(300);
  ok("＋ 단추 확대, 칠하지 않음", (await ev("S.z")) > z0 * 1.2 && (await ev("S.undo.length")) === dirtyBefore);
  await key("1"); await sleep(300); ok("1 = 100%", Math.abs((await ev("S.z")) - 1) < 1e-6 && (await ev("document.querySelector('#zpct').textContent")) === "100%");
  await key("-"); await sleep(300); ok("- = 축소", (await ev("S.z")) < 1);
  await key("0"); await sleep(300);
  await page.mouse.move(683, 380); await page.mouse.wheel(0, -300); await sleep(400);
  ok("휠 = 확대", (await ev("S.z")) > z0 * 1.1);
  await key("0"); await sleep(300);
  // 스페이스+끌기
  await key("b");
  await page.keyboard.down(" "); const ox1 = await ev("S.ox");
  await page.mouse.move(700, 400); await page.mouse.down(); await page.mouse.move(650, 400, { steps: 4 }); await page.mouse.up();
  await page.keyboard.up(" ");
  ok("스페이스+끌기 = 옮기기(칠하지 않음)", Math.abs((await ev("S.ox")) - ox1 + 50) < 2);
  await key("0"); await sleep(300);
  // 원본 보기 V · ` · 번호 T
  await key("v"); ok("V = 색 숨김", (await ev("ovC.style.opacity")) === "0"); await key("v");
  await page.keyboard.down("Backquote"); await sleep(80); ok("` 누르는 동안 원본", (await ev("ovC.style.opacity")) === "0");
  await page.keyboard.up("Backquote"); await sleep(80); ok("` 떼면 색 복귀", (await ev("ovC.style.opacity")) !== "0");
  await key("t"); ok("T = 번호 숨김", (await ev("S.showNums")) === false); await key("t");
  // 메뉴 열고 Esc
  await page.click(".menu .mbtn >> nth=0"); ok("메뉴 열림", await ev("!!document.querySelector('.menu.open')"));
  await key("Escape"); ok("Esc = 메뉴 닫힘", await ev("!document.querySelector('.menu.open')"));
  await shot("02_tools");

  // ── ✨ 클릭 칠하기(SAM 도우미 5112 가 켜져 있을 때)
  await key("s");
  const S2 = await findEmpty(60);
  const before = await ev("S.undo.length");
  await page.mouse.click(...(await scr(S2[0] + 30, S2[1] + 30)));
  await sleep(300); await idle(60000);
  const samMsg = await ev("document.querySelector('#msg').textContent");
  const samDone = (await ev("S.undo.length")) > before;
  ok("✨ 클릭 = 칠함(또는 못 찾음 안내)", samDone || /못 찾았|꺼져/.test(samMsg), samMsg);
  if (samDone) {
    const v1 = await ev("samLast.val"), n1 = await countVal(v1);
    await page.mouse.click(...(await scr(S2[0] + 30, S2[1] + 30))); await sleep(300); await idle(60000);
    ok("✨ 같은 자리 다시 = 다른 모양", /번째 모양/.test(await ev("document.querySelector('#msg').textContent")), `n1=${n1} → ${await countVal(v1)}`);
    // 지금 모양 안의 한 점을 오른쪽 클릭(두 번째 후보는 누른 점을 안 품을 수도 있다)
    const pin = await ev(`(()=>{const v=${v1},W=S.W;for(const R of [4,2,1]){for(let i=0;i<S.L.length;i++){if(S.L[i]!==v)continue;const x=i%W,y=(i/W)|0;let all=true;for(let d=-R;d<=R&&all;d++)for(let e=-R;e<=R;e++)if(S.L[(y+d)*W+x+e]!==v){all=false;break}if(all)return [x,y]}}return null})()`);
    await page.mouse.click(...(await scr(...pin)), { button: "right" });
    ok("✨ 오른쪽 = 그 열매 통째로 지우기", (await countVal(v1)) === 0, `남은 ${await countVal(v1)}`);
  }
  // 네모 끌기
  const S3 = await findEmpty(80);
  const u3 = await ev("S.undo.length");
  await page.mouse.move(...(await scr(S3[0] + 5, S3[1] + 5))); await page.mouse.down();
  await page.mouse.move(...(await scr(S3[0] + 75, S3[1] + 75)), { steps: 6 }); await page.mouse.up();
  await sleep(300); await idle(60000);
  const boxMsg = await ev("document.querySelector('#msg').textContent");
  ok("✨ 네모 = 칠함(또는 못 찾음 안내)", (await ev("S.undo.length")) > u3 || /못 찾았|꺼져/.test(boxMsg), boxMsg);

  // ── 메뉴: 초벌·번호 나누기·원본·전부 지우기 (모두 Ctrl+Z 로 되돌려지는지)
  async function act(name) { await ev(`ACTS[${JSON.stringify(name)}]()`); await sleep(200); await idle(30000); return ev("document.querySelector('#msg').textContent"); }
  const snapSum = () => ev("(()=>{let h=0;for(let i=0;i<S.L.length;i+=7)h=(h*31+S.L[i])|0;return h})()");
  for (const a of ["draft-add", "split-gt", "split-draft"]) {
    const h0 = await snapSum(), u = await ev("S.undo.length");
    const m = await act(a);
    const changed = (await ev("S.undo.length")) > u;
    if (changed) { await key("Control+z"); ok(`${a} → Ctrl+Z 로 원래대로`, (await snapSum()) === h0, m); }
    else ok(`${a} (바뀐 것 없음/없는 사진)`, true, m);
  }
  dialogs.push(true);
  { const h0 = await snapSum(), m = await act("draft-replace"); if ((await snapSum()) !== h0) { await key("Control+z"); ok("draft-replace → Ctrl+Z", (await snapSum()) === h0, m); } else ok("draft-replace (없음)", true, m); }
  dialogs.push(true);
  { const h0 = await snapSum(); await act("clear-all"); ok("전부 지우기", (await ev("S.L.every(v=>v===0)"))); await key("Control+z"); ok("전부 지우기 → Ctrl+Z", (await snapSum()) === h0); }

  // ── 저장: 붓 한 획 더 긋고 Ctrl+S → 디스크 대조용으로 L 을 남긴다
  await key("b"); await key("n"); const sv = await ev("S.cur");
  [sx, sy] = await scr(ex + 20, ey + 100); [tx, ty] = await scr(ex + 90, ey + 100);
  await page.mouse.move(sx, sy); await page.mouse.down(); await page.mouse.move(tx, ty, { steps: 6 }); await page.mouse.up();
  res.saved_id = sv;
  await key("Control+s"); await sleep(300); await idle();
  const saveMsg = await ev("document.querySelector('#msg').textContent");
  ok("Ctrl+S 저장", /저장했습니다/.test(saveMsg) && !(await ev("S.dirty")), saveMsg);
  ok("목록에 ✓", (await ev("document.querySelector('#photo').selectedOptions[0].textContent")).startsWith("✓"));

  // ── 넘기기: 바뀐 채로 D → 취소면 머묾, 확인이면 저장 후 넘어감
  [sx, sy] = await scr(ex + 20, ey + 110);
  await page.mouse.move(sx, sy); await page.mouse.down(); await page.mouse.move(sx + 20, sy, { steps: 3 }); await page.mouse.up();
  dialogs.push(false); await key("d"); await sleep(400);
  ok("바뀐 채로 D + 취소 = 머묾", (await ev("S.stem")) === stem0 && (await ev("S.dirty")));
  await key("Control+z"); await key("Control+z");
  // 다시 한 획 지운 게 dirty 로 남음 → 확인 = 저장하고 넘어감. 이 저장이 stem0 의 마지막 저장이므로 여기서 L 을 남긴다
  await dumpL();
  dialogs.push(true); await key("d"); await sleep(500); await idle();
  ok("D + 확인 = 저장하고 넘어감", (await ev("S.stem")) !== stem0 && !(await ev("S.dirty")));
  const stem1 = await ev("S.stem");
  await key("a"); await idle(); ok("A = 이전 사진", (await ev("S.stem")) === stem0);
  await key("Control+Enter"); await sleep(300); await idle();
  ok("Ctrl+Enter = 저장하고 다음", (await ev("S.stem")) === stem1);

  // ── 빼기 / 빼기 취소
  await ev("ACTS.exclude()"); await sleep(300); await idle();
  ok("이 사진 빼기 → 다음으로", (await ev("S.stem")) !== stem1);
  await key("a"); await idle();
  ok("빼기 표시 ✕", (await ev("document.querySelector('#photo').selectedOptions[0].textContent")).startsWith("✕"));
  await ev("ACTS.unexclude()"); await sleep(300); await idle();
  ok("빼기 취소", !(await ev("document.querySelector('#photo').selectedOptions[0].textContent")).startsWith("✕"));

  // ── 목록: 찾기·안 한 것만·과일 바꾸기
  await page.fill("#q", stem1.slice(-4)); await page.press("#q", "Enter"); await sleep(300);
  ok("이름 찾기", (await ev("document.querySelector('#photo').options.length")) >= 1);
  await page.fill("#q", ""); await page.press("#q", "Enter"); await sleep(300); await idle();
  await page.check("#only-todo"); await sleep(300); await idle();
  ok("안 한 것만", await ev("[...document.querySelector('#photo').options].every(o=>o.textContent.startsWith('　'))"));
  await page.uncheck("#only-todo"); await sleep(300); await idle();
  // 입력칸에서 친 글자는 단축키가 안 먹는다
  const t0 = await ev("S.tool"); await page.click("#q"); await page.keyboard.type("e"); await sleep(100);
  ok("입력칸 글자 ≠ 단축키", (await ev("S.tool")) === t0); await page.fill("#q", "");
  // 맞는 사진이 없으면 그림판을 비운다(다른 사진 위에 칠하지 않게)
  await page.fill("#q", "zzz_없는이름"); await page.press("#q", "Enter"); await sleep(300);
  ok("맞는 사진 없음 = 그림판 비움", (await ev("S.L === null && S.stem === '' && ovC.width === 0")));
  await page.fill("#q", ""); await page.press("#q", "Enter"); await sleep(300); await idle();
  ok("검색 지우면 다시 열림", await ev("!!S.L"));
  await page.locator("#msg").click();          // 입력칸에서 포커스를 빼야 단축키가 먹는다
  // 바뀐 채로 과일 바꾸기 + 취소 = 목록 표시도 원래 과일로(코드 검수 지적)
  { const fr = await ev("S.fruit"); await key("b"); const [ax, ay] = await scr(ex + 20, ey + 40);
    await page.mouse.move(ax, ay); await page.mouse.down(); await page.mouse.move(ax + 20, ay, { steps: 3 }); await page.mouse.up();
    dialogs.push(false); await page.selectOption("#fruit", "grape"); await sleep(400);
    ok("바뀐 채로 과일 바꾸기 + 취소 = 표시 되돌림", (await ev("document.querySelector('#fruit').value")) === fr && (await ev("S.fruit")) === fr);
    await key("Control+z"); }
  dialogs.push(true);
  await page.selectOption("#fruit", "grape"); await sleep(500);
  await page.waitForFunction(() => window.eval("S.fruit==='grape' && S.L"), null, { timeout: 30000 }); await idle();
  ok("과일 바꾸기(포도)", (await ev("S.fruit")) === "grape");
  await shot("03_grape");

  // ── 작은 화면(노트북 1280×720 · 1024×600)
  for (const [w, h] of [[1280, 720], [1024, 600]]) {
    await page.setViewportSize({ width: w, height: h }); await sleep(400);
    const lay = await ev("(()=>{const q=(s)=>document.querySelector(s).getBoundingClientRect();const st=q('#stage'),zb=q('#zoombar'),sv=q('#save');return {stageH:st.height|0,zoomIn:zb.right<=st.right+1&&zb.bottom<=st.bottom+1,saveVis:sv.right<=innerWidth&&sv.bottom<=innerHeight,scrollX:document.documentElement.scrollWidth>innerWidth}})()");
    ok(`${w}×${h} 화면 배치`, lay.stageH > 200 && lay.zoomIn && lay.saveVis && !lay.scrollX, JSON.stringify(lay));
    await shot(`04_${w}x${h}`);
  }
} catch (e) {
  res.errors.push("시험 중단: " + (e.stack || e.message));
  await shot("99_crash").catch(() => {});
}
ok("브라우저 오류 없음", res.errors.length === 0, res.errors.join(" | "));
fs.writeFileSync(path.join(OUT, `${BR}_result.json`), JSON.stringify(res, null, 1));
const fails = res.checks.filter((c) => !c.ok).length;
console.log(`\n${BR}: ${res.checks.length - fails}/${res.checks.length} 통과`);
await b.close();
process.exit(fails ? 1 : 0);
