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


def wrap_controller_result(result):
    """将现有 Controller 方法返回的 dict/list 包装为统一响应。

    适配策略：
    - 如果 result 包含 'success' 键 → 透传（已是标准格式）
    - 如果 result 包含 'total' 键 → 分页数据，包进 data
    - 如果 result 是 list → 包进 {"items": result}
    - 否则 → 整个 result 作为 data

    Args:
        result: 现有 Controller 方法的返回值。

    Returns:
        (dict, int): (响应体, HTTP状态码)
    """
    if isinstance(result, dict):
        if "success" in result:
            is_ok = result.get("success", False)
            return (
                {"success": is_ok, "data": result, "message": result.get("message", "")},
                200 if is_ok else 400,
            )
        if "total" in result:
            return ({"success": True, "data": result, "message": "查询成功"}, 200)
        return ({"success": True, "data": result, "message": "操作成功"}, 200)

    if isinstance(result, list):
        return ({"success": True, "data": {"items": result}, "message": "查询成功"}, 200)

    return ({"success": True, "data": result, "message": "操作成功"}, 200)
