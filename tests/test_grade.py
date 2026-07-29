"""
tests/test_grade.py - 成绩管理单元测试（backend包版本）
"""

import unittest
from unittest.mock import patch, MagicMock


class TestGrade(unittest.TestCase):
    def setUp(self):
        # get_logger() calls Settings.get_instance() at import time;
        # patch it at the source before any grade_controller import.
        self.patcher_config = patch("backend.config.settings.Settings")
        self.mock_settings = self.patcher_config.start()
        ms = MagicMock()
        ms.log_level = "ERROR"
        ms.log_dir = "logs"
        self.mock_settings.get_instance.return_value = ms

        self.patcher_db = patch("backend.controllers.grade_controller.DatabaseManager")
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        # Mock the ORM classes that record_grade / audit_grade construct,
        # so that SQLAlchemy mapper configuration never runs without a
        # real engine and fully-loaded model registry.
        self.patcher_grade = patch("backend.controllers.grade_controller.Grade")
        self.patcher_grade.start()
        self.patcher_ol = patch("backend.controllers.grade_controller.OperationLog")
        self.patcher_ol.start()

        self.patcher_log = patch("backend.controllers.grade_controller.logger")
        self.patcher_log.start()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_db.stop()
        self.patcher_grade.stop()
        self.patcher_ol.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    def test_record_grade_valid(self):
        from backend.controllers.grade_controller import GradeController
        session_mock = MagicMock(); self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [MagicMock(), None]
        result = GradeController().record_grade("T001", "STU001", 1, 85)
        self.assertTrue(result["success"])

    def test_record_grade_invalid(self):
        from backend.controllers.grade_controller import GradeController
        for s in [-1, 101, "abc"]:
            with self.subTest(score=s):
                r = GradeController().record_grade("T001", "STU001", 1, s)
                self.assertFalse(r["success"]); self.assertIn("格式错误", r["message"])

    def test_record_grade_boundary(self):
        from backend.controllers.grade_controller import GradeController
        session_mock = MagicMock(); self._mock_session(session_mock)
        # first() returns [enrollment_mock, None] per score iteration
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [
            MagicMock(), None,  # score=0
            MagicMock(), None,  # score=60
            MagicMock(), None,  # score=100
        ]
        ctrl = GradeController()
        for s in [0, 60, 100]:
            with self.subTest(score=s):
                self.assertTrue(ctrl.record_grade("T001", "STU001", 1, s)["success"])

    def test_gpa_all_ranges(self):
        from backend.utils.gpa_calculator import calculate_gpa
        cases = [(95, 4.0), (90, 4.0), (89, 3.7), (85, 3.7), (84, 3.3), (80, 3.3),
                 (79, 3.0), (75, 3.0), (74, 2.7), (70, 2.7), (69, 2.3), (65, 2.3),
                 (64, 2.0), (60, 2.0), (59, 0.0), (0, 0.0)]
        for s, g in cases:
            with self.subTest(score=s):
                self.assertEqual(calculate_gpa(s), g)

    def test_cumulative_gpa(self):
        from backend.utils.gpa_calculator import calculate_cumulative_gpa
        self.assertEqual(calculate_cumulative_gpa([
            {"gpa_point": 4.0, "credit": 3.0},
            {"gpa_point": 3.0, "credit": 4.0},
            {"gpa_point": 2.0, "credit": 3.0},
        ]), 3.0)
        self.assertEqual(calculate_cumulative_gpa([]), 0.0)

    def test_grade_audit_approve(self):
        from backend.controllers.grade_controller import GradeController
        session_mock = MagicMock(); self._mock_session(session_mock)
        grade_mock = MagicMock()
        grade_mock.status = "待审核"; grade_mock.score = 75
        grade_mock.new_score = 85
        grade_mock.modify_reason = "申请修改为85: 录入错误"
        session_mock.query.return_value.filter_by.return_value.first.return_value = grade_mock
        result = GradeController().audit_grade("ADMIN", 1, "approve", "核实无误")
        self.assertTrue(result["success"]); self.assertIn("通过", result["message"])

    def test_grade_audit_reject(self):
        from backend.controllers.grade_controller import GradeController
        session_mock = MagicMock(); self._mock_session(session_mock)
        grade_mock = MagicMock()
        grade_mock.status = "待审核"; grade_mock.score = 75
        session_mock.query.return_value.filter_by.return_value.first.return_value = grade_mock
        result = GradeController().audit_grade("ADMIN", 1, "reject", "证据不足")
        self.assertTrue(result["success"]); self.assertIn("驳回", result["message"])


if __name__ == "__main__":
    unittest.main()
