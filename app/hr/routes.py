from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from app.auth.decorators import role_required
from app.extensions import db
from app.forms import ComplaintUpdateForm
from app.models.complaint import Complaint
from app.query_filters import filter_complaints, read_filters
from app.services.complaint_service import (
    add_complaint_update,
    complaint_counts,
    complaints_for_recipient,
)

hr_bp = Blueprint("hr", __name__)


def _own_complaint_or_403(complaint_id):
    complaint = db.session.get(Complaint, complaint_id)
    if complaint is None:
        abort(404)
    if complaint.recipient_id != current_user.id or current_user.role != "hr":
        abort(403)
    return complaint


def _queue():
    filters = read_filters(statuses=("Submitted", "Under Review", "Resolved", "Closed"))
    complaints = filter_complaints(complaints_for_recipient(current_user), filters)
    return filters, complaints


@hr_bp.route("/dashboard")
@role_required("hr")
def dashboard():
    filters, complaints = _queue()
    return render_template(
        "hr/dashboard.html",
        complaints=complaints,
        counts=complaint_counts(complaints),
        filters=filters,
    )


@hr_bp.route("/complaints")
@role_required("hr")
def complaints():
    filters, complaints = _queue()
    return render_template("hr/complaints.html", complaints=complaints, filters=filters)


@hr_bp.route("/complaints/<int:complaint_id>")
@role_required("hr")
def complaint_detail(complaint_id):
    complaint = _own_complaint_or_403(complaint_id)
    return render_template(
        "hr/complaint_details.html",
        complaint=complaint,
        form=ComplaintUpdateForm(status=complaint.status),
    )


@hr_bp.route("/complaints/<int:complaint_id>/update", methods=["POST"])
@role_required("hr")
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
            return redirect(url_for("hr.complaint_detail", complaint_id=complaint.id))
    return render_template("hr/complaint_details.html", complaint=complaint, form=form), 400
