"""Query-string filters for dashboards, employee lists, and alerts."""

from datetime import datetime, timedelta
from types import SimpleNamespace

from flask import request

from app.services.assessment_engine import (
    ATTENTION,
    DIMENSIONS,
    DIMENSION_LABELS,
    INSUFFICIENT,
    POSITIVE,
    SUPPORT,
)
from app.services.complaint_service import STATUSES as COMPLAINT_STATUSES

CLASSIFICATIONS = (POSITIVE, SUPPORT, ATTENTION, INSUFFICIENT)
DIMENSION_CHOICES = tuple((key, DIMENSION_LABELS[key].split()[0]) for key in DIMENSIONS)
ALERT_STATUSES = ("Open", "In Progress", "Completed")


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def read_filters(classifications=CLASSIFICATIONS, dimensions=DIMENSIONS, statuses=()):
    classification = request.args.get("classification", "").strip()
    if classification not in classifications:
        classification = ""
    dimension = request.args.get("dimension", "").strip()
    if dimension not in dimensions:
        dimension = ""
    status = request.args.get("status", "").strip()
    if status not in statuses:
        status = ""
    start_text = request.args.get("start", "").strip()
    end_text = request.args.get("end", "").strip()
    start = parse_date(start_text)
    end = parse_date(end_text)
    if start is None:
        start_text = ""
    if end is None:
        end_text = ""
    before = end + timedelta(days=1) if end is not None else None
    return SimpleNamespace(
        q=request.args.get("q", "").strip(),
        classification=classification,
        dimension=dimension,
        status=status,
        start_text=start_text,
        end_text=end_text,
        start=start,
        before=before,
        has_dates=start is not None or before is not None,
        active=bool(request.args.get("q", "").strip() or classification or dimension or status or start or before),
    )


def text_match(query, *parts):
    needle = query.casefold()
    haystack = " ".join(part or "" for part in parts).casefold()
    return needle in haystack


def in_window(moment, start, before):
    if start is None and before is None:
        return True
    if moment is None:
        return False
    if start is not None and moment < start:
        return False
    if before is not None and moment >= before:
        return False
    return True


def classification_matches(assessment, classification, dimension):
    if not classification:
        return True
    if assessment is None:
        return classification == INSUFFICIENT
    dims = (dimension,) if dimension in DIMENSIONS else DIMENSIONS
    return any(assessment.classification_for(item) == classification for item in dims)


def filter_complaints(complaints, filters):
    selected = []
    for complaint in complaints:
        if filters.status and complaint.status != filters.status:
            continue
        if filters.q and not text_match(
            filters.q, complaint.subject, complaint.category, complaint.employee.name
        ):
            continue
        if not in_window(complaint.created_at, filters.start, filters.before):
            continue
        selected.append(complaint)
    return selected


__all__ = [
    "ALERT_STATUSES",
    "CLASSIFICATIONS",
    "COMPLAINT_STATUSES",
    "DIMENSION_CHOICES",
    "classification_matches",
    "filter_complaints",
    "in_window",
    "read_filters",
    "text_match",
]
