from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import generics, permissions
from rest_framework.views import APIView

from core.responses import api_response

from .serializers import (
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserSerializer,
)


class LoginView(APIView):
    """POST username + password -> user info + access/refresh tokens."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()
        user = serializer.validated_data["user"]
        return api_response(
            message="Login successful.",
            data={
                "username": user.username,
                "role": list(user.groups.values_list("name", flat=True)),
                "tokens": tokens,
            },
        )


class RefreshView(APIView):
    """POST refresh token -> new access + refresh tokens (rotated).

    The supplied refresh token is verified against the database: it must
    exist, be valid, and be unexpired. On success the old token is
    invalidated and a fresh pair is returned.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            message="Token refreshed successfully.",
            data={"tokens": serializer.save()},
        )


class RegisterView(generics.CreateAPIView):
    """POST username + password -> create a user (unique username)."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(
            message="Registration successful.",
            data={
                "username": user.username,
                "role": list(user.groups.values_list("name", flat=True)),
            },
        )


class RoleListCreateView(APIView):
    """GET -> all roles.  POST -> create a new role."""

    def get(self, request):
        roles = Group.objects.all().order_by("name")
        return api_response(
            message="Roles retrieved successfully.",
            data=RoleSerializer(roles, many=True).data,
        )

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return api_response(
            message="Role created successfully.",
            data=RoleSerializer(role).data,
        )


class MeView(APIView):
    """GET -> the currently authenticated user's profile."""

    def get(self, request):
        return api_response(
            message="User profile retrieved successfully.",
            data=UserSerializer(request.user).data,
        )


class UserListView(generics.ListAPIView):
    """GET -> all users."""

    queryset = get_user_model().objects.all().order_by("id")
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return api_response(
            message="Users retrieved successfully.",
            data=self.get_serializer(queryset, many=True).data,
        )
