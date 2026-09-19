# -*- coding: utf-8 -*-
"""
«제외» 로 판정된 사진을 원본 폴더에서 정말 치울 때 쓸 **삭제 스크립트를 만들어 주는** 도구
작성: 2026-09-16

⚠️ 이 파이썬 파일은 아무것도 지우지 않습니다. `.sh` 파일을 하나 만들어 줄 뿐입니다.
   만들어진 스크립트는 **곽동신이 내용을 직접 읽어 보고** 직접 실행합니다.
   (작업 지침: Claude 는 삭제·이동을 직접 하지 않고 스크립트만 만든다)

기본값은 «지우기» 가 아니라 «따로 빼두기(quarantine)» 입니다 — mv 로 격리 폴더에 옮기고,
되돌리는 명령도 스크립트 안에 주석으로 같이 적어 둡니다.

사용 예:
  PY=/home/kds0206/.conda/envs/kwak/bin/python
  $PY export/make_delete_script.py --fruit blueberry                       # 격리(mv) 스크립트
  $PY export/make_delete_script.py --fruit all --mode rm                   # 진짜 삭제 스크립트
  bash 260916_제외사진_격리_blueberry.sh          ← 이건 사람이 직접
"""
import os
import sys
import argparse
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from dupes import excluded_stems, DATASET, DATA_DIR, FRUITS   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def q(s):
    return "'" + s.replace("'", "'\\''") + "'"


def main():
    ap = argparse.ArgumentParser(description="제외 사진 격리/삭제 스크립트 생성(실행은 사람이)")
    ap.add_argument("--fruit", required=True, choices=FRUITS + ["all"])
    ap.add_argument("--mode", default="mv", choices=["mv", "rm"],
                    help="mv=격리 폴더로 옮김(기본, 되돌릴 수 있음) / rm=진짜 삭제")
    ap.add_argument("--quarantine", default=os.path.join(ROOT, "excluded_quarantine"),
                    help="mv 모드에서 옮겨 둘 폴더")
    ap.add_argument("--drop-flag", action="store_true", help="'문제 있음(flag)' 도 제외 대상에 포함")
    ap.add_argument("--out", default=None, help="만들 .sh 경로")
    args = ap.parse_args()

    fruits = FRUITS if args.fruit == "all" else [args.fruit]
    today = date.today().strftime("%y%m%d")
    out = args.out or os.path.join(ROOT, "export", "%s_제외사진_%s_%s.sh"
                                   % (today, "삭제" if args.mode == "rm" else "격리", args.fruit))

    L = ["#!/usr/bin/env bash",
         "# 제외 사진 %s 스크립트 — 생성 %s" % ("삭제" if args.mode == "rm" else "격리", date.today()),
         "# 만든 것: export/make_delete_script.py   (실행은 사람이 직접)",
         "#",
         "# ⚠️ 실행하면 아래 폴더의 파일이 바뀝니다. 내용을 먼저 읽어 보세요.",
         "#    대상 폴더: %s" % DATASET,
         "#    (환경변수 LABELTOOL_DATA_ROOT 로 정해집니다 — 지우려는 폴더가 맞는지 꼭 확인하세요)",
         "# ⚠️ 이 데이터셋은 팀 공용입니다. 실행 전에 팀에 알리세요.",
         "#",
         "# 이미 폴더에 없는 파일은 «건너뜁니다»(중간에 멈추지 않습니다).",
         "# 맨 끝에 «이동 N / 없음 M» 처럼 몇 개를 처리했는지 찍어 줍니다.",
         "set -eu",
         "N_DONE=0", "N_MISS=0", ""]
    total = 0
    missing_now = 0
    for fruit in fruits:
        items = excluded_stems(fruit, include_duplicates=True, drop_flag=args.drop_flag)
        L.append('echo "=== %s : %d장 ==="' % (fruit, len(items)))
        if not items:
            L.append('echo "  제외 대상이 없습니다"')
            L.append("")
            continue
        if args.mode == "mv":
            qi = os.path.join(args.quarantine, fruit, "images")
            qm = os.path.join(args.quarantine, fruit, "masks")
            L.append("mkdir -p %s %s" % (q(qi), q(qm)))
        for s, reason in items:
            src_i = os.path.join(DATASET, fruit, "images", s + ".png")
            src_m = os.path.join(DATASET, fruit, "masks", s + ".png")
            L.append("# %s  (%s)" % (s, reason))
            for p in (src_i, src_m):
                if not os.path.exists(p):
                    missing_now += 1
                if args.mode == "mv":
                    sub = "images" if p == src_i else "masks"
                    act = "mv -n %s %s/" % (q(p), q(os.path.join(args.quarantine, fruit, sub)))
                else:
                    act = "rm -f %s" % q(p)
                # 없는 파일은 건너뛴다. (예전에는 set -eu + mv 라 첫 줄에서 스크립트가 통째로 멈췄다)
                L.append("[ -f %s ] && { %s || exit 1; N_DONE=$((N_DONE+1)); } || N_MISS=$((N_MISS+1))"
                         % (q(p), act))
        total += len(items)
        L.append("")
        if args.mode == "mv":
            L.append("# 되돌리려면(이 과일):")
            L.append("#   mv %s/*.png %s/" % (q(os.path.join(args.quarantine, fruit, 'images')),
                                              q(os.path.join(DATASET, fruit, 'images'))))
            L.append("#   mv %s/*.png %s/" % (q(os.path.join(args.quarantine, fruit, 'masks')),
                                              q(os.path.join(DATASET, fruit, 'masks'))))
            L.append("")
    L.append('echo "끝났습니다. 총 %d장 대상(파일 %d개)."' % (total, total * 2))
    L.append('echo "%s $N_DONE / 없음 $N_MISS"' % ("삭제" if args.mode == "rm" else "이동"))

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    os.chmod(out, 0o644)
    print("대상 폴더(LABELTOOL_DATA_ROOT): %s" % DATASET)
    print("스크립트를 만들었습니다: %s" % out)
    print("대상 %d장 (%s 모드). 내용을 읽어 본 뒤 직접 실행하세요:  bash %s" % (total, args.mode, out))
    if missing_now:
        print("※ 대상 파일 %d개 중 %d개는 **지금 이 폴더에 이미 없습니다**(중복 정리로 빠진 사진 등)."
              % (total * 2, missing_now))
        print("   스크립트는 그런 파일을 건너뛰고 끝에 «%s N / 없음 M» 을 찍습니다."
              % ("삭제" if args.mode == "rm" else "이동"))
    print("※ 이 파이썬 파일은 아무것도 지우지 않았습니다.")


if __name__ == "__main__":
    main()
