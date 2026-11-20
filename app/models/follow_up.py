from app.extensions import db
from app.timeutil import utcnow


class FollowUpAction(db.Model):
    __tablename__ = "follow_up_actions"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action_description = db.Column(db.Text, nullable=False)
    remarks = db.Column(db.Text)
    status = db.Column(db.String(32), nullable=False)
    usefulness = db.Column(db.String(32))
    usefulness_note = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    alert = db.relationship("Alert", back_populates="follow_ups")
    manager = db.relationship("User", foreign_keys=[manager_id])
