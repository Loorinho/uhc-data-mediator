import ipaddress
import logging
import uuid

from core.auditing.models import AuditEvent
from django.db import transaction

logger = logging.getLogger(__name__)


def get_role(user):
    if user is None or not user.is_authenticated:
        return ""

    role = getattr(user, "role", None)

    if isinstance(role, str):
        return role

    if role is not None and hasattr(role, "name"):
        return str(role.name)

    group = user.groups.order_by("name").first()
    return group.name if group else ""


def get_organization(user):
    if user is None or not user.is_authenticated:
        return ""

    organization = getattr(user, "organization", None)

    if organization is None:
        return ""

    return str(getattr(organization, "name", organization))[:255]


def get_ip_address(request):
    if request is None:
        return None

    # REMOTE_ADDR is the directly connected peer.
    # Only interpret forwarded headers when your
    # reverse proxy is explicitly trusted.
    value = request.META.get("REMOTE_ADDR", "")

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def get_request_correlation_id(request):
    if request is None:
        return uuid.uuid4()

    value = getattr(request, "correlation_id", None)

    if value:
        return uuid.UUID(str(value))

    return uuid.uuid4()


def record_audit_event(
    *,
    action,
    outcome,
    request=None,
    actor=None,
    resource_type="",
    resource_id="",
    correlation_id=None,
    details=None,
    http_status=None,
):
    """
    Persist one security or processing audit event.

    If request is provided, resolve actor, request
    metadata, and correlation ID automatically.

    Pass an explicit correlation_id when recording
    an event from a background worker.

    Never pass credentials or raw datasets in details.
    """
    if actor is None and request is not None:
        actor = getattr(request, "user", None)

    if actor is not None and not actor.is_authenticated:
        actor = None

    if correlation_id is None:
        correlation_id = get_request_correlation_id(request)

    correlation_id = uuid.UUID(str(correlation_id))

    identifier = ""

    if actor is not None:
        identifier = str(
            getattr(actor, "email", "") or getattr(actor, "username", "") or actor.pk
        )[:255]

    return AuditEvent.objects.create(
        actor=actor,
        actor_identifier=identifier,
        actor_role=get_role(actor),
        organization=get_organization(actor),
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id or ""),
        outcome=outcome,
        http_method=(request.method if request is not None else ""),
        http_path=(request.path[:1000] if request is not None else ""),
        http_status=http_status,
        correlation_id=correlation_id,
        ip_address=get_ip_address(request),
        details=details or {},
    )


def record_after_commit(**kwargs):
    """
    Use this for business events that should be
    recorded only after a DB transaction commits.

    If the operation rolls back, its success event
    must not be written.
    """
    transaction.on_commit(lambda: record_audit_event(**kwargs))
