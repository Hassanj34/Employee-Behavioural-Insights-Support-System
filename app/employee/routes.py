from datetime import timedelta

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from app.query_filters import filter_complaints, read_filters

from app.auth.decorators import role_required
from app.extensions import db
from app.forms import AssessmentForm, ComplaintForm
from app.models.assessment import Assessment
from app.models.complaint import Complaint
from app.services.alert_service import save_assessment
from app.services.assessment_engine import (
    DIMENSIONS,
    LIKERT_LABELS,
    QUESTION_BY_CODE,
    SECTION_NOTES,
    chart_payload,
    history_for,
    latest_for,
    present_indicators,
    questions_for_dimension,
)
from app.timeutil import utcnow
from app.services.complaint_service import complaints_for_employee
from app.services.complaint_service import submit_complaint as lodge_complaint
from app.services.recommendation_engine import recommendations_for_classifications

employee_bp = Blueprint("employee", __name__)


def _own_assessment_or_403(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    if assessment is None:
        abort(404)
    if assessment.employee_id != current_user.id:
        abort(403)
    return assessment


def _own_complaint_or_403(complaint_id):
    complaint = db.session.get(Complaint, complaint_id)
    if complaint is None:
        abort(404)
    if complaint.employee_id != current_user.id:
        abort(403)
    return complaint


def _response_payload(form):
    payload = {}
    for code in QUESTION_BY_CODE:
        value = form[code.lower()].data
        if value not in (None, ""):
            payload[code] = value
    return payload


def _check_in_due(latest):
    if latest is None:
        return True
    return utcnow() - latest.submission_date >= timedelta(days=7)


@employee_bp.route("/dashboard")
@role_required("employee")
def dashboard():
    filters = read_filters()
    absolute_latest = latest_for(current_user.id)
    latest = (
        latest_for(current_user.id, filters.start, filters.before)
        if filters.has_dates
        else absolute_latest
    )
    indicators = present_indicators(latest, "employee") if latest else []
    recommendations = []
    if latest:
        classifications = {item["key"]: item["classification"] for item in indicators}
        recommendations = recommendations_for_classifications(classifications)
    complaints = complaints_for_employee(current_user)
    return render_template(
        "employee/dashboard.html",
        latest=latest,
        indicators=indicators,
        recommendations=recommendations,
        open_complaints=sum(1 for item in complaints if item.status in {"Submitted", "Under Review"}),
        check_in_due=_check_in_due(absolute_latest),
        filters=filters,
    )


@employee_bp.route("/assessment", methods=["GET", "POST"])
@role_required("employee")
def assessment():
    form = AssessmentForm()
    if form.validate_on_submit():
        try:
            record = save_assessment(current_user, _response_payload(form))
        except ValueError as exc:
            flash(str(exc), "danger")
        else:
            flash("Assessment submitted. Your indicators are ready.", "success")
            return redirect(url_for("employee.results", assessment_id=record.id))
    sections = [
        {
            "key": dimension,
            "title": {"workload": "Workload", "motivation": "Motivation", "learning": "Learning Confidence"}[
                dimension
            ],
            "note": SECTION_NOTES[dimension],
            "questions": questions_for_dimension(dimension),
        }
        for dimension in DIMENSIONS
    ]
    return render_template("employee/assessment.html", form=form, sections=sections)


@employee_bp.route("/results/<int:assessment_id>")
@role_required("employee")
def results(assessment_id):
    record = _own_assessment_or_403(assessment_id)
    indicators = present_indicators(record, "employee")
    classifications = {item["key"]: item["classification"] for item in indicators}
    return render_template(
        "employee/results.html",
        assessment=record,
        indicators=indicators,
        recommendations=recommendations_for_classifications(classifications),
        likert_labels=LIKERT_LABELS,
        questions=QUESTION_BY_CODE,
    )


@employee_bp.route("/history")
@role_required("employee")
def history():
    filters = read_filters()
    records = history_for(current_user.id, filters.start, filters.before)
    return render_template(
        "employee/history.html",
        assessments=list(reversed(records)),
        chart=chart_payload(records),
        filters=filters,
    )


@employee_bp.route("/complaints")
@role_required("employee")
def complaints():
    filters = read_filters(statuses=("Submitted", "Under Review", "Resolved", "Closed"))
    return render_template(
        "employee/complaints.html",
        complaints=filter_complaints(complaints_for_employee(current_user), filters),
        filters=filters,
    )


@employee_bp.route("/complaints/new", methods=["GET", "POST"])
@role_required("employee")
def submit_complaint():
    form = ComplaintForm()
    if form.validate_on_submit():
        complaint, error = lodge_complaint(
            current_user,
            form.recipient_role.data,
            form.category.data,
            form.subject.data,
            form.description.data,
        )
        if error:
            flash(error, "danger")
        else:
            flash("Complaint submitted.", "success")
            return redirect(url_for("employee.complaint_detail", complaint_id=complaint.id))
    return render_template("employee/submit_complaint.html", form=form)


@employee_bp.route("/complaints/<int:complaint_id>")
@role_required("employee")
def complaint_detail(complaint_id):
    complaint = _own_complaint_or_403(complaint_id)
    return render_template("employee/complaint_detail.html", complaint=complaint)


