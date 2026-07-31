"""JWT authentication, account revocation, and role authorization."""

import functools
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from flask import g, request

from backend.api.response import error_response


_JWT_ALGORITHM = "HS256"
_DEV_SECRET = hashlib.sha256(b"edumgmt-development-only-secret").hexdigest()


def _jwt_settings():
    configured = os.environ.get("EDUMGMT_JWT_SECRET", "").strip()
    expiration = 24
    try:
        from backend.config.settings import Settings

        settings = Settings.get_instance()
        configured = configured or settings.jwt_secret.strip()
        expiration = settings.jwt_expiration_hours
    except Exception:
        pass
    return configured or _DEV_SECRET, expiration


def validate_jwt_configuration(production=False):
    """Fail closed in production when no strong, non-default secret is set."""
    secret, _ = _jwt_settings()
    placeholders = {
        _DEV_SECRET,
        "REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS",
        "CHANGE_ME",
    }
    if production and (secret in placeholders or len(secret) < 32):
        raise RuntimeError(
            "Production requires EDUMGMT_JWT_SECRET or [web].jwt_secret "
            "with at least 32 characters"
        )


def create_token(user_id: str, role: str, token_version: int = 0) -> str:
    secret, expiration = _jwt_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "token_version": int(token_version or 0),
        "iat": now,
        "exp": now + timedelta(hours=expiration),
    }
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        secret, _ = _jwt_settings()
        return jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError):
        return None


def require_auth(f):
    """Authenticate the token and re-check current account security state."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return error_response(
                "未登录或登录已过期", status_code=401, code="AUTH_REQUIRED"
            )

        payload = decode_token(auth_header[7:])
        if not payload or not payload.get("user_id"):
            return error_response(
                "登录凭证无效或已过期", status_code=401, code="TOKEN_INVALID"
            )

        try:
            from backend.models.base import DatabaseManager
            from backend.models.user_account import UserAccount

            with DatabaseManager.get_instance().get_session() as session:
                account = session.query(UserAccount).filter_by(
                    user_id=payload["user_id"]
                ).first()
                if account is None:
                    return error_response(
                        "账号不存在", status_code=401, code="ACCOUNT_NOT_FOUND"
                    )
                if account.is_locked == 1:
                    return error_response(
                        "账号已锁定", status_code=401, code="ACCOUNT_LOCKED"
                    )
                current_version = int(account.token_version or 0)
                if int(payload.get("token_version", -1)) != current_version:
                    return error_response(
                        "登录凭证已撤销", status_code=401, code="TOKEN_REVOKED"
                    )
                g.current_user = {
                    "user_id": account.user_id,
                    "role": account.role,
                    "token_version": current_version,
                }
        except Exception:
            return error_response(
                "认证服务暂时不可用",
                status_code=503,
                code="AUTH_SERVICE_UNAVAILABLE",
            )

        return f(*args, **kwargs)

    decorated._requires_auth = True
    return decorated


def require_role(*roles: str):
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            current_role = g.current_user.get("role", "")
            if current_role not in roles:
                return error_response(
                    "无权执行此操作", status_code=403, code="ROLE_FORBIDDEN"
                )
            return f(*args, **kwargs)

        decorated._required_roles = frozenset(roles)
        return decorated

    return decorator
