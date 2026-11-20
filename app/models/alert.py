from app.extensions import db
from app.timeutil import utcnow


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False, index=True
    )
    dimension = db.Column(db.String(32), nullable=False)
    score = db.Column(db.Float, nullable=False)
    classification = db.Column(db.String(64), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="Open")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    employee = db.relationship("User", foreign_keys=[employee_id])
    manager = db.relationship("User", foreign_keys=[manager_id])
    assessment = db.relationship("Assessment", backref="alerts")
    follow_ups = db.relationship(
        "FollowUpAction",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="FollowUpAction.created_at",
    )
