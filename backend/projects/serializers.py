from rest_framework import serializers

from accounts.serializers import UserSerializer
from projects.access import can_archive, can_delete, can_edit_project, can_manage_members
from projects.models import Project, ProjectEvent, ProjectMember, ProjectRole, ProjectStatus


class OrganizationRefSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()


class ProjectSerializer(serializers.ModelSerializer):
    organization = OrganizationRefSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_archived = serializers.BooleanField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    role = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_manage_members = serializers.SerializerMethodField()
    can_archive = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "organization",
            "name",
            "slug",
            "key",
            "summary",
            "product_description",
            "status",
            "status_label",
            "is_archived",
            "archived_at",
            "created_by",
            "member_count",
            "role",
            "can_edit",
            "can_manage_members",
            "can_archive",
            "can_delete",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _roles(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        project_role = getattr(obj, "current_role", None)
        if project_role is None and user and user.is_authenticated:
            membership = obj.memberships.filter(user=user).only("role").first()
            project_role = membership.role if membership else None
        org_role = self.context.get("org_role")
        if org_role is None and user and user.is_authenticated:
            org_membership = obj.organization.memberships.filter(user=user).only("role").first()
            org_role = org_membership.role if org_membership else None
        return project_role, org_role

    def get_role(self, obj):
        project_role, _org_role = self._roles(obj)
        return project_role

    def get_can_edit(self, obj):
        project_role, org_role = self._roles(obj)
        return bool(org_role) and can_edit_project(project_role, org_role)

    def get_can_manage_members(self, obj):
        project_role, org_role = self._roles(obj)
        return bool(org_role) and can_manage_members(project_role, org_role)

    def get_can_archive(self, obj):
        project_role, org_role = self._roles(obj)
        return bool(org_role) and can_archive(project_role, org_role)

    def get_can_delete(self, obj):
        project_role, org_role = self._roles(obj)
        return bool(org_role) and can_delete(project_role, org_role)


class ProjectWriteSerializer(serializers.Serializer):
    organization = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    summary = serializers.CharField(max_length=280, required=False, allow_blank=True, default="")
    product_description = serializers.CharField(max_length=20000)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value

    def validate_product_description(self, value):
        value = value.strip()
        if len(value) < 20:
            raise serializers.ValidationError(
                "Describe the product in at least a sentence. Orbit stores this as the source description."
            )
        return value


class ProjectUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False)
    summary = serializers.CharField(max_length=280, required=False, allow_blank=True)
    product_description = serializers.CharField(required=False, max_length=20000)
    status = serializers.CharField(required=False)
    organization = serializers.UUIDField(required=False)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value

    def validate_product_description(self, value):
        value = value.strip()
        if len(value) < 20:
            raise serializers.ValidationError("Product description must be at least 20 characters.")
        return value

    def validate_status(self, value):
        raise serializers.ValidationError(
            "Status cannot be set directly. "
            f"'{value}' is not applied. Use the lifecycle service when a later phase opens that transition."
        )

    def validate_organization(self, value):
        raise serializers.ValidationError("A project cannot be moved to another organization.")


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["id", "user", "role", "created_at", "updated_at"]


class ProjectMemberWriteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ProjectRole.choices, default=ProjectRole.VIEWER)


class ProjectMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ProjectRole.choices)


class ProjectEventSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = ProjectEvent
        fields = ["id", "event_type", "message", "metadata", "actor", "created_at"]


class LifecycleQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProjectStatus.choices, required=False)
