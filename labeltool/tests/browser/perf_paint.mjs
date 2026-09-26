// 그림판 속도 기준선을 재는 스크립트 — 첫 화면 로드 · 사진 넘김 · ✨ 첫 클릭(ms)
// 작성: 2026-09-25 (C00 기준선)
// 쓰는 법(모래상자 서버 전용, 5111 금지): node tests/browser/perf_paint.mjs <base_url> <firefox|chromium> <out_dir>
// 결과: <out_dir>/<browser>_perf.json. 저장은 하지 않는다(✨ 는 칠하기만 하고 사진을 넘기지 않는다).
import fs from "node:fs";
import path from "node:path";
import { chromium, firefox } from "/home/kds0206/.local/share/playwright-runtime/node_modules/playwright/index.mjs";

const [BASE, BR = "chromium", OUT = "."] = process.argv.slice(2);
if (!BASE || /:5111\b/.test(BASE)) { console.error("모래상자 주소를 주세요(5111 금지)"); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const med = (a) => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const p90 = (a) => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(s.length * 0.9))]; };
const stat = (a) => ({ n: a.length, median: med(a), p90: p90(a), min: Math.min(...a), max: Math.max(...a), all: a });

const b = await (BR === "chromium" ? chromium : firefox).launch();
const res = { browser: BR, base: BASE, at: new Date().toISOString(), errors: [] };

async function fresh() {                       // 캐시 없는 새 창
  const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
  await ctx.addInitScript(() => localStorage.setItem("who", "속도봇"));
  const page = await ctx.newPage();
  page.on("pageerror", (e) => res.errors.push("pageerror: " + e.message));
  page.on("dialog", (d) => d.dismiss());      // 확인창이 뜨면 취소(저장 안 함)
  const ev = (e) => page.evaluate((x) => window.eval(x), e);
  const ready = () => page.waitForFunction(() => window.eval(
    "S.L && S.stem && !S.busy && document.querySelector('#loading').style.display!=='block'"), null, { timeout: 60000, polling: 20 });
  return { ctx, page, ev, ready };
}

try {
  // ① 첫 화면 로드 — 주소 입력부터 사진·라벨이 다 그려져 손댈 수 있을 때까지(새 창 3번)
  const load = [], dcl = [];
  for (let i = 0; i < 3; i++) {
    const { ctx, page, ready } = await fresh();
    const t0 = Date.now();
    await page.goto(BASE + "/");
    await ready();
    load.push(Date.now() - t0);
    dcl.push(Math.round(await page.evaluate(() => performance.getEntriesByType("navigation")[0].domContentLoadedEventEnd)));
    await ctx.close();
  }
  res.first_load_ms = stat(load); res.dom_content_loaded_ms = stat(dcl);
  console.log("첫 화면 로드", JSON.stringify(res.first_load_ms));

  // ② 사진 넘김(D) — 바꾼 것 없이 다음 사진이 다 그려질 때까지. 과일 둘 × 8번
  const { ctx, page, ev, ready } = await fresh();
  await page.goto(BASE + "/"); await ready();
  res.flip_ms = {};
  for (const fr of ["peach", "apple"]) {
    await page.selectOption("#fruit", fr);
    await page.waitForFunction((f) => window.eval(`S.fruit==='${f}'`), fr, { timeout: 60000 }); await ready();
    const a = [];
    for (let i = 0; i < 8; i++) {
      const s0 = await ev("S.stem");
      const t0 = Date.now();
      await page.keyboard.press("d");
      await page.waitForFunction((s) => window.eval(`S.stem!==${JSON.stringify(s)}`), s0, { timeout: 60000, polling: 10 });
      await ready();
      a.push(Date.now() - t0);
    }
    res.flip_ms[fr] = stat(a);
    console.log("사진 넘김", fr, JSON.stringify(res.flip_ms[fr]));
    // C06: 사람이 한 장을 보는 동안(1.5초) 앞·뒤 사진을 미리 받아 둔 뒤 넘김 — 실제 쓰는 모양
    const c = [];
    for (let i = 0; i < 6; i++) {
      await sleep(1500);
      const s0 = await ev("S.stem");
      const t0 = Date.now();
      await page.keyboard.press("d");
      await page.waitForFunction((s) => window.eval(`S.stem!==${JSON.stringify(s)}`), s0, { timeout: 60000, polling: 10 });
      await ready();
      c.push(Date.now() - t0);
    }
    (res.flip_dwell_ms = res.flip_dwell_ms || {})[fr] = stat(c);
    console.log("사진 넘김(1.5초 본 뒤)", fr, JSON.stringify(res.flip_dwell_ms[fr]));
  }

  // ③ ✨ 첫 클릭 — 사진마다 처음 누른 클릭(도우미가 그 사진을 처음 봄) · 같은 사진 두 번째 클릭(다른 자리)
  const first = [], second = [], helperSec = [];
  await page.selectOption("#fruit", "peach");
  await page.waitForFunction(() => window.eval("S.fruit==='peach'"), null, { timeout: 60000 }); await ready();
  await page.keyboard.press("s");
  for (let i = 0; i < 3; i++) {
    if (i) {                                   // 칠한 것을 버리고 다음 사진으로 — 확인창은 취소되므로 되돌리기로 비운다
      while (await ev("S.undo.length")) { await page.keyboard.press("Control+z"); await sleep(30); }
      await ev("setDirty(false)");             // 되돌리기로 비워도 «저장 안 됨» 표시는 남는다 → 확인창 없이 넘기려고 끈다
      const s0 = await ev("S.stem"); await page.keyboard.press("d");
      await page.waitForFunction((s) => window.eval(`S.stem!==${JSON.stringify(s)}`), s0, { timeout: 60000 }); await ready();
    }
    for (const [k, arr] of [[0, first], [1, second]]) {
      const xy = await ev(`(()=>{const r=stage.getBoundingClientRect();const fx=${k ? 0.62 : 0.4},fy=${k ? 0.6 : 0.45};return [r.left+S.ox+S.W*fx*S.z, r.top+S.oy+S.H*fy*S.z]})()`);
      const t0 = Date.now();
      await page.mouse.click(xy[0], xy[1]);
      await page.waitForFunction(() => window.eval("S.samBusy"), null, { timeout: 5000, polling: 5 }).catch(() => {});
      await page.waitForFunction(() => window.eval("!S.samBusy"), null, { timeout: 60000, polling: 10 });
      arr.push(Date.now() - t0);
      const m = /\(([\d.]+)초\)/.exec(await ev("document.querySelector('#msg').textContent"));
      if (m) helperSec.push(Math.round(parseFloat(m[1]) * 1000));
    }
  }
  res.sam_first_click_ms = stat(first); res.sam_second_click_ms = stat(second);
  res.sam_helper_reported_ms = helperSec.length ? stat(helperSec) : null;
  console.log("✨ 첫 클릭", JSON.stringify(res.sam_first_click_ms), "두 번째", JSON.stringify(res.sam_second_click_ms));
  while (await ev("S.undo.length")) { await page.keyboard.press("Control+z"); await sleep(30); }
  await ctx.close();
} catch (e) { res.errors.push("script: " + e.message); console.error(e); }
fs.writeFileSync(path.join(OUT, `${BR}_perf.json`), JSON.stringify(res, null, 1));
await b.close();
process.exit(res.errors.length ? 1 : 0);
