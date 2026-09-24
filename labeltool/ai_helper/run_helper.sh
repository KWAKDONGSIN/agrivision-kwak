#!/bin/bash
# «클릭 칠하기» 도우미(SAM, 127.0.0.1:5112) 켜기·끄기·살아있나 확인 — cron 이 1분마다 check 를 부른다
# 사용: bash run_helper.sh [start|stop|restart|check]
cd "$(dirname "$0")"
PORT=${SAM_PORT:-5112}
PY=/home/kds0206/venvs/labelai/bin/python
PIDF=logs/sam.pid
alive() { curl -fsS -m 5 -o /dev/null "http://127.0.0.1:$PORT/health" 2>/dev/null; }
start() {
  [ -f logs/stop.flag ] && [ "$1" != force ] && { echo "stop.flag 있음 — 사람이 끈 것. 켜려면 start"; return; }
  rm -f logs/stop.flag
  alive && { echo "이미 켜져 있음"; return; }
  # 메모리를 제일 적게 쓰는 GPU 하나(남의 프로세스는 건드리지 않는다)
  GPU=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | sort -t, -k2,2n -k1,1nr | awk -F, 'NR==1{print $1}')
  echo "$(date '+%F %T') 시작 GPU=$GPU" >> logs/helper.log
  CUDA_VISIBLE_DEVICES=$GPU SAM_PORT=$PORT nohup $PY -u sam_server.py >> logs/helper.log 2>&1 &
  echo $! > $PIDF
  for i in $(seq 1 90); do alive && { echo "켜짐 PID $(cat $PIDF) GPU $GPU"; return; }; sleep 1; done
  echo "90초 안에 안 켜짐 — logs/helper.log 확인"
}
stop() {
  touch logs/stop.flag
  # 파일의 PID 가 정말 우리 sam_server.py 일 때만 끈다(번호가 남의 프로세스에 재사용됐을 수 있다)
  if [ -f $PIDF ]; then
    pid=$(cat $PIDF)
    if ps -p "$pid" -o cmd= 2>/dev/null | grep -q "sam_server.py"; then kill "$pid" && echo "껐음 PID $pid"; fi
  fi
  rm -f $PIDF
}
case "${1:-start}" in
  start) start force ;;
  stop) stop ;;
  restart) stop; sleep 2; start force ;;
  check) alive || { [ -f logs/stop.flag ] || { echo "$(date '+%F %T') 죽어 있어 다시 켬" >> logs/helper.log; start; }; } ;;
esac
