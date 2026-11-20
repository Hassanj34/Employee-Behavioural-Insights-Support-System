from tests.conftest import add_user, login


def test_each_role_reaches_its_dashboard(client, ctx):
    add_user("Manager One", "manager.one@ebiss.local", "manager")
    add_user("Employee One", "employee.one@ebiss.local", "employee")
    add_user("HR One", "hr.one@ebiss.local", "hr")
    add_user("Senior Manager One", "senior.manager@ebiss.local", "senior_manager")

    expectations = {
        "employee.one@ebiss.local": "/employee/dashboard",
        "manager.one@ebiss.local": "/manager/dashboard",
        "hr.one@ebiss.local": "/hr/dashboard",
        "senior.manager@ebiss.local": "/senior-manager/dashboard",
    }
    for email, location in expectations.items():
        client.get("/logout")
        response = login(client, email)
        assert response.status_code == 302
        assert response.location.endswith(location)


def test_bad_password_is_rejected(client, ctx):
    add_user("Employee One", "employee.one@ebiss.local", "employee")
    response = login(client, "employee.one@ebiss.local", "wrong-password")
    assert response.status_code == 200
    assert b"incorrect" in response.data


def test_anonymous_user_is_sent_to_login(client):
    response = client.get("/employee/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location
