"""Phase 6 — support/ticketing: a ticket ties a customer issue to (optionally)
a specific device serial; covers validation, status lifecycle, and RBAC."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_support.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-support"

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
            User(name="کارشناس فنی", role=UserRole.technical, phone="0912",
                 password_hash=hash_password("pass1234")),
            User(name="انباردار", role=UserRole.warehouse, phone="0913",
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


def _customer() -> int:
    return client.post("/api/parties", headers=_h("0910"),
                       json={"name": "مشتری", "is_customer": True}).json()["id"]


def _serial_unit(serial: str) -> int:
    model = client.post("/api/product-models", headers=_h("0910"),
                        json={"name": "دستگاه", "tracking_type": "serial"}).json()
    return client.post("/api/stock-items", headers=_h("0913"),
                       json={"model_id": model["id"], "serial_number": serial}).json()["id"]


def test_create_ticket_with_device():
    cust = _customer()
    unit = _serial_unit("DEV-001")
    r = client.post("/api/tickets", headers=_h("0912"), json={
        "customer_id": cust, "device_unit_id": unit, "owner_id": 2,
        "title": "دستگاه روشن نمی‌شود", "description": "پس از قطع برق",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "open" and body["device_unit_id"] == unit


def test_create_ticket_without_device_is_allowed():
    cust = _customer()
    r = client.post("/api/tickets", headers=_h("0910"),
                    json={"customer_id": cust, "title": "سوال عمومی"})
    assert r.status_code == 201 and r.json()["device_unit_id"] is None


def test_device_must_be_a_serial_unit():
    cust = _customer()
    r = client.post("/api/tickets", headers=_h("0912"), json={
        "customer_id": cust, "device_unit_id": 999999, "title": "دستگاه نامعتبر"})
    assert r.status_code == 422


def test_customer_must_have_customer_role():
    supp = client.post("/api/parties", headers=_h("0910"),
                       json={"name": "فقط تأمین‌کننده", "is_customer": False,
                             "is_supplier": True}).json()["id"]
    r = client.post("/api/tickets", headers=_h("0912"),
                    json={"customer_id": supp, "title": "نامعتبر"})
    assert r.status_code == 422


def test_ticket_status_lifecycle():
    cust = _customer()
    tid = client.post("/api/tickets", headers=_h("0912"),
                      json={"customer_id": cust, "title": "پیگیری"}).json()["id"]
    for st in ("investigating", "closed"):
        r = client.patch(f"/api/tickets/{tid}", headers=_h("0912"), json={"status": st})
        assert r.status_code == 200 and r.json()["status"] == st


def test_filter_by_customer_and_status():
    cust = _customer()
    client.post("/api/tickets", headers=_h("0912"),
                json={"customer_id": cust, "title": "باز ۱"})
    tid = client.post("/api/tickets", headers=_h("0912"),
                      json={"customer_id": cust, "title": "بسته ۱"}).json()["id"]
    client.patch(f"/api/tickets/{tid}", headers=_h("0912"), json={"status": "closed"})

    open_ones = client.get("/api/tickets", headers=_h("0910"),
                           params={"customer_id": cust, "status": "open"}).json()
    assert all(t["status"] == "open" for t in open_ones)
    assert any(t["title"] == "باز ۱" for t in open_ones)


def test_warehouse_cannot_write_tickets():
    cust = _customer()
    r = client.post("/api/tickets", headers=_h("0913"),
                    json={"customer_id": cust, "title": "غیرمجاز"})
    assert r.status_code == 403
