from __future__ import annotations

from rest_framework import serializers

from .models import CompanyProfile, Item, Notification, Party


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ["id", "name", "is_customer", "is_supplier", "national_id",
                  "registration_no", "phone", "email", "address", "notes", "created_at"]


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ["id", "name", "brand_sub", "address", "phone1", "phone2", "mobile",
                  "email", "website", "economic_code", "registration_no",
                  "bank_name", "bank_branch", "bank_account", "bank_iban",
                  "bank_branch_code"]
        read_only_fields = ["id"]


class ItemSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Item
        fields = ["id", "name", "sku", "unit", "kind", "kind_display", "is_active"]


class NotificationSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "kind", "kind_display", "message", "source_ref",
                  "is_read", "created_at"]
