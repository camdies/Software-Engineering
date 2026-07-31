"""Shared JSON response helpers and stable API error codes."""

from flask import g, jsonify


def _request_id():
    return getattr(g, "request_id", None)


def success_response(data=None, message="操作成功", status_code=200):
    payload = {"success": True, "data": data, "message": message}
    request_id = _request_id()
    if request_id:
        payload["request_id"] = request_id
    return jsonify(payload), status_code


def error_response(
    message="操作失败",
    data=None,
    status_code=400,
    code="INVALID_REQUEST",
):
    return jsonify({
        "success": False,
        "code": code,
        "message": message,
        "data": data,
        "request_id": _request_id(),
    }), status_code
