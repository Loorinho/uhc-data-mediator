from django.urls import path

from .views import (
    LoginView,
    MeView,
    RefreshView,
    RegisterView,
    RoleListCreateView,
    UserListView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("users/", UserListView.as_view(), name="auth-users"),
    path("roles/", RoleListCreateView.as_view(), name="auth-roles"),
]
