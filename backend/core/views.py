from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config import __phase__, __version__


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    connection.ensure_connection()
    return Response(
        {
            "status": "ok",
            "service": "orbit",
            "version": __version__,
            "phase": __phase__,
        }
    )
