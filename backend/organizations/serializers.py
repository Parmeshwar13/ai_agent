from rest_framework import serializers

from accounts.serializers import UserSerializer
from organizations.models import Organization, OrganizationEvent, OrganizationMember, OrganizationRole


class OrganizationSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)
    project_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "role",
            "member_count",
            "project_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_role(self, obj):
        user = self.context.get("user")
        if user is None and "request" in self.context:
            user = self.context["request"].user
        if user is None:
            return None
        cached = getattr(obj, "_role_for_user", None)
        if cached:
            return cached
        membership = obj.memberships.filter(user=user).only("role").first()
        return membership.role if membership else None


class OrganizationWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value


class OrganizationUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, required=False)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ["id", "user", "role", "created_at", "updated_at"]


class MemberWriteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationRole.choices, default=OrganizationRole.MEMBER)


class MemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=OrganizationRole.choices)


class OrganizationDeleteSerializer(serializers.Serializer):
    confirm_slug = serializers.CharField()


class OrganizationEventSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationEvent
        fields = ["id", "event_type", "message", "metadata", "actor", "created_at"]
