from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.services.notifications import clear_notifications, mark_notifications_read

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications/read", methods=["POST"])
@login_required
def read():
    marked = mark_notifications_read(current_user)
    return jsonify({"ok": True, "read": marked})


@notifications_bp.route("/notifications/clear", methods=["POST"])
@login_required
def clear():
    cleared = clear_notifications(current_user)
    return jsonify({"ok": True, "cleared": cleared})
