"""grade_bp — 成绩管理 API。

POST /api/grade/record        — 录入单个成绩
POST /api/grade/batch         — 批量导入 Excel 成绩
POST /api/grade/modify        — 教师提交成绩修改申请
POST /api/grade/audit/<id>    — 管理员审核成绩修改
"""

import os
import tempfile

from flask import Blueprint, request, g

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.controllers.grade_controller import GradeController

grade_bp = Blueprint("grade", __name__, url_prefix="/api/grade")


@grade_bp.route("/record", methods=["POST"])
@require_auth
@require_role("teacher")
def record_grade():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()
    plan_id = data.get("plan_id")
    score = data.get("score")

    if not student_id or not plan_id or score is None:
        return error_response("学号、课程计划ID和成绩不能为空")

    result = GradeController().record_grade(
        g.current_user["user_id"], student_id, int(plan_id), score
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "成绩录入失败"))


@grade_bp.route("/batch", methods=["POST"])
@require_auth
@require_role("teacher")
def batch_record_grade():
    plan_id = request.form.get("plan_id", type=int)
    if not plan_id:
        return error_response("请提供 plan_id")

    file = request.files.get("file")
    if not file:
        return error_response("请上传 Excel 文件")

    # 保存到临时文件
    suffix = os.path.splitext(file.filename or "temp.xlsx")[1] or ".xlsx"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        file.save(tmp.name)
        tmp.close()
        result = GradeController().batch_record_grade(
            g.current_user["user_id"], plan_id, tmp.name
        )
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    return success_response(result)


@grade_bp.route("/modify", methods=["POST"])
@require_auth
@require_role("teacher")
def apply_modify():
    data = request.get_json(silent=True) or {}
    grade_id = data.get("grade_id")
    new_score = data.get("new_score")
    reason = data.get("reason") or ""

    if not grade_id or new_score is None:
        return error_response("成绩ID和新成绩不能为空")

    result = GradeController().apply_grade_modify(
        g.current_user["user_id"], int(grade_id), new_score, reason
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "修改申请失败"))


@grade_bp.route("/audit/<int:grade_id>", methods=["POST"])
@require_auth
@require_role("admin")
def audit_grade(grade_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action")  # 'approve' or 'reject'
    comment = data.get("comment") or ""

    if action not in ("approve", "reject"):
        return error_response("请选择审核操作 (approve/reject)")

    result = GradeController().audit_grade(
        g.current_user["user_id"], grade_id, action, comment
    )
    if result.get("success"):
        return success_response(message=result["message"])
    return error_response(result.get("message", "审核操作失败"))
