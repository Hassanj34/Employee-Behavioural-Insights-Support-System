from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.alert import Alert
from app.models.notification import Notification
from app.timeutil import utcnow


def ensure_notifications(user):
    """Create a notification for every alert already assigned to this manager."""
    alerts = db.session.execute(
        db.select(Alert.id, Alert.created_at).where(Alert.manager_id == user.id)
    ).all()
    if not alerts:
        return
    existing = set(
        db.session.scalars(
            db.select(Notification.alert_id).where(Notification.recipient_id == user.id)
        )
    )
    added = False
    for alert_id, created_at in alerts:
        if alert_id in existing:
            continue
        db.session.add(
            Notification(
                recipient_id=user.id,
                alert_id=alert_id,
                created_at=created_at,
            )
        )
        added = True
    if added:
        db.session.commit()


def notifications_for(user):
    ensure_notifications(user)
    return db.session.scalars(
        db.select(Notification)
        .where(Notification.recipient_id == user.id, Notification.cleared_at.is_(None))
        .options(joinedload(Notification.alert).joinedload(Alert.employee))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    ).unique().all()


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
    if pending:
        db.session.commit()
    return len(pending)
