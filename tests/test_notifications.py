from app.extensions import db
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
