"""Phase 5 — accounting: the ledger, per-party balances, and totals.

Drives the real chain end-to-end: issuing a final sales invoice books income,
recording a purchase books an expense, and a party that is both nets out.
"""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_accounting.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-accounting"

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
            User(name="فروش", role=UserRole.sales, phone="0911",
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


def _party(name, **roles) -> int:
    body = {"name": name, "is_customer": roles.get("cust", False),
            "is_supplier": roles.get("supp", False)}
    return client.post("/api/parties", headers=_h("0910"), json=body).json()["id"]


def _bulk_model(name) -> int:
    return client.post("/api/product-models", headers=_h("0910"),
                       json={"name": name, "tracking_type": "quantity",
                             "unit_of_measure": "عدد"}).json()["id"]


def _sell(customer_id, model_id, qty, price) -> None:
    """Create an activity, then issue a FINAL invoice with a line (books income)."""
    # Put goods in the warehouse first (inbound movement — no accounting effect),
    # otherwise the final invoice is blocked by the negative-stock guard.
    client.post("/api/stock-items", headers=_h("0913"),
                json={"model_id": model_id, "quantity": qty, "direction": "in"})
    act = client.post("/api/activities", headers=_h("0910"), json={
        "customer_id": customer_id, "owner_id": 1, "type": "sale"}).json()
    r = client.post("/api/invoices", headers=_h("0910"), json={
        "activity_id": act["id"], "kind": "final",
        "items": [{"description": "کالا", "product_model_id": model_id,
                   "quantity": qty, "unit_price": price}]})
    assert r.status_code == 201, r.text


def _buy(supplier_id, model_id, qty, unit_cost) -> None:
    r = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier_id,
        "items": [{"product_model_id": model_id, "quantity": qty, "unit_cost": unit_cost}],
    })
    assert r.status_code == 201


def test_income_expense_and_party_balance_net_out():
    both = _party("طرف دوطرفه", cust=True, supp=True)
    model = _bulk_model("کالای الف")
    # sell them 1,000,000 (income) and buy 300,000 from them (expense)
    _sell(both, model, qty=1, price=1_000_000)
    _buy(both, model, qty=3, unit_cost=100_000)  # 300,000

    bal = client.get(f"/api/accounting/parties/{both}/balance", headers=_h("0914")).json()
    assert bal["income"] == 1_000_000
    assert bal["expense"] == 300_000
    assert bal["balance"] == 700_000  # positive → they owe us net


def test_balances_list_and_summary():
    cust = _party("مشتری تنها", cust=True)
    supp = _party("تأمین‌کننده تنها", supp=True)
    model = _bulk_model("کالای ب")
    _sell(cust, model, qty=1, price=500_000)
    _buy(supp, model, qty=2, unit_cost=50_000)  # 100,000

    balances = client.get("/api/accounting/balances", headers=_h("0910")).json()
    by_id = {b["party_id"]: b for b in balances}
    assert by_id[cust]["balance"] == 500_000
    assert by_id[supp]["balance"] == -100_000  # we owe the supplier
    assert by_id[cust]["party_name"] == "مشتری تنها"

    summary = client.get("/api/accounting/summary", headers=_h("0914")).json()
    # summary is company-wide across all tests in this module
    assert summary["net"] == summary["income"] - summary["expense"]
    assert summary["income"] > 0 and summary["expense"] > 0


def test_documents_ledger_lists_income_and_expense():
    docs = client.get("/api/accounting/documents", headers=_h("0914")).json()
    kinds = {d["type"] for d in docs}
    assert "income" in kinds and "expense" in kinds
    # an income doc points at an invoice; an expense doc points at a purchase
    inc = next(d for d in docs if d["type"] == "income")
    exp = next(d for d in docs if d["type"] == "expense")
    assert inc["invoice_id"] is not None and inc["purchase_id"] is None
    assert exp["purchase_id"] is not None and exp["invoice_id"] is None


def test_only_manager_or_accountant_may_read_accounting():
    # sales & warehouse are operational roles, not financial
    assert client.get("/api/accounting/summary", headers=_h("0911")).status_code == 403
    assert client.get("/api/accounting/balances", headers=_h("0913")).status_code == 403
    assert client.get("/api/accounting/summary", headers=_h("0914")).status_code == 200
