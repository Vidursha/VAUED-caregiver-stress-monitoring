from flask import Blueprint, jsonify, request

from backend.services.chat_service import chat_reply

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    ui_state = data.get("ui_state") or {}
    heatmap_cell = data.get("heatmap_cell")
    return jsonify({"reply": chat_reply(message, ui_state, heatmap_cell)})
