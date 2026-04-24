from flask import Blueprint, jsonify, request

from backend.services.sensor_service import list_sensor_records

sensor_bp = Blueprint("sensor", __name__)


@sensor_bp.route("/api/sensor/records", methods=["GET"])
def sensor_records():
    try:
        caregiver_id = request.args.get("caregiver_id")
        month = request.args.get("month")
        data = list_sensor_records(caregiver_id=caregiver_id, month=month)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500