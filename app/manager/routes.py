from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.auth.decorators import role_required
from app.extensions import db
from app.forms import FollowUpForm
from app.models.alert import Alert
from app.models.assessment import Assessment
from app.models.follow_up import FollowUpAction
from app.models.user import User
from app.query_filters import (
    CLASSIFICATIONS,
    classification_matches,
    in_window,
    read_filters,
    text_match,
)
from app.services.alert_service import FOLLOW_UP_TO_ALERT
from app.services.notifications import queue_follow_up, queue_follow_up_review
from app.services.recommendation_engine import recommendations_for_classifications
from app.services.alert_settings import get_alert_settings
from app.services.assessment_engine import (
    ATTENTION,
    DIMENSION_LABELS,
    DIMENSIONS,
    SIGNIFICANT,
    INSUFFICIENT,
    LIKERT_LABELS,
    QUESTION_BY_CODE,
    SUPPORT,
    chart_payload,
    history_for,
    latest_for,
    present_indicators,
)
from app.timeutil import utcnow

manager_bp = Blueprint("manager", __name__)


def _assigned_employee_or_403(employee_id):
    employee = db.session.get(User, employee_id)
    if employee is None or employee.role != "employee":
        abort(404)
    if employee.manager_id != current_user.id:
        abort(403)
    return employee


def _own_alert_or_403(alert_id):
    alert = db.session.get(Alert, alert_id)
    if alert is None:
        abort(404)
    if alert.manager_id != current_user.id:
        abort(403)
    return alert


def _team():
    return db.session.scalars(
        db.select(User)
        .where(User.manager_id == current_user.id, User.role == "employee")
        .order_by(User.name)
    ).all()


def _team_rows(filters):
    rows = []
    attention_people = 0
    support_indicators = 0
    for employee in _team():
        if filters.q and not text_match(
            filters.q,
            employee.name,
            employee.email,
            employee.designation,
            employee.department,
        ):
            continue
        latest = latest_for(employee.id, filters.start, filters.before)
        if not classification_matches(latest, filters.classification, filters.dimension):
            continue
        if latest is not None and any(
            latest.classification_for(dimension) == ATTENTION for dimension in DIMENSIONS
        ):
            attention_people += 1
        if latest is not None:
            support_indicators += sum(
                1 for dimension in DIMENSIONS if latest.classification_for(dimension) == SUPPORT
            )
        rows.append({"employee": employee, "latest": latest})
    return rows, attention_people, support_indicators


def _manager_alerts():
    return db.session.scalars(
        db.select(Alert)
        .where(Alert.manager_id == current_user.id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
    ).all()


def _alerts_for(rows, filters):
    visible_ids = {row["employee"].id for row in rows}
    selected = []
    for alert in _manager_alerts():
        if alert.employee_id not in visible_ids:
            continue
        if not in_window(alert.created_at, filters.start, filters.before):
            continue
        selected.append(alert)
    return selected


@manager_bp.route("/dashboard")
@role_required("manager")
def dashboard():
    filters = read_filters()
    rows, attention_people, support_indicators = _team_rows(filters)
    alerts = _alerts_for(rows, filters)
    open_alerts = sum(1 for alert in alerts if alert.status == "Open")
    pending_follow_ups = sum(1 for alert in alerts if alert.status != "Completed")
    return render_template(
        "manager/dashboard.html",
        rows=rows,
        team_count=len(rows),
        attention_people=attention_people,
        support_indicators=support_indicators,
        open_alerts=open_alerts,
        pending_follow_ups=pending_follow_ups,
        insufficient=INSUFFICIENT,
        filters=filters,
        empty_message="No employees match these filters." if filters.active else None,
    )


@manager_bp.route("/employees")
@role_required("manager")
def employees():
    filters = read_filters()
    rows, _, _ = _team_rows(filters)
    return render_template(
        "manager/employees.html",
        rows=rows,
        insufficient=INSUFFICIENT,
        filters=filters,
        empty_message="No employees match these filters." if filters.active else None,
    )


@manager_bp.route("/employee/<int:employee_id>")
@role_required("manager")
def employee_detail(employee_id):
    employee = _assigned_employee_or_403(employee_id)
    records = history_for(employee.id)
    latest = records[-1] if records else None
    indicators = present_indicators(latest, "manager") if latest else []
    recommendations = (
        recommendations_for_classifications(
            {item["key"]: item["classification"] for item in indicators}
        )
        if indicators
        else []
    )
    alerts = db.session.scalars(
        db.select(Alert)
        .where(Alert.manager_id == current_user.id, Alert.employee_id == employee.id)
        .order_by(Alert.created_at.desc())
    ).all()
    follow_ups = []
    if alerts:
        follow_ups = db.session.scalars(
            db.select(FollowUpAction)
            .where(FollowUpAction.alert_id.in_([alert.id for alert in alerts]))
            .order_by(FollowUpAction.created_at.desc())
        ).all()
    return render_template(
        "manager/employee_details.html",
        employee=employee,
        latest=latest,
        indicators=indicators,
        recommendations=recommendations,
        assessments=list(reversed(records)),
        chart=chart_payload(records),
        alerts=alerts,
        follow_ups=follow_ups,
        questions=QUESTION_BY_CODE,
        likert_labels=LIKERT_LABELS,
        responses=latest.response_map() if latest else {},
    )


@manager_bp.route("/employee/<int:employee_id>/history")
@role_required("manager")
def employee_history(employee_id):
    employee = _assigned_employee_or_403(employee_id)
    filters = read_filters()
    records = history_for(employee.id, filters.start, filters.before)
    return render_template(
        "manager/history.html",
        employee=employee,
        assessments=list(reversed(records)),
        chart=chart_payload(records),
        filters=filters,
    )


def _filtered_alerts(filters):
    selected = []
    for alert in _manager_alerts():
        if filters.q and not text_match(filters.q, alert.employee.name, alert.employee.email):
            continue
        if filters.dimension and alert.dimension != DIMENSION_LABELS[filters.dimension]:
            continue
        if filters.classification and alert.classification != filters.classification:
            continue
        if filters.status and alert.status != filters.status:
            continue
        if not in_window(alert.created_at, filters.start, filters.before):
            continue
        selected.append(alert)
    return selected


USEFULNESS_CHOICES = ("Useful", "Partly useful", "Not useful")


def _later_reading(alert):
    nxt = db.session.scalars(
        db.select(Assessment)
        .where(
            Assessment.employee_id == alert.employee_id,
            Assessment.submission_date > alert.created_at,
        )
        .order_by(Assessment.submission_date.asc(), Assessment.id.asc())
    ).first()
    if nxt is None:
        return None
    dimension = next(
        (key for key, label in DIMENSION_LABELS.items() if label == alert.dimension),
        None,
    )
    if dimension is None:
        return None
    return {
        "date": nxt.submission_date,
        "score": nxt.score_for(dimension),
        "classification": nxt.classification_for(dimension),
    }


@manager_bp.route("/alerts")
@role_required("manager")
def alerts():
    filters = read_filters(
        classifications=CLASSIFICATIONS + (SIGNIFICANT,),
        statuses=("Open", "In Progress", "Completed"),
    )
    return render_template(
        "manager/alerts.html",
        alerts=_filtered_alerts(filters),
        filters=filters,
        settings=get_alert_settings(),
    )


@manager_bp.route("/alerts/<int:alert_id>")
@role_required("manager")
def alert_detail(alert_id):
    alert = _own_alert_or_403(alert_id)
    form = FollowUpForm()
    return render_template(
        "manager/alert_detail.html",
        alert=alert,
        form=form,
        later=_later_reading(alert),
        usefulness_choices=USEFULNESS_CHOICES,
    )


@manager_bp.route("/alerts/<int:alert_id>/follow-up", methods=["POST"])
@role_required("manager")
def record_follow_up(alert_id):
    alert = _own_alert_or_403(alert_id)
    form = FollowUpForm()
    if form.validate_on_submit():
        now = utcnow()
        action = FollowUpAction(
            alert_id=alert.id,
            manager_id=current_user.id,
            action_description=form.action_description.data.strip(),
            remarks=(form.remarks.data or "").strip() or None,
            status=form.status.data,
            created_at=now,
            updated_at=now,
        )
        alert.status = FOLLOW_UP_TO_ALERT[form.status.data]
        db.session.add(action)
        db.session.flush()
        queue_follow_up(action)
        db.session.commit()
        flash("Follow-up recorded.", "success")
        return redirect(url_for("manager.alert_detail", alert_id=alert.id))
    return render_template(
        "manager/alert_detail.html",
        alert=alert,
        form=form,
        later=_later_reading(alert),
        usefulness_choices=USEFULNESS_CHOICES,
    ), 400


@manager_bp.route("/alerts/<int:alert_id>/follow-up/<int:action_id>/review", methods=["POST"])
@role_required("manager")
def review_follow_up(alert_id, action_id):
    alert = _own_alert_or_403(alert_id)
    action = db.session.get(FollowUpAction, action_id)
    if action is None or action.alert_id != alert.id:
        abort(404)
    usefulness = (request.form.get("usefulness") or "").strip()
    note = (request.form.get("usefulness_note") or "").strip()
    if usefulness not in USEFULNESS_CHOICES:
        flash("Choose whether this follow-up was useful.", "danger")
    elif len(note) > 5000:
        flash("Keep the review note under 5000 characters.", "danger")
    else:
        action.usefulness = usefulness
        action.usefulness_note = note or None
        action.reviewed_at = utcnow()
        queue_follow_up_review(action)
        db.session.commit()
        flash("Usefulness review saved.", "success")
    return redirect(url_for("manager.alert_detail", alert_id=alert.id))


@manager_bp.route("/follow-ups")
@role_required("manager")
def follow_ups():
    actions = db.session.scalars(
        db.select(FollowUpAction)
        .where(FollowUpAction.manager_id == current_user.id)
        .order_by(FollowUpAction.created_at.desc())
    ).all()
    return render_template("manager/follow_ups.html", actions=actions)
