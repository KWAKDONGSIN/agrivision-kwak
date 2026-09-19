# -*- coding: utf-8 -*-
"""**호환 껍데기** — 옛 import 를 그대로 돌게 하는 얇은 다시 내보내기 모듈.

작성: 2026-09-20 (구조 정리 사이클 2)
실제 코드는 `app/api/instances.py (번호본 읽기·쓰기·라우트) · app/domain/maskio.py (uint16 PNG) · app/api/counts.py (`/api/instance_stats`)` 에 있다. 이 파일에는 코드가 없다.

왜 남기는가: 이 이름으로 부르는 곳이 툴 **밖**에도 있다 —
  · `export/export_dataset.py` (`from instances import source_of, load_inst, …`)
  · `semantic-segmentation/tools/tests_merged_260918/counts/test_counts.py:158` (`import instances`)
  · 지난 사이클 시험들(`tests/unit/u3_instances_u16.py` 등)
그것들이 «조용히 자체 구현으로 떨어지는» 일을 막으려고 이름을 그대로 남긴다
(사이클 1 3차 판정 §2 «호환 껍데기(높음)»).
공개 이름이 하나라도 사라지면 `tests/unit/u6_py_contract.py` 가 실패한다.
"""
from api.instances import *    # noqa: F401,F403
from api.instances import (CACHE_DIR, CC4, ERROR_CSV, KIND_SOURCE, NO_NUM, PARK,
                           SEED_DIRS, SEED_SOURCE, cache_file, cached_counts,
                           count_fresh, count_now, count_one, has_numbers, ids_of,
                           inst_fixed_path, load_counts, load_inst, mask_path_of,
                           png_u16_bytes, read_u16, recount, register, save_counts,
                           seed_source_of, sig_of, source_name, source_of,
                           stale_stems, start_count, summary, write_u16_atomic)  # noqa: F401

