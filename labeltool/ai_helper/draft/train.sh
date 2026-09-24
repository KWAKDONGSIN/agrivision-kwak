#!/bin/bash
# 모델 초벌용 YOLO 분할 모델 학습 — smoke(1에폭·10%) 로 손실이 줄어드는지 먼저 본 뒤 full 을 돌린다
# 사용: bash train.sh smoke|full  (GPU 는 GPUS 환경변수, 기본 3,4,5,6 — 7 은 클릭 칠하기 도우미)
cd "$(dirname "$0")"
MODE=${1:-smoke}; GPUS=${GPUS:-3,4,5,6}
PY=/home/kds0206/venvs/labelai/bin/python
if [ "$MODE" = smoke ]; then ARGS="epochs=1 fraction=0.1 name=smoke"; else ARGS="epochs=${EPOCHS:-40} name=full patience=15"; fi
exec /home/kds0206/venvs/labelai/bin/yolo segment train model=yolo11m-seg.pt data=../yolo_ds/data.yaml imgsz=1280 batch=16 \
  device=$GPUS workers=8 project=$PWD/runs exist_ok=False plots=True $ARGS
