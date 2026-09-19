#!/usr/bin/env bash
# 통합 데이터셋 빌드 시험(`semantic-segmentation/tools/tests_merged_260918/`)을 **격리 사본**에서 돌린다.
# 작성: 2026-09-19
#
# 왜 사본인가
#   원본 시험들은 자기 폴더 안(`tests_merged_260918/*/sandbox/`)에 모래상자를 만든다.
#   다른 세션(예: «상자+개수 세기» 사이클)이 같은 폴더에서 같은 시험을 돌리고 있으면 서로를 덮어쓴다.
#   그래서 돌릴 때마다 원본을 **읽어서** 사본을 새로 맞추고(rsync), 사본 안에서만 쓴다.
#   원본 시험 파일은 한 글자도 고치지 않는다(지시서: «그대로 두고 run_all 에서 호출만»).
#
# 쓰는 곳: tests/_sandbox/merged/   ·   원본: 읽기만
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS="$(dirname "$HERE")"
T="$(dirname "$TESTS")"
: "${PY:=/home/kds0206/.conda/envs/kwak/bin/python}"
SRC_TOOLS=/data/project/2026summer/kds0206/semantic-segmentation/tools
SRC=$SRC_TOOLS/tests_merged_260918
MIRROR=$TESTS/_sandbox/merged

if [ ! -d "$SRC" ]; then
  echo "SKIP 통합시험 — 원본 폴더가 없습니다: $SRC"
  exit 0
fi

mkdir -p "$MIRROR"
# tools/ 의 파이썬 파일을 심볼릭 링크로 걸어 둔다(사본이 `TOOLS = dirname(HERE)` 로 찾는다 · 읽기만)
for f in "$SRC_TOOLS"/*.py; do
  [ -e "$f" ] || continue
  ln -sfn "$f" "$MIRROR/$(basename "$f")"
done
# 시험 파일만 사본으로. 원본의 모래상자·로그는 가져오지 않는다(용량·충돌).
rsync -a --delete \
  --exclude 'sandbox' --exclude 'sandbox_*' --exclude '__pycache__' \
  --exclude '*.log' --exclude '*.txt' \
  "$SRC/" "$MIRROR/tests_merged_260918/"

# ── 얼린 툴 자료 (2026-09-20 구조 사이클 2 · 1차 검수 §7-3)
#   통합 시험 몇 개는 공용 `T/data/<과일>/status.json` 을 **지금 것으로** 읽는다. 사람이 툴에서
#   판정 한 장을 확정하면 손으로 적어 둔 숫자가 어긋나 시험이 실패한다(09-19 22:55 실측: 977→975).
#   그래서 **판정·묶음 파일만** 얼려 둔 사본(`tests/fixtures/tool_data_260920/`)을 쓰고,
#   무거운 폴더(masks_fixed·boxes·instances_fixed·proposals …)는 심볼릭 링크로 «지금 것» 을 본다.
#   `build_merged_dataset.py` 와 시험 셋이 `MERGED_TOOL_DATA` 를 보면 그것을 쓴다(없으면 예전 그대로).
FROZEN="$TESTS/fixtures/tool_data_260920"
TOOLDATA="$MIRROR/tool_data"
if [ -d "$FROZEN" ] && [ -d "$T/data" ]; then
  rm -rf "$TOOLDATA"
  for fd in "$T/data"/*; do
    [ -d "$fd" ] || continue
    f=$(basename "$fd")
    mkdir -p "$TOOLDATA/$f"
    for e in "$fd"/*; do [ -e "$e" ] && ln -sfn "$e" "$TOOLDATA/$f/$(basename "$e")"; done
    for fn in status.json duplicates.json; do
      if [ -f "$FROZEN/$f/$fn" ]; then rm -f "$TOOLDATA/$f/$fn"; cp "$FROZEN/$f/$fn" "$TOOLDATA/$f/$fn"; fi
    done
  done
  export MERGED_TOOL_DATA="$TOOLDATA"
  echo "얼린 툴 자료를 씁니다: $TOOLDATA (status.json·duplicates.json 만 얼렸습니다)"
else
  echo "얼린 툴 자료가 없습니다 — 공용 data/ 를 그대로 읽습니다(시험이 흔들릴 수 있습니다)"
fi

cd "$MIRROR/tests_merged_260918"
rc=0; SP=0; SF=0
for t in test_build_merged.py stage2/test_fixes_m2.py stage3/test_fixes_m3.py \
         stage4/test_confirm_kinds.py stage5/test_spec.py stage5/test_fix_m5c.py \
         counts/test_counts.py; do
  [ -f "$t" ] || { echo "### $t : 없음(건너뜀)"; continue; }
  log="$MIRROR/$(echo "$t" | tr '/' '_').log"
  s=$(date +%s)
  PYTHONDONTWRITEBYTECODE=1 "$PY" -u "$t" > "$log" 2>&1
  r=$?
  e=$(( $(date +%s) - s ))
  # 일곱 시험이 요약 문구를 서로 다르게 쓴다(«통과 N / 실패 M» · «항목 N개» · «전부 통과»).
  # 다행히 항목 한 줄은 모두 «[통과]»·«[실패]» 로 시작하므로 그 줄을 센다.
  p=$(grep -acE '^[[:space:]]*\[통과\]' "$log"); f=$(grep -acE '^[[:space:]]*\[실패\]' "$log")
  SP=$((SP + p)); SF=$((SF + f))
  echo "### $t : rc=$r · ${e}초 · 통과 $p / 실패 $f"
  [ "$r" -ne 0 ] && rc=1
done
echo "MERGED_DONE rc=$rc"
echo "통과 $SP / 실패 $SF"
# 이 시험들은 «아무것도 지우지 않는다» 는 규칙이라 돌릴 때마다 꼬리표를 붙여 쌓는다(한 번에 약 5.6GB).
# 통과했으면 사본의 모래상자를 지운다(원본 폴더는 건드리지 않는다).
# 실패했으면 **남겨 둔다** — 그 안을 봐야 하니까.
if [ "$rc" -eq 0 ]; then
  du -sh "$MIRROR" 2>/dev/null | sed 's/^/치우기 전 /'
  find "$MIRROR/tests_merged_260918" -maxdepth 2 -type d \( -name 'sandbox' -o -name 'sandbox_*' \) \
       -exec rm -rf {} + 2>/dev/null
  du -sh "$MIRROR" 2>/dev/null | sed 's/^/치운 뒤 /'
else
  echo "실패가 있어 모래상자를 남겨 둡니다: $MIRROR/tests_merged_260918"
fi
exit $rc
