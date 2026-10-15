from django.http import JsonResponse


def health_check(request):
    return JsonResponse({
        "statusCode": 200,
        "message": "Service is healthy.",
        "data": {
            "status": "ok",
            "service": "uhc-data-mediator-api",
        },
    })

