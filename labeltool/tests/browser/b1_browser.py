# -*- coding: utf-8 -*-
"""사이클4 1차 — **진짜 파이어폭스** 회귀 (1366×768).  작성: 2026-09-19

보는 것 (지시 9):
  네 과일 × (상자 / 번호 / 개수 칸) × (`/` 편집 화면 · `/box` 전용 화면)
    · 초벌 **출처 표시**가 서버가 준 `seed_source` 와 같은 말인가 (지어내지 않는가)
    · 상자 저장 → 확정 → **개수 칸이 그 자리에서 초록**으로 바뀌는가
    · 번호 확정 → 개수 출처가 «번호 확정» 으로 바뀌는가
    · 옛 서버(5342)에 **새 화면**을 붙이면 조용히 옛 표시로 물러서는가(지어내지 않는가)
모래상자는 **내 폴더**(cycle_4/stage1/sandbox·sandbox_old) · 포트 5361·5362 · 스크린샷 ~/ff_shots/cnt4b.
실서버 5111 과 교수님 5100·5101·5105 에는 **붙지 않는다**.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sandbox as M                                # tests/lib/sandbox.py
L = M.L
OUT = {}
FRUITS = ["peach", "grape", "apple", "blueberry"]
# 과일마다 «이 사진» 하나를 고정한다(찾기 쉽고 초벌 출처가 과일마다 다른 것을 보이게)
# 과일마다 사진 하나를 **이름으로** 고정한다. 블루베리도 이름을 준다 — 이름 없이 «목록 첫 장» 을
# 기다리면 1,195장 목록이 30초 안에 안 떠서 시간 초과가 났다(2026-09-19 19:36 실측).
STEM = {"peach": "210629-t1-01", "grape": "0",
        "apple": "20150919_174151_image1", "blueberry": "Camera 1 Video (1)_1"}
# 🔴 2026-09-19 «개수 세기» 사이클4 **2차 검수**: 포도를 다시 껐다(교수님 확인 8번 대기) —
#    그래서 포도의 기대값은 `certh_gt` 가 아니라 **`cc4`**(번호본이 없어 4-연결 폴백)이고
#    ③ 번호 단추도 **잠겨** 있어야 한다. 포도를 켜면 이 두 줄을 옛 값으로 되돌린다.
GRAPE_ON = L.grape_seeded()             # ← `app/instances.py SEED_DIRS` 를 **읽어서** 정한다(손으로 적지 않는다)
WANT = {"peach": "team:박성문", "grape": "certh_gt" if GRAPE_ON else "cc4",
        "apple": "gt_numbers", "blueberry": "team:박성문"}


def chip(b):
    return L.ev(b, "(()=>{const e=document.querySelector('#cnts');"
                   "return e?{t:e.textContent,c:e.className,tip:e.title}:null})()")


def boxinfo(b):
    return L.ev(b, "(document.querySelector('#boxinfo')||{}).textContent||''")


def task(b, name):
    b.js("const x=[...document.querySelectorAll('.task')].find(e=>e.dataset.task===arguments[0]);"
         "if(x && !x.disabled) x.click();", name)
    time.sleep(0.9)


def one_fruit(b, api, fruit, view):
    tag = "%s/%s" % (fruit, view)
    b.open_photo(fruit, STEM[fruit])
    stem = L.ev(b, "S.stem")      # app.js 의 `S` 는 최상위 const 라 전역 객체의 칸이 아니다
    item = api.get("/api/item?fruit=%s&stem=%s" % (fruit, __import__("urllib.parse", fromlist=["x"]).quote(stem)))
    cn = item.get("counts") or {}
    ss = cn.get("seed_source")
    L.chk("%s: 서버 seed_source = %s" % (tag, WANT[fruit]), ss == WANT[fruit], ss)
    L.chk("%s: /api/item 의 옛 n_inst 가 counts.instances 와 같다" % tag,
          item.get("n_inst") == cn.get("instances"), (item.get("n_inst"), cn.get("instances")))
    # ── 개수 칸 (어느 작업에서도 늘 보여야 한다)
    c = chip(b)
    L.chk("%s: 개수 칸이 있다(«?» 가 아니다)" % tag, bool(c) and "?" not in c["t"], c and c["t"])
    L.chk("%s: 풍선말이 서버 출처를 그대로 말한다" % tag,
          bool(c) and ("«✨ 초벌» 이 쓰는 것" in c["tip"]), (c or {}).get("tip", "")[:120])
    L.chk("%s: 풍선말에 옛 «늘 4-연결» 단정이 없다" % tag,
          bool(c) and "센 개수는 4-연결 덩어리 기준" not in c["tip"], (c or {}).get("tip", "")[:120])
    # ── 상자 초벌: 화면이 말하는 출처
    task(b, "box")
    time.sleep(1.2)
    info = boxinfo(b)
    seed = api.get("/api/boxes_seed?fruit=%s&stem=%s&source=team:%%EB%%B0%%95%%EC%%84%%B1%%EB%%AC%%B8"
                   % (fruit, __import__("urllib.parse", fromlist=["x"]).quote(stem)))
    L.chk("%s: 박성문 상자 초벌이 나온다(n>0)" % tag, seed.get("ok") and seed.get("n", 0) > 0, seed.get("n"))
    L.chk("%s: 상자 초벌 seed_source = team:박성문" % tag,
          seed.get("seed_source") == "team:박성문", seed.get("seed_source"))
    nb = L.ev(b, "S.boxes.length")
    L.chk("%s: 화면에 초벌 상자가 깔려 있다" % tag, nb > 0, nb)
    # ⚠ 이 단정은 **모래상자가 깨끗할 때**만 «초벌» 이다. `b2_export.py` 가 먼저 돌면 그 사진에
    #   사람이 저장한 상자가 생겨 «저장된 상자» 가 된다(그것이 규칙이다 — 사람 저장이 늘 우선).
    #   그래서 `runb3_cnt4.sh` 는 **sync → b1 → b2** 순서로 돌린다. 둘 다 정상 문구로 본다.
    L.chk("%s: 화면 회색 줄이 «초벌» 또는 «저장된 상자» 라고 말한다" % tag,
          ("초벌" in info) or ("저장된 상자" in info), info[:90])
    # ── 번호 화면 (번호본이 네 과일 모두 있다 — 사이클4 M1)
    #    `/box` 전용 화면은 마스크·번호 단추를 **숨기는 것이 정상**이라 그 화면에서는 «없음» 을 본다.
    task(b, "num")
    time.sleep(1.0)
    dis = L.ev(b, "(()=>{const x=[...document.querySelectorAll('.task')]"
                  ".find(e=>e.dataset.task==='num');"
                  "return x?(x.offsetParent===null?'숨김':!!x.disabled):null})()")
    if view == "box":
        L.chk("%s: /box 는 ③ 번호 단추를 숨긴다(정상)" % tag, dis in ("숨김", None), dis)
    else:
        want_on = GRAPE_ON or fruit != "grape"
        L.chk("%s: ③ 번호 단추가 %s" % (tag, "켜져 있다(번호본이 있다)" if want_on
                                       else "잠겨 있다(포도는 아직 안 켬 — 교수님 확인 8번)"),
              dis is (False if want_on else True), dis)
    b.shot(os.path.join(M.SHOTS, "b1_%s_%s.png" % (fruit, view)))
    return {"stem": stem, "counts": cn, "seed": {k: seed.get(k) for k in ("n", "source", "seed_source")},
            "chip": c, "boxinfo": info[:120]}


def main():
    p = None
    b = None
    try:
        p = L.start(port=M.PORT, sb=M.SB, pw=M.PW)
        api = L.Api(base="http://127.0.0.1:%d" % M.PORT, pw=M.PW)
        b = L.browser(1366, 768, base="http://127.0.0.1:%d" % M.PORT, pw=M.PW)
        for view in ("/", "/box"):
            if view == "/box":
                b.go("/box")
                b.wait("return !!document.querySelector('#fruit option')", 30)
                L.close_tour(b)
            for fruit in FRUITS:
                OUT["%s|%s" % (fruit, view)] = one_fruit(b, api, fruit, view.strip("/") or "edit")
        # ── 가로 스크롤 · 줄바꿈 (1366×768)
        sc = L.ev(b, "({w:document.documentElement.scrollWidth,c:document.documentElement.clientWidth})")
        L.chk("1366 폭에서 가로 스크롤 없음", sc["w"] <= sc["c"] + 1, sc)
    finally:
        if b:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    json.dump(OUT, open(os.path.join(HERE, "b1_browser.json"), "w"), ensure_ascii=False, indent=1)
    return L.summary("b1_browser")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
