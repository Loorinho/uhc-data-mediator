from core.auditing.services import get_role
from rest_framework.permissions import BasePermission


class IsAuditor(BasePermission):
    message = "Only auditors may access security audit records."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return get_role(user).lower() == "auditor"
