from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.auth.decorators import role_required
from app.extensions import db
from app.forms import AlertSettingsForm, ComplaintUpdateForm
from app.models.complaint import Complaint
from app.query_filters import filter_complaints, read_filters
from app.services.alert_settings import get_alert_settings, update_alert_settings
from app.services.complaint_service import (
    add_complaint_update,
    complaint_counts,
    complaints_for_recipient,
)

senior_manager_bp = Blueprint("senior_manager", __name__)


def _own_complaint_or_403(complaint_id):
    complaint = db.session.get(Complaint, complaint_id)
    if complaint is None:
        abort(404)
    if complaint.recipient_id != current_user.id or current_user.role != "senior_manager":
        abort(403)
    return complaint


def _queue():
    filters = read_filters(statuses=("Submitted", "Under Review", "Resolved", "Closed"))
    complaints = filter_complaints(complaints_for_recipient(current_user), filters)
    return filters, complaints


@senior_manager_bp.route("/dashboard")
@role_required("senior_manager")
def dashboard():
    filters, complaints = _queue()
    return render_template(
        "senior_manager/dashboard.html",
        complaints=complaints,
        counts=complaint_counts(complaints),
        filters=filters,
    )


@senior_manager_bp.route("/complaints")
@role_required("senior_manager")
def complaints():
    filters, complaints = _queue()
    return render_template(
        "senior_manager/complaints.html",
        complaints=complaints,
        filters=filters,
    )


@senior_manager_bp.route("/complaints/<int:complaint_id>")
@role_required("senior_manager")
def complaint_detail(complaint_id):
    complaint = _own_complaint_or_403(complaint_id)
    return render_template(
        "senior_manager/complaint_details.html",
        complaint=complaint,
        form=ComplaintUpdateForm(status=complaint.status),
    )


@senior_manager_bp.route("/complaints/<int:complaint_id>/update", methods=["POST"])
@role_required("senior_manager")
def update_complaint(complaint_id):
    complaint = _own_complaint_or_403(complaint_id)
    form = ComplaintUpdateForm()
    if form.validate_on_submit():
        try:
            add_complaint_update(
                complaint,
                current_user,
                form.status.data,
                form.response_text.data,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
        else:
            flash("Complaint updated.", "success")
            return redirect(url_for("senior_manager.complaint_detail", complaint_id=complaint.id))
    return render_template("senior_manager/complaint_details.html", complaint=complaint, form=form), 400


@senior_manager_bp.route("/settings", methods=["GET", "POST"])
@role_required("senior_manager")
def settings():
    current = get_alert_settings()
    if request.method == "GET":
        form = AlertSettingsForm(
            data={
                "positive_min": current.positive_min,
                "support_min": current.support_min,
                "significant_drop": current.significant_drop,
            }
        )
    else:
        form = AlertSettingsForm()
    if form.validate_on_submit():
        try:
            update_alert_settings(
                form.positive_min.data,
                form.support_min.data,
                form.significant_drop.data,
                current_user,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
        else:
            flash("Alert rules saved. New check-ins use these rules.", "success")
            return redirect(url_for("senior_manager.settings"))
    return render_template("senior_manager/settings.html", form=form, settings=current)
