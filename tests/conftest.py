import os
import tempfile
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db
from config import TestConfig

PASSWORD = "Demo@2026"


@pytest.fixture
def app():
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)

    class LocalConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + Path(path).as_posix()

    application = create_app(LocalConfig)
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()
    os.remove(path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield


def add_user(name, email, role, manager=None, department="Product Engineering", designation="Team Member"):
    from app.models.user import User

    user = User(
        name=name,
        email=email,
        role=role,
        department=department,
        designation=designation,
        is_active=True,
        manager_id=manager.id if manager else None,
    )
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email, password=PASSWORD):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
