from django.urls import path

from core.interoperability.views import (
    TriggerTransformationAPIView,
)

urlpatterns = [
    path(
        "acquisition/<uuid:acquisition_id>/transform/",
        TriggerTransformationAPIView.as_view(),
        name="trigger-canonical-transformation",
    ),
]
