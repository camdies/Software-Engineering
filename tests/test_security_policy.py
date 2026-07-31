"""Regression tests for authentication revocation and route policy closure."""

import unittest
from unittest.mock import MagicMock, patch

from flask import Flask


class TestTokenVersion(unittest.TestCase):
    def _client(self, account):
        from backend.api.auth import require_auth
        from backend.api.response import success_response

        app = Flask(__name__)

        @app.get("/protected")
        @require_auth
        def protected():
            return success_response({"ok": True})

        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = account
        cm = MagicMock()
        cm.__enter__.return_value = session
        cm.__exit__.return_value = False
        db = MagicMock()
        db.get_session.return_value = cm
        return app.test_client(), db

    def test_changed_token_version_revokes_token(self):
        from backend.api.auth import create_token

        account = MagicMock(user_id="STU001", role="student", is_locked=0, token_version=2)
        client, db = self._client(account)
        token = create_token("STU001", "student", 1)
        with patch("backend.models.base.DatabaseManager.get_instance", return_value=db):
            response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["code"], "TOKEN_REVOKED")

    def test_auth_database_failure_is_503(self):
        from backend.api.auth import create_token

        client, db = self._client(MagicMock())
        db.get_session.side_effect = RuntimeError("database down")
        token = create_token("STU001", "student", 0)
        with patch("backend.models.base.DatabaseManager.get_instance", return_value=db):
            response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "AUTH_SERVICE_UNAVAILABLE")

    def test_production_rejects_placeholder_secret(self):
        from backend.api.auth import validate_jwt_configuration

        with patch.dict(
            "os.environ",
            {"EDUMGMT_JWT_SECRET": "REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS"},
        ):
            with self.assertRaises(RuntimeError):
                validate_jwt_configuration(production=True)

    def test_missing_invalid_locked_and_deleted_accounts_are_401(self):
        from backend.api.auth import create_token

        token = create_token("S001", "student", 0)
        account = MagicMock(user_id="S001", role="student", is_locked=0, token_version=0)
        client, db = self._client(account)
        self.assertEqual(client.get("/protected").status_code, 401)
        self.assertEqual(client.get(
            "/protected", headers={"Authorization": "Bearer invalid"}
        ).status_code, 401)

        session = db.get_session.return_value.__enter__.return_value
        session.query.return_value.filter_by.return_value.first.return_value = None
        with patch("backend.models.base.DatabaseManager.get_instance", return_value=db):
            response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.get_json()["code"], "ACCOUNT_NOT_FOUND")

        account.is_locked = 1
        session.query.return_value.filter_by.return_value.first.return_value = account
        with patch("backend.models.base.DatabaseManager.get_instance", return_value=db):
            response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.get_json()["code"], "ACCOUNT_LOCKED")

    def test_role_decorator_denies_unlisted_role(self):
        from backend.api.auth import require_role
        from flask import g

        app = Flask(__name__)

        @app.before_request
        def actor():
            g.current_user = {"role": "student", "user_id": "S001"}

        @app.get("/admin")
        @require_role("admin")
        def admin_only():
            return {"ok": True}

        response = app.test_client().get("/admin")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["code"], "ROLE_FORBIDDEN")


class TestAccessPolicyClosure(unittest.TestCase):
    def test_global_error_handlers_keep_stable_semantics(self):
        from backend.api.app_factory import create_app
        from backend.api.errors import ApiError
        from sqlalchemy.exc import SQLAlchemyError

        app = create_app()

        @app.get("/typed-error")
        def typed_error():
            raise ApiError("冲突", code="TEST_CONFLICT", status_code=409)

        @app.get("/database-error")
        def database_error():
            raise SQLAlchemyError("down")

        @app.get("/unexpected-error")
        def unexpected_error():
            raise RuntimeError("boom")

        client = app.test_client()
        self.assertEqual(client.get("/typed-error").status_code, 409)
        self.assertEqual(client.get("/database-error").status_code, 503)
        response = client.get("/unexpected-error")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()["code"], "INTERNAL_ERROR")

    def test_every_api_route_is_classified(self):
        from backend.api.access_manifest import ACCESS_POLICY_MANIFEST, PUBLIC_ENDPOINTS
        from backend.api.app_factory import create_app

        app = create_app()
        actual = {
            rule.endpoint for rule in app.url_map.iter_rules()
            if rule.rule.startswith("/api/")
        }
        self.assertEqual(actual, set(ACCESS_POLICY_MANIFEST))
        for endpoint in actual - set(PUBLIC_ENDPOINTS):
            with self.subTest(authenticated_endpoint=endpoint):
                self.assertTrue(
                    getattr(app.view_functions[endpoint], "_requires_auth", False),
                    f"{endpoint} is classified but missing @require_auth",
                )

    def test_plan_routes_declare_plan_policy(self):
        from backend.api.app_factory import create_app

        app = create_app()
        required = {
            "audit.handle_course_plan",
            "grade.batch_record_grade",
            "grade.record_grade",
            "stats.get_class_stats",
            "stats.get_score_distribution",
            "teacher.update_course_plan",
            "teacher.get_course_grades",
            "teacher.get_enrolled_students",
        }
        for endpoint in required:
            with self.subTest(endpoint=endpoint):
                self.assertTrue(hasattr(app.view_functions[endpoint], "_plan_access_policy"))

    def test_cross_owner_teacher_request_is_forbidden(self):
        from backend.api.access_policy import require_plan_access
        from backend.api.auth import create_token, require_auth, require_role
        from backend.api.errors import ApiError
        from backend.api.response import success_response
        from backend.models.course_plan import CoursePlan
        from backend.models.user_account import UserAccount

        app = Flask(__name__)

        @app.errorhandler(ApiError)
        def api_error(error):
            from backend.api.response import error_response
            return error_response(
                error.message, status_code=error.status_code, code=error.code
            )

        @app.get("/plans/<int:plan_id>")
        @require_auth
        @require_role("teacher")
        @require_plan_access("statistics", source="path")
        def owned_plan(plan_id):
            return success_response({"plan_id": plan_id})

        account = MagicMock(user_id="T001", role="teacher", is_locked=0, token_version=0)
        foreign_plan = MagicMock(plan_id=7, teacher_id="T002")
        session = MagicMock()

        def query(model):
            chain = MagicMock()
            chain.filter_by.return_value.first.return_value = (
                account if model is UserAccount else foreign_plan if model is CoursePlan else None
            )
            return chain

        session.query.side_effect = query
        cm = MagicMock()
        cm.__enter__.return_value = session
        cm.__exit__.return_value = False
        db = MagicMock()
        db.get_session.return_value = cm
        token = create_token("T001", "teacher", 0)
        with patch("backend.models.base.DatabaseManager.get_instance", return_value=db), patch(
            "backend.api.access_policy.DatabaseManager.get_instance", return_value=db
        ):
            response = app.test_client().get(
                "/plans/7", headers={"Authorization": f"Bearer {token}"}
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["code"], "PLAN_ACCESS_DENIED")

    def test_authorize_plan_access_all_role_paths(self):
        from backend.api.access_policy import authorize_plan_access
        from backend.api.errors import ApiError, ForbiddenError

        plan = MagicMock(plan_id=1, teacher_id="T001")
        session = MagicMock()
        plan_query = MagicMock()
        enrollment_query = MagicMock()
        session.query.side_effect = [plan_query]
        plan_query.filter_by.return_value.first.return_value = None
        with self.assertRaises(ApiError):
            authorize_plan_access(session, {"role": "admin", "user_id": "A"}, 99)

        for actor in (
            {"role": "admin", "user_id": "A"},
            {"role": "teacher", "user_id": "T001"},
        ):
            with self.subTest(actor=actor):
                session = MagicMock()
                session.query.return_value.filter_by.return_value.first.return_value = plan
                self.assertIs(authorize_plan_access(session, actor, 1), plan)

        session = MagicMock()
        session.query.side_effect = [plan_query, enrollment_query]
        plan_query.filter_by.return_value.first.return_value = plan
        enrollment_query.filter_by.return_value.first.return_value = MagicMock()
        self.assertIs(authorize_plan_access(
            session, {"role": "student", "user_id": "S001"}, 1, "read"
        ), plan)

        session = MagicMock()
        plan_query = MagicMock(); enrollment_query = MagicMock()
        session.query.side_effect = [plan_query, enrollment_query]
        plan_query.filter_by.return_value.first.return_value = plan
        enrollment_query.filter_by.return_value.first.return_value = None
        with self.assertRaises(ForbiddenError):
            authorize_plan_access(
                session, {"role": "student", "user_id": "S001"}, 1, "read"
            )

        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = plan
        with self.assertRaises(ForbiddenError):
            authorize_plan_access(
                session, {"role": "teacher", "user_id": "T999"}, 1
            )

    def test_plan_id_extraction_rejects_invalid_semantic_input(self):
        from backend.api.access_policy import _extract_plan_id
        from backend.api.errors import ApiError

        app = Flask(__name__)
        cases = [
            ("query", "/?plan_id=7", None),
            ("json", "/", {"plan_id": 8}),
            ("form", "/", None),
        ]
        with app.test_request_context("/?plan_id=7"):
            self.assertEqual(_extract_plan_id("query", "plan_id"), 7)
        with app.test_request_context("/", method="POST", json={"plan_id": 8}):
            self.assertEqual(_extract_plan_id("json", "plan_id"), 8)
        with app.test_request_context("/", method="POST", data={"plan_id": "9"}):
            self.assertEqual(_extract_plan_id("form", "plan_id"), 9)
        with app.test_request_context("/"):
            with self.assertRaises(ApiError):
                _extract_plan_id("query", "plan_id")

    def test_plan_decorator_success_and_database_failure(self):
        from backend.api.access_policy import require_plan_access
        from backend.api.errors import ApiError
        from backend.api.response import error_response

        app = Flask(__name__)

        @app.before_request
        def actor():
            from flask import g
            g.current_user = {"role": "admin", "user_id": "A001"}

        @app.errorhandler(ApiError)
        def api_error(error):
            return error_response(error.message, status_code=error.status_code, code=error.code)

        @app.get("/plans/<int:plan_id>")
        @require_plan_access("read", source="path")
        def plan_view(plan_id):
            return {"plan_id": plan_id}

        plan = MagicMock(plan_id=1)
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = plan
        cm = MagicMock()
        cm.__enter__.return_value = session
        cm.__exit__.return_value = False
        db = MagicMock()
        db.get_session.return_value = cm
        with patch("backend.api.access_policy.DatabaseManager.get_instance", return_value=db):
            self.assertEqual(app.test_client().get("/plans/1").status_code, 200)

        db.get_session.side_effect = RuntimeError("down")
        with patch("backend.api.access_policy.DatabaseManager.get_instance", return_value=db):
            response = app.test_client().get("/plans/1")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "AUTHORIZATION_SERVICE_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
