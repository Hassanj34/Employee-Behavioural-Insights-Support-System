from app.extensions import db
from app.models.assessment import Assessment
from app.models.complaint import Complaint
from tests.conftest import add_user, login

ANSWERS = {
    "w1": "2",
    "w2": "2",
    "w3": "2",
    "w4": "2",
    "w5": "2",
    "wf1": "2",
    "wf2": "2",
    "m1": "4",
    "m2": "4",
    "m3": "4",
    "m4": "4",
    "m5": "4",
    "l1": "4",
    "l2": "4",
    "l3": "4",
    "l4": "4",
    "l5": "4",
}


def test_employees_cannot_open_each_others_results(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee One", "employee.one@ebiss.local", "employee", manager)
    add_user("Secret Employee", "employee.two@ebiss.local", "employee", manager)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=ANSWERS)
    with client.application.app_context():
        assessment_id = db.session.query(Assessment).one().id
    client.get("/logout")
    login(client, "employee.one@ebiss.local")
    denied = client.get(f"/employee/results/{assessment_id}")
    assert denied.status_code == 403
    assert b"Secret Employee" not in denied.data


def test_manager_cannot_open_an_unassigned_employee(client, ctx):
    manager_one = add_user("Manager One", "manager.one@ebiss.local", "manager")
    manager_two = add_user("Manager Two", "manager.two@ebiss.local", "manager")
    employee = add_user("Assigned Elsewhere", "employee.four@ebiss.local", "employee", manager_two)
    login(client, manager_one.email)
    denied = client.get(f"/manager/employee/{employee.id}")
    assert denied.status_code == 403
    assert b"Assigned Elsewhere" not in denied.data


def test_manager_cannot_open_hr_complaints(client, ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("HR One", "hr.one@ebiss.local", "hr")
    add_user("Employee One", "employee.one@ebiss.local", "employee", manager)
    login(client, "employee.one@ebiss.local")
    client.post(
        "/employee/complaints/new",
        data={
            "recipient_role": "hr",
            "category": "Workplace Treatment",
            "subject": "Private HR matter",
            "description": "This description must stay with HR only.",
        },
    )
    with client.application.app_context():
        complaint_id = db.session.query(Complaint).one().id
    client.get("/logout")
    login(client, manager.email)
    list_page = client.get("/hr/complaints")
    detail = client.get(f"/hr/complaints/{complaint_id}")
    assert list_page.status_code == 403
    assert detail.status_code == 403
    assert b"Private HR matter" not in list_page.data
    assert b"stay with HR only" not in detail.data


def test_hr_cannot_open_senior_manager_complaints(client, ctx):
    add_user("HR One", "hr.one@ebiss.local", "hr")
    add_user("Senior Manager One", "senior.manager@ebiss.local", "senior_manager")
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee One", "employee.one@ebiss.local", "employee", manager)
    login(client, "employee.one@ebiss.local")
    client.post(
        "/employee/complaints/new",
        data={
            "recipient_role": "senior_manager",
            "category": "Recognition or Fairness",
            "subject": "Escalated recognition concern",
            "description": "Only the senior manager should read this description.",
        },
    )
    with client.application.app_context():
        complaint_id = db.session.query(Complaint).one().id
    client.get("/logout")
    login(client, "hr.one@ebiss.local")
    denied = client.get(f"/senior-manager/complaints/{complaint_id}")
    queue = client.get("/senior-manager/complaints")
    assert denied.status_code == 403
    assert queue.status_code == 403
    assert b"Escalated recognition concern" not in denied.data
    assert b"Only the senior manager" not in denied.data
