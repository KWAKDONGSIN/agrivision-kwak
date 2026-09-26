// 붓질 끝(손 뗄 때) 긴 작업과 그 안의 계산 시간(되돌리기 저장·번호 가운데·팔레트)을 재는 스크립트(C13)
// 작성: 2026-09-25
// 쓰는 법(모래상자 서버 전용, 5111 금지): node tests/browser/perf_stroke.mjs <base_url> <chromium|firefox> <out_json>
// 저장은 하지 않는다. 칠한 것은 Ctrl+Z 로 되돌린다.
import fs from "node:fs";
import { chromium, firefox } from "/home/kds0206/.local/share/playwright-runtime/node_modules/playwright/index.mjs";

const [BASE, BR = "chromium", OUT = ""] = process.argv.slice(2);
if (!BASE || /:5111\b/.test(BASE)) { console.error("모래상자 주소를 주세요(5111 금지)"); process.exit(2); }
const med = (a) => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const b = await (BR === "chromium" ? chromium : firefox).launch();
const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
await ctx.addInitScript(() => localStorage.setItem("who", "속도봇"));
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("dialog", (d) => d.dismiss());
const ev = (e) => page.evaluate((x) => window.eval(x), e);
const ready = () => page.waitForFunction(() => window.eval(
  "S.L && S.stem && !S.busy && document.querySelector('#loading').style.display!=='block'"), null, { timeout: 60000, polling: 20 });
const res = { browser: BR, at: new Date().toISOString(), fruits: {} };
await page.goto(BASE + "/"); await ready();
// 손 뗄 때 도는 함수의 시간을 잰다(함수 이름은 전역이라 감쌀 수 있다)
await ev(`window.__t = {}; for (const f of ["pushUndo","changed","computeCenters","renderPalette","renderCount","drawHud"]) {
  const o = window[f]; window[f] = function (...a) { const t = performance.now(); try { return o.apply(this, a); } finally { (__t[f] = __t[f] || []).push(performance.now() - t); } };
}`).catch((e) => errors.push("wrap: " + e.message));
if (BR === "chromium") await ev(`window.__long = []; new PerformanceObserver((l) => l.getEntries().forEach((e) => __long.push(Math.round(e.duration)))).observe({ type: "longtask" })`);
for (const fr of ["peach", "apple", "blueberry"]) {
  await page.selectOption("#fruit", fr);
  await page.waitForFunction((f) => window.eval(`S.fruit==='${f}'`), fr, { timeout: 60000 }); await ready();
  await page.keyboard.press("b");
  await ev("__t = {}; if (window.__long) __long.length = 0");
  const up = [];
  const r0 = await ev("(()=>{const r=stage.getBoundingClientRect();return [r.left+r.width/2, r.top+r.height/2]})()");
  for (let k = 0; k < 5; k++) {
    await page.mouse.move(r0[0] - 100, r0[1] + k * 12); await page.mouse.down();
    for (let i = 1; i <= 30; i++) await page.mouse.move(r0[0] - 100 + i * 7, r0[1] + k * 12 + Math.sin(i) * 4);
    const t0 = await ev("performance.now()");
    await page.mouse.up();
    // 손 뗀 뒤 다음 그림(frame)까지
    up.push(Math.round(await ev(`new Promise((r) => requestAnimationFrame(() => r(performance.now() - ${t0})))`)));
  }
  await page.waitForTimeout(400);                 // 미뤄 둔 일(있다면)이 끝날 때까지
  const t = await ev("Object.fromEntries(Object.entries(__t).map(([k, v]) => [k, v.map((x) => Math.round(x * 10) / 10)]))");
  const long = BR === "chromium" ? await ev("__long.slice()") : null;
  res.fruits[fr] = { size: await ev("[S.W, S.H]"), ids: await ev("centers.length"), up_to_frame_ms: up, fn_ms: t, longtasks_ms: long };
  console.log(fr, JSON.stringify(res.fruits[fr]));
  while (await ev("S.undo.length")) await page.keyboard.press("Control+z");
  await ev("setDirty(false)");
}
res.errors = errors;
if (OUT) fs.writeFileSync(OUT, JSON.stringify(res, null, 1));
await b.close();
process.exit(errors.length ? 1 : 0);
