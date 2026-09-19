// 1) toImg 와 draw() 변환의 역함수 일치 확인 (CSS 픽셀 기준)
function mk(s, tx, ty){return {s,tx,ty};}
function drawPos(v, ix, iy){ return [v.tx + v.s*ix, v.ty + v.s*iy]; }   // draw(): translate->scale (CSS px)
function toImg(v, cx, cy){ return [(cx - v.tx)/v.s, (cy - v.ty)/v.s]; } // toImg()
let worst=0;
for (const s of [0.03,0.1,0.5,1,1.7,3,10,30]) for (const tx of [-1234.5, 0, 77.25, 5000])
  for (const ix of [0, 1, 623.5, 1247, 1248]) {
    const [cx,cy]=drawPos(mk(s,tx,tx),ix,ix);
    const [bx,by]=toImg(mk(s,tx,tx),cx,cy);
    worst=Math.max(worst, Math.abs(bx-ix), Math.abs(by-ix));
  }
console.log("A. toImg<->draw 역변환 최대오차(이미지px):", worst);

// 2) 휠 확대: 커서 밑 이미지 좌표가 보존되는가
let worstZoom=0;
for (const s of [0.1,1,3,10]) { let v=mk(s,123.4,-55.6);
  for (let i=0;i<40;i++){ const mx=400,my=300; const before=toImg(v,mx,my);
    const k = i%2? 1/1.15 : 1.15; const ns=Math.max(0.03,Math.min(30,v.s*k));
    v.tx = mx-(mx-v.tx)*(ns/v.s); v.ty = my-(my-v.ty)*(ns/v.s); v.s=ns;
    const after=toImg(v,mx,my);
    worstZoom=Math.max(worstZoom,Math.abs(after[0]-before[0]),Math.abs(after[1]-before[1]));
  } }
console.log("B. 휠 확대 후 커서밑 좌표 이동(이미지px):", worstZoom);

// 3) boxMouseMove «move» 모드 — 화면에서 100px 오른쪽으로 끌었을 때 상자가 실제로 간 거리
function simMove(s, screenStep, nEvents, W=4000, H=4000){
  let b={xyxy:[100,100,200,200]}; let drag={mode:"move",px:50,py:50}; let mx=50,my=50;
  const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  for(let i=0;i<nEvents;i++){
    mx += screenStep/s;                                  // 화면 screenStep px = 이미지 screenStep/s px
    const x=mx,y=my, dx=x-drag.px, dy=y-drag.py;
    const w=b.xyxy[2]-b.xyxy[0], h=b.xyxy[3]-b.xyxy[1];
    const nx=clamp(b.xyxy[0]+dx,0,W-w), ny=clamp(b.xyxy[1]+dy,0,H-h);
    b.xyxy=[Math.round(nx),Math.round(ny),Math.round(nx+w),Math.round(ny+h)];
    drag.px=x; drag.py=y;
  }
  return {moved:b.xyxy[0]-100, should:(screenStep*nEvents)/s};
}
console.log("C. move 모드 (화면 1px 씩 100회 드래그):");
for (const s of [0.25,0.5,1,2,3,5,30]) { const r=simMove(s,1,100);
  console.log(`   배율 ${String(s).padStart(5)}x : 상자가 간 거리 ${String(r.moved).padStart(6)} px  /  마우스가 간 거리 ${r.should.toFixed(2)} px`); }

/* ─────────────────────────────────────────────────────────────────────────────
   🔴 2026-09-19 구조 사이클1 **2차 검수** §2-4 가 붙인 단정.
   그 전까지 이 파일은 숫자를 **찍기만** 하고 아무것도 못박지 않았다 — 즉 `sim/sim` 묶음은
   890개 단정 중 **0개**를 맡고 있었고 rc 가 늘 0 이어서 **절대 실패할 수 없었다**(기준선 ③ 에도
   «-/-» 로 들어가 있었다). 세 가지 불변식을 여기서 못박는다.
   ⚠ 남은 한계(3차·구조3 에 넘김): 위 `toImg`·`drawPos` 는 `app.js` 에서 **떼어 온 것이 아니라
   손으로 옮겨 적은 사본**이다(boxsim.js 는 떼어 온다). 그래서 이 묶음은 «수식이 맞나» 만 보고
   «app.js 가 그 수식을 쓰나» 는 못 본다. 구조 3 이 `view.js` 로 쪼갤 때 boxsim 처럼 떼어 오게
   고치는 것이 맞다.                                                                        */
let tests = 0, fails = 0;
const ok = (c, n, x) => { tests++; if (!c) { fails++; console.log("  [실패] " + n + (x ? "  " + x : "")); }
                          else console.log("  [통과] " + n + (x ? "  " + x : "")); };
ok(worst < 1e-6, "A. toImg ↔ draw 역변환 오차가 1e-6 이미지px 미만", "최대 " + worst);
ok(worstZoom < 1e-6, "B. 휠 확대 뒤 커서 밑 좌표가 1e-6 이미지px 미만으로 움직인다", "최대 " + worstZoom);
/* C. 「화면 1px 씩 100회 드래그」 로 상자가 실제로 간 거리 — 2026-09-19 23:4x 실측값을 굳힌다.
   ⚠ 이 표는 «맞는 값» 이 아니라 «지금 값» 이다. 배율 2x 에서 상자는 마우스(50px)의 **두 배**인
   100px 을 가고, 3x·5x·30x 에서는 **아예 움직이지 않는다** — 매 사건마다 `Math.round` 를 하므로
   0.5px 은 1px 로 올라가고 0.33px 은 0 으로 내려간다. 구조 정리는 동작을 바꾸지 않는 작업이니
   이 값이 달라지면 **실패**로 잡아야 한다. 「고칠 것」 목록에 올릴 결함이고, 고치는 사이클이
   이 표를 새 값으로 갈아 끼우면서 «왜 바꿨나» 를 여기 적는다. */
const MOVE_EXPECT = { "0.25": 400, "0.5": 200, "1": 100, "2": 100, "3": 0, "5": 0, "30": 0 };
for (const s of [0.25, 0.5, 1, 2, 3, 5, 30]) {
  const r = simMove(s, 1, 100);
  ok(r.moved === MOVE_EXPECT[String(s)],
     `C. 배율 ${s}x — 상자가 간 거리 ${r.moved}px (기준선 ${MOVE_EXPECT[String(s)]}px · 마우스 ${r.should.toFixed(2)}px)`);
}
console.log(`\n합계: ${tests}개 중 ${tests - fails}개 통과, ${fails}개 실패`);
process.exit(fails ? 1 : 0);
