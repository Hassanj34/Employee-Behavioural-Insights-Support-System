from app.extensions import db
from app.timeutil import utcnow


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.UniqueConstraint("recipient_id", "alert_id", name="uq_notification_recipient_alert"),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    cleared_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    recipient = db.relationship("User", foreign_keys=[recipient_id])
    alert = db.relationship("Alert")
