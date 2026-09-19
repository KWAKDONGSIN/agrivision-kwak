/* 이동됨 — 이 파일의 내용(2,664줄)은 2026-09-20 «구조 정리 사이클 3» 에서 역할별 12파일로 나뉘었습니다.
   → /static/js/{state,api,view,mask,boxes,instances,counts,list,export,tour,keys,main}.js
     어느 기능이 어디로 갔는지는 각 파일 머리 주석(«옮겨 온 곳: app.js NNN-NNN줄»)에 적혀 있습니다.
     쪼개기 전 원본은 cycles/260920_structure/cycle_3/stage1/before/app.js 에 그대로 있습니다.

   ⚠ 이 파일을 지우지 않고 남겨 둔 까닭 — «옛 index.html 을 캐시에서 쓰는 브라우저» 때문입니다.
     정적 파일은 서버를 다시 켜지 않아도 바로 나가므로, 이미 툴을 열어 둔 사람의 브라우저가
     새로고침(Ctrl+F5) 전에 옛 index.html 로 이 파일을 부를 수 있습니다. 그때 이 파일이 빈 파일이면
     화면이 통째로 죽습니다. 그래서 아래 세 줄이 **새 파일들을 대신 불러 줍니다**(순서 그대로).
     새 index.html 로 들어온 사람은 이 파일을 아예 부르지 않으므로 두 번 실리는 일은 없습니다.
     모두가 한 번씩 새로고침한 뒤(며칠 뒤) 이 다리는 지워도 됩니다. */
"use strict";
if (document.readyState === "loading") {            // 문서를 읽는 중일 때만(그 밖에는 아무 일도 안 한다)
  ["state", "api", "view", "mask", "boxes", "instances", "counts", "list", "export", "tour",
   "keys", "main"].forEach(function (n) {
    document.write('<script src="/static/js/' + n + '.js"><\/script>');
  });
}
