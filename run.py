"""run.py — Web 版教务管理系统入口。

启动 Flask 服务器，同时服务 REST API 和 Vue 前端。

用法:
    python run.py                  # 默认 localhost:5000
    python run.py --public         # 对外监听 0.0.0.0:5000（局域网可访问）
    python run.py --port 8080      # 指定端口
    python run.py --public --port 8080
"""

import sys
import os
import argparse

# 确保项目根目录在 sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='教务管理系统 Web 服务器')
    parser.add_argument('--public', action='store_true',
                        help='对外监听 (0.0.0.0)，局域网内可访问')
    parser.add_argument('--port', type=int, default=5000,
                        help='监听端口 (默认 5000)')
    args = parser.parse_args()

    host = '0.0.0.0' if args.public else '127.0.0.1'
    print("=" * 60)
    print("  高校教务管理系统 v3.0")
    print(f"  监听地址: http://{host}:{args.port}")
    if args.public:
        import socket
        hostname = socket.gethostname()
        print(f"  主机名: {hostname}")
        print(f"  局域网伙伴请访问: http://{hostname}:{args.port}")
    print("=" * 60)

    app.run(
        host=host,
        port=args.port,
        debug=True,
        threaded=True,
    )
