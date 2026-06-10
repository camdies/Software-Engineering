"""auth_bp — 登录/登出/密码修改 API。

POST /api/auth/login          — 登录，返回 JWT
POST /api/auth/logout         — 登出
POST /api/auth/change-password — 修改密码
POST /api/auth/reset-password  — 管理员重置用户密码
"""

from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import create_token, require_auth, require_role
from backend.controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user_id = (data.get("user_id") or "").strip()
    password = data.get("password") or ""
    if not user_id or not password:
        return error_response("请输入账号和密码")

    ip_addr = request.remote_addr or ""
    controller = AuthController()
    result = controller.login(user_id, password, ip_addr)

    if not result.get("success"):
        return error_response(result.get("message", "登录失败"))

    token = create_token(result["user_id"], result["role"])
    return success_response({
        "token": token,
        "role": result["role"],
        "user_id": result["user_id"],
    }, "登录成功")


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    user_id = g.current_user["user_id"]
    AuthController().logout(user_id)
    return success_response(message="已退出登录")


@auth_bp.route("/change-password", methods=["POST"])
@require_auth
def change_password():
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password") or ""
    new_pwd = data.get("new_password") or ""
    if not old_pwd or not new_pwd:
        return error_response("请输入原密码和新密码")

    result = AuthController().change_password(
        g.current_user["user_id"], old_pwd, new_pwd
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "密码修改失败"))


@auth_bp.route("/reset-password", methods=["POST"])
@require_auth
@require_role("admin")
def reset_password():
    data = request.get_json(silent=True) or {}
    target_user = (data.get("user_id") or "").strip()
    if not target_user:
        return error_response("请输入目标用户账号")

    result = AuthController().request_password_reset(
        g.current_user["user_id"], target_user
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "密码重置失败"))
