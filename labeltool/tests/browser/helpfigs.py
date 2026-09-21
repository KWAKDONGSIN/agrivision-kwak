# -*- coding: utf-8 -*-
"""사용법 두 문서(`help.html`·`how_to.html`)에 실린 **화면 사진 열일곱 장**을 지금 화면으로 다시 찍는 자.
작성: 2026-09-21

왜 있나
  그 사진들은 2026-09-18~20 에 찍은 것이라 U1~U10·G1~G6 이 바꾼 지금 화면과 다르다
  (실측 — 열일곱 장 모두 맨 윗줄이 옛 파랑회색 `rgb(34,48,63)` 이고 지금은 `rgb(28,28,28)` 이다).
  help.html 의 figcaption 두 곳은 이미 «⚠️ 이 그림은 재배치 전 화면입니다» 라고 적고 있었다.

  한 장씩 손으로 찍으면 다음에 또 낡는다 → **어떤 사진·어떤 상태인지를 코드에 적어 둔다.**
  캡션에 적힌 사진 이름·창 크기를 그대로 따르므로 캡션과 그림이 어긋날 길이 없다.

쓰는 법
    python3 tests/browser/helpfigs.py take            # ~/ff_shots/tests_260920/helpfigs/
    python3 tests/browser/helpfigs.py take easy,box   # 그 이름이 든 창 묶음만

지키는 것
  모래상자 서버에만 붙는다(빈 포트를 스스로 찾는다). 실서버 5111 · 교수님 5100·5101·5105 에는
  붙지도 끄지도 않는다. 원본 데이터와 팀원 폴더는 **읽기만** 한다.
  ⚠ 마지막 묶음(how_to)은 사용법 글이 «저장 → 다 했어요» 를 설명하므로 **모래상자에서만**
    저장·확정을 누른다. `take()` 가 시작할 때마다 `sync`·`reset_status` 로 되돌리므로 남지 않는다.
"""
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lib"))
import sandbox as L                                      # noqa: E402

SB = os.path.join(L.SB_ROOT, "sb_helpfigs")
#   ⚠ shots12 와 **모래상자를 같이 쓰면 안 된다.** 아래 `copy_counts_cache()` 가 센 열매 수를
#     넣는데 `L.sync()` 는 `cache` 를 지우지도 덮지도 않는다(--exclude) → 그 값이 남아
#     shots12 의 화면 12장이 «개수»·«현황 표»·«카드 번호» 에서 달라진다(실측 — 열 장이 어긋났다).
OUT = os.path.join(L.SHOTS, "helpfigs")

# 캡션에 적힌 사진 — 바꾸려면 help.html 의 figcaption 도 같이 고친다
GRAPE = "1027"                       # 쉬움·전문가 («포도 1027 · 1400×860»)
APPLE_EDIT = "20150921_132038_image1"        # 편집 화면 (캡션에 이름이 적혀 있다)
APPLE_DUP = "20150919_174151_image1"         # 오른쪽 칸 — 중복 묶음이 있는 사과
APPLE_ERR = "20150919_174151_image201"       # 후보 자리로 확대 — 메모에 후보 좌표가 적힌 사과
#   ↑ 이 사진이라야 한다. «🔍 후보 자리로 확대» 는 «라벨 안 된 열매 후보» 메모
#     (`x1,y1,x2,y2: …`)가 있을 때만 나온다 — 박성문 팀 CSV 의 «번호 오류» 는 빨간 상자라
#     다른 말(«＃ 번호에서 고치기»)이 뜨고 🔍 가 안 생긴다(counts.js 의 갈래 순서).


def _fruit(b, fruit):
    b.js("const s=document.querySelector('#fruit');s.value=arguments[0];"
         "s.dispatchEvent(new Event('change'))", fruit)
    b.wait("return document.querySelectorAll('#grid .card').length>0", 60)
    L.close_tour(b)
    time.sleep(1.5)                  # 카드 그림이 다 뜰 때까지


def _easy(b, on):
    """쉬움 모드를 켜거나 끈다(지금 상태를 읽고 **다를 때만** 누른다)."""
    if bool(L.ev(b, "document.body.classList.contains('easy')")) != on:
        b.js("document.querySelector('#easytgl').click();")
        time.sleep(1.0)


def _side(b, on):
    if bool(L.ev(b, "!document.querySelector('#side').classList.contains('fold')")) != on:
        b.js("document.querySelector('#sidetgl').click();")
        time.sleep(0.8)


def shot(b, name):
    p = os.path.join(OUT, name + ".png")
    b.shot(p)
    print("   %-10s %s" % (name, p))


# ── 한 장씩 ────────────────────────────────────────────────────────────
def fig_easy(b):            # 쉬움 모드 편집 화면 (1400×860)
    _fruit(b, "grape")
    _easy(b, True)
    b.open_photo("grape", GRAPE)
    time.sleep(1.5)
    shot(b, "easy")


def fig_expert(b):          # 같은 사진, 전문가 모드 (1400×860)
    _easy(b, False)
    time.sleep(1.2)
    shot(b, "expert")


def fig_edit(b):            # 편집 화면 — 오른쪽 칸은 접힌 채
    _fruit(b, "apple")
    _easy(b, False)
    b.open_photo("apple", APPLE_EDIT)
    _side(b, False)
    time.sleep(1.5)
    shot(b, "edit")


def fig_box(b):             # ▭ 상자 그리기
    b.key("x")
    time.sleep(1.2)
    shot(b, "box")
    b.key("x")
    time.sleep(0.8)


def fig_side(b):            # 오른쪽 칸을 편 모습 — 중복 묶음이 있는 사과
    b.open_photo("apple", APPLE_DUP)
    _side(b, True)
    time.sleep(1.5)
    shot(b, "side")
    _side(b, False)


def fig_notezoom(b):        # «후보 자리로 확대» — 노란 점선이 가운데 크게
    b.open_photo("apple", APPLE_ERR)
    time.sleep(2.0)
    shot(b, "notezoom")


def fig_list(b):            # 사진 목록 — 카드가 가득 찬 모습
    b.js("document.querySelector('.tab[data-view=\"list\"]').click();")
    time.sleep(1.0)
    # 앞 장이 검색 칸에 사진 이름을 남겨 두면 카드가 한 장만 보인다 → «✕ 조건 지우기» 로 지운다
    b.js("document.querySelector('.qf[data-qf=\"all\"]').click();")
    b.wait("return document.querySelectorAll('#grid .card').length>10", 60)
    time.sleep(2.5)                  # 카드 그림이 다 뜰 때까지
    shot(b, "list")


def fig_counts(b):          # 현황 탭 — 열매 개수 표
    b.js("document.querySelector('.tab[data-view=\"dash\"]').click();")
    b.wait("return document.querySelector('#dash').textContent.length>100", 30)
    time.sleep(1.2)
    # 열매 개수 표가 화면 안에 들어오게 (표가 아래에 있으면 안 보인다)
    b.js("const h=[...document.querySelectorAll('#dash h2,#dash h3')]"
         ".find(x=>x.textContent.includes('열매 개수')||x.textContent.includes('개수'));"
         "if(h) h.scrollIntoView({block:'start'});")
    time.sleep(0.8)
    shot(b, "counts")


def fig_export(b):          # 데이터 정리 탭
    b.js("document.querySelector('.tab[data-view=\"exp\"]').click();")
    time.sleep(1.5)
    shot(b, "export")


# ── how_to.html — «사진 한 장, 세 걸음» 여섯 걸음 + 팀 자료 두 장 ──────────
#    글이 «쉬움 모드» 를 전제로 쓰여 있어 이 묶음은 처음부터 끝까지 쉬움 모드다.
HOWTO_GRAPE = "500"                  # 글에 «실제 존재하는 포도 500번» 이라고 적혀 있다
HOWTO_WHO = "사용법 사본"            # 내 이름 칸 — 사람 이름을 쓰면 실적처럼 보인다
APPLE_SUSPECT = "20150921_131346_image151"   # 박성문 «번호 오류» CSV 에 든 사과(빨간 점선)


def fig_login(b):           # 1. 들어가기 — 비밀번호 화면(비밀번호는 안 찍힌다)
    b.go("/login")
    time.sleep(1.2)
    shot(b, "login")


def fig_pick(b):            # 2. 사진 고르기 — 쉬움 모드 목록에서 이름으로 찾기
    b.go("/")                                  # 앞 장이 /login 에 있다
    b.wait("return !!document.querySelector('#fruit option')", 60)
    L.close_tour(b)
    b.js("const w=document.querySelector('#who');w.value=arguments[0];"
         "w.dispatchEvent(new Event('change'))", HOWTO_WHO)
    _fruit(b, "grape")
    _easy(b, True)
    b.js("const q=document.querySelector('#f-q');q.value=arguments[0];"
         "q.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))", HOWTO_GRAPE)
    time.sleep(2.5)
    shot(b, "pick")


def fig_fix(b):             # 3. 잘못된 곳 고치기 — 지우개로 지우는 중
    b.open_photo("grape", HOWTO_GRAPE)
    b.js("document.querySelector('[data-tool=erase]').click();")
    for _ in range(3):
        b.js("document.querySelector('#zoomin').click();")
        time.sleep(0.3)
    time.sleep(1.2)
    b.drag("#cv", 620, 300, 660, 380)          # 한 번 그어 «고치는 중» 을 만든다(모래상자)
    time.sleep(0.8)
    shot(b, "fix")


def fig_saved(b):           # 4. 저장하고 — 위에 «수정본 저장 완료», 아래 «✅ 저장됨»
    b.js("document.querySelector('#btn-save').click();")
    b.wait("return document.querySelector('#todo').textContent.includes('저장')", 60)
    time.sleep(1.2)
    shot(b, "saved")


def fig_confirm(b):         # 5. «다 했어요» 를 누른 뒤 — 아래 줄이 «✔ 확정» 이 된다
    b.js("document.querySelector('#btn-confirm').click();")
    b.wait("return document.querySelector('#topmsg,#stemname')!==null", 30)
    time.sleep(2.0)
    # 이 사진이 목록의 **마지막** 이면 다음 장으로 못 넘어가 아래 줄이 «저장됨» 인 채로 남는다.
    #   글이 말하는 «확정된 모습» 을 보이려면 같은 사진을 다시 열어 상태를 새로 읽어야 한다.
    b.js("document.querySelector('.tab[data-view=\"list\"]').click();")
    time.sleep(1.0)
    b.open_photo("grape", HOWTO_GRAPE)
    b.wait("return document.querySelector('#todo').textContent.indexOf('확정 —')>=0", 60)
    time.sleep(1.2)
    shot(b, "confirm")


def fig_howto(b):           # 6. 다 끝나면 — 이 사용법 화면으로 돌아온다
    b.go("/static/how_to.html")
    time.sleep(2.0)
    shot(b, "howto")


def fig_team_grape(b):      # 팀 자료 — 데이터 정리의 «포도 삭제대상 목록»
    b.go("/")
    b.wait("return !!document.querySelector('#fruit option')", 60)
    L.close_tour(b)
    _fruit(b, "grape")
    _easy(b, True)
    b.js("document.querySelector('.tab[data-view=\"exp\"]').click();")
    time.sleep(1.5)
    b.js("const d=[...document.querySelectorAll('#view-exp details')]"
         ".find(x=>x.textContent.includes('삭제대상')); if(d) d.open=true;")
    time.sleep(1.5)
    shot(b, "team_grape")


def fig_team_apple(b):      # 팀 자료 — 사과 «의심 개체 표시» 를 켠 편집 화면
    b.js("document.querySelector('.tab[data-view=\"list\"]').click();")
    time.sleep(1.0)
    _fruit(b, "apple")
    b.open_photo("apple", APPLE_SUSPECT)
    b.js("const c=document.querySelector('#team-suspect');"
         "if(c && !c.checked){c.click();}")
    time.sleep(1.5)
    shot(b, "team_apple")


# 창 크기별로 묶는다 — 창 하나에 여러 장 (캡션에 적힌 크기 그대로)
PLAN = [(1400, 860, [("easy", fig_easy), ("expert", fig_expert)]),
        (1366, 768, [("edit", fig_edit), ("box", fig_box), ("side", fig_side),
                     ("notezoom", fig_notezoom), ("list", fig_list),
                     ("counts", fig_counts), ("export", fig_export)]),
        (1366, 768, [("login", fig_login), ("pick", fig_pick), ("fix", fig_fix),
                     ("saved", fig_saved), ("confirm", fig_confirm), ("howto", fig_howto),
                     ("team_grape", fig_team_grape), ("team_apple", fig_team_apple)])]


def copy_counts_cache():
    """센 열매 수(`app/cache/instance_counts`)를 모래상자로 옮긴다 — **읽기만** 하고 사본에 쓴다.

    `L.sync()` 는 `cache` 를 일부러 뺀다(시험은 빈 상태에서 시작해야 한다). 그래서 그냥 찍으면
    «열매 개수» 표가 전부 0 이라 사용법 그림으로 쓸 수 없다. 여기서만 실제 값을 넣는다.
    """
    src = os.path.join(L.T, "app", "cache", "instance_counts")
    dst = os.path.join(SB, "app", "cache", "instance_counts")
    if not os.path.isdir(src):
        return 0
    os.makedirs(dst, exist_ok=True)
    n = 0
    for fn in sorted(os.listdir(src)):
        if fn.endswith(".json"):
            shutil.copy2(os.path.join(src, fn), os.path.join(dst, fn))
            n += 1
    print("센 열매 수 %d개 과일을 모래상자로 옮겼다" % n)
    return n


def take(only=None):
    os.makedirs(OUT, exist_ok=True)
    L.sync(SB)
    L.reset_status(SB)
    copy_counts_cache()
    port = L.free_port(5681)
    p = L.start(port=port, sb=SB)
    base = "http://127.0.0.1:%d" % port
    done = []
    try:
        for w, h, figs in PLAN:
            if only and not any(n in only for n, _ in figs):
                continue
            b = L.browser(w=w, h=h, base=base)
            try:
                print("── 창 %d×%d" % (w, h))
                for n, fn in figs:
                    fn(b)                       # 앞 장이 만든 상태를 뒷 장이 이어 쓴다(순서를 지킨다)
                    if not only or n in only:
                        done.append(n)
            finally:
                try:                       # 목록 화면에서는 S 가 없을 수 있다 — 끄는 것이 먼저다
                    L.run(b, "S.edDirty = false; S.bDirty = false; S.numDirty = false;")
                except Exception:          # noqa: BLE001
                    pass
                b.close()
    finally:
        L.stop(p)
    print("찍은 것 %d장 — %s" % (len(done), OUT))
    return 0 if done else 1


if __name__ == "__main__":
    sel = set(sys.argv[2].split(",")) if len(sys.argv) >= 3 else None
    if len(sys.argv) >= 2 and sys.argv[1] == "take":
        sys.exit(take(sel))
    print(__doc__)
    sys.exit(2)
