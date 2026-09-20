#!/usr/bin/env bash
# 툴 서버가 살아 있는지 1분마다 보고, 죽었으면 다시 켜는 감시자. 작성: 2026-09-20
# 사람이 일부러 끈 경우(run.sh stop → logs/stop.flag)는 다시 켜지 않는다.
# 설치:  bash scripts/watchdog.sh install     (크론 두 줄: 1분 감시 + 재부팅 시 시작)
# 떼기:  bash scripts/watchdog.sh uninstall
# 상태:  bash scripts/watchdog.sh status
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=${PORT:-5111}
LOG="$HERE/app/logs/watchdog.log"
FLAG="$HERE/app/logs/stop.flag"
MARK="# labeltool watchdog"

say() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

check() {
  mkdir -p "$HERE/app/logs"
  # 크론이 진짜로 1분마다 도는지 사람이 확인할 수 있게 «마지막으로 본 시각» 한 줄(덮어쓰기).
  date '+%Y-%m-%d %H:%M:%S' > "$HERE/app/logs/watchdog_alive"
  [ -f "$FLAG" ] && exit 0                       # 사람이 일부러 꺼 둔 상태
  # 로그가 5MB 를 넘으면 뒤 1000줄만 남긴다(디스크를 먹지 않게)
  if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 5000000 ]; then
    tail -1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  fi
  if curl -fsS -m 10 -o /dev/null "http://127.0.0.1:$PORT/login" 2>/dev/null; then exit 0; fi
  say "응답 없음 — 다시 켭니다 (포트 $PORT)"
  PORT="$PORT" bash "$HERE/app/run.sh" restart >> "$LOG" 2>&1
  sleep 3
  if curl -fsS -m 10 -o /dev/null "http://127.0.0.1:$PORT/login" 2>/dev/null; then say "다시 켜짐 OK"
  else say "다시 켜기 실패 — app/logs/server.log 를 보세요"; fi
}

install_cron() {
  local tmp; tmp=$(mktemp)
  crontab -l 2>/dev/null | grep -v "$MARK" > "$tmp"
  printf '* * * * * bash %s/scripts/watchdog.sh check %s\n' "$HERE" "$MARK" >> "$tmp"
  printf '@reboot sleep 30; bash %s/app/run.sh %s\n' "$HERE" "$MARK" >> "$tmp"
  crontab "$tmp"; rm -f "$tmp"
  echo "크론에 넣었습니다 (1분 감시 + 재부팅 시 자동 시작)"; crontab -l | grep "$MARK"
}

uninstall_cron() {
  local tmp; tmp=$(mktemp)
  crontab -l 2>/dev/null | grep -v "$MARK" > "$tmp"
  crontab "$tmp"; rm -f "$tmp"
  echo "크론에서 뺐습니다"
}

case "${1:-check}" in
  check) check ;;
  install) install_cron ;;
  uninstall) uninstall_cron ;;
  status)
    echo "== 크론"; crontab -l 2>/dev/null | grep "$MARK" || echo "  (없음)"
    echo "== 서버"; curl -fsS -m 5 -o /dev/null "http://127.0.0.1:$PORT/login" 2>/dev/null \
      && echo "  살아 있음 (포트 $PORT)" || echo "  응답 없음 (포트 $PORT)"
    echo "== 일부러 꺼 둠"; [ -f "$FLAG" ] && echo "  예 — $FLAG (다시 켜려면 bash app/run.sh)" || echo "  아니요"
    echo "== 감시자가 마지막으로 본 시각(1분마다 갱신)"; cat "$HERE/app/logs/watchdog_alive" 2>/dev/null | sed 's/^/  /' || echo "  (아직 없음 — 크론이 안 돌고 있을 수 있습니다)"
    echo "== 최근 감시 기록"; tail -5 "$LOG" 2>/dev/null || echo "  (없음)" ;;
  *) echo "사용법: bash scripts/watchdog.sh [check|install|uninstall|status]"; exit 1 ;;
esac
