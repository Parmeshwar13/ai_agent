# Compose

The runnable stack is the repository-root `docker-compose.yml`.

It starts PostgreSQL, Redis, the Django API, and an nginx build of the frontend. Redis is provisioned for later workers. Phase 1 does not connect to it on startup, and the API still runs if Redis is absent when you use SQLite locally.

This compose file uses development settings so a local stack can boot. Production must set `DJANGO_SETTINGS_MODULE=config.settings.production`, a unique `DJANGO_SECRET_KEY`, and `DATABASE_URL`.
