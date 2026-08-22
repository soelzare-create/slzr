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


def _final_invoice(customer_id, amount) -> dict:
    act = client.post("/api/activities", headers=_h("0910"), json={
        "customer_id": customer_id, "owner_id": 1, "type": "sale"}).json()
    return client.post("/api/invoices", headers=_h("0910"), json={
        "activity_id": act["id"], "kind": "final",
        "items": [{"description": "خدمات", "quantity": 1, "unit_price": amount}]}).json()


def test_partial_then_full_receipt_moves_invoice_status():
    cust = _party("مشتری اقساطی", cust=True)
    inv = _final_invoice(cust, 1_000_000)
    assert inv["status"] == "unpaid" and inv["remaining"] == 1_000_000

    # take 40% now
    r1 = client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "invoice_id": inv["id"], "amount": 400_000,
        "paid_at": "2026-08-22"})
    assert r1.status_code == 201, r1.text
    got = client.get(f"/api/invoices/{inv['id']}", headers=_h("0910")).json()
    assert got["status"] == "partial"
    assert got["paid_amount"] == 400_000 and got["remaining"] == 600_000

    # settle the rest two weeks later
    client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "invoice_id": inv["id"], "amount": 600_000,
        "paid_at": "2026-09-05"})
    got = client.get(f"/api/invoices/{inv['id']}", headers=_h("0910")).json()
    assert got["status"] == "paid" and got["remaining"] == 0


def test_receipt_cannot_exceed_remaining():
    cust = _party("مشتری سقف", cust=True)
    inv = _final_invoice(cust, 500_000)
    r = client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "invoice_id": inv["id"], "amount": 600_000})
    assert r.status_code == 400


def test_cash_account_balance_reflects_vouchers():
    acc = client.post("/api/accounting/accounts", headers=_h("0914"), json={
        "name": "صندوق تست", "type": "cash", "opening_balance": 1_000_000}).json()
    assert acc["balance"] == 1_000_000
    # a standalone receipt into the account raises its balance
    client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "amount": 200_000, "account_id": acc["id"],
        "category": "علی‌الحساب"})
    # an operating-expense payment lowers it
    client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "payment", "amount": 300_000, "account_id": acc["id"],
        "category": "اجاره"})
    accounts = client.get("/api/accounting/accounts", headers=_h("0914")).json()
    mine = next(a for a in accounts if a["id"] == acc["id"])
    assert mine["balance"] == 900_000  # 1,000,000 + 200,000 − 300,000


def test_expense_by_category_groups_payments():
    acc = client.post("/api/accounting/accounts", headers=_h("0914"), json={
        "name": "صندوق ۲", "type": "cash"}).json()
    client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "payment", "amount": 500_000, "account_id": acc["id"],
        "category": "حقوق و دستمزد"})
    rows = client.get("/api/accounting/expense-by-category", headers=_h("0914")).json()
    cats = {r["category"]: r["amount"] for r in rows}
    assert cats.get("حقوق و دستمزد", 0) >= 500_000


def test_standalone_receipt_needs_no_invoice():
    r = client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "amount": 50_000, "category": "درآمد متفرقه"})
    assert r.status_code == 201, r.text


def test_only_finance_roles_record_vouchers():
    r = client.post("/api/accounting/payments", headers=_h("0911"), json={
        "direction": "payment", "amount": 1000, "category": "x"})
    assert r.status_code == 403


def test_received_cheque_clears_into_account_and_settles_invoice():
    cust = _party("مشتری چکی", cust=True)
    inv = _final_invoice(cust, 1_000_000)
    acc = client.post("/api/accounting/accounts", headers=_h("0914"),
                      json={"name": "بانک ملت", "type": "bank"}).json()
    # register two cheques as two installments on the invoice
    ch1 = client.post("/api/accounting/cheques", headers=_h("0914"), json={
        "direction": "received", "number": "111", "amount": 600_000,
        "due_date": "2026-09-01", "party_id": cust, "invoice_id": inv["id"]}).json()
    client.post("/api/accounting/cheques", headers=_h("0914"), json={
        "direction": "received", "number": "112", "amount": 400_000,
        "due_date": "2026-09-15", "party_id": cust, "invoice_id": inv["id"]})

    # cashing the first cheque → invoice becomes partial, account balance rises
    r = client.post(f"/api/accounting/cheques/{ch1['id']}/clear", headers=_h("0914"),
                    json={"account_id": acc["id"], "cleared_at": "2026-09-02"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cleared" and r.json()["payment_id"] is not None

    got = client.get(f"/api/invoices/{inv['id']}", headers=_h("0910")).json()
    assert got["status"] == "partial" and got["paid_amount"] == 600_000

    accounts = client.get("/api/accounting/accounts", headers=_h("0914")).json()
    mine = next(a for a in accounts if a["id"] == acc["id"])
    assert mine["balance"] == 600_000


def test_cheque_clear_needs_account_and_only_once():
    cust = _party("مشتری چک ۲", cust=True)
    inv = _final_invoice(cust, 200_000)
    ch = client.post("/api/accounting/cheques", headers=_h("0914"), json={
        "direction": "received", "number": "222", "amount": 200_000,
        "due_date": "2026-09-01", "invoice_id": inv["id"]}).json()
    # no account → rejected
    assert client.post(f"/api/accounting/cheques/{ch['id']}/clear", headers=_h("0914"),
                       json={}).status_code == 400
    acc = client.post("/api/accounting/accounts", headers=_h("0914"),
                      json={"name": "صندوق چک", "type": "cash"}).json()
    assert client.post(f"/api/accounting/cheques/{ch['id']}/clear", headers=_h("0914"),
                       json={"account_id": acc["id"]}).status_code == 200
    # already cleared → cannot clear again
    assert client.post(f"/api/accounting/cheques/{ch['id']}/clear", headers=_h("0914"),
                       json={"account_id": acc["id"]}).status_code == 400


def test_bounced_cheque_has_no_cash_effect():
    ch = client.post("/api/accounting/cheques", headers=_h("0914"), json={
        "direction": "issued", "number": "333", "amount": 90_000,
        "due_date": "2026-09-01"}).json()
    r = client.post(f"/api/accounting/cheques/{ch['id']}/bounce", headers=_h("0914"))
    assert r.status_code == 200 and r.json()["status"] == "bounced"
    # a bounced cheque cannot then be cleared
    assert client.post(f"/api/accounting/cheques/{ch['id']}/clear", headers=_h("0914"),
                       json={}).status_code == 400


def test_summary_tracks_received_and_receivable():
    before = client.get("/api/accounting/summary", headers=_h("0910")).json()
    cust = _party("مشتری خلاصه", cust=True)
    inv = _final_invoice(cust, 200_000)
    client.post("/api/accounting/payments", headers=_h("0914"), json={
        "direction": "receipt", "invoice_id": inv["id"], "amount": 50_000})
    after = client.get("/api/accounting/summary", headers=_h("0910")).json()
    assert after["received"] == before["received"] + 50_000
    # receivable = accrued income − received
    assert after["receivable"] == after["income"] - after["received"]
    assert client.get("/api/accounting/balances", headers=_h("0913")).status_code == 403
    assert client.get("/api/accounting/summary", headers=_h("0914")).status_code == 200
