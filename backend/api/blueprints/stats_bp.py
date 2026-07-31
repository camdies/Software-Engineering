"""stats_bp — 统计分析 API。

GET  /api/stats/class/<plan_id>      — 班级成绩统计
GET  /api/stats/distribution/<plan_id> — 成绩分布
GET  /api/stats/gpa-trend            — GPA趋势 (学生用)
POST /api/stats/export               — 统计数据导出 Excel
"""

import io
import os
import tempfile

from flask import Blueprint, request, g, send_file

from backend.api.response import success_response, error_response
from backend.api.auth import require_auth, require_role
from backend.api.access_policy import authorize_plan_access, require_plan_access
from backend.utils.export_util import ExportError
from backend.controllers.stats_controller import StatsController
from backend.models.base import DatabaseManager

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("/class/<int:plan_id>", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
@require_plan_access("statistics", source="path")
def get_class_stats(plan_id):
    class_name = request.args.get("class_name")
    result = StatsController().get_class_stats(
        g.current_user, plan_id, class_name
    )
    return success_response(result)


@stats_bp.route("/distribution/<int:plan_id>", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
@require_plan_access("statistics", source="path")
def get_score_distribution(plan_id):
    result = StatsController().get_score_distribution(g.current_user, plan_id)
    return success_response(result)


@stats_bp.route("/gpa-trend", methods=["GET"])
@require_auth
@require_role("student", "admin")
def get_gpa_trend():
    requested = request.args.get("student_id")
    if g.current_user["role"] == "student" and requested:
        return error_response(
            "学生接口不接受 student_id",
            status_code=422,
            code="TARGET_ID_NOT_ALLOWED",
        )
    student_id = requested if g.current_user["role"] == "admin" else g.current_user["user_id"]
    result = StatsController().get_gpa_trend(student_id)
    return success_response(result)


@stats_bp.route("/export", methods=["POST"])
@require_auth
def export_stats():
    data = request.get_json(silent=True) or {}
    export_type = data.get("type", "class")
    role = g.current_user["role"]
    actor_id = g.current_user["user_id"]
    student_id = None

    sd = None
    if export_type == "class":
        plan_id = data.get("plan_id")
        class_name = data.get("class_name")
        if not plan_id:
            return error_response("请提供 plan_id")
        if role not in {"teacher", "admin"}:
            return error_response("无权导出班级统计", status_code=403, code="ROLE_FORBIDDEN")
        with DatabaseManager.get_instance().get_session() as session:
            authorize_plan_access(session, g.current_user, int(plan_id), "statistics_export")
        sd = StatsController().get_class_stats(g.current_user, int(plan_id), class_name)
    elif export_type == "academic":
        if role == "teacher":
            return error_response("无权导出学生学业数据", status_code=403, code="ROLE_FORBIDDEN")
        if role == "student" and data.get("student_id"):
            return error_response("学生接口不接受 student_id", status_code=422, code="TARGET_ID_NOT_ALLOWED")
        student_id = data.get("student_id") if role == "admin" else actor_id
        if role == "admin" and (not student_id or not (data.get("reason") or "").strip()):
            return error_response("管理员代导出必须提供目标学生和原因", status_code=422, code="DELEGATED_EXPORT_REASON_REQUIRED")
        sd = StatsController().get_academic_stats(student_id)
    elif export_type == "schedule":
        if role == "teacher":
            return error_response("无权导出学生课表", status_code=403, code="ROLE_FORBIDDEN")
        if role == "student" and data.get("student_id"):
            return error_response("学生接口不接受 student_id", status_code=422, code="TARGET_ID_NOT_ALLOWED")
        student_id = data.get("student_id") if role == "admin" else actor_id
        if role == "admin" and (not student_id or not (data.get("reason") or "").strip()):
            return error_response("管理员代导出必须提供目标学生和原因", status_code=422, code="DELEGATED_EXPORT_REASON_REQUIRED")
        sd = StatsController().get_schedule_data(student_id, data.get("semester"))
    else:
        return error_response("不支持的导出类型", status_code=422, code="EXPORT_TYPE_INVALID")

    try:
        with tempfile.TemporaryDirectory(prefix="edumgmt-export-") as temp_dir:
            path = os.path.join(temp_dir, "export.xlsx")
            StatsController().export_stats_to_excel(sd, path)
            with open(path, "rb") as export_file:
                blob = export_file.read()
    except ExportError:
        if role == "admin" and export_type in {"academic", "schedule"}:
            _write_delegated_export_audit(
                actor_id, student_id, export_type, data.get("semester"),
                data.get("reason") or "", result="失败",
            )
        return error_response("导出文件生成失败", status_code=500, code="EXPORT_FAILED")

    if role == "admin" and export_type in {"academic", "schedule"}:
        _write_delegated_export_audit(
            actor_id, student_id, export_type, data.get("semester"), data["reason"],
            result="成功",
        )

    return send_file(
        io.BytesIO(blob),
        as_attachment=True,
        download_name=f"stats_{export_type}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _write_delegated_export_audit(
    actor_id, target_id, export_type, semester, reason, *, result
):
    from datetime import datetime
    from backend.models.operation_log import OperationLog

    with DatabaseManager.get_instance().get_session() as session:
        session.add(OperationLog(
            user_id=actor_id,
            log_type="导出",
            operation=(
                f"管理员代导出学生数据: target={target_id}; type={export_type}"
            )[:200],
            result=result,
            log_time=datetime.now(),
            ip_address=request.remote_addr or "",
            target_id=target_id,
            resource_type=export_type,
            semester=semester or "",
            reason=reason,
            request_id=g.request_id,
        ))
