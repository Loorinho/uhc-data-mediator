from rest_framework.permissions import BasePermission


class IsApplicationAdmin(BasePermission):
    """Application administrators are superusers or members of the admin group."""

    message = "Only administrators can manage users and roles."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.groups.filter(name__iexact="admin").exists())
        )
