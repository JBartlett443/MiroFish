import os
import tempfile

import pytest

from app import create_app
from app import db as db_mod


@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "pw",
            "DATABASE_PATH": path,
        }
    )
    yield app
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield


@pytest.fixture
def login(client):
    client.post("/admin/login", data={"username": "admin", "password": "pw"})
    return client


def seed_user(name="Jane Doe", employee_id="E1"):
    uid = db_mod.execute(
        "INSERT INTO users (name, employee_id) VALUES (?, ?)",
        (name, employee_id),
    )
    return uid


def seed_fob(fob_uid, user_id):
    db_mod.execute(
        "INSERT INTO fobs (fob_uid, user_id) VALUES (?, ?)",
        (fob_uid, user_id),
    )


def seed_scan(user_id, scanned_at, direction, source="fob", fob_uid=None):
    db_mod.execute(
        """
        INSERT INTO scans (fob_uid, user_id, scanned_at, direction, entry_source, created_by)
        VALUES (?, ?, ?, ?, ?, 'test')
        """,
        (fob_uid, user_id, scanned_at, direction, source),
    )
