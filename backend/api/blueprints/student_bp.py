"""student_bp — 学生 API。

GET /api/student/courses     — 可选课程列表
GET /api/student/my-courses  — 我的已选课程
GET /api/student/grades      — 我的成绩
GET /api/student/stats       — 学业统计
"""

from flask import Blueprint, request, g

from backend.api.response import success_response
from backend.api.auth import require_auth, require_role
from backend.controllers.student_controller import StudentController
from backend.controllers.stats_controller import StatsController

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


@student_bp.route("/courses", methods=["GET"])
@require_auth
@require_role("student")
def get_available_courses():
    semester = request.args.get("semester")
    result = StudentController().get_available_courses(semester)
    return success_response({"items": result})


@student_bp.route("/my-courses", methods=["GET"])
@require_auth
@require_role("student")
def get_my_courses():
    result = StudentController().get_my_courses(g.current_user["user_id"])
    return success_response({"items": result})


@student_bp.route("/grades", methods=["GET"])
@require_auth
@require_role("student")
def get_my_grades():
    result = StudentController().get_my_grades(g.current_user["user_id"])
    return success_response({"items": result})


@student_bp.route("/stats", methods=["GET"])
@require_auth
@require_role("student")
def get_my_stats():
    result = StatsController().get_academic_stats(g.current_user["user_id"])
    return success_response(result)
