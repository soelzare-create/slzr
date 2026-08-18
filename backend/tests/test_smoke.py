"""Phase 1 smoke tests — foundation: auth, users, and RBAC.

Runs against a throwaway SQLite database so it never touches the dev data.
"""
from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a temp DB *before* importing app modules.
_tmp_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(
        User(
            name="مدیر تست",
            role=UserRole.manager,
            phone="09120000000",
            password_hash=hash_password("admin1234"),
        )
    )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _login(phone: str, password: str) -> str:
    resp = client.post(
        "/api/auth/login", data={"username": phone, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_root_and_health():
    assert client.get("/health").json() == {"status": "ok"}
    assert "motto" in client.get("/").json()


def test_login_wrong_password():
    resp = client.post(
        "/api/auth/login", data={"username": "09120000000", "password": "nope"}
    )
    assert resp.status_code == 401


def test_login_and_me():
    token = _login("09120000000", "admin1234")
    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["role"] == "manager"


def test_manager_creates_user_and_rbac_blocks_non_manager():
    manager_token = _login("09120000000", "admin1234")

    # Manager can create a sales user.
    resp = client.post(
        "/api/users",
        headers=_auth(manager_token),
        json={
            "name": "فروشنده یک",
            "role": "sales",
            "phone": "09121111111",
            "password": "sales1234",
        },
    )
    assert resp.status_code == 201, resp.text

    # The sales user can log in and read /me...
    sales_token = _login("09121111111", "sales1234")
    assert client.get("/api/auth/me", headers=_auth(sales_token)).status_code == 200

    # ...but cannot access manager-only user administration.
    forbidden = client.get("/api/users", headers=_auth(sales_token))
    assert forbidden.status_code == 403


def test_unauthenticated_is_rejected():
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/users").status_code == 401


def test_duplicate_phone_conflict():
    manager_token = _login("09120000000", "admin1234")
    payload = {
        "name": "تکراری",
        "role": "technical",
        "phone": "09120000000",  # already exists
        "password": "pass1234",
    }
    resp = client.post("/api/users", headers=_auth(manager_token), json=payload)
    assert resp.status_code == 409
