from flask import Blueprint, jsonify, request

from backend.services.chat_service import chat_reply

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400

        ui_state = data.get("ui_state") or {}
        heatmap_cell = data.get("heatmap_cell")
        reply = chat_reply(message, ui_state, heatmap_cell)
        return jsonify({"success": True, "data": {"reply": reply}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
