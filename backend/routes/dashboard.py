from flask import Blueprint, jsonify, request
from backend.services.dashboard_service import (
    get_dashboard_summary,
    get_stress_distribution,
    get_monthly_stress_trend
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    try:
        caregiver_id = request.args.get("caregiver_id")
        month = request.args.get("month")
        data = get_dashboard_summary(caregiver_id=caregiver_id, month=month)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/stress-distribution", methods=["GET"])
def dashboard_stress_distribution():
    try:
        caregiver_id = request.args.get("caregiver_id")
        month = request.args.get("month")
        data = get_stress_distribution(caregiver_id=caregiver_id, month=month)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/api/dashboard/monthly-trend", methods=["GET"])
def dashboard_monthly_trend():
    try:
        caregiver_id = request.args.get("caregiver_id")
        data = get_monthly_stress_trend(caregiver_id=caregiver_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500