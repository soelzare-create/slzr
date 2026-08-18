"""Phase 2 smoke tests — customers, activities, and project stages."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_p2.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-phase2"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

client = TestClient(app)


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


def _token(phone: str) -> str:
    r = client.post("/api/auth/login", data={"username": phone, "password": "pass1234"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _h(phone: str) -> dict:
    return {"Authorization": f"Bearer {_token(phone)}"}


def test_customer_crud_and_rbac():
    # technical (not sales/manager) cannot create a customer
    blocked = client.post("/api/parties", headers=_h("0912"),
                          json={"name": "شرکت الف"})
    assert blocked.status_code == 403

    # sales can
    created = client.post("/api/parties", headers=_h("0911"),
                          json={"name": "شرکت الف", "phone": "02100"})
    assert created.status_code == 201, created.text
    cid = created.json()["id"]

    # everyone authenticated can read
    got = client.get(f"/api/parties/{cid}", headers=_h("0912"))
    assert got.status_code == 200 and got.json()["name"] == "شرکت الف"

    # search
    found = client.get("/api/parties", headers=_h("0910"), params={"q": "الف"})
    assert any(c["id"] == cid for c in found.json())


def test_activity_flow_and_stage_rule():
    # a customer + owner to attach to
    cid = client.post("/api/parties", headers=_h("0911"),
                      json={"name": "مشتری پروژه"}).json()["id"]

    # create a PROJECT activity
    proj = client.post("/api/activities", headers=_h("0911"),
                       json={"customer_id": cid, "owner_id": 2, "type": "project",
                             "title": "پیاده‌سازی شبکه"})
    assert proj.status_code == 201, proj.text
    pid = proj.json()["id"]
    assert proj.json()["status"] == "open"

    # technical can add a project stage
    st = client.post(f"/api/activities/{pid}/stages", headers=_h("0912"),
                     json={"stage": "discovery"})
    assert st.status_code == 201, st.text

    # detail view includes the stage
    detail = client.get(f"/api/activities/{pid}", headers=_h("0910"))
    assert len(detail.json()["stages"]) == 1

    # create a SALE activity — stages must be rejected for non-project
    sale = client.post("/api/activities", headers=_h("0911"),
                       json={"customer_id": cid, "owner_id": 2, "type": "sale"})
    sid = sale.json()["id"]
    bad = client.post(f"/api/activities/{sid}/stages", headers=_h("0912"),
                      json={"stage": "discovery"})
    assert bad.status_code == 400


def test_activity_invalid_references():
    bad = client.post("/api/activities", headers=_h("0911"),
                      json={"customer_id": 9999, "owner_id": 1, "type": "sale"})
    assert bad.status_code == 422


def test_activity_status_update():
    cid = client.post("/api/parties", headers=_h("0911"),
                      json={"name": "برای تغییر وضعیت"}).json()["id"]
    aid = client.post("/api/activities", headers=_h("0911"),
                     json={"customer_id": cid, "owner_id": 2, "type": "sale"}).json()["id"]
    upd = client.patch(f"/api/activities/{aid}", headers=_h("0910"),
                       json={"status": "done"})
    assert upd.status_code == 200 and upd.json()["status"] == "done"
