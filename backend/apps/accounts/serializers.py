from __future__ import annotations

from rest_framework import serializers

from .models import Permission, Role, System, User, UserRole


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ["id", "code", "name"]


class RoleSerializer(serializers.ModelSerializer):
    system_code = serializers.CharField(source="system.code", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "code", "name", "system", "system_code", "is_manager"]


class UserSerializer(serializers.ModelSerializer):
    role_codes = serializers.SerializerMethodField()
    permission_codes = serializers.SerializerMethodField()
    department_codes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "phone", "full_name", "is_active", "is_system_admin",
            "role_codes", "permission_codes", "department_codes",
        ]

    def get_role_codes(self, obj) -> list[str]:
        return list(obj.roles.values_list("code", flat=True))

    def get_permission_codes(self, obj) -> list[str]:
        return sorted(obj.permission_codes())

    def get_department_codes(self, obj) -> list[str]:
        return sorted(obj.department_codes())


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Role.objects.all(), required=False, write_only=True
    )

    class Meta:
        model = User
        fields = ["id", "phone", "full_name", "is_active", "is_system_admin",
                  "password", "role_ids"]

    def create(self, validated):
        role_ids = validated.pop("role_ids", [])
        password = validated.pop("password", "") or "changeme123"
        user = User.objects.create_user(password=password, **validated)
        for role in role_ids:
            UserRole.objects.get_or_create(user=user, role=role)
        return user

    def update(self, instance, validated):
        role_ids = validated.pop("role_ids", None)
        password = validated.pop("password", None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        if role_ids is not None:
            instance.userrole_set.all().delete()
            for role in role_ids:
                UserRole.objects.get_or_create(user=instance, role=role)
        return instance


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
