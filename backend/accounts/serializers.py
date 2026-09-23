from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at", "full_name"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    organization_name = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate_email(self, value):
        email = User.objects.normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value
