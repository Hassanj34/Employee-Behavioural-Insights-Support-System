from datetime import datetime

from app.extensions import db
from app.models.assessment import Assessment
from tests.conftest import add_user, login

from tests.test_assessments import LOW_WORKLOAD, WORKLOAD_HIGH, WORKLOAD_LOW


def _without_notifications(response):
    html = response.get_data(as_text=True)
    start = html.find('<div class="notify">')
    end = html.find('<span class="avatar"')
    if start != -1 and end != -1:
        html = html[:start] + html[end:]
    return html.encode()


def test_employee_search_and_classification_filter(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee Two", "employee.two@ebiss.local", "employee", manager)
    add_user("Quiet Person", "quiet.person@ebiss.local", "employee", manager, designation="Researcher")
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.get("/logout")
    login(client, "manager.one@ebiss.local")

    by_name = client.get("/manager/employees", query_string={"q": "Quiet"})
    assert b"Quiet Person" in by_name.data
    assert b"Employee Two" not in _without_notifications(by_name)

    by_role = client.get("/manager/employees", query_string={"q": "Researcher"})
    assert b"Quiet Person" in by_role.data
    assert b"Employee Two" not in _without_notifications(by_role)

    hidden = client.get(
        "/manager/employees",
        query_string={"dimension": "workload", "classification": "Positive / Balanced"},
    )
    assert b"Employee Two" not in _without_notifications(hidden)
    assert b"No employees match these filters." in hidden.data

    shown = client.get(
        "/manager/employees",
        query_string={"dimension": "motivation", "classification": "Positive / Balanced"},
    )
    assert b"Employee Two" in shown.data


def test_alert_filters_by_area_classification_and_status(client, ctx):
    _manager_and_employee(client, ctx)
    login(client, "manager.one@ebiss.local")

    other_area = client.get("/manager/alerts", query_string={"dimension": "learning"})
    assert b"Employee Two" not in _without_notifications(other_area)
    assert b"No alerts match these filters." in other_area.data
    assert b"Learning Confidence" not in other_area.data

    attention = client.get("/manager/alerts", query_string={"classification": "Attention Required"})
    assert b"Employee Two" in attention.data
    assert b"Workload" in attention.data

    positive = client.get("/manager/alerts", query_string={"classification": "Positive / Balanced"})
    assert b"Employee Two" not in _without_notifications(positive)

    open_only = client.get("/manager/alerts", query_string={"status": "Open"})
    assert b"Employee Two" in open_only.data
    completed = client.get("/manager/alerts", query_string={"status": "Completed"})
    assert b"No alerts match these filters." in completed.data


def test_dashboard_and_history_date_filters(client, ctx):
    _manager_and_employee(client, ctx)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=WORKLOAD_HIGH)
    with client.application.app_context():
        rows = db.session.scalars(db.select(Assessment).order_by(Assessment.id)).all()
        rows[0].submission_date = datetime(2026, 1, 15, 9, 0)
        rows[1].submission_date = datetime(2026, 6, 2, 9, 0)
        db.session.commit()

    early = client.get("/employee/history", query_string={"start": "2026-01-01", "end": "2026-01-31"})
    early_text = early.get_data(as_text=True)
    assert "2.00" in early_text
    assert "15 Jan 2026" in early_text
    assert "02 Jun 2026" not in early_text

    later = client.get("/employee/history", query_string={"start": "2026-06-01", "end": "2026-06-30"})
    later_text = later.get_data(as_text=True)
    assert "4.00" in later_text
    assert "2.00" not in later_text
    assert b"Print summary" in later.data

    client.get("/logout")
    login(client, "manager.one@ebiss.local")
    empty_window = client.get(
        "/manager/dashboard",
        query_string={"start": "2026-03-01", "end": "2026-03-31"},
    )
    assert b"No check-in in this date range." in empty_window.data
    assert b"Employee Two" in empty_window.data


def test_printable_summary_and_complaint_date_filter(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    employee = add_user("Employee Two", "employee.two@ebiss.local", "employee", manager)
    employee_id = employee.id
    add_user("HR One", "hr.one@ebiss.local", "hr")
    login(client, "employee.two@ebiss.local")
    submitted = client.post("/employee/assessment", data=LOW_WORKLOAD, follow_redirects=True)
    assert b"Print summary" in submitted.data
    client.post(
        "/employee/complaints/new",
        data={
            "recipient_role": "hr",
            "category": "Promotion or Career Progression",
            "subject": "Promotion decision concern",
            "description": "The promotion timeline and criteria were not explained.",
        },
    )
    client.get("/logout")
    login(client, "manager.one@ebiss.local")
    detail = client.get(f"/manager/employee/{employee_id}")
    assert b"Print summary" in detail.data
    client.get("/logout")
    login(client, "hr.one@ebiss.local")
    future = client.get("/hr/dashboard", query_string={"start": "2099-01-01"})
    assert b"Promotion decision concern" not in _without_notifications(future)
    assert b"No complaints match these filters." in future.data
    current = client.get("/hr/dashboard", query_string={"status": "Submitted"})
    assert b"Promotion decision concern" in current.data


def _manager_and_employee(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee Two", "employee.two@ebiss.local", "employee", manager)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=WORKLOAD_LOW)
    client.get("/logout")
