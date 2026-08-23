"""Phase 4B — recording a purchase brings goods into stock and books an expense,
mirroring the sales flow. Covers serial + bulk lines, stock/ledger effects,
supplier-role validation, and RBAC."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_purchases.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-purchases"

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
    db.add_all(
        [
            User(name="مدیر", role=UserRole.manager, phone="0910",
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


def _supplier() -> int:
    return client.post("/api/parties", headers=_h("0910"),
                       json={"name": "تأمین‌کننده", "is_customer": False,
                             "is_supplier": True}).json()["id"]


def _model(tracking: str) -> int:
    return client.post("/api/product-models", headers=_h("0910"),
                       json={"name": f"کالای {tracking}", "tracking_type": tracking,
                             "unit_of_measure": "عدد"}).json()["id"]


def _stock(model_id: int) -> float:
    return client.get(f"/api/product-models/{model_id}", headers=_h("0910")).json()[
        "current_stock"
    ]


def test_bulk_purchase_adds_stock_and_books_expense():
    supplier = _supplier()
    model = _model("quantity")
    assert _stock(model) == 0

    r = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier,
        "reference": "INV-500",
        "items": [{"product_model_id": model, "quantity": 10, "unit_cost": 2000}],
    })
    assert r.status_code == 201
    body = r.json()
    assert float(body["total_amount"]) == 20000  # 10 × 2000
    assert _stock(model) == 10  # goods arrived in the warehouse

    # accounting booked one expense against the supplier
    db = SessionLocal()
    try:
        docs = db.query(FinancialDocument).filter_by(
            purchase_id=body["id"], type=FinancialType.expense
        ).all()
        assert len(docs) == 1 and float(docs[0].amount) == 20000
        assert docs[0].party_id == supplier
    finally:
        db.close()


def test_serial_purchase_registers_the_unit():
    supplier = _supplier()
    model = _model("serial")
    r = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier,
        "items": [{"product_model_id": model, "serial_number": "SN-777", "unit_cost": 5000}],
    })
    assert r.status_code == 201
    assert float(r.json()["total_amount"]) == 5000
    assert _stock(model) == 1  # the serialized unit is now in stock

    # the serial is now known to inventory
    units = client.get("/api/stock-items", headers=_h("0910"),
                       params={"model_id": model}).json()
    assert any(u["serial_number"] == "SN-777" for u in units)


def test_duplicate_serial_is_rejected():
    supplier = _supplier()
    model = _model("serial")
    line = {"product_model_id": model, "serial_number": "SN-DUP", "unit_cost": 100}
    assert client.post("/api/purchases", headers=_h("0913"),
                       json={"supplier_id": supplier, "items": [line]}).status_code == 201
    dup = client.post("/api/purchases", headers=_h("0913"),
                      json={"supplier_id": supplier, "items": [line]})
    assert dup.status_code == 409


def test_purchase_requires_a_supplier_role():
    # a customer-only party may not be purchased from
    cust = client.post("/api/parties", headers=_h("0910"),
                       json={"name": "فقط مشتری", "is_customer": True,
                             "is_supplier": False}).json()["id"]
    model = _model("quantity")
    r = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": cust,
        "items": [{"product_model_id": model, "quantity": 1, "unit_cost": 10}],
    })
    assert r.status_code == 422


def test_purchase_requires_at_least_one_item():
    supplier = _supplier()
    r = client.post("/api/purchases", headers=_h("0913"),
                    json={"supplier_id": supplier, "items": []})
    assert r.status_code == 422


def test_sales_role_cannot_record_a_purchase():
    supplier = _supplier()
    model = _model("quantity")
    r = client.post("/api/purchases", headers=_h("0911"), json={
        "supplier_id": supplier,
        "items": [{"product_model_id": model, "quantity": 1, "unit_cost": 10}],
    })
    assert r.status_code == 403


def test_mark_purchase_paid():
    supplier = _supplier()
    model = _model("quantity")
    pid = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier,
        "items": [{"product_model_id": model, "quantity": 2, "unit_cost": 500}],
    }).json()["id"]
    r = client.patch(f"/api/purchases/{pid}", headers=_h("0910"),
                     json={"status": "paid"})
    assert r.status_code == 200 and r.json()["status"] == "paid"


def test_purchase_free_service_item_creates_catalog_entry_no_stock():
    supplier = _supplier()
    before = client.get("/api/product-models", headers=_h("0910")).json()
    r = client.post("/api/purchases", headers=_h("0913"), json={
        "supplier_id": supplier,
        "items": [{"description": "خدمات حمل و نقل", "quantity": 1, "unit_cost": 800_000}],
    })
    assert r.status_code == 201, r.text
    assert float(r.json()["total_amount"]) == 800_000

    models = client.get("/api/product-models", headers=_h("0910")).json()
    svc = next(m for m in models if m["name"] == "خدمات حمل و نقل")
    assert svc["is_service"] is True
    assert svc["current_stock"] == 0
    assert len(models) == len(before) + 1  # a new catalog entry was kept

    # the expense is still booked for the supplier
    db = SessionLocal()
    try:
        docs = db.query(FinancialDocument).filter_by(party_id=supplier,
                                                     type=FinancialType.expense).all()
        assert any(float(d.amount) == 800_000 for d in docs)
    finally:
        db.close()


def test_purchase_reuses_existing_product_by_name():
    supplier = _supplier()
    # buy a free item twice by the same name → only one catalog entry
    for _ in range(2):
        client.post("/api/purchases", headers=_h("0913"), json={
            "supplier_id": supplier,
            "items": [{"description": "لایسنس نرم‌افزار", "quantity": 1, "unit_cost": 100}]})
    models = client.get("/api/product-models", headers=_h("0910")).json()
    assert sum(1 for m in models if m["name"] == "لایسنس نرم‌افزار") == 1
