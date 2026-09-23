"""Explicit project lifecycle.

Phase 1 records projects at CREATED and rejects every other transition.
Later phases own the transitions that imply discovery, planning, or an
agent run. Nothing in this module executes tools, git, or a sandbox.
"""

from projects.models import ProjectStatus

HAPPY_PATH = [
    ProjectStatus.CREATED,
    ProjectStatus.DISCOVERY,
    ProjectStatus.SPECIFICATION,
    ProjectStatus.ARCHITECTURE,
    ProjectStatus.PLANNING,
    ProjectStatus.READY,
    ProjectStatus.IMPLEMENTING,
    ProjectStatus.TESTING,
    ProjectStatus.REVIEWING,
    ProjectStatus.PR_CREATED,
    ProjectStatus.COMPLETED,
]

FAILURE_PATH = [
    ProjectStatus.TESTING,
    ProjectStatus.FAILED,
    ProjectStatus.ANALYZING_FAILURE,
    ProjectStatus.FIXING,
    ProjectStatus.TESTING,
]

TERMINAL = {
    ProjectStatus.COMPLETED,
    ProjectStatus.HUMAN_REVIEW_REQUIRED,
}

# Stages that would claim Orbit generated artifacts or ran an agent.
# They stay closed until the owning phase exists.
AGENT_OWNED = {
    ProjectStatus.DISCOVERY,
    ProjectStatus.SPECIFICATION,
    ProjectStatus.ARCHITECTURE,
    ProjectStatus.PLANNING,
    ProjectStatus.READY,
    ProjectStatus.IMPLEMENTING,
    ProjectStatus.TESTING,
    ProjectStatus.REVIEWING,
    ProjectStatus.PR_CREATED,
    ProjectStatus.COMPLETED,
    ProjectStatus.FAILED,
    ProjectStatus.ANALYZING_FAILURE,
    ProjectStatus.FIXING,
    ProjectStatus.HUMAN_REVIEW_REQUIRED,
}

# Phase 1: creation is the only writer of status. The map is the extension
# point for later phases. Do not add transitions here to simulate progress.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {status: set() for status in ProjectStatus.values}

STATUS_DESCRIPTIONS = {
    ProjectStatus.CREATED: "The product idea is registered. Discovery has not started.",
    ProjectStatus.DISCOVERY: "Orbit is identifying personas, modules, and open questions.",
    ProjectStatus.SPECIFICATION: "Requirements are being written into the product wiki.",
    ProjectStatus.ARCHITECTURE: "Architecture decisions are being recorded.",
    ProjectStatus.PLANNING: "Work is being broken into a dependency graph of tasks.",
    ProjectStatus.READY: "The plan is approved and a task can be picked up.",
    ProjectStatus.IMPLEMENTING: "A coding agent is changing the project repository.",
    ProjectStatus.TESTING: "Tests, lint, and build checks are running in a sandbox.",
    ProjectStatus.REVIEWING: "Changes are being prepared for review.",
    ProjectStatus.PR_CREATED: "A pull request exists. Main has not been modified directly.",
    ProjectStatus.COMPLETED: "The current task cycle is complete and project knowledge is updated.",
    ProjectStatus.FAILED: "A check failed. The run has not been abandoned.",
    ProjectStatus.ANALYZING_FAILURE: "Failure output is being analyzed. Tests are not assumed to pass.",
    ProjectStatus.FIXING: "A bounded repair is being applied.",
    ProjectStatus.HUMAN_REVIEW_REQUIRED: "Retry or resource limits were reached. Autonomy has stopped.",
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def lifecycle_payload(current: str) -> dict:
    def entry(status):
        return {
            "value": status.value,
            "label": status.label,
            "description": STATUS_DESCRIPTIONS[status],
        }

    return {
        "current": current,
        "automation": "none",
        "phase": 1,
        "note": (
            "Status changes are closed in this release. "
            "Discovery, planning, and agent execution will advance the lifecycle later. "
            "A project cannot be marked complete by editing its status."
        ),
        "allowed_transitions": sorted(ALLOWED_TRANSITIONS.get(current, set())),
        "happy_path": [entry(status) for status in HAPPY_PATH],
        "failure_path": [entry(status) for status in FAILURE_PATH],
        "terminal": sorted(TERMINAL),
    }
