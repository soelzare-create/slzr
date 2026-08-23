"""Phase 4A tests — sales: invoices carry their own line items; proformas are
quotes with no side effects; a final invoice books income and takes linked
warehouse goods out of stock. One activity may hold several of each."""
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


def _activity():
    """A customer + a bare activity (no items — an activity is just a folder)."""
    sales = _h("0911")
    cid = client.post("/api/parties", headers=sales,
                      json={"name": "مشتری فروش"}).json()["id"]
    aid = client.post("/api/activities", headers=sales,
                     json={"customer_id": cid, "owner_id": 2, "type": "project"}).json()["id"]
    return dict(cid=cid, aid=aid)


def _bulk_product(name, qty_in):
    wh = _h("0913")
    mid = client.post("/api/product-models", headers=wh,
                      json={"name": name, "tracking_type": "quantity"}).json()["id"]
    client.post("/api/stock-items", headers=wh,
                json={"model_id": mid, "quantity": qty_in, "direction": "in"})
    return mid


def test_activity_needs_no_items():
    """An activity is created with no items and no price."""
    ctx = _activity()
    detail = client.get(f"/api/activities/{ctx['aid']}", headers=_h("0910"))
    assert detail.status_code == 200, detail.text


def test_proforma_has_no_side_effects():
    ctx = _activity()
    mgr, sales = _h("0910"), _h("0911")
    mid = _bulk_product("سوییچ", 10)

    pf = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "proforma",
        "settlement_due_date": "2026-09-01",
        "items": [
            {"description": "سوییچ", "product_model_id": mid, "quantity": 2, "unit_price": 6_000_000},
            {"description": "نصب و راه‌اندازی", "quantity": 1, "unit_price": 1_000_000},
        ],
    })
    assert pf.status_code == 201, pf.text
    assert float(pf.json()["total_amount"]) == 13_000_000  # 2*6M + 1M
    assert pf.json()["kind"] == "proforma"
    assert len(pf.json()["items"]) == 2

    # stock untouched, no ledger entry
    stock = client.get(f"/api/product-models/{mid}", headers=mgr).json()
    assert stock["current_stock"] == 10


def test_final_books_income_and_reduces_linked_stock():
    ctx = _activity()
    mgr, sales = _h("0910"), _h("0911")
    mid = _bulk_product("کابل", 50)

    fin = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [
            {"description": "کابل", "product_model_id": mid, "quantity": 20, "unit_price": 100_000},
            {"description": "خدمات پشتیبانی", "quantity": 1, "unit_price": 3_000_000},
        ],
    })
    assert fin.status_code == 201, fin.text
    assert float(fin.json()["total_amount"]) == 5_000_000  # 20*100k + 3M

    # linked line reduced stock; service line did not
    stock = client.get(f"/api/product-models/{mid}", headers=mgr).json()
    assert stock["current_stock"] == 30  # 50 - 20

    db = SessionLocal()
    try:
        docs = db.query(FinancialDocument).filter_by(party_id=ctx["cid"]).all()
        assert len(docs) == 1
        assert docs[0].type == FinancialType.income
        assert float(docs[0].amount) == 5_000_000
    finally:
        db.close()


def test_several_proformas_and_finals_per_activity():
    ctx = _activity()
    sales = _h("0911")
    for _ in range(3):
        r = client.post("/api/invoices", headers=sales, json={
            "activity_id": ctx["aid"], "kind": "proforma",
            "items": [{"description": "قلم", "quantity": 1, "unit_price": 1000}]})
        assert r.status_code == 201, r.text
    for _ in range(2):
        r = client.post("/api/invoices", headers=sales, json={
            "activity_id": ctx["aid"], "kind": "final",
            "items": [{"description": "قلم", "quantity": 1, "unit_price": 1000}]})
        assert r.status_code == 201, r.text

    pfs = client.get(f"/api/invoices?activity_id={ctx['aid']}&kind=proforma", headers=sales)
    fins = client.get(f"/api/invoices?activity_id={ctx['aid']}&kind=final", headers=sales)
    assert len(pfs.json()) == 3
    assert len(fins.json()) == 2


def test_convert_proforma_carries_source_and_allows_edited_prices():
    ctx = _activity()
    sales = _h("0911")
    pf = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "proforma",
        "items": [{"description": "روتر", "quantity": 1, "unit_price": 5_000_000}]}).json()

    # convert -> a NEW final built from the (edited) proforma lines
    fin = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "source_proforma_id": pf["id"],
        "items": [{"description": "روتر", "quantity": 1, "unit_price": 5_500_000}]})
    assert fin.status_code == 201, fin.text
    assert fin.json()["source_proforma_id"] == pf["id"]
    assert float(fin.json()["total_amount"]) == 5_500_000

    # the proforma still exists as its own record
    assert client.get(f"/api/invoices/{pf['id']}", headers=sales).status_code == 200


def test_serial_line_sells_the_specific_unit_on_final():
    ctx = _activity()
    mgr, sales, wh = _h("0910"), _h("0911"), _h("0913")
    mid = client.post("/api/product-models", headers=wh,
                      json={"name": "سوییچ سیسکو", "tracking_type": "serial",
                            "base_price": 5_000_000}).json()["id"]
    uid = client.post("/api/stock-items", headers=wh,
                      json={"model_id": mid, "serial_number": "SW-777"}).json()["id"]

    # a proforma referencing the serial unit does NOT sell it
    pf = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "proforma",
        "items": [{"description": "سوییچ سیسکو", "stock_item_id": uid, "unit_price": 6_000_000}]})
    assert pf.status_code == 201, pf.text
    assert client.get(f"/api/product-models/{mid}", headers=mgr).json()["current_stock"] == 1

    # a final invoice sells that exact device (stock -> 0)
    fin = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [{"description": "سوییچ سیسکو", "stock_item_id": uid, "unit_price": 6_000_000}]})
    assert fin.status_code == 201, fin.text
    assert float(fin.json()["total_amount"]) == 6_000_000
    assert client.get(f"/api/product-models/{mid}", headers=mgr).json()["current_stock"] == 0

    # the same unit can't be sold twice
    again = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [{"description": "سوییچ سیسکو", "stock_item_id": uid, "unit_price": 6_000_000}]})
    assert again.status_code == 400


def test_proforma_without_activity_auto_creates_a_sale_activity():
    sales = _h("0911")
    cid = client.post("/api/parties", headers=sales,
                      json={"name": "مشتری مستقیم"}).json()["id"]
    # no activity_id — just a customer
    pf = client.post("/api/invoices", headers=sales, json={
        "customer_id": cid, "kind": "proforma",
        "items": [{"description": "سرور", "quantity": 1, "unit_price": 9_000_000}]})
    assert pf.status_code == 201, pf.text
    aid = pf.json()["activity_id"]
    assert aid is not None
    # the auto-created activity is a «فروش کالا» sale for that customer
    act = client.get(f"/api/activities/{aid}", headers=sales).json()
    assert act["type"] == "sale"
    assert act["title"] == "فروش کالا"
    assert act["customer_id"] == cid


def test_invoice_needs_activity_or_customer():
    sales = _h("0911")
    r = client.post("/api/invoices", headers=sales, json={
        "kind": "proforma",
        "items": [{"description": "چیزی", "quantity": 1, "unit_price": 1000}]})
    assert r.status_code == 422


def test_free_invoice_line_is_registered_as_a_service():
    ctx = _activity()
    sales, mgr = _h("0911"), _h("0910")
    before = client.get("/api/product-models", headers=mgr).json()
    fin = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [{"description": "خدمات مشاوره", "quantity": 1, "unit_price": 4_000_000}]})
    assert fin.status_code == 201, fin.text  # no stock error for a free line
    models = client.get("/api/product-models", headers=mgr).json()
    svc = next(m for m in models if m["name"] == "خدمات مشاوره")
    assert svc["is_service"] is True and len(models) == len(before) + 1


def test_final_invoice_needs_items():
    ctx = _activity()
    sales = _h("0911")
    r = client.post("/api/invoices", headers=sales,
                    json={"activity_id": ctx["aid"], "kind": "final"})
    assert r.status_code == 400


def test_cannot_sell_more_linked_stock_than_available():
    ctx = _activity()
    sales = _h("0911")
    mid = _bulk_product("فیبر", 5)
    r = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [{"description": "فیبر", "product_model_id": mid, "quantity": 10, "unit_price": 1}]})
    assert r.status_code == 400  # not enough stock


def test_proforma_can_be_deleted_but_final_cannot():
    ctx = _activity()
    sales = _h("0911")
    pf = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "proforma",
        "items": [{"description": "قلم", "quantity": 1, "unit_price": 1000}]}).json()
    assert client.delete(f"/api/invoices/{pf['id']}", headers=sales).status_code == 204

    fin = client.post("/api/invoices", headers=sales, json={
        "activity_id": ctx["aid"], "kind": "final",
        "items": [{"description": "قلم", "quantity": 1, "unit_price": 1000}]}).json()
    assert client.delete(f"/api/invoices/{fin['id']}", headers=sales).status_code == 400
