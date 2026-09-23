# Orbit API — Phase 1

Base path: `/api`. Authenticated routes expect `Authorization: Bearer <access>`.

Interactive schema: `/api/docs/`.

## Auth

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register/` | Public | Create user, workspace, and tokens |
| POST | `/auth/login/` | Public | Email and password |
| POST | `/auth/refresh/` | Public | Rotate refresh token |
| POST | `/auth/logout/` | User | Blacklist refresh token |
| GET, PATCH | `/auth/me/` | User | Profile and organization list |
| POST | `/auth/password/` | User | Change password |

Emails are stored and matched case-insensitively.

## Organizations

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST | `/organizations/` | List memberships, create |
| GET, PATCH, DELETE | `/organizations/{id}/` | Read, update, delete |
| GET, POST | `/organizations/{id}/members/` | List, add by email |
| PATCH, DELETE | `/organizations/{id}/members/{member_id}/` | Change role, remove |
| GET | `/organizations/{id}/events/` | Recent tenant history |

Delete requires `{ "confirm_slug": "<slug>" }`. Unknown organizations return 404 for non-members.

Adding a member fails if that email has no Orbit account. This release does not send mail.

## Projects

| Method | Path | Purpose |
| --- | --- | --- |
| GET, POST | `/projects/` | List visible projects, create |
| GET | `/projects/lifecycle/` | State machine definition |
| GET, PATCH, DELETE | `/projects/{id}/` | Read, edit details, permanent delete |
| GET | `/projects/{id}/lifecycle/` | Lifecycle for this project |
| POST | `/projects/{id}/archive/` | Hide without deleting history |
| POST | `/projects/{id}/unarchive/` | Restore |
| GET, POST | `/projects/{id}/members/` | Explicit project roles |
| PATCH, DELETE | `/projects/{id}/members/{member_id}/` | Change or remove |
| GET | `/projects/{id}/events/` | Append-only project history |

List filters: `organization`, `status`, `search`, `include_archived`, `page`, `page_size`.

`status` and `organization` are rejected on PATCH. Status changes go through `projects.services.transition_project`, which Phase 1 always refuses.

Permanent delete requires `?confirm=true`. Prefer archive.

## Health

`GET /api/health/` returns `{ "status": "ok", "service": "orbit", "version": "0.1.0", "phase": 1 }` after a database check.
