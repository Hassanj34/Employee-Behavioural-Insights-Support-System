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


def test_every_role_can_open_their_own_profile(client, ctx):
    senior = add_user(
        "Zara Qureshi",
        "zara.qureshi@systems.local",
        "senior_manager",
        department="Corporate Office",
        designation="Director, Karachi",
    )
    manager = add_user(
        "Imran Sheikh",
        "imran.sheikh@systems.local",
        "manager",
        senior,
        department="Digital Services",
        designation="Delivery Manager",
    )
    add_user(
        "Ayesha Khan",
        "ayesha.khan@systems.local",
        "employee",
        manager,
        department="Digital Services",
        designation="Software Engineer",
    )
    add_user(
        "Nadia Hussain",
        "nadia.hussain@systems.local",
        "hr",
        department="People and Culture",
        designation="HR Business Partner",
    )

    expectations = {
        "ayesha.khan@systems.local": (b"Ayesha Khan", b"Software Engineer", b"Imran Sheikh", True),
        "imran.sheikh@systems.local": (b"Imran Sheikh", b"Delivery Manager", b"Zara Qureshi", True),
        "nadia.hussain@systems.local": (b"Nadia Hussain", b"HR Business Partner", b"HR Representative", False),
        "zara.qureshi@systems.local": (b"Zara Qureshi", b"Director, Karachi", b"Senior Manager", False),
    }
    for email, (own_name, designation, visible_detail, shows_manager) in expectations.items():
        client.get("/logout")
        login(client, email)
        page = client.get("/profile")
        assert page.status_code == 200
        assert b'href="/profile"' in page.data
        assert own_name in page.data
        assert email.encode() in page.data
        assert designation in page.data
        assert visible_detail in page.data
        assert (b"<dt>Manager</dt>" in page.data) is shows_manager


def test_anonymous_user_is_sent_to_login(client):
    response = client.get("/employee/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location
