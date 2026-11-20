from app.extensions import db
from app.models.assessment import Assessment
from app.models.complaint import Complaint
from tests.conftest import add_user, login

PROMOTION = {
    "recipient_role": "hr",
    "category": "Promotion or Career Progression",
    "subject": "Promotion decision concern",
    "description": "I would like the promotion timeline and criteria to be reviewed.",
}


def test_hr_complaint_is_hidden_from_manager_and_senior_manager(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    other_manager = add_user("Manager Two", "manager.two@ebiss.local", "manager")
    employee = add_user("Employee One", "employee.one@ebiss.local", "employee", manager)
    hr = add_user("HR One", "hr.one@ebiss.local", "hr")
    senior = add_user("Senior Manager One", "senior.manager@ebiss.local", "senior_manager")

    login(client, employee.email)
    created = client.post("/employee/complaints/new", data=PROMOTION, follow_redirects=True)
    assert b"Promotion decision concern" in created.data
    assert b"Submitted" in created.data

    with client.application.app_context():
        complaint = db.session.query(Complaint).one()
        complaint_id = complaint.id
        assert complaint.recipient_id == hr.id

    client.get("/logout")
    login(client, hr.email)
    hr_page = client.get(f"/hr/complaints/{complaint_id}")
    assert hr_page.status_code == 200
    assert b"Promotion decision concern" in hr_page.data

    updated = client.post(
        f"/hr/complaints/{complaint_id}/update",
        data={"status": "Under Review", "response_text": "We are reviewing the promotion timeline."},
        follow_redirects=True,
    )
    assert b"Under Review" in updated.data

    client.get("/logout")
    login(client, employee.email)
    own = client.get(f"/employee/complaints/{complaint_id}")
    assert b"Under Review" in own.data
    assert b"reviewing the promotion timeline" in own.data

    for email in (manager.email, other_manager.email, senior.email):
        client.get("/logout")
        login(client, email)
        denied = client.get(f"/hr/complaints/{complaint_id}")
        assert denied.status_code == 403
        assert b"Promotion decision concern" not in denied.data
        assert b"promotion timeline and criteria" not in denied.data


def test_second_hr_account_cannot_open_another_hr_queue(client, ctx):
    add_user("HR One", "hr.one@ebiss.local", "hr")
    hr_two = add_user("HR Two", "hr.two@ebiss.local", "hr")
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee One", "employee.one@ebiss.local", "employee", manager)
    login(client, "employee.one@ebiss.local")
    client.post("/employee/complaints/new", data=PROMOTION)
    with client.application.app_context():
        complaint_id = db.session.query(Complaint).one().id
    client.get("/logout")
    login(client, hr_two.email)
    denied = client.get(f"/hr/complaints/{complaint_id}")
    assert denied.status_code == 403
    queue = client.get("/hr/complaints")
    assert b"Promotion decision concern" not in queue.data
