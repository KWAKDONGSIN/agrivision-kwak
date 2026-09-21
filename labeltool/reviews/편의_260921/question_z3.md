# 검토 요청 — 웹 라벨링 툴의 «편의·안정성» 개선분에서 빠진 것과 위험

당신은 웹 프런트엔드(순수 JS·CSS, 프레임워크 없음)와 «사람이 실제로 쓰는 도구»의
신뢰성을 보는 검토자다. 파일을 읽을 수 없으니 아래 붙인 내용만 보고 답하라.

## 맥락
- 대학 연구실의 과일 사진 라벨링(주석) 웹 도구다. 학부생 5~6명이 하루 몇 시간씩 쓴다.
- 화면은 하나다 — 위 줄(파일 이름·저장 단추), 왼쪽 도구상자(붓·지우개·다각형·자동채움·이동),
  가운데 캔버스(사진 위에 마스크를 칠한다), 오른쪽 패널, 아래 판정 줄.
- 세 가지를 저장한다 — ① 칠한 영역(마스크, Uint8Array W×H) ② 상자(bounding box 배열)
  ③ 번호(인스턴스 id, Uint16Array W×H). 각각 `edDirty`·`bDirty`·`numDirty` 깃발이 있다.
- 서버는 파이썬(Flask 류)이고 **재시작하면 안 된다**(사람이 쓰는 중). 그래서 이번 작업은
  정적 파일(html·css·js)만 고쳤다. 새 라이브러리·CDN·빌드 도구를 못 쓴다.
- 기존 회귀 시험 1,358개 + 진짜 파이어폭스 시험 24벌이 있고 전부 통과했다.

## 2026-09-21 하루에 넣은 것 (한 줄씩)
안정성
- S1 `fetch` 가 서버에 닿지도 못하면(와이파이 끊김·서버 재시작) 지금까지 조용히 씹혔다 →
  `.catch` 로 다른 오류와 **같은 모양** `{ok:false,error:"…"}` 을 돌려준다.
- S2 실패 알림이 3초 뒤 사라지던 것을 → «확인» 을 눌러야 지워지게. 성공은 3초 그대로.
- S3 30초마다 `/api/health` 를 두드려 안 닿으면 화면 맨 위에 붉은 띠. 닿으면 저절로 사라짐.
  끊긴 뒤에는 5초마다 본다.
- S4 창 닫기 경고가 세 깃발을 다 보는지 확인 — 이미 보고 있었다(코드 안 고침).
- S5 1분마다 localStorage 에 저장 전 작업을 한 벌 적어 두고, 같은 사진을 다시 열면
  «되돌릴까요» 를 묻는다(자동 저장이 아니다).
- S6 저장 중 그 단추를 잠가 이중 저장을 막는다. 전에는 잠금이 하나도 없었다.

편의(그림판·포토샵·윈도우 관습)
- U1 저장 안 된 상태면 파일 이름 옆에 «*» + 저장 단추에 노란 테두리(0.2초마다 깃발을 본다)
- U2 배율 %를 확대바에 늘 표시 · U3 상자 «다시하기» Ctrl+Y · U4 캔버스 더블클릭 = 화면 맞춤
- U5 도구별 커서 · U6 고른 도구를 «눌린» 모양으로 · U7 F1 단축키 한 장 표(겹창)
- U8 붓/지우개 굵기를 따로 기억 · U9 `~` 키를 누르는 동안만 원본만 보기
- U10 상자 모드 십자 안내선

디자인
- G1~G7 색 133가지를 CSS 토큰 계단으로 접고, `:focus-visible` 키보드 테두리를 넣고,
  숫자 칸을 `min-width:…ch` 로 고정해 흔들림을 없앴다.

## 핵심 새 코드 (요점만)

### S6 — 저장 잠금
```js
function lockWhile(sels, fn) {
  let busy = false;
  return async function () {
    if (busy) return;                     // 이미 도는 중 — 두 번째 누름은 버린다
    busy = true;
    const els = (sels || []).map((s) => $(s)).filter(Boolean);
    els.forEach((e) => e.classList.add("saving"));   // css: pointer-events:none; opacity
    try { return await fn.apply(this, arguments); }
    finally { busy = false; els.forEach((e) => e.classList.remove("saving")); }
  };
}
// 네 자리에서 감쌌다: 판정 단추 다섯 + Enter · 상자 저장 · 번호 저장
// `disabled` 를 안 쓴 까닭 — 다른 규칙이 이미 disabled 를 켰다 껐다 해서 되돌릴 값이 없다.
```

### S1+S3 — 네트워크
```js
function api(url, opt) {
  return fetch(url, opt).then(async (r) => {
    setNet(true);
    if (r.status === 401) { location.href = "/login?next=…"; return null; }
    const t = await r.text();
    let j = null;
    try { j = JSON.parse(t); } catch (e) { j = { ok:false, error:"서버가 예상 밖의 답을…" }; }
    if (!r.ok && j && j.error === undefined) j.error = "서버 오류 " + r.status;
    return j;
  }).catch(() => {
    setNet(false); netSchedule();
    return { ok:false, error:"서버에 닿지 못했습니다. … (한 일은 그대로 남아 있습니다)" };
  });
}
const NET_EVERY = 30000, NET_EVERY_DOWN = 5000;
let netDown = false, netTimer = null, netBusy = false;
function netProbe() {
  if (netBusy) return Promise.resolve(!netDown);
  netBusy = true;
  return fetch("/api/health", { cache:"no-store" }).then(() => true, () => false)
    .then((ok) => { netBusy = false; setNet(ok); netSchedule(); return ok; });
}
function netSchedule() { clearTimeout(netTimer); netTimer = setTimeout(netProbe, netDown ? 5000 : 30000); }
netSchedule();   // 파일을 읽는 순간 감시가 시작된다
// 붉은 띠는 document.body.firstChild 로 끼워 넣어 아래를 32px 밀어 내린다(겹치지 않게).
```

### S5 — 임시 백업 (localStorage)
```js
const KEY = "backup_260921";   // 칸 하나만 쓴다 — 한 번에 한 장
const EVERY = 60000;           // 1분마다
const LIMIT = 2000000;         // 글자 수 상한(localStorage 는 보통 5MB)
const MAXRUNS = 300000;        // 런렝스로 접다가 토막이 이보다 많으면 null 로 포기(1.2초 멈춤 방지)

function snap() {              // 더러운 것만 담는다
  if (!S.stem) return null;
  const o = { v:1, fruit:S.fruit, stem:S.stem, W:S.W, H:S.H, at:Date.now() };
  let any = false;
  if (S.edDirty && S.ed)  { const p = packRuns(S.ed);   if (p !== null) { o.ed = p; any = true; } }
  if (S.bDirty && S.boxes) { o.boxes = S.boxes; any = true; }
  if (S.numDirty && S.inst){ const p = packRuns(S.inst); if (p !== null) { o.inst = p; any = true; } }
  return any ? o : null;
}
function backupNow() {
  const o = snap();
  if (!o) { drop(); return 0; }                  // 저장할 것이 없다 = 지난 백업도 쓸모없다
  let s; try { s = JSON.stringify(o); } catch (e) { return 0; }
  if (s.length > LIMIT) { drop(); return 0; }    // 너무 크다 — 조용히 포기
  try { localStorage.setItem(KEY, s); } catch (e) { drop(); return 0; }   // 자리 없다 — 조용히 포기
  return s.length;
}
setInterval(backupNow, EVERY);

async function backupOffer(ready) {              // 사진을 열 때 부른다
  const o = read();
  if (!o || o.fruit !== S.fruit || o.stem !== S.stem) return false;
  if (ready) { try { await ready; } catch (e) {} }   // 상자·번호 불러오기를 기다린 뒤에 묻는다
  if (o.stem !== S.stem) return false;
  if (o.W !== S.W || o.H !== S.H) { drop(); return false; }
  // 서버에서 방금 읽은 것과 같으면 묻지 않고 지운다(저장한 뒤 다시 열었을 때)
  const same = …;
  if (same) { drop(); return false; }
  if (!confirm("«저장하지 않은 작업» 이 남아 있습니다 … 되돌릴까요?")) { drop(); return false; }
  apply(o);   // 마스크는 pushUndo 뒤에 · 상자는 bpush 뒤에 얹어 Ctrl+Z 로 되돌릴 수 있다
}
```

### U1 — 저장 안 됨 표시
```js
const EVERY = 200;   // 0.2초마다 세 깃발을 본다(깃발을 올리는 자리가 40군데가 넘어 한 곳으로 모았다)
let last = "";
function dirtyMark() {
  const on = MARK.filter((m) => !!S[m[0]]);
  const key = on.map((m) => m[0]).join(",");
  if (key === last) return;      // 바뀐 게 없으면 화면을 안 건드린다
  last = key;
  // 저장 단추에 .unsaved 를 켜고, #stemname 옆 형제 <span id="dirtystar">*</span> 를 켠다
}
setInterval(dirtyMark, EVERY);
```

## 물어보는 것
1. **위험** — 이 코드가 실제 사용자에게 **데이터를 잃게 하거나 도구를 멈추게 할** 수 있는
   구체적인 경로가 있나? 있다면 «어떤 상황 → 무슨 일» 로 적어라. 심각한 것부터.
2. **빠진 것** — 「안정성」이라 부르면서 아직 안 막은 흔한 사고가 있나?
   (여러 탭 · 여러 사람이 같은 사진 · 새로고침 · 모바일 · 오래 켜 둔 탭 등)
3. 위 1·2 중 **정적 파일만 고쳐서**(파이썬·서버 재시작 없이) 막을 수 있는 것은 어느 것인가.
4. 반대로 **과하게 만든 것**, 즉 빼는 편이 나은 것이 있나?

결론을 먼저, 근거를 뒤에. 동의하지 않는 점은 분명히 말할 것.
추측이면 «추측» 이라고 표시하라. 파일을 읽으려 하지 마라(읽을 파일이 없다).
