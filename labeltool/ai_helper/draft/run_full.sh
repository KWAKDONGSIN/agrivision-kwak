#!/bin/bash
# 본 학습 → 전체 사진 초벌 예측을 이어서 한다 (nohup 으로 띄워 두면 사람이 없어도 끝까지 간다)
cd "$(dirname "$0")"
echo "$(date '+%F %T') 학습 시작" >> full_status.txt
EPOCHS=30 bash train.sh full > full_train.log 2>&1 || { echo "$(date '+%F %T') 학습 실패 — full_train.log" >> full_status.txt; exit 1; }
echo "$(date '+%F %T') 학습 끝 · 예측 시작" >> full_status.txt
CUDA_VISIBLE_DEVICES=3 LABELTOOL_DATA_ROOT=$(cat ../../app/logs/last_data_root) \
  /home/kds0206/venvs/labelai/bin/python predict.py runs/full/weights/best.pt > predict.log 2>&1 \
  && echo "$(date '+%F %T') 예측 끝 — ALL_DONE" >> full_status.txt \
  || echo "$(date '+%F %T') 예측 실패 — predict.log" >> full_status.txt
