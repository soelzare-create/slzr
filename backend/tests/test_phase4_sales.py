"""Phase 4A tests — sales: activity items, proforma/final invoices, and the
wiring to inventory (stock-out) and accounting (income)."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_p4s.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-p4s"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.accounting import FinancialDocument  # noqa: E402
from app.models.enums import FinancialType, UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all([
        User(name="مدیر", role=UserRole.manager, phone="0910",
             password_hash=hash_password("pass1234")),
        User(name="فروش", role=UserRole.sales, phone="0911",
             password_hash=hash_password("pass1234")),
        User(name="انباردار", role=UserRole.warehouse, phone="0913",
             password_hash=hash_password("pass1234")),
    ])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _h(phone):
    r = client.post("/api/auth/login", data={"username": phone, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


_serial_seq = 0


def _next_serial() -> str:
    global _serial_seq
    _serial_seq += 1
    return f"S-{_serial_seq}"


def _setup_sale():
    """A customer, a sale activity, a serial unit in stock, added as a line."""
    mgr, sales, wh = _h("0910"), _h("0911"), _h("0913")
    cid = client.post("/api/parties", headers=sales,
                      json={"name": "مشتری فروش"}).json()["id"]
    aid = client.post("/api/activities", headers=sales,
                     json={"customer_id": cid, "owner_id": 2, "type": "sale"}).json()["id"]
    mid = client.post("/api/product-models", headers=wh,
                      json={"name": "سوییچ", "tracking_type": "serial",
                            "base_price": 5_000_000}).json()["id"]
    uid = client.post("/api/stock-items", headers=wh,
                      json={"model_id": mid, "serial_number": _next_serial()}).json()["id"]
    line = client.post(f"/api/activities/{aid}/items", headers=sales,
                       json={"stock_item_id": uid, "price": 6_000_000})
    assert line.status_code == 201, line.text
    return dict(cid=cid, aid=aid, mid=mid, uid=uid)


def test_proforma_has_no_side_effects_then_finalize_does():
    ctx = _setup_sale()
    sales, mgr = _h("0911"), _h("0910")

    # proforma: total computed, but the unit stays in warehouse, no ledger entry
    pf = client.post("/api/invoices", headers=sales,
                     json={"activity_id": ctx["aid"], "kind": "proforma",
                           "settlement_due_date": "2026-09-01"})
    assert pf.status_code == 201, pf.text
    assert float(pf.json()["total_amount"]) == 6_000_000
    assert pf.json()["kind"] == "proforma"

    stock = client.get(f"/api/product-models/{ctx['mid']}", headers=mgr).json()
    assert stock["current_stock"] == 1  # still in stock

    # finalize -> unit becomes sold, income recorded
    fin = client.post(f"/api/invoices/{pf.json()['id']}/finalize", headers=sales)
    assert fin.status_code == 200, fin.text
    assert fin.json()["kind"] == "final"

    stock = client.get(f"/api/product-models/{ctx['mid']}", headers=mgr).json()
    assert stock["current_stock"] == 0  # sold out of the warehouse

    db = SessionLocal()
    try:
        docs = db.query(FinancialDocument).filter_by(party_id=ctx["cid"]).all()
        assert len(docs) == 1
        assert docs[0].type == FinancialType.income
        assert float(docs[0].amount) == 6_000_000
    finally:
        db.close()


def test_only_one_final_invoice_per_activity():
    ctx = _setup_sale()
    sales = _h("0911")
    first = client.post("/api/invoices", headers=sales,
                        json={"activity_id": ctx["aid"], "kind": "final"})
    assert first.status_code == 201, first.text
    second = client.post("/api/invoices", headers=sales,
                         json={"activity_id": ctx["aid"], "kind": "final"})
    assert second.status_code == 409


def test_final_invoice_needs_items():
    sales = _h("0911")
    cid = client.post("/api/parties", headers=sales, json={"name": "بی‌قلم"}).json()["id"]
    aid = client.post("/api/activities", headers=sales,
                     json={"customer_id": cid, "owner_id": 2, "type": "sale"}).json()["id"]
    r = client.post("/api/invoices", headers=sales,
                    json={"activity_id": aid, "kind": "final"})
    assert r.status_code == 400


def test_bulk_line_reduces_stock_on_finalize():
    sales, wh, mgr = _h("0911"), _h("0913"), _h("0910")
    cid = client.post("/api/parties", headers=sales, json={"name": "مشتری فله"}).json()["id"]
    aid = client.post("/api/activities", headers=sales,
                     json={"customer_id": cid, "owner_id": 2, "type": "sale"}).json()["id"]
    mid = client.post("/api/product-models", headers=wh,
                      json={"name": "کابل", "tracking_type": "quantity"}).json()["id"]
    client.post("/api/stock-items", headers=wh,
                json={"model_id": mid, "quantity": 50, "direction": "in"})
    client.post(f"/api/activities/{aid}/items", headers=sales,
                json={"product_model_id": mid, "quantity": 20, "price": 2_000_000})

    client.post("/api/invoices", headers=sales,
                json={"activity_id": aid, "kind": "final"})
    stock = client.get(f"/api/product-models/{mid}", headers=mgr).json()
    assert stock["current_stock"] == 30  # 50 in - 20 sold


def test_cannot_sell_more_bulk_than_in_stock():
    sales, wh = _h("0911"), _h("0913")
    cid = client.post("/api/parties", headers=sales, json={"name": "کم‌موجودی"}).json()["id"]
    aid = client.post("/api/activities", headers=sales,
                     json={"customer_id": cid, "owner_id": 2, "type": "sale"}).json()["id"]
    mid = client.post("/api/product-models", headers=wh,
                      json={"name": "فیبر", "tracking_type": "quantity"}).json()["id"]
    client.post("/api/stock-items", headers=wh,
                json={"model_id": mid, "quantity": 5, "direction": "in"})
    client.post(f"/api/activities/{aid}/items", headers=sales,
                json={"product_model_id": mid, "quantity": 10, "price": 1})
    r = client.post("/api/invoices", headers=sales,
                    json={"activity_id": aid, "kind": "final"})
    assert r.status_code == 400  # not enough stock
