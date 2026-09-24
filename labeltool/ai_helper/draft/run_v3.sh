#!/bin/bash
# 정직한 성능 측정: 촬영 단위 분할(yolo_ds_v3)로 학습 → eval_v3.py (초벌 파일은 만들지 않는다)
cd "$(dirname "$0")"; export YOLO_OFFLINE=1
log() { echo "$(date '+%F %T') $*" >> v3_status.txt; }
log "학습 시작"
/home/kds0206/venvs/labelai/bin/yolo segment train model=yolo11m-seg.pt data=../yolo_ds_v3/data.yaml imgsz=1280 batch=16 device=${GPUS:-3,4,5,6} workers=8 project=$PWD/runs name=eval_v3 epochs=30 patience=15 plots=False > eval_v3_train.log 2>&1 || { log "학습 실패"; exit 1; }
log "평가 시작"
CUDA_VISIBLE_DEVICES=3 /home/kds0206/venvs/labelai/bin/python eval_v3.py > eval_v3.log 2>&1 && log "ALL_DONE" || log "평가 실패"
