from django.db.models import Count

from organizations.models import Organization, OrganizationMember


def organizations_for_user(user):
    return (
        Organization.objects.filter(memberships__user=user)
        .annotate(
            member_count=Count("memberships", distinct=True),
            project_count=Count("projects", distinct=True),
        )
        .order_by("name")
        .distinct()
    )


def attach_roles(user, organizations):
    organizations = list(organizations)
    roles = {
        row["organization_id"]: row["role"]
        for row in OrganizationMember.objects.filter(
            user=user,
            organization_id__in=[organization.id for organization in organizations],
        ).values("organization_id", "role")
    }
    for organization in organizations:
        organization._role_for_user = roles.get(organization.id)
    return organizations


def members_for_organization(organization):
    return (
        OrganizationMember.objects.filter(organization=organization)
        .select_related("user")
        .order_by("created_at")
    )
