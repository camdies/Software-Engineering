"""teacher_bp — 教师 API。

GET /api/teacher/plans               — 授课计划
GET /api/teacher/plans/<id>/students — 选课学生名单
GET /api/teacher/grades              — 某课程已有成绩列表
"""

from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.controllers.teacher_controller import TeacherController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.student import Student

teacher_bp = Blueprint("teacher", __name__, url_prefix="/api/teacher")


@teacher_bp.route("/plans", methods=["GET"])
@require_auth
@require_role("teacher")
def get_teaching_plans():
    semester = request.args.get("semester")
    result = TeacherController().get_teaching_plans(
        g.current_user["user_id"], semester
    )
    return success_response({"items": result})


@teacher_bp.route("/plans/<int:plan_id>/students", methods=["GET"])
@require_auth
@require_role("teacher")
def get_enrolled_students(plan_id):
    result = TeacherController().get_enrolled_students(plan_id)
    return success_response({"items": result})


@teacher_bp.route("/grades", methods=["GET"])
@require_auth
@require_role("teacher")
def get_course_grades():
    """获取某课程下所有学生的成绩（含已录入和未录入）。"""
    plan_id = request.args.get("plan_id", type=int)
    if not plan_id:
        return error_response("请提供 plan_id")

    with DatabaseManager.get_instance().get_session() as session:
        # 已选该课程的学生
        from backend.models.enrollment import Enrollment
        enrollments = (
            session.query(Enrollment)
            .filter_by(plan_id=plan_id, status="已选")
            .all()
        )
        data = []
        for e in enrollments:
            student = session.query(Student).filter_by(student_id=e.student_id).first()
            grade = session.query(Grade).filter_by(
                student_id=e.student_id, plan_id=plan_id
            ).first()
            data.append({
                "student_id": e.student_id,
                "name": student.name if student else "",
                "enroll_id": e.enroll_id,
                "score": grade.score if grade else None,
                "gpa_point": float(grade.gpa_point) if grade and grade.gpa_point else None,
                "grade_id": grade.grade_id if grade else None,
                "grade_status": grade.status if grade else "未录入",
            })
    return success_response({"items": data})
