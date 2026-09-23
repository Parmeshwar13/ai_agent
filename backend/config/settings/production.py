"""Production settings. Refuses insecure defaults."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

if SECRET_KEY in {  # noqa: F405
    "",
    "orbit-dev-insecure-secret-key",
    "orbit-dev-insecure-secret-key-32b",
    "change-me-in-production",
}:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set to a unique value in production.")

if not env("DATABASE_URL", default=""):  # noqa: F405
    raise ImproperlyConfigured("DATABASE_URL must point at PostgreSQL in production.")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
