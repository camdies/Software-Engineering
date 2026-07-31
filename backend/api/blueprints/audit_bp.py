"""audit_bp — 管理员审核中心 API。

统一管理三种审核：
- GET  /api/audit/password-resets     — 密码重置申请列表
- POST /api/audit/password-resets/<id> — 处理密码重置
- GET  /api/audit/course-plans        — 授课计划审核列表
- POST /api/audit/course-plans/<id>   — 处理授课计划审核
- GET  /api/audit/overview             — 待处理数量统计
"""

from datetime import datetime
from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.api.access_policy import require_plan_access
from backend.models.base import DatabaseManager
from backend.models.password_reset_request import PasswordResetRequest
from backend.models.user_account import UserAccount
from backend.models.course_plan import CoursePlan
from backend.models.course import Course
from backend.models.teacher import Teacher
from backend.models.grade import Grade
from backend.models.operation_log import OperationLog
from backend.utils.auth_util import hash_password
from backend.config.settings import Settings

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")


@audit_bp.route("/overview", methods=["GET"])
@require_auth
@require_role("admin")
def get_overview():
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        pending_pwd = session.query(PasswordResetRequest).filter_by(status="待审核").count()
        pending_grades = session.query(Grade).filter_by(status="待审核").count()
        pending_plans = session.query(CoursePlan).filter_by(status="待审核").count()
    return success_response({
        "password_resets": pending_pwd,
        "grade_modifications": pending_grades,
        "course_plans": pending_plans,
    })


# ── 密码重置审核 ──

@audit_bp.route("/password-resets", methods=["GET"])
@require_auth
@require_role("admin")
def get_password_resets():
    status = request.args.get("status", "待审核")
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        requests_q = (
            session.query(PasswordResetRequest)
            .filter_by(status=status)
            .order_by(PasswordResetRequest.request_time.desc())
            .all()
        )
        data = [r.to_dict() for r in requests_q]
    return success_response({"items": data})


@audit_bp.route("/password-resets/<int:request_id>", methods=["POST"])
@require_auth
@require_role("admin")
def handle_password_reset(request_id):
    body = request.get_json(silent=True) or {}
    action = body.get("action")  # approve / reject
    comment = body.get("comment", "")
    admin_id = body.get("admin_id", g.current_user["user_id"])

    if action not in ("approve", "reject"):
        return error_response("请选择 approve 或 reject")

    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        reset_req = session.query(PasswordResetRequest).filter_by(request_id=request_id).first()
        if not reset_req:
            return error_response("申请不存在")
        if reset_req.status != "待审核":
            return error_response("该申请已处理")

        if action == "approve":
            user = session.query(UserAccount).filter_by(user_id=reset_req.user_id).first()
            if user:
                if reset_req.new_password:
                    user.password_hash = reset_req.new_password
                else:
                    user.password_hash = hash_password(Settings.get_instance().default_password)
                user.is_locked = 0
                user.login_fail_count = 0
                user.token_version = int(user.token_version or 0) + 1
            reset_req.status = "已通过"
            log_msg = f"审核通过密码重置: user={reset_req.user_id}"
        else:
            reset_req.status = "已驳回"
            log_msg = f"驳回密码重置: user={reset_req.user_id}"

        reset_req.admin_id = admin_id
        reset_req.process_time = datetime.now()
        if comment:
            reset_req.comment = comment

        session.add(OperationLog(
            user_id=admin_id, log_type="审核",
            operation=log_msg, result="成功",
            log_time=datetime.now(),
        ))

    return success_response(message=f"已{action == 'approve' and '通过' or '驳回'}")


# ── 授课计划审核 ──

@audit_bp.route("/course-plans", methods=["GET"])
@require_auth
@require_role("admin")
def get_course_plan_audit_list():
    status = request.args.get("status", "待审核")
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        plans = (
            session.query(CoursePlan)
            .filter_by(status=status)
            .order_by(CoursePlan.created_at.desc())
            .all()
        )
        data = []
        for p in plans:
            course = session.query(Course).filter_by(course_id=p.course_id).first()
            teacher = session.query(Teacher).filter_by(teacher_id=p.teacher_id).first()
            d = p.to_dict()
            d["course_name"] = course.course_name if course else ""
            d["teacher_name"] = teacher.name if teacher else ""
            data.append(d)
    return success_response({"items": data})


@audit_bp.route("/course-plans/<int:plan_id>", methods=["POST"])
@require_auth
@require_role("admin")
@require_plan_access("audit", source="path")
def handle_course_plan(plan_id):
    body = request.get_json(silent=True) or {}
    action = body.get("action")
    comment = body.get("comment", "")

    if action not in ("approve", "reject"):
        return error_response("请选择 approve 或 reject")

    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        cplan = session.query(CoursePlan).filter_by(plan_id=plan_id).first()
        if not cplan:
            return error_response("授课计划不存在")
        if cplan.status != "待审核":
            return error_response("该计划已处理")

        cplan.status = "已通过" if action == "approve" else "已驳回"
        if comment:
            cplan.audit_comment = comment

        log_msg = f"审核{'通过' if action == 'approve' else '驳回'}授课计划: plan_id={plan_id}, course={cplan.course_id}"
        session.add(OperationLog(
            user_id=g.current_user["user_id"], log_type="审核",
            operation=log_msg, result="成功",
            log_time=datetime.now(),
        ))

    return success_response(message=f"已{action == 'approve' and '通过' or '驳回'}")
