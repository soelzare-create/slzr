from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, System, User
from .permissions import HasPermissionCode
from .serializers import (
    LoginSerializer, RoleSerializer, SystemSerializer, UserSerializer,
    UserWriteSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Login by phone + password → JWT access/refresh + user profile."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request,
        username=serializer.validated_data["phone"],
        password=serializer.validated_data["password"],
    )
    if user is None or not user.is_active:
        return Response({"detail": "شماره یا رمز عبور نادرست است."},
                        status=status.HTTP_401_UNAUTHORIZED)
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


class IsSystemAdmin(HasPermissionCode):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated
                    and request.user.is_system_admin)


class UserViewSet(viewsets.ModelViewSet):
    """User administration — system admin only (Section 3, decision #8)."""

    queryset = User.objects.all().prefetch_related("roles")
    permission_classes = [IsSystemAdmin]

    def get_serializer_class(self):
        if self.action in {"list", "retrieve"}:
            return UserSerializer
        return UserWriteSerializer


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Role.objects.select_related("system").all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class SystemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = [IsAuthenticated]
