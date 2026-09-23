from django.db import transaction

from accounts.models import User
from core.text import unique_slug
from organizations.access import assert_can_assign_role, assert_not_last_owner
from organizations.models import (
    Organization,
    OrganizationEvent,
    OrganizationEventType,
    OrganizationMember,
    OrganizationRole,
)


def _record(organization, actor, event_type, message, metadata=None):
    return OrganizationEvent.objects.create(
        organization=organization,
        actor=actor,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


@transaction.atomic
def create_organization(*, owner, name, description=""):
    slug = unique_slug(
        name,
        lambda candidate: Organization.objects.filter(slug=candidate).exists(),
        fallback="workspace",
    )
    organization = Organization.objects.create(
        name=name.strip(),
        slug=slug,
        description=(description or "").strip(),
        created_by=owner,
    )
    OrganizationMember.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationRole.OWNER,
    )
    _record(
        organization,
        owner,
        OrganizationEventType.CREATED,
        f"{owner.full_name} created the organization.",
        {"name": organization.name},
    )
    return organization


@transaction.atomic
def update_organization(*, organization, actor, name=None, description=None):
    changed = []
    if name is not None and name.strip() and name.strip() != organization.name:
        organization.name = name.strip()
        changed.append("name")
    if description is not None and description != organization.description:
        organization.description = description
        changed.append("description")
    if not changed:
        return organization
    organization.save(update_fields=[*changed, "updated_at"])
    _record(
        organization,
        actor,
        OrganizationEventType.UPDATED,
        f"{actor.full_name} updated the organization.",
        {"fields": changed},
    )
    return organization


@transaction.atomic
def add_member(*, organization, actor_membership, email, role):
    assert_can_assign_role(actor_membership, role)
    normalized = User.objects.normalize_email(email)
    user = User.objects.filter(email=normalized).first()
    if user is None:
        raise LookupError(normalized)
    if OrganizationMember.objects.filter(organization=organization, user=user).exists():
        raise ValueError("already_member")
    member = OrganizationMember.objects.create(organization=organization, user=user, role=role)
    _record(
        organization,
        actor_membership.user,
        OrganizationEventType.MEMBER_ADDED,
        f"{actor_membership.user.full_name} added {user.full_name} as {role}.",
        {"user_id": str(user.id), "role": role},
    )
    return member


@transaction.atomic
def change_member_role(*, organization, actor_membership, member, role):
    assert_can_assign_role(actor_membership, role)
    if member.role == OrganizationRole.OWNER and actor_membership.role != OrganizationRole.OWNER:
        raise PermissionError("owner_protected")
    assert_not_last_owner(organization, member, next_role=role)
    if member.role == role:
        return member
    previous = member.role
    member.role = role
    member.save(update_fields=["role", "updated_at"])
    _record(
        organization,
        actor_membership.user,
        OrganizationEventType.MEMBER_ROLE_CHANGED,
        f"{actor_membership.user.full_name} changed {member.user.full_name} from {previous} to {role}.",
        {"user_id": str(member.user_id), "from": previous, "to": role},
    )
    return member


@transaction.atomic
def remove_member(*, organization, actor_membership, member):
    if member.role == OrganizationRole.OWNER and actor_membership.role != OrganizationRole.OWNER:
        raise PermissionError("owner_protected")
    if member.user_id != actor_membership.user_id and actor_membership.role == OrganizationRole.MEMBER:
        raise PermissionError("forbidden")
    assert_not_last_owner(organization, member, next_role=None)
    user = member.user
    member.delete()
    _record(
        organization,
        actor_membership.user,
        OrganizationEventType.MEMBER_REMOVED,
        f"{actor_membership.user.full_name} removed {user.full_name}.",
        {"user_id": str(user.id)},
    )


@transaction.atomic
def delete_organization(*, organization, actor):
    name = organization.name
    organization.delete()
    return name
