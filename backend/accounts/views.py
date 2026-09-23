from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers import PasswordChangeSerializer, RegisterSerializer, UserSerializer
from accounts.services import register_user
from accounts.throttles import AuthRateThrottle
from organizations.selectors import attach_roles, organizations_for_user
from organizations.serializers import OrganizationSerializer

User = get_user_model()


def _session_body(user, *, access, refresh):
    organizations = attach_roles(user, organizations_for_user(user))
    return {
        "access": access,
        "refresh": refresh,
        "user": UserSerializer(user).data,
        "organizations": OrganizationSerializer(organizations, many=True, context={"user": user}).data,
    }


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = User.objects.normalize_email(request.data.get("email", ""))
        user = User.objects.filter(email=email).first()
        if user is None or "access" not in response.data:
            return response
        return Response(
            _session_body(user, access=response.data["access"], refresh=response.data["refresh"])
        )


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _organization = register_user(**serializer.validated_data)
        refresh = RefreshToken.for_user(user)
        return Response(
            _session_body(user, access=str(refresh.access_token), refresh=str(refresh)),
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.data.get("refresh")
        if not raw:
            return Response(
                {"detail": "Refresh token is required.", "code": "refresh_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(raw)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid or expired.", "code": "token_invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organizations = attach_roles(request.user, organizations_for_user(request.user))
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "organizations": OrganizationSerializer(
                    organizations, many=True, context={"user": request.user}
                ).data,
            }
        )

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "Password updated."})
