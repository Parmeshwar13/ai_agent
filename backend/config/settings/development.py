"""Local development settings. SQLite is the default database."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Preview hosts and local Vite are not a fixed origin list.
CORS_ALLOW_ALL_ORIGINS = True
