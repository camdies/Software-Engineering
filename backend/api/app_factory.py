"""backend/api/app_factory.py — Flask 应用工厂。

create_app() 函数创建并配置 Flask 应用：
- 初始化数据库
- 注册所有 7 个 Blueprint
- 配置 CORS
- 生产模式：服务 Vue dist 静态文件 + SPA fallback
"""

import os
import sys

from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.api.blueprints.auth_bp import auth_bp
from backend.api.blueprints.admin_bp import admin_bp
from backend.api.blueprints.student_bp import student_bp
from backend.api.blueprints.teacher_bp import teacher_bp
from backend.api.blueprints.enrollment_bp import enrollment_bp
from backend.api.blueprints.grade_bp import grade_bp
from backend.api.blueprints.stats_bp import stats_bp
from backend.api.blueprints.audit_bp import audit_bp
from backend.api.blueprints.password_reset_bp import password_reset_bp
from backend.api.response import error_response


def create_app() -> Flask:
    """创建并配置 Flask 应用。

    Returns:
        Flask: 已配置的 Flask 应用实例。
    """
    # 确保项目根目录在 sys.path 中
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    app = Flask(
        __name__,
        static_folder=None,  # 我们手动处理静态文件
    )

    # CORS — 允许跨域（开发时 Vite dev server 在不同端口）
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册 Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(enrollment_bp)
    app.register_blueprint(grade_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(audit_bp)

    # 全局错误处理
    @app.errorhandler(404)
    def handle_404(e):
        return error_response("请求的资源不存在", status_code=404)

    @app.errorhandler(500)
    def handle_500(e):
        return error_response("服务器内部错误", status_code=500)

    # ── 生产模式：服务 Vue 前端静态文件 ──
    _setup_static_serving(app)

    # ── 初始化数据库 ──
    try:
        from backend.models.base import DatabaseManager
        DatabaseManager.get_instance().create_all_tables()
    except Exception:
        # 启动时不阻断，允许稍后配置
        pass

    return app


def _setup_static_serving(app: Flask):
    """配置前端静态文件服务和 SPA fallback。

    查找 frontend/dist/ 目录，如果存在则注册路由。

    这允许单进程部署：Flask 同时服务 API 和前端。
    """
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "dist"
    )
    frontend_dist = os.path.normpath(frontend_dist)

    if not os.path.isdir(frontend_dist):
        return  # 开发模式，前端由 Vite dev server 提供

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        assets_dir = os.path.join(frontend_dist, "assets")
        return send_from_directory(assets_dir, filename)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # 如果路径看起来像 API，不处理（让 Blueprint 处理）
        if path.startswith("api/"):
            return error_response("Not Found", status_code=404)
        file_path = os.path.join(frontend_dist, path) if path else frontend_dist
        if path and os.path.isfile(file_path):
            return send_from_directory(frontend_dist, path)
        # SPA fallback：所有非 API 路径返回 index.html
        return send_from_directory(frontend_dist, "index.html")
