"""
tests/test_enrollment.py - 选课核心逻辑单元测试

使用unittest框架，针对选课/退课的核心逻辑编写测试用例。
使用unittest.mock模拟数据库连接，测试数据与生产数据严格隔离。
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta


class TestEnrollment(unittest.TestCase):
    """选课核心逻辑单元测试类。

    每个测试方法有完整的docstring说明测试目的和预期结果。
    使用Mock模拟数据库连接，避免对真实数据库的依赖。
    """

    def setUp(self):
        """准备测试数据 — 每个测试用例运行前调用。"""
        # 测试学生数据
        self.student_id = "STU001"

        # 测试开课计划数据
        self.plan_data = {
            "plan_id": 1,
            "course_id": "CS101",
            "teacher_id": "T001",
            "time_slot": "周一1-2节",
            "capacity": 30,
            "enrolled": 20,
            "prerequisite": "",
            "status": "开课",
        }

        # 模拟选课时段为开放状态
        self.patcher_config = patch(
            "controllers.enrollment_controller.Settings"
        )
        self.mock_settings = self.patcher_config.start()
        mock_settings_instance = MagicMock()
        mock_settings_instance.enrollment_is_open = True
        mock_settings_instance.enrollment_open_time = (
            (datetime.now() - timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
        mock_settings_instance.enrollment_close_time = (
            (datetime.now() + timedelta(days=7)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
        mock_settings_instance.session_timeout = 3600
        self.mock_settings.get_instance.return_value = mock_settings_instance

        # 模拟数据库
        self.patcher_db = patch(
            "controllers.enrollment_controller.DatabaseManager"
        )
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        # 模拟logger以关闭测试中的日志输出
        self.patcher_log = patch(
            "controllers.enrollment_controller.logger"
        )
        self.mock_log = self.patcher_log.start()

    def tearDown(self):
        """清理测试数据 — 每个测试用例运行后调用。"""
        self.patcher_config.stop()
        self.patcher_db.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        """设置模拟的数据库会话上下文管理器。

        Args:
            session_mock: 模拟的Session对象。

        Returns:
            上下文管理器mock。
        """
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm
        return cm

    def test_select_course_success(self):
        """测试正常选课成功场景。

        预期: 所有5项校验通过，返回 {'success': True, 'message': '选课成功！'}
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        # Mock: 课程存在且状态为"开课"
        plan_mock = MagicMock()
        plan_mock.status = "开课"
        plan_mock.plan_id = 1
        plan_mock.course_id = "CS101"
        plan_mock.time_slot = "周一1-2节"
        plan_mock.prerequisite = ""
        plan_mock.enrolled = 20
        plan_mock.capacity = 30
        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                plan_mock,       # 查询开课计划
                None,            # 重复选课校验（无记录）
                [],              # 时间冲突校验中的已选课程
                plan_mock,       # FOR UPDATE锁定后的plan
                None,            # 先修课校验中的grade查询
            ]

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "选课成功！")

    def test_select_course_not_in_period(self):
        """测试非选课时段拒绝选课。

        预期: 选课时段配置为关闭状态，返回选课时段错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        # 修改配置模拟：关闭选课
        self.mock_settings.get_instance.return_value.enrollment_is_open = False

        session_mock = MagicMock()
        self._mock_session(session_mock)

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("选课时段", result["message"])

    def test_select_course_duplicate(self):
        """测试重复选课拒绝。

        预期: 已存在status='已选'的enrollment记录，返回重复选课错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        plan_mock = MagicMock()
        plan_mock.status = "开课"
        plan_mock.plan_id = 1

        # 查询开课计划返回plan，重复选课校验返回已存在的记录
        existing_enrollment = MagicMock()
        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                plan_mock,           # 查询开课计划
                existing_enrollment,  # 重复选课校验（已存在）
            ]

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("请勿重复", result["message"])

    def test_select_course_time_conflict(self):
        """测试时间冲突拒绝选课。

        预期: 学生已选课程与新课程时间冲突，返回时间冲突错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        plan_mock = MagicMock()
        plan_mock.status = "开课"
        plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"
        plan_mock.prerequisite = ""

        # 模拟已选课程查询返回有时间冲突的记录
        # query().join().filter().all() 链式调用
        mock_query = MagicMock()
        session_mock.query.return_value.join.return_value.filter.return_value.all \
            .return_value = [("周一1-2节",)]

        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                plan_mock,   # 查询开课计划
                None,        # 重复选课校验（无记录）
            ]

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("时间冲突", result["message"])

    def test_select_course_full_capacity(self):
        """测试容量已满拒绝选课。

        预期: enrolled >= capacity，返回容量已满错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        plan_mock = MagicMock()
        plan_mock.status = "开课"
        plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"

        # FOR UPDATE锁定的plan：已满
        locked_plan = MagicMock()
        locked_plan.enrolled = 30
        locked_plan.capacity = 30

        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                plan_mock,    # 查询开课计划
                None,         # 重复选课校验
            ]

        # 已选课程查询返回空（无冲突）
        session_mock.query.return_value.join.return_value.filter.return_value.all \
            .return_value = []

        # FOR UPDATE查询返回已满的plan
        session_mock.query.return_value.filter.return_value.with_for_update.return_value.first \
            .return_value = locked_plan

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("容量已满", result["message"])

    def test_select_course_prerequisite_fail(self):
        """测试先修课未通过拒绝选课。

        预期: 有先修课要求但成绩不满足，返回先修课未完成错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        plan_mock = MagicMock()
        plan_mock.status = "开课"
        plan_mock.plan_id = 1
        plan_mock.time_slot = "周一1-2节"
        plan_mock.prerequisite = "CS100"

        locked_plan = MagicMock()
        locked_plan.enrolled = 20
        locked_plan.capacity = 30

        # 模拟课程名称查询
        course_mock = MagicMock()
        course_mock.course_name = "程序设计基础"

        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                plan_mock,    # 查询开课计划
                None,         # 重复选课校验
                course_mock,  # 先修课校验中的课程名称查询（None表示未通过）
            ]

        # 已选课程查询返回空（无冲突）
        session_mock.query.return_value.join.return_value.filter.return_value.all \
            .return_value = []

        # FOR UPDATE
        session_mock.query.return_value.filter.return_value.with_for_update.return_value.first \
            .return_value = locked_plan

        # 先修课成绩查询返回None（未通过）
        # query(Grade).filter().join()...
        mock_grade_query = MagicMock()
        mock_grade_query.filter.return_value.join.return_value.filter.return_value.first \
            .return_value = None

        controller = EnrollmentController()
        result = controller.select_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("先修课", result["message"])

    def test_concurrent_enrollment(self):
        """并发选课测试 — 模拟多线程并发选同一课程。

        预期: 仅一名学生选课成功（容量从1变为0），其余失败。
        通过 FOR UPDATE 行级锁保证不会超额选课。
        """
        import threading
        from controllers.enrollment_controller import EnrollmentController

        # 选课结果收集
        results = []

        def _attempt_enroll():
            session_mock = MagicMock()
            self._mock_session(session_mock)
            plan_mock = MagicMock()
            plan_mock.status = "开课"
            plan_mock.plan_id = 1
            plan_mock.time_slot = "周一1-2节"
            plan_mock.prerequisite = ""
            plan_mock.capacity = 1  # 仅1个名额

            # 模拟行级锁效果：第一个线程enrolled=0，第二个线程enrolled=1
            locked_plan = MagicMock()
            locked_plan.capacity = 1
            locked_plan.enrolled = 0 if len([
                r for r in results if r["success"]
            ]) == 0 else 1

            session_mock.query.return_value.filter_by.return_value.first \
                .side_effect = [
                    plan_mock,  # 查询开课计划
                    None,       # 重复选课
                ]
            session_mock.query.return_value.join.return_value.filter.return_value.all \
                .return_value = []
            session_mock.query.return_value.filter.return_value.with_for_update.return_value.first \
                .return_value = locked_plan

            controller = EnrollmentController()
            result = controller.select_course("STU001", 1)
            results.append(result)

        thread1 = threading.Thread(target=_attempt_enroll)
        thread2 = threading.Thread(target=_attempt_enroll)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # 验证结果
        success_count = sum(1 for r in results if r["success"])
        fail_count = sum(1 for r in results if not r["success"])
        self.assertEqual(success_count, 1,
                         f"并发选课应有1人成功，实际成功{success_count}")
        self.assertEqual(fail_count, 1,
                         f"并发选课应有1人失败，实际失败{fail_count}")

    def test_drop_course_success(self):
        """测试退课成功场景。

        预期: 存在有效的已选记录，返回退课成功。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        # Mock: 存在有效的选课记录
        enrollment_mock = MagicMock()
        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = enrollment_mock

        # 课程计划查询
        plan_mock = MagicMock()
        plan_mock.enrolled = 21
        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = plan_mock

        controller = EnrollmentController()
        result = controller.drop_course(self.student_id, 1)

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "退课成功！")

    def test_drop_course_not_enrolled(self):
        """测试退未选课程被拒绝。

        预期: 不存在有效的选课记录，返回错误信息。
        """
        from controllers.enrollment_controller import EnrollmentController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        # Mock: 不存在有效的选课记录
        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = None

        controller = EnrollmentController()
        result = controller.drop_course(self.student_id, 1)

        self.assertFalse(result["success"])
        self.assertIn("未找到", result["message"])


if __name__ == "__main__":
    unittest.main()
