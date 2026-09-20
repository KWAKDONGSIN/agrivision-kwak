# -*- coding: utf-8 -*-
"""라벨링·검수 웹툴 서버 — **앱을 만들고 기능 묶음을 붙이는 것만** 한다.
작성: 2026-09-16 · 구조 정리: 2026-09-20 (사이클 2)

어디에 무엇이 있나 (처음 온 사람이 여기부터 본다)
  core/paths.py         경로·과일 목록·데이터셋 폴더 (상수는 여기)
  core/util.py          시각·자물쇠·오류 응답·로그
  core/auth.py          팀 공용 비밀번호 문지기 (`/login`)
  core/status_store.py  `status.json` **쓰는 길 하나** (판정·사람 확정)
  domain/maskio.py      마스크 PNG(0/255·uint16) 파일 형식
  domain/statusfmt.py   status 항목의 꼴 · 작업자 B·C 산출물 읽기
  domain/rules.py       데이터 규칙(이름 있는 함수) — 규칙표가 여기를 가리킨다
  domain/dupes.py       근접 중복 묶음
  api/*.py              주소(라우트). 각 파일이 `register(app, ctx)` 하나를 갖는다

- Flask, 0.0.0.0:5111 (환경변수 LABELTOOL_PASSWORD 가 있으면 공용 비밀번호 게이트가 켜진다)
- 팀 표준 데이터셋은 **읽기 전용**. 사람이 고친 마스크는 data/<fruit>/masks_fixed/ 에만 쓴다.
- 작업자 B(inspection.csv, duplicates.json) / 작업자 C(proposals/, proposal_scores.csv) 산출물은
  있으면 읽고, 없으면 해당 기능을 숨긴다.
실행: bash app/run.sh
"""
import os

from flask import Flask
from PIL import Image

from api import boxes as api_boxes
from api import counts as api_counts
from api import dashboard as api_dashboard
from api import dupes as api_dupes
from api import export as api_export
from api import instances as api_instances
from api import masks as api_masks
from api import photos as api_photos
from api import team_review as api_team_review
from core import auth, paths, status_store, util
from core.auth import LABELTOOL_PASSWORD
from core.paths import (CACHE_DIR, DATASET, DATA_DIR, FRUITS, MAX_UPLOAD_BYTES, check,
                        fixed_path, gt_path, img_path, proposal_path, stems_of)
from core.util import err_json, lock_for, now_str
from domain import dupes as DUP
from domain.maskio import save_mask_atomic
from domain.statusfmt import STATUSES

Image.MAX_IMAGE_PIXELS = None

app = Flask(__name__, static_folder=None)
# 한 번에 받을 수 있는 요청 크기 상한(수정본 PNG 는 2MP 기준 수백 KB). 너무 큰 요청은 413.
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# api 묶음이 서로 이름을 직접 부르지 않게 «넘겨주는 꾸러미» 하나로 모은다.
# (0917 부터 boxes.py·instances.py 가 쓰던 방식 그대로 — 키 이름을 바꾸지 않는다)
CTX = {
    "check": check, "DATA_DIR": DATA_DIR, "DATASET": DATASET, "FRUITS": FRUITS,
    "STATUSES": STATUSES, "img_path": img_path, "gt_path": gt_path,
    "fixed_path": fixed_path, "proposal_path": proposal_path, "stems_of": stems_of,
    "lock_for": lock_for, "err_json": err_json, "now_str": now_str,
    "labeled": api_masks.labeled, "save_mask_atomic": save_mask_atomic,
    "read_status": status_store.read_status, "write_status": status_store.write_status,
    "update_status": status_store.update_status,
    "write_status_entry": status_store.write_status_entry,
    "backup_status": status_store.backup_status,
    # 0918 사이클4: 상자·번호를 저장하면 그 작업의 확정이 «수정함» 으로 찍힌다
    "confirm_status": status_store.confirm_status,
    # 0918 사이클4 3차 전 소수정(총괄 결정 1) · 0919 사이클5 2차: 되돌리기·0개 저장은 확정을 벗긴다
    "clear_confirm": status_store.clear_confirm,
}

# 순서: 문지기 → 오류 응답 → 기능 묶음. 주소가 서로 겹치지 않으므로 묶음 사이 순서는 상관없다.
auth.register(app, CTX)
util.register_errors(app)
for _mod in (api_photos, api_masks, api_boxes, api_instances, api_counts,
             api_dupes, api_export, api_dashboard, api_team_review):
    _mod.register(app, CTX)




if __name__ == "__main__":
    print("[라벨링툴] 원본 데이터 폴더(LABELTOOL_DATA_ROOT): %s" % DATASET, flush=True)
    if DATASET != DUP.DEFAULT_DATASET:
        print("[라벨링툴] ※ 기본값이 아닌 폴더를 보고 있습니다(기본: %s)" % DUP.DEFAULT_DATASET, flush=True)
    for f in FRUITS:
        os.makedirs(os.path.join(DATA_DIR, f, "masks_fixed"), exist_ok=True)
        d = os.path.join(DATASET, f, "images")
        print("[라벨링툴]   %-10s %s (%s)" % (
            f, d, ("%d장" % len(stems_of(f))) if os.path.isdir(d) else "폴더 없음 — 이 과일은 비어 보입니다"),
            flush=True)
    port = int(os.environ.get("PORT", "5111"))
    print("[라벨링툴] 비밀번호 게이트: %s" % ("켜짐(/login)" if LABELTOOL_PASSWORD else "꺼짐(LABELTOOL_PASSWORD 없음)"),
          flush=True)
    # 0918 사이클2: 모래상자는 «127.0.0.1 만» 열어야 한다(남이 실수로 들어오지 못하게).
    # 환경변수 HOST 를 주지 않으면 예전과 똑같이 0.0.0.0 이다 — 실서버 동작은 안 바뀐다.
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=port, threaded=True, debug=False)
