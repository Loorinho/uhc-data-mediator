from django.urls import path

from core.ingestion.views.acquisition_detail import AcquisitionDetailAPIView
from core.ingestion.views.acquisition import AcquisitionView

urlpatterns = [
    path("", AcquisitionView.as_view(), name="acquisition-list-create"),
    path(
            "<uuid:acquisition_id>/",
            AcquisitionDetailAPIView.as_view(),
            name="acquisition-detail",
        ),
]