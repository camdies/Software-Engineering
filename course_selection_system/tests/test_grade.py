"""
tests/test_grade.py - 成绩管理单元测试

使用unittest框架，针对成绩录入、绩点计算、批量导入、审核等核心逻辑编写测试用例。
"""

import unittest
from unittest.mock import patch, MagicMock


class TestGrade(unittest.TestCase):
    """成绩管理单元测试类。

    测试成绩录入、绩点计算全区间、批量导入含非法数据、
    审核通过/驳回等场景。
    """

    def setUp(self):
        """准备测试数据。"""
        self.teacher_id = "T001"
        self.student_id = "STU001"
        self.plan_id = 1

        # 模拟数据库
        self.patcher_db = patch(
            "controllers.grade_controller.DatabaseManager"
        )
        self.mock_db_cls = self.patcher_db.start()
        self.mock_db = MagicMock()
        self.mock_db_cls.get_instance.return_value = self.mock_db

        # 模拟logger
        self.patcher_log = patch(
            "controllers.grade_controller.logger"
        )
        self.patcher_log.start()

    def tearDown(self):
        """清理测试数据。"""
        self.patcher_db.stop()
        self.patcher_log.stop()

    def _mock_session(self, session_mock):
        """设置模拟的数据库会话上下文管理器。"""
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=session_mock)
        cm.__exit__ = MagicMock(return_value=False)
        self.mock_db.get_session.return_value = cm

    def test_record_grade_valid(self):
        """测试合法成绩录入成功。

        预期: score=85，录入成功，返回成功信息。
        """
        from controllers.grade_controller import GradeController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        # enrollment存在
        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                MagicMock(),  # enrollment存在
                None,          # grade表中无记录
            ]

        controller = GradeController()
        result = controller.record_grade(
            self.teacher_id, self.student_id, self.plan_id, 85
        )

        self.assertTrue(result["success"])
        self.assertIn("成功", result["message"])

    def test_record_grade_invalid_score(self):
        """测试非法成绩值被拒绝。

        测试值: -1, 101, 'abc'
        预期: 全部返回 False，错误信息包含'格式错误'。
        """
        from controllers.grade_controller import GradeController

        controller = GradeController()
        invalid_scores = [-1, 101, "abc"]

        for score in invalid_scores:
            with self.subTest(score=score):
                result = controller.record_grade(
                    self.teacher_id, self.student_id,
                    self.plan_id, score
                )
                self.assertFalse(result["success"])
                self.assertIn("格式错误", result["message"])

    def test_record_grade_boundary(self):
        """测试成绩边界值。

        测试值: 0, 60, 100
        预期: 全部合法，录入成功。
        """
        from controllers.grade_controller import GradeController

        session_mock = MagicMock()
        self._mock_session(session_mock)
        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = [
                MagicMock(),  # enrollment存在
                None,          # grade表中无记录
            ]

        controller = GradeController()
        for score in [0, 60, 100]:
            with self.subTest(score=score):
                result = controller.record_grade(
                    self.teacher_id, self.student_id,
                    self.plan_id, score
                )
                self.assertTrue(result["success"],
                                f"边界值{score}应该合法")

    def test_gpa_calculation_all_ranges(self):
        """测试绩点计算全区间映射。

        验证每个分数段对应的绩点值。
        """
        from utils.gpa_calculator import calculate_gpa

        test_cases = [
            (95, 4.0), (90, 4.0),  # 优秀
            (89, 3.7), (85, 3.7),  # 良好上
            (84, 3.3), (80, 3.3),  # 良好下
            (79, 3.0), (75, 3.0),  # 中等上
            (74, 2.7), (70, 2.7),  # 中等下
            (69, 2.3), (65, 2.3),  # 及格上
            (64, 2.0), (60, 2.0),  # 及格下
            (59, 0.0), (30, 0.0), (0, 0.0),  # 不及格
        ]

        for score, expected_gpa in test_cases:
            with self.subTest(score=score):
                gpa = calculate_gpa(score)
                self.assertEqual(gpa, expected_gpa,
                                 f"成绩{score}的绩点应为{expected_gpa}，实为{gpa}")

    def test_gpa_cumulative_calculation(self):
        """测试累计平均绩点计算。"""
        from utils.gpa_calculator import calculate_cumulative_gpa

        grade_list = [
            {"gpa_point": 4.0, "credit": 3.0},  # 12.0
            {"gpa_point": 3.0, "credit": 4.0},  # 12.0
            {"gpa_point": 2.0, "credit": 3.0},  # 6.0
        ]
        # 累计 = (4*3 + 3*4 + 2*3) / (3+4+3) = 30/10 = 3.0
        gpa = calculate_cumulative_gpa(grade_list)
        self.assertEqual(gpa, 3.0)

    def test_gpa_cumulative_empty(self):
        """测试空成绩列表时累计GPA返回0.0。"""
        from utils.gpa_calculator import calculate_cumulative_gpa
        self.assertEqual(calculate_cumulative_gpa([]), 0.0)
        self.assertEqual(calculate_cumulative_gpa(None), 0.0)

    def test_gpa_cumulative_zero_credit(self):
        """测试学分为0时累计GPA返回0.0。"""
        from utils.gpa_calculator import calculate_cumulative_gpa
        grade_list = [{"gpa_point": 3.0, "credit": 0.0}]
        self.assertEqual(calculate_cumulative_gpa(grade_list), 0.0)

    def test_batch_import_mixed_data(self):
        """测试批量导入含非法数据。

        预期: 合法记录成功导入，非法记录归入fail_list。
        """
        import tempfile
        import os
        from openpyxl import Workbook

        # 创建临时Excel文件
        tmp_path = os.path.join(tempfile.gettempdir(), "test_grades.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.append(["学号", "成绩"])
        ws.append(["STU001", 85])   # 合法
        ws.append(["", 75])          # 学号为空 - 非法
        ws.append(["STU002", 101])   # 成绩超范围 - 非法
        ws.append(["STU003", 60])    # 合法
        wb.save(tmp_path)

        session_mock = MagicMock()
        self._mock_session(session_mock)

        # 选课记录查询：STU001和STU003有选课，STU002没有
        def _mock_first():
            return MagicMock()  # 默认存在

        session_mock.query.return_value.filter_by.return_value.first \
            .side_effect = lambda: MagicMock()

        from controllers.grade_controller import GradeController

        controller = GradeController()
        result = controller.batch_record_grade(
            self.teacher_id, self.plan_id, tmp_path
        )

        self.assertIn("success_count", result)
        self.assertIn("fail_list", result)
        self.assertGreater(result["fail_count"], 0,
                           "包含非法数据，fail_count应>0")

        os.remove(tmp_path)

    def test_grade_audit_approve(self):
        """测试成绩审核通过。

        预期: grade.status更新为'已更正'，score和gpa_point更新为新值。
        """
        from controllers.grade_controller import GradeController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        grade_mock = MagicMock()
        grade_mock.status = "待审核"
        grade_mock.score = 75
        grade_mock.gpa_point = 3.0
        grade_mock.modify_reason = "申请修改为85: 录入错误"

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = grade_mock

        controller = GradeController()
        result = controller.audit_grade(
            "ADMIN01", 1, "approve", "核实无误"
        )

        self.assertTrue(result["success"])
        self.assertIn("通过", result["message"])

    def test_grade_audit_reject(self):
        """测试成绩审核驳回。

        预期: grade.status恢复为'正常'，score不变。
        """
        from controllers.grade_controller import GradeController

        session_mock = MagicMock()
        self._mock_session(session_mock)

        grade_mock = MagicMock()
        grade_mock.status = "待审核"
        grade_mock.score = 75
        grade_mock.modify_reason = "申请修改为85: 录入错误"

        session_mock.query.return_value.filter_by.return_value.first \
            .return_value = grade_mock

        controller = GradeController()
        result = controller.audit_grade(
            "ADMIN01", 1, "reject", "证据不足"
        )

        self.assertTrue(result["success"])
        self.assertIn("驳回", result["message"])


if __name__ == "__main__":
    unittest.main()
