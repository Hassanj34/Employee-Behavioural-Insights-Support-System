from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.alert import Alert
from app.models.notification import Notification
from app.timeutil import utcnow


def _clip(value, limit):
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def queue_notification(
    *,
    recipient_id,
    kind,
    title,
    summary,
    body,
    href,
    actor_id=None,
    created_at=None,
    alert_id=None,
    complaint_id=None,
    follow_up_id=None,
    response_id=None,
):
    """Add one notification for a single recipient. The caller commits."""
    if recipient_id is None or recipient_id == actor_id:
        return None
    note = Notification(
        recipient_id=recipient_id,
        kind=kind,
        title=_clip(title, 200),
        summary=_clip(summary, 255),
        body=(body or "").strip(),
        href=href,
        alert_id=alert_id,
        complaint_id=complaint_id,
        follow_up_id=follow_up_id,
        response_id=response_id,
        created_at=created_at or utcnow(),
    )
    db.session.add(note)
    return note


def queue_alert_notification(alert):
    return queue_notification(
        recipient_id=alert.manager_id,
        actor_id=alert.employee_id,
        kind="alert",
        title=alert.employee.name,
        summary=f"{alert.dimension} · {alert.score:.2f} · {alert.classification}",
        body=alert.explanation,
        href=f"/manager/alerts/{alert.id}",
        alert_id=alert.id,
        created_at=alert.created_at,
    )


def queue_complaint_submitted(complaint):
    return queue_notification(
        recipient_id=complaint.recipient_id,
        actor_id=complaint.employee_id,
        kind="complaint",
        title=complaint.employee.name,
        summary=f"New complaint · {complaint.subject}",
        body=f"{complaint.category}. Status: Submitted.",
        href=_recipient_complaint_href(complaint),
        complaint_id=complaint.id,
        created_at=complaint.created_at,
    )


def queue_complaint_update(complaint, responder, status, response_text, response):
    return queue_notification(
        recipient_id=complaint.employee_id,
        actor_id=responder.id,
        kind="complaint_update",
        title=responder.name,
        summary=f"{complaint.subject} is now {status}",
        body=response_text,
        href=f"/employee/complaints/{complaint.id}",
        complaint_id=complaint.id,
        response_id=response.id,
        created_at=response.created_at,
    )


def queue_follow_up(action):
    alert = action.alert
    return queue_notification(
        recipient_id=alert.employee_id,
        actor_id=action.manager_id,
        kind="follow_up",
        title=action.manager.name,
        summary=f"{alert.dimension} follow-up is {action.status}",
        body=action.action_description,
        href=f"/employee/results/{alert.assessment_id}",
        alert_id=alert.id,
        follow_up_id=action.id,
        created_at=action.created_at,
    )


def queue_follow_up_review(action):
    alert = action.alert
    return queue_notification(
        recipient_id=alert.employee_id,
        actor_id=action.manager_id,
        kind="follow_up_review",
        title=action.manager.name,
        summary=f"{alert.dimension} follow-up marked {action.usefulness}",
        body=action.usefulness_note or action.action_description,
        href=f"/employee/results/{alert.assessment_id}",
        alert_id=alert.id,
        follow_up_id=action.id,
        created_at=action.reviewed_at,
    )


def _recipient_complaint_href(complaint):
    if complaint.recipient_role == "hr":
        return f"/hr/complaints/{complaint.id}"
    return f"/senior-manager/complaints/{complaint.id}"


def ensure_notifications(user):
    """Create a notification for every alert already assigned to this manager."""
    alerts = db.session.scalars(
        db.select(Alert).where(Alert.manager_id == user.id).options(joinedload(Alert.employee))
    ).unique().all()
    if not alerts:
        return
    existing = set(
        db.session.scalars(
            db.select(Notification.alert_id).where(
                Notification.recipient_id == user.id,
                Notification.alert_id.is_not(None),
            )
        )
    )
    added = False
    for alert in alerts:
        if alert.id in existing:
            continue
        queue_alert_notification(alert)
        added = True
    if added:
        db.session.commit()


def notifications_for(user):
    ensure_notifications(user)
    return db.session.scalars(
        db.select(Notification)
        .where(Notification.recipient_id == user.id, Notification.cleared_at.is_(None))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    ).all()


def unread_count(notes):
    return sum(1 for note in notes if note.read_at is None)


def mark_notifications_read(user):
    now = utcnow()
    pending = db.session.scalars(
        db.select(Notification).where(
            Notification.recipient_id == user.id,
            Notification.cleared_at.is_(None),
            Notification.read_at.is_(None),
        )
    ).all()
    for note in pending:
        note.read_at = now
    if pending:
        db.session.commit()
    return len(pending)


def clear_notifications(user):
    now = utcnow()
    pending = db.session.scalars(
        db.select(Notification).where(
            Notification.recipient_id == user.id,
            Notification.cleared_at.is_(None),
        )
    ).all()
    for note in pending:
        note.cleared_at = now
        if note.read_at is None:
            note.read_at = now
    if pending:
        db.session.commit()
    return len(pending)


def backfill_event_notifications():
    """Give existing complaints and follow-ups a notification once."""
    from app.models.complaint import Complaint, ComplaintResponse
    from app.models.follow_up import FollowUpAction

    added = False
    sent_complaints = set(
        db.session.execute(
            db.select(Notification.complaint_id, Notification.recipient_id).where(Notification.kind == "complaint")
        ).all()
    )
    complaints = db.session.scalars(
        db.select(Complaint).options(joinedload(Complaint.employee))
    ).unique().all()
    for complaint in complaints:
        if (complaint.id, complaint.recipient_id) in sent_complaints:
            continue
        queue_complaint_submitted(complaint)
        added = True

    sent_responses = set(
        db.session.scalars(db.select(Notification.response_id).where(Notification.response_id.is_not(None))).all()
    )
    responses = db.session.scalars(
        db.select(ComplaintResponse).options(
            joinedload(ComplaintResponse.complaint).joinedload(Complaint.employee),
            joinedload(ComplaintResponse.responder),
        )
    ).unique().all()
    for response in responses:
        if response.id in sent_responses:
            continue
        queue_complaint_update(
            response.complaint,
            response.responder,
            response.complaint.status,
            response.response_text,
            response,
        )
        added = True

    sent_follow_ups = set(
        db.session.scalars(
            db.select(Notification.follow_up_id).where(Notification.kind == "follow_up")
        ).all()
    )
    actions = db.session.scalars(
        db.select(FollowUpAction).options(
            joinedload(FollowUpAction.alert).joinedload(Alert.employee),
            joinedload(FollowUpAction.manager),
        )
    ).unique().all()
    for action in actions:
        if action.id in sent_follow_ups:
            continue
        queue_follow_up(action)
        added = True

    if added:
        db.session.commit()
