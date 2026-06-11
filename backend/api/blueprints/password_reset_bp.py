"""password_reset_bp — 密码重置申请 API。

POST /api/auth/forgot-password — 提交密码重置请求（无需登录）
"""

from datetime import datetime
from flask import Blueprint, request

from backend.api.response import success_response, error_response
from backend.controllers.auth_controller import AuthController

password_reset_bp = Blueprint("password_reset", __name__, url_prefix="/api/auth")


@password_reset_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    reason = (data.get("reason") or "").strip()

    if not user_id:
        return error_response("请输入账号")

    result = AuthController().forgot_password(user_id, reason)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "申请失败"))
