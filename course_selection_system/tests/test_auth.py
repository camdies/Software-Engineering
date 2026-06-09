"""
tests/test_auth.py - 登录认证单元测试

测试login认证逻辑、密码修改、会话验证等功能。
"""

import unittest
from unittest.mock import patch, MagicMock


class TestAuth(unittest.TestCase):
    """登录认证模块单元测试。"""

    def setUp(self):
        """准备测试数据。"""
        self.patcher_db = patch(
            "controllers.auth_controller.DatabaseManager"
        )
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        self.patcher_log = patch("controllers.auth_controller.logger")
        self.patcher_log.start()

    def tearDown(self):
        """清理。"""
        self.patcher_db.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    def test_login_success(self):
        """测试正常登录成功。

        预期: 密码验证通过，返回success=True和正确role。
        """
        from controllers.auth_controller import AuthController
        from utils.auth_util import hash_password

        session_mock = MagicMock()
        self._mock_session(session_mock)

        user_mock = MagicMock()
        user_mock.is_locked = 0
        user_mock.login_fail_count = 0
        user_mock.role = "student"
        user_mock.password_hash = hash_password("123456")

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = user_mock

        controller = AuthController()
        result = controller.login("STU001", "123456")

        self.assertTrue(result["success"])
        self.assertEqual(result["role"], "student")
        self.assertEqual(result["user_id"], "STU001")

    def test_login_user_not_found(self):
        """测试不存在的用户登录。

        预期: 返回success=False，提示用户不存在。
        """
        from controllers.auth_controller import AuthController

        session_mock = MagicMock()
        self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = None

        controller = AuthController()
        result = controller.login("UNKNOWN", "password")

        self.assertFalse(result["success"])
        self.assertIn("不存在", result["message"])

    def test_login_locked_account(self):
        """测试已锁定账号拒绝登录。

        预期: 返回success=False，提示账号已锁定。
        """
        from controllers.auth_controller import AuthController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        user_mock = MagicMock()
        user_mock.is_locked = 1

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = user_mock

        controller = AuthController()
        result = controller.login("STU001", "password")

        self.assertFalse(result["success"])
        self.assertIn("锁定", result["message"])

    def test_login_wrong_password(self):
        """测试密码错误登录。

        预期: 返回success=False，login_fail_count+1。
        """
        from controllers.auth_controller import AuthController
        from utils.auth_util import hash_password

        session_mock = MagicMock()
        self._mock_session(session_mock)

        user_mock = MagicMock()
        user_mock.is_locked = 0
        user_mock.login_fail_count = 0
        user_mock.password_hash = hash_password("correct_password")

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = user_mock

        controller = AuthController()
        result = controller.login("STU001", "wrong_password")

        self.assertFalse(result["success"])
        self.assertIn("密码错误", result["message"])

    def test_password_hash_and_verify(self):
        """测试密码哈希加密和验证的完整性。

        预期: hash_password生成60字符哈希，verify_password正确验证。
        """
        from utils.auth_util import hash_password, verify_password

        hashed = hash_password("test_password")
        self.assertEqual(len(hashed), 60)
        self.assertTrue(verify_password("test_password", hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_password_hash_empty(self):
        """测试空密码抛出ValueError。"""
        from utils.auth_util import hash_password

        with self.assertRaises(ValueError):
            hash_password("")

    def test_change_password_success(self):
        """测试修改密码成功。"""
        from controllers.auth_controller import AuthController
        from utils.auth_util import hash_password

        session_mock = MagicMock()
        self._mock_session(session_mock)

        old_hash = hash_password("old_password")
        user_mock = MagicMock()
        user_mock.password_hash = old_hash

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = user_mock

        controller = AuthController()
        result = controller.change_password(
            "STU001", "old_password", "new_password"
        )

        self.assertTrue(result["success"])

    def test_change_password_short(self):
        """测试新密码长度不足6位时拒绝。"""
        from controllers.auth_controller import AuthController

        controller = AuthController()
        result = controller.change_password(
            "STU001", "old", "12345"
        )

        self.assertFalse(result["success"])
        self.assertIn("长度", result["message"])


if __name__ == "__main__":
    unittest.main()
