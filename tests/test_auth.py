import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_health_is_public(api):
    response = api.get("/api/health/")
    assert response.status_code == 200
    assert response.data["service"] == "orbit"
    assert response.data["phase"] == 1
    assert response.data["status"] == "ok"


def test_register_creates_user_and_workspace(api):
    response = api.post(
        "/api/auth/register/",
        {
            "email": "Ada@Example.com",
            "password": "correct-horse-battery",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "organization_name": "Analytical Engines",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["user"]["email"] == "ada@example.com"
    assert response.data["access"]
    assert len(response.data["organizations"]) == 1
    assert response.data["organizations"][0]["name"] == "Analytical Engines"
    assert response.data["organizations"][0]["role"] == "owner"
    assert User.objects.filter(email="ada@example.com").count() == 1


def test_register_defaults_workspace_name(api):
    response = api.post(
        "/api/auth/register/",
        {
            "email": "grace@example.com",
            "password": "correct-horse-battery",
            "first_name": "Grace",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["organizations"][0]["name"] == "Grace's workspace"


def test_register_rejects_duplicate_and_short_password(api):
    payload = {
        "email": "ada@example.com",
        "password": "correct-horse-battery",
        "first_name": "Ada",
    }
    assert api.post("/api/auth/register/", payload, format="json").status_code == 201
    duplicate = api.post("/api/auth/register/", payload, format="json")
    assert duplicate.status_code == 400
    assert "email" in duplicate.data["errors"]

    weak = api.post(
        "/api/auth/register/",
        {"email": "other@example.com", "password": "short", "first_name": "Other"},
        format="json",
    )
    assert weak.status_code == 400
    assert "password" in weak.data["errors"]


def test_login_logout_and_me(api, make_user):
    user = make_user("ada@example.com")
    denied = api.get("/api/auth/me/")
    assert denied.status_code == 401

    login = api.post(
        "/api/auth/login/",
        {"email": "Ada@Example.com", "password": "correct-horse-battery"},
        format="json",
    )
    assert login.status_code == 200
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.data["user"]["id"] == str(user.id)

    patched = api.patch("/api/auth/me/", {"first_name": "Augusta"}, format="json")
    assert patched.status_code == 200
    assert patched.data["full_name"] == "Augusta Lovelace"

    logout = api.post("/api/auth/logout/", {"refresh": login.data["refresh"]}, format="json")
    assert logout.status_code == 204
    reused = api.post("/api/auth/refresh/", {"refresh": login.data["refresh"]}, format="json")
    assert reused.status_code == 401


def test_password_change_checks_current_password(auth_client, owner):
    client = auth_client(owner)
    bad = client.post(
        "/api/auth/password/",
        {"current_password": "wrong-password-value", "new_password": "another-strong-pass"},
        format="json",
    )
    assert bad.status_code == 400
    changed = client.post(
        "/api/auth/password/",
        {"current_password": "correct-horse-battery", "new_password": "another-strong-pass"},
        format="json",
    )
    assert changed.status_code == 200
    owner.refresh_from_db()
    assert owner.check_password("another-strong-pass")


def test_seed_demo_refuses_when_debug_is_off():
    with pytest.raises(CommandError):
        call_command("seed_demo")
