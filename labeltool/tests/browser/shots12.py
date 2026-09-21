# -*- coding: utf-8 -*-
"""화면 12장을 늘 **같은 순서·같은 자리**로 찍고, 두 벌을 화소로 대조하는 자(3단계 디자인용).
작성: 2026-09-21

왜 따로 만드나
  3단계(G1~G7)는 `style.css` 의 색·테두리·반지름을 손댄다. «바뀌면 안 되는 곳이 안 바뀌었나» 를
  사람 눈으로만 보면 한 화소짜리 어긋남을 놓친다. 고치기 **전**에 한 벌, **뒤**에 한 벌을 찍어
  칸마다 다른 화소 수를 세면 «의도한 데만 바뀌었다» 를 숫자로 말할 수 있다.
  G1 은 선언만 더하므로 **열두 장이 모두 0화소 차이**여야 한다.

  이름을 `b*.py` 로 안 붙인 까닭 — `run_all.sh` 의 브라우저 묶음은 이름을 적어 부르지만(b1·t2),
  단위는 `u*.py` 를 글롭한다. 자(自)는 시험이 아니라 **도구**라 묶음 표에 줄을 만들지 않는다.

쓰는 법
    python3 tests/browser/shots12.py take  before     # ~/ff_shots/tests_260920/design12/before/
    python3 tests/browser/shots12.py take  after
    python3 tests/browser/shots12.py diff  before after

지키는 것
  모래상자 서버에만 붙는다(빈 포트를 스스로 찾는다). 실서버 5111 · 교수님 5100·5101·5105 에는
  붙지도 끄지도 않는다. 원본 데이터는 읽기만 한다.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402
from PIL import Image, ImageChops                        # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_shots12")
ROOT = os.path.join(L.SHOTS, "design12")
FRUIT = "peach"
STEM = "210629-t1-01"
F1 = ""                                        # WebDriver 의 F1 · Esc (b16 과 같은 값)
ESC = ""


def _open(b, w):
    """로그인한 브라우저로 과일을 고르고 목록이 찰 때까지 기다린다."""
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
         "s.dispatchEvent(new Event('change'))", FRUIT)
    b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
    L.close_tour(b)
    time.sleep(1.2)                 # 카드 그림이 다 뜰 때까지 (안 기다리면 판마다 다르게 찍힌다)


def take(name):
    out = os.path.join(ROOT, name)
    os.makedirs(out, exist_ok=True)
    L.sync(SB)
    L.reset_status(SB)
    port = L.free_port(5661)
    p = L.start(port=port, sb=SB)
    base = "http://127.0.0.1:%d" % port
    b = None
    try:
        # ── 넓은 창(1366) — 열 장 ────────────────────────────────────────
        b = L.browser(w=1366, h=768, base=base)
        _open(b, 1366)
        b.shot(os.path.join(out, "01_list_easy.png"))

        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.8)
        b.shot(os.path.join(out, "02_list_adv.png"))

        b.open_photo(FRUIT, STEM)
        time.sleep(1.2)
        b.shot(os.path.join(out, "03_edit_adv.png"))

        b.key("x")                                   # ② 상자 그리기
        time.sleep(0.8)
        b.shot(os.path.join(out, "04_box_adv.png"))
        b.key("x")
        time.sleep(0.6)

        if L.ev(b, "!!S.inst"):
            b.key("k")                               # ③ 열매 번호
            time.sleep(0.9)
            b.shot(os.path.join(out, "05_num_adv.png"))
            b.key("k")
            time.sleep(0.6)
        else:                                        # 번호본이 없는 사진이면 빈 칸을 남기지 않는다
            b.shot(os.path.join(out, "05_num_adv.png"))

        b.js("document.querySelector('#easytgl').click();")
        time.sleep(0.9)
        b.shot(os.path.join(out, "06_edit_easy.png"))

        b.key("x")
        time.sleep(0.8)
        b.shot(os.path.join(out, "07_box_easy.png"))
        b.key("x")
        time.sleep(0.6)

        b.key(F1)                                    # 단축키 한 장 겹창 (U7)
        time.sleep(0.6)
        b.shot(os.path.join(out, "08_keyhelp.png"))
        b.key(ESC)
        time.sleep(0.5)

        b.js("document.querySelector('.tab[data-view=\"dash\"]').click();")
        b.wait("return document.querySelector('#dash').textContent.length>100", 30)
        time.sleep(0.8)
        # 현황 탭 머리말의 «언제 만든 표인가»(#dashtime · 서버가 준 시각)는 판마다 달라진다.
        #   실측 — 그대로 찍으면 두 판이 105화소 어긋나고, 그 자리는 (176,58)~(200,67) 로
        #   초 단위 두 글자다. 자가 흔들리면 «안 바뀌었다» 를 말할 수 없으므로 글자 수가
        #   같은 가짜 시각으로 덮는다(앱 코드가 아니라 화면의 그 칸 하나만).
        b.js("const t=document.querySelector('#dashtime'); if(t) t.textContent='0000-00-00 00:00:00';")
        time.sleep(0.3)
        b.shot(os.path.join(out, "09_dash.png"))

        b.js("document.querySelector('.tab[data-view=\"exp\"]').click();")
        time.sleep(1.0)
        b.shot(os.path.join(out, "10_export.png"))

        L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
        b.close()
        b = None

        # ── 좁은 창 1200 · 휴대폰 폭 390 — 두 장 ─────────────────────────
        #   ⚠ 390 을 청해도 이 파이어폭스는 **500** 아래로는 안 줄어든다(찍힌 그림의 폭을
        #     실측했다). 이름은 앞 라운드들과 맞춰 두지만 실제 폭은 500 이다 — U7 이 같은 것을
        #     재서 고쳐 적었다. 진짜 휴대폰 한 바퀴는 사람이 해야 한다(plan.md 맨 아래).
        for w, tag in [(1200, "11_narrow_1200"), (390, "12_phone_390")]:
            b = L.browser(w=w, h=780, base=base)
            _open(b, w)
            b.open_photo(FRUIT, STEM)
            time.sleep(1.4)
            b.shot(os.path.join(out, tag + ".png"))
            L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
            b.close()
            b = None
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
        L.stop(p)
    png = sorted(x for x in os.listdir(out) if x.endswith(".png"))
    print("화면 %d장 — %s" % (len(png), out))
    for x in png:
        print("   ", x)
    return 0 if len(png) == 12 else 1


def diff(a, b):
    """두 벌을 화소로 대조한다. 다른 화소가 하나라도 있으면 rc=1.

    **바뀐 자리**(getbbox — 왼쪽·위·오른쪽·아래)도 같이 적는다. G1 은 «0화소» 로 끝났지만
    G2 부터는 화면이 **일부러** 바뀐다 — 그때 물어야 할 것은 «0인가» 가 아니라
    «바뀐 자리가 내가 손댄 그 칸뿐인가» 다(예: G2 는 상단 바라 아래쪽 y 가 바 높이 안이어야 한다).
    """
    pa, pb = os.path.join(ROOT, a), os.path.join(ROOT, b)
    names = sorted(set(os.listdir(pa)) | set(os.listdir(pb)))
    names = [x for x in names if x.endswith(".png")]
    bad = 0
    print("%-22s %10s %10s %12s   %s" % ("화면", a, b, "다른 화소", "바뀐 자리 (좌,위,우,아래)"))
    print("─" * 88)
    for n in names:
        fa, fb = os.path.join(pa, n), os.path.join(pb, n)
        if not (os.path.exists(fa) and os.path.exists(fb)):
            print("%-22s %10s %10s %12s" % (n, os.path.exists(fa), os.path.exists(fb), "없음"))
            bad += 1
            continue
        ia = Image.open(fa).convert("RGB")
        ib = Image.open(fb).convert("RGB")
        if ia.size != ib.size:
            print("%-22s %10s %10s %12s" % (n, ia.size, ib.size, "크기 다름"))
            bad += 1
            continue
        d = ImageChops.difference(ia, ib).convert("L")
        n_diff = sum(1 for v in d.getdata() if v)
        print("%-22s %10s %10s %12d   %s" % (n, ia.size[0], ib.size[0], n_diff, d.getbbox() or "-"))
        if n_diff:
            bad += 1
    print("─" * 88)
    print("다른 칸 %d / %d" % (bad, len(names)))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "take":
        sys.exit(take(sys.argv[2]))
    if len(sys.argv) >= 4 and sys.argv[1] == "diff":
        sys.exit(diff(sys.argv[2], sys.argv[3]))
    print(__doc__)
    sys.exit(2)
