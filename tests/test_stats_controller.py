import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from openpyxl import load_workbook


class TestStatsController(unittest.TestCase):
    def controller(self, session=None):
        from backend.controllers.stats_controller import StatsController

        controller = StatsController.__new__(StatsController)
        db = MagicMock()
        if session is not None:
            cm = MagicMock()
            cm.__enter__.return_value = session
            cm.__exit__.return_value = False
            db.get_session.return_value = cm
        controller._db = db
        return controller

    def test_schedule_uses_explicit_semester_and_shared_grid(self):
        course = {
            "plan_id": 1, "course_id": "CS101", "course_name": "程序设计",
            "semester": "2026-2027-1", "weekday": 1, "period_start": 1,
            "period_count": 2, "start_week": 1, "end_week": 18, "location": "A101",
        }
        student_controller = MagicMock()
        student_controller.get_my_courses.return_value = [course]
        with patch(
            "backend.controllers.student_controller.StudentController",
            return_value=student_controller,
        ):
            result = self.controller().get_schedule_data("S001", "2026-2027-1")
        student_controller.get_my_courses.assert_called_once_with("S001", "2026-2027-1")
        self.assertIn("C2:C3", result["merge_ranges"])

    def test_schedule_default_uses_current_semester_resolver(self):
        from backend.controllers.student_controller import StudentController
        from backend.services.semester_resolver import CurrentSemesterResolver

        student_controller = MagicMock()
        student_controller.get_my_courses.return_value = []
        semester = MagicMock(semester="2026-2027-1")
        session = MagicMock()
        controller = self.controller(session)
        with patch.object(CurrentSemesterResolver, "resolve", return_value=semester), patch(
            "backend.controllers.student_controller.StudentController",
            return_value=student_controller,
        ):
            result = controller.get_schedule_data("S001")
        self.assertEqual(result["semester"], "2026-2027-1")
        student_controller.get_my_courses.assert_called_once_with("S001", "2026-2027-1")

    def test_score_distribution_excludes_unrecorded_scores(self):
        from backend.models.course_plan import CoursePlan
        from backend.models.grade import Grade

        plan = MagicMock(plan_id=1)
        grade_95 = MagicMock(score=95)
        grade_80 = MagicMock(score=80)
        grade_65 = MagicMock(score=65)
        grade_40 = MagicMock(score=40)
        grade_none = MagicMock(score=None)
        session = MagicMock()

        def query(model):
            chain = MagicMock()
            if model is CoursePlan:
                chain.filter_by.return_value.first.return_value = plan
            elif model is Grade:
                chain.filter_by.return_value.all.return_value = [
                    grade_95, grade_80, grade_65, grade_40, grade_none,
                ]
            return chain

        session.query.side_effect = query
        result = self.controller(session).get_score_distribution(
            {"role": "admin", "user_id": "A001"}, 1
        )
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["excellent"]["count"], 1)
        self.assertEqual(result["fail"]["count"], 1)

    def test_controller_exports_all_supported_shapes(self):
        controller = self.controller()
        cases = [
            ({"rank_list": [{"rank": 1, "student_id": "S1", "name": "学生", "score": 90}]}, "成绩排名", "A2", 1),
            ({"failed_courses": [{"course_name": "课程", "score": 50, "semester": "2026-1"}]}, "学业统计", "A2", "课程"),
            ({"schedule": [["第1节", "08:30", "课程", "", "", "", "", "", ""]], "merge_ranges": []}, "个人课表", "C2", "课程"),
        ]
        for data, sheet_name, cell, expected in cases:
            with self.subTest(sheet=sheet_name), tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "out.xlsx")
                controller.export_stats_to_excel(data, path)
                workbook = load_workbook(path)
                self.assertEqual(workbook[sheet_name][cell].value, expected)
                workbook.close()

    def test_unsupported_export_raises_typed_error(self):
        from backend.utils.export_util import ExportError

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ExportError):
                self.controller().export_stats_to_excel({}, os.path.join(directory, "x.xlsx"))


if __name__ == "__main__":
    unittest.main()
