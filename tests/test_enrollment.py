"""
tests/test_enrollment.py - 选课核心逻辑单元测试（backend包版本）
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading


class TestEnrollment(unittest.TestCase):
    def setUp(self):
        self.patcher_config = patch("backend.config.settings.Settings")
        self.mock_settings = self.patcher_config.start()
        ms = MagicMock()
        ms.log_level = "ERROR"
        ms.log_dir = "logs"
        ms.enrollment_is_open = True
        ms.enrollment_open_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        ms.enrollment_close_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        ms.session_timeout = 3600
        self.mock_settings.get_instance.return_value = ms

        self.patcher_db = patch("backend.controllers.enrollment_controller.DatabaseManager")
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        from backend.controllers.enrollment_controller import EnrollmentController
        self.patcher_period = patch.object(
            EnrollmentController, "_check_enrollment_period",
            return_value={"valid": True, "message": ""},
        )
        self.patcher_period.start()

        self.patcher_enrollment = patch("backend.controllers.enrollment_controller.Enrollment")
        self.patcher_enrollment.start()
        self.patcher_oplog = patch("backend.controllers.enrollment_controller.OperationLog")
        self.patcher_oplog.start()
        self.patcher_log = patch("backend.controllers.enrollment_controller.logger")
        self.patcher_log.start()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_db.stop()
        self.patcher_period.stop()
        self.patcher_enrollment.stop()
        self.patcher_oplog.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    @staticmethod
    def _set_filter_by_first(query_mock, side_effect):
        query_mock.return_value.filter_by.return_value.first.side_effect = side_effect

    def test_select_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock()
        plan.status = "已通过"; plan.plan_id = 1; plan.course_id = "CS101"
        plan.time_slot = "周一1-2节"; plan.prerequisite = ""
        plan.enrolled = 20; plan.capacity = 30
        self._set_filter_by_first(sm.query, [plan, None])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        sm.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = plan
        r = EnrollmentController().select_course("STU001", 1)
        self.assertTrue(r["success"])

    def test_select_course_not_in_period(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        self.patcher_period.stop()
        self.patcher_period = patch.object(
            EnrollmentController, "_check_enrollment_period",
            return_value={"valid": False, "message": "当前不在选课时段，无法提交选课"},
        )
        self.patcher_period.start()
        sm = MagicMock(); self._mock_session(sm)
        r = EnrollmentController().select_course("STU001", 1)
        self.patcher_period.stop()
        self.patcher_period = patch.object(
            EnrollmentController, "_check_enrollment_period",
            return_value={"valid": True, "message": ""},
        )
        self.patcher_period.start()
        self.assertFalse(r["success"]); self.assertIn("选课时段", r["message"])

    def test_select_course_duplicate(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock(); plan.status = "已通过"; plan.plan_id = 1
        existing = MagicMock(); existing.status = "已选"
        self._set_filter_by_first(sm.query, [plan, existing])
        r = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("请勿重复", r["message"])

    def test_select_course_time_conflict(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock(); plan.status = "已通过"; plan.plan_id = 1
        plan.weekday = 1; plan.period_start = 1; plan.period_count = 2
        plan.start_week = 1; plan.end_week = 20; plan.prerequisite = ""
        # _check_time_conflict returns another MagicMock with weekday/period
        # matching plan => conflict
        conflict_plan = MagicMock()
        conflict_plan.plan_id = 2  # different plan_id
        conflict_plan.weekday = 1; conflict_plan.period_start = 1
        conflict_plan.period_count = 2
        conflict_plan.start_week = 1; conflict_plan.end_week = 20
        self._set_filter_by_first(sm.query, [plan, None])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = [conflict_plan]
        # _check_and_lock_capacity should not be reached
        r = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("时间冲突", r["message"])

    def test_select_course_full_capacity(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock(); plan.status = "已通过"; plan.plan_id = 1
        plan.weekday = 1; plan.period_start = 1; plan.period_count = 2
        plan.start_week = 1; plan.end_week = 20; plan.prerequisite = ""
        locked = MagicMock(); locked.enrolled = 30; locked.capacity = 30
        self._set_filter_by_first(sm.query, [plan, None])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        sm.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = locked
        r = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("容量已满", r["message"])

    def test_select_course_prerequisite_fail(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock(); plan.status = "已通过"; plan.plan_id = 1
        plan.weekday = 1; plan.period_start = 1; plan.period_count = 2
        plan.start_week = 1; plan.end_week = 20; plan.prerequisite = "CS100"
        locked = MagicMock(); locked.enrolled = 20; locked.capacity = 30
        course_mock = MagicMock(); course_mock.course_name = "程序设计基础"
        # first() returns: plan (line 69), None (existing), course_mock
        # (failed prerequisite course-name lookup)
        self._set_filter_by_first(sm.query, [plan, None, course_mock])
        # _check_time_conflict uses all()
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        # _check_prerequisite's Grade sub-query uses filter().join().filter().first()
        # — make it return None (prerequisite NOT passed)
        sm.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = None
        # _check_and_lock_capacity
        sm.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = locked

        r = EnrollmentController().select_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("先修课", r["message"])

    def test_concurrent_enrollment(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        results = []
        def attempt():
            sm = MagicMock(); self._mock_session(sm)
            plan = MagicMock(); plan.status = "已通过"; plan.plan_id = 1
            plan.weekday = 1; plan.period_start = 1; plan.period_count = 2
            plan.start_week = 1; plan.end_week = 20; plan.prerequisite = ""
            locked = MagicMock(); locked.capacity = 1
            locked.enrolled = 0 if sum(1 for r in results if r["success"]) == 0 else 1
            self._set_filter_by_first(sm.query, [plan, None])
            sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
            sm.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = locked
            results.append(EnrollmentController().select_course("STU001", 1))
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(1 for r in results if r["success"]), 1)

    def test_drop_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        enroll_mock = MagicMock(); plan_mock = MagicMock()
        plan_mock.enrolled = 21
        self._set_filter_by_first(sm.query, [enroll_mock, plan_mock])
        r = EnrollmentController().drop_course("STU001", 1)
        self.assertTrue(r["success"])

    def test_drop_course_not_enrolled(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        self._set_filter_by_first(sm.query, [None])
        r = EnrollmentController().drop_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("未找到", r["message"])


if __name__ == "__main__":
    unittest.main()
