/* tests 공용 경로 — node 시뮬(sim/*.js)이 «지금 배포되는» 정적 파일을 떼어 쓸 때 쓴다.
   작성: 2026-09-19.  경로 하드코딩은 이 파일에만 둔다. */
"use strict";
const path = require("path");
const TESTS = path.resolve(__dirname, "..");            // …/260916_라벨링툴/tests
const T = path.resolve(TESTS, "..");                    // …/260916_라벨링툴
module.exports = {
  T, TESTS,
  STATIC: path.join(T, "app", "static"),
  APP_JS: path.join(T, "app", "static", "app.js"),
  UI_JS:  path.join(T, "app", "static", "ui.js"),
};
