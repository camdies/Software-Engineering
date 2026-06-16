"""
backend/controllers/auth_controller.py - 登录认证控制器

负责用户登录验证、登出、会话管理、密码修改等认证相关业务逻辑。
所有操作写入operation_log审计日志。
"""

from datetime import datetime

from backend.models.base import DatabaseManager
from backend.models.user_account import UserAccount
from backend.models.operation_log import OperationLog
from backend.config.settings import Settings
from backend.utils.auth_util import hash_password, verify_password
from backend.utils.validator import validate_password
from backend.utils.log_util import get_logger

logger = get_logger("auth_controller")


class AuthController:
    """登录认证控制器。

    提供用户身份认证、会话管理、密码修改等功能。
    所有认证操作均记录操作日志以确保审计追溯。
    """

    def __init__(self):
        self._db = DatabaseManager.get_instance()
        self._session_store = {}  # 内存中的会话存储，生产环境可替换为Redis

    def login(self, user_id: str, password: str,
              ip_address: str = "") -> dict:
        """用户登录验证。

        验证流程:
        1. 查询 user_account 表验证用户是否存在
        2. 检查账号是否已锁定
        3. 使用 bcrypt.checkpw() 验证密码哈希
        4. 密码错误累计超过5次则锁定账号
        5. 验证通过后更新 last_login 时间
        6. 写入 operation_log（登录类型）

        Args:
            user_id: 用户账号（学号/工号/管理员账号）。
            password: 明文密码。
            ip_address: 客户端IP地址。

        Returns:
            dict: {'success': bool, 'role': str, 'user_id': str, 'message': str}
        """
        try:
            with self._db.get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=user_id
                ).first()

                # 用户不存在
                if user is None:
                    self._write_log(session, user_id, "登录",
                                    f"用户{user_id}不存在", "失败", ip_address)
                    logger.warning(f"登录失败: 用户{user_id}不存在")
                    return {
                        "success": False,
                        "role": "",
                        "user_id": user_id,
                        "message": "用户不存在",
                    }

                # 账号已锁定
                if user.is_locked == 1:
                    self._write_log(session, user_id, "登录",
                                    f"账号{user_id}已锁定，尝试登录", "失败",
                                    ip_address)
                    logger.warning(f"登录失败: 账号{user_id}已锁定")
                    return {
                        "success": False,
                        "role": "",
                        "user_id": user_id,
                        "message": "账号已锁定，请联系管理员",
                    }

                # 验证密码
                if not verify_password(password, user.password_hash):
                    user.login_fail_count = (user.login_fail_count or 0) + 1
                    max_attempts = Settings.get_instance().max_login_attempts
                    if user.login_fail_count >= max_attempts:
                        user.is_locked = 1
                        logger.warning(
                            f"账号{user_id}密码错误已达{max_attempts}次，已锁定"
                        )
                    self._write_log(session, user_id, "登录",
                                    f"密码错误(第{user.login_fail_count}次)",
                                    "失败", ip_address)
                    return {
                        "success": False,
                        "role": "",
                        "user_id": user_id,
                        "message": (
                            f"密码错误，剩余尝试次数: "
                            f"{max(0, max_attempts - (user.login_fail_count or 0))}"
                        ),
                    }

                # 登录成功
                user.last_login = datetime.now()
                user.login_fail_count = 0

                role = user.role
                logger.info(f"用户{user_id}({role})登录成功")

                # 先返回成功，日志写入在 return 之前；如果日志失败，
                # return 仍然会执行（_write_log 内部捕获异常不回滚）。
                self._write_log(session, user_id, "登录",
                                f"用户{user_id}登录成功", "成功", ip_address)

                return {
                    "success": True,
                    "role": role,
                    "user_id": user_id,
                    "message": "登录成功",
                }

        except Exception as e:
            logger.error(f"登录过程异常: {e}", exc_info=True)
            return {
                "success": False,
                "role": "",
                "user_id": user_id,
                "message": "系统异常，请稍后重试",
            }

    def logout(self, user_id: str) -> bool:
        """用户登出，清除会话信息。

        Args:
            user_id: 用户账号。

        Returns:
            bool: 登出成功返回True。
        """
        try:
            # 清除内存中的会话信息
            self._session_store.pop(user_id, None)
            with self._db.get_session() as session:
                self._write_log(session, user_id, "登录",
                                f"用户{user_id}登出", "成功", "")
            logger.info(f"用户{user_id}登出成功")
            return True
        except Exception as e:
            logger.error(f"登出过程异常: {e}", exc_info=True)
            return False

    def verify_session(self, session_data: dict) -> bool:
        """校验当前Session是否有效。

        检查项:
        - Session数据非空
        - 会话未过期（在session_timeout内）
        - 用户未被锁定

        Args:
            session_data: 会话数据字典，需包含 user_id 和 login_time。

        Returns:
            bool: 会话有效返回True，否则返回False。
        """
        if not session_data or "user_id" not in session_data:
            return False
        try:
            from backend.config.settings import Settings
            timeout = Settings.get_instance().session_timeout
            login_time = session_data.get("login_time")
            if login_time:
                elapsed = (datetime.now() - login_time).total_seconds()
                if elapsed > timeout:
                    logger.warning(
                        f"用户{session_data['user_id']}会话已过期"
                    )
                    return False
            # 检查用户是否被锁定
            with self._db.get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=session_data["user_id"]
                ).first()
                if user and user.is_locked == 1:
                    logger.warning(
                        f"用户{session_data['user_id']}已被锁定"
                    )
                    return False
            return True
        except Exception as e:
            logger.error(f"会话验证异常: {e}", exc_info=True)
            return False

    def change_password(self, user_id: str, old_pwd: str,
                        new_pwd: str) -> dict:
        """修改用户密码。

        流程:
        1. 验证原密码正确性
        2. 校验新密码长度不少于6位
        3. 使用bcrypt加密新密码并更新数据库
        4. 写入操作日志

        Args:
            user_id: 用户账号。
            old_pwd: 原密码。
            new_pwd: 新密码。

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # 校验新密码
            valid, err = validate_password(new_pwd)
            if not valid:
                return {"success": False, "message": err}

            with self._db.get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=user_id
                ).first()
                if user is None:
                    return {"success": False, "message": "用户不存在"}

                # 验证原密码
                if not verify_password(old_pwd, user.password_hash):
                    self._write_log(session, user_id, "系统",
                                    "修改密码-原密码错误", "失败", "")
                    return {"success": False, "message": "原密码错误"}

                # 新密码与原密码不能相同
                if verify_password(new_pwd, user.password_hash):
                    return {"success": False,
                            "message": "新密码不能与原密码相同"}

                # 更新密码
                user.password_hash = hash_password(new_pwd)
                self._write_log(session, user_id, "系统", "修改密码", "成功",
                                "")
                logger.info(f"用户{user_id}密码修改成功")

                return {"success": True, "message": "密码修改成功"}

        except Exception as e:
            logger.error(f"密码修改异常: {e}", exc_info=True)
            return {"success": False, "message": "系统异常，请稍后重试"}

    def request_password_reset(self, admin_id: str, user_id: str) -> dict:
        """管理员重置用户密码（设为默认密码）。

        Args:
            admin_id: 管理员账号。
            user_id: 目标用户账号。

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            default_pwd = "123456"
            with self._db.get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=user_id
                ).first()
                if user is None:
                    return {"success": False, "message": "目标用户不存在"}
                user.password_hash = hash_password(default_pwd)
                user.is_locked = 0
                user.login_fail_count = 0
                self._write_log(session, admin_id, "系统",
                                f"重置{user_id}密码", "成功", "")
                logger.info(f"管理员{admin_id}重置了{user_id}的密码")
                return {"success": True,
                        "message": f"密码已重置为默认密码: {default_pwd}"}
        except Exception as e:
            logger.error(f"密码重置异常: {e}", exc_info=True)
            return {"success": False, "message": "系统异常，请稍后重试"}

    def forgot_password(self, user_id: str, reason: str = "") -> dict:
        """用户申请找回密码（提交重置申请）。

        Args:
            user_id: 账号。
            reason: 申请原因。

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            from backend.models.password_reset_request import PasswordResetRequest

            with self._db.get_session() as session:
                user = session.query(UserAccount).filter_by(
                    user_id=user_id
                ).first()
                if user is None:
                    return {"success": False, "message": "账号不存在"}

                # 检查是否已有待审核的申请
                existing = session.query(PasswordResetRequest).filter_by(
                    user_id=user_id, status="待审核"
                ).first()
                if existing:
                    return {"success": False,
                            "message": "您已有待审核的密码重置申请，请等待管理员处理"}

                req = PasswordResetRequest(
                    user_id=user_id,
                    reason=reason or "",
                    status="待审核",
                    request_time=datetime.now(),
                )
                session.add(req)
                self._write_log(session, user_id, "系统",
                                f"用户{user_id}提交密码重置申请", "成功", "")
                logger.info(f"用户{user_id}提交了密码重置申请")
                return {"success": True,
                        "message": "密码重置申请已提交，请等待管理员审核"}
        except Exception as e:
            logger.error(f"密码重置申请异常: {e}", exc_info=True)
            return {"success": False, "message": "系统异常，请稍后重试"}

    def _write_log(self, session, user_id: str, log_type: str,
                   operation: str, result: str, ip_address: str) -> None:
        """写入操作日志，失败不影响主流程。"""
        try:
            log_entry = OperationLog(
                user_id=user_id,
                log_type=log_type,
                operation=operation,
                result=result,
                log_time=datetime.now(),
                ip_address=ip_address,
            )
            session.add(log_entry)
            # 立即 flush 以便发现问题时 expunge，否则 commit 阶段才报错会
            # 回滚整个事务（包括登录成功的 user 状态更新）。
            session.flush()
        except Exception:
            session.rollback()
            # 把污染对象踢出 session，后续 commit 不受影响
            try:
                session.expunge(log_entry)
            except Exception:
                pass
            logger.warning(f"操作日志写入失败（已跳过）: user={user_id} {operation}")
