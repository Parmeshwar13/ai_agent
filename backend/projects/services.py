"""Project registry services.

Status is not a free-form field. transition_project is the only writer, and
Phase 1 allows no transitions. Callers cannot mark a project complete.
"""

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from core.exceptions import InvalidLifecycleTransition
from core.text import unique_key, unique_slug
from organizations.models import OrganizationMember
from projects.lifecycle import can_transition
from projects.models import (
    Project,
    ProjectEvent,
    ProjectEventType,
    ProjectMember,
    ProjectRole,
    ProjectStatus,
)


def _record(project, actor, event_type, message, metadata=None):
    return ProjectEvent.objects.create(
        project=project,
        actor=actor,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


@transaction.atomic
def create_project(*, organization, creator, name, product_description, summary=""):
    slug = unique_slug(
        name,
        lambda candidate: Project.objects.filter(organization=organization, slug=candidate).exists(),
        fallback="project",
    )
    key = unique_key(
        name,
        lambda candidate: Project.objects.filter(organization=organization, key=candidate).exists(),
    )
    project = Project.objects.create(
        organization=organization,
        name=name.strip(),
        slug=slug,
        key=key,
        summary=(summary or "").strip(),
        product_description=product_description.strip(),
        status=ProjectStatus.CREATED,
        created_by=creator,
    )
    ProjectMember.objects.create(project=project, user=creator, role=ProjectRole.OWNER)
    _record(
        project,
        creator,
        ProjectEventType.PROJECT_CREATED,
        f"{creator.full_name} created {project.name}.",
        {"status": project.status, "key": project.key},
    )
    return project


@transaction.atomic
def update_project(*, project, actor, name=None, summary=None, product_description=None):
    changed = []
    if name is not None and name.strip() and name.strip() != project.name:
        project.name = name.strip()
        changed.append("name")
    if summary is not None and summary != project.summary:
        project.summary = summary.strip()
        changed.append("summary")
    if product_description is not None and product_description.strip() != project.product_description:
        project.product_description = product_description.strip()
        changed.append("product_description")
    if not changed:
        return project
    project.save(update_fields=[*changed, "updated_at"])
    _record(
        project,
        actor,
        ProjectEventType.PROJECT_UPDATED,
        f"{actor.full_name} updated {', '.join(changed).replace('_', ' ')}.",
        {"fields": changed},
    )
    return project


@transaction.atomic
def transition_project(*, project, actor, to_status, reason=""):
    """Single status writer. Refuses anything Phase 1 has not opened."""

    if to_status not in ProjectStatus.values:
        raise InvalidLifecycleTransition("Unknown project status.")
    if not can_transition(project.status, to_status):
        raise InvalidLifecycleTransition(
            "That lifecycle transition is not allowed in this release. "
            "Orbit will not mark discovery, implementation, tests, or completion "
            "as done until those engines exist and have actually run."
        )
    previous = project.status
    project.status = to_status
    project.save(update_fields=["status", "updated_at"])
    _record(
        project,
        actor,
        ProjectEventType.STATUS_CHANGED,
        f"{actor.full_name} moved the project from {previous} to {to_status}.",
        {"from": previous, "to": to_status, "reason": reason},
    )
    return project


@transaction.atomic
def set_archived(*, project, actor, archived: bool):
    if archived and project.archived_at is None:
        project.archived_at = timezone.now()
        project.save(update_fields=["archived_at", "updated_at"])
        _record(
            project,
            actor,
            ProjectEventType.PROJECT_ARCHIVED,
            f"{actor.full_name} archived the project.",
        )
    elif not archived and project.archived_at is not None:
        project.archived_at = None
        project.save(update_fields=["archived_at", "updated_at"])
        _record(
            project,
            actor,
            ProjectEventType.PROJECT_UNARCHIVED,
            f"{actor.full_name} restored the project.",
        )
    return project


@transaction.atomic
def add_project_member(*, project, actor, email, role):
    normalized = User.objects.normalize_email(email)
    user = User.objects.filter(email=normalized).first()
    if user is None:
        raise LookupError(normalized)
    if not OrganizationMember.objects.filter(organization=project.organization, user=user).exists():
        raise PermissionError("not_in_organization")
    if ProjectMember.objects.filter(project=project, user=user).exists():
        raise ValueError("already_member")
    member = ProjectMember.objects.create(project=project, user=user, role=role)
    _record(
        project,
        actor,
        ProjectEventType.MEMBER_ADDED,
        f"{actor.full_name} added {user.full_name} as {role}.",
        {"user_id": str(user.id), "role": role},
    )
    return member


@transaction.atomic
def change_project_member_role(*, project, actor, member, role):
    if member.role == ProjectRole.OWNER and role != ProjectRole.OWNER:
        other_owners = ProjectMember.objects.filter(project=project, role=ProjectRole.OWNER).exclude(pk=member.pk)
        if not other_owners.exists():
            raise PermissionError("last_owner")
    if member.role == role:
        return member
    previous = member.role
    member.role = role
    member.save(update_fields=["role", "updated_at"])
    _record(
        project,
        actor,
        ProjectEventType.MEMBER_ROLE_CHANGED,
        f"{actor.full_name} changed {member.user.full_name} from {previous} to {role}.",
        {"user_id": str(member.user_id), "from": previous, "to": role},
    )
    return member


@transaction.atomic
def remove_project_member(*, project, actor, member):
    if member.role == ProjectRole.OWNER:
        other_owners = ProjectMember.objects.filter(project=project, role=ProjectRole.OWNER).exclude(pk=member.pk)
        if not other_owners.exists():
            raise PermissionError("last_owner")
    user = member.user
    member.delete()
    _record(
        project,
        actor,
        ProjectEventType.MEMBER_REMOVED,
        f"{actor.full_name} removed {user.full_name} from the project.",
        {"user_id": str(user.id)},
    )
