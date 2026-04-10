from flask import Blueprint, jsonify
from backend.services.caregiver_service import (
    get_caregiver_stress_list,
    get_caregiver_by_id
)

caregiver_bp = Blueprint("caregivers", __name__)

@caregiver_bp.route("/api/caregivers", methods=["GET"])
def caregiver_list():
    data = get_caregiver_stress_list()
    return jsonify(data)

@caregiver_bp.route("/api/caregivers/<caregiver_id>", methods=["GET"])
def caregiver_detail(caregiver_id):
    data = get_caregiver_by_id(caregiver_id)
    if data is None:
        return jsonify({"error": "Caregiver not found"}), 404
    return jsonify(data)