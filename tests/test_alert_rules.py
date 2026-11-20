from app.extensions import db
from app.models.alert import Alert
from app.models.follow_up import FollowUpAction
from app.services.alert_settings import get_alert_settings
from app.services.assessment_engine import SIGNIFICANT
from tests.conftest import add_user, login

HIGH = {"w1": "5", "w2": "5", "w3": "5", "m1": "5", "m2": "5", "m3": "5", "l1": "5", "l2": "5", "l3": "5"}
MOTIVATION_DROP = {
    "w1": "5",
    "w2": "5",
    "w3": "5",
    "m1": "3",
    "m2": "3",
    "m3": "4",
    "l1": "5",
    "l2": "5",
    "l3": "5",
}
LOW_WORKLOAD = {
    "w1": "2",
    "w2": "2",
    "w3": "2",
    "wf1": "2",
    "wf2": "2",
    "m1": "4",
    "m2": "4",
    "m3": "4",
    "l1": "4",
    "l2": "4",
    "l3": "4",
}


def _people():
    manager = add_user("Imran Sheikh", "imran.sheikh@systems.local", "manager")
    employee = add_user("Sana Iqbal", "sana.iqbal@systems.local", "employee", manager)
    return manager, employee


def test_score_drop_above_attention_line_opens_an_alert(client, ctx):
    _people()
    login(client, "sana.iqbal@systems.local")
    client.post("/employee/assessment", data=HIGH)
    client.post("/employee/assessment", data=MOTIVATION_DROP)
    with client.application.app_context():
        alerts = db.session.query(Alert).all()
        assert len(alerts) == 1
        assert alerts[0].dimension == "Motivation"
        assert alerts[0].classification == SIGNIFICANT
        assert "fell by" in alerts[0].explanation
    client.get("/logout")
    login(client, "imran.sheikh@systems.local")
    page = client.get("/manager/alerts")
    assert b"Significant Change" in page.data
    assert b"Sana Iqbal" in page.data


def test_support_score_without_a_prior_result_does_not_alert(client, ctx):
    _people()
    login(client, "sana.iqbal@systems.local")
    client.post("/employee/assessment", data=MOTIVATION_DROP)
    with client.application.app_context():
        assert db.session.query(Alert).count() == 0


def test_senior_manager_can_raise_the_change_threshold(client, ctx):
    _people()
    add_user("Zara Qureshi", "zara.qureshi@systems.local", "senior_manager")
    login(client, "imran.sheikh@systems.local")
    assert client.get("/senior-manager/settings").status_code == 403
    client.get("/logout")
    login(client, "zara.qureshi@systems.local")
    saved = client.post(
        "/senior-manager/settings",
        data={"positive_min": "3.50", "support_min": "2.50", "significant_drop": "2.00"},
        follow_redirects=True,
    )
    assert b"Alert rules saved." in saved.data
    client.get("/logout")
    login(client, "sana.iqbal@systems.local")
    client.post("/employee/assessment", data=HIGH)
    client.post("/employee/assessment", data=MOTIVATION_DROP)
    with client.application.app_context():
        assert db.session.query(Alert).count() == 0
        assert get_alert_settings().significant_drop == 2


def test_manager_can_rate_whether_a_follow_up_was_useful(client, ctx):
    manager, _employee = _people()
    manager_email = manager.email
    login(client, "sana.iqbal@systems.local")
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.get("/logout")
    login(client, manager_email)
    with client.application.app_context():
        alert_id = db.session.query(Alert).one().id
    recorded = client.post(
        f"/manager/alerts/{alert_id}/follow-up",
        data={
            "action_description": "Moved two tasks off the Karachi release week.",
            "remarks": "Review after the next check-in.",
            "status": "Completed",
        },
        follow_redirects=True,
    )
    assert b"Was this follow-up useful?" in recorded.data
    with client.application.app_context():
        action_id = db.session.query(FollowUpAction).one().id
    reviewed = client.post(
        f"/manager/alerts/{alert_id}/follow-up/{action_id}/review",
        data={"usefulness": "Useful", "usefulness_note": "The next sprint plan had fewer collisions."},
        follow_redirects=True,
    )
    assert b"Usefulness review saved." in reviewed.data
    with client.application.app_context():
        action = db.session.get(FollowUpAction, action_id)
        assert action.usefulness == "Useful"
        assert action.reviewed_at is not None
