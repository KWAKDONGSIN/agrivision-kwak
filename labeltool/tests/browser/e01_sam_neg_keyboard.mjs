// E01 ✨ Shift+클릭(떼어 내기)과 «키보드만으로 한 장 끝내기»를 실제 마우스·키보드로 눌러 보는 시험 — 모래상자 전용
// 작성: 2026-09-25
// 쓰는 법: bash tests/browser/run_e01.sh [포트=5441]  (직접: node e01_sam_neg_keyboard.mjs <base_url> <firefox|chromium> <out_dir>)
// ✨ 도우미 답(/api/sam·/api/sam_similar)은 page.route 로 정해진 모양을 돌려준다 — 도우미(GPU7)를 쓰지 않고, 답이 늘 같아 결과가 흔들리지 않는다.
import fs from "node:fs";
import path from "node:path";
import { chromium, firefox } from "/home/kds0206/.local/share/playwright-runtime/node_modules/playwright/index.mjs";

const [BASE, BR = "firefox", OUT = "."] = process.argv.slice(2);
if (!BASE || /:5111\b/.test(BASE)) { console.error("모래상자 주소를 주세요(5111 금지)"); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });
const res = { browser: BR, checks: [], errors: [], notes: [] };
const ok = (name, cond, detail = "") => { res.checks.push({ name, ok: !!cond, detail: String(detail).slice(0, 300) }); console.log((cond ? "PASS " : "FAIL ") + name + (detail ? "  " + String(detail).slice(0, 160) : "")); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const b = await (BR === "chromium" ? chromium : firefox).launch();
const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
const page = await ctx.newPage();
page.on("pageerror", (e) => res.errors.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) res.errors.push("console: " + m.text()); });
page.on("dialog", (d) => (d.type() === "prompt" ? d.accept("시험봇") : d.accept()));
const ev = (expr) => page.evaluate((e) => window.eval(e), expr);
const idle = async (ms = 20000) => { const t = Date.now(); while (Date.now() - t < ms) { if (await ev("!S.busy && !S.samBusy && document.querySelector('#loading').style.display!=='block'")) return; await sleep(100); } };
const shot = (n) => page.screenshot({ path: path.join(OUT, `e01_${BR}_${n}.png`) });
const msg = () => ev("$('#msg').textContent");
async function key(k) { await page.keyboard.press(k); await sleep(80); }
async function scr(x, y) { return ev(`(()=>{const r=stage.getBoundingClientRect();return [r.left+S.ox+(${x}+0.5)*S.z, r.top+S.oy+(${y}+0.5)*S.z]})()`); }
const findEmpty = (w, h) => ev(`(()=>{for(let y=Math.floor(S.H*0.2);y<S.H-${h};y+=13)for(let x=Math.floor(S.W*0.2);x<S.W-${w};x+=13){let e=true;for(let yy=0;yy<${h}&&e;yy+=2)for(let xx=0;xx<${w};xx+=2)if(S.L[(y+yy)*S.W+x+xx]){e=false;break}if(e)return [x,y]}return null})()`);
const valAt = (x, y) => ev(`S.L[${y}*S.W+${x}]`);
const countVal = (v) => ev(`(()=>{let n=0;for(let i=0;i<S.L.length;i++)if(S.L[i]===${v})n++;return n})()`);
// 원들의 합집합 모양을 바깥 네모 + 0/255 PNG(도우미 후보와 같은 꼴)로 — 브라우저 canvas 로 만든다
const cand = (circles) => ev(`(()=>{const C=${JSON.stringify(circles)};
  const x0=Math.min(...C.map(c=>c[0]-c[2])),y0=Math.min(...C.map(c=>c[1]-c[2])),x1=Math.max(...C.map(c=>c[0]+c[2])),y1=Math.max(...C.map(c=>c[1]+c[2]));
  const w=x1-x0+1,h=y1-y0+1,cv=document.createElement('canvas');cv.width=w;cv.height=h;const g=cv.getContext('2d'),d=g.createImageData(w,h);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4;d.data[i+3]=255;if(C.some(c=>(x0+x-c[0])**2+(y0+y-c[1])**2<=c[2]*c[2]))d.data[i]=d.data[i+1]=d.data[i+2]=255}
  g.putImageData(d,0,0);return {x0,y0,w,h,png:cv.toDataURL('image/png').split(',')[1]}})()`);
// 가짜 도우미: 부른 횟수를 세고, 지금 정해 둔 답을 돌려준다
const fake = { sam: { n: 0, cands: [] }, sim: { n: 0, cands: [] } };
await page.route(/\/api\/sam(\?|$)/, async (r) => { fake.sam.n++; await r.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, sec: 0.01, cands: fake.sam.cands }) }); });
await page.route(/\/api\/sam_similar(\?|$)/, async (r) => { fake.sim.n++; await r.fulfill({ contentType: "application/json", body: JSON.stringify({ ok: true, sec: 0.01, cands: fake.sim.cands }) }); });

async function openPeach() {
  await page.goto(BASE + "/");
  await page.evaluate(() => { localStorage.setItem("who", "시험봇"); localStorage.removeItem("paint.sort"); });
  await page.goto(BASE + "/");
  await page.waitForFunction(() => window.eval("S.L && S.stem"), null, { timeout: 30000 }); await idle();
  await page.selectOption("#fruit", "peach"); await sleep(300);
  await page.waitForFunction(() => window.eval("S.fruit==='peach' && S.L"), null, { timeout: 30000 }); await idle();
}

try {
  // ═══ A. ✨ Shift+클릭 = 방금 칠한 열매에서 잘못 붙은 부분 떼어 내기 (마우스로) ═══
  await openPeach();
  res.stemA = await ev("S.stem");
  const E = await findEmpty(170, 90); ok("A 빈 칸 찾음", E, JSON.stringify(E));
  const [ex, ey] = E;
  const A = [ex + 45, ey + 45, 30], B = [ex + 110, ey + 45, 26];        // 붙은 두 알(A 는 진짜, B 는 잘못 붙은 옆 알)
  const union = await cand([A, B]), onlyB = await cand([B]);
  fake.sam.cands = [union, onlyB];                                     // 클릭 = 첫 후보(두 알 통째), Shift+클릭 = 가장 작은 후보(B)
  await key("s");
  ok("A S 키 = ✨ 도구", (await ev("S.tool")) === "sam");
  const u0 = await ev("S.undo.length");
  let [px, py] = await scr(A[0], A[1]);
  await page.mouse.click(px, py); await sleep(150); await idle();
  const val = await ev("samLast && samLast.val");
  ok("A ✨ 클릭 = 두 알 통째로 한 번호", val && (await valAt(A[0], A[1])) === val && (await valAt(B[0], B[1])) === val && (await ev("S.undo.length")) === u0 + 1, `val=${val} ${await msg()}`);
  const nUnion = await countVal(val);

  // 번호가 다른 곳을 Shift+클릭 → 도우미를 부르지 않고 안내만
  const n0 = fake.sam.n;
  [px, py] = await scr(ex + 160, ey + 85);
  await page.keyboard.down("Shift"); await page.mouse.click(px, py); await page.keyboard.up("Shift"); await sleep(150); await idle();
  ok("A 다른 곳 Shift+클릭 = 안내만(도우미 안 부름·칠 그대로)", fake.sam.n === n0 && /거기는 \d+번이 아닙니다/.test(await msg()) && (await countVal(val)) === nUnion, await msg());

  // B 를 Shift+클릭 → B 만 떨어지고 A 는 남음 · 되돌리기 한 칸
  const u1 = await ev("S.undo.length");
  [px, py] = await scr(B[0], B[1]);
  await page.keyboard.down("Shift"); await page.mouse.click(px, py); await page.keyboard.up("Shift"); await sleep(150); await idle();
  const nA = await countVal(val);
  ok("A Shift+클릭 = 가장 작은 후보(B)만 떼어 냄", fake.sam.n === n0 + 1 && (await valAt(B[0], B[1])) === 0 && (await valAt(A[0], A[1])) === val && nA > 0 && nA < nUnion
    && /떼어 냈습니다/.test(await msg()) && (await ev("S.undo.length")) === u1 + 1, `${nUnion}→${nA} ${await msg()}`);
  ok("A 떼어 낸 뒤 같은 자리 다시 누르기 = 후보 바꾸기 아님", (await ev("samLast.x")) === -99);
  await shot("A_neg");
  await key("Control+z");
  ok("A Ctrl+Z = 떼어 낸 B 돌아옴", (await valAt(B[0], B[1])) === val && (await countVal(val)) === nUnion);
  await key("Control+y");
  ok("A Ctrl+Y = 다시 떼어 냄", (await valAt(B[0], B[1])) === 0 && (await countVal(val)) === nA);

  // 떼어 낼 모양이 열매 전체를 덮으면 → 하지 않음(열매가 통째로 사라지지 않게)
  await key("Control+z");
  fake.sam.cands = [union];
  const u2 = await ev("S.undo.length");
  [px, py] = await scr(A[0], A[1]);
  await page.keyboard.down("Shift"); await page.mouse.click(px, py); await page.keyboard.up("Shift"); await sleep(150); await idle();
  ok("A 통째로 사라질 Shift+클릭 = 거절·칠 그대로", /통째로 사라져서/.test(await msg()) && (await countVal(val)) === nUnion && (await ev("S.undo.length")) === u2, await msg());

  // 도우미가 후보를 못 찾으면 → 지우개 안내
  fake.sam.cands = [];
  await page.keyboard.down("Shift"); await page.mouse.click(px, py); await page.keyboard.up("Shift"); await sleep(150); await idle();
  ok("A 후보 없음 = 지우개 안내·칠 그대로", /떼어 낼 부분을 못 찾았습니다/.test(await msg()) && (await countVal(val)) === nUnion, await msg());

  // ✨ 로 칠한 적이 없으면 → 먼저 칠하라는 안내(도우미 안 부름)
  await ev("samLast=null");
  const n3 = fake.sam.n;
  await page.keyboard.down("Shift"); await page.mouse.click(px, py); await page.keyboard.up("Shift"); await sleep(150); await idle();
  ok("A ✨ 전 Shift+클릭 = 먼저 칠하라는 안내", fake.sam.n === n3 && /먼저 ✨/.test(await msg()), await msg());

  // ═══ B. 키보드만으로 한 장 끝내기 — 여기서부터 마우스를 쓰지 않는다 ═══
  await openPeach();                                    // 새로 열어 A 의 칠은 버린다(저장 안 함)
  await ev("document.activeElement.blur()");            // 과일 고르기 칸에 남은 초점을 치운다(칸 안의 D 는 단축키가 아님)
  await key("d"); await idle();
  const stemB = await ev("S.stem");
  ok("B D = 다음 사진", stemB && stemB !== res.stemA, `${res.stemA} → ${stemB}`);
  res.stemB = stemB;
  // Tab 만으로 팔레트의 열매 색 칸까지
  let tabs = 0, onSw = false;
  for (; tabs < 150 && !onSw; tabs++) { await page.keyboard.press("Tab"); onSw = await ev("!!document.activeElement.matches('.sw[data-id]') && +document.activeElement.dataset.id>0 && !!CN[+document.activeElement.dataset.id]"); }
  ok("B Tab 으로 열매 색 칸까지 감", onSw, `Tab ${tabs}번`);
  res.tabsToSwatch = tabs;
  const swId = await ev("+document.activeElement.dataset.id");
  await key("Enter");
  ok("B Enter = 그 색 고름", (await ev("S.cur")) === swId, `cur=${await ev("S.cur")} sw=${swId}`);

  // G = 비슷한 열매 찾기(가짜 답: 빈 곳 두 알)
  const F = await findEmpty(140, 70); ok("B 빈 칸 찾음", F, JSON.stringify(F));
  const [fx, fy] = F;
  fake.sim.cands = [await cand([[fx + 30, fy + 35, 22]]), await cand([[fx + 100, fy + 35, 22]])];
  const maxBefore = await ev("Math.max(maxId(),S.lastNew)");
  const uB = await ev("S.undo.length");
  await key("g"); await sleep(150); await idle();
  ok("B G = 후보 2개 보임", fake.sim.n === 1 && (await ev("S.sim && S.sim.cands.length")) === 2 && /후보 2개/.test(await msg()), await msg());
  await shot("B_sim");
  // 안내대로 Enter = 모두 받기. 초점은 방금 고른 색 칸에 그대로 있다
  res.focusBeforeEnter = await ev("document.activeElement.id || document.activeElement.className");
  await key("Enter"); await sleep(100);
  const acc1 = await ev("!S.sim && S.undo.length");
  ok("B 색 칸에 초점이 있어도 Enter = 모두 받기", acc1 === uB + 1, `초점=${res.focusBeforeEnter} sim남음=${await ev("!!S.sim")} tool=${await ev("S.tool")} ${await msg()}`);
  if (acc1 !== uB + 1) {
    // 그 길이 막히면 키보드 사용자가 할 수 있는 다른 길: G 다시 → Shift+Tab 으로 «모두 받기» 단추(색 칸보다 앞) → Enter
    // (헤드리스 파이어폭스는 문서 끝에서 Tab 이 처음으로 돌아오지 않아 뒤로 간다)
    res.notes.push("색 칸 초점에서 Enter 가 모두 받기 대신 색 칸을 누름 → 단추로 우회");
    if (await ev("!!S.sim")) { await key("Escape"); }
    await key("g"); await sleep(150); await idle();
    let t2 = 0, onBtn = false;
    for (; t2 < 150 && !onBtn; t2++) { await page.keyboard.press("Shift+Tab"); onBtn = await ev("document.activeElement.matches('[data-act=sim-accept]')"); }
    ok("B (우회) Shift+Tab 으로 «모두 받기» 단추까지 감", onBtn, `Shift+Tab ${t2}번`);
    await key("Enter"); await sleep(100);
  }
  const ids2 = [maxBefore + 1, maxBefore + 2];
  ok("B 받은 두 알 = 새 번호 둘", (await ev("!S.sim")) && (await valAt(fx + 30, fy + 35)) === ids2[0] && (await valAt(fx + 100, fy + 35)) === ids2[1], `${await valAt(fx + 30, fy + 35)},${await valAt(fx + 100, fy + 35)} 기대 ${ids2}`);
  await key("Control+z");
  ok("B Ctrl+Z = 두 알 한 번에 사라짐", (await valAt(fx + 30, fy + 35)) === 0 && (await valAt(fx + 100, fy + 35)) === 0);
  await key("Control+y");
  ok("B Ctrl+Y = 두 알 다시", (await valAt(fx + 30, fy + 35)) === ids2[0] && (await valAt(fx + 100, fy + 35)) === ids2[1]);
  const nIds = await ev("idsNow().ids.length");
  await shot("B_accepted");

  // Ctrl+Enter = 저장하고 다음 사진
  await key("Control+Enter"); await sleep(300); await idle();
  const stemC = await ev("S.stem");
  ok("B Ctrl+Enter = 저장하고 다음 사진", stemC && stemC !== stemB && /저장했습니다|열었습니다/.test(await msg()), `${stemB} → ${stemC}`);
  const disk = await ev(`(async()=>{const it=await (await fetch('/api/item?fruit=peach&stem='+encodeURIComponent(${JSON.stringify(stemB)}))).json();
    const bd=await loadBundle('peach',${JSON.stringify(stemB)},false);const s=new Set(bd.L);s.delete(0);
    return {conf:(it.confirmed||{}).status||it.confirmed,has:${JSON.stringify(ids2)}.every(v=>s.has(v)),n:[...s].filter(v=>v!==HOLE).length}})()`);
  ok("B 저장이 디스크에 — 사람 확정 · 새 두 번호 있음 · 번호 수 같음", disk.conf === "fixed" && disk.has && disk.n === nIds, JSON.stringify(disk) + ` 화면 ${nIds}`);

  // 다음 장은 «빼기»로 끝내기 — 메뉴도 키보드로(Tab 으로 «파일» → ↓ 로 열고 항목 이동 → Enter)
  // «파일» 은 문서 맨 앞이라 Shift+Tab 으로 뒤로 간다(파이어폭스는 blur 뒤 Tab 이 처음이 아니라 제자리 다음부터라서)
  let t3 = 0, onFile = false;
  for (; t3 < 80 && !onFile; t3++) { await page.keyboard.press("Shift+Tab"); onFile = await ev("document.activeElement.matches('.mbtn') && document.activeElement.textContent.trim()==='파일'"); }
  ok("B Shift+Tab 으로 «파일» 메뉴 단추", onFile, `Shift+Tab ${t3}번`);
  await key("ArrowDown");
  let t4 = 0, onEx = await ev("document.activeElement.matches('[data-act=exclude]')");
  for (; t4 < 20 && !onEx; t4++) { await key("ArrowDown"); onEx = await ev("document.activeElement.matches('[data-act=exclude]')"); }
  ok("B ↓ 로 «이 사진 빼기» 까지", onEx, `↓ ${t4 + 1}번`);
  await key("Enter"); await sleep(300); await idle();
  const ex3 = await ev(`(async()=>{const it=await (await fetch('/api/item?fruit=peach&stem='+encodeURIComponent(${JSON.stringify(stemC)}))).json();return {conf:(it.confirmed||{}).status||it.confirmed,focus:document.activeElement.textContent.trim().slice(0,4)}})()`);
  ok("B 키보드로 «빼기» = 사람 확정 exclude · 초점은 «파일» 단추로", ex3.conf === "exclude" && ex3.focus === "파일", JSON.stringify(ex3));
  ok("B 마우스를 쓰지 않았음(viaMouse=false)", (await ev("viaMouse")) === false);
  await shot("B_done");
} catch (e) {
  res.errors.push("시험 중단: " + (e.stack || e.message));
  console.log("시험 중단:", e.message);
  await shot("crash").catch(() => {});
}
ok("페이지 오류 없음", !res.errors.length, res.errors.join(" | "));
await b.close();
fs.writeFileSync(path.join(OUT, `e01_${BR}_result.json`), JSON.stringify(res, null, 1));
const bad = res.checks.filter((c) => !c.ok).length;
console.log(`== E01 ${BR}: ${res.checks.length - bad}/${res.checks.length} 통과 ==`);
process.exit(bad ? 1 : 0);
