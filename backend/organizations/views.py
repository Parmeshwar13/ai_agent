from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.access import ADMIN_ROLES, OWNER_ONLY, organization_or_404, require_roles
from organizations.selectors import attach_roles, members_for_organization, organizations_for_user
from organizations.serializers import (
    MemberRoleSerializer,
    MemberWriteSerializer,
    OrganizationDeleteSerializer,
    OrganizationEventSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
    OrganizationWriteSerializer,
)
from organizations.services import (
    add_member,
    change_member_role,
    create_organization,
    delete_organization,
    remove_member,
    update_organization,
)


def _with_role(organization, role):
    organization._role_for_user = role
    return organization


class OrganizationListCreateView(APIView):
    def get(self, request):
        organizations = attach_roles(request.user, organizations_for_user(request.user))
        return Response(OrganizationSerializer(organizations, many=True, context={"user": request.user}).data)

    def post(self, request):
        serializer = OrganizationWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = create_organization(owner=request.user, **serializer.validated_data)
        organization.member_count = 1
        organization.project_count = 0
        _with_role(organization, "owner")
        return Response(
            OrganizationSerializer(organization, context={"user": request.user}).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(APIView):
    def get(self, request, organization_id):
        organization, membership = organization_or_404(request.user, organization_id)
        annotated = (
            type(organization)
            .objects.filter(pk=organization.pk)
            .annotate(
                member_count=Count("memberships", distinct=True),
                project_count=Count("projects", distinct=True),
            )
            .get()
        )
        _with_role(annotated, membership.role)
        return Response(OrganizationSerializer(annotated, context={"user": request.user}).data)

    def patch(self, request, organization_id):
        organization, membership = organization_or_404(request.user, organization_id)
        require_roles(membership, ADMIN_ROLES)
        serializer = OrganizationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_organization(organization=organization, actor=request.user, **serializer.validated_data)
        return self.get(request, organization_id)

    def delete(self, request, organization_id):
        organization, membership = organization_or_404(request.user, organization_id)
        require_roles(membership, OWNER_ONLY)
        serializer = OrganizationDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["confirm_slug"] != organization.slug:
            raise ValidationError({"confirm_slug": "Slug confirmation does not match."})
        delete_organization(organization=organization, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationMemberListCreateView(APIView):
    def get(self, request, organization_id):
        organization, _membership = organization_or_404(request.user, organization_id)
        members = members_for_organization(organization)
        return Response(OrganizationMemberSerializer(members, many=True).data)

    def post(self, request, organization_id):
        organization, membership = organization_or_404(request.user, organization_id)
        require_roles(membership, ADMIN_ROLES)
        serializer = MemberWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member = add_member(
                organization=organization,
                actor_membership=membership,
                email=serializer.validated_data["email"],
                role=serializer.validated_data["role"],
            )
        except LookupError:
            raise ValidationError(
                {"email": "No Orbit account uses that email. Ask them to register, then add them."}
            ) from None
        except ValueError as exc:
            if str(exc) == "already_member":
                raise ValidationError({"email": "That person is already a member."}) from None
            raise
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from None
        member = members_for_organization(organization).get(pk=member.pk)
        return Response(OrganizationMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class OrganizationMemberDetailView(APIView):
    def patch(self, request, organization_id, member_id):
        organization, membership = organization_or_404(request.user, organization_id)
        require_roles(membership, ADMIN_ROLES)
        member = members_for_organization(organization).filter(pk=member_id).first()
        if member is None:
            return Response({"detail": "Member not found.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            change_member_role(
                organization=organization,
                actor_membership=membership,
                member=member,
                role=serializer.validated_data["role"],
            )
        except PermissionError as exc:
            raise PermissionDenied("You cannot change that member's role.") from exc
        member.refresh_from_db()
        return Response(OrganizationMemberSerializer(member).data)

    def delete(self, request, organization_id, member_id):
        organization, membership = organization_or_404(request.user, organization_id)
        member = members_for_organization(organization).filter(pk=member_id).first()
        if member is None:
            return Response({"detail": "Member not found.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        if membership.role not in ADMIN_ROLES and member.user_id != request.user.id:
            raise PermissionDenied("You do not have permission to remove that member.")
        try:
            remove_member(organization=organization, actor_membership=membership, member=member)
        except PermissionError as exc:
            raise PermissionDenied("You cannot remove that member.") from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationEventListView(APIView):
    def get(self, request, organization_id):
        organization, _membership = organization_or_404(request.user, organization_id)
        events = organization.events.select_related("actor").all()[:50]
        return Response(OrganizationEventSerializer(events, many=True).data)
