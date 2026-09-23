"""Fast, isolated settings for the Orbit test suite."""

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DEMO_SEED = False

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = ()  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/minute",
    "user": "1000/minute",
    "auth": "1000/minute",
}
