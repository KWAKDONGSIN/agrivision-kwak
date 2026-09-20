#!/usr/bin/env bash
# 라벨링·검수 툴 서버 실행 (nohup) — 작성: 2026-09-16
# 사용법:  bash app/run.sh        (끄기: bash app/run.sh stop)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/home/kds0206/.conda/envs/kwak/bin/python
PORT=${PORT:-5111}
# 원본 이미지·마스크 폴더. 검수 완료 «수정판 데이터셋» 을 보게 하려면 이것만 바꾸면 된다:
#   LABELTOOL_DATA_ROOT=~/datasets_fixed bash app/run.sh restart
DEFAULT_DATA_ROOT=/data/project/2026summer/kds0206/datasets_resized_2mp
LASTFILE="$HERE/logs/last_data_root"
# 환경변수를 주지 않았는데 지난번 기록이 있으면 그것을 이어받는다.
# (그냥 restart 하면 보던 폴더가 기본값으로 조용히 바뀌던 문제를 막습니다)
if [ -z "${LABELTOOL_DATA_ROOT:-}" ] && [ -f "$LASTFILE" ]; then
  LABELTOOL_DATA_ROOT="$(cat "$LASTFILE")"
  echo "지난번에 보던 원본 폴더를 이어서 씁니다: $LABELTOOL_DATA_ROOT"
  echo "  (바꾸려면  LABELTOOL_DATA_ROOT=<폴더> bash app/run.sh restart)"
fi
LABELTOOL_DATA_ROOT=${LABELTOOL_DATA_ROOT:-$DEFAULT_DATA_ROOT}
export LABELTOOL_DATA_ROOT
# 팀 공용 비밀번호. ~/.council/labeltool.env 에 «LABELTOOL_PASSWORD=...» 한 줄로 두면
# 그것을 읽어 서버에 넘깁니다. 파일이 없으면 비밀번호 없이(예전처럼) 뜹니다.
PWFILE="${LABELTOOL_ENV_FILE:-$HOME/.council/labeltool.env}"
if [ -f "$PWFILE" ]; then
  # shellcheck disable=SC1090
  . "$PWFILE"
fi
LABELTOOL_PASSWORD=${LABELTOOL_PASSWORD:-}
export LABELTOOL_PASSWORD
LOG="$HERE/logs/server.log"
PIDF="$HERE/logs/server.pid"
mkdir -p "$HERE/logs"

stop_server() {
  # 0920: 감시자(scripts/watchdog.sh)가 «사람이 일부러 껐다» 를 알아보는 표시.
  # restart 는 곧바로 다시 켜므로 아래 start 자리에서 지운다.
  touch "$HERE/logs/stop.flag" 2>/dev/null || true
  if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
    P=$(cat "$PIDF")
    kill "$P" && echo "서버를 껐습니다 (PID $P)"
    for _ in $(seq 1 20); do            # 최대 10초 기다린다
      kill -0 "$P" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$P" 2>/dev/null; then
      echo "아직 안 꺼졌습니다 (PID $P). 잠시 뒤 다시 시도하세요."; return 1
    fi
    rm -f "$PIDF"
  else
    echo "켜져 있는 서버가 없습니다"
  fi
}

if [ "${1:-start}" = "stop" ]; then stop_server; exit 0; fi
if [ "${1:-start}" = "restart" ]; then stop_server || exit 1; fi

if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "이미 켜져 있습니다 (PID $(cat "$PIDF")). 끄려면: bash app/run.sh stop"
  exit 0
fi

cd "$HERE"
rm -f "$HERE/logs/stop.flag"                     # 0920: 켰으니 «일부러 꺼 둠» 표시를 지운다
printf '%s' "$LABELTOOL_DATA_ROOT" > "$LASTFILE"
PORT="$PORT" LABELTOOL_DATA_ROOT="$LABELTOOL_DATA_ROOT" LABELTOOL_PASSWORD="$LABELTOOL_PASSWORD" \
  nohup "$PY" -u server.py >> "$LOG" 2>&1 &
echo $! > "$PIDF"
sleep 2
if kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "켜졌습니다.  PID $(cat "$PIDF")"
  echo "접속 주소는 팀 카톡 참조 (포트 ${PORT})"
  if [ -n "$LABELTOOL_PASSWORD" ]; then
    echo "비밀번호 게이트: 켜짐 (비밀번호는 $PWFILE)"
  else
    echo "비밀번호 게이트: 꺼짐 ($PWFILE 이 없습니다)"
  fi
  echo "원본 데이터 폴더: $LABELTOOL_DATA_ROOT"
  echo "로그: $LOG"
else
  echo "실행 실패. 로그를 보세요: $LOG"; tail -20 "$LOG"; exit 1
fi
