"""Optional DRF exception handler to enforce the agreed API error envelope."""

from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # Let Django handle unexpected server errors.
    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
    elif isinstance(detail, dict):
        message = "Request validation failed."
    elif isinstance(detail, list):
        message = "Request validation failed."
    else:
        message = str(detail)
    response.data = {
        "statusCode": response.status_code,
        "message": message,
        "data": detail
        if isinstance(detail, (dict, list)) and "detail" not in detail
        else None,
    }
    return response
