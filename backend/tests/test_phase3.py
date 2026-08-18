"""Phase 3 smoke tests — inventory over the single stock-items table."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_p3.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-phase3"

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
    db.add_all([
        User(name="مدیر", role=UserRole.manager, phone="0910",
             password_hash=hash_password("pass1234")),
        User(name="انباردار", role=UserRole.warehouse, phone="0913",
             password_hash=hash_password("pass1234")),
        User(name="فروش", role=UserRole.sales, phone="0911",
             password_hash=hash_password("pass1234")),
    ])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _h(phone: str) -> dict:
    r = client.post("/api/auth/login", data={"username": phone, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_rbac_sales_cannot_write_inventory():
    r = client.post("/api/product-models", headers=_h("0911"),
                    json={"name": "سوییچ", "tracking_type": "serial"})
    assert r.status_code == 403


def test_product_model_has_unit_of_measure():
    m = client.post("/api/product-models", headers=_h("0913"),
                    json={"name": "کابل", "tracking_type": "quantity",
                          "unit_of_measure": "متر"}).json()
    assert m["unit_of_measure"] == "متر"
    assert m["current_stock"] == 0


def test_serial_stock_tracks_warehouse_units():
    m = client.post("/api/product-models", headers=_h("0913"),
                    json={"name": "سوییچ سیسکو X", "tracking_type": "serial",
                          "base_price": 5000000}).json()
    mid = m["id"]
    assert m["unit_of_measure"] == "عدد"  # default

    for sn in ("SN-1", "SN-2"):
        r = client.post("/api/stock-items", headers=_h("0913"),
                        json={"model_id": mid, "serial_number": sn})
        assert r.status_code == 201, r.text

    got = client.get(f"/api/product-models/{mid}", headers=_h("0910"))
    assert got.json()["current_stock"] == 2

    unit_id = client.get("/api/stock-items", headers=_h("0913"),
                         params={"model_id": mid}).json()[0]["id"]
    client.patch(f"/api/stock-items/{unit_id}", headers=_h("0913"),
                 json={"status": "sold"})
    got = client.get(f"/api/product-models/{mid}", headers=_h("0910"))
    assert got.json()["current_stock"] == 1


def test_duplicate_serial_rejected():
    mid = client.post("/api/product-models", headers=_h("0913"),
                      json={"name": "روتر", "tracking_type": "serial"}).json()["id"]
    client.post("/api/stock-items", headers=_h("0913"),
                json={"model_id": mid, "serial_number": "DUP-1"})
    dup = client.post("/api/stock-items", headers=_h("0913"),
                      json={"model_id": mid, "serial_number": "DUP-1"})
    assert dup.status_code == 409


def test_serial_model_requires_serial_number():
    mid = client.post("/api/product-models", headers=_h("0913"),
                      json={"name": "سرور", "tracking_type": "serial"}).json()["id"]
    bad = client.post("/api/stock-items", headers=_h("0913"),
                      json={"model_id": mid, "quantity": 3, "direction": "in"})
    assert bad.status_code == 400


def test_non_serial_movements_and_negative_guard():
    mid = client.post("/api/product-models", headers=_h("0913"),
                      json={"name": "فیبر نوری", "tracking_type": "quantity",
                            "unit_of_measure": "متر"}).json()["id"]

    client.post("/api/stock-items", headers=_h("0913"),
                json={"model_id": mid, "quantity": 100, "direction": "in"})
    client.post("/api/stock-items", headers=_h("0913"),
                json={"model_id": mid, "quantity": 30, "direction": "out"})
    got = client.get(f"/api/product-models/{mid}", headers=_h("0910"))
    assert got.json()["current_stock"] == 70

    bad = client.post("/api/stock-items", headers=_h("0913"),
                      json={"model_id": mid, "quantity": 999, "direction": "out"})
    assert bad.status_code == 400


def test_non_serial_rejects_serial_number():
    mid = client.post("/api/product-models", headers=_h("0913"),
                      json={"name": "پیچ", "tracking_type": "quantity"}).json()["id"]
    bad = client.post("/api/stock-items", headers=_h("0913"),
                      json={"model_id": mid, "serial_number": "X"})
    assert bad.status_code == 400
