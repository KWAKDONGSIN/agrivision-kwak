#!/usr/bin/env bash
# f1 레인 감사용 모래상자 서버(포트 5443)를 띄우거나 끈다 — 실서버 5111·교수님 포트는 건드리지 않는다 (작성: 2026-09-25)
# 쓰는 법: bash auto/f1_sandbox.sh start | stop
set -u
T="$(cd "$(dirname "$0")/../../.." && pwd)"
PORT=5443
SB=$T/tests/_sandbox/f1_audit
PY=/home/kds0206/.conda/envs/kwak/bin/python
case ${1:-start} in
  start)
    if ss -ltn | grep -q ":$PORT "; then echo "포트 $PORT 사용 중"; exit 2; fi
    mkdir -p "$SB/app/logs"
    rsync -a --delete --exclude logs --exclude cache --exclude __pycache__ "$T/app/" "$SB/app/"
    rsync -a "$T/data/" "$SB/data/"; rsync -a --exclude __pycache__ "$T/export/" "$SB/export/"
    ( cd "$SB/app" && PORT=$PORT LABELTOOL_DATA_ROOT="$(cat "$T/app/logs/last_data_root")" LABELTOOL_PASSWORD= HOST=127.0.0.1 \
        PYTHONDONTWRITEBYTECODE=1 setsid nohup "$PY" -u server.py > logs/server.log 2>&1 & echo $! > "$SB/server.pid" )
    for _ in $(seq 60); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.5; done
    curl -s -o /dev/null -w "HTTP %{http_code} %{time_total}s\n" "http://127.0.0.1:$PORT/"
    echo "PID $(cat "$SB/server.pid")";;
  stop)
    # setsid 가 낳은 손자 python 이 진짜 서버라 pid 파일만으로는 안 죽는다 → 5443 을 쥔 프로세스 중 cwd 가 내 모래상자인 것만 끈다
    for P in $(ss -ltnp 2>/dev/null | grep ":$PORT " | grep -o 'pid=[0-9]*' | cut -d= -f2); do
      if readlink "/proc/$P/cwd" 2>/dev/null | grep -q "tests/_sandbox/f1_audit/app"; then kill "$P" && echo "껐음 $P"; fi
    done
    rm -f "$SB/server.pid";;
esac
