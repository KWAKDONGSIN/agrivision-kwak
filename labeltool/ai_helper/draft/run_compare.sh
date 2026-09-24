#!/bin/bash
# 평가 학습(eval_v3)이 끝나면 초벌 개선 방법 비교를 GPU 5·6 에서 나눠 돌린다(GPU 3장 이하 규칙: 7 = ✨ 도우미)
cd "$(dirname "$0")"; export YOLO_OFFLINE=1
PY=/home/kds0206/venvs/labelai/bin/python
echo "$(date '+%F %T') 비교 시작" >> compare_status.txt
CUDA_VISIBLE_DEVICES=5 $PY compare_variants.py A,B,D > compare_ABD.log 2>&1 &
CUDA_VISIBLE_DEVICES=6 $PY compare_variants.py C > compare_C.log 2>&1 &
wait
echo "$(date '+%F %T') 비교 끝 — ALL_DONE" >> compare_status.txt
