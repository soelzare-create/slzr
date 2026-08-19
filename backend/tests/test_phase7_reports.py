"""Phase 7 — the management overview aggregates counts, finance, invoice/purchase
status, and top debtor/creditor parties across the whole system."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_reports.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-reports"

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
            User(name="حسابدار", role=UserRole.accountant, phone="0914",
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


def _bulk_model(name) -> int:
    return client.post("/api/product-models", headers=_h("0910"),
                       json={"name": name, "tracking_type": "quantity",
                             "unit_of_measure": "عدد"}).json()["id"]


def _sell(customer_id, model_id, qty, price) -> None:
    client.post("/api/stock-items", headers=_h("0913"),
                json={"model_id": model_id, "quantity": qty, "direction": "in"})
    act = client.post("/api/activities", headers=_h("0910"),
                      json={"customer_id": customer_id, "owner_id": 1, "type": "sale"}).json()
    client.post(f"/api/activities/{act['id']}/items", headers=_h("0910"),
                json={"product_model_id": model_id, "quantity": qty, "price": price})
    client.post("/api/invoices", headers=_h("0910"),
                json={"activity_id": act["id"], "kind": "final"})


def _buy(supplier_id, model_id, qty, unit_cost) -> None:
    client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier_id,
        "items": [{"product_model_id": model_id, "quantity": qty, "unit_cost": unit_cost}]})


def test_overview_aggregates_everything():
    cust = client.post("/api/parties", headers=_h("0910"),
                       json={"name": "مشتری بزرگ", "is_customer": True}).json()["id"]
    supp = client.post("/api/parties", headers=_h("0910"),
                       json={"name": "تأمین‌کننده بزرگ", "is_customer": False,
                             "is_supplier": True}).json()["id"]
    model = _bulk_model("کالای گزارش")
    _sell(cust, model, qty=2, price=1_000_000)   # income 1,000,000 -> customer is a debtor
    _buy(supp, model, qty=5, unit_cost=100_000)  # expense 500,000 -> supplier is a creditor
    client.post("/api/tickets", headers=_h("0910"),
                json={"customer_id": cust, "title": "تیکت باز"})

    ov = client.get("/api/reports/overview", headers=_h("0910")).json()

    assert ov["counts"]["customers"] >= 1
    assert ov["counts"]["suppliers"] >= 1
    assert ov["counts"]["open_tickets"] >= 1
    assert ov["finance"]["income"] >= 1_000_000
    assert ov["finance"]["expense"] >= 500_000
    assert ov["finance"]["net"] == ov["finance"]["income"] - ov["finance"]["expense"]

    # invoice/purchase status counts are present and add up
    assert ov["invoices"]["total"] == (
        ov["invoices"]["unpaid"] + ov["invoices"]["paid"] + ov["invoices"]["overdue"]
    )
    assert ov["purchases"]["total"] >= 1

    # the customer shows up as a debtor (they owe us), the supplier as a creditor
    debtor_ids = {d["party_id"] for d in ov["top_debtors"]}
    creditor_ids = {c["party_id"] for c in ov["top_creditors"]}
    assert cust in debtor_ids
    assert supp in creditor_ids
    assert all(d["balance"] > 0 for d in ov["top_debtors"])
    assert all(c["balance"] < 0 for c in ov["top_creditors"])


def test_overview_readable_by_accountant_not_warehouse():
    assert client.get("/api/reports/overview", headers=_h("0914")).status_code == 200
    assert client.get("/api/reports/overview", headers=_h("0913")).status_code == 403
