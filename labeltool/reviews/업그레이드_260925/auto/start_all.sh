#!/usr/bin/env bash
# 260925 업그레이드 레인 4개를 tmux 로 띄우고, 죽은 레인은 다시 띄우는 스크립트 (cron 이 10분마다·재부팅 때 부른다)
A=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴/cycles/260925_업그레이드/auto
[ -e "$A/STOP" ] || [ -e "$A/ALL_DONE" ] && exit 0
[ "$(date +%s)" -ge "$(date -d '2026-09-27 12:00' +%s)" ] && exit 0
for L in w1 r1 f1 cx; do
  tmux has-session -t "up925_$L" 2>/dev/null && continue
  tmux new-session -d -s "up925_$L" "bash $A/run_lane.sh $L"
  echo "$(date '+%F %H:%M:%S') [start_all] $L 띄움" >> "$A/start_all.log"
done
