"""
tests/test_auth.py - 登录认证单元测试（backend包版本）
"""

import unittest
from unittest.mock import patch, MagicMock


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.patcher_db = patch("backend.controllers.auth_controller.DatabaseManager")
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db
        self.patcher_log = patch("backend.controllers.auth_controller.logger")
        self.patcher_log.start()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    def test_login_success(self):
        """测试正常登录成功。"""
        from backend.controllers.auth_controller import AuthController
        from backend.utils.auth_util import hash_password
        session_mock = MagicMock()
        self._mock_session(session_mock)
        user_mock = MagicMock()
        user_mock.is_locked = 0; user_mock.login_fail_count = 0
        user_mock.role = "student"
        user_mock.password_hash = hash_password("123456")
        session_mock.query.return_value.filter_by.return_value.first.return_value = user_mock
        result = AuthController().login("STU001", "123456")
        self.assertTrue(result["success"]); self.assertEqual(result["role"], "student")

    def test_login_user_not_found(self):
        """测试用户不存在。"""
        from backend.controllers.auth_controller import AuthController
        session_mock = MagicMock(); self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first.return_value = None
        result = AuthController().login("UNKNOWN", "pwd")
        self.assertFalse(result["success"]); self.assertIn("不存在", result["message"])

    def test_login_locked(self):
        """测试账号已锁定。"""
        from backend.controllers.auth_controller import AuthController
        session_mock = MagicMock(); self._mock_session(session_mock)
        user_mock = MagicMock(); user_mock.is_locked = 1
        session_mock.query.return_value.filter_by.return_value.first.return_value = user_mock
        result = AuthController().login("STU001", "pwd")
        self.assertFalse(result["success"]); self.assertIn("锁定", result["message"])

    def test_login_wrong_password(self):
        """测试密码错误。"""
        from backend.controllers.auth_controller import AuthController
        from backend.utils.auth_util import hash_password
        session_mock = MagicMock(); self._mock_session(session_mock)
        user_mock = MagicMock()
        user_mock.is_locked = 0; user_mock.login_fail_count = 0
        user_mock.password_hash = hash_password("correct")
        session_mock.query.return_value.filter_by.return_value.first.return_value = user_mock
        result = AuthController().login("STU001", "wrong")
        self.assertFalse(result["success"])

    def test_password_hash_verify(self):
        from backend.utils.auth_util import hash_password, verify_password
        h = hash_password("test"); self.assertEqual(len(h), 60)
        self.assertTrue(verify_password("test", h))
        self.assertFalse(verify_password("wrong", h))

    def test_change_password_short(self):
        from backend.controllers.auth_controller import AuthController
        result = AuthController().change_password("STU001", "old", "12345")
        self.assertFalse(result["success"]); self.assertIn("长度", result["message"])


if __name__ == "__main__":
    unittest.main()
