"""Company profile (letterhead + bank) settings and the party registration no."""
from __future__ import annotations

import pytest

from apps.core.models import Party

pytestmark = pytest.mark.django_db


def _auth(api, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


def test_company_profile_read_and_admin_edit(seeded, make_user, api):
    admin = make_user("09120000091", "ادمین", system_admin=True)
    _auth(api, admin)
    got = api.get("/api/company")
    assert got.status_code == 200
    assert got.data["name"]  # seeded default

    resp = api.patch("/api/company", {"bank_account": "123-456", "bank_iban": "IR33"},
                     format="json")
    assert resp.status_code == 200, resp.data
    assert resp.data["bank_account"] == "123-456"
    assert api.get("/api/company").data["bank_iban"] == "IR33"


def test_company_profile_not_editable_by_non_admin(seeded, make_user, api):
    seller = make_user("09120000092", "فروشنده", role_code="sales_employee")
    _auth(api, seller)
    assert api.get("/api/company").status_code == 200  # read allowed
    resp = api.patch("/api/company", {"bank_account": "x"}, format="json")
    assert resp.status_code == 403


def test_party_registration_no_roundtrip(seeded, make_user, api):
    admin = make_user("09120000093", "ادمین", system_admin=True)
    _auth(api, admin)
    resp = api.post("/api/parties", {"name": "مشتری", "is_customer": True,
                                     "registration_no": "TR-9001"}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["registration_no"] == "TR-9001"
    assert Party.objects.get(pk=resp.data["id"]).registration_no == "TR-9001"
