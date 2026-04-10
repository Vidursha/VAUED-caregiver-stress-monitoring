from flask import Blueprint, jsonify
from backend.services.dashboard_service import (
    get_dashboard_summary,
    get_stress_distribution
)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    data = get_dashboard_summary()
    return jsonify(data)

@dashboard_bp.route("/api/dashboard/stress-distribution", methods=["GET"])
def dashboard_stress_distribution():
    data = get_stress_distribution()
    return jsonify(data)