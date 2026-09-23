"""API exception helpers. Tenant misses are 404s so existence does not leak."""

from rest_framework.exceptions import APIException, NotFound
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = 409
    default_detail = "The request conflicts with the current state."
    default_code = "conflict"


class InvalidLifecycleTransition(Conflict):
    default_detail = "That lifecycle transition is not allowed."
    default_code = "invalid_lifecycle_transition"


def orbit_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    code = getattr(exc, "default_code", "error")
    if hasattr(exc, "get_codes"):
        try:
            code = exc.get_codes()
        except Exception:
            code = getattr(exc, "default_code", "error")
    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        response.data = {"detail": detail["detail"], "code": code}
    elif isinstance(detail, list):
        response.data = {"detail": detail, "code": code}
    else:
        response.data = {"errors": detail, "code": "validation_error"}
    return response


def not_found(detail: str = "Not found.") -> NotFound:
    return NotFound(detail)
