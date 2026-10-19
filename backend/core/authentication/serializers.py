from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from core.models import RefreshToken

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """A system role (backed by Django's Group)."""

    class Meta:
        model = Group
        fields = ("id", "name")

    def validate_name(self, value):
        if Group.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A role with that name already exists.")
        return value


class LoginSerializer(serializers.Serializer):
    """Validate username + password, then issue an access JWT and a
    database-stored refresh token."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid credentials supplied")
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        access = AccessToken.for_user(user)
        access["username"] = user.username
        access["roles"] = list(user.groups.values_list("name", flat=True))
        refresh = RefreshToken.objects.create(user=user)
        return {
            "access": str(access),
            "refresh": refresh.token,
        }


class RefreshSerializer(serializers.Serializer):
    """Verify a DB-stored refresh token, then rotate it: the old token is
    invalidated and a new access + refresh pair is issued."""

    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken.objects.select_related("user").get(token=value)
        except RefreshToken.DoesNotExist:
            raise serializers.ValidationError("Invalid refresh token.")
        if not token.is_valid or token.is_expired:
            raise serializers.ValidationError("Invalid refresh token.")
        return value

    def create(self, validated_data):
        old_token = RefreshToken.objects.select_related("user").get(
            token=validated_data["refresh"]
        )
        old_token.invalidate()

        user = old_token.user
        access = AccessToken.for_user(user)
        access["username"] = user.username
        access["roles"] = list(user.groups.values_list("name", flat=True))
        new_refresh = RefreshToken.objects.create(user=user)
        return {
            "access": str(access),
            "refresh": new_refresh.token,
        }


class RegisterSerializer(serializers.ModelSerializer):
    """Create a user with a unique username, a hashed password, and a role
    that must already exist in the system."""

    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Group.objects.all(),
        error_messages={
            "does_not_exist": "Role '{value}' does not exist.",
            "incorrect_type": "A role name is required.",
        },
    )

    class Meta:
        model = User
        fields = ("username", "password", "role")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def create(self, validated_data):
        role = validated_data.pop("role")
        user = User.objects.create_user(**validated_data)
        user.groups.add(role)
        return user


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(
        many=True, slug_field="name", source="groups", read_only=True
    )

    class Meta:
        model = User
        fields = ("id", "username", "roles", "is_superuser")
