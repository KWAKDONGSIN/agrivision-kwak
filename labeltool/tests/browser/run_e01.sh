#!/usr/bin/env bash
# E01 ✨ Shift+클릭·키보드만으로 한 장 끝내기 시험을 새 모래상자에서 파이어폭스·크로미움으로 돌린다 (작성: 2026-09-25)
# 쓰는 법: bash tests/browser/run_e01.sh [포트=5441]   — 실서버 5111·교수님 포트는 건드리지 않는다
set -u
T="$(cd "$(dirname "$0")/../.." && pwd)"
PORT=${1:-5441}
case $PORT in 5100|5101|5102|5104|5105|5111|5112) echo "남의 포트"; exit 2;; esac
if ss -ltn | grep -q ":$PORT "; then echo "포트 $PORT 사용 중 — 멈춤"; exit 2; fi
SB=$T/tests/_sandbox/e01; OUT=$T/tests/_out/e01
NODE=/home/kds0206/.local/share/jev-runtime/node_modules/node/bin/node
PY=/home/kds0206/.conda/envs/kwak/bin/python
mkdir -p "$OUT"; RC=0
for BR in firefox chromium; do
  rm -rf "$SB"; mkdir -p "$SB/app/logs"
  rsync -a --exclude logs --exclude cache --exclude __pycache__ "$T/app/" "$SB/app/"
  rsync -a "$T/data/" "$SB/data/"; rsync -a --exclude __pycache__ "$T/export/" "$SB/export/"
  (cd "$SB/app" && PORT=$PORT LABELTOOL_DATA_ROOT="$(cat "$T/app/logs/last_data_root")" LABELTOOL_PASSWORD= HOST=127.0.0.1 \
     PYTHONDONTWRITEBYTECODE=1 exec "$PY" -u server.py > logs/server.log 2>&1) &
  SP=$!
  for _ in $(seq 60); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.5; done
  "$NODE" "$T/tests/browser/e01_sam_neg_keyboard.mjs" "http://127.0.0.1:$PORT" "$BR" "$OUT" || RC=1
  # 디스크 대조: 키보드 저장·빼기가 모래상자 작업 기록(worklog)에 남았나
  grep -q '"action": *"save"' "$SB/app/logs/worklog.jsonl" 2>/dev/null && grep -q '"action": *"exclude"' "$SB/app/logs/worklog.jsonl" \
    && echo "PASS 모래상자 worklog 에 save·exclude 줄" || { echo "FAIL 모래상자 worklog 에 save·exclude 줄 없음"; RC=1; }
  kill "$SP"; wait "$SP" 2>/dev/null        # 내가 띄운 서버만 끈다
done
echo "== 끝 (RC=$RC) =="; exit $RC
