// 그림판(/) UX·속도·접근성 감사 — 실제 브라우저(Playwright)로 재서 JSON 으로 남긴다 (f1 레인, 작성: 2026-09-25)
// 쓰는 법: node f1_audit.mjs <모래상자 주소> <firefox|chromium> <out_dir>   (실서버 5111 금지 · 저장은 하지 않는다)
import fs from "node:fs";
import path from "node:path";
import { chromium, firefox } from "/home/kds0206/.local/share/playwright-runtime/node_modules/playwright/index.mjs";

const [BASE, BR = "firefox", OUT = "."] = process.argv.slice(2);
if (!BASE || /:5111\b/.test(BASE)) { console.error("모래상자 주소를 주세요(5111 금지)"); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });
const R = { browser: BR, perf: {}, a11y: {}, ux: {}, errors: [], notes: [] };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await (BR === "chromium" ? chromium : firefox).launch();
const ctx = await b.newContext({ viewport: { width: 1366, height: 768 } });
const page = await ctx.newPage();
page.on("pageerror", (e) => R.errors.push("pageerror: " + e.message));
page.on("console", (m) => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) R.errors.push("console: " + m.text()); });
page.on("dialog", async (d) => { R.notes.push("dialog: " + d.message().slice(0, 60)); await d.dismiss(); });
const ev = (expr) => page.evaluate((e) => window.eval(e), expr);
const idle = async (ms = 30000) => { const t = Date.now(); while (Date.now() - t < ms) { if (await ev("!S.busy && !S.samBusy && document.querySelector('#loading').style.display!=='block'")) return; await sleep(50); } };
const shot = (n) => page.screenshot({ path: path.join(OUT, `${BR}_${n}.png`) });
const med = (a) => { const s = [...a].sort((p, q) => p - q); return s.length ? s[s.length >> 1] : null; };

try {
  /* ── 1. 첫 화면 ── */
  await page.goto(BASE + "/"); await page.evaluate(() => localStorage.setItem("who", "감사봇"));
  await ctx.clearCookies();
  let t0 = Date.now();
  await page.goto(BASE + "/", { waitUntil: "load" });
  const tLoadEvent = Date.now() - t0;
  await page.waitForFunction(() => window.eval("S.L && S.stem"), null, { timeout: 60000 }); await idle();
  R.perf.first_open_ms = Date.now() - t0; R.perf.load_event_ms = tLoadEvent;
  R.perf.first_resources = await page.evaluate(() => performance.getEntriesByType("resource").map((e) => ({
    url: e.name.replace(/^https?:\/\/[^/]+/, "").slice(0, 80), ms: Math.round(e.duration), kb: Math.round((e.transferSize || e.encodedBodySize || 0) / 1024) })));
  R.perf.first_fruit = await ev("S.fruit"); R.perf.first_stem = await ev("S.stem");
  R.perf.first_size = await ev("[S.W,S.H]"); R.perf.first_ids = await ev("(S.idsCache||{ids:[]}).ids.length");
  R.perf.list_pages = R.perf.first_resources.filter((r) => r.url.includes("/api/list")).length;
  R.perf.js_kb = (R.perf.first_resources.find((r) => r.url.includes("paint.js")) || {}).kb;
  await shot("1_first");

  /* 정적·이미지 캐시 헤더 */
  R.perf.headers = {};
  for (const u of ["/static/paint/paint.js", "/static/paint/paint.css", `/img?fruit=${R.perf.first_fruit}&stem=${encodeURIComponent(R.perf.first_stem)}`,
    `/mask?fruit=${R.perf.first_fruit}&stem=${encodeURIComponent(R.perf.first_stem)}&layer=gt`, `/api/list?fruit=${R.perf.first_fruit}&sort=name&page_size=500&page=1`]) {
    const r = await page.request.get(BASE + u); const h = r.headers();
    R.perf.headers[u.split("?")[0]] = { status: r.status(), cache: h["cache-control"] || "(없음)", etag: !!h.etag, enc: h["content-encoding"] || "(없음)", type: h["content-type"], kb: Math.round((await r.body()).length / 1024) };
  }

  /* ── 2. 과일마다 열기 시간·사진 넘김 시간·계산 비용 ── */
  R.perf.fruits = {};
  const fruits = await page.$$eval("#fruit option", (o) => o.map((x) => x.value));
  for (const f of fruits) {
    t0 = Date.now(); await page.selectOption("#fruit", f);
    await page.waitForFunction((ff) => window.eval(`S.fruit==='${ff}' && S.L && !S.busy`), f, { timeout: 60000 }); await idle();
    const open_ms = Date.now() - t0;
    const sw = [];
    for (let i = 0; i < 3; i++) {
      const before = await ev("S.stem"); t0 = Date.now(); await page.keyboard.press("d");
      await page.waitForFunction((bf) => window.eval(`S.stem!=='${bf}' && !S.busy`), before, { timeout: 60000 }); await idle();
      sw.push(Date.now() - t0);
    }
    const cost = await ev(`(()=>{const t=(fn,n)=>{const a=performance.now();for(let i=0;i<n;i++)fn();return +((performance.now()-a)/n).toFixed(1)};
      return {W:S.W,H:S.H,ids:(S.idsCache||{ids:[]}).ids.length,undo_snapshot:t(snapshot,3),computeCenters:t(computeCenters,3),drawHud:t(drawHud,10),renderPalette:t(renderPalette,3),idsNow:t(idsNow,2),maxId:t(maxId,2),paintRect_full:t(()=>paintRect(0,0,S.W,S.H),2),boxesNow:t(boxesNow,1),encodeInstances:t(encodeInstances,1)}})()`);
    const img = R.perf.first_resources; // placeholder to keep shape
    const res = await page.evaluate(() => performance.getEntriesByType("resource").slice(-12).map((e) => ({ url: e.name.replace(/^https?:\/\/[^/]+/, "").split("&stem")[0].slice(0, 40), ms: Math.round(e.duration), kb: Math.round((e.transferSize || e.encodedBodySize || 0) / 1024) })));
    R.perf.fruits[f] = { open_ms, switch_ms: sw, switch_med: med(sw), ...cost, last_resources: res.filter((r) => /img|mask|instances/.test(r.url)) };
  }

  /* ── 3. 붓질 한 번(30점)의 벽시계 시간 + 긴 작업(크로미움만) ── */
  await page.selectOption("#fruit", "peach"); await page.waitForFunction(() => window.eval("S.fruit==='peach' && S.L && !S.busy"), null, { timeout: 60000 }); await idle();
  await page.keyboard.press("b");
  if (BR === "chromium") await page.evaluate(() => { window.__long = []; new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__long.push(Math.round(e.duration)))).observe({ type: "longtask" }); });
  const r0 = await ev("(()=>{const r=stage.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()");
  const strokes = [];
  for (let k = 0; k < 3; k++) {
    t0 = performance.now();
    await page.mouse.move(r0[0] - 100, r0[1] + k * 12); await page.mouse.down();
    for (let i = 1; i <= 30; i++) await page.mouse.move(r0[0] - 100 + i * 7, r0[1] + k * 12 + Math.sin(i) * 4);
    await page.mouse.up(); strokes.push(Math.round(performance.now() - t0));
  }
  R.perf.stroke_ms = strokes; R.perf.stroke_undo_len = await ev("S.undo.length");
  if (BR === "chromium") R.perf.longtasks_ms = await page.evaluate(() => window.__long);
  R.perf.mousemove_hud_ms = await ev("(()=>{const a=performance.now();for(let i=0;i<20;i++){mouse={sx:100+i,sy:100};drawHud()}return +((performance.now()-a)/20).toFixed(2)})()");
  await shot("2_brush");
  await ev("undo();undo();undo();setDirty(false)");

  /* ── 4. ✨ 클릭 칠하기 첫 클릭·둘째 클릭 ── */
  await page.keyboard.press("s");
  const c = await ev("centers.length? centers.slice(0,2).map(c=>[Math.round(c[1]),Math.round(c[2])]) : []");
  R.perf.sam = [];
  for (const [ix, iy] of c) {
    const [sx, sy] = await ev(`(()=>{const r=stage.getBoundingClientRect();return [r.left+S.ox+(${ix}+0.5)*S.z, r.top+S.oy+(${iy}+0.5)*S.z]})()`);
    await ev("S.protect=false");
    t0 = Date.now(); await page.mouse.click(sx, sy);
    await page.waitForFunction(() => window.eval("!S.samBusy && !/찾는 중/.test(document.querySelector('#msg').textContent)"), null, { timeout: 90000 });
    R.perf.sam.push({ ms: Date.now() - t0, msg: await ev("document.querySelector('#msg').textContent") });
  }
  await shot("3_sam");
  await ev("while(S.undo.length)undo();setDirty(false)");

  /* ── 5. 접근성: 이름·크기·키보드 도달·라벨·live ── */
  R.a11y = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const name = (e) => (e.getAttribute("aria-label") || (e.labels && e.labels[0] && e.labels[0].textContent) || e.textContent.replace(/\s+/g, " ").trim() || e.title || e.placeholder || "").slice(0, 30);
    const items = [...document.querySelectorAll("button, a, input, select, .sw, #who, #curbox")].filter(vis).map((e) => {
      const r = e.getBoundingClientRect(), fs = parseFloat(getComputedStyle(e).fontSize);
      return { sel: (e.id ? "#" + e.id : e.tagName.toLowerCase() + (e.className ? "." + String(e.className).split(" ")[0] : "")), name: name(e), w: Math.round(r.width), h: Math.round(r.height),
        tabbable: e.tabIndex >= 0, role: e.getAttribute("role") || e.tagName.toLowerCase(), pressed: e.getAttribute("aria-pressed"), fontPx: fs, titleOnly: !e.getAttribute("aria-label") && !e.textContent.trim() && !!e.title };
    });
    const small = items.filter((i) => i.w < 24 || i.h < 24);
    const noName = items.filter((i) => !i.name);
    const notTab = items.filter((i) => !i.tabbable);
    const lum = (rgb) => { const [r, g, b] = rgb.match(/\d+/g).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
    const cr = (fg, bg) => { const a = lum(fg), b = lum(bg); return +((Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)).toFixed(2); };
    const face = "rgb(192,192,192)";
    const m = document.querySelector("#msg"); const keep = m.className;
    const contrast = {};
    for (const cls of ["", "err", "ok"]) { m.className = cls; contrast["#msg." + (cls || "plain")] = cr(getComputedStyle(m).color, face); }
    m.className = keep;
    contrast["#tools span(11px)"] = cr(getComputedStyle(document.querySelector("#tools span")).color, face);
    contrast["#options(12px)"] = cr(getComputedStyle(document.querySelector("#options")).color, face);
    contrast["#title"] = cr("rgb(255,255,255)", "rgb(0,0,128)");
    contrast["#t-dirty on title"] = cr("rgb(255,216,74)", "rgb(16,132,208)");
    contrast[".sw white text on id1"] = cr("rgb(255,255,255)", getComputedStyle(document.querySelector(".sw[data-id]:not(.erase)") || document.body).backgroundColor);
    contrast[".drop kbd"] = cr("rgb(0,0,0)", "rgb(255,255,255)");
    const tiny = [...document.querySelectorAll("#win *")].filter((e) => vis(e) && e.children.length === 0 && e.textContent.trim() && parseFloat(getComputedStyle(e).fontSize) < 12).length;
    return {
      n_interactive: items.length, small_targets: small.map((i) => `${i.sel} ${i.name} ${i.w}x${i.h}`), no_name: noName.map((i) => i.sel),
      title_only_name: items.filter((i) => i.titleOnly).map((i) => `${i.sel}(${i.name})`), not_keyboard: notTab.map((i) => `${i.sel} ${i.name}`),
      tools_aria_pressed: items.filter((i) => i.pressed !== null).length, msg_live: m.getAttribute("aria-live") || "(없음)", loading_live: document.querySelector("#loading").getAttribute("aria-live") || "(없음)",
      selects_labelled: [...document.querySelectorAll("select, #q")].map((s) => `#${s.id}: ${s.labels && s.labels.length ? "label" : s.getAttribute("aria-label") ? "aria-label" : s.title ? "title만" : "없음"}`),
      canvas_role: document.querySelector("#stage").getAttribute("role") || "(없음)", canvas_label: document.querySelector("#stage").getAttribute("aria-label") || "(없음)",
      menus_aria: document.querySelectorAll(".mbtn[aria-haspopup], .mbtn[aria-expanded]").length, contrast, text_under_12px: tiny,
      document_title: document.title, lang: document.documentElement.lang, focus_style: getComputedStyle(document.querySelector("#save"), ":focus-visible").outlineStyle,
      reduced_motion_honoured: /prefers-reduced-motion/.test(String(animateTo)),
    };
  });
  /* 키보드 걷기: Tab 을 눌러 무엇에 닿는지 · 메뉴가 Enter 로 열리는지 · 화살표가 되는지 · Esc 뒤 초점 */
  await page.click("#title");
  const order = [];
  for (let i = 0; i < 24; i++) { await page.keyboard.press("Tab"); order.push(await ev("(()=>{const e=document.activeElement;return e.id?'#'+e.id:e.tagName.toLowerCase()+':'+(e.textContent||'').trim().slice(0,8)})()")); }
  R.a11y.tab_order = order;
  await page.focus(".mbtn"); await page.keyboard.press("Enter");
  R.a11y.menu_opens_with_enter = await ev("!!document.querySelector('.menu.open')");
  await page.keyboard.press("ArrowDown");
  R.a11y.menu_arrow_moves_focus = await ev("!!document.activeElement.closest('.drop')");
  await page.keyboard.press("Tab");
  R.a11y.menu_tab_reaches_item = await ev("!!document.activeElement.closest('.drop')");
  await page.keyboard.press("Escape");
  R.a11y.esc_closes_menu = !(await ev("!!document.querySelector('.menu.open')"));
  R.a11y.focus_after_esc = await ev("(()=>{const e=document.activeElement;return e.id?'#'+e.id:e.tagName.toLowerCase()+':'+(e.textContent||'').trim().slice(0,8)})()");
  // 팔레트 색은 키보드로 고를 수 있나 (Tab 으로 .sw 에 닿는지)
  R.a11y.swatch_tabbable = order.some((o) => o.startsWith("div:"));
  // 단축키가 입력칸 초점에서 새는지 (이름 찾기 칸에서 d 를 치면 사진이 넘어가는지)
  const stemBefore = await ev("S.stem"); await page.focus("#q"); await page.keyboard.type("d"); await sleep(400);
  R.a11y.shortcut_leaks_from_input = (await ev("S.stem")) !== stemBefore; await page.fill("#q", "");
  await page.focus(".mbtn"); await page.keyboard.press("Enter"); await shot("4_menu_keyboard"); await page.keyboard.press("Escape");

  /* ── 6. 작은 화면·큰 글씨 ── */
  R.ux.viewports = {};
  for (const [w, h] of [[1024, 640], [800, 600], [1366, 768]]) {
    await page.setViewportSize({ width: w, height: h }); await sleep(300); await ev("fit(false)");
    R.ux.viewports[`${w}x${h}`] = await page.evaluate(() => {
      const st = document.querySelector("#stage").getBoundingClientRect(), nav = document.querySelector("#nav").getBoundingClientRect(), mb = document.querySelector("#menubar").getBoundingClientRect();
      const pal = document.querySelector("#palette"), sw = document.querySelector("#swatches");
      return { stage: `${Math.round(st.width)}x${Math.round(st.height)}`, menubar_h: Math.round(mb.height), nav_wraps: nav.height > 40, overflow_x: document.documentElement.scrollWidth > innerWidth,
        stage_pct: Math.round(st.width * st.height * 100 / (innerWidth * innerHeight)), palette_scroll: sw.scrollWidth > sw.clientWidth, toolbox_scroll: document.querySelector("#toolbox").scrollHeight > document.querySelector("#toolbox").clientHeight };
    });
    if (w === 800) await shot("5_800x600");
  }
  await page.setViewportSize({ width: 1366, height: 768 });
  /* 글씨 크기 150% 흉내(root font 21px) — 메뉴·도구 상자가 깨지는지 */
  await page.addStyleTag({ content: "html,body{font-size:21px!important}" }); await sleep(200);
  R.ux.font150 = await page.evaluate(() => ({ nav_h: Math.round(document.querySelector("#nav").getBoundingClientRect().height), menubar_h: Math.round(document.querySelector("#menubar").getBoundingClientRect().height),
    tools_clipped: [...document.querySelectorAll("#tools button")].some((b) => b.scrollHeight > b.clientHeight + 2), overflow_x: document.documentElement.scrollWidth > innerWidth }));
  await shot("6_font150");

  /* ── 7. 상태 알림이 사라지는지(붙박이 오류) · 확인창 사용 개수 ── */
  R.ux.uses_native_dialogs = await ev("(String(save)+String(askWho)+String(leaveOk)+JSON.stringify(Object.values(ACTS).map(String))).split(/confirm\\(|prompt\\(|alert\\(/).length-1");
  R.ux.title_updates_with_photo = (await page.title()).includes(await ev("S.stem"));
  R.ux.transitions_all = await page.evaluate(() => [...document.styleSheets].flatMap((s) => { try { return [...s.cssRules]; } catch { return []; } }).some((r) => /transition:\s*all/.test(r.cssText)));
  R.ux.buttons_without_hover_or_active = await page.evaluate(() => [...document.styleSheets].flatMap((s) => { try { return [...s.cssRules]; } catch { return []; } }).filter((r) => /:active/.test(r.selectorText || "")).length);
} catch (e) { R.errors.push("audit: " + e.message); }
fs.writeFileSync(path.join(OUT, `${BR}.json`), JSON.stringify(R, null, 1));
console.log(JSON.stringify({ browser: BR, first_open_ms: R.perf.first_open_ms, sam: R.perf.sam, errors: R.errors }, null, 0));
await b.close();
