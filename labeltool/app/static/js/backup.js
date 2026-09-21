/* backup — 저장 전 작업을 1분마다 브라우저에 임시로 적어 두고, 같은 사진을 다시 열면 되돌려 준다
   작성: 2026-09-21 (260921 편의·안정성 사이클 · S5)

   왜 있나
     S1~S3 은 «서버에 못 닿는 것» 을 막았다. 그래도 남는 구멍이 하나 있다 — **브라우저가 죽는 것**.
     노트북 배터리가 나가거나 파이어폭스가 탭을 떨어뜨리면, 저장 전 붓질 30분이 아무 흔적도 없이
     사라진다(창 닫기 경고 S4 는 «사람이 닫을 때» 만 뜬다). 서버는 저장 전 상태를 모른다.
     → 1분마다 localStorage 에 한 벌 적어 두고, 같은 사진을 다시 열면 «되돌릴까요» 를 묻는다.

   지킨 것
     · **새 주소를 만들지 않았다.** 파이썬을 한 줄도 안 고치므로 실서버(5111) 재시작이 필요 없다.
     · 한 번에 **한 장**만 적어 둔다 — 여러 장을 쌓으면 5MB 자리를 금방 넘겨서, 정작 지금 하는
       일의 백업이 밀려난다. 다른 사진에서 새로 더러워지면 그 사진 것으로 바뀐다.
     · 자리가 없으면(큰 사진 · 다른 탭이 이미 채워 둠) **조용히 포기한다.** 백업은 덤이라서,
       «백업을 못 했습니다» 라는 붉은 알림으로 사람 일을 막는 것이 더 나쁘다.
     · 되돌리기는 **되돌릴 수 있게** 얹는다(마스크는 pushUndo · 상자는 bpush) → Ctrl+Z 로 서버
       값으로 되돌아간다. 저장은 사람이 Ctrl+S 로 한다(자동 저장이 아니다).
     · 서버에서 방금 읽은 것과 백업이 **같으면 묻지 않고 지운다** — 저장한 뒤 그 사진을 다시 열었을
       때 «되돌릴까요» 가 뜨면 사람은 저장이 안 된 줄 안다.

   의존은 «위에서 아래로» — 이 파일이 맨 마지막이라 UI·S 를 그냥 쓴다.
*/
"use strict";

(function () {
const flash = UI.flash;

const KEY = "backup_260921";          // 한 칸만 쓴다(한 장치고 한 장)
const EVERY = 60000;                  // 1분마다
const LIMIT = 2000000;                // 글자 수 상한 — 이보다 크면 적지 않는다(localStorage 는 보통 5MB)

/* ─────────── 배열을 «같은 값이 몇 번» 으로 접어 글자로 (마스크 2백만 칸 → 보통 수십 KB) ─────────── */
/* 실측(1080×1920 사진 한 장, 둥근 덩어리): 14,501글자 · 8ms.
   **잘게 엇갈린 것은 접어도 안 줄어든다** — 한 칸씩 0/1 이 엇갈리는 300만 칸을 끝까지 세면 1.2초가
   걸렸다(실측). 1분마다 화면이 1.2초 멈추면 붓질이 끊긴다 → 토막이 이만큼 많아지면 **세다 말고
   포기한다**(null). 백업은 덤이라서, 못 하는 것보다 일을 막는 것이 더 나쁘다. */
const MAXRUNS = 300000;
function packRuns(a) {
  const out = [];
  let v = a[0], n = 1;
  for (let i = 1; i < a.length; i++) {
    if (a[i] === v) { n++; continue; }
    out.push(v, n);
    if (out.length > MAXRUNS * 2) return null;
    v = a[i]; n = 1;
  }
  out.push(v, n);
  return out.join(",");
}
/* 되돌리기. 길이가 안 맞으면 **null** — 반쯤 채운 배열을 화면에 올리지 않는다. */
function unpackRuns(s, len, Arr) {
  const p = String(s || "").split(",");
  const out = new Arr(len);
  let i = 0;
  for (let k = 0; k + 1 < p.length; k += 2) {
    const v = +p[k], n = +p[k + 1];
    if (!(n > 0) || i + n > len) return null;
    if (v) out.fill(v, i, i + n);
    i += n;
  }
  return i === len ? out : null;
}

/* 상자는 서버가 저장할 때 번호(id)를 1부터 다시 붙인다 → «같은 상자인가» 는 종류+좌표로 본다. */
function boxSig(arr) {
  return (arr || []).map((b) => (b.cls || "") + ":"
    + ((b.xyxy || []).map((n) => Math.round(n)).join(","))).join("|");
}

function read() {
  try {
    const o = JSON.parse(localStorage.getItem(KEY) || "null");
    return (o && o.v === 1) ? o : null;
  } catch (e) { return null; }
}
function drop() { try { localStorage.removeItem(KEY); } catch (e) {} }

/* ─────────── 1분마다: 저장 안 한 것이 있으면 적고, 없으면 지운다 ─────────── */
function snap() {
  if (!S.stem) return null;
  const o = { v: 1, fruit: S.fruit, stem: S.stem, W: S.W, H: S.H, at: Date.now() };
  let any = false;
  if (S.edDirty && S.ed) { const p = packRuns(S.ed); if (p !== null) { o.ed = p; any = true; } }
  if (S.bDirty && S.boxes) { o.boxes = S.boxes; any = true; }
  if (S.numDirty && S.inst) { const p = packRuns(S.inst); if (p !== null) { o.inst = p; any = true; } }
  return any ? o : null;
}

/* 돌려주는 값 = 적은 글자 수(못 적었으면 0). 시험이 1분을 기다리지 않게 UI.backupNow 로 내놓는다. */
function backupNow() {
  const o = snap();
  if (!o) { drop(); return 0; }                    // 저장할 것이 없다 = 지난 백업도 쓸모가 없다
  let s;
  try { s = JSON.stringify(o); } catch (e) { return 0; }
  if (s.length > LIMIT) { drop(); return 0; }      // 너무 크다 — 조용히 포기한다
  try { localStorage.setItem(KEY, s); } catch (e) { drop(); return 0; }   // 자리가 없다 — 조용히 포기
  return s.length;
}

/* ─────────── 사진을 열 때: 되돌릴 것이 있으면 묻는다 ─────────── */
function stampKo(ms) {
  const d = new Date(ms), p = (n) => (n < 10 ? "0" : "") + n;
  return `${d.getMonth() + 1}월 ${d.getDate()}일 ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function apply(o) {
  const done = [];
  if (o.ed !== undefined && S.ed) {
    const bits = unpackRuns(o.ed, S.W * S.H, Uint8Array);
    if (bits) { UI.pushUndo(); UI.applyBits(bits); done.push("칠한 영역"); }
  }
  if (o.boxes !== undefined && Array.isArray(o.boxes)) {
    UI.bpush();                                    // Ctrl+Z 로 서버 상자로 돌아갈 수 있게(bDirty 도 켜진다)
    S.boxes = o.boxes; S.bsel = -1;
    UI.boxInfo(`임시 백업에서 되돌린 상자 ${o.boxes.length}개 — 아직 저장 전입니다`);
    done.push("상자");
  }
  if (o.inst !== undefined && S.inst) {
    const arr = unpackRuns(o.inst, S.W * S.H, Uint16Array);
    if (arr) { S.inst = arr; S.numDirty = true; UI.repaintNum(); done.push("번호"); }
  }
  S.dirty = true;
  return done;
}

/* `ready` = 상자·번호 불러오기가 끝났다는 약속. **그것을 기다린 뒤** 물어야 한다 —
   먼저 되돌리면 뒤늦게 끝난 loadBoxes()·loadInstances() 가 서버 값으로 덮어쓴다. */
async function backupOffer(ready) {
  const o = read();
  if (!o || o.fruit !== S.fruit || o.stem !== S.stem) return false;   // 다른 사진 것은 그대로 둔다
  if (ready) { try { await ready; } catch (e) {} }
  if (o.stem !== S.stem) return false;                               // 기다리는 사이 사진이 바뀌었다
  if (o.W !== S.W || o.H !== S.H) { drop(); return false; }           // 사진이 바뀌었다 — 못 믿는다

  // 서버에서 방금 읽은 것과 똑같으면 되돌릴 것이 없다(저장한 뒤 다시 열었을 때)
  const same = (o.ed === undefined || (S.ed && packRuns(S.ed) === o.ed))
            && (o.inst === undefined || (S.inst && packRuns(S.inst) === o.inst))
            && (o.boxes === undefined || boxSig(S.boxes) === boxSig(o.boxes));
  if (same) { drop(); return false; }

  const what = [o.ed !== undefined && "칠한 영역", o.boxes !== undefined && "상자",
                o.inst !== undefined && "번호"].filter(Boolean).join(" · ");
  if (!confirm("이 사진에 «저장하지 않은 작업» 이 남아 있습니다.\n"
    + `(${stampKo(o.at)} 에 이 브라우저가 임시로 적어 둔 것 — ${what})\n\n`
    + "되돌릴까요?\n"
    + "«확인» = 그때 하던 것으로 되돌립니다(되돌린 뒤 Ctrl+S 로 저장하세요. Ctrl+Z 로 취소).\n"
    + "«취소» = 서버에 저장된 것을 그대로 씁니다(임시 기록은 지웁니다).")) {
    drop();                                        // 한 번 거절한 것을 다시 묻지 않는다
    return false;
  }
  const done = apply(o);
  if (!done.length) { drop(); return false; }
  flash(`임시 백업에서 ${done.join(" · ")} 을 되돌렸습니다 — 확인하고 Ctrl+S 로 저장하세요`);
  return true;
}

setInterval(backupNow, EVERY);


/* ── 이 파일이 내놓는 것 (list.js 의 openItem 과 시험이 쓴다) ── */
Object.assign(UI, { backupNow, backupOffer, backupPack: packRuns, backupUnpack: unpackRuns });
})();
