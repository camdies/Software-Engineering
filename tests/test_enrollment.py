"""
tests/test_enrollment.py - 选课核心逻辑单元测试（backend包版本）
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading


class TestEnrollment(unittest.TestCase):
    def setUp(self):
        self.patcher_config = patch("backend.controllers.enrollment_controller.Settings")
        self.mock_settings = self.patcher_config.start()
        ms = MagicMock()
        ms.enrollment_is_open = True
        ms.enrollment_open_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        ms.enrollment_close_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        ms.session_timeout = 3600
        self.mock_settings.get_instance.return_value = ms

        self.patcher_db = patch("backend.controllers.enrollment_controller.DatabaseManager")
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        self.patcher_log = patch("backend.controllers.enrollment_controller.logger")
        self.patcher_log.start()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_db.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    def test_select_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        plan_mock = MagicMock()
        plan_mock.status = "开课"; plan_mock.plan_id = 1; plan_mock.course_id = "CS101"
        plan_mock.time_slot = "周一1-2节"; plan_mock.prerequisite = ""
        plan_mock.enrolled = 20; plan_mock.capacity = 30
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [plan_mock, None]
        session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = plan_mock
        result = EnrollmentController().select_course("STU001", 1)
        self.assertTrue(result["success"])

    def test_select_course_not_in_period(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        self.mock_settings.get_instance.return_value.enrollment_is_open = False
        session_mock = MagicMock(); self._mock_session(session_mock)
        result = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("选课时段", result["message"])

    def test_select_course_duplicate(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        plan_mock = MagicMock(); plan_mock.status = "开课"; plan_mock.plan_id = 1
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [plan_mock, MagicMock()]
        result = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("请勿重复", result["message"])

    def test_select_course_time_conflict(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        plan_mock = MagicMock(); plan_mock.status = "开课"; plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"; plan_mock.prerequisite = ""
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [plan_mock, None]
        session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = [("周一1-2节",)]
        result = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("时间冲突", result["message"])

    def test_select_course_full_capacity(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        plan_mock = MagicMock(); plan_mock.status = "开课"; plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"
        locked_plan = MagicMock(); locked_plan.enrolled = 30; locked_plan.capacity = 30
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [plan_mock, None]
        session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = locked_plan
        result = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("容量已满", result["message"])

    def test_select_course_prerequisite_fail(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        plan_mock = MagicMock(); plan_mock.status = "开课"; plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"; plan_mock.prerequisite = "CS100"
        locked_plan = MagicMock(); locked_plan.enrolled = 20; locked_plan.capacity = 30
        course_mock = MagicMock(); course_mock.course_name = "程序设计基础"
        session_mock.query.return_value.filter_by.return_value.first.side_effect = [plan_mock, None, course_mock]
        session_mock.query.return_value.join.return_value.filter.return_value.all.return_value = []
        session_mock.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = locked_plan
        # prerequisite grade query returns None
        mgq = MagicMock()
        mgq.filter.return_value.join.return_value.filter.return_value.first.return_value = None
        result = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("先修课", result["message"])

    def test_concurrent_enrollment(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        results = []
        def attempt():
            sm = MagicMock(); self._mock_session(sm)
            pm = MagicMock(); pm.status = "开课"; pm.plan_id = 1
            pm.time_slot = "周一1-2节"; pm.prerequisite = ""; pm.capacity = 1
            lp = MagicMock(); lp.capacity = 1
            lp.enrolled = 0 if len([r for r in results if r["success"]]) == 0 else 1
            sm.query.return_value.filter_by.return_value.first.side_effect = [pm, None]
            sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
            sm.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = lp
            results.append(EnrollmentController().select_course("STU001", 1))
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(1 for r in results if r["success"]), 1)

    def test_drop_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first.return_value = MagicMock()
        plan_mock = MagicMock(); plan_mock.enrolled = 21
        result = EnrollmentController().drop_course("STU001", 1)
        self.assertTrue(result["success"])

    def test_drop_course_not_enrolled(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        session_mock = MagicMock(); self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first.return_value = None
        result = EnrollmentController().drop_course("STU001", 1)
        self.assertFalse(result["success"]); self.assertIn("未找到", result["message"])


if __name__ == "__main__":
    unittest.main()
