#!/bin/bash
# 초벌 v4: 해상도 1536 으로 작은 열매(블루베리·포도 알)를 더 잘 잡는지 촬영 단위로 정직하게 비교 → 나을 때만 전체 학습·draft_v4 예측 → 헷갈림 점수 (작성: 2026-09-24)
# 띄우기: tmux new -d -s draftv4 'bash run_v4.sh'   ·  GPU 는 5,6,7 세 장만(사용자 지시 2026-09-24)
# draft_v2·사람 라벨은 절대 덮어쓰지 않는다. 결과: v4_status.txt(한 줄씩) · v4_result.txt · v4_decision.txt
cd "$(dirname "$0")"; export YOLO_OFFLINE=1
Y=/home/kds0206/venvs/labelai/bin/yolo; PY=/home/kds0206/venvs/labelai/bin/python; GPUS=${GPUS:-5,6,7}
DR=$(cat ../../app/logs/last_data_root)
log() { echo "$(date '+%F %T') $*" >> v4_status.txt; }
[ -e runs/eval_v4 ] || [ -e runs/full_v4 ] && { log "runs/eval_v4 또는 full_v4 가 이미 있음 — 덮어쓰지 않으려고 멈춤"; exit 1; }
log "스모크 시작 (GPU $GPUS, imgsz 1536)"
$Y segment train model=yolo11m-seg.pt data=../yolo_ds_v3/data.yaml imgsz=1536 batch=12 device=$GPUS workers=8 project=$PWD/runs name=smoke_v4 epochs=1 fraction=0.1 plots=False > smoke_v4.log 2>&1 || { log "스모크 실패 — smoke_v4.log 확인"; exit 1; }
L=$(tail -1 runs/smoke_v4/results.csv | cut -d, -f3,4,5); log "스모크 손실 $L"
echo "$L" | grep -qi nan && { log "스모크 NaN — 멈춤"; exit 1; }
log "정직 비교 학습 시작 (촬영 단위 분할 yolo_ds_v3, 30에폭)"
$Y segment train model=yolo11m-seg.pt data=../yolo_ds_v3/data.yaml imgsz=1536 batch=12 device=$GPUS workers=8 project=$PWD/runs name=eval_v4 epochs=30 patience=15 plots=False > eval_v4_train.log 2>&1 || { log "비교 학습 실패"; exit 1; }
CUDA_VISIBLE_DEVICES=${GPUS%%,*} $PY eval_v4.py > eval_v4.log 2>&1 || { log "v4 평가 실패"; exit 1; }
# v3(1280) 와 v4(1536) 의 과일별 mask mAP50 평균 비교
M3=$(grep -oP 'mask mAP50 \K[0-9.]+' v3_result.txt | awk '{s+=$1;n++} END{printf "%.4f", s/n}')
M4=$(grep -oP 'mask mAP50 \K[0-9.]+' v4_result.txt | awk '{s+=$1;n++} END{printf "%.4f", s/n}')
log "비교: v3(1280) 평균 mask mAP50 $M3 · v4(1536) $M4"
if awk "BEGIN{exit !($M4 > $M3 + 0.005)}"; then
  echo "v4 채택: 평균 mask mAP50 $M3 → $M4 (+0.005 넘게 좋아짐)" > v4_decision.txt; log "v4 가 낫다 → 전체 데이터 학습"
  $Y segment train model=yolo11m-seg.pt data=../yolo_ds_v2/data.yaml imgsz=1536 batch=12 device=$GPUS workers=8 project=$PWD/runs name=full_v4 epochs=30 patience=15 plots=True > full_v4_train.log 2>&1 || { log "전체 학습 실패"; exit 1; }
  log "전체 학습 끝 · draft_v4 예측 시작"
  g=5; for f in apple blueberry grape peach; do
    CUDA_VISIBLE_DEVICES=$g IMGSZ=1536 ONLY=$f DRAFT_DIR=draft_v4 LABELTOOL_DATA_ROOT=$DR $PY predict.py runs/full_v4/weights/best.pt > predict_v4_$f.log 2>&1 &
    g=$((g+1)); [ $g -gt 7 ] && g=5
  done; wait
  W=runs/full_v4/weights/best.pt; Z=1536
else
  echo "v4 안 씀: 평균 mask mAP50 $M3 → $M4 (좋아지지 않음) · 초벌은 draft_v2 그대로" > v4_decision.txt; log "v4 가 낫지 않다 → draft_v2 유지"
  W=runs/full_v2/weights/best.pt; Z=1280
fi
log "헷갈림 점수 계산 시작 ($W, imgsz $Z)"
g=5; for f in apple blueberry grape peach; do
  CUDA_VISIBLE_DEVICES=$g IMGSZ=$Z ONLY=$f LABELTOOL_DATA_ROOT=$DR $PY uncertainty.py $W > unc_$f.log 2>&1 &
  g=$((g+1)); [ $g -gt 7 ] && g=5
done; wait
log "헷갈림 점수 끝 — ALL_DONE"
