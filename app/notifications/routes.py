from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.services.notifications import clear_notifications

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications/clear", methods=["POST"])
@login_required
def clear():
    cleared = clear_notifications(current_user)
    return jsonify({"ok": True, "cleared": cleared})
