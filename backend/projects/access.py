"""Project authorization.

The tenant boundary is the organization. A user who is not a member of the
organization receives 404 for every project in it, including by direct id.
"""

from rest_framework.exceptions import NotFound, PermissionDenied

from organizations.access import ADMIN_ROLES, membership_for
from organizations.models import OrganizationRole
from projects.models import Project, ProjectMember, ProjectRole

PROJECT_EDITOR_ROLES = {ProjectRole.OWNER, ProjectRole.MAINTAINER}


def project_or_404(user, project_id) -> tuple[Project, str | None, str]:
    """Return project, explicit project role (or None), and organization role.

    Missing projects and projects outside the caller's organizations are
    indistinguishable.
    """

    project = (
        Project.objects.filter(pk=project_id, organization__memberships__user=user)
        .select_related("organization", "created_by")
        .first()
    )
    if project is None:
        raise NotFound("Project not found.")
    org_membership = membership_for(user, project.organization)
    if org_membership is None:
        raise NotFound("Project not found.")
    project_membership = ProjectMember.objects.filter(project=project, user=user).only("role").first()
    project_role = project_membership.role if project_membership else None
    return project, project_role, org_membership.role


def can_edit_project(project_role: str | None, org_role: str) -> bool:
    if org_role in ADMIN_ROLES:
        return True
    return project_role in PROJECT_EDITOR_ROLES


def can_manage_members(project_role: str | None, org_role: str) -> bool:
    if org_role in ADMIN_ROLES:
        return True
    return project_role == ProjectRole.OWNER


def can_archive(project_role: str | None, org_role: str) -> bool:
    return can_manage_members(project_role, org_role)


def can_delete(project_role: str | None, org_role: str) -> bool:
    return org_role == OrganizationRole.OWNER or project_role == ProjectRole.OWNER


def require_edit(project_role, org_role) -> None:
    if not can_edit_project(project_role, org_role):
        raise PermissionDenied("You can view this project, but you cannot change it.")


def require_member_management(project_role, org_role) -> None:
    if not can_manage_members(project_role, org_role):
        raise PermissionDenied("You cannot change membership for this project.")


def require_archive(project_role, org_role) -> None:
    if not can_archive(project_role, org_role):
        raise PermissionDenied("You cannot archive this project.")


def org_role_is_admin(org_role: str) -> bool:
    return org_role in {OrganizationRole.OWNER, OrganizationRole.ADMIN}
