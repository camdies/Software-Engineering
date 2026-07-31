"""Black-box role, ownership, export boundary, and error-semantic tests."""

import unittest
from unittest.mock import MagicMock, patch

from openpyxl import Workbook


class TestStatsApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.api.app_factory import create_app
        cls.app = create_app()

    def setUp(self):
        from backend.models.course_plan import CoursePlan
        from backend.models.user_account import UserAccount

        self.identity = {"user_id": "S001", "role": "student", "token_version": 0}
        self.account = MagicMock(user_id="S001", role="student", is_locked=0, token_version=0)
        self.plan = MagicMock(plan_id=7, teacher_id="T001")
        session = MagicMock()

        def query(model):
            chain = MagicMock()
            if model is UserAccount:
                chain.filter_by.return_value.first.return_value = self.account
            elif model is CoursePlan:
                chain.filter_by.return_value.first.return_value = self.plan
            return chain

        session.query.side_effect = query
        cm = MagicMock()
        cm.__enter__.return_value = session
        cm.__exit__.return_value = False
        self.db = MagicMock()
        self.db.get_session.return_value = cm
        self.db_patch = patch("backend.models.base.DatabaseManager.get_instance", return_value=self.db)
        self.policy_db_patch = patch("backend.api.access_policy.DatabaseManager.get_instance", return_value=self.db)
        self.decode_patch = patch(
            "backend.api.auth.decode_token", side_effect=lambda token: dict(self.identity)
        )
        self.db_patch.start(); self.policy_db_patch.start(); self.decode_patch.start()
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer test"}

    def tearDown(self):
        self.decode_patch.stop(); self.policy_db_patch.stop(); self.db_patch.stop()

    def become(self, user_id, role):
        self.identity.update(user_id=user_id, role=role)
        self.account.user_id = user_id
        self.account.role = role

    @staticmethod
    def write_workbook(stats, path):
        workbook = Workbook()
        workbook.active["A1"] = "ok"
        workbook.save(path)
        return path

    def test_student_identity_cannot_be_overridden(self):
        response = self.client.get("/api/stats/gpa-trend?student_id=S999", headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()["code"], "TARGET_ID_NOT_ALLOWED")
        response = self.client.post(
            "/api/stats/export",
            json={"type": "schedule", "student_id": "S999"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_teacher_cross_owner_stats_is_forbidden(self):
        self.become("T999", "teacher")
        response = self.client.get("/api/stats/class/7", headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["code"], "PLAN_ACCESS_DENIED")

    def test_teacher_owned_stats_and_export_succeed(self):
        from backend.controllers.stats_controller import StatsController

        self.become("T001", "teacher")
        with patch.object(StatsController, "get_class_stats", return_value={"rank_list": []}):
            response = self.client.get("/api/stats/class/7", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        with patch.object(StatsController, "get_score_distribution", return_value={"total": 0}):
            response = self.client.get("/api/stats/distribution/7", headers=self.headers)
            self.assertEqual(response.status_code, 200)
        with patch.object(StatsController, "get_class_stats", return_value={"rank_list": []}), patch.object(
            StatsController, "export_stats_to_excel", side_effect=self.write_workbook
        ):
            response = self.client.post(
                "/api/stats/export", json={"type": "class", "plan_id": 7}, headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data.startswith(b"PK"))

    def test_export_role_and_semantic_rejections(self):
        response = self.client.post(
            "/api/stats/export", json={"type": "class", "plan_id": 7}, headers=self.headers
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            "/api/stats/export", json={"type": "unknown"}, headers=self.headers
        )
        self.assertEqual(response.status_code, 422)

        self.become("T001", "teacher")
        response = self.client.post(
            "/api/stats/export", json={"type": "academic"}, headers=self.headers
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            "/api/stats/export", json={"type": "class"}, headers=self.headers
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_delegated_export_requires_reason_and_is_audited(self):
        from backend.controllers.stats_controller import StatsController

        self.become("A001", "admin")
        response = self.client.post(
            "/api/stats/export",
            json={"type": "academic", "student_id": "S001"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 422)
        with patch.object(StatsController, "get_academic_stats", return_value={"failed_courses": []}), patch.object(
            StatsController, "export_stats_to_excel", side_effect=self.write_workbook
        ), patch("backend.models.operation_log.OperationLog", return_value=MagicMock()):
            response = self.client.post(
                "/api/stats/export",
                json={"type": "academic", "student_id": "S001", "reason": "教务复核"},
                headers=self.headers,
            )
        self.assertEqual(response.status_code, 200)

    def test_export_failure_returns_json_500_even_for_download_request(self):
        from backend.controllers.stats_controller import StatsController
        from backend.utils.export_util import ExportError

        with patch.object(StatsController, "get_schedule_data", return_value={"schedule": []}), patch.object(
            StatsController, "export_stats_to_excel", side_effect=ExportError("bad")
        ):
            response = self.client.post(
                "/api/stats/export", json={"type": "schedule"}, headers=self.headers
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["code"], "EXPORT_FAILED")


if __name__ == "__main__":
    unittest.main()
