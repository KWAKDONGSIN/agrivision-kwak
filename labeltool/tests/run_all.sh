#!/usr/bin/env bash
# 라벨링·검수 툴 — **시험 전부를 한 번에**.  작성: 2026-09-19
#
#   bash tests/run_all.sh                    ← 보통 이것 하나. 브라우저 묶음은 빠진다
#   bash tests/run_all.sh --browser          ← 진짜 파이어폭스 시나리오까지(느리다)
#   bash tests/run_all.sh --rebaseline       ← 지금 코드로 «기준선» 을 새로 뜬다
#   bash tests/run_all.sh --check-baseline   ← 기준선과 대조해 다른 칸을 표로
#   bash tests/run_all.sh --no-merged        ← 통합 데이터셋 빌드 시험을 건너뛴다(빠르게)
#   bash tests/run_all.sh --only unit,sim    ← 고른 묶음만
#   bash tests/run_all.sh --clean            ← 모래상자·로그를 지우고 끝낸다(디스크 되찾기)
#
# 지키는 것
#   · 쓰기는 `tests/_sandbox/` 안에서만. 공용 `data/`·데이터셋·팀원 폴더는 읽기만.
#   · 서버는 **빈 포트**를 스스로 찾아 127.0.0.1 로 띄우고, 끝나면 **내가 띄운 PID 만** 끈다.
#     실서버 5111 · 교수님 5100·5101·5105 에는 붙지도 끄지도 않는다. `pkill` 을 쓰지 않는다.
#   · 무엇이 어디서 왔는지는 `tests/ORIGIN.md`. 기준선 뜻은 `tests/README.md`.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T="$(dirname "$HERE")"
PY=${PY:-/home/kds0206/.conda/envs/kwak/bin/python}
NODE=${NODE:-/home/kds0206/.local/node22/bin/node}
OUT="$HERE/_out"
LOGS="$OUT/logs"
mkdir -p "$LOGS"
export PYTHONPATH="$HERE/lib${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

WANT_BROWSER=0; WANT_REBASE=0; WANT_CHECK=0; WANT_MERGED=1; ONLY=""; WANT_CLEAN=0
for a in "$@"; do
  case "$a" in
    --browser)        WANT_BROWSER=1 ;;
    --rebaseline)     WANT_REBASE=1 ;;
    --check-baseline) WANT_CHECK=1 ;;
    --no-merged)      WANT_MERGED=0 ;;
    --clean)          WANT_CLEAN=1 ;;
    --only=*)         ONLY="${a#--only=}" ;;
    --only)           ONLY="NEXT" ;;
    -h|--help)        sed -n '2,20p' "$0"; exit 0 ;;
    *) if [ "$ONLY" = "NEXT" ]; then ONLY="$a"; else echo "모르는 옵션: $a"; exit 2; fi ;;
  esac
done
want() { [ -z "$ONLY" ] && return 0; case ",$ONLY," in *,"$1",*) return 0 ;; *) return 1 ;; esac; }

# ── --clean : 모래상자·로그를 치운다 (2026-09-19 2차 검수 §8-1) ────────────
#   실패한 모래상자는 봐야 하니 스스로 지우지 않는다 → `tests/` 가 6.1GB 까지 커진다(실측).
#   이 플래그는 **사람이 시킬 때만** 치운다. `_sandbox`·`_out` 은 다음 실행에서 다시 만들어진다.
if [ "$WANT_CLEAN" = 1 ]; then
  BEFORE=$(du -sh "$HERE" 2>/dev/null | cut -f1)
  rm -rf "$HERE/_sandbox" "$HERE/_out"
  mkdir -p "$LOGS"
  printf '치웠습니다: tests/_sandbox · tests/_out  (%s → %s)\n' "$BEFORE" "$(du -sh "$HERE" 2>/dev/null | cut -f1)"
  if [ "$#" = 1 ]; then exit 0; fi         # --clean 하나만 줬으면 여기서 끝
fi

# ── 결과 표 모으기 ────────────────────────────────────────────────
SUM="$OUT/bundles.tsv"
printf '묶음\t통과\t실패\t초\trc\n' > "$SUM"
FAILED=0
T0=$(date +%s)

note() { printf '\n══ %s\n' "$1"; }

# 로그에서 «통과 N / 실패 M» 또는 «N개 중 M개 통과» 를 읽는다
count_from() {                      # $1=log  → "통과<탭>실패"
  local p f l
  l=$(grep -aoE '통과 [0-9]+ / 실패 [0-9]+' "$1" | tail -1)
  if [ -n "$l" ]; then
    p=$(echo "$l" | grep -oE '통과 [0-9]+' | grep -oE '[0-9]+')
    f=$(echo "$l" | grep -oE '실패 [0-9]+' | grep -oE '[0-9]+')
    printf '%s\t%s' "$p" "$f"; return
  fi
  l=$(grep -aoE '[0-9]+개 중 [0-9]+개 통과, [0-9]+개 실패' "$1" | tail -1)
  if [ -n "$l" ]; then
    p=$(echo "$l" | sed -E 's/^[0-9]+개 중 ([0-9]+)개 통과.*/\1/')
    f=$(echo "$l" | sed -E 's/.*통과, ([0-9]+)개 실패/\1/')
    printf '%s\t%s' "$p" "$f"; return
  fi
  printf -- '-\t-'            # 통과/실패를 못 읽은 묶음(요약 줄이 없는 것) — 칸을 비우지 않는다
}

run1() {                            # $1=묶음이름  $2=로그이름  나머지=명령
  local name="$1" logn="$2"; shift 2
  local log="$LOGS/$logn.log" s e rc pf
  s=$(date +%s)
  "$@" > "$log" 2>&1; rc=$?
  e=$(( $(date +%s) - s ))
  pf=$(count_from "$log")
  printf '%s\t%s\t%s\t%s\n' "$name" "$pf" "$e" "$rc" >> "$SUM"
  if [ "$rc" -ne 0 ]; then FAILED=1; printf '  ✘ %-28s rc=%s · %s초 · %s\n' "$name" "$rc" "$e" "$log"
  else printf '  ✔ %-28s %s초 · %s\n' "$name" "$e" "$(echo -e "$pf" | tr '\t' '/')"; fi
  return $rc
}

# ═══ 1) 문법 ══════════════════════════════════════════════════════
if want syntax; then
  note "1. 문법 — py_compile · node --check"
  # 2026-09-20 구조 사이클 2: `app/core`·`app/api`·`app/domain` 이 생겼다 — 새 파일도 같이 본다.
  #   글롭으로 적으므로 파일이 더 늘어도 여기를 고치지 않는다(묶음 줄은 늘지 않는다 = 기준선 ③ 그대로).
  run1 "syntax/py_compile" syntax_py "$PY" -m py_compile \
      "$T/app/server.py" "$T/app/instances.py" "$T/app/boxes.py" "$T/app/dupes.py" \
      "$T/app/maskio.py" "$T"/app/core/*.py "$T"/app/api/*.py "$T"/app/domain/*.py \
      "$T/export/export_dataset.py" "$T/export/make_delete_script.py" \
      "$T/scripts/ff.py"
  run1 "syntax/node_app.js" syntax_appjs "$NODE" --check "$T/app/static/app.js"
  run1 "syntax/node_ui.js"  syntax_uijs  "$NODE" --check "$T/app/static/ui.js"
  run1 "syntax/bash_run.sh" syntax_runsh bash -n "$T/app/run.sh"
fi

# ═══ 2) 단위 (서버 없음) ═══════════════════════════════════════════
if want unit; then
  note "2. 단위 — 서버를 띄우지 않는 파이썬 단정"
  for f in "$HERE"/unit/u*.py; do
    [ -f "$f" ] || continue
    case "$(basename "$f")" in _backup_*|*_AFTER*|*_BEFORE*) continue ;; esac
    b=$(basename "$f" .py)
    ( cd "$HERE/unit" && run1 "unit/$b" "unit_$b" "$PY" -u "$f" ) || FAILED=1
  done
fi

# ═══ 3) 시뮬 (node · 브라우저 없음) ════════════════════════════════
if want sim; then
  note "3. 시뮬 — app.js 의 함수를 떼어 내 node 로 돌린다"
  for f in "$HERE"/sim/*.js; do
    [ -f "$f" ] || continue
    # 🔴 2026-09-19 2차 검수 §8-2: 이 글롭은 폴더에 **떨어진 것을 다 돌린다.** `_backup_*.js` 를
    #   sim/ 안에 두면 묶음이 조용히 늘어 기준선 ③ 이 «다르다» 가 된다. 백업은
    #   `tests/_backup_260919_st1b/` 에 두고, 여기서도 이름으로 걸러 낸다.
    case "$(basename "$f")" in _backup_*) continue ;; esac
    b=$(basename "$f" .js)
    ( cd "$HERE/sim" && run1 "sim/$b" "sim_$b" "$NODE" "$f" ) || FAILED=1
  done
fi

# ═══ 4) API 회귀 (모래상자 서버) ════════════════════════════════════
if want api; then
  note "4. API 회귀 — 모래상자 서버에 대고(빈 포트 · 내 PID 만 끈다)"
  # t3_login_rate·t4_flag 는 2026-09-20 구조 사이클 2 가 더한 것(로그인 429 · 판정 flag 갈래).
  #   글롭을 쓰지 않는다 — 폴더에 떨어진 것이 조용히 묶음을 늘리지 않게(2차 검수 §8-2 와 같은 이유).
  for f in t1_api regress_all t3_login_rate t4_flag; do
    [ -f "$HERE/api/$f.py" ] || continue
    ( cd "$HERE/api" && run1 "api/$f" "api_$f" "$PY" -u "$HERE/api/$f.py" ) || FAILED=1
  done
fi

# ═══ 5) 통합 데이터셋 빌드 시험 (격리 사본) ══════════════════════════
if want merged && [ "$WANT_MERGED" = 1 ]; then
  note "5. 통합 시험 — tests_merged_260918 (격리 사본에서)"
  run1 "merged/tests_merged_260918" merged env PY="$PY" bash "$HERE/merged/run_merged.sh" || FAILED=1
  grep -a '^###' "$LOGS/merged.log" | sed 's/^/    /'
fi

# ═══ 6) 진짜 브라우저 (--browser) ═══════════════════════════════════
if want browser && [ "$WANT_BROWSER" = 1 ]; then
  note "6. 진짜 파이어폭스 — 스크린샷은 ~/ff_shots/tests_260920 에만"
  ( cd "$HERE/browser" && run1 "browser/prep_sandbox" browser_prep \
      "$PY" -c "import sandbox as L; L.sync(); L.reset_status(); print('모래상자 준비 끝')" ) || FAILED=1
  for f in b1_browser t2_ui; do
    [ -f "$HERE/browser/$f.py" ] || continue
    ( cd "$HERE/browser" && run1 "browser/$f" "browser_$f" "$PY" -u "$HERE/browser/$f.py" ) || FAILED=1
  done
elif want browser; then
  printf '\n══ 6. 진짜 파이어폭스 — 건너뜀(`--browser` 를 주면 돌립니다)\n'
fi

# ═══ 7) 기준선 ══════════════════════════════════════════════════════
if [ "$WANT_REBASE" = 1 ]; then
  note "7. 기준선 새로 뜨기 (--rebaseline)"
  run1 "baseline/rebaseline" baseline_take "$PY" -u "$HERE/baseline/snapshot.py" --rebaseline || FAILED=1
  tail -4 "$LOGS/baseline_take.log" | sed 's/^/    /'
fi
if [ "$WANT_CHECK" = 1 ]; then
  note "8. 기준선 대조 (--check-baseline)"
  run1 "baseline/check" baseline_check "$PY" -u "$HERE/baseline/snapshot.py" --check || FAILED=1
  sed -n '/──/,$p' "$LOGS/baseline_check.log" | sed 's/^/    /'
fi

# ═══ 표 ════════════════════════════════════════════════════════════
TOTAL=$(( $(date +%s) - T0 ))
echo
echo "═══════════════════════════════════════════════════════════════════════"
printf "%-32s %8s %8s %7s %5s\n" "묶음" "통과" "실패" "초" "rc"
echo "───────────────────────────────────────────────────────────────────────"
tail -n +2 "$SUM" | while IFS=$'\t' read -r n p f s r; do
  printf "%-32s %8s %8s %7s %5s\n" "$n" "${p:--}" "${f:--}" "$s" "$r"
done
echo "───────────────────────────────────────────────────────────────────────"
awk -F'\t' 'NR>1{if($2+0==$2)p+=$2; if($3+0==$3)f+=$3} END{printf "%-32s %8d %8d\n", "합계(단정 수)", p, f}' "$SUM"
printf "%-32s %8s초\n" "전체 걸린 시간" "$TOTAL"
echo "═══════════════════════════════════════════════════════════════════════"
if [ "$FAILED" = 0 ]; then echo "전부 통과 (로그: $LOGS)"; else echo "실패가 있습니다 — 로그: $LOGS"; fi
exit $FAILED
