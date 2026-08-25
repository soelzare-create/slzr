"""Tests for RBAC + object-level ownership through the API (Section 3)."""
from __future__ import annotations

import pytest

from apps.core.models import Party
from apps.sales.models import Proforma

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    token = RefreshToken.for_user(user).access_token
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


def test_login_returns_permissions(seeded, api):
    resp = api.post("/api/auth/login", {"phone": "09120000000",
                                        "password": "admin1234"}, format="json")
    assert resp.status_code == 200
    assert resp.data["user"]["is_system_admin"] is True


def test_employee_sees_only_own_proformas(seeded, make_user, api):
    e1 = make_user("09120000011", "کارمند۱", role_code="sales_employee")
    e2 = make_user("09120000012", "کارمند۲", role_code="sales_employee")
    customer = Party.objects.create(name="م", is_customer=True)
    Proforma.objects.create(customer=customer, owner=e1)
    Proforma.objects.create(customer=customer, owner=e2)

    _auth(api, e1)
    resp = api.get("/api/proformas")
    assert resp.status_code == 200
    results = resp.data["results"] if "results" in resp.data else resp.data
    assert len(results) == 1  # only e1's own record


def test_manager_sees_all_department_proformas(seeded, make_user, api):
    e1 = make_user("09120000021", "کارمند", role_code="sales_employee")
    mgr = make_user("09120000022", "مدیرفروش", role_code="sales_manager")
    customer = Party.objects.create(name="م", is_customer=True)
    Proforma.objects.create(customer=customer, owner=e1)
    Proforma.objects.create(customer=customer, owner=mgr)

    _auth(api, mgr)
    resp = api.get("/api/proformas")
    results = resp.data["results"] if "results" in resp.data else resp.data
    assert len(results) == 2  # manager holds sales.view_all


def test_employee_cannot_administer_users(seeded, make_user, api):
    e1 = make_user("09120000031", "کارمند", role_code="sales_employee")
    _auth(api, e1)
    resp = api.get("/api/users")
    assert resp.status_code == 403
