/* 화면(JS) 한 덩어리 만들기 — 시뮬(`boxsim.js`·`modesim.js`)이 «지금 배포되는 화면 코드»에서
   함수를 글자 그대로 떼어 낼 때 쓴다.  작성: 2026-09-20 (구조 정리 사이클 3 1차)

왜 필요한가
  시뮬은 `app.js` **한 파일**을 읽어 `src.indexOf("function bpush()")` 처럼 문구로 구간을 잘랐다.
  구조 사이클 3 이 화면 코드를 `static/js/*.js` 여러 파일로 쪼개면 그 문구를 못 찾아
  시뮬 81항목이 통째로 죽는다(cycle_1/stage2_review.md §2 · tests/unit/u5_js_contract.py).
  → 그래서 «`index.html` 의 `<script>` 순서대로 파일을 이어 붙인 한 덩어리» 를 만들어 준다.
     시뮬은 그 덩어리에 예전과 **똑같은** 문구 자르기를 한다(시험 두 줄만 바뀐다).

지키는 것
  · 순서는 **`index.html` 이 정한다**(시험이 파일 목록을 따로 적어 두지 않는다 — 적어 두면 낡는다).
  · 이어 붙일 때 파일 사이에 줄바꿈 하나만 넣는다. 글자를 고치지 않는다(떼어 낸 코드가 그대로여야
    시뮬이 «지금 배포되는 코드» 를 시험하는 것이 된다).
  · 쪼개기 **전**(app.js·ui.js 두 파일)에도 똑같이 동작한다 — 그래서 쪼개기 전후를 같은 로더로 잰다.

스위치(옛 로더로 되돌리기)
  `SIM_SRC=appjs node boxsim.js` → 예전처럼 `app.js` 한 파일만 읽는다(`tests/lib/paths.js` 의 APP_JS).
  기본값은 이 덩어리다.
*/
"use strict";
const fs = require("fs");
const path = require("path");
const P = require("../../lib/paths.js");

/** `index.html` 의 `<script src="/static/...">` 를 **적힌 순서대로** 돌려준다(절대경로). */
function sources() {
  const html = fs.readFileSync(path.join(P.STATIC, "index.html"), "utf8");
  const out = [];
  const re = /<script\s+[^>]*src="([^"]+)"/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const rel = m[1].replace(/^\/static\//, "").replace(/^\//, "").replace(/\?.*$/, "");
    const p = path.join(P.STATIC, rel);
    if (fs.existsSync(p)) out.push(p);
  }
  return out;
}

/** 위 파일들을 이어 붙인 한 덩어리. */
function bundle() {
  return sources().map((p) => fs.readFileSync(p, "utf8")).join("\n");
}

/** 시뮬이 쓰는 입구 — 스위치(SIM_SRC=appjs)면 옛 로더(app.js 한 파일). */
function simSource() {
  if ((process.env.SIM_SRC || "") === "appjs") return fs.readFileSync(P.APP_JS, "utf8");
  return bundle();
}

/** 사람이 확인할 때: 무엇을 몇 줄씩 붙였는지. */
function describe() {
  return sources().map((p) => path.relative(P.STATIC, p)
    + "(" + fs.readFileSync(p, "utf8").split("\n").length + "줄)").join(" + ");
}

module.exports = { sources, bundle, simSource, describe };

if (require.main === module) {
  const b = bundle();
  console.log("덩어리 " + b.split("\n").length + "줄 = " + describe());
}
