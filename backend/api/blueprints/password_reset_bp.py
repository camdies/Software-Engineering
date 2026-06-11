"""password_reset_bp — 密码重置申请 API。

POST /api/auth/forgot-password — 提交密码重置请求（无需登录）
"""

from datetime import datetime
from flask import Blueprint, request

from backend.api.response import success_response, error_response
from backend.models.base import DatabaseManager
from backend.models.password_reset_request import PasswordResetRequest
from backend.models.user_account import UserAccount

password_reset_bp = Blueprint("password_reset", __name__, url_prefix="/api/auth")


@password_reset_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    reason = (data.get("reason") or "").strip()

    if not user_id:
        return error_response("请输入账号")

    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        user = session.query(UserAccount).filter_by(user_id=user_id).first()
        if not user:
            return error_response("该账号不存在")

        # 检查是否有待处理的申请
        existing = (
            session.query(PasswordResetRequest)
            .filter_by(user_id=user_id, status="待审核")
            .first()
        )
        if existing:
            return error_response("您已有一个待处理的密码重置申请，请等待管理员处理")

        req = PasswordResetRequest(
            user_id=user_id,
            reason=reason or "忘记密码",
            status="待审核",
            request_time=datetime.now(),
        )
        session.add(req)

    return success_response(message="密码重置申请已提交，请等待管理员审核")
