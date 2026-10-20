from django.urls import include, path

from core.ingestion.views.exploration import (
    DistrictDetailView,
    DistrictListView,
    PopulationDetailView,
    PopulationListView,
)

from .authentication.views import RoleListCreateView, UserListView
from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    # Feature: authentication & authorization
    path("auth/", include("core.authentication.urls")),
    # Users & roles
    path("users/", UserListView.as_view(), name="user-list"),
    path("roles/", RoleListCreateView.as_view(), name="role-list-create"),
    # Data Acquisiton
    path("acquisition/", include("core.ingestion.urls")),
    # Interoperability
    path("interoperability/", include("core.interoperability.urls")),
    path("districts/", DistrictListView.as_view(), name="district-list"),
    path("districts/<uuid:id>/", DistrictDetailView.as_view(), name="district-detail"),
    path("population/", PopulationListView.as_view(), name="population-list"),
    path(
        "population/<uuid:id>/",
        PopulationDetailView.as_view(),
        name="population-detail",
    ),
    path("", include("core.governance.urls")),
    path(
        "",
        include("core.interoperability.fhir_urls"),
    ),
    # Audit
    path(
        "audit-events/",
        include("core.auditing.urls"),
    ),
]
