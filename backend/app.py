from pathlib import Path
import sys

from flask import Flask
from flask_cors import CORS

# Allow running as `python backend/app.py` from project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from backend.database import ensure_db_initialized
from backend.routes.dashboard import dashboard_bp
from backend.routes.caregivers import caregiver_bp
from backend.routes.sensor import sensor_bp
from backend.routes.chat import chat_bp


def create_app():
    ensure_db_initialized()
    app = Flask(__name__)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "http://localhost:4173",
                    "http://127.0.0.1:4173",
                ]
            }
        },
    )

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(sensor_bp)
    app.register_blueprint(chat_bp)

    @app.route("/")
    def home():
        return {"message": "Nurse Stress Dashboard Backend Running"}

    @app.route("/api/health")
    def health():
        return {
            "success": True,
            "data": {
                "status": "ok",
                "message": "Backend API running",
            },
        }

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)