import waitress
from backend.api.auth import validate_jwt_configuration
from run import app  # run.py creates the Flask app

if __name__ == "__main__":
    validate_jwt_configuration(production=True)
    print("=" * 60)
    print("  EduMgmt System v3.0 - Production Server")
    print("  Starting waitress on http://0.0.0.0:5000")
    print("=" * 60)
    waitress.serve(app, host="0.0.0.0", port=5000, threads=8)
