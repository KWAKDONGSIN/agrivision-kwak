#!/bin/bash
# 초벌 v2: 포도·복숭아를 원본 정답 번호로 바꾼 데이터(yolo_ds_v2)로 스모크 → 본 학습 → data/<과일>/draft_v2 예측 (v1 draft 는 그대로)
cd "$(dirname "$0")"
export YOLO_OFFLINE=1   # 0923 저녁: 시작 때 인터넷 확인이 몇 분씩 멈춰서 끔
Y=/home/kds0206/venvs/labelai/bin/yolo; PY=/home/kds0206/venvs/labelai/bin/python; GPUS=${GPUS:-3,4,5,6}
log() { echo "$(date '+%F %T') $*" >> v2_status.txt; }
log "스모크 시작"
$Y segment train model=yolo11m-seg.pt data=../yolo_ds_v2/data.yaml imgsz=1280 batch=16 device=$GPUS workers=8 project=$PWD/runs name=smoke_v2 epochs=1 fraction=0.1 plots=False > smoke_v2.log 2>&1 || { log "스모크 실패"; exit 1; }
L=$(tail -1 runs/smoke_v2/results.csv | cut -d, -f3,4,5); log "스모크 손실 $L"
echo "$L" | grep -qi nan && { log "스모크 NaN — 멈춤"; exit 1; }
log "본 학습 시작"
$Y segment train model=yolo11m-seg.pt data=../yolo_ds_v2/data.yaml imgsz=1280 batch=16 device=$GPUS workers=8 project=$PWD/runs name=full_v2 epochs=30 patience=15 plots=True > full_v2_train.log 2>&1 || { log "학습 실패"; exit 1; }
log "학습 끝 · 예측 시작"
DR=$(cat ../../app/logs/last_data_root); g=3
for f in apple blueberry grape peach; do
  CUDA_VISIBLE_DEVICES=$g ONLY=$f DRAFT_DIR=draft_v2 LABELTOOL_DATA_ROOT=$DR $PY predict.py runs/full_v2/weights/best.pt > predict_v2_$f.log 2>&1 &
  g=$((g+1))
done
wait
log "예측 끝 — ALL_DONE"
