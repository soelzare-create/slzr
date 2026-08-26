from __future__ import annotations

from datetime import date as date_cls

from rest_framework import serializers

from .models import Account, Expense, JournalEntry, JournalLine, Payment


class AccountSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Account
        fields = ["id", "code", "name", "type", "type_display", "parent", "is_active"]


class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source="account.code", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    party_name = serializers.CharField(source="party.name", read_only=True, default=None)

    class Meta:
        model = JournalLine
        fields = ["id", "account", "account_code", "account_name", "party",
                  "party_name", "debit", "credit", "description"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)
    total_debit = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ["id", "number", "date", "description", "source_ref", "is_reversal",
                  "reversal_of", "total_debit", "lines", "created_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    paid_from_name = serializers.CharField(source="paid_from.name", read_only=True)
    party_name = serializers.CharField(source="party.name", read_only=True, default=None)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    date = serializers.DateField(required=False)

    class Meta:
        model = Expense
        fields = ["id", "number", "kind", "kind_display", "category", "amount",
                  "paid_from", "paid_from_name", "party", "party_name", "date",
                  "description", "status", "status_display", "owner_name", "created_at"]
        read_only_fields = ["number", "status", "owner"]

    def validate_amount(self, v):
        if v <= 0:
            raise serializers.ValidationError("مبلغ باید بزرگتر از صفر باشد.")
        return v

    def validate(self, attrs):
        attrs.setdefault("date", date_cls.today())
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    party_name = serializers.CharField(source="party.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    date = serializers.DateField(required=False)

    class Meta:
        model = Payment
        fields = ["id", "number", "direction", "direction_display", "party", "party_name",
                  "amount", "account", "account_name", "date", "description", "status",
                  "status_display", "owner_name", "created_at"]
        read_only_fields = ["number", "status", "owner"]

    def validate_amount(self, v):
        if v <= 0:
            raise serializers.ValidationError("مبلغ باید بزرگتر از صفر باشد.")
        return v

    def validate(self, attrs):
        attrs.setdefault("date", date_cls.today())
        return attrs
