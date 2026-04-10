from flask import Flask
from backend.routes.dashboard import dashboard_bp
from backend.routes.caregivers import caregiver_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(caregiver_bp)

    @app.route("/")
    def home():
        return {"message": "Nurse Stress Dashboard Backend Running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)