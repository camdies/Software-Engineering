"""backend/api/auth.py — JWT 认证与授权。

提供：
- create_token() — 登录成功后生成 JWT
- @require_auth — 要求有效 JWT 的装饰器
- @require_role(*roles) — 要求特定角色的装饰器工厂

JWT payload: {user_id, role, exp, iat}
使用 HS256 签名，密钥来自 config.ini [web].jwt_secret。
"""

import os
import functools
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, g

from backend.api.response import error_response


# 默认密钥（本地单进程部署足够；生产环境应配置固定密钥）
_JWT_SECRET = os.urandom(32).hex()
_JWT_ALGORITHM = "HS256"
_JWT_EXPIRATION_HOURS = 24

# 加载 config.ini 中配置的密钥（如果存在）
try:
    from backend.config.settings import Settings
    _config = Settings.get_instance()._config
    _configured_secret = _config.get("web", "jwt_secret", fallback="")
    if _configured_secret.strip():
        _JWT_SECRET = _configured_secret.strip()
except Exception:
    pass


def create_token(user_id: str, role: str) -> str:
    """生成 JWT。

    Args:
        user_id: 用户账号。
        role: 用户角色 (admin/teacher/student)。

    Returns:
        str: 编码后的 JWT 字符串。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=_JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码并验证 JWT。

    Args:
        token: JWT 字符串。

    Returns:
        dict | None: payload 字典，验证失败返回 None。
    """
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def require_auth(f):
    """要求请求携带有效 JWT 的装饰器。

    从 Authorization: Bearer <token> 头提取令牌，
    验证后将 user_id 和 role 写入 flask.g.current_user。

    验证失败返回 401。
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response("未登录或登录已过期", status_code=401)

        token = auth_header[7:]
        payload = decode_token(token)
        if payload is None:
            return error_response("未登录或登录已过期", status_code=401)

        # 检查用户是否被锁定
        try:
            from backend.models.base import DatabaseManager
            from backend.models.user_account import UserAccount
            with DatabaseManager.get_instance().get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=payload["user_id"]
                ).first()
                if user and user.is_locked == 1:
                    return error_response("账号已被锁定，请联系管理员", status_code=403)
        except Exception:
            pass

        g.current_user = {
            "user_id": payload["user_id"],
            "role": payload["role"],
        }
        return f(*args, **kwargs)

    return decorated


def require_role(*roles: str):
    """要求当前用户具有指定角色之一的装饰器工厂。

    必须在 @require_auth 之后使用。

    Args:
        *roles: 允许的角色列表，如 'admin', 'teacher'。

    Returns:
        装饰器函数。
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            current_role = g.current_user.get("role", "")
            if current_role not in roles:
                return error_response("无权执行此操作", status_code=403)
            return f(*args, **kwargs)
        return decorated
    return decorator
