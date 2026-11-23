from app.extensions import db
from app.models.complaint import Complaint, ComplaintResponse
from app.models.user import User
from app.services.notifications import queue_complaint_submitted, queue_complaint_update
from app.timeutil import utcnow

CATEGORIES = (
    "Promotion or Career Progression",
    "Project or Role Assignment",
    "Workplace Treatment",
    "Recognition or Fairness",
    "Other Workplace Complaint",
)

STATUSES = ("Submitted", "Under Review", "Resolved", "Closed")

RECIPIENT_ROLES = ("hr", "senior_manager")


def resolve_recipient(role):
    return db.session.scalars(
        db.select(User).where(User.role == role, User.is_active.is_(True)).order_by(User.id)
    ).first()


def complaints_for_recipient(user):
    return db.session.scalars(
        db.select(Complaint)
        .where(Complaint.recipient_id == user.id)
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
    ).all()


def complaints_for_employee(user):
    return db.session.scalars(
        db.select(Complaint)
        .where(Complaint.employee_id == user.id)
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
    ).all()


def complaint_counts(complaints):
    counts = {status: 0 for status in STATUSES}
    for complaint in complaints:
        counts[complaint.status] = counts.get(complaint.status, 0) + 1
    counts["total"] = len(complaints)
    return counts


def submit_complaint(employee, recipient_role, category, subject, description):
    if recipient_role not in RECIPIENT_ROLES:
        return None, "Choose HR or a Senior Manager."
    if category not in CATEGORIES:
        return None, "Choose a complaint category."
    recipient = resolve_recipient(recipient_role)
    if recipient is None:
        return None, "No active recipient is available for that route."
    now = utcnow()
    complaint = Complaint(
        employee_id=employee.id,
        recipient_role=recipient_role,
        recipient_id=recipient.id,
        category=category,
        subject=subject.strip(),
        description=description.strip(),
        status="Submitted",
        created_at=now,
        updated_at=now,
    )
    db.session.add(complaint)
    db.session.flush()
    queue_complaint_submitted(complaint)
    db.session.commit()
    return complaint, None


def add_complaint_update(complaint, responder, status, response_text):
    if status not in STATUSES:
        raise ValueError("Choose a valid status.")
    text = (response_text or "").strip()
    if not text:
        raise ValueError("Enter a response or resolution remark.")
    now = utcnow()
    complaint.status = status
    complaint.updated_at = now
    response = ComplaintResponse(
        complaint_id=complaint.id,
        responder_id=responder.id,
        response_text=text,
        created_at=now,
    )
    db.session.add(response)
    db.session.flush()
    queue_complaint_update(complaint, responder, status, text, response)
    db.session.commit()
