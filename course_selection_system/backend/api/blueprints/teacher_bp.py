"""teacher_bp — 教师 API。

GET  /api/teacher/plans               — 授课计划
POST /api/teacher/course-plan         — 提交新的授课计划申请
PUT  /api/teacher/course-plan/<id>    — 修改待审核的申请
GET  /api/teacher/plans/<id>/students — 选课学生名单
GET  /api/teacher/grades              — 某课程已有成绩列表
"""

from datetime import datetime
from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.controllers.teacher_controller import TeacherController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.student import Student
from backend.models.course_plan import CoursePlan
from backend.models.course import Course

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


# ── 教师申请新的授课计划 ──

@teacher_bp.route("/course-plan", methods=["POST"])
@require_auth
@require_role("teacher")
def submit_course_plan():
    data = request.get_json(silent=True) or {}
    course_id = (data.get("course_id") or "").strip()
    semester = (data.get("semester") or "").strip()
    weekday = data.get("weekday")
    period_start = data.get("period_start")
    period_count = data.get("period_count", 2)

    if not all([course_id, semester, weekday, period_start]):
        return error_response("请填写完整信息：课程、学期、上课日、起始节次")

    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        course = session.query(Course).filter_by(course_id=course_id).first()
        if not course:
            return error_response("课程代码不存在")

        plan = CoursePlan(
            course_id=course_id,
            teacher_id=g.current_user["user_id"],
            semester=semester,
            weekday=int(weekday),
            period_start=int(period_start),
            period_count=int(period_count),
            start_week=data.get("start_week", 1),
            end_week=data.get("end_week", 20),
            location=data.get("location", ""),
            capacity=data.get("capacity", 30),
            prerequisite=data.get("prerequisite", ""),
            status="待审核",
            created_at=datetime.now(),
        )
        session.add(plan)

    return success_response(message="授课计划申请已提交，等待管理员审核")


@teacher_bp.route("/course-plan/<int:plan_id>", methods=["PUT"])
@require_auth
@require_role("teacher")
def update_course_plan(plan_id):
    data = request.get_json(silent=True) or {}
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        plan = session.query(CoursePlan).filter_by(plan_id=plan_id, teacher_id=g.current_user["user_id"]).first()
        if not plan:
            return error_response("授课计划不存在或无权修改")
        if plan.status != "待审核":
            return error_response("仅可修改待审核状态的申请")

        for key in ("weekday", "period_start", "period_count", "start_week", "end_week", "location", "capacity", "prerequisite"):
            if key in data:
                setattr(plan, key, data[key])

    return success_response(message="授课计划已更新")
