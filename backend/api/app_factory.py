"""backend/api/app_factory.py — Flask 应用工厂。

create_app() 函数创建并配置 Flask 应用：
- 初始化数据库
- 注册所有 9 个 Blueprint
- 配置 CORS
- 生产模式：服务 Vue dist 静态文件 + SPA fallback
"""

import os
import sys
import uuid

from flask import Flask, g, request, send_from_directory
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

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
from backend.api.errors import ApiError

_WARNED_DEFAULT_PASSWORD = False


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
    app.config['JSON_AS_ASCII'] = False  # 中文不转义为 \uXXXX

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

    @app.before_request
    def _assign_request_id():
        supplied = request.headers.get("X-Request-ID", "").strip()
        g.request_id = supplied[:64] if supplied else uuid.uuid4().hex

    @app.after_request
    def _attach_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return error_response(
            error.message,
            data=error.data,
            status_code=error.status_code,
            code=error.code,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        from backend.utils.log_util import get_logger
        get_logger("app_factory").error("Database request failed", exc_info=True)
        return error_response(
            "数据库服务暂时不可用",
            status_code=503,
            code="DATABASE_UNAVAILABLE",
        )

    # 全局错误处理
    @app.errorhandler(404)
    def handle_404(e):
        return error_response("请求的资源不存在", status_code=404, code="NOT_FOUND")

    @app.errorhandler(500)
    def handle_500(e):
        import traceback
        from backend.utils.log_util import get_logger
        _log = get_logger("app_factory")
        _log.error(f"500 Internal Server Error: {e}\n{traceback.format_exc()}")
        return error_response("服务器内部错误", status_code=500, code="INTERNAL_ERROR")

    # ── 生产模式：服务 Vue 前端静态文件 ──
    _setup_static_serving(app)

    # ── 启动安全检查 ──
    global _WARNED_DEFAULT_PASSWORD
    if not _WARNED_DEFAULT_PASSWORD:
        _WARNED_DEFAULT_PASSWORD = True
        from backend.config.settings import Settings
        raw = Settings.get_instance()._config.get(
            "system", "default_password", fallback="123456"
        ).strip()
        from backend.utils.log_util import get_logger
        _startup_log = get_logger("app_factory")
        if raw == "123456":
            _startup_log.warning(
                "⚠ 安全警告：默认密码仍为弱口令 '123456'，"
                "请修改 backend/config/config.ini 中 [system] default_password"
            )
        if raw == "":
            _startup_log.warning(
                "⚠ 安全警告：default_password 为空字符串（极度危险），"
                "运行时已兜底为 '123456'。请修改 backend/config/config.ini"
            )

    # ── 初始化并升级数据库（延迟到首次请求）──
    # DatabaseManager 会在任何 ORM 查询前执行幂等的增量升级；不会重建表。
    @app.before_request
    def _init_db_on_first_request():
        if getattr(app, '_db_ready', False):
            return
        try:
            from backend.models.base import DatabaseManager
            DatabaseManager.get_instance()
            app._db_ready = True
        except Exception:
            from backend.utils.log_util import get_logger
            get_logger("app_factory").error("数据库初始化/升级失败", exc_info=True)
            return error_response(
                "数据库初始化或升级失败，请检查服务日志",
                status_code=503,
                code="DATABASE_SCHEMA_UNAVAILABLE",
            )

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
