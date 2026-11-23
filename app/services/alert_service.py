from app.extensions import db
from app.models.alert import Alert
from app.models.assessment import Assessment, AssessmentResponse
from app.services.alert_settings import get_alert_settings
from app.services.notifications import queue_alert_notification
from app.services.assessment_engine import (
    ATTENTION,
    DIMENSIONS,
    DIMENSION_LABELS,
    SIGNIFICANT,
    classify,
    explain,
    score_responses,
    validate_responses,
)
from app.services.recommendation_engine import recommendation_for
from app.timeutil import utcnow

FOLLOW_UP_TO_ALERT = {
    "Pending": "Open",
    "In Progress": "In Progress",
    "Completed": "Completed",
}


def save_assessment(employee, responses, submission_date=None):
    cleaned = validate_responses(responses)
    scores = score_responses(cleaned)
    settings = get_alert_settings()
    classifications = {
        dimension: classify(scores[dimension], settings.positive_min, settings.support_min)
        for dimension in DIMENSIONS
    }
    when = submission_date or utcnow()
    assessment = Assessment(
        employee_id=employee.id,
        submission_date=when,
        status="Completed",
        workload_score=scores["workload"],
        motivation_score=scores["motivation"],
        learning_score=scores["learning"],
        workload_classification=classifications["workload"],
        motivation_classification=classifications["motivation"],
        learning_classification=classifications["learning"],
    )
    try:
        db.session.add(assessment)
        db.session.flush()
        for code, value in cleaned.items():
            db.session.add(
                AssessmentResponse(
                    assessment_id=assessment.id,
                    question_code=code,
                    response_value=value,
                )
            )
        create_alerts(employee, assessment, cleaned, settings)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return assessment


def create_alerts(employee, assessment, responses, settings=None):
    if not employee.manager_id:
        return []
    settings = settings or get_alert_settings()
    previous = db.session.scalars(
        db.select(Assessment)
        .where(
            Assessment.employee_id == employee.id,
            Assessment.id != assessment.id,
            Assessment.submission_date <= assessment.submission_date,
        )
        .order_by(Assessment.submission_date.desc(), Assessment.id.desc())
    ).first()
    created = []
    drop_limit = round(settings.significant_drop, 2)
    for dimension in DIMENSIONS:
        classification = assessment.classification_for(dimension)
        score = round(assessment.score_for(dimension), 2)
        previous_score = round(previous.score_for(dimension), 2) if previous is not None else None
        drop = round(previous_score - score, 2) if previous_score is not None else None
        significant = drop is not None and drop >= drop_limit
        if classification != ATTENTION and not significant:
            continue
        if classification == ATTENTION:
            explanation = explain(dimension, responses, classification, audience="manager")
            if significant:
                explanation += (
                    f" The score also fell by {drop:.2f} from the previous check-in "
                    f"({previous_score:.2f} to {score:.2f})."
                )
            alert_classification = classification
            recommendation = recommendation_for(dimension, classification)
        else:
            alert_classification = SIGNIFICANT
            explanation = (
                f"{DIMENSION_LABELS[dimension]} fell by {drop:.2f}, from {previous_score:.2f} "
                f"to {score:.2f}, since the previous check-in. The current score is still above "
                "the attention line, but the change is large enough to review. This is a prompt for "
                "a supportive conversation, not a diagnosis or an employment decision."
            )
            recommendation = recommendation_for(dimension, classification) or (
                f"Ask what changed for {DIMENSION_LABELS[dimension].lower()} since the last check-in."
            )
        alert = Alert(
            employee_id=employee.id,
            manager_id=employee.manager_id,
            assessment_id=assessment.id,
            dimension=DIMENSION_LABELS[dimension],
            score=score,
            classification=alert_classification,
            explanation=explanation,
            recommendation=recommendation,
            status="Open",
            created_at=assessment.submission_date,
        )
        db.session.add(alert)
        db.session.flush()
        queue_alert_notification(alert)
        created.append(alert)
    return created
