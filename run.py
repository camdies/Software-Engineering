"""run.py — Web 版教务管理系统入口。

启动 Flask 服务器，同时服务 REST API 和 Vue 前端。
开发模式: python run.py → http://localhost:5000

生产部署:
  gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""

import sys
import os

# 确保项目根目录在 sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,  # 多线程模式 — 选课并发 FOR UPDATE 锁依赖此配置
    )
