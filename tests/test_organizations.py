import pytest

pytestmark = pytest.mark.django_db


def test_organization_crud_and_last_owner_guard(auth_client, owner, outsider, organization, make_user):
    client = auth_client(owner)
    listed = client.get("/api/organizations/")
    assert listed.status_code == 200
    assert listed.data[0]["slug"] == organization.slug
    assert listed.data[0]["role"] == "owner"

    created = client.post(
        "/api/organizations/",
        {"name": "Second Studio", "description": "Another tenant"},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["role"] == "owner"

    outsider_client = auth_client(outsider)
    hidden = outsider_client.get(f"/api/organizations/{organization.id}/")
    assert hidden.status_code == 404
    hidden_members = outsider_client.get(f"/api/organizations/{organization.id}/members/")
    assert hidden_members.status_code == 404

    added = client.post(
        f"/api/organizations/{organization.id}/members/",
        {"email": outsider.email, "role": "member"},
        format="json",
    )
    assert added.status_code == 201

    missing = client.post(
        f"/api/organizations/{organization.id}/members/",
        {"email": "nobody@example.com", "role": "member"},
        format="json",
    )
    assert missing.status_code == 400

    member_client = auth_client(outsider)
    forbidden = member_client.patch(
        f"/api/organizations/{organization.id}/",
        {"name": "Hijacked"},
        format="json",
    )
    assert forbidden.status_code == 403

    demote = client.patch(
        f"/api/organizations/{organization.id}/members/{organization.memberships.get(user=owner).id}/",
        {"role": "member"},
        format="json",
    )
    assert demote.status_code == 403

    remove = client.delete(
        f"/api/organizations/{organization.id}/members/{organization.memberships.get(user=owner).id}/"
    )
    assert remove.status_code == 403

    updated = client.patch(
        f"/api/organizations/{organization.id}/",
        {"description": "Updated by owner"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["description"] == "Updated by owner"

    bad_delete = client.delete(
        f"/api/organizations/{organization.id}/",
        {"confirm_slug": "nope"},
        format="json",
    )
    assert bad_delete.status_code == 400
    deleted = client.delete(
        f"/api/organizations/{organization.id}/",
        {"confirm_slug": organization.slug},
        format="json",
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/organizations/{organization.id}/").status_code == 404


def test_member_cannot_grant_owner(auth_client, owner, organization, make_user):
    admin = make_user("admin@example.com", first_name="Ari")
    owner_membership = organization.memberships.get(user=owner)
    from organizations.models import OrganizationRole
    from organizations.services import add_member

    add_member(
        organization=organization,
        actor_membership=owner_membership,
        email=admin.email,
        role=OrganizationRole.ADMIN,
    )
    client = auth_client(admin)
    response = client.post(
        f"/api/organizations/{organization.id}/members/",
        {"email": "owner@example.com", "role": "owner"},
        format="json",
    )
    # Owner is already a member; the role check happens before the duplicate check.
    assert response.status_code == 403
