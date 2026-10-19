"""
Centralize FHIR authorization.
We don't want analysts calling generation endpoints simply because they know the URL.
"""

from rest_framework.exceptions import PermissionDenied


def user_roles(user):
    """
    Adapt this function if your authentication system
    stores roles in a custom user.role field instead
    of Django Groups.
    """
    roles = set(user.groups.values_list("name", flat=True))

    custom_role = getattr(user, "role", None)

    if isinstance(custom_role, str):
        roles.add(custom_role)

    if hasattr(custom_role, "name"):
        roles.add(custom_role.name)

    return {role.lower() for role in roles}


def is_admin(user):
    return user.is_superuser or "admin" in user_roles(user)


def can_view_release(user, release):
    if not user.is_authenticated:
        return False

    # Auditors review generated evidence, including unpublished releases.
    # This does not grant export-generation or release-management rights.
    if is_admin(user) or "auditor" in user_roles(user):
        return True

    roles = user_roles(user)
    product = release.product

    if "data_provider" in roles and product.data_owner_id == user.pk:
        return True

    # No general internal-data grant is assumed.
    # Analyst and other authorized readers can see
    # published PUBLIC data.
    if (
        release.status == "PUBLISHED"
        and product.sensitivity_classification == "PUBLIC"
        and roles.intersection(
            {
                "analyst",
                "data_provider",
                "data_steward",
            }
        )
    ):
        return True

    return False


def can_manage_release(user, release):
    if not user.is_authenticated:
        return False

    if is_admin(user):
        return True

    return (
        "data_provider" in user_roles(user) and release.product.data_owner_id == user.pk
    )


def require_view_release(user, release):
    if not can_view_release(user, release):
        raise PermissionDenied(
            "You are not authorized to access this data product release."
        )


def require_manage_release(user, release):
    if not can_manage_release(user, release):
        raise PermissionDenied(
            "You are not authorized to generate or "
            "validate FHIR resources for this release."
        )
