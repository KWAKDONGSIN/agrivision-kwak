# -*- coding: utf-8 -*-
"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.

작성: 2026-09-20 (구조 정리 사이클 2)
실제 코드는 `app/domain/dupes.py (묶음 읽기·제외 목록) · app/core/paths.py (경로) · app/domain/rules.py (대표 고르기) · app/core/status_store.py (status.json)` 에 있다. 이 파일에는 코드가 없다.

왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
  · `export/export_dataset.py`·`export/make_delete_script.py` (`from dupes import …`)
  · `app/api/instances.py` (`DUP.read_status`·`DUP.DATA_DIR`)
그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
"""
from domain.dupes import *     # noqa: F401,F403
from domain.dupes import (APP_DIR, DATASET, DATA_DIR, DEFAULT_DATASET, FRUITS, ROOT,
                          dataset_for, duplicate_exclusions, excluded_stems,
                          load_duplicate_groups, pick_representative,
                          read_status, representative_map)  # noqa: F401

