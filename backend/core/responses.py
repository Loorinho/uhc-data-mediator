from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_response(message: str, data: Any = None, status_code: int = 200) -> Response:
    """Standard success envelope shared by all API endpoints.

    Shape: { "statusCode": int, "message": str, "data": Any }
    """
    return Response(
        {
            "statusCode": status_code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def custom_exception_handler(exc, context):
    """Wrap all DRF errors in the same envelope shape.

    Shape: { "statusCode": int, "message": str, "data": errors }
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    message = "An error occurred."
    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail is not None:
            message = str(detail)
        elif response.data:
            # Surface the first field/non-field error message
            first_errors = next(iter(response.data.values()))
            if isinstance(first_errors, list) and first_errors:
                message = str(first_errors[0])
            else:
                message = str(first_errors)
    elif isinstance(response.data, list) and response.data:
        message = str(response.data[0])

    response.data = {
        "statusCode": response.status_code,
        "message": message,
        "data": None,
    }
    return response
