from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class OrganizationRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class OrganizationEventType(models.TextChoices):
    CREATED = "organization_created", "Organization created"
    UPDATED = "organization_updated", "Organization updated"
    MEMBER_ADDED = "member_added", "Member added"
    MEMBER_REMOVED = "member_removed", "Member removed"
    MEMBER_ROLE_CHANGED = "member_role_changed", "Member role changed"


class Organization(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=48, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organizations_created",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.name


class OrganizationMember(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=16, choices=OrganizationRole.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_member",
            ),
            models.CheckConstraint(
                check=models.Q(role__in=OrganizationRole.values),
                name="organization_member_role_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "organization"]),
            models.Index(fields=["organization", "role"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.user_id} @ {self.organization_id} ({self.role})"


class OrganizationEvent(TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization_events",
    )
    event_type = models.CharField(max_length=40, choices=OrganizationEventType.choices)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(event_type__in=OrganizationEventType.values),
                name="organization_event_type_valid",
            ),
        ]
