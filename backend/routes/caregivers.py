from flask import Blueprint, jsonify
from backend.services.caregiver_service import (
    get_caregiver_stress_list,
    get_caregiver_by_id
)

caregiver_bp = Blueprint("caregivers", __name__)

@caregiver_bp.route("/api/caregivers", methods=["GET"])
def caregiver_list():
    try:
        data = get_caregiver_stress_list()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@caregiver_bp.route("/api/caregivers/<caregiver_id>", methods=["GET"])
def caregiver_detail(caregiver_id):
    try:
        data = get_caregiver_by_id(caregiver_id)
        if data is None:
            return jsonify({"success": False, "error": "Caregiver not found"}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500