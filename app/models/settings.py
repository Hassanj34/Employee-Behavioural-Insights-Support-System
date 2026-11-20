from app.extensions import db
from app.timeutil import utcnow


class AlertSettings(db.Model):
    __tablename__ = "alert_settings"

    id = db.Column(db.Integer, primary_key=True)
    positive_min = db.Column(db.Float, nullable=False, default=3.50)
    support_min = db.Column(db.Float, nullable=False, default=2.50)
    significant_drop = db.Column(db.Float, nullable=False, default=0.75)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    updated_by = db.relationship("User", foreign_keys=[updated_by_id])
