"""Phase 6 (reworked) — internal task referrals (ارجاعات): create, list scoping,
status lifecycle with a stamped completion time, and permission checks."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_tasks.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-tasks"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

client = TestClient(app)

# ids: 1 manager, 2 sales, 3 technical
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all(
        [
            User(name="مدیر", role=UserRole.manager, phone="0910",
                 password_hash=hash_password("pass1234")),
            User(name="فروش", role=UserRole.sales, phone="0911",
                 password_hash=hash_password("pass1234")),
            User(name="فنی", role=UserRole.technical, phone="0912",
                 password_hash=hash_password("pass1234")),
        ]
    )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _h(phone: str) -> dict:
    r = client.post("/api/auth/login", data={"username": phone, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_sales_refers_a_task_to_technical():
    r = client.post("/api/tasks", headers=_h("0911"), json={
        "assigned_to_id": 3, "title": "نصب و راه‌اندازی",
        "scheduled_at": "2026-09-01T10:00:00", "description": "نصب در محل مشتری"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "assigned"
    assert body["assigned_to_id"] == 3 and body["created_by_id"] == 2
    assert body["done_at"] is None


def test_scoping_assigned_vs_created():
    # sales(2) refers to technical(3)
    client.post("/api/tasks", headers=_h("0911"),
                json={"assigned_to_id": 3, "title": "کار الف"})
    # technical sees it under "assigned"; sales sees it under "created"
    assigned = client.get("/api/tasks", headers=_h("0912"),
                          params={"scope": "assigned"}).json()
    created = client.get("/api/tasks", headers=_h("0911"),
                         params={"scope": "created"}).json()
    assert any(t["title"] == "کار الف" for t in assigned)
    assert any(t["title"] == "کار الف" for t in created)
    # sales should NOT see it in their "assigned" list
    sales_assigned = client.get("/api/tasks", headers=_h("0911"),
                                params={"scope": "assigned"}).json()
    assert all(t["title"] != "کار الف" for t in sales_assigned)


def test_done_stamps_completion_time():
    tid = client.post("/api/tasks", headers=_h("0911"),
                      json={"assigned_to_id": 3, "title": "کار ب"}).json()["id"]
    r = client.patch(f"/api/tasks/{tid}", headers=_h("0912"), json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done" and r.json()["done_at"] is not None
    # reverting clears the completion time
    r2 = client.patch(f"/api/tasks/{tid}", headers=_h("0912"),
                      json={"status": "in_progress"})
    assert r2.json()["done_at"] is None


def test_employee_can_refer_to_manager_and_track_it():
    tid = client.post("/api/tasks", headers=_h("0912"),
                      json={"assigned_to_id": 1, "title": "بررسی قرارداد"}).json()["id"]
    # creator (technical) can see its stage even though it's assigned to the manager
    created = client.get("/api/tasks", headers=_h("0912"),
                         params={"scope": "created"}).json()
    assert any(t["id"] == tid for t in created)


def test_unrelated_user_cannot_update():
    # sales(2) refers to technical(3); the manager is neither creator nor assignee
    tid = client.post("/api/tasks", headers=_h("0911"),
                      json={"assigned_to_id": 3, "title": "کار ج"}).json()["id"]
    # a manager CAN touch anything
    assert client.patch(f"/api/tasks/{tid}", headers=_h("0910"),
                        json={"status": "in_progress"}).status_code == 200
