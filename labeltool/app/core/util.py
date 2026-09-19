# -*- coding: utf-8 -*-
"""공통 — 시각·숫자·자물쇠·오류 응답·로그. 기능이 없는 잔심부름만 둔다.

구조 사이클 2(2026-09-20)에서 `server.py` 앞머리에 있던 것을 그대로 옮겼다.
"""

from __future__ import annotations
from typing import Any
import logging
import os
import threading
from datetime import datetime

from flask import Response, jsonify, request

from core import paths
from core.auth import API_PATHS, API_PREFIXES
from core.paths import _mtime, mtime_of          # noqa: F401  (옛 이름을 여기서도 부를 수 있게)



_locks = {}
_locks_guard = threading.Lock()


def lock_for(key: str) -> Any:
    """같은 이름의 작업이 함께 쓰는 스레드 잠금을 돌려준다."""
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def now_str() -> str:
    """현재 서버 시각을 기록용 문자열로 돌려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def as_int(v: Any, default: Any=None) -> Any:
    """숫자가 아니면 default. (주소창에 이상한 값이 들어와도 500 이 나지 않게)"""
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default



def short_path(p: Any) -> Any:
    """사람에게 보여 줄 짧은 경로 — 툴 폴더 안이면 그 아래만."""
    p = str(p or "")
    return p[len(paths.ROOT) + 1:] if p.startswith(paths.ROOT + os.sep) else p.replace(os.path.expanduser("~"), "~")


def log_warn(msg: str, *a: Any) -> None:
    """경고 한 줄 — 요청 안이면 Flask 로거, 밖이면 표준 로거(어느 쪽이든 app/logs/server.log).

    전에는 `app.logger` 를 직접 불렀는데, 그 함수들이 `app` 이 없는 모듈로 내려왔다.
    """
    try:
        from flask import current_app
        current_app.logger.warning(msg, *a)
    except Exception:
        logging.getLogger("labeltool").warning(msg, *a)


def log_exc(msg: str, *a: Any) -> None:
    """예외까지 같이 남긴다(log_warn 과 같은 규칙)."""
    try:
        from flask import current_app
        current_app.logger.exception(msg, *a)
    except Exception:
        logging.getLogger("labeltool").exception(msg, *a)




# ---------------------------------------------------------------- 오류 응답(쉬운 한국어 JSON)
def err_json(msg: str, code: int) -> Any:
    """화면(app.js)이 그대로 띄울 수 있는 한 문장. 예전 코드가 j.msg 를 보므로 둘 다 넣는다."""
    return jsonify({"ok": False, "error": msg, "msg": msg}), code

def register_errors(app: Any) -> None:
    """오류 응답(쉬운 한국어 JSON) — API 주소면 JSON, 그 밖은 Flask 가 내던 것 그대로."""


    @app.errorhandler(413)
    def _too_large(e):
        return err_json("보낸 데이터가 너무 큽니다(최대 64MB). 사진이 너무 크거나 브라우저가 이상한 값을 보냈습니다. "
                        "새로고침한 뒤 다시 저장해 보세요.", 413)


    def _is_api_path():
        p = request.path
        return p.startswith(API_PREFIXES) or p in API_PATHS


    def _as_is(e, fallback_code):
        """API 가 아닌 주소면 Flask 가 원래 내보내던 쪽을 그대로 돌려준다."""
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e.get_response()
        return Response("", status=fallback_code)


    @app.errorhandler(404)
    def _not_found(e):
        if _is_api_path():
            return err_json("찾는 것이 없습니다. 사진이나 과일 이름이 맞는지 확인해 주세요.", 404)
        return _as_is(e, 404)


    @app.errorhandler(400)
    def _bad_request(e):
        if _is_api_path():
            return err_json("보낸 값이 올바르지 않습니다. 새로고침한 뒤 다시 해 보세요.", 400)
        return _as_is(e, 400)


    @app.errorhandler(500)
    def _server_error(e):
        if _is_api_path():
            return err_json("서버에서 문제가 생겼습니다. 툴 담당자에게 알려 주세요(app/logs/server.log).", 500)
        return _as_is(e, 500)
