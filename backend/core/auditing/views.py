import uuid

from core.auditing.models import AuditEvent
from core.auditing.permissions import IsAuditor
from core.responses import api_response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def audit_event_data(event):
    return {
        "id": str(event.id),
        "actorId": (str(event.actor_id) if event.actor_id else None),
        "actorIdentifier": event.actor_identifier,
        "actorRole": event.actor_role,
        "organization": event.organization,
        "action": event.action,
        "resourceType": event.resource_type,
        "resourceId": event.resource_id,
        "outcome": event.outcome,
        "httpMethod": event.http_method,
        "httpPath": event.http_path,
        "httpStatus": event.http_status,
        "correlationId": str(event.correlation_id),
        "ipAddress": event.ip_address,
        "details": event.details,
        "createdAt": event.created_at.isoformat(),
    }


class AuditEventListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAuditor,
    ]

    def get(self, request):
        queryset = AuditEvent.objects.all()

        action = request.query_params.get("action")
        outcome = request.query_params.get("outcome")
        actor_id = request.query_params.get("actor_id")
        resource_type = request.query_params.get("resource_type")
        resource_id = request.query_params.get("resource_id")
        correlation_id = request.query_params.get("correlation_id")

        if action:
            queryset = queryset.filter(action=action)

        if outcome:
            if outcome not in AuditEvent.Outcome.values:
                return api_response(
                    "Invalid audit outcome.",
                    status_code=400,
                )

            queryset = queryset.filter(outcome=outcome)

        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)

        try:
            if actor_id:
                queryset = queryset.filter(actor_id=uuid.UUID(actor_id))

            if correlation_id:
                queryset = queryset.filter(correlation_id=uuid.UUID(correlation_id))

            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))

        except (TypeError, ValueError, AttributeError):
            return api_response(
                "Invalid query parameters.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1 or not 1 <= page_size <= 100:
            return api_response(
                "Page and page_size are out of range.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        queryset = queryset.order_by("-created_at", "-id")

        total = queryset.count()
        total_pages = max(
            1,
            (total + page_size - 1) // page_size,
        )

        offset = (page - 1) * page_size

        events = queryset[offset : offset + page_size]

        return api_response(
            "Audit events retrieved successfully.",
            data={
                "items": [audit_event_data(event) for event in events],
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "totalItems": total,
                    "totalPages": total_pages,
                    "hasNext": page < total_pages,
                    "hasPrevious": page > 1,
                },
            },
        )
