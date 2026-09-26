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
  ok("복숭아 = 규칙 줄 숨김(C05)", await ev("$('#rule').hidden"));
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

  // ── 키보드로 팔레트 색 고르기(C08): 색 칸·지금 색·작업자가 Tab 대상 · Enter·스페이스 = 누르기 · 마우스 뒤 스페이스는 옮기기 그대로
  ok("C08 팔레트·작업자 모두 Tab 대상", await ev("[...document.querySelectorAll('.sw,#curbox,#who')].every(e=>e.tabIndex===0 && e.getAttribute('role')==='button') && document.querySelectorAll('.sw[data-id]').length>=3"));
  const cur0 = await ev("S.cur");
  await page.focus('#zoombar [data-act="fit"]'); await key("Tab");
  ok("C08 확대 단추 다음 Tab = 지금 색", (await ev("document.activeElement.id")) === "curbox");
  const tabTo = async (test) => { for (let i = 0; i < 60; i++) { await key("Tab"); if (await ev(`(()=>{const e=document.activeElement;return ${test}})()`)) return true; } return false; };
  await tabTo(`e.matches('.sw[data-id]') && +e.dataset.id>0 && +e.dataset.id!==${cur0}`);
  const kid = await ev("+document.activeElement.dataset.id"); await key("Enter");
  ok("C08 Enter = 그 색", (await ev("S.cur")) === kid && (await ev("document.activeElement.getAttribute('aria-pressed')")) === "true", `${cur0}→${kid}`);
  await tabTo(`e.matches('.sw[data-id]') && +e.dataset.id>0 && +e.dataset.id!==${kid}`);
  const kid2 = await ev("+document.activeElement.dataset.id"); await key(" ");
  ok("C08 스페이스 = 그 색 · 옮기기 안 켜짐", (await ev("S.cur")) === kid2 && !(await ev("spaceDown")), `${kid}→${kid2}`);
  await page.focus('#zoombar [data-act="fit"]'); await key("Tab"); await key("Enter");
  ok("C08 지금 색 Enter = 그 칸으로 초점", await ev(`document.activeElement.matches('.sw.on') && +document.activeElement.dataset.id===${kid2}`));
  const hasHole = await ev("!!document.querySelector('.sw.hole')");
  if (hasHole) { await page.focus('#zoombar [data-act="fit"]'); await key("Tab"); await tabTo("e.matches('.sw.hole')"); await key("Enter"); ok("C08 회색 ? Enter = 설명", /번호가 없는 곳/.test(await ev("$('#msg').textContent"))); }
  await tabTo("e.id==='who'"); dialogs.push(true); await key("Enter"); await sleep(200);
  ok("C08 작업자 Enter = 이름 묻기", /시험봇/.test(await ev("$('#who').textContent")) && res.checks.some((c) => /작업자 이름/.test(c.name)));
  // 마우스로 색 칸을 누른 뒤(초점이 칸에 남음) 스페이스 = 끌어서 옮기기(예전 그대로), 색은 안 바뀜
  await page.click(`.sw[data-id="${cur0 && cur0 !== kid2 ? cur0 : 0}"]`);
  const curM = await ev("S.cur"); await page.keyboard.down(" "); await sleep(80);
  ok("C08 마우스 뒤 스페이스 = 옮기기", (await ev("spaceDown")) && (await ev("S.cur")) === curM,
    await ev("(()=>{const e=document.activeElement;return [e.className,e.id,e.matches(':focus-visible'),spaceDown,S.cur].join('|')})()") + `|${curM}`);
  await page.keyboard.up(" "); await key("b"); await ev(`setCur(${cur0})`);

  // ── 보조기기 알림·상태(C09): 알림 줄 live · 도구·원본보기 aria-pressed · 메뉴 aria-expanded · 칸 이름 · 탭 제목
  ok("C09 알림 줄·불러오는 중 live", await ev("$('#msg').getAttribute('role')==='status' && $('#loading').getAttribute('aria-live')==='polite' && ['fruit','photo','q'].every(i=>$('#'+i).getAttribute('aria-label'))"));
  ok("C09 탭 제목 = 사진 이름", (await ev("document.title")) === `${await ev("S.stem")} - 라벨 그림판`, await ev("document.title"));
  await key("e");
  ok("C09 도구 aria-pressed", await ev("[...document.querySelectorAll('#tools [data-tool]')].every(b=>b.getAttribute('aria-pressed')===String(b.dataset.tool==='eraser'))"));
  await key("b"); await key("v");
  const origOn = await ev("$('#orig').getAttribute('aria-pressed')"); await key("v");
  ok("C09 원본 보기 aria-pressed", origOn === "true" && (await ev("$('#orig').getAttribute('aria-pressed')")) === "false", origOn);
  await page.click("#menubar .menu:nth-child(3) .mbtn"); await sleep(80);
  const expOpen = await ev("document.querySelector('#menubar .menu:nth-child(3) .mbtn').getAttribute('aria-expanded')"); await key("Escape");
  ok("C09 메뉴 aria-expanded 열림·Esc 닫힘", expOpen === "true" && (await ev("[...document.querySelectorAll('.mbtn')].every(b=>b.getAttribute('aria-haspopup')==='true' && b.getAttribute('aria-expanded')==='false')")), expOpen);
  await ev("say('시험 실패 알림','err')");
  const liveErr = await ev("$('#msg').getAttribute('aria-live')"); await ev("say('시험 알림')");
  ok("C09 실패 알림은 assertive", liveErr === "assertive" && (await ev("$('#msg').getAttribute('aria-live')")) === "polite", liveErr);

  // ── 글자 대비 AA(C11): 실패·완료 알림, 제목줄 «저장 안 됨» 칩이 4.5 이상 · 도구 이름 12px
  const CR = `((f,b)=>{const L=c=>{const v=c.match(/\\d+/g).slice(0,3).map(x=>{x/=255;return x<=0.03928?x/12.92:((x+0.055)/1.055)**2.4});return .2126*v[0]+.7152*v[1]+.0722*v[2]};const [x,y]=[L(f),L(b)].sort((a,b)=>a-b);return (y+.05)/(x+.05)})`;
  const crOf = (sel, bg) => ev(`${CR}(getComputedStyle($('${sel}')).color, ${bg ? `'${bg}'` : `getComputedStyle($('${sel}')).backgroundColor`})`);
  await ev("say('시험 실패','err')"); const crErr = await crOf("#msg", "rgb(192,192,192)");
  await ev("say('시험 완료','ok')"); const crOk = await crOf("#msg", "rgb(192,192,192)"); await ev("say('시험 알림')");
  const dirty0 = await ev("S.dirty"); await ev("setDirty(true)"); const crDirty = await crOf("#t-dirty"); await ev(`setDirty(${dirty0})`);
  ok("C11 대비 실패·완료·저장안됨 ≥ 4.5", crErr >= 4.5 && crOk >= 4.5 && crDirty >= 4.5, `${crErr.toFixed(2)}/${crOk.toFixed(2)}/${crDirty.toFixed(2)}`);
  ok("C11 도구 이름 12px", await ev("[...document.querySelectorAll('#tools button:not(.wide) span')].every(s=>parseFloat(getComputedStyle(s).fontSize)>=12 && s.scrollWidth<=s.parentElement.clientWidth)"));

  // ── 메뉴 키보드(C10): 닫힌 단추에서 ↓ = 열고 첫 항목 · ↑↓ 돌기 · Esc/고른 뒤 초점 = 메뉴 단추
  const focAct = () => ev("(document.activeElement.dataset.act||document.activeElement.tagName)");
  await page.focus("#menubar .menu:nth-child(1) .mbtn"); await key("ArrowDown");
  const a1 = await focAct(); await key("ArrowUp"); const a2 = await focAct(); await key("ArrowDown"); const a3 = await focAct();
  ok("C10 ↓ 열고 첫 항목 · ↑ 끝으로 · ↓ 처음으로", a1 === "save" && a2 === "A" && a3 === "save" && (await ev("$('#menubar .menu:nth-child(1)').classList.contains('open')")), `${a1}/${a2}/${a3}`);
  await key("ArrowDown"); await key("Escape");
  ok("C10 Esc = 닫고 초점은 파일 단추", (await ev("!document.querySelector('.menu.open') && document.activeElement===document.querySelector('#menubar .menu:nth-child(1) .mbtn')")));
  const col0 = await ev("S.showColor");
  await page.focus("#menubar .menu:nth-child(3) .mbtn"); await key("Enter"); await sleep(50); await key("ArrowDown"); await key("Enter"); await sleep(80);
  ok("C10 Enter 로 고른 뒤 초점은 보기 단추", (await ev("S.showColor")) === !col0 && (await ev("!document.querySelector('.menu.open') && document.activeElement===document.querySelector('#menubar .menu:nth-child(3) .mbtn')")), String(await focAct()));
  await page.click("#menubar .menu:nth-child(3) .mbtn"); await sleep(50); await page.click('#menubar [data-act="toggle-color"]'); await sleep(80);
  ok("C10 마우스로 골라도 초점은 보기 단추", (await ev("S.showColor")) === col0 && (await ev("document.activeElement===document.querySelector('#menubar .menu:nth-child(3) .mbtn')")));
  await ev("document.activeElement.blur()");

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
  // 512 크롭 네모(C04): C 로 켜면 사진 가운데 512×512 자리에 빨간 선, 다시 C 로 끔
  { await key("c");
    const red = await ev("(()=>{const cw=Math.min(512,S.W),ch=Math.min(512,S.H),x=Math.round(S.ox+Math.floor((S.W-cw)/2)*S.z),y=Math.round(S.oy+Math.floor((S.H-ch)/2)*S.z+ch*S.z/2);const d=hudX.getImageData(x-2,y,5,1).data;for(let i=0;i<d.length;i+=4)if(d[i]>200&&d[i+1]<80&&d[i+3]>200)return true;return false})()");
    ok("C = 512 크롭 네모 보임", (await ev("S.showCrop")) === true && red);
    await key("c"); ok("C 다시 = 숨김", (await ev("S.showCrop")) === false); }
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
  // C18 작업 기록: 저장하면 이 사진의 작업 시간·수정 횟수를 서버로 보내고(디스크는 paint_e2e_check.py 가 대조) 0 부터 다시 센다
  {
    const w18 = await ev("(()=>{const w=S.lastWork||{};return {...w,now:{...S.wl},ids:idsNow().ids.length}})()");
    ok("C18 저장 = 작업 기록(시간·수정·되돌리기·번호 수) 보내고 새로 셈", w18.action === "save" && w18.stem === (await ev("S.stem")) && w18.edits >= 1 && w18.undos >= 1
      && w18.active_s > 0 && w18.active_s <= w18.wall_s + 0.01 && w18.n_save === w18.ids && w18.now.edits === 0 && w18.now.undos === 0 && w18.now.n0 === w18.ids, JSON.stringify(w18));
    const u18 = await ev("(()=>{const a=S.wl.undos;S.undo.push({x0:0,y0:0,w:1,h:1,data:new Uint16Array([S.L[0]])});undo(true);const b=S.wl.undos;S.undo.push({x0:0,y0:0,w:1,h:1,data:new Uint16Array([S.L[0]])});undo();const c=S.wl.undos;S.redo=[];S.wl.undos=a;setDirty(false);return [a,b,c]})()");
    ok("C18 ✨ 후보 바꾸기(undo(true))는 되돌리기로 안 셈", u18[1] === u18[0] && u18[2] === u18[0] + 1, JSON.stringify(u18));
  }
  // C25 누른 채 끄는 동안도 작업 시간: 90초 붓질(10초마다 움직임)+떼기 = 100초 다 셈 · 안 누른 움직임은 안 셈 · 100ms 안의 움직임은 묶음(시계는 가짜로 돌린다)
  {
    const c25 = await ev(`(()=>{const real=Date.now,w=S.wl,a0=w.active;let t=real();Date.now=()=>t;try{
      const pm=(b)=>document.dispatchEvent(new PointerEvent("pointermove",{buttons:b}));
      wlTick();const a1=w.active;for(let i=0;i<9;i++){t+=10e3;pm(1);}t+=10e3;document.dispatchEvent(new PointerEvent("pointerup"));const a2=w.active;
      t+=50e3;pm(0);const a3=w.active;pm(1);const l=w.last;t+=50;pm(1);const thr=w.last===l;
      return {drag:a2-a1,hover:a3-a2,thr};}finally{Date.now=real;w.active=a0;w.last=real();}})()`);
    ok("C25 긴 드래그도 작업 시간으로 셈(안 누른 움직임 제외·100ms 묶음)", c25.drag === 100e3 && c25.hover === 0 && c25.thr, JSON.stringify(c25));
  }
  // C16 저장 뒤 의심 열매: 저장 때 계산한 목록 = 지금 다시 계산한 목록 · 알림에 개수 · 한 장 계산 시간
  {
    const s16 = await ev("(()=>{const t0=performance.now(),a=suspects(),t=performance.now()-t0;return {same:JSON.stringify(a)===JSON.stringify(S.sus),n:S.sus.length,t,msg:$('#msg').textContent}})()");
    ok("C16 저장 뒤 의심 열매 목록·알림", s16.same && (s16.n ? s16.msg.includes(`한 번 볼 열매 ${s16.n}개`) : !/한 번 볼 열매/.test(s16.msg)), JSON.stringify(s16));
    ok("C16 의심 열매 계산 400ms 이하", s16.t <= 400, s16.t.toFixed(1) + "ms");
    // 만든 장면(100×100): 보통 원 6개 + 큰 원(넓이) + 가는 선(둥근 정도) + 떨어진 두 조각 + 점(작음) + 둘러싸인 고리 안 열매
    const syn = await ev(`(()=>{const k=[S.L,S.W,S.H];const W=120,H=120,L=new Uint16Array(W*H);
      const disc=(cx,cy,r,v)=>{for(let y=0;y<H;y++)for(let x=0;x<W;x++)if((x-cx)**2+(y-cy)**2<=r*r)L[y*W+x]=v};
      [[10,10],[30,10],[50,10],[70,10],[90,10],[10,30]].forEach(([x,y],i)=>disc(x,y,6,i+1));
      disc(60,60,22,7); for(let x=5;x<85;x++)L[100*W+x]=8; disc(100,40,5,9); disc(110,55,5,9); L[115*W+115]=10; L[115*W+116]=10;
      disc(30,50,9,11); disc(30,50,4,12);
      S.L=L;S.W=W;S.H=H;computeCenters();const r=suspects();S.L=k[0];S.W=k[1];S.H=k[2];computeCenters();
      const g=(v)=>((r.find(s=>s.v===v)||{}).why||[]).join('|');return {ids:r.map(s=>s.v),w7:g(7),w8:g(8),w9:g(9),w10:g(10),w12:g(12)}})()`);
    ok("C16 넓이·둥근 정도·조각·둘러싸임을 잡고 보통 열매는 안 잡음", /넓이.*배/.test(syn.w7) && /둥근 정도/.test(syn.w8) && /조각 2개/.test(syn.w9) && /넓이/.test(syn.w10) && /둘러싸임/.test(syn.w12)
      && syn.ids.every((v) => v > 6), JSON.stringify(syn));
    // 빨간 점선: 의심 번호 하나를 넣고 그리면 화면에 빨간 점이 생기고, 그 번호가 없으면 안 그린다
    const red = await ev(`(()=>{const keep=S.sus,v=centers.length?centers[0][0]:0;const cnt=()=>{drawHud();const d=hudX.getImageData(0,0,hud.width,hud.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]>240&&d[i+1]<60&&d[i+2]<60&&d[i+3]>200)n++;return n};
      S.sus=[];const a=cnt();S.sus=[{v,why:['시험']}];const b=cnt();S.sus=[{v:65000,why:['없음']}];const c=cnt();S.sus=keep;drawHud();return [a,b,c]})()`);
    ok("C16 빨간 점선 동그라미 그림·없는 번호는 건너뜀", red[1] > red[0] + 20 && red[2] === red[0], JSON.stringify(red));
  }
  // C17 ✨ 결과 모양 경고: 둥근 모양은 조용, 가는 막대(가지)·납작한 띠(잎)·사진의 10% 넘는 덩어리는 경고
  {
    const w17 = await ev(`(()=>{const mk=(w,h,f)=>{const a=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(f(x,y))a[(y*w+x)*4]=255;return a};
      const t=(w,h,f)=>samShapeWarn(mk(w,h,f),{w,h},65000);
      const big=Math.ceil(Math.sqrt(S.L.length*0.12));
      return {disc:t(41,41,(x,y)=>(x-20)**2+(y-20)**2<=400),ell:t(61,31,(x,y)=>((x-30)/30)**2+((y-15)/15)**2<=1),
        stick:t(200,6,()=>true),diag:t(120,120,(x,y)=>Math.abs(x-y)<=3),big:t(big,big,()=>true)}})()`);
    ok("C17 모양 경고: 원·2:1 타원 조용, 막대·대각선·큰 덩어리 경고", !w17.disc && !w17.ell && /길쭉함/.test(w17.stick) && /길쭉함/.test(w17.diag) && /사진의 1\d%/.test(w17.big), JSON.stringify(w17));
    // ✨ 클릭을 가짜 답(가는 막대 후보)으로 흉내: 칠은 하고, 알림 줄은 빨간 글씨 경고. Ctrl+Z 로 되돌리고 원래 상태로
    const c17 = await ev(`(async()=>{const keep={post:postJSON,cur:S.cur,ln:S.lastNew,last:samLast,msg:$('#msg').textContent};
      let ix=-1,iy=-1;for(let y=5;y<S.H-10&&ix<0;y+=7)for(let x=5;x<S.W-130;x+=7){let e=true;for(let k=0;k<120&&e;k+=3)if(S.L[y*S.W+x+k]||S.L[(y+4)*S.W+x+k])e=false;if(e){ix=x;iy=y;break}}
      if(ix<0)return {skip:1};
      const png=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');g.fillStyle='#000';g.fillRect(0,0,w,h);g.fillStyle='#fff';g.fillRect(0,0,w,h);return c.toDataURL('image/png').split(',')[1]};
      postJSON=async()=>({sec:0.1,cands:[{x0:ix,y0:iy,w:120,h:5,png:png(120,5)}]});samLast=null;const u0=S.undo.length;
      try{await samClick(ix+2,iy+2)}finally{postJSON=keep.post}
      const r={msg:$('#msg').textContent,cls:$('#msg').className,painted:S.L[(iy+2)*S.W+ix+60]>0,undo:S.undo.length-u0};
      if(r.undo)undo();r.back=S.L[(iy+2)*S.W+ix+60]===0;samLast=keep.last;S.lastNew=keep.ln;setCur(keep.cur);renderPalette();say(keep.msg);return r})()`);
    ok("C17 ✨ 길쭉한 결과 = 칠하고 빨간 경고·Ctrl+Z 로 되돌림", c17.skip || (c17.painted && c17.undo === 1 && c17.back && /⚠ 잎·가지/.test(c17.msg) && c17.cls === "err"), JSON.stringify(c17));
  }

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
  ok("C18 빼기 = 작업 기록 exclude", (await ev("(S.lastWork||{}).action")) === "exclude" && (await ev("S.lastWork.stem")) === stem1);
  await key("a"); await idle();
  ok("빼기 표시 ✕", (await ev("document.querySelector('#photo').selectedOptions[0].textContent")).startsWith("✕"));
  await ev("ACTS.unexclude()"); await sleep(300); await idle();
  ok("빼기 취소", !(await ev("document.querySelector('#photo').selectedOptions[0].textContent")).startsWith("✕"));

  // ── 다음·이전 사진 미리 받기(C06): 미리 받은 것을 쓰고, 그 라벨이 새로 받은 것과 같다 · 남이 그새 바꾸면 새로 받는다 · 빨리 연달아 넘기면 마지막 것
  const pfReady = (d) => page.waitForFunction((d) => window.eval(`(()=>{const o=$('#photo').options[$('#photo').selectedIndex+${d}];const e=o&&PF.get(S.fruit+'|'+o.value);if(!e)return false;e.p.then(()=>e.ok=1);return e.ok===1})()`), d, { timeout: 30000, polling: 100 });
  await pfReady(1);
  const tf = Date.now(); await key("d"); await idle();
  const flipMs = Date.now() - tf;
  const same = await ev("loadBundle(S.fruit,S.stem,false).then(b=>b.L.length===S.L.length&&b.L.every((v,i)=>v===S.L[i]))");
  ok("C06 미리 받은 사진으로 넘김 · 라벨 같음", (await ev("S.lastPrefetchHit")) && same, `${flipMs}ms`);
  await key("a"); await idle(); await pfReady(1);
  const nx = await ev("$('#photo').options[$('#photo').selectedIndex+1].value");
  await ev(`postJSON('/api/status',{fruit:S.fruit,stem:${JSON.stringify(nx)},by:'시험봇',status:'flag',note:'C06 시험 — 남이 그새 바꿈'})`);
  await key("d"); await idle();
  await page.waitForFunction((s) => window.eval(`S.stem===${JSON.stringify(s)} && !S.busy && !S.lastPrefetchHit && S.item.status==='flag'`), nx, { timeout: 15000, polling: 50 }).catch(() => {});
  ok("C06 남이 바꾼 사진은 새로 받음", (await ev("S.stem")) === nx && !(await ev("S.lastPrefetchHit")) && (await ev("S.item.status")) === "flag");
  // C19: 상태·at 은 같고 파일만 바뀐 경우(같은 초 저장) — 미리 받은 file_sig 가 다르면 새로 받는다
  await key("a"); await idle(); await pfReady(1);
  const fsOk = await ev("(async()=>{const k=S.fruit+'|'+$('#photo').options[$('#photo').selectedIndex+1].value;const b=await PF.get(k).p;const had=typeof b.item.file_sig==='string'&&b.item.file_sig.length>0;b.item.file_sig='낡은지문';return had})()");
  await key("d"); await idle();
  await page.waitForFunction((s) => window.eval(`S.stem===${JSON.stringify(s)} && !S.busy`), nx, { timeout: 15000, polling: 50 }).catch(() => {});
  ok("C19 파일 지문만 달라도 새로 받음", fsOk && (await ev("S.stem")) === nx && !(await ev("S.lastPrefetchHit")) && (await ev("S.item.file_sig")) !== "낡은지문");
  const i0 = await ev("$('#photo').selectedIndex"), n0 = await ev("$('#photo').options.length");
  if (i0 + 3 < n0) {
    await page.keyboard.press("d"); await page.keyboard.press("d"); await page.keyboard.press("d");
    await sleep(300); await idle(); await sleep(200); await idle();
    const want = await ev(`$('#photo').options[${i0 + 3}].value`);
    ok("C06 빨리 D 세 번 = 세 장 뒤", (await ev("S.stem")) === want && (await ev("$('#photo').value")) === want, await ev("S.stem"));
  }

  // ── 목록: 찾기·안 한 것만·과일 바꾸기
  await page.fill("#q", stem1.slice(-4)); await page.press("#q", "Enter"); await sleep(300);
  ok("이름 찾기", (await ev("document.querySelector('#photo').options.length")) >= 1);
  await page.fill("#q", ""); await page.press("#q", "Enter"); await sleep(300); await idle();
  await page.check("#only-todo"); await sleep(300); await idle();
  ok("안 한 것만", await ev("[...document.querySelector('#photo').options].every(o=>o.textContent.startsWith('　'))"));
  await page.uncheck("#only-todo"); await sleep(300); await idle();
  // 카운팅 표본 100장(C01): 과일 사진이 100장 이상이면 정확히 100장, 다시 계산해도 같은 목록, 진행률에 «표본 n/100»
  await page.check("#only-sample"); await sleep(300); await idle();
  const nAll = await ev("S.items.length"), nS = await ev("document.querySelector('#photo').options.length");
  ok("표본 100장만", nS === Math.min(100, nAll) && await ev("[...document.querySelector('#photo').options].every(o=>S.sample.has(o.value))"), `${nS}/${nAll}`);
  ok("표본 = 결정적", await ev("(()=>{const a=sampleOf(S.fruit,[...S.items].reverse());return a.size===S.sample.size&&[...a].every(s=>S.sample.has(s))})()"));
  ok("표본 진행률", /표본 \d+\/\d+ 확정/.test(await ev("document.querySelector('#prog').textContent")), await ev("document.querySelector('#prog').textContent"));
  await page.uncheck("#only-sample"); await sleep(300); await idle();
  // C15 헷갈리는 순: 미확정이 앞(점수 큰 순) · 확정은 뒤 · 지금 사진 그대로 · 이름 순으로 돌아옴
  const stemS = await ev("S.stem");
  await page.selectOption("#sort", "unc"); await sleep(300); await idle();
  const u15 = await ev(`(()=>{const o=[...$('#photo').options].map(o=>o.value),it=o.map(s=>S.items.find(x=>x.stem===s)),
    todo=it.map(x=>itemMark(x)==='　'),sc=it.map(x=>todo[it.indexOf(x)]?uncScore(x):-2);
    return {n:o.length,all:S.items.length,unc:Object.keys(S.unc).length,cur:S.stem,sel:$('#photo').value,
      todoFirst:todo.indexOf(false)<0||todo.slice(todo.indexOf(false)).every(t=>!t),
      desc:sc.every((v,i)=>i===0||v<=sc[i-1]),top:sc[0],tag:/헷갈림 \\d\\.\\d\\d$/.test($('#photo').options[0].textContent)}})()`);
  ok("C15 헷갈리는 순 = 미확정 앞·점수 큰 순·지금 사진 그대로", u15.n === u15.all && u15.unc > 0 && u15.todoFirst && u15.desc && u15.cur === stemS && u15.sel === stemS && (u15.top < 0 || u15.tag), JSON.stringify(u15));
  ok("C15 점수 = (개수 차이 비율 + unc) 평균", await ev("(()=>{const k=Object.keys(S.unc)[0],u=S.unc[k];const a=uncScore({stem:k,n_inst:u.sure*2+2}),g=(u.sure+2)/(u.sure*2+2);return Math.abs(a-(g+u.unc)/2)<1e-9&&uncScore({stem:'없는이름',n_inst:3})===-1})()"));
  ok("C15 고른 순서 기억", await ev("localStorage.getItem('paint.sort')==='unc'"));
  await page.selectOption("#sort", "name"); await sleep(300); await idle();
  ok("C15 이름 순으로 돌아옴", await ev("(()=>{const o=[...$('#photo').options].map(o=>o.value);return o.every((s,i)=>i===0||o[i-1]<s)&&S.stem===" + JSON.stringify(stemS) + "})()"));
  // C21: 저장(✓)한 사진을 다시 칠한 채(dirty) «안 한 것만»·정렬·이름 찾기를 바꿔도 지금 사진이 목록에 남고 칠이 안 사라진다
  //      (디스크는 안 쓴다 — 목록 항목의 확정 표시만 잠깐 바꿨다가 되돌린다)
  await ev("(()=>{const it=S.items.find(x=>x.stem===S.stem);window._c21=it.confirmed;it.confirmed='ok';setDirty(true)})()");
  const c21 = async () => ev("({stem:S.stem,sel:$('#photo').value,dirty:S.dirty,inList:[...$('#photo').options].some(o=>o.value===S.stem)})");
  const c21ok = (r) => r.stem === stemS && r.sel === stemS && r.dirty && r.inList;
  await page.check("#only-todo"); await sleep(300); await idle(); const r21a = await c21();
  await page.selectOption("#sort", "unc"); await sleep(300); await idle(); const r21b = await c21();
  await page.selectOption("#sort", "name"); await page.fill("#q", "zzz_없는이름"); await page.press("#q", "Enter"); await sleep(300); await idle(); const r21c = await c21();
  ok("C21 안 저장한 지금 사진은 안 한 것만·정렬·이름 찾기에도 그대로", c21ok(r21a) && c21ok(r21b) && c21ok(r21c), JSON.stringify([r21a, r21b, r21c]));
  await ev("(()=>{S.items.find(x=>x.stem===S.stem).confirmed=window._c21;setDirty(false)})()");
  await page.fill("#q", ""); await page.uncheck("#only-todo"); await sleep(300); await idle();
  ok("C21 되돌림 뒤 지금 사진 그대로", (await ev("S.stem")) === stemS && !(await ev("S.dirty")));
  // C22: 저장을 기다리는 사이 Ctrl+Z·N 은 안 먹고, 그새 ✨ 답처럼 칠이 바뀌어도 세 파일은 저장 누른 순간의 칠 · 바뀐 칠은 «저장 안 됨» 으로 남는다
  //      (postJSON 을 가짜로 바꿔 디스크는 안 쓴다 — 답은 손으로 하나씩 풀어 준다)
  const c22 = await ev(`(async()=>{const keep={post:postJSON,ln:S.lastNew,wl:S.wl,it:{...S.items.find(x=>x.stem===S.stem)}};
    const calls=[],gate=[];postJSON=(u,b)=>{calls.push([u,b]);return new Promise(r=>gate.push(r)).then(()=>({}))};
    const n0=S.undo.length,bin0=encodeBinary(),inst0=encodeInstances(),box0=JSON.stringify(boxesNow()),L0=S.L.slice();
    const tick=()=>new Promise(r=>setTimeout(r,30));
    const p=save();await tick();
    const r={busy:S.busy};undo();redo();newNumber();r.same=S.L.every((v,i)=>v===L0[i])&&S.undo.length===n0&&S.lastNew===keep.ln;r.msg=$('#msg').textContent;
    let k=-1;for(let i=0;i<S.L.length;i++)if(!S.L[i]){k=i;break}
    const before=snapshot();S.L[k]=S.cur||1;pushUndo(before,k%S.W,(k/S.W)|0,k%S.W+1,((k/S.W)|0)+1);
    while(gate.length||!calls.find(c=>c[0]==='/api/boxes')){if(gate.length)gate.shift()();await tick()}
    r.ok=await p;const g=(u)=>(calls.find(c=>c[0]===u)||[])[1]||{};
    r.bin=g('/api/save').png===bin0;r.inst=g('/api/save_instances').png===inst0;r.box=JSON.stringify(g('/api/boxes').boxes)===box0;
    r.dirty=S.dirty;r.later=/아직 저장 안 됐습니다/.test($('#msg').textContent);
    postJSON=keep.post;undo();S.redo=[];S.lastNew=keep.ln;S.wl=keep.wl;Object.assign(S.items.find(x=>x.stem===S.stem),keep.it);markOption();setDirty(false);
    r.back=S.L.every((v,i)=>v===L0[i]);return r})()`);
  ok("C22 저장 중 Ctrl+Z·Ctrl+Y·N 막힘 + 세 파일 = 저장 누른 순간 + 그새 바뀐 칠은 «저장 안 됨»",
    c22.busy && c22.same && /끝난 뒤 다시/.test(c22.msg) && c22.ok && c22.bin && c22.inst && c22.box && c22.dirty && c22.later && c22.back, JSON.stringify(c22));
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
  await page.waitForFunction(() => window.eval("S.item && S.item.fruit==='grape'"), null, { timeout: 30000 }).catch(() => {}); await idle();
  ok("포도 = 규칙 줄 «미정» 보임(C05)", await ev("!$('#rule').hidden && /포도 규칙 미정/.test($('#rule').textContent) && $('#rule').getBoundingClientRect().height>0"));
  await shot("03_grape");

  // ── 재학습 준비 표시(C03): 사람 확정 수 = 목록 ✓ 수 · 모래상자에서 한 번 내보낸 뒤 창으로 돌아오면 «마지막 내보내기» · 링크 = 옛 툴 데이터 정리 탭(포도)
  { await page.waitForFunction(() => window.eval("S.exports !== null && /사람 확정/.test($('#exp-txt').textContent)"), null, { timeout: 10000 });
    const nOk = await ev("S.items.filter(it=>itemMark(it)==='✓ ').length"), t1 = await ev("$('#exp-txt').textContent");
    ok("사람 확정 수 표시", t1.includes(`사람 확정 ${nOk}장`) && /내보낸 적 없음|마지막 내보내기/.test(t1), t1);
    const st = await ev(`postJSON('/api/export_start',{fruit:'grape',kinds:['mask','boxes','counts'],confirmed_only:true,by:'시험봇'})`);
    let js = {}; for (let i = 0; i < 100 && js.state !== "done" && js.state !== "error"; i++) { await sleep(300); js = await ev(`getJSON('/api/export_status?job=${st.job}')`); }
    await ev("window.dispatchEvent(new Event('focus'))");
    await page.waitForFunction(() => window.eval("/마지막 내보내기/.test($('#exp-txt').textContent)"), null, { timeout: 10000 }).catch(() => {});
    const t2 = await ev("$('#exp-txt').textContent");
    ok("내보낸 뒤 마지막 내보내기 시각", js.state === "done" && t2.includes(String(js.finished).slice(5, 16)), `${js.state} ${js.n_images}장 | ${t2}`);
    const href = await ev("$('#exp-link').href");
    const p2 = await ctx.newPage(); p2.on("dialog", (d) => d.accept("시험봇").catch(() => {}));
    await p2.goto(href); await p2.waitForFunction(() => !document.querySelector("#view-exp").classList.contains("hidden"), null, { timeout: 15000 }).catch(() => {});
    const o = await p2.evaluate(() => ({ exp: !document.querySelector("#view-exp").classList.contains("hidden"), fruit: document.querySelector("#fruit").value }));
    ok("내보내기 링크 = 옛 툴 데이터 정리(포도)", /\/old#exp=grape$/.test(href) && o.exp && o.fruit === "grape", href + " " + JSON.stringify(o));
    await p2.close(); }

  // ── 닮은 사진 묶음(C02): 대표가 아닌 사진 → 이름표(노랑) · 대표 열기 · «대표만 남기기» = 나머지 ✕(사람 확정)
  // 포도 목록이 다 와서 첫 사진이 열린 뒤에 시작한다(S.L 은 복숭아 것이 남아 있어 위 기다림만으로는 이르다)
  await page.waitForFunction(() => window.eval("S.item && S.item.fruit==='grape' && S.stem===document.querySelector('#photo').value"), null, { timeout: 30000 }); await idle();
  { const pv = await ev("getJSON('/api/duplicate_preview?fruit=grape')");
    let pick = null;
    for (const sm of pv.sample || []) {
      const it = await ev(`getJSON('/api/item?fruit=grape&stem=${sm.stem}')`);
      if (it.dup_rep !== sm.stem && it.dup_members.some((m, i) => m !== it.dup_rep && !it.dup_member_confirmed[i])) { pick = it; break; }
    }
    ok("묶음 표본 찾음", !!pick, pick ? pick.stem : JSON.stringify(pv).slice(0, 120));
    if (pick) {
      await ev(`openPhoto('${pick.stem}')`); await idle();
      ok("대표 아님 이름표", await ev("!$('#dupmenu').hidden && $('#dupbtn').classList.contains('notrep') && /닮은 사진 \\d+장/.test($('#dupbtn').textContent)"),
        await ev("$('#dupbtn').textContent"));
      await page.click("#dupbtn"); await sleep(150);
      ok("묶음 목록 펼침", await ev("$('#dupmenu').classList.contains('open') && $('#dupdrop').querySelectorAll('[data-dupopen]').length") === pick.dup_members.length);
      await shot("03b_dup");
      await page.click(`#dupdrop [data-dupopen="${pick.dup_rep}"]`); await sleep(300); await idle();
      ok("대표 열기", (await ev("S.stem")) === pick.dup_rep && /대표/.test(await ev("$('#dupbtn').textContent")));
      const todo = await ev("dupTodo(S.item)");
      await page.click("#dupbtn"); await sleep(150);
      dialogs.push(true); await page.click('#dupdrop [data-act="dup-keep-rep"]'); await sleep(300); await idle();
      const it2 = await ev(`getJSON('/api/item?fruit=grape&stem=${pick.dup_rep}')`);
      ok("대표만 남기기 = 나머지 사람 확정 ✕", todo.length > 0 && todo.every((s) => it2.dup_member_confirmed[it2.dup_members.indexOf(s)] === "exclude") && !todo.includes(pick.dup_rep)
        && (await ev("S.stem")) === pick.dup_rep, JSON.stringify(todo));
      ok("목록 ✕ 표시·번호 안 잘림", await ev(`${JSON.stringify(todo)}.every(s=>{const o=[...$('#photo').options].find(o=>o.value===s);return !o||/^✕ \\d+\\. /.test(o.textContent)})`));
      ok("다시 누를 것 없음", await ev("dupTodo(S.item).length===0 && $('#dupdrop [data-act=\"dup-keep-rep\"]').disabled"));
    } }

  // ── C14: 비슷한 열매 한꺼번에 찾기 — G = 찾기, 후보 누르기 = 뺌/넣음, Enter = 모두 받기(되돌리기 한 번), Esc = 버림
  {
    await idle();
    const hashL = () => ev("(()=>{let h=0;for(let i=0;i<S.L.length;i++)h=(Math.imul(h,31)+S.L[i])|0;return h})()");
    const u0 = await ev("S.undo.length"), d0 = await ev("S.dirty"), h0 = await hashL(), cur0 = await ev("S.cur");
    // 1) 도우미 없이 정해진 후보로: 빈 곳 후보는 새 번호, 이미 칠한 열매 위 후보는 처음부터 빠짐
    const E = await findEmpty(40), big = await ev("(()=>{const v=centers.find(c=>c[3]>400);return v?v[0]:0})()");
    const r1 = await ev(`(()=>{const sq=(x0,y0,w)=>({x0,y0,w,h:w,m:new Uint8Array(w*w).fill(1),n:w*w,on:true});
      const a=sq(${E[0]}+5,${E[1]}+5,30);
      simC=document.createElement('canvas');simC.width=S.W;simC.height=S.H;simD=simC.getContext('2d').createImageData(S.W,S.H);
      S.sim={gen:S.gen,v:1,cands:[a]};simPaint(a);setTool('sam');const btn=!!document.querySelector('[data-act=sim-accept]');
      const n0=maxId();simAccept();const v=S.L[(${E[1]}+20)*S.W+${E[0]}+20];return {btn,v,n0,dr:S.draftIds.has(v),sim:S.sim,find:!!document.querySelector('[data-act=sim-find]')}})()`);
    ok("C14 받기 = 빈 곳 후보마다 새 번호 · 노란 동그라미 · 찾기 단추로 돌아감", r1.btn && r1.v === r1.n0 + 1 && r1.dr && r1.sim === null && r1.find, JSON.stringify(r1));
    await key("Control+z"); ok("C14 Ctrl+Z 한 번 = 받기 전 그대로", (await hashL()) === h0);
    if (big) {
      const skipped = await ev(`(()=>{const c=centers.find(c=>c[0]===${big}),x0=Math.round(c[1])-5,y0=Math.round(c[2])-5,m=new Uint8Array(100).fill(1);
        S.sim={gen:S.gen,v:1,cands:[{x0,y0,w:10,h:10,m,n:100,on:true}]};const u=S.undo.length;simAccept();return S.undo.length===u&&/받을 후보가 없었/.test($('#msg').textContent)})()`);
      ok("C14 이미 칠한 열매 위 후보는 안 칠함", skipped && (await hashL()) === h0);
    }
    // 2) 실제 도우미(5112)로: 지금 색 = 가운데 크기의 열매 → G
    const ex = await ev("(()=>{const c=[...centers].sort((a,b)=>a[3]-b[3]);return c.length?c[c.length>>1][0]:0})()");
    if (ex) {
      await ev(`setCur(${ex})`); await key("g"); await sleep(300); await idle(90000);
      const st = await ev("({n:S.sim?S.sim.cands.length:0,msg:$('#msg').textContent,tool:S.tool})");
      ok("C14 G = 후보를 보이거나 «못 찾음» 안내", st.tool === "sam" && (st.n > 0 ? /후보 \d+개/.test(st.msg) : /찾지 못했|꺼져|실패/.test(st.msg)), JSON.stringify(st));
      if (st.n > 0) {
        await shot("03_c14_similar");
        const yellow = await ev("(()=>{const d=hudX.getImageData(0,0,hud.width,hud.height).data;let n=0;for(let i=0;i<d.length;i+=16)if(d[i]>200&&d[i+1]>180&&d[i+2]<80)n++;return n})()");
        ok("C14 노란 테두리가 화면에 그려짐", yellow > 20, yellow + "점");
        // 후보 안에서 가운데(무게중심)에 가장 가까운 점 — 파이어폭스는 마우스 좌표를 정수로 반올림해서 가장자리 점은 빗나갈 수 있다
        const p = await ev("(()=>{const c=S.sim.cands[0];let sx=0,sy=0,n=0;for(let k=0;k<c.m.length;k++)if(c.m[k]){sx+=k%c.w;sy+=(k/c.w)|0;n++}const mx=sx/n,my=sy/n;let b=null,bd=1e18;for(let k=0;k<c.m.length;k++)if(c.m[k]){const d=(k%c.w-mx)**2+(((k/c.w)|0)-my)**2;if(d<bd){bd=d;b=[c.x0+k%c.w,c.y0+((k/c.w)|0)]}}return b})()");
        const z0 = await ev("[S.z,S.ox,S.oy]");
        await ev(`(()=>{const r=stage.getBoundingClientRect();stopAnim();S.z=Math.max(S.z,2);S.ox=r.width/2-(${p[0]}+0.5)*S.z;S.oy=r.height/2-(${p[1]}+0.5)*S.z;applyView()})()`);   // 확대해서 후보를 화면 가운데에
        await page.mouse.click(...(await scr(...p))); await sleep(100);
        const off = await ev("[S.sim.cands[0].on, $('#sim-n').textContent, S.undo.length]");
        ok("C14 후보 누르기 = 뺌(칠하지 않음)", off[0] === false && off[1] === `${st.n - 1}/${st.n}` && off[2] === u0, JSON.stringify(off));
        await ev(`S.z=${z0[0]};S.ox=${z0[1]};S.oy=${z0[2]};applyView()`);
        const n0 = await ev("idsNow().ids.length");
        await key("Enter"); await sleep(100);
        const got = await ev("idsNow().ids.length") - n0;
        ok("C14 Enter = 남은 후보 받기(뺀 것 제외)", got >= 1 && got <= st.n - 1 && (await ev("S.sim")) === null && (await ev("S.undo.length")) === u0 + 1, `${got}/${st.n - 1}`);
        await key("Control+z"); ok("C14 받은 것 Ctrl+Z 한 번에 되돌림", (await hashL()) === h0);
        await key("g"); await sleep(300); await idle(90000);
        const had = await ev("!!S.sim"); await key("Escape");
        ok("C14 Esc = 후보 버림·라벨 그대로", had && (await ev("S.sim")) === null && (await hashL()) === h0 && /버렸습니다/.test(await ev("$('#msg').textContent")));
      }
    }
    await ev(`setCur(${cur0});setDirty(${d0})`); await key("b");
  }

  // ── C13: 손 뗄 때 번호 가운데를 바뀐 화소만으로 고친다 → 사진 전체를 다시 훑은 값과 늘 같아야 한다
  {
    await idle();
    const u0 = await ev("S.undo.length"), d0 = await ev("S.dirty");
    const same = () => ev("(()=>{const a=JSON.stringify([centers,S.idsCache]);computeCenters();return a===JSON.stringify([centers,S.idsCache])})()");
    const c = await ev("(()=>{const v=centers.find(c=>c[3]>200);return v?[Math.round(v[1]),Math.round(v[2])]:[Math.floor(S.W/2),Math.floor(S.H/2)]})()");
    const drag = async (btn, k) => {
      const [sx, sy] = await scr(c[0] - 30, c[1] + k), [tx, ty] = await scr(c[0] + 30, c[1] + k);
      await page.mouse.move(sx, sy); await page.mouse.down({ button: btn }); await page.mouse.move(tx, ty, { steps: 6 }); await page.mouse.up({ button: btn }); await sleep(60);
    };
    const r = [];
    await key("b"); await key("n"); await drag("left", 0); r.push(await same());      // 새 번호로 열매 위를 칠함(다른 열매 보호)
    await drag("right", 6); r.push(await same());                                      // 오른쪽 = 지우기
    await key("e"); await drag("left", -6); r.push(await same());                      // 지우개
    await key("Control+z"); r.push(await same()); await key("Control+z"); r.push(await same());
    await key("Control+y"); r.push(await same());
    ok("C13 바뀐 화소만 고친 가운데 = 전체 다시 훑은 값(칠하기·지우기·되돌리기·다시)", r.every(Boolean) && (await ev("S.undo.length")) > u0, JSON.stringify(r));
    const t = await ev("(()=>{const t0=performance.now();for(let k=0;k<20;k++)changed();return (performance.now()-t0)/20})()");
    ok("C13 changed() 한 번 8ms 이하(사진 전체를 안 훑음)", t <= 8, t.toFixed(2) + "ms");
    while ((await ev("S.undo.length")) > u0) await key("Control+z");
    await ev(`setDirty(${d0})`); await key("b");
    // ✨ 계산 중 커서 = progress, 끝나면 도구 커서로
    const cur = await ev("(()=>{setTool('sam');samBusy(true);const a=getComputedStyle(stage).cursor,b=getComputedStyle(hud).cursor;samBusy(false);const c=getComputedStyle(stage).cursor;setTool('brush');return [a,b,c]})()");
    ok("C13 ✨ 계산 중 커서 progress·끝나면 원래대로", cur[0] === "progress" && cur[1] === "progress" && cur[2] === "cell", JSON.stringify(cur));
  }

  // ── 작은 화면(노트북 1280×720 · 1024×600)
  ok("C12 큰 화면: 도구 설명 펼침·접기 단추 없음", await ev("$('#options .tip').open && getComputedStyle($('#options .tip>summary')).display==='none'"));
  const LONG = "13번으로 칠했습니다. 마음에 안 들면 같은 자리를 다시 누르세요 — 후보 3개 중 1번째 모양";
  for (const [w, h] of [[1280, 720], [1024, 600], [800, 600]]) {
    await page.setViewportSize({ width: w, height: h }); await sleep(400);
    const lay = await ev("(()=>{const q=(s)=>document.querySelector(s).getBoundingClientRect();const st=q('#stage'),zb=q('#zoombar'),sv=q('#save');return {stageH:st.height|0,zoomIn:zb.right<=st.right+1&&zb.bottom<=st.bottom+1,saveVis:sv.right<=innerWidth&&sv.bottom<=innerHeight,scrollX:document.documentElement.scrollWidth>innerWidth}})()");
    ok(`${w}×${h} 화면 배치`, lay.stageH > 200 && lay.zoomIn && lay.saveVis && !lay.scrollX, JSON.stringify(lay));
    if (w <= 1024) {
      await key("s"); await ev(`say(${JSON.stringify(LONG)})`);
      // 알림: 두 줄 안에 다 들어가고(글자 높이 ≤ 칸 높이), 잘려도 title 에 전체
      const m = await ev("(()=>{const m=$('#msg'),r=document.createRange();r.selectNodeContents(m);return {w:m.clientWidth,textH:r.getBoundingClientRect().height|0,boxH:m.clientHeight,title:m.title,sb:$('#statusbar').getBoundingClientRect().bottom<=innerHeight+1}})()");
      ok(`C12 ${w}×${h} 알림 두 줄·title 전체`, m.title === LONG && m.textH <= m.boxH + 1 && m.w >= 300 && m.sb, JSON.stringify(m));
      const t0 = await ev("[$('#options .tip').open, getComputedStyle($('#options .tip>summary')).display]");
      await page.click("#options .tip>summary"); await key("b");
      ok(`C12 ${w}×${h} 설명 접힘·펼친 채 도구 바꿔도 유지`, t0[0] === false && t0[1] !== "none" && await ev("$('#options .tip').open && !!$('#options [data-size]')"), JSON.stringify(t0));
      await page.click("#options .tip>summary");
    }
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
