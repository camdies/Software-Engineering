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
from backend.controllers.stats_controller import StatsController
from backend.models.base import DatabaseManager

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("/class/<int:plan_id>", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
def get_class_stats(plan_id):
    class_name = request.args.get("class_name")
    result = StatsController().get_class_stats(
        g.current_user["user_id"], plan_id, class_name
    )
    return success_response(result)


@stats_bp.route("/distribution/<int:plan_id>", methods=["GET"])
@require_auth
@require_role("teacher", "admin")
def get_score_distribution(plan_id):
    result = StatsController().get_score_distribution(plan_id)
    return success_response(result)


@stats_bp.route("/gpa-trend", methods=["GET"])
@require_auth
@require_role("student", "teacher", "admin")
def get_gpa_trend():
    student_id = request.args.get("student_id") or g.current_user["user_id"]
    result = StatsController().get_gpa_trend(student_id)
    return success_response(result)


@stats_bp.route("/export", methods=["POST"])
@require_auth
def export_stats():
    data = request.get_json(silent=True) or {}
    export_type = data.get("type", "class")

    sd = None
    if export_type == "class":
        plan_id = data.get("plan_id")
        class_name = data.get("class_name")
        if not plan_id:
            return error_response("请提供 plan_id")
        sd = StatsController().get_class_stats(
            g.current_user["user_id"], int(plan_id), class_name
        )
    elif export_type == "academic":
        student_id = data.get("student_id") or g.current_user["user_id"]
        sd = StatsController().get_academic_stats(student_id)
    elif export_type == "schedule":
        student_id = data.get("student_id") or g.current_user["user_id"]
        sd = StatsController().get_schedule_data(student_id)
    else:
        return error_response("不支持的导出类型")

    # Use mkstemp so we can close the fd before openpyxl writes to the
    # file — NamedTemporaryFile keeps the handle open, which blocks
    # concurrent writes on Windows (mandatory file locking).
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    try:
        StatsController().export_stats_to_excel(sd, path)
        # Read into memory so we can delete the temp file immediately.
        # Flask's send_file() with a path can race with os.unlink() on
        # Windows because the file read is deferred to the WSGI layer.
        import io
        with open(path, "rb") as f:
            blob = f.read()
    finally:
        if os.path.exists(path):
            os.unlink(path)

    return send_file(
        io.BytesIO(blob),
        as_attachment=True,
        download_name=f"stats_{export_type}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
