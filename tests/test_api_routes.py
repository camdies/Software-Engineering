import unittest
from unittest.mock import MagicMock, patch


class TestApiRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.api.app_factory import create_app
        cls.app = create_app()

    def setUp(self):
        from backend.models.course_plan import CoursePlan
        from backend.models.user_account import UserAccount

        self.identity = {"user_id": "S001", "role": "student", "token_version": 0}
        self.account = MagicMock(user_id="S001", role="student", is_locked=0, token_version=0)
        self.plan = MagicMock(plan_id=1, teacher_id="T001")
        session = MagicMock()

        def query(model):
            chain = MagicMock()
            if model is UserAccount:
                chain.filter_by.return_value.first.return_value = self.account
            elif model is CoursePlan:
                chain.filter_by.return_value.first.return_value = self.plan
            return chain

        session.query.side_effect = query
        cm = MagicMock(); cm.__enter__.return_value = session; cm.__exit__.return_value = False
        self.db = MagicMock(); self.db.get_session.return_value = cm
        self.patches = [
            patch("backend.models.base.DatabaseManager.get_instance", return_value=self.db),
            patch("backend.api.access_policy.DatabaseManager.get_instance", return_value=self.db),
            patch("backend.api.auth.decode_token", side_effect=lambda token: dict(self.identity)),
        ]
        for item in self.patches: item.start()
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer test"}

    def tearDown(self):
        for item in reversed(self.patches): item.stop()

    def become(self, user_id, role):
        self.identity.update(user_id=user_id, role=role)
        self.account.user_id = user_id; self.account.role = role

    def test_student_routes_use_current_semester_and_token_identity(self):
        from backend.controllers.stats_controller import StatsController
        from backend.controllers.student_controller import StudentController
        from backend.services.semester_resolver import CurrentSemesterResolver

        semester = MagicMock(semester="2026-2027-1", total_weeks=18)
        with patch.object(CurrentSemesterResolver, "resolve", return_value=semester), patch.object(
            StudentController, "get_available_courses", return_value=[]
        ) as available, patch.object(
            StudentController, "get_my_courses", return_value=[]
        ) as mine, patch.object(
            StudentController, "get_my_grades", return_value=[]
        ), patch.object(StatsController, "get_academic_stats", return_value={"total_credits": 0}):
            self.assertEqual(self.client.get("/api/student/courses", headers=self.headers).status_code, 200)
            mine_response = self.client.get("/api/student/my-courses", headers=self.headers)
            self.assertEqual(mine_response.status_code, 200)
            self.assertEqual(mine_response.get_json()["data"]["semester"], "2026-2027-1")
            self.assertEqual(self.client.get("/api/student/grades", headers=self.headers).status_code, 200)
            self.assertEqual(self.client.get("/api/student/stats", headers=self.headers).status_code, 200)
        self.assertEqual(available.call_args.kwargs["semester"], "2026-2027-1")
        mine.assert_called_once_with("S001", "2026-2027-1")

    def test_enrollment_blueprint_preserves_conflict_and_service_status(self):
        from backend.controllers.enrollment_controller import EnrollmentController

        with patch.object(EnrollmentController, "select_course", return_value={
            "success": False, "message": "课程容量已满", "code": "COURSE_FULL", "status_code": 409,
        }):
            response = self.client.post(
                "/api/enrollment/select", json={"plan_id": 1}, headers=self.headers
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "COURSE_FULL")

        with patch.object(EnrollmentController, "drop_course", return_value={
            "success": False, "message": "数据库不可用", "code": "ENROLLMENT_DB_UNAVAILABLE", "status_code": 503,
        }):
            response = self.client.post(
                "/api/enrollment/drop", json={"plan_id": 1}, headers=self.headers
            )
        self.assertEqual(response.status_code, 503)

    def test_logout_failure_is_not_reported_as_success(self):
        from backend.controllers.auth_controller import AuthController

        with patch.object(AuthController, "logout", return_value=False):
            response = self.client.post("/api/auth/logout", headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "LOGOUT_SERVICE_UNAVAILABLE")

    def test_teacher_owned_roster_route_calls_actor_aware_controller(self):
        from backend.controllers.teacher_controller import TeacherController

        self.become("T001", "teacher")
        with patch.object(TeacherController, "get_enrolled_students", return_value=[]) as roster:
            response = self.client.get("/api/teacher/plans/1/students", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        roster.assert_called_once_with("T001", 1)


if __name__ == "__main__":
    unittest.main()
