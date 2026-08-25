"""Shared pytest fixtures. Seeds the access matrix + chart of accounts once."""
from __future__ import annotations

import pytest
from django.core.management import call_command


@pytest.fixture
def seeded(db):
    call_command("seed")


@pytest.fixture
def make_user(db):
    from apps.accounts.models import Role, User, UserRole

    def _make(phone, name="کاربر", role_code=None, system_admin=False):
        user = User.objects.create_user(phone=phone, password="pass1234",
                                        full_name=name, is_system_admin=system_admin)
        if role_code:
            role = Role.objects.get(code=role_code)
            UserRole.objects.create(user=user, role=role)
        return user

    return _make


@pytest.fixture
def api(db):
    from rest_framework.test import APIClient
    return APIClient()
