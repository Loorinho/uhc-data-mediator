from django.urls import path

from .views import AcquisitionView

urlpatterns = [
    path("", AcquisitionView.as_view(), name="acquisition"),
]
