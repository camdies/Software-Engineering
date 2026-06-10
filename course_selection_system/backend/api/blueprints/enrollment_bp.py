"""enrollment_bp — 选课/退课 API。

POST /api/enrollment/select  — 选课
POST /api/enrollment/drop    — 退课
"""

from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.controllers.enrollment_controller import EnrollmentController

enrollment_bp = Blueprint("enrollment", __name__, url_prefix="/api/enrollment")


@enrollment_bp.route("/select", methods=["POST"])
@require_auth
@require_role("student")
def select_course():
    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id")
    if not plan_id:
        return error_response("请提供课程计划ID")

    result = EnrollmentController().select_course(
        g.current_user["user_id"], int(plan_id)
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "选课失败"))


@enrollment_bp.route("/drop", methods=["POST"])
@require_auth
@require_role("student")
def drop_course():
    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id")
    if not plan_id:
        return error_response("请提供课程计划ID")

    result = EnrollmentController().drop_course(
        g.current_user["user_id"], int(plan_id)
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "退课失败"))
