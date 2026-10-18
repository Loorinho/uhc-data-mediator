from django.urls import path

from backend.core.ingestion.views.exploration import AcquisitionObservationsView
from core.ingestion.views.acquisition import AcquisitionView
from core.ingestion.views.acquisition_detail import AcquisitionDetailAPIView

urlpatterns = [
    path("", AcquisitionView.as_view(), name="acquisition-list-create"),
    path(
        "<uuid:acquisition_id>/",
        AcquisitionDetailAPIView.as_view(),
        name="acquisition-detail",
    ),
    path(
        "<uuid:acquisition_id>/observations/",
        AcquisitionObservationsView.as_view(),
        name="acquisition-observations",
    ),
]
