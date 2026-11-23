from app.extensions import db
from app.models.complaint import Complaint
from app.models.notification import Notification
from tests.conftest import add_user, login

LOW_WORKLOAD = {
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


def test_alert_notifies_only_the_assigned_manager(client, ctx):
    manager = add_user("Imran Sheikh", "imran.sheikh@systems.local", "manager")
    other = add_user("Hira Baig", "hira.baig@systems.local", "manager")
    employee = add_user("Private Employee", "private.employee@systems.local", "employee", manager)

    login(client, employee.email)
    submitted = client.post("/employee/assessment", data=LOW_WORKLOAD)
    assert submitted.status_code == 302
    own_page = client.get("/employee/dashboard")
    assert b"notify-badge" not in own_page.data
    assert b"notify-item" not in own_page.data

    client.get("/logout")
    login(client, other.email)
    other_page = client.get("/manager/dashboard")
    assert other_page.status_code == 200
    assert b"Private Employee" not in other_page.data
    assert b"notify-badge" not in other_page.data

    client.get("/logout")
    login(client, manager.email)
    page = client.get("/manager/dashboard")
    assert page.status_code == 200
    assert b"notify-badge" in page.data
    assert b"Private Employee" in page.data
    assert b"Workload" in page.data
    assert b'href="/manager/alerts/' in page.data

    with client.application.app_context():
        note = db.session.query(Notification).one()
        assert note.recipient_id == manager.id
        assert note.cleared_at is None

    assert b'class="notify-badge">1<' in page.data
    assert b"Clear all" in page.data
    cleared = client.post("/notifications/clear")
    assert cleared.status_code == 200
    after = client.get("/manager/dashboard")
    assert b"notify-badge" not in after.data
    assert b"notify-item" not in after.data
    assert b"Private Employee" in after.data
    reloaded = client.get("/manager/dashboard")
    assert b"notify-badge" not in reloaded.data


def test_badge_counts_every_alert_for_that_manager(client, ctx):
    manager = add_user("Imran Sheikh", "imran.sheikh@systems.local", "manager")
    other = add_user("Hira Baig", "hira.baig@systems.local", "manager")
    first = add_user("First Employee", "first.employee@systems.local", "employee", manager)
    second = add_user("Second Employee", "second.employee@systems.local", "employee", manager)
    outside = add_user("Outside Employee", "outside.employee@systems.local", "employee", other)

    for person in (first, second, outside):
        login(client, person.email)
        client.post("/employee/assessment", data=LOW_WORKLOAD)
        client.get("/logout")

    login(client, manager.email)
    page = client.get("/manager/dashboard")
    assert b'class="notify-badge">2<' in page.data
    assert b"First Employee" in page.data
    assert b"Second Employee" in page.data
    assert b"Outside Employee" not in page.data

    client.post("/notifications/clear")
    client.get("/logout")
    login(client, other.email)
    other_page = client.get("/manager/dashboard")
    assert b'class="notify-badge">1<' in other_page.data
    assert b"Outside Employee" in other_page.data
    assert b"First Employee" not in other_page.data


def test_opening_notifications_clears_the_badge_but_keeps_the_list(client, ctx):
    manager = add_user("Imran Sheikh", "imran.sheikh@systems.local", "manager")
    other = add_user("Hira Baig", "hira.baig@systems.local", "manager")
    employee = add_user("Private Employee", "private.employee@systems.local", "employee", manager)
    outside = add_user("Outside Employee", "outside.employee@systems.local", "employee", other)
    login(client, employee.email)
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.get("/logout")
    login(client, outside.email)
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.get("/logout")

    login(client, manager.email)
    opened = client.post("/notifications/read")
    assert opened.status_code == 200
    page = client.get("/manager/dashboard")
    assert b"notify-badge" not in page.data
    assert b"Private Employee" in page.data
    assert b"Workload" in page.data
    with client.application.app_context():
        note = db.session.query(Notification).filter_by(recipient_id=manager.id).one()
        assert note.read_at is not None
        assert note.cleared_at is None

    client.get("/logout")
    login(client, other.email)
    other_page = client.get("/manager/dashboard")
    assert b'class="notify-badge">1<' in other_page.data
    assert b"Outside Employee" in other_page.data


def test_complaint_and_follow_up_notify_only_the_relevant_person(client, ctx):
    manager = add_user("Imran Sheikh", "imran.sheikh@systems.local", "manager")
    other_manager = add_user("Hira Baig", "hira.baig@systems.local", "manager")
    employee = add_user("Ayesha Khan", "ayesha.khan@systems.local", "employee", manager)
    hr = add_user("Nadia Hussain", "nadia.hussain@systems.local", "hr")
    other_hr = add_user("Second HR", "second.hr@systems.local", "hr")
    senior = add_user("Zara Qureshi", "zara.qureshi@systems.local", "senior_manager")

    login(client, employee.email)
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.post(
        "/employee/complaints/new",
        data={
            "recipient_role": "hr",
            "category": "Workplace Treatment",
            "subject": "Private HR matter",
            "description": "This description must stay with HR only.",
        },
    )
    client.get("/logout")

    login(client, hr.email)
    hr_page = client.get("/hr/dashboard")
    assert b'class="notify-badge">1<' in hr_page.data
    assert b"Private HR matter" in hr_page.data
    assert b'href="/hr/complaints/' in hr_page.data
    client.get("/logout")

    for email in (other_hr.email, manager.email, senior.email, employee.email):
        login(client, email)
        page = client.get("/profile")
        assert b"Private HR matter" not in page.data
        client.get("/logout")

    login(client, manager.email)
    with client.application.app_context():
        from app.models.alert import Alert

        alert_id = db.session.query(Alert).filter_by(manager_id=manager.id).one().id
    recorded = client.post(
        f"/manager/alerts/{alert_id}/follow-up",
        data={
            "action_description": "Moved two tasks off the Karachi release week.",
            "remarks": "Review after the next check-in.",
            "status": "In Progress",
        },
    )
    assert recorded.status_code == 302
    with client.application.app_context():
        from app.models.follow_up import FollowUpAction

        action_id = db.session.query(FollowUpAction).one().id
    reviewed = client.post(
        f"/manager/alerts/{alert_id}/follow-up/{action_id}/review",
        data={"usefulness": "Useful", "usefulness_note": "The next sprint had fewer collisions."},
    )
    assert reviewed.status_code == 302
    manager_page = client.get("/manager/dashboard")
    assert b"Moved two tasks" not in manager_page.data
    client.get("/logout")

    login(client, employee.email)
    employee_page = client.get("/employee/dashboard")
    assert b"Workload follow-up is In Progress" in employee_page.data
    assert b"Moved two tasks off the Karachi release week." in employee_page.data
    assert b"follow-up marked Useful" in employee_page.data
    assert b'href="/employee/results/' in employee_page.data
    client.get("/logout")

    login(client, other_manager.email)
    assert b"Moved two tasks" not in client.get("/manager/dashboard").data
    client.get("/logout")

    login(client, hr.email)
    with client.application.app_context():
        complaint_id = db.session.query(Complaint).one().id
    client.post(
        f"/hr/complaints/{complaint_id}/update",
        data={"status": "Under Review", "response_text": "We are reviewing this with your manager."},
    )
    hr_after = client.get("/hr/dashboard")
    assert b"We are reviewing this with your manager." not in hr_after.data
    client.get("/logout")

    login(client, employee.email)
    updated = client.get("/employee/dashboard")
    assert b"Private HR matter is now Under Review" in updated.data
    assert b"We are reviewing this with your manager." in updated.data
    assert b'href="/employee/complaints/' in updated.data
    client.get("/logout")

    for email in (manager.email, senior.email, other_hr.email):
        login(client, email)
        assert b"We are reviewing this with your manager." not in client.get("/profile").data
        client.get("/logout")

    login(client, employee.email)
    client.post(
        "/employee/complaints/new",
        data={
            "recipient_role": "senior_manager",
            "category": "Recognition or Fairness",
            "subject": "Escalated recognition concern",
            "description": "Only the senior manager should read this description.",
        },
    )
    client.get("/logout")
    login(client, senior.email)
    senior_page = client.get("/senior-manager/dashboard")
    assert b"Escalated recognition concern" in senior_page.data
    assert b'href="/senior-manager/complaints/' in senior_page.data
    client.get("/logout")
    login(client, hr.email)
    assert b"Escalated recognition concern" not in client.get("/hr/dashboard").data
