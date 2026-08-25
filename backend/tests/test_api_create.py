"""API create endpoints assign owner server-side (regression: owner must not be
a required request field)."""
from __future__ import annotations

import pytest

from apps.core.models import Item, Party

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


def test_create_proforma_sets_owner_to_creator(seeded, make_user, api):
    seller = make_user("09120000041", "فروشنده", role_code="sales_employee")
    customer = Party.objects.create(name="مشتری", is_customer=True)
    item = Item.objects.create(name="کالا")
    _auth(api, seller)
    resp = api.post("/api/proformas", {
        "customer": customer.id,
        "lines": [{"item": item.id, "quantity": 1, "unit_price": 100}],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["owner"] == seller.id
    assert resp.data["number"].startswith("PF-")


def test_create_purchase_defaults_owner(seeded, make_user, api):
    buyer = make_user("09120000042", "بازرگان", role_code="procurement_manager")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="کالا")
    _auth(api, buyer)
    resp = api.post("/api/purchases", {
        "supplier": supplier.id,
        "lines": [{"item": item.id, "quantity": 2, "unit_price": 500}],
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["owner"] == buyer.id
