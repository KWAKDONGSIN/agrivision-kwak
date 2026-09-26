// 그림판 paint.js 의 sampleOf 를 그대로 잘라 써서 과일별 카운팅 표본 100장 목록(JSON)을 뽑는다 — 쓰는 법: node 이파일 <모래상자 주소>
import fs from "fs";
const B = process.argv[2];
const src = fs.readFileSync(new URL("../../../app/static/paint/paint.js", import.meta.url), "utf8");
const part = src.slice(src.indexOf("const SAMPLE_N"), src.indexOf("function renderList"));
const { sampleOf } = new Function(part + "; return { sampleOf };")();
const out = { rule: "hash32('count100|'+fruit+'|'+stem) 오름차순(같으면 이름순) 앞 100장 — app/static/paint/paint.js sampleOf", fruits: {} };
for (const f of (await (await fetch(B + "/api/fruits")).json()).fruits) {
  const items = [];
  for (let p = 1; ; p++) {
    const j = await (await fetch(`${B}/api/list?fruit=${f.fruit}&sort=name&page_size=500&page=${p}`)).json();
    items.push(...j.items);
    if (p >= j.pages) break;
  }
  out.fruits[f.fruit] = { n_images: items.length, sample: [...sampleOf(f.fruit, items)].sort() };
}
console.log(JSON.stringify(out, null, 1));
