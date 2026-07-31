import unittest
from unittest.mock import MagicMock, patch


class TestControllerFailClosed(unittest.TestCase):
    def test_student_read_failures_propagate(self):
        from backend.controllers.student_controller import StudentController

        controller = StudentController.__new__(StudentController)
        controller._db = MagicMock()
        controller._db.get_session.side_effect = RuntimeError("database down")
        for method, args in (
            (controller.get_available_courses, ()),
            (controller.get_my_courses, ("S001",)),
            (controller.get_my_grades, ("S001",)),
        ):
            with self.subTest(method=method.__name__), self.assertRaises(RuntimeError):
                method(*args)

    def test_teacher_read_failures_propagate(self):
        from backend.controllers.teacher_controller import TeacherController

        controller = TeacherController.__new__(TeacherController)
        controller._db = MagicMock()
        controller._db.get_session.side_effect = RuntimeError("database down")
        with self.assertRaises(RuntimeError):
            controller.get_teaching_plans("T001")
        with self.assertRaises(RuntimeError):
            controller.get_enrolled_students("T001", 1)

    def test_grade_controller_rechecks_plan_owner(self):
        from backend.controllers.grade_controller import GradeController

        controller = GradeController.__new__(GradeController)
        session = MagicMock()
        plan = MagicMock(teacher_id="T002")
        session.query.return_value.filter_by.return_value.first.return_value = plan
        cm = MagicMock(); cm.__enter__.return_value = session; cm.__exit__.return_value = False
        controller._db = MagicMock(); controller._db.get_session.return_value = cm
        result = controller.record_grade("T001", "S001", 1, 80)
        self.assertFalse(result["success"])
        self.assertIn("无权", result["message"])

    def test_stats_empty_results_are_valid_but_database_errors_propagate(self):
        from backend.controllers.stats_controller import StatsController
        from backend.models.course_plan import CoursePlan
        from backend.models.grade import Grade

        plan = MagicMock(plan_id=1)
        session = MagicMock()

        def query(model):
            chain = MagicMock()
            if model is CoursePlan:
                chain.filter_by.return_value.first.return_value = plan
            elif model is Grade:
                chain.join.return_value.filter.return_value.all.return_value = []
            return chain

        session.query.side_effect = query
        cm = MagicMock(); cm.__enter__.return_value = session; cm.__exit__.return_value = False
        controller = StatsController.__new__(StatsController)
        controller._db = MagicMock(); controller._db.get_session.return_value = cm
        result = controller.get_class_stats({"role": "admin", "user_id": "A"}, 1)
        self.assertEqual(result["rank_list"], [])

        controller._db.get_session.side_effect = RuntimeError("database down")
        with self.assertRaises(RuntimeError):
            controller.get_academic_stats("S001")
        with self.assertRaises(RuntimeError):
            controller.get_gpa_trend("S001")


if __name__ == "__main__":
    unittest.main()
