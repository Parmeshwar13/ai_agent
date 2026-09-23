# Orbit architecture

Orbit is a multi-tenant platform that will create and develop independent software products. It is not a workforce system, clinic system, store, or any other end-user application.

```text
ORBIT PLATFORM
    ├── Identity and tenancy        Phase 1
    ├── Product intelligence        later
    ├── Agent orchestration         later
    ├── Sandbox                     later
    ├── Git                         later
    └── UI
            │
            ▼
     GENERATED PROJECT
```

A generated project is a separate repository and a separate product. Adding a new kind of product must not require a change to Orbit's domain model beyond what the product description already carries.

## Phase 1 boundary

Phase 1 implements the registry:

- Users authenticate with email and a rotating JWT.
- An organization is the tenant.
- A project belongs to exactly one organization and starts at `created`.
- Authorization is enforced in querysets and object lookups. A miss across tenants is a 404, so existence does not leak.
- Project status has one writer, `transition_project`. Every transition is closed. Clients cannot mark a project complete.

Later phases plug into that writer. They must not add a second way to set `Project.status`.

## Rules that later phases inherit

1. Do not hardcode a generated application.
2. Do not assume every generated project uses Django.
3. Keep the LLM provider behind an abstraction. Phase 1 has no provider.
4. Never execute agent commands on the Orbit host. Tools will run in a sandbox.
5. Never modify `main` directly.
6. Never claim a test passed unless the command ran and passed.
7. Never allow an infinite agent loop. Retry and resource limits end in `human_review_required`.
8. Record every agent action. Phase 1 records project and organization events.
9. Do not overwrite project knowledge without a version. The wiki is not built yet; do not fake it.
10. Keep secrets out of generated repositories and out of this repository.

## Request path

```text
Browser
  └── Vite (or nginx)  /api  →  Django
        ├── accounts          identity
        ├── organizations     tenant boundary
        └── projects          registry and lifecycle
```

The browser calls relative `/api` URLs. It does not call `localhost` for the API, so a hosted preview and a local dev server behave the same way.

## What is intentionally absent

Discovery, wiki documents, architecture decisions, task graphs, GitHub, the coding agent, the sandbox, test execution, pull requests, and websockets are mapped in the navigation and in `docs/roadmap.md`. Their packages exist as boundaries, not as implementations. Do not import them as if they run.
