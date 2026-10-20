from django.urls import path

from core.ingestion.views.acquisition import AcquisitionView
from core.ingestion.views.acquisition_detail import AcquisitionDetailAPIView
from core.ingestion.views.exploration import AcquisitionObservationsView

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
