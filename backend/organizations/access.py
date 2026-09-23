"""Authorization for the organization tenant boundary.

Queries that miss a tenant return 404. Role failures return 403.
Frontend hiding is not a substitute for these checks.
"""

from rest_framework.exceptions import NotFound, PermissionDenied

from organizations.models import Organization, OrganizationMember, OrganizationRole

ADMIN_ROLES = {OrganizationRole.OWNER, OrganizationRole.ADMIN}
OWNER_ONLY = {OrganizationRole.OWNER}


def membership_for(user, organization) -> OrganizationMember | None:
    if not user or not user.is_authenticated:
        return None
    return (
        OrganizationMember.objects.filter(organization=organization, user=user)
        .select_related("organization", "user")
        .first()
    )


def organization_or_404(user, organization_id) -> tuple[Organization, OrganizationMember]:
    membership = (
        OrganizationMember.objects.filter(organization_id=organization_id, user=user)
        .select_related("organization")
        .first()
    )
    if membership is None:
        raise NotFound("Organization not found.")
    return membership.organization, membership


def require_roles(membership: OrganizationMember | None, roles: set[str]) -> OrganizationMember:
    if membership is None or membership.role not in roles:
        raise PermissionDenied("You do not have permission to do that in this organization.")
    return membership


def assert_can_assign_role(actor: OrganizationMember, role: str) -> None:
    if role not in OrganizationRole.values:
        raise PermissionDenied("Unknown organization role.")
    if role == OrganizationRole.OWNER and actor.role != OrganizationRole.OWNER:
        raise PermissionDenied("Only an owner can grant the owner role.")


def assert_not_last_owner(organization, member: OrganizationMember, *, next_role: str | None) -> None:
    """Prevent an organization from being left without an owner."""

    if member.role != OrganizationRole.OWNER:
        return
    if next_role == OrganizationRole.OWNER:
        return
    other_owners = (
        OrganizationMember.objects.select_for_update()
        .filter(organization=organization, role=OrganizationRole.OWNER)
        .exclude(pk=member.pk)
    )
    if not other_owners.exists():
        raise PermissionDenied("The organization must keep at least one owner.")
