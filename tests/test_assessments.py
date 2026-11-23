from app.extensions import db
from app.models.alert import Alert
from app.models.assessment import Assessment
from tests.conftest import add_user, login

LOW_WORKLOAD = {
    "w1": "2",
    "w2": "2",
    "w3": "3",
    "w4": "3",
    "w5": "3",
    "wf1": "2",
    "wf2": "1",
    "m1": "4",
    "m2": "5",
    "m3": "4",
    "m4": "4",
    "m5": "4",
    "l1": "4",
    "l2": "4",
    "l3": "5",
    "l4": "5",
    "l5": "5",
}
LOW_LEARNING = {
    "w1": "4",
    "w2": "4",
    "w3": "5",
    "w4": "5",
    "w5": "5",
    "m1": "4",
    "m2": "5",
    "m3": "4",
    "m4": "4",
    "m5": "4",
    "l1": "2",
    "l2": "3",
    "l3": "2",
    "l4": "2",
    "l5": "2",
    "lf1": "2",
    "lf2": "2",
}
MIXED = {
    "w1": "2",
    "w2": "2",
    "w3": "2",
    "w4": "2",
    "w5": "2",
    "m1": "5",
    "m2": "5",
    "m3": "5",
    "m4": "5",
    "m5": "5",
    "l1": "2",
    "l2": "2",
    "l3": "2",
    "l4": "2",
    "l5": "2",
    "wf1": "2",
    "wf2": "2",
    "lf1": "1",
    "lf2": "2",
}
SUPPORT_ONLY = {
    "w1": "3",
    "w2": "3",
    "w3": "3",
    "w4": "3",
    "w5": "3",
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
WORKLOAD_LOW = {
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
WORKLOAD_HIGH = {
    "w1": "4",
    "w2": "4",
    "w3": "4",
    "w4": "4",
    "w5": "4",
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


def _people(ctx):
    manager = add_user("Manager One", "manager.one@ebiss.local", "manager")
    employee = add_user("Employee Two", "employee.two@ebiss.local", "employee", manager)
    return manager, employee


def test_workload_attention_creates_manager_alert(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    response = client.post("/employee/assessment", data=LOW_WORKLOAD, follow_redirects=True)
    assert response.status_code == 200
    assert b"Attention Required" in response.data
    assert b"Positive / Balanced" in response.data
    assert b"workload pressure" in response.data
    assert b"Overall score" not in response.data
    page = response.get_data(as_text=True)
    assert "2.29" in page

    client.get("/logout")
    login(client, "manager.one@ebiss.local")
    dashboard = client.get("/manager/dashboard")
    assert b"Employee Two" in dashboard.data
    assert b"Attention Required" in dashboard.data
    alerts = client.get("/manager/alerts")
    assert b"Workload" in alerts.data
    assert b"Learning Confidence" not in alerts.data


def test_learning_attention_recommends_mentoring(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    response = client.post("/employee/assessment", data=LOW_LEARNING, follow_redirects=True)
    assert b"mentoring" in response.data
    assert b"Learning Confidence" in response.data


def test_mixed_result_is_not_combined(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    response = client.post("/employee/assessment", data=MIXED, follow_redirects=True)
    text = response.get_data(as_text=True)
    assert text.count("Attention Required") >= 2
    assert "Positive / Balanced" in text
    assert "individual discussion" in text


def test_support_recommended_does_not_open_an_alert(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=SUPPORT_ONLY)
    with client.application.app_context():
        assert db.session.query(Alert).count() == 0


def test_disagreement_requires_follow_up_questions(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    incomplete = dict(LOW_WORKLOAD)
    incomplete.pop("wf1")
    incomplete.pop("wf2")
    response = client.post("/employee/assessment", data=incomplete)
    assert response.status_code == 200
    assert b"follow-up" in response.data.lower()
    with client.application.app_context():
        assert db.session.query(Assessment).count() == 0


def test_incomplete_assessment_is_not_stored(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    response = client.post("/employee/assessment", data={"w1": "2"})
    assert response.status_code == 200
    with client.application.app_context():
        assert db.session.query(Assessment).count() == 0


def test_history_keeps_both_submissions_in_order(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=WORKLOAD_LOW)
    client.post("/employee/assessment", data=WORKLOAD_HIGH)
    history = client.get("/employee/history")
    text = history.get_data(as_text=True)
    assert "2.00" in text
    assert "4.00" in text
    with client.application.app_context():
        rows = db.session.query(Assessment).order_by(Assessment.submission_date.asc(), Assessment.id.asc()).all()
        assert len(rows) == 2
        assert rows[0].workload_score == 2
        assert rows[1].workload_score == 4


def test_manager_can_record_follow_up(client, ctx):
    _people(ctx)
    login(client, "employee.two@ebiss.local")
    client.post("/employee/assessment", data=LOW_WORKLOAD)
    client.get("/logout")
    login(client, "manager.one@ebiss.local")
    with client.application.app_context():
        alert = db.session.query(Alert).one()
        alert_id = alert.id
    response = client.post(
        f"/manager/alerts/{alert_id}/follow-up",
        data={
            "action_description": "Discussed current responsibilities and identified conflicting deadlines.",
            "remarks": "Priorities were clarified.",
            "status": "Completed",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Follow-up recorded." in response.data
    with client.application.app_context():
        alert = db.session.get(Alert, alert_id)
        assert alert.status == "Completed"
        assert len(alert.follow_ups) == 1
