"""ASGI entrypoint.

WebSocket agent streaming is a later phase. This module is the stable
entrypoint so Channels can be added without moving the project layout.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_asgi_application()
