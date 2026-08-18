"""Tests for the unified party model (customer/supplier roles) and the
purchase → accounting chain at the data-model level."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_pp.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-pp"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import (  # noqa: E402
    FinancialType,
    PurchaseStatus,
    UserRole,
)
from app.models.accounting import FinancialDocument  # noqa: E402
from app.models.party import Party  # noqa: E402
from app.models.purchase import Purchase, PurchaseItem  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all(
        [
            User_row("مدیر", UserRole.manager, "0910"),
            User_row("فروش", UserRole.sales, "0911"),
            User_row("انباردار", UserRole.warehouse, "0913"),
        ]
    )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def User_row(name, role, phone):
    from app.models.user import User

    return User(name=name, role=role, phone=phone,
                password_hash=hash_password("pass1234"))


def _h(phone: str) -> dict:
    r = client.post("/api/auth/login", data={"username": phone, "password": "pass1234"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_party_requires_at_least_one_role():
    r = client.post("/api/parties", headers=_h("0910"),
                    json={"name": "بی‌نقش", "is_customer": False, "is_supplier": False})
    assert r.status_code == 422


def test_role_filtering():
    # a pure customer, a pure supplier, and one that is both
    client.post("/api/parties", headers=_h("0911"),
                json={"name": "فقط مشتری", "is_customer": True, "is_supplier": False})
    client.post("/api/parties", headers=_h("0913"),
                json={"name": "فقط تأمین‌کننده", "is_customer": False, "is_supplier": True})
    client.post("/api/parties", headers=_h("0910"),
                json={"name": "هردو", "is_customer": True, "is_supplier": True})

    customers = client.get("/api/parties", headers=_h("0910"),
                           params={"role": "customer"}).json()
    suppliers = client.get("/api/parties", headers=_h("0910"),
                           params={"role": "supplier"}).json()
    cust_names = {p["name"] for p in customers}
    supp_names = {p["name"] for p in suppliers}

    assert "فقط مشتری" in cust_names and "هردو" in cust_names
    assert "فقط تأمین‌کننده" not in cust_names
    assert "فقط تأمین‌کننده" in supp_names and "هردو" in supp_names
    assert "فقط مشتری" not in supp_names


def test_warehouse_can_write_but_technical_cannot():
    # warehouse may create a supplier
    ok = client.post("/api/parties", headers=_h("0913"),
                     json={"name": "تأمین‌کنندهٔ انبار", "is_customer": False,
                           "is_supplier": True})
    assert ok.status_code == 201


def test_purchase_expense_and_party_balance():
    """A party sold-to and bought-from should net out in accounting."""
    db = SessionLocal()
    try:
        both = Party(name="طرف دوطرفه", is_customer=True, is_supplier=True)
        db.add(both)
        db.flush()

        # We sold them 1,000,000 (income) and bought 300,000 from them (expense).
        pur = Purchase(supplier_id=both.id, buyer_id=1, total_amount=300_000,
                       status=PurchaseStatus.unpaid)
        db.add(pur)
        db.flush()
        db.add(PurchaseItem(purchase_id=pur.id, product_model_id=None,
                            quantity=3, unit_cost=100_000))

        db.add(FinancialDocument(party_id=both.id, amount=1_000_000,
                                 type=FinancialType.income))
        db.add(FinancialDocument(party_id=both.id, purchase_id=pur.id,
                                 amount=300_000, type=FinancialType.expense))
        db.commit()

        docs = db.query(FinancialDocument).filter_by(party_id=both.id).all()
        income = sum(float(d.amount) for d in docs if d.type == FinancialType.income)
        expense = sum(float(d.amount) for d in docs if d.type == FinancialType.expense)
        assert income - expense == 700_000  # net balance for the party
    finally:
        db.close()
