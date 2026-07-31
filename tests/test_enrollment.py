"""
tests/test_enrollment.py - 选课核心逻辑单元测试（backend包版本）
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading
from sqlalchemy.exc import IntegrityError, OperationalError


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
        query_mock.return_value.with_for_update.return_value.filter_by.return_value.first.side_effect = side_effect

    def test_select_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock()
        plan.status = "已通过"; plan.plan_id = 1; plan.course_id = "CS101"
        plan.time_slot = "周一1-2节"; plan.prerequisite = ""
        plan.enrolled = 20; plan.capacity = 30
        self._set_filter_by_first(sm.query, [MagicMock(), plan, None])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
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
        self._set_filter_by_first(sm.query, [MagicMock(), plan, existing])
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
        self._set_filter_by_first(sm.query, [MagicMock(), plan, None])
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
        self._set_filter_by_first(sm.query, [MagicMock(), plan, None])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        plan.enrolled = locked.enrolled; plan.capacity = locked.capacity
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
        self._set_filter_by_first(sm.query, [MagicMock(), plan, None])
        sm.query.return_value.filter_by.return_value.first.return_value = course_mock
        # _check_time_conflict uses all()
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        # _check_prerequisite's Grade sub-query uses filter().join().filter().first()
        # — make it return None (prerequisite NOT passed)
        sm.query.return_value.filter.return_value.join.return_value.filter.return_value.first.return_value = None
        # _check_and_lock_capacity
        plan.enrolled = locked.enrolled; plan.capacity = locked.capacity

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
            self._set_filter_by_first(sm.query, [MagicMock(), plan, None])
            sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
            plan.enrolled = locked.enrolled; plan.capacity = locked.capacity
            results.append(EnrollmentController().select_course("STU001", 1))
        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(1 for r in results if r["success"]), 1)

    def test_drop_course_success(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        enroll_mock = MagicMock(); enroll_mock.status = "已选"; plan_mock = MagicMock()
        plan_mock.enrolled = 21
        self._set_filter_by_first(sm.query, [MagicMock(), plan_mock, enroll_mock])
        r = EnrollmentController().drop_course("STU001", 1)
        self.assertTrue(r["success"])

    def test_drop_course_not_enrolled(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        sm = MagicMock(); self._mock_session(sm)
        self._set_filter_by_first(sm.query, [MagicMock(), MagicMock(), None])
        r = EnrollmentController().drop_course("STU001", 1)
        self.assertFalse(r["success"]); self.assertIn("未找到", r["message"])

    def test_select_student_and_plan_fail_closed(self):
        from backend.controllers.enrollment_controller import EnrollmentController

        for side_effect, code in (([None], "STUDENT_NOT_FOUND"), ([MagicMock(), None], "PLAN_NOT_AVAILABLE")):
            with self.subTest(code=code):
                sm = MagicMock(); self._mock_session(sm)
                self._set_filter_by_first(sm.query, side_effect)
                result = EnrollmentController().select_course("STU001", 1)
                self.assertEqual(result["code"], code)

    def test_reselect_dropped_course_runs_validations_before_reactivation(self):
        from backend.controllers.enrollment_controller import EnrollmentController

        sm = MagicMock(); self._mock_session(sm)
        plan = MagicMock(
            plan_id=1, status="已通过", enrolled=1, capacity=2,
            weekday=1, period_start=1, period_count=2,
            start_week=1, end_week=18, prerequisite="",
        )
        dropped = MagicMock(status="已退")
        self._set_filter_by_first(sm.query, [MagicMock(), plan, dropped])
        sm.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = EnrollmentController().select_course("STU001", 1)
        self.assertTrue(result["success"])
        self.assertEqual(dropped.status, "已选")
        self.assertEqual(plan.enrolled, 2)

    def test_select_exception_semantics_and_bounded_deadlock_retry(self):
        from backend.controllers.enrollment_controller import EnrollmentController

        controller = EnrollmentController()
        deadlock = OperationalError("select", {}, Exception(1213, "deadlock"))
        controller._select_once = MagicMock(side_effect=[
            deadlock,
            {"success": True, "message": "ok"},
        ])
        self.assertTrue(controller.select_course("S", 1)["success"])
        self.assertEqual(controller._select_once.call_count, 2)

        controller._select_once = MagicMock(side_effect=OperationalError(
            "select", {}, Exception(9999, "database down")
        ))
        self.assertEqual(controller.select_course("S", 1)["status_code"], 503)
        controller._select_once = MagicMock(side_effect=IntegrityError(
            "insert", {}, Exception("duplicate")
        ))
        self.assertEqual(controller.select_course("S", 1)["code"], "ALREADY_ENROLLED")
        controller._select_once = MagicMock(side_effect=RuntimeError("boom"))
        self.assertEqual(controller.select_course("S", 1)["status_code"], 503)

    def test_sql_server_lock_hint_and_deadlock_codes(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        from backend.models.student import Student

        controller = EnrollmentController()
        controller._db.is_mssql = True
        session = MagicMock()
        row = MagicMock()
        session.query.return_value.with_hint.return_value.filter_by.return_value.first.return_value = row
        self.assertIs(controller._locked_first(session, Student, student_id="S"), row)
        session.query.return_value.with_hint.assert_called_once()
        for code in (1213, 1205):
            self.assertTrue(controller._is_deadlock(
                OperationalError("x", {}, Exception(code, "deadlock"))
            ))

    def test_real_enrollment_period_semantics(self):
        from backend.controllers.enrollment_controller import EnrollmentController
        from backend.services.semester_resolver import CurrentSemesterResolver

        self.patcher_period.stop()
        controller = EnrollmentController()
        session = MagicMock()
        now = datetime.now()
        cases = [
            (MagicMock(enrollment_open=0), "当前学期选课未开放"),
            (MagicMock(enrollment_open=1, enroll_start=now + timedelta(days=1), enroll_end=None), "选课尚未开始"),
            (MagicMock(enrollment_open=1, enroll_start=None, enroll_end=now - timedelta(days=1)), "选课已结束"),
            (MagicMock(enrollment_open=1, enroll_start=None, enroll_end=None), ""),
        ]
        try:
            for semester, message in cases:
                with self.subTest(message=message), patch.object(
                    CurrentSemesterResolver, "resolve", return_value=semester
                ):
                    self.assertEqual(controller._check_enrollment_period(session)["message"], message)
        finally:
            self.patcher_period = patch.object(
                EnrollmentController, "_check_enrollment_period",
                return_value={"valid": True, "message": ""},
            )
            self.patcher_period.start()


if __name__ == "__main__":
    unittest.main()
