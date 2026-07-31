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
from backend.models.base import DatabaseManager
from backend.services.semester_resolver import CurrentSemesterResolver

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


@student_bp.route("/courses", methods=["GET"])
@require_auth
@require_role("student")
def get_available_courses():
    semester = request.args.get("semester")
    if not semester:
        with DatabaseManager.get_instance().get_session() as session:
            semester = CurrentSemesterResolver.resolve(session).semester
    department = request.args.get("department")
    credit_range = request.args.get("credit_range")
    weekday = request.args.get("weekday")
    exam_type = request.args.get("exam_type")
    course_type = request.args.get("course_type")
    result = StudentController().get_available_courses(
        semester=semester,
        department=department,
        credit_range=credit_range,
        weekday=weekday,
        exam_type=exam_type,
        course_type=course_type,
    )
    return success_response({"items": result})


@student_bp.route("/my-courses", methods=["GET"])
@require_auth
@require_role("student")
def get_my_courses():
    semester = request.args.get("semester")
    if not semester:
        with DatabaseManager.get_instance().get_session() as session:
            semester_config = CurrentSemesterResolver.resolve(session)
            semester = semester_config.semester
            total_weeks = semester_config.total_weeks
    else:
        total_weeks = None
    result = StudentController().get_my_courses(g.current_user["user_id"], semester)
    return success_response({
        "items": result,
        "semester": semester,
        "total_weeks": total_weeks,
    })


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
