import pytest
from rest_framework.test import APIClient

from accounts.models import User
from organizations.models import OrganizationRole
from organizations.services import add_member, create_organization
from projects.services import create_project


PASSWORD = "correct-horse-battery"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make(email, first_name="Ada", last_name="Lovelace", password=PASSWORD):
        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    return _make


@pytest.fixture
def make_org(db):
    def _make(owner, name="Northwind"):
        return create_organization(owner=owner, name=name, description="Test workspace")

    return _make


@pytest.fixture
def make_project(db):
    def _make(organization, creator, name="Clinic scheduling", description=None):
        return create_project(
            organization=organization,
            creator=creator,
            name=name,
            summary="A separate product.",
            product_description=description
            or "Scheduling for independent clinics, with roles for desk staff and clinicians.",
        )

    return _make


@pytest.fixture
def owner(make_user):
    return make_user("owner@example.com", first_name="Owen")


@pytest.fixture
def outsider(make_user):
    return make_user("outsider@example.com", first_name="Outsider")


@pytest.fixture
def organization(owner, make_org):
    return make_org(owner, "Northwind")


@pytest.fixture
def auth_client(api):
    def _auth(user):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        assert response.status_code == 200, response.content
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    return _auth


@pytest.fixture
def member_user(make_user, organization):
    user = make_user("member@example.com", first_name="Mina")
    actor = organization.memberships.get(user__email="owner@example.com")
    add_member(
        organization=organization,
        actor_membership=actor,
        email=user.email,
        role=OrganizationRole.MEMBER,
    )
    return user
