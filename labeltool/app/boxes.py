# -*- coding: utf-8 -*-
"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.

작성: 2026-09-20 (구조 정리 사이클 2)
실제 코드는 `app/api/boxes.py (라우트·팀원 상자·내보내기) · app/domain/rules.py (상자 정리 규칙)` 에 있다. 이 파일에는 코드가 없다.

왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
  · `semantic-segmentation/tools/build_merged_dataset.py` (`import boxes` → `export_boxes_to`)
  · `export/export_dataset.py` (`from boxes import human_count, team_count`)
  · 지난 사이클 시험들(`tests/unit/u1_boxes_selftest.py` 등)
그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
"""
from api.boxes import *        # noqa: F401,F403
from api.boxes import (CLASSES, MAX_BOXES, MIN_SIDE, TEAM_BOX_DIRS, TEAM_CLS,
                       boxes_of, clean, demo, export_boxes_to, human_count,
                       read_team_boxes, register, team_box_path, team_count)  # noqa: F401

