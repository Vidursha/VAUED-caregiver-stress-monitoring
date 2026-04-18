from flask import Blueprint, jsonify

from backend.services.sensor_service import list_sensor_records

sensor_bp = Blueprint("sensor", __name__)


@sensor_bp.route("/api/sensor/records", methods=["GET"])
def sensor_records():
    return jsonify(list_sensor_records())
