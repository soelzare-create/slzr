"""Tests for party contact people (افراد رابط) — the سمت field, mandatory
position selection, and attribution of who added each contact."""
from __future__ import annotations

import os
import tempfile

import pytest

_tmp_db = os.path.join(tempfile.mkdtemp(), "test_contacts.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
os.environ["SECRET_KEY"] = "test-secret-contacts"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all(
        [
            User(name="سمیرا مدیر", role=UserRole.manager, phone="0910",
                 password_hash=hash_password("pass1234")),
            User(name="کارمند فنی", role=UserRole.technical, phone="0912",
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


def _make_party() -> int:
    r = client.post("/api/parties", headers=_h("0910"),
                    json={"name": "شرکت نمونه", "is_customer": True})
    return r.json()["id"]


def test_add_contact_records_who_added_it():
    party_id = _make_party()
    r = client.post(
        f"/api/parties/{party_id}/contacts",
        headers=_h("0910"),
        json={"name": "رضا احمدی", "phone": "09120000000", "position": "procurement"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["position"] == "procurement"
    assert body["created_by_name"] == "سمیرا مدیر"  # attribution captured
    assert body["created_by_id"] == 1


def test_position_is_required():
    party_id = _make_party()
    r = client.post(
        f"/api/parties/{party_id}/contacts",
        headers=_h("0910"),
        json={"name": "بدون سمت"},  # no position → must be rejected
    )
    assert r.status_code == 422


def test_position_must_be_from_the_list():
    party_id = _make_party()
    r = client.post(
        f"/api/parties/{party_id}/contacts",
        headers=_h("0910"),
        json={"name": "سمت نامعتبر", "position": "president"},
    )
    assert r.status_code == 422


def test_contacts_listed_and_embedded_on_party():
    party_id = _make_party()
    for name, pos in [("مدیرعامل شرکت", "ceo"), ("حسابدار", "finance")]:
        client.post(f"/api/parties/{party_id}/contacts", headers=_h("0910"),
                    json={"name": name, "position": pos})

    listed = client.get(f"/api/parties/{party_id}/contacts", headers=_h("0910")).json()
    assert {c["name"] for c in listed} == {"مدیرعامل شرکت", "حسابدار"}

    # The CRM detail (GET a party) embeds its contacts.
    party = client.get(f"/api/parties/{party_id}", headers=_h("0910")).json()
    assert {c["position"] for c in party["contacts"]} == {"ceo", "finance"}


def test_delete_contact():
    party_id = _make_party()
    cid = client.post(f"/api/parties/{party_id}/contacts", headers=_h("0910"),
                      json={"name": "قابل حذف", "position": "other"}).json()["id"]
    assert client.delete(f"/api/parties/{party_id}/contacts/{cid}",
                         headers=_h("0910")).status_code == 204
    remaining = client.get(f"/api/parties/{party_id}/contacts", headers=_h("0910")).json()
    assert all(c["id"] != cid for c in remaining)


def test_technical_role_cannot_add_contact():
    party_id = _make_party()
    r = client.post(f"/api/parties/{party_id}/contacts", headers=_h("0912"),
                    json={"name": "غیرمجاز", "position": "sales"})
    assert r.status_code == 403


def test_add_contact_to_missing_party_is_404():
    r = client.post("/api/parties/999999/contacts", headers=_h("0910"),
                    json={"name": "کسی", "position": "staff"})
    assert r.status_code == 404
