// 휴대폰 판정 단추와 한 손가락 간단 편집·두 손가락 확대 이동을 연결한다.
"use strict";
(function () {
  const phone = matchMedia('(max-width:820px)'), cv = UI.cv, $ = UI.$;
  const hint = document.createElement('p');
  hint.id = 'mobile-hint'; hint.className = 'mobile-only';
  hint.textContent = '두 손가락으로 확대·이동하세요. 상자는 한 손가락으로 그립니다. 번호는 고르거나 크게 칠한 뒤 아래 단추로 적용하세요. 정밀 편집은 PC에서 하세요.';
  $('#view-edit').append(hint);
  const bar = document.createElement('nav');
  bar.id = 'mobile-bar'; bar.className = 'mobile-only'; bar.setAttribute('aria-label', '사진 판정');
  bar.innerHTML = '<button id="mobile-prev">이전</button><button id="mobile-confirm" class="ok">확정</button><button id="mobile-next">다음</button><button id="mobile-undo">되돌림</button>';
  document.body.append(bar);
  for (const id of ['prev', 'confirm', 'next']) $('#mobile-' + id).onclick = () => $(id === 'confirm' ? '#btn-confirm' : '#' + id).click();
  $('#mobile-undo').onclick = () => {
    if (S.numMode && UI.hasPendingRegion()) { UI.numKey({key:'Escape'}); return; }
    $(S.boxMode ? '#boxundo' : S.numMode ? '#numundo' : '#undo').click();
  };
  const actions = document.createElement('div'); actions.id = 'mobile-num-actions'; actions.className = 'mobile-only tools';
  actions.innerHTML = '<button id="mobile-num-delete">고른 번호 삭제</button><button id="mobile-num-add">칠한 번호 붙이기</button>';
  $('#numpanel').append(actions);
  $('#mobile-num-delete').onclick = () => { if (S.numMode) UI.numKey({key:'d'}); };
  $('#mobile-num-add').onclick = () => { if (S.numMode) UI.numKey({key:'n'}); };

  // 좁은 화면의 표는 각 값 옆에 원래 열 이름을 반복해 읽을 수 있게 한다.
  for (const el of [$('#dash'), $('#exp-list')]) {
    new MutationObserver(() => {
      for (const table of el.querySelectorAll('table')) {
        const labels = [...table.rows[0].cells].map(c => c.textContent);
        for (const row of [...table.rows].slice(1)) [...row.cells].forEach((cell,i) => { cell.dataset.label = labels[i] || ''; });
      }
    }).observe(el, {childList:true, subtree:true});
  }
  const resetScroll = () => { if (phone.matches && !$('#view-edit').classList.contains('hidden')) window.scrollTo(0,0); };
  new MutationObserver(resetScroll).observe($('#stemname'), {childList:true});
  new MutationObserver(resetScroll).observe($('#view-edit'), {attributes:true, attributeFilter:['class']});
  let stroke = null, pinch = null, multi = false;
  function cancelStroke() {
    if (stroke === 'box' && S.drag) { S.boxes = JSON.parse(S.drag.before); S.drag = null; UI.boxInfo(); }
    if (stroke === 'num') { UI.clearPending(); S.numBrushing = false; }
    stroke = null; S.dirty = true;
  }
  function pair(t) {
    const r = cv.getBoundingClientRect();
    return {x:(t[0].clientX+t[1].clientX)/2-r.left, y:(t[0].clientY+t[1].clientY)/2-r.top,
      d:Math.max(1,Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY))};
  }
  cv.addEventListener('touchstart', e => {
    if (!phone.matches || !S.img) return;
    e.preventDefault();
    if (e.touches.length >= 2) {
      cancelStroke(); multi = true; pinch = {...pair(e.touches), ...S.view}; return;
    }
    if (multi) return;
    const [x,y] = UI.toImg(e.touches[0]);
    if (S.boxMode) { stroke = 'box'; UI.boxMouseDown({button:0},x,y); }
    else if (S.numMode && ['erase','add'].includes(S.ntool)) {
      // 번호는 큰 붓과 삭제만 제공한다. 정밀 분할·합치기는 PC 도구를 쓴다.
      if (UI.hasPendingRegion()) return;
      stroke = 'num';
      const shape = $('#numshape').value; $('#numshape').value = 'brush';
      UI.numMouseDown({button:0},x,y); $('#numshape').value = shape;
    }
  }, {passive:false});
  cv.addEventListener('touchmove', e => {
    if (!phone.matches || !S.img) return;
    e.preventDefault();
    if (e.touches.length >= 2 && pinch) {
      const p = pair(e.touches), s = Math.max(.03,Math.min(30,pinch.s*p.d/pinch.d));
      S.view = {s, tx:p.x-(pinch.x-pinch.tx)*s/pinch.s, ty:p.y-(pinch.y-pinch.ty)*s/pinch.s};
      S.dirty = true; return;
    }
    if (multi || !stroke || !e.touches.length) return;
    const [x,y] = UI.toImg(e.touches[0]);
    if (stroke === 'box') UI.boxMouseMove(x,y); else UI.numMouseMove(x,y);
  }, {passive:false});
  cv.addEventListener('touchend', e => {
    if (!phone.matches) return;
    e.preventDefault();
    if (!multi && stroke) {
      if (stroke === 'box') UI.boxMouseUp(); else UI.numMouseUp();
      stroke = null;
    }
    if (!e.touches.length) { pinch = null; multi = false; }
  }, {passive:false});
  cv.addEventListener('touchcancel', e => {
    if (!phone.matches) return;
    e.preventDefault(); cancelStroke(); pinch = null; multi = false;
  }, {passive:false});
  // 작은 화면의 마우스 호환 이벤트도 정밀 마스크 편집을 시작하지 못하게 한다.
  cv.addEventListener('mousedown', e => {
    if (phone.matches && !S.boxMode && !S.numMode) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  window.addEventListener('resize', () => {
    if (phone.matches) { cancelStroke(); pinch = null; multi = false; UI.resizeCanvas(); UI.fitView(); }
  });
})();
