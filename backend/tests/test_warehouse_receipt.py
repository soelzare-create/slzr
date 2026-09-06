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


def test_invoice_line_shows_serials_from_receipt(seeded, make_user, api):
    from apps.sales.models import Proforma, ProformaLine
    from apps.sales import services as sales
    from apps.warehouse.models import GoodsReceipt, ReceiptItem

    purchase, line = _registered_purchase(make_user)  # item qty 2, cost 500
    wh = make_user("09120000077", "انباردار", role_code="warehouse_employee")
    receipt = GoodsReceipt.objects.create(purchase=purchase, received_by=wh)
    ReceiptItem.objects.create(receipt=receipt, purchase_line=line, item=line.item,
                               quantity=2, serials=["A1", "A2"])

    seller = make_user("09120000078", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    proforma = Proforma.objects.create(customer=customer, owner=seller)
    ProformaLine.objects.create(proforma=proforma, item=line.item, quantity=1,
                                unit_price=600, source_purchase_line=line)  # ≥ 500×1.05
    sales.confirm_proforma(proforma, actor=seller)
    invoice = sales.convert_to_invoice(proforma, actor=seller)

    _auth(api, seller)
    resp = api.get(f"/api/invoices/{invoice.id}")
    assert resp.status_code == 200, resp.data
    assert resp.data["lines"][0]["serials"] == ["A1", "A2"]


def test_serials_report_lists_all(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    wh = make_user("09120000079", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)
    api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 2, "serials": ["Z1", "Z2"]}],
    }, format="json")
    r = api.get("/api/receipts/serials")
    assert r.status_code == 200, r.data
    found = {row["serial"] for row in r.data}
    assert {"Z1", "Z2"} <= found
    row = next(x for x in r.data if x["serial"] == "Z1")
    assert row["purchase_number"] == purchase.number


def test_warehouse_can_delete_receipt(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    wh = make_user("09120000080", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)
    created = api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 2, "serials": ["D1", "D2"]}],
    }, format="json").data
    rid = created["id"]
    assert any(x["serial"] == "D1" for x in api.get("/api/receipts/serials").data)

    resp = api.delete(f"/api/receipts/{rid}")
    assert resp.status_code == 204
    assert api.get(f"/api/receipts/{rid}").status_code == 404
    # its serials are gone from the report, and the purchase is no longer received
    assert not any(x["serial"] == "D1" for x in api.get("/api/receipts/serials").data)
    purchase.refresh_from_db()
    assert not purchase.goods_receipts.exists()


def test_delete_receipt_requires_warehouse_permission(seeded, make_user, api):
    purchase, line = _registered_purchase(make_user)
    wh = make_user("09120000081", "انباردار", role_code="warehouse_employee")
    _auth(api, wh)
    created = api.post("/api/receipts", {
        "purchase": purchase.id,
        "items": [{"purchase_line": line.id, "quantity": 1, "serials": []}],
    }, format="json").data
    # a user without warehouse access cannot delete it
    seller = make_user("09120000082", "فروشنده", role_code="sales_employee")
    _auth(api, seller)
    assert api.delete(f"/api/receipts/{created['id']}").status_code == 403


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
