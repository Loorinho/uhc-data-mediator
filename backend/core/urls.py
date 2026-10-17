
from django.urls import include, path

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

]
