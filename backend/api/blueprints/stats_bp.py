"""stats_bp — 统计分析 API。

GET  /api/stats/class/<plan_id>      — 班级成绩统计
GET  /api/stats/distribution/<plan_id> — 成绩分布
POST /api/stats/export               — 统计数据导出 Excel
"""

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


@stats_bp.route("/export", methods=["POST"])
@require_auth
def export_stats():
    """导出统计数据为 Excel 文件。

    请求体: {"type": "class", "plan_id": 1, "class_name": "..."}
    或: {"type": "academic", "student_id": "S001"}
    """
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
    else:
        return error_response("不支持的导出类型")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    try:
        StatsController().export_stats_to_excel(sd, tmp.name)
        tmp.close()
        return send_file(
            tmp.name,
            as_attachment=True,
            download_name=f"stats_{export_type}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
