# Orbit

Orbit is a multi-tenant platform for autonomous software development. It does not ship a workforce app, a clinic app, or a store. It is the system that will eventually create those products as separate projects.

**This repository is Phase 1.** A person can create an account, an organization, and a project, and Orbit will hold that project at the start of its lifecycle. Discovery, architecture, task planning, GitHub, the coding agent, the sandbox, tests, and pull requests are not implemented. The navigation shows where they will live. It does not pretend they have run.

```text
User
  └── Organization          tenant boundary
        └── Project         independent product, status = created
              └── Events    append-only history
```

## What works

- Email registration and login, with rotating JWT access tokens and blacklistable refresh tokens.
- An organization is created with the account. Owners and admins manage members. The last owner cannot be removed.
- Projects store a product description, a human key, and an explicit lifecycle.
- Cross-organization access returns 404, including by id. Hiding a link in the UI is not the control.
- Archive keeps history. Permanent delete requires confirmation.
- Status cannot be patched to `completed`, or to anything else. `transition_project` is the only writer, and Phase 1 allows no transitions.

## What does not work yet

Do not expect Orbit to understand a product description, choose a stack, create a GitHub repository, write code, run tests, or open a pull request. Those are later phases. See [docs/roadmap.md](docs/roadmap.md).

Three different product ideas can be registered from the new-project screen. Registering them does not build them.

## Stack

| Piece | Choice |
| --- | --- |
| API | Django 5, Django REST Framework |
| Database | PostgreSQL in compose; SQLite if `DATABASE_URL` is unset |
| Auth | `djangorestframework-simplejwt` |
| Frontend | React, TypeScript, Vite |
| Reserved | Redis is in compose for later workers. Phase 1 does not require it. |

The LLM provider, Docker sandbox, and GitHub client are not wired. When they are, the provider stays behind an interface, and agent commands run in a sandbox rather than on this host.

## Run it locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_demo   # DEBUG only
../.venv/bin/python manage.py runserver 0.0.0.0:8000
```

In another shell:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL. The app calls `/api`, and Vite proxies that to Django, so the browser never needs to know the API host.

Demo account, after `seed_demo`:

```text
demo@orbit.dev
orbit-demo-pass
```

That password is a local demo credential. `seed_demo` refuses to run when `DEBUG` is false. Production settings refuse the default secret and require `DATABASE_URL`.

Copy [.env.example](.env.example) if you want PostgreSQL or a custom secret. Without `DATABASE_URL`, development uses `backend/db.sqlite3`.

API docs: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/).

## Tests

```bash
.venv/bin/python -m pytest
```

The suite covers registration, token logout, organization roles, the last-owner guard, and the tenant boundary: another organization's project is invisible in lists, search, direct fetch, member routes, and create attempts.

## Docker

```bash
docker compose up --build
```

The frontend is served on port `8080` and proxies `/api` to the API. PostgreSQL and Redis start with it. This compose file uses development settings so a local stack can boot. Do not treat those settings as production.

## Layout

```text
backend/          Django project: accounts, organizations, projects
frontend/         React dashboard
agent/            Reserved tool-calling packages. Empty of behavior.
infrastructure/   Dockerfiles and nginx
docs/             Architecture, API, phase notes, roadmap
tests/            Platform tests
```

Reserved backend packages (`wiki`, `sandbox`, `git`, and the others) are not in `INSTALLED_APPS`. They mark the boundary for later phases.

## Authorization, short version

A user who is not a member of an organization cannot read that organization's projects. Inside an organization, every member can read. Editing a project requires an organization owner or admin, or a project owner or maintainer. Project members must already belong to the organization.

Details: [docs/phase-1.md](docs/phase-1.md) and [docs/api.md](docs/api.md).

## Engineering rules already in force

- Generated products stay independent of Orbit's code.
- No generated application is hardcoded.
- No stack is assumed for a future generated project.
- Project knowledge is not overwritten; Phase 1 only appends events.
- Secrets belong in the environment, not in a repository.
- An agent, when it exists, will not run on this host and will not commit to `main`.
