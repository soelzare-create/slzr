"""Tests for the procurement purchase-assignment flow (Section 5)."""
from __future__ import annotations

import pytest

from apps.core.models import Item, Notification, Party
from apps.procurement.models import Purchase

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


def _payload(supplier, item):
    return {"supplier": supplier.id,
            "lines": [{"item": item.id, "quantity": 1, "unit_price": 1000}]}


def test_manager_assigns_purchase_on_create(seeded, make_user, api):
    mgr = make_user("09120000091", "مدیر بازرگانی", role_code="procurement_manager")
    emp = make_user("09120000092", "کارمند بازرگانی", role_code="procurement_employee")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="کالا")

    _auth(api, mgr)
    resp = api.post("/api/purchases", {**_payload(supplier, item), "owner": emp.id}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["owner"] == emp.id
    # The assignee is notified.
    assert Notification.objects.filter(recipient=emp).exists()


def test_employee_cannot_assign_to_others_on_create(seeded, make_user, api):
    emp = make_user("09120000093", "کارمند", role_code="procurement_employee")
    other = make_user("09120000094", "دیگری", role_code="procurement_employee")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    item = Item.objects.create(name="کالا")

    _auth(api, emp)
    resp = api.post("/api/purchases", {**_payload(supplier, item), "owner": other.id}, format="json")
    assert resp.status_code == 201
    assert resp.data["owner"] == emp.id  # forced to the creator, not `other`


def test_manager_reassigns_purchase(seeded, make_user, api):
    mgr = make_user("09120000095", "مدیر", role_code="procurement_manager")
    emp = make_user("09120000096", "کارمند", role_code="procurement_employee")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    purchase = Purchase.objects.create(supplier=supplier, owner=mgr)

    _auth(api, mgr)
    resp = api.post(f"/api/purchases/{purchase.id}/assign", {"owner": emp.id}, format="json")
    assert resp.status_code == 200
    purchase.refresh_from_db()
    assert purchase.owner_id == emp.id


def test_employee_cannot_reassign(seeded, make_user, api):
    emp = make_user("09120000097", "کارمند", role_code="procurement_employee")
    supplier = Party.objects.create(name="تأمین", is_supplier=True)
    purchase = Purchase.objects.create(supplier=supplier, owner=emp)

    _auth(api, emp)
    resp = api.post(f"/api/purchases/{purchase.id}/assign", {"owner": emp.id}, format="json")
    assert resp.status_code == 403


def test_team_endpoint_lists_procurement_users(seeded, make_user, api):
    mgr = make_user("09120000098", "مدیر", role_code="procurement_manager")
    make_user("09120000099", "کارمند", role_code="procurement_employee")
    make_user("09120000100", "فروشنده", role_code="sales_employee")
    _auth(api, mgr)
    resp = api.get("/api/purchases/team")
    assert resp.status_code == 200
    names = {u["full_name"] for u in resp.data}
    assert "مدیر" in names and "کارمند" in names and "فروشنده" not in names
