from core.auditing.views import AuditEventListAPIView
from django.urls import path

urlpatterns = [
    path(
        "",
        AuditEventListAPIView.as_view(),
        name="audit-event-list",
    ),
]
