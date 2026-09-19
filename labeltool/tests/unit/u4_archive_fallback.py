# -*- coding: utf-8 -*-
"""단위 ④ «옛 판 서버» 를 띄우는 길이 살아 있나 — 백업 아카이브 폴백. 작성: 2026-09-19

2026-09-19 22:00~22:02 에 `_backup_*` 205개를 `_archive/backups_260920/` 로 **옮겼다.**
그래서 «옛 판 서버 + 새 화면» 을 재현하는 시험(`browser/t2_ui.py` 의 [라] 묶음)이
`T/app/_backup_260918_c4_server.py` 를 그냥 열면 **FileNotFoundError** 로 죽는다.
`tests/lib/sandbox.py` 의 `backup_src()` 가 «원래 자리 → 없으면 아카이브» 로 찾아 주기 때문에 산다.

이 시험은 **그 폴백이 살아 있는지**를 못박는다. 리팩터하다 이 함수를 지우면 여기서 먼저 걸린다.
서버를 띄우지 않는다(파일만 본다).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "lib"))
import sandbox as L                                   # noqa: E402  tests/lib/sandbox.py


def main():
    L.chk("단위4-1 아카이브 폴더가 있다", os.path.isdir(L.ARCHIVE), L.ARCHIVE)

    found, missing = [], []
    for d, fn in L.OLDFILES:
        p = L.backup_src(d, L.OLD_TAG + fn)
        (found if p else missing).append("%s/%s%s" % (d, L.OLD_TAG, fn))
    L.chk("단위4-2 «옛 판» 파일 4개를 다 찾는다(원래 자리든 아카이브든)",
          not missing, "못 찾음: %s" % missing if missing else "찾음 %d개" % len(found))

    # 지금은 아카이브 쪽에서 찾아야 맞다(원래 자리에서 옮겼으니까)
    p = L.backup_src("app", L.OLD_TAG + "server.py")
    L.chk("단위4-3 옮긴 뒤에는 아카이브에서 찾는다",
          bool(p) and p.startswith(L.ARCHIVE), p)

    # 순서: 원래 자리가 **먼저**다(사이클이 새 백업을 만들면 그것을 쓴다)
    # 🔴 2026-09-20 구조 사이클 2: 전에는 `_backup_260919_cnt4_server.py` 가 «원래 자리에 남아 있는
    #    백업» 의 보기였다. 그 파일도 아카이브로 옮겼으므로(카운팅 5 가 굳었다) 보기가 사라졌다.
    #    이제 **이 시험이 스스로 한 개를 만들어** 순서를 확인하고 곧바로 치운다(남기지 않는다).
    probe = "_backup_260920_u4probe_server.py"
    pp = os.path.join(L.T, "app", probe)
    made = False
    try:
        if not os.path.exists(pp):
            with open(pp, "w", encoding="utf-8") as f:
                f.write("# u4 폴백 순서 확인용 임시 파일 — 시험이 끝나면 지웁니다\n")
            made = True
        keep = L.backup_src("app", probe)
        L.chk("단위4-4 원래 자리에 남아 있는 백업은 원래 자리에서 찾는다(아카이브보다 먼저)",
              bool(keep) and not keep.startswith(L.ARCHIVE), keep)
    finally:
        if made and os.path.exists(pp):
            os.remove(pp)
    L.chk("단위4-4b 임시 파일을 남기지 않았다", not os.path.exists(pp), pp)

    L.chk("단위4-5 없는 이름은 None 을 준다(조용히 엉뚱한 파일을 고르지 않는다)",
          L.backup_src("app", "_backup_260101_없는파일.py") is None)

    # 아카이브가 «원래 상대경로» 를 지켰나 — 되돌리기가 `cp -a` 한 줄이 되려면 이게 맞아야 한다
    n = 0
    for d, _, fns in os.walk(L.ARCHIVE):
        n += len([1 for f in fns if f.startswith("_backup_")])
    L.chk("단위4-6 아카이브에 백업 파일이 들어 있다", n > 0, "%d개" % n)
    L.chk("단위4-7 아카이브가 원래 폴더 이름을 지켰다(app·export·scripts)",
          all(os.path.isdir(os.path.join(L.ARCHIVE, x)) for x in ("app", "export", "scripts")),
          sorted(os.listdir(L.ARCHIVE)))
    return L.summary("unit/u4_archive_fallback")


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
