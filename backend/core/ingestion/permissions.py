from rest_framework.permissions import BasePermission

DATA_PROVIDER_ROLE = "data_provider"


class IsDataProvider(BasePermission):
    """Only users with the 'data_provider' role (Django group) may proceed."""

    message = (
        "You are not authorized to trigger a data acquisition."
    )

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.groups.filter(name=DATA_PROVIDER_ROLE).exists()
        )
