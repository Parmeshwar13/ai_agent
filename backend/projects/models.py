from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from organizations.models import Organization


class ProjectStatus(models.TextChoices):
    CREATED = "created", "Created"
    DISCOVERY = "discovery", "Discovery"
    SPECIFICATION = "specification", "Specification"
    ARCHITECTURE = "architecture", "Architecture"
    PLANNING = "planning", "Planning"
    READY = "ready", "Ready"
    IMPLEMENTING = "implementing", "Implementing"
    TESTING = "testing", "Testing"
    REVIEWING = "reviewing", "Reviewing"
    PR_CREATED = "pr_created", "Pull request created"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    ANALYZING_FAILURE = "analyzing_failure", "Analyzing failure"
    FIXING = "fixing", "Fixing"
    HUMAN_REVIEW_REQUIRED = "human_review_required", "Human review required"


class ProjectRole(models.TextChoices):
    OWNER = "owner", "Owner"
    MAINTAINER = "maintainer", "Maintainer"
    VIEWER = "viewer", "Viewer"


class ProjectEventType(models.TextChoices):
    PROJECT_CREATED = "project_created", "Project created"
    PROJECT_UPDATED = "project_updated", "Project updated"
    PROJECT_ARCHIVED = "project_archived", "Project archived"
    PROJECT_UNARCHIVED = "project_unarchived", "Project restored"
    MEMBER_ADDED = "member_added", "Member added"
    MEMBER_REMOVED = "member_removed", "Member removed"
    MEMBER_ROLE_CHANGED = "member_role_changed", "Member role changed"
    STATUS_CHANGED = "status_changed", "Status changed"


class Project(TimeStampedModel):
    """An independent software product owned by one organization.

    Orbit does not assume a stack for this product. The description is the
    input later discovery will read. It is not a generated application.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=48)
    key = models.CharField(max_length=6)
    summary = models.CharField(max_length=280, blank=True)
    product_description = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=ProjectStatus.choices,
        default=ProjectStatus.CREATED,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="projects_created",
    )
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                name="unique_project_slug_per_organization",
            ),
            models.UniqueConstraint(
                fields=["organization", "key"],
                name="unique_project_key_per_organization",
            ),
            models.CheckConstraint(
                check=models.Q(status__in=ProjectStatus.values),
                name="project_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["organization", "archived_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.key} {self.name}"

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None


class ProjectMember(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(max_length=16, choices=ProjectRole.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="unique_project_member"),
            models.CheckConstraint(
                check=models.Q(role__in=ProjectRole.values),
                name="project_member_role_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "project"]),
            models.Index(fields=["project", "role"]),
        ]
        ordering = ["created_at"]


class ProjectEvent(TimeStampedModel):
    """Append-only project history. Rows are not rewritten."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_events",
    )
    event_type = models.CharField(max_length=40, choices=ProjectEventType.choices)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(event_type__in=ProjectEventType.values),
                name="project_event_type_valid",
            ),
        ]
