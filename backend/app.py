from pathlib import Path

from flask import Flask

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
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

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(caregiver_bp)
    app.register_blueprint(sensor_bp)
    app.register_blueprint(chat_bp)

    @app.route("/")
    def home():
        return {"message": "Nurse Stress Dashboard Backend Running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)