"""Editing of documents (Item/Party/Proforma/Purchase/Invoice) and the
goods (کالا) vs service (خدمت) split on records."""
from __future__ import annotations

import datetime

import pytest

from apps.core.models import Item, Party

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


# --- goods / service categorization ---------------------------------------

def test_proforma_splits_goods_and_service_totals(seeded, make_user, api):
    seller = make_user("09120000051", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    goods = Item.objects.create(name="سوییچ", kind=Item.Kind.GOODS)
    service = Item.objects.create(name="نصب", kind=Item.Kind.SERVICE)
    _auth(api, seller)
    resp = api.post("/api/proformas", {
        "customer": customer.id,
        "lines": [
            {"item": goods.id, "quantity": 2, "unit_price": 1000},   # 2000 goods
            {"item": service.id, "quantity": 1, "unit_price": 500},  # 500 service
        ],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert int(resp.data["total"]) == 2500
    assert int(resp.data["goods_total"]) == 2000
    assert int(resp.data["service_total"]) == 500
    kinds = {l["item_kind"] for l in resp.data["lines"]}
    assert kinds == {"GOODS", "SERVICE"}


# --- item edit -------------------------------------------------------------

def test_item_can_be_edited(seeded, make_user, api):
    admin = make_user("09120000052", "ادمین", system_admin=True)
    item = Item.objects.create(name="قطعه", kind=Item.Kind.GOODS, unit="عدد")
    _auth(api, admin)
    resp = api.patch(f"/api/items/{item.id}", {"kind": "SERVICE", "name": "خدمت نصب"},
                     format="json")
    assert resp.status_code == 200, resp.data
    item.refresh_from_db()
    assert item.kind == Item.Kind.SERVICE
    assert item.name == "خدمت نصب"


# --- proforma edit (draft only) -------------------------------------------

def test_proforma_editable_while_draft(seeded, make_user, api):
    seller = make_user("09120000053", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="کالا", kind=Item.Kind.GOODS)
    _auth(api, seller)
    created = api.post("/api/proformas", {
        "customer": customer.id,
        "lines": [{"item": item.id, "quantity": 1, "unit_price": 100}],
    }, format="json").data
    pid = created["id"]
    resp = api.patch(f"/api/proformas/{pid}", {
        "lines": [{"item": item.id, "quantity": 3, "unit_price": 200}],
    }, format="json")
    assert resp.status_code == 200, resp.data
    assert int(resp.data["total"]) == 600


def test_proforma_not_editable_after_convert(seeded, make_user, api):
    seller = make_user("09120000054", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="کالا", kind=Item.Kind.GOODS)
    _auth(api, seller)
    created = api.post("/api/proformas", {
        "customer": customer.id,
        "lines": [{"item": item.id, "quantity": 1, "unit_price": 100}],
    }, format="json").data
    pid = created["id"]
    # convert straight to an invoice (decoupled flow) → proforma is now INVOICED
    conv = api.post(f"/api/proformas/{pid}/convert")
    assert conv.status_code == 200, conv.data
    resp = api.patch(f"/api/proformas/{pid}", {
        "lines": [{"item": item.id, "quantity": 9, "unit_price": 999}],
    }, format="json")
    assert resp.status_code == 400


# --- purchase edit (draft only) -------------------------------------------

def test_purchase_editable_while_draft_then_locked(seeded, make_user, api):
    buyer = make_user("09120000055", "بازرگان", role_code="procurement_manager")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="کالا", kind=Item.Kind.GOODS)
    _auth(api, buyer)
    created = api.post("/api/purchases", {
        "supplier": supplier.id,
        "lines": [{"item": item.id, "quantity": 2, "unit_price": 500}],
    }, format="json").data
    pid = created["id"]
    # draft edit works
    resp = api.patch(f"/api/purchases/{pid}", {
        "lines": [{"item": item.id, "quantity": 4, "unit_price": 500}],
    }, format="json")
    assert resp.status_code == 200, resp.data
    assert int(resp.data["total"]) == 2000
    # register → locked
    api.post(f"/api/purchases/{pid}/register")
    resp = api.patch(f"/api/purchases/{pid}", {
        "lines": [{"item": item.id, "quantity": 99, "unit_price": 1}],
    }, format="json")
    assert resp.status_code == 400


# --- invoice: metadata edit only, no direct create/delete -----------------

def test_invoice_metadata_editable_but_financials_frozen(seeded, make_user, api):
    from apps.sales.models import Invoice, InvoiceLine

    seller = make_user("09120000056", "فروشنده", role_code="sales_employee")
    c1 = Party.objects.create(name="مشتری ۱", is_customer=True)
    c2 = Party.objects.create(name="مشتری ۲", is_customer=True)
    item = Item.objects.create(name="خدمت", kind=Item.Kind.SERVICE)
    inv = Invoice.objects.create(type=Invoice.Type.SERVICE, customer=c1, owner=seller,
                                 date=datetime.date.today())
    InvoiceLine.objects.create(invoice=inv, item=item, quantity=1, unit_price=1000)
    _auth(api, seller)
    # notes are editable; customer (financial) is read-only and must not change
    resp = api.patch(f"/api/invoices/{inv.id}", {
        "notes": "یادداشت اصلاح‌شده", "customer": c2.id,
    }, format="json")
    assert resp.status_code == 200, resp.data
    inv.refresh_from_db()
    assert inv.notes == "یادداشت اصلاح‌شده"
    assert inv.customer_id == c1.id  # unchanged
    assert int(resp.data["service_total"]) == 1000


def test_invoice_direct_create_and_delete_blocked(seeded, make_user, api):
    from apps.sales.models import Invoice, InvoiceLine

    seller = make_user("09120000057", "فروشنده", role_code="sales_employee")
    c1 = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="خدمت", kind=Item.Kind.SERVICE)
    inv = Invoice.objects.create(type=Invoice.Type.SERVICE, customer=c1, owner=seller,
                                 date=datetime.date.today())
    InvoiceLine.objects.create(invoice=inv, item=item, quantity=1, unit_price=1000)
    _auth(api, seller)
    assert api.post("/api/invoices", {"customer": c1.id}, format="json").status_code == 405
    assert api.delete(f"/api/invoices/{inv.id}").status_code == 405
