"""Warehouse goods-receipt: recording physical hand-over of a purchase and
entering serial numbers. It is a record layer (does not gate invoicing)."""
from __future__ import annotations

import pytest

from apps.core.models import Item, Party
from apps.procurement.models import Purchase, PurchaseLine
from apps.procurement import services as proc

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


def _registered_purchase(make_user):
    buyer = make_user("09120000071", "بازرگان", role_code="procurement_manager")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="سوییچ", kind=Item.Kind.GOODS, unit="دستگاه")
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)
    line = PurchaseLine.objects.create(purchase=purchase, item=item, quantity=2, unit_price=500)
    proc.register_purchase(purchase, actor=buyer)
    return purchase, line


def test_warehouse_records_receipt_with_serials(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    wh = make_user("09120000072", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)

    # the receivable list shows the registered purchase, not yet received
    rec = api.get("/api/receipts/receivable")
    assert rec.status_code == 200, rec.data
    row = next(r for r in rec.data if r["id"] == purchase.id)
    assert row["received"] is False and len(row["lines"]) == 1

    resp = api.post("/api/receipts", {
        "purchase": purchase.id,
        "notes": "تحویل شد",
        "items": [{"purchase_line": line.id, "quantity": 2, "serials": ["SN-1", "SN-2"]}],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["number"].startswith("GR-")
    assert resp.data["items"][0]["serials"] == ["SN-1", "SN-2"]
    assert resp.data["items"][0]["item_name"] == "سوییچ"

    purchase.refresh_from_db()
    assert purchase.goods_receipts.exists()
    # now marked received in the receivable list
    rec2 = api.get("/api/receipts/receivable")
    assert next(r for r in rec2.data if r["id"] == purchase.id)["received"] is True


def test_receipt_serials_optional(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    wh = make_user("09120000073", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)
    resp = api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 2, "serials": []}],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["items"][0]["serials"] == []


def test_receipt_blocked_for_unregistered_purchase(seeded, make_user, api):
    buyer = make_user("09120000074", "بازرگان", role_code="procurement_manager")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="کالا", kind=Item.Kind.GOODS)
    purchase = Purchase.objects.create(supplier=supplier, owner=buyer)  # DRAFT
    line = PurchaseLine.objects.create(purchase=purchase, item=item, quantity=1, unit_price=100)
    wh = make_user("09120000075", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)
    resp = api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 1, "serials": []}],
    }, format="json")
    assert resp.status_code == 400


def test_receipt_requires_warehouse_permission(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    seller = make_user("09120000076", "فروشنده", role_code="sales_employee")
    _auth(api, seller)
    assert api.get("/api/receipts/receivable").status_code == 403
    resp = api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 1, "serials": []}],
    }, format="json")
    assert resp.status_code == 403
