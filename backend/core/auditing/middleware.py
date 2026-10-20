import logging
import uuid

from core.auditing.models import AuditEvent
from core.auditing.services import record_audit_event

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """
    Audit security-relevant HTTP access.

    Place after Django AuthenticationMiddleware.

    Background-worker outcomes must be recorded
    separately in their processing services.
    """

    # Routes handled specially, or intentionally
    # excluded to prevent audit-log read recursion.
    EXCLUDED_PREFIXES = (
        "/api/v1/audit-events/",
        "/admin/",
        "/static/",
        "/media/",
    )

    # Health checks and other non-sensitive probes.
    EXCLUDED_PATHS = ("/api/v1/health/",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.correlation_id = uuid.uuid4()

        response = self.get_response(request)

        response["X-Correlation-ID"] = str(request.correlation_id)

        self.record_request(request, response)

        return response

    def record_request(self, request, response):
        path = request.path
        method = request.method
        status_code = response.status_code

        if path in self.EXCLUDED_PATHS:
            return

        if path.startswith(self.EXCLUDED_PREFIXES):
            return

        # Limit automatic recording to our API.
        if not path.startswith("/api/v1/"):
            return

        if status_code in (401, 403):
            action = "ACCESS_DENIED"
            outcome = AuditEvent.Outcome.DENIED

        elif status_code >= 500:
            action = "API_REQUEST_FAILED"
            outcome = AuditEvent.Outcome.FAILURE

        elif path.startswith("/api/v1/auth/"):
            action = "AUTH_REQUEST"
            outcome = (
                AuditEvent.Outcome.SUCCESS
                if status_code < 400
                else AuditEvent.Outcome.FAILURE
            )

        elif method in ("GET", "HEAD"):
            # Read-only access to API resources.
            # Skip OPTIONS and HEAD to avoid noise.
            if method == "HEAD":
                return

            action = "DATA_VIEWED"
            outcome = (
                AuditEvent.Outcome.SUCCESS
                if status_code < 400
                else AuditEvent.Outcome.FAILURE
            )

        elif method in ("POST", "PUT", "PATCH", "DELETE"):
            action = "API_MUTATION_REQUEST"
            outcome = (
                AuditEvent.Outcome.SUCCESS
                if status_code < 400
                else AuditEvent.Outcome.FAILURE
            )

        else:
            return

        try:
            record_audit_event(
                action=action,
                outcome=outcome,
                request=request,
                resource_type="HTTP_ENDPOINT",
                resource_id=path,
                http_status=status_code,
                details={
                    "method": method,
                },
            )
        except Exception:
            logger.exception(
                "CRITICAL: Audit write failed for %s %s",
                method,
                path,
            )
            # Preserve existing API behavior, but
            # surface the audit failure to operations
            # via error logs and monitoring.
