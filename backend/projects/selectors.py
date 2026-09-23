from django.db.models import Count, OuterRef, Q, Subquery

from projects.models import Project, ProjectMember


def projects_for_user(user, *, organization_id=None, status=None, search="", include_archived=False):
    """Projects visible to a user. Organization membership is the hard boundary."""

    role_subquery = ProjectMember.objects.filter(project=OuterRef("pk"), user=user).values("role")[:1]
    queryset = Project.objects.filter(organization__memberships__user=user).select_related(
        "organization", "created_by"
    )
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    if not include_archived:
        queryset = queryset.filter(archived_at__isnull=True)
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(summary__icontains=search)
            | Q(product_description__icontains=search)
            | Q(key__icontains=search)
        )
    return (
        queryset.annotate(
            member_count=Count("memberships", distinct=True),
            current_role=Subquery(role_subquery),
        )
        .distinct()
        .order_by("-created_at")
    )


def members_for_project(project):
    return ProjectMember.objects.filter(project=project).select_related("user").order_by("created_at")
