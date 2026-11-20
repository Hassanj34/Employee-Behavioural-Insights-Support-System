"""Organization-wide alert rules. One row, edited from the settings screen."""

from app.extensions import db
from app.models.settings import AlertSettings
from app.timeutil import utcnow


def get_alert_settings():
    settings = db.session.get(AlertSettings, 1)
    if settings is None:
        settings = AlertSettings(
            id=1,
            positive_min=3.50,
            support_min=2.50,
            significant_drop=0.75,
        )
        db.session.add(settings)
        db.session.commit()
    return settings


def update_alert_settings(positive_min, support_min, significant_drop, user):
    positive_min = round(float(positive_min), 2)
    support_min = round(float(support_min), 2)
    significant_drop = round(float(significant_drop), 2)
    if not (1 <= support_min < positive_min <= 5):
        raise ValueError(
            "The attention line must stay below the positive line, and both must be between 1 and 5."
        )
    if not (0.25 <= significant_drop <= 4):
        raise ValueError("The significant-change amount must be between 0.25 and 4.")
    settings = get_alert_settings()
    settings.positive_min = positive_min
    settings.support_min = support_min
    settings.significant_drop = significant_drop
    settings.updated_at = utcnow()
    settings.updated_by_id = user.id
    db.session.commit()
    return settings
