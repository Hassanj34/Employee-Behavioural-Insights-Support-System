from app.extensions import db
from app.timeutil import utcnow


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    kind = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    href = db.Column(db.String(255), nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=True, index=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id"), nullable=True, index=True)
    follow_up_id = db.Column(db.Integer, db.ForeignKey("follow_up_actions.id"), nullable=True, index=True)
    response_id = db.Column(db.Integer, db.ForeignKey("complaint_responses.id"), nullable=True, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    cleared_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    recipient = db.relationship("User", foreign_keys=[recipient_id])
    alert = db.relationship("Alert")
