from django.urls import path

from core.interoperability.api_exploration import (
    CanonicalObservationDetailView,
    CanonicalObservationListView,
    MeasureDetailView,
    MeasureListView,
    MeasureMappingListView,
)
from core.interoperability.views import (
    TriggerTransformationAPIView,
)

urlpatterns = [
    path(
        "acquisition/<uuid:acquisition_id>/transform/",
        TriggerTransformationAPIView.as_view(),
        name="trigger-canonical-transformation",
    ),
    path("canonical/measures/", MeasureListView.as_view(), name="canonical-measures"),
    path(
        "canonical/measures/<str:code>/",
        MeasureDetailView.as_view(),
        name="canonical-measure-detail",
    ),
    path(
        "canonical/measure-mappings/",
        MeasureMappingListView.as_view(),
        name="canonical-mappings",
    ),
    path(
        "canonical/observations/",
        CanonicalObservationListView.as_view(),
        name="canonical-observations",
    ),
    path(
        "canonical/observations/<uuid:id>/",
        CanonicalObservationDetailView.as_view(),
        name="canonical-observation-detail",
    ),
]
