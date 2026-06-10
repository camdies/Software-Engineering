"""admin_bp — 管理员 API。

GET    /api/admin/students           — 分页查询学生
POST   /api/admin/students           — 创建学生
PUT    /api/admin/students/<id>      — 更新学生
DELETE /api/admin/students/<id>      — 删除学生

GET    /api/admin/teachers           — 分页查询教师
POST   /api/admin/teachers           — 创建教师
PUT    /api/admin/teachers/<id>      — 更新教师
DELETE /api/admin/teachers/<id>      — 删除教师

GET    /api/admin/courses            — 分页查询课程
POST   /api/admin/courses            — 创建课程
PUT    /api/admin/courses/<id>       — 更新课程
DELETE /api/admin/courses/<id>       — 删除课程

GET    /api/admin/course-plans       — 查询开课计划
POST   /api/admin/enrollment-control — 设置选课时段
GET    /api/admin/enrollment-stats   — 选课统计

GET    /api/admin/logs               — 操作日志
GET    /api/admin/grades/pending     — 待审核成绩列表
"""

from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.controllers.admin_controller import AdminController
from backend.controllers.enrollment_controller import EnrollmentController
from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.grade import Grade
from backend.models.course import Course

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── Student CRUD ──

@admin_bp.route("/students", methods=["GET"])
@require_auth
@require_role("admin")
def get_students():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    student_id = request.args.get("student_id")
    name = request.args.get("name")
    class_name = request.args.get("class_name")
    result = AdminController().get_students(page, page_size, student_id, name, class_name)
    return success_response(result)


@admin_bp.route("/students", methods=["POST"])
@require_auth
@require_role("admin")
def create_student():
    data = request.get_json(silent=True) or {}
    sid = (data.get("student_id") or "").strip()
    name = (data.get("name") or "").strip()
    if not sid or not name:
        return error_response("学号和姓名不能为空")
    result = AdminController().create_student(
        sid, name, data.get("major"), data.get("class_name"), data.get("contact")
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "创建失败"))


@admin_bp.route("/students/<student_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_student(student_id):
    data = request.get_json(silent=True) or {}
    result = AdminController().update_student(student_id, **data)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "更新失败"))


@admin_bp.route("/students/<student_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_student(student_id):
    result = AdminController().delete_student(student_id)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "删除失败"))


# ── Teacher CRUD ──

@admin_bp.route("/teachers", methods=["GET"])
@require_auth
@require_role("admin")
def get_teachers():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    teacher_id = request.args.get("teacher_id")
    name = request.args.get("name")
    college = request.args.get("college")
    result = AdminController().get_teachers(page, page_size, teacher_id, name, college)
    return success_response(result)


@admin_bp.route("/teachers", methods=["POST"])
@require_auth
@require_role("admin")
def create_teacher():
    data = request.get_json(silent=True) or {}
    tid = (data.get("teacher_id") or "").strip()
    name = (data.get("name") or "").strip()
    if not tid or not name:
        return error_response("工号和姓名不能为空")
    result = AdminController().create_teacher(
        tid, name, data.get("college"), data.get("contact")
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "创建失败"))


@admin_bp.route("/teachers/<teacher_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_teacher(teacher_id):
    data = request.get_json(silent=True) or {}
    result = AdminController().update_teacher(teacher_id, **data)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "更新失败"))


@admin_bp.route("/teachers/<teacher_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_teacher(teacher_id):
    result = AdminController().delete_teacher(teacher_id)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "删除失败"))


# ── Course CRUD ──

@admin_bp.route("/courses", methods=["GET"])
@require_auth
@require_role("admin")
def get_courses():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    course_id = request.args.get("course_id")
    course_name = request.args.get("course_name")
    result = AdminController().get_courses(page, page_size, course_id, course_name)
    return success_response(result)


@admin_bp.route("/courses", methods=["POST"])
@require_auth
@require_role("admin")
def create_course():
    data = request.get_json(silent=True) or {}
    cid = (data.get("course_id") or "").strip()
    name = (data.get("course_name") or "").strip()
    if not cid or not name:
        return error_response("课程代码和课程名称不能为空")
    result = AdminController().create_course(
        cid, name, data.get("credit"), data.get("hours"), data.get("exam_type")
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "创建失败"))


@admin_bp.route("/courses/<course_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_course(course_id):
    data = request.get_json(silent=True) or {}
    result = AdminController().update_course(course_id, **data)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "更新失败"))


@admin_bp.route("/courses/<course_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_course(course_id):
    result = AdminController().delete_course(course_id)
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "删除失败"))


# ── Course Plans ──

@admin_bp.route("/course-plans", methods=["GET"])
@require_auth
@require_role("admin")
def get_course_plans():
    semester = request.args.get("semester")
    with DatabaseManager.get_instance().get_session() as session:
        query = session.query(CoursePlan)
        if semester:
            query = query.filter(CoursePlan.semester == semester)
        plans = query.order_by(CoursePlan.plan_id.desc()).all()
        data = []
        for p in plans:
            course = session.query(Course).filter_by(course_id=p.course_id).first()
            d = p.to_dict()
            d["course_name"] = course.course_name if course else ""
            data.append(d)
    return success_response({"items": data})


# ── Enrollment Control ──

@admin_bp.route("/enrollment-control", methods=["GET"])
@require_auth
@require_role("admin")
def get_enrollment_control():
    from backend.config.settings import Settings
    s = Settings.get_instance()
    return success_response({
        "is_open": s.enrollment_is_open,
        "open_time": s.enrollment_open_time,
        "close_time": s.enrollment_close_time,
    })


@admin_bp.route("/enrollment-control", methods=["POST"])
@require_auth
@require_role("admin")
def set_enrollment_control():
    data = request.get_json(silent=True) or {}
    is_open = data.get("is_open", False)
    open_time = data.get("open_time", "")
    close_time = data.get("close_time", "")
    # 写回 config.ini
    import configparser, os
    from backend.config.settings import Settings as _S
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "config", "config.ini")
    config_path = os.path.normpath(config_path)
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    if "enrollment" not in cfg:
        cfg.add_section("enrollment")
    cfg.set("enrollment", "is_open", str(is_open).lower())
    if open_time:
        cfg.set("enrollment", "open_time", open_time)
    if close_time:
        cfg.set("enrollment", "close_time", close_time)
    with open(config_path, "w", encoding="utf-8") as f:
        cfg.write(f)
    # 刷新 Settings 单例中的缓存
    _S.get_instance()._config = cfg
    return success_response(message="选课时段设置已更新")


# ── Enrollment Statistics ──

@admin_bp.route("/enrollment-stats", methods=["GET"])
@require_auth
@require_role("admin")
def get_enrollment_stats():
    semester = request.args.get("semester")
    from backend.models.enrollment import Enrollment
    with DatabaseManager.get_instance().get_session() as session:
        query = session.query(CoursePlan)
        if semester:
            query = query.filter(CoursePlan.semester == semester)
        plans = query.all()
        stats = []
        for p in plans:
            course = session.query(Course).filter_by(course_id=p.course_id).first()
            enrolled_count = (
                session.query(Enrollment)
                .filter_by(plan_id=p.plan_id, status="已选")
                .count()
            )
            stats.append({
                "plan_id": p.plan_id,
                "course_id": p.course_id,
                "course_name": course.course_name if course else "",
                "teacher_id": p.teacher_id,
                "semester": p.semester,
                "capacity": p.capacity,
                "enrolled": enrolled_count,
            })
    return success_response({"items": stats})


# ── Pending Grades for Audit ──

@admin_bp.route("/grades/pending", methods=["GET"])
@require_auth
@require_role("admin")
def get_pending_grades():
    with DatabaseManager.get_instance().get_session() as session:
        grades = (
            session.query(Grade)
            .filter(Grade.status == "待审核")
            .all()
        )
        data = []
        for g in grades:
            plan = session.query(CoursePlan).filter_by(plan_id=g.plan_id).first()
            course = session.query(Course).filter_by(course_id=plan.course_id).first() if plan else None
            data.append({
                **g.to_dict(),
                "course_name": course.course_name if course else "",
                "semester": plan.semester if plan else "",
            })
    return success_response({"items": data})


# ── Operation Logs ──

@admin_bp.route("/logs", methods=["GET"])
@require_auth
@require_role("admin")
def get_logs():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    user_id = request.args.get("user_id")
    log_type = request.args.get("log_type")
    result = AdminController().get_logs(page, page_size, user_id, log_type)
    return success_response(result)
