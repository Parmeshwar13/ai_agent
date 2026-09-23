# Phase 1 — registry

Phase 1 is complete when a person can:

1. Create an account and receive an organization they own.
2. Create additional organizations.
3. Invite an existing Orbit user into an organization by email.
4. Register a project with a natural-language product description.
5. See the project lifecycle, held at Created, with every other transition refused.
6. Archive a project without destroying its event history.
7. Fail to read or modify another organization's projects, including by guessing ids.

Phase 1 does not discover requirements, choose a stack, create a repository, run an agent, execute tests, or open a pull request.

## Lifecycle

```text
CREATED → DISCOVERY → SPECIFICATION → ARCHITECTURE → PLANNING → READY
       → IMPLEMENTING → TESTING → REVIEWING → PR_CREATED → COMPLETED

TESTING → FAILED → ANALYZING_FAILURE → FIXING → TESTING
limit exceeded → HUMAN_REVIEW_REQUIRED
```

The graph is queryable at `GET /api/projects/lifecycle/` and `GET /api/projects/{id}/lifecycle/`. `allowed_transitions` is empty. That is the feature, not a gap: Orbit will not pretend a stage finished.

## Tenancy

| Action | Who |
| --- | --- |
| Read organization and its projects | Any member |
| Update organization, manage members | Owner or admin |
| Grant owner, delete organization | Owner |
| Create a project | Any organization member |
| Edit a project | Organization owner/admin, or project owner/maintainer |
| Manage project members, archive | Organization owner/admin, or project owner |
| Delete a project | Organization owner or project owner, with `confirm=true` |

The last owner of an organization or project cannot be removed.

## Local demo

```bash
cd backend
python manage.py migrate
python manage.py seed_demo
```

Demo email `demo@orbit.dev`, password `orbit-demo-pass`. The command refuses to run when `DEBUG` is false.
