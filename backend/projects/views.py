import uuid

from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import OrbitPagination
from organizations.access import organization_or_404
from projects.access import (
    project_or_404,
    require_archive,
    require_edit,
    require_member_management,
)
from projects.lifecycle import lifecycle_payload
from projects.models import ProjectStatus
from projects.selectors import members_for_project, projects_for_user
from projects.serializers import (
    ProjectEventSerializer,
    ProjectMemberRoleSerializer,
    ProjectMemberSerializer,
    ProjectMemberWriteSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    ProjectWriteSerializer,
)
from projects.services import (
    add_project_member,
    change_project_member_role,
    create_project,
    remove_project_member,
    set_archived,
    update_project,
)


class ProjectListCreateView(APIView):
    def get(self, request):
        organization_id = request.query_params.get("organization") or None
        status_filter = request.query_params.get("status") or None
        if status_filter and status_filter not in ProjectStatus.values:
            raise ValidationError({"status": "Unknown project status."})
        if organization_id:
            try:
                uuid.UUID(str(organization_id))
            except ValueError as exc:
                raise ValidationError({"organization": "Must be a UUID."}) from exc
            organization_or_404(request.user, organization_id)
        include_archived = request.query_params.get("include_archived") in {"1", "true", "yes"}
        search = (request.query_params.get("search") or "").strip()
        queryset = projects_for_user(
            request.user,
            organization_id=organization_id,
            status=status_filter,
            search=search,
            include_archived=include_archived,
        )
        paginator = OrbitPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ProjectSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProjectWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization, _membership = organization_or_404(
            request.user, serializer.validated_data["organization"]
        )
        project = create_project(
            organization=organization,
            creator=request.user,
            name=serializer.validated_data["name"],
            summary=serializer.validated_data.get("summary", ""),
            product_description=serializer.validated_data["product_description"],
        )
        project.member_count = 1
        project.current_role = "owner"
        return Response(
            ProjectSerializer(project, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class LifecycleView(APIView):
    def get(self, request):
        return Response(lifecycle_payload(ProjectStatus.CREATED))


class ProjectDetailView(APIView):
    def _load(self, request, project_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        annotated = (
            type(project)
            .objects.filter(pk=project.pk)
            .select_related("organization", "created_by")
            .annotate(member_count=Count("memberships", distinct=True))
            .get()
        )
        annotated.current_role = project_role
        return annotated, project_role, org_role

    def get(self, request, project_id):
        project, project_role, org_role = self._load(request, project_id)
        return Response(
            ProjectSerializer(
                project,
                context={"request": request, "org_role": org_role, "project_role": project_role},
            ).data
        )

    def patch(self, request, project_id):
        project, project_role, org_role = self._load(request, project_id)
        require_edit(project_role, org_role)
        serializer = ProjectUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_project(
            project=project,
            actor=request.user,
            name=serializer.validated_data.get("name"),
            summary=serializer.validated_data.get("summary"),
            product_description=serializer.validated_data.get("product_description"),
        )
        return self.get(request, project_id)

    def delete(self, request, project_id):
        project, project_role, org_role = self._load(request, project_id)
        require_archive(project_role, org_role)
        if org_role != "owner" and project_role != "owner":
            raise PermissionDenied("Only an organization owner or project owner can delete a project.")
        if request.query_params.get("confirm") != "true":
            raise ValidationError(
                {"confirm": "Pass confirm=true to permanently delete. Archive keeps the project history."}
            )
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectLifecycleView(APIView):
    def get(self, request, project_id):
        project, _project_role, _org_role = project_or_404(request.user, project_id)
        return Response(lifecycle_payload(project.status))


class ProjectArchiveView(APIView):
    def post(self, request, project_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        require_archive(project_role, org_role)
        set_archived(project=project, actor=request.user, archived=True)
        annotated = (
            type(project)
            .objects.filter(pk=project.pk)
            .select_related("organization", "created_by")
            .annotate(member_count=Count("memberships", distinct=True))
            .get()
        )
        annotated.current_role = project_role
        return Response(
            ProjectSerializer(annotated, context={"request": request, "org_role": org_role}).data
        )


class ProjectUnarchiveView(APIView):
    def post(self, request, project_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        require_archive(project_role, org_role)
        set_archived(project=project, actor=request.user, archived=False)
        annotated = (
            type(project)
            .objects.filter(pk=project.pk)
            .select_related("organization", "created_by")
            .annotate(member_count=Count("memberships", distinct=True))
            .get()
        )
        annotated.current_role = project_role
        return Response(
            ProjectSerializer(annotated, context={"request": request, "org_role": org_role}).data
        )


class ProjectMemberListCreateView(APIView):
    def get(self, request, project_id):
        project, _project_role, _org_role = project_or_404(request.user, project_id)
        return Response(ProjectMemberSerializer(members_for_project(project), many=True).data)

    def post(self, request, project_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        require_member_management(project_role, org_role)
        serializer = ProjectMemberWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member = add_project_member(
                project=project,
                actor=request.user,
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
            )
        except LookupError:
            raise ValidationError({"email": "No Orbit account uses that email."}) from None
        except ValueError:
            raise ValidationError({"email": "That person is already on this project."}) from None
        except PermissionError:
            raise ValidationError(
                {"email": "That person must be a member of the organization before joining the project."}
            ) from None
        member = members_for_project(project).get(pk=member.pk)
        return Response(ProjectMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class ProjectMemberDetailView(APIView):
    def patch(self, request, project_id, member_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        require_member_management(project_role, org_role)
        member = members_for_project(project).filter(pk=member_id).first()
        if member is None:
            return Response({"detail": "Member not found.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProjectMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            change_project_member_role(
                project=project,
                actor=request.user,
                member=member,
                role=serializer.validated_data["role"],
            )
        except PermissionError:
            raise PermissionDenied("The project must keep at least one owner.") from None
        member.refresh_from_db()
        return Response(ProjectMemberSerializer(member).data)

    def delete(self, request, project_id, member_id):
        project, project_role, org_role = project_or_404(request.user, project_id)
        require_member_management(project_role, org_role)
        member = members_for_project(project).filter(pk=member_id).first()
        if member is None:
            return Response({"detail": "Member not found.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            remove_project_member(project=project, actor=request.user, member=member)
        except PermissionError:
            raise PermissionDenied("The project must keep at least one owner.") from None
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectEventListView(APIView):
    def get(self, request, project_id):
        project, _project_role, _org_role = project_or_404(request.user, project_id)
        events = project.events.select_related("actor").all()
        paginator = OrbitPagination()
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(ProjectEventSerializer(page, many=True).data)
