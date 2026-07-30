"""backend/api/response.py — 统一 JSON 响应格式。

所有 API 端点都通过这两个辅助函数返回结果。
前端 Axios 拦截器期望 {"success": bool, "data": ..., "message": str} 结构。
"""

from flask import jsonify


def success_response(data=None, message="操作成功", status_code=200):
    """构造成功响应。

    Args:
        data: 响应数据，可以是 dict / list / None。
        message: 提示消息。
        status_code: HTTP 状态码，默认 200。

    Returns:
        Flask Response
    """
    return jsonify({"success": True, "data": data, "message": message}), status_code


def error_response(message="操作失败", data=None, status_code=400):
    """构造错误响应。

    Args:
        message: 错误提示消息。
        data: 可选的附加数据。
        status_code: HTTP 状态码，默认 400。

    Returns:
        Flask Response
    """
    return jsonify({"success": False, "data": data, "message": message}), status_code
