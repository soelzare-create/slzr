from __future__ import annotations

from rest_framework import serializers

from .models import Account, JournalEntry, JournalLine


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
