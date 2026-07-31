"""run.py - EduMgmt Web Entry Point.

Starts the Flask server, serving both REST API and Vue frontend.

Usage:
    python run.py                  # default localhost:5000
    python run.py --public         # listen on 0.0.0.0:5000 (LAN accessible)
    python run.py --port 8080      # custom port
    python run.py --public --port 8080
"""

import sys
import os
import argparse

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.api.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EduMgmt Web Server')
    parser.add_argument('--public', action='store_true',
                        help='Listen on 0.0.0.0 (LAN accessible)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port (default 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='启用 Flask debug 模式（热重载）')
    parser.add_argument('--upgrade-db-only', action='store_true',
                        help='仅检查并升级数据库结构，然后退出')
    args = parser.parse_args()

    if args.upgrade_db_only:
        from backend.models.base import DatabaseManager
        DatabaseManager.get_instance()
        print("Database schema is current.")
        raise SystemExit(0)

    host = '0.0.0.0' if args.public else '127.0.0.1'
    print("=" * 60)
    print("  EduMgmt System v3.0")
    print(f"  Listening: http://{host}:{args.port}")
    if args.public:
        import socket
        hostname = socket.gethostname()
        print(f"  Hostname: {hostname}")
        print(f"  LAN access: http://{hostname}:{args.port}")
    print("=" * 60)

    app.run(
        host=host,
        port=args.port,
        debug=args.debug,
        threaded=True,
    )
