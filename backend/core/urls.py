
from django.urls import path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "uhc-data-mediator-api",
    })


urlpatterns = [
    path("health/", health_check, name="health-check"),
]
