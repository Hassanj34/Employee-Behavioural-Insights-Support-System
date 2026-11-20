from app.extensions import db
from app.timeutil import utcnow


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_role = db.Column(db.String(32), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="Submitted", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    employee = db.relationship("User", foreign_keys=[employee_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])
    responses = db.relationship(
        "ComplaintResponse",
        backref="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintResponse.created_at",
    )


class ComplaintResponse(db.Model):
    __tablename__ = "complaint_responses"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False, index=True
    )
    responder_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    responder = db.relationship("User", foreign_keys=[responder_id])
