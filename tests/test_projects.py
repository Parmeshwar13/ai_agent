import pytest

from core.exceptions import InvalidLifecycleTransition
from projects.lifecycle import ALLOWED_TRANSITIONS, lifecycle_payload
from projects.models import ProjectStatus
from projects.services import transition_project

pytestmark = pytest.mark.django_db

DESCRIPTION = "A marketplace for independent bookbinders, with orders, quotes, and roles."


def test_project_is_scoped_to_its_organization(
    auth_client, owner, outsider, organization, make_org, make_user, make_project
):
    other_owner = make_user("other@example.com", first_name="Omar")
    other_org = make_org(other_owner, "Other House")
    project = make_project(organization, owner, name="Bindery")
    foreign = make_project(other_org, other_owner, name="Foreign catalog")

    client = auth_client(owner)
    listing = client.get("/api/projects/")
    assert listing.status_code == 200
    ids = {row["id"] for row in listing.data["results"]}
    assert str(project.id) in ids
    assert str(foreign.id) not in ids

    assert client.get(f"/api/projects/{foreign.id}/").status_code == 404
    assert client.get(f"/api/projects/{foreign.id}/events/").status_code == 404
    assert client.get(f"/api/projects/{foreign.id}/members/").status_code == 404
    assert client.get(f"/api/projects/?organization={other_org.id}").status_code == 404

    created = client.post(
        "/api/projects/",
        {
            "organization": str(other_org.id),
            "name": "Sneaky",
            "product_description": DESCRIPTION,
        },
        format="json",
    )
    assert created.status_code == 404

    own = client.post(
        "/api/projects/",
        {
            "organization": str(organization.id),
            "name": "Field notes",
            "summary": "Notes product",
            "product_description": DESCRIPTION,
        },
        format="json",
    )
    assert own.status_code == 201
    assert own.data["status"] == "created"
    assert own.data["key"]
    assert own.data["role"] == "owner"
    assert own.data["organization"]["id"] == str(organization.id)

    outsider_client = auth_client(outsider)
    assert outsider_client.get(f"/api/projects/{project.id}/").status_code == 404
    leaked = outsider_client.get(f"/api/projects/?search=Bindery")
    assert leaked.status_code == 200
    assert leaked.data["results"] == []


def test_same_slug_is_allowed_in_different_organizations(
    owner, organization, make_org, make_user, make_project
):
    other = make_org(make_user("second@example.com"), "Second")
    first = make_project(organization, owner, name="Atlas")
    second = make_project(other, other.created_by, name="Atlas")
    assert first.slug == second.slug
    assert first.organization_id != second.organization_id


def test_status_cannot_be_forged_and_transitions_are_closed(
    auth_client, owner, organization, make_project
):
    project = make_project(organization, owner)
    client = auth_client(owner)
    forged = client.patch(
        f"/api/projects/{project.id}/",
        {"status": "completed"},
        format="json",
    )
    assert forged.status_code == 400
    project.refresh_from_db()
    assert project.status == ProjectStatus.CREATED

    moved = client.patch(
        f"/api/projects/{project.id}/",
        {"organization": "00000000-0000-0000-0000-000000000000"},
        format="json",
    )
    assert moved.status_code == 400

    with pytest.raises(InvalidLifecycleTransition):
        transition_project(project=project, actor=owner, to_status=ProjectStatus.IMPLEMENTING)

    assert all(not targets for targets in ALLOWED_TRANSITIONS.values())
    payload = client.get(f"/api/projects/{project.id}/lifecycle/").data
    assert payload["current"] == "created"
    assert payload["allowed_transitions"] == []
    assert payload["automation"] == "none"
    assert payload["happy_path"][0]["value"] == "created"
    assert payload["happy_path"][-1]["value"] == "completed"
    assert lifecycle_payload(project.status)["phase"] == 1


def test_org_member_can_read_but_not_edit(auth_client, owner, organization, member_user, make_project):
    project = make_project(organization, owner, name="Read only product")
    client = auth_client(member_user)
    detail = client.get(f"/api/projects/{project.id}/")
    assert detail.status_code == 200
    assert detail.data["can_edit"] is False
    denied = client.patch(
        f"/api/projects/{project.id}/",
        {"summary": "Changed by a viewer"},
        format="json",
    )
    assert denied.status_code == 403
    project.refresh_from_db()
    assert project.summary != "Changed by a viewer"


def test_archive_preserves_history_and_hides_from_default_list(
    auth_client, owner, organization, make_project
):
    project = make_project(organization, owner, name="Archive me")
    client = auth_client(owner)
    archived = client.post(f"/api/projects/{project.id}/archive/")
    assert archived.status_code == 200
    assert archived.data["is_archived"] is True

    hidden = client.get(f"/api/projects/?organization={organization.id}")
    assert str(project.id) not in {row["id"] for row in hidden.data["results"]}
    visible = client.get(
        f"/api/projects/?organization={organization.id}&include_archived=true"
    )
    assert str(project.id) in {row["id"] for row in visible.data["results"]}

    events = client.get(f"/api/projects/{project.id}/events/")
    types = [row["event_type"] for row in events.data["results"]]
    assert "project_created" in types
    assert "project_archived" in types

    restored = client.post(f"/api/projects/{project.id}/unarchive/")
    assert restored.status_code == 200
    assert restored.data["is_archived"] is False


def test_project_member_must_belong_to_the_organization(
    auth_client, owner, outsider, organization, make_project
):
    project = make_project(organization, owner)
    client = auth_client(owner)
    rejected = client.post(
        f"/api/projects/{project.id}/members/",
        {"email": outsider.email, "role": "viewer"},
        format="json",
    )
    assert rejected.status_code == 400

    unconfirmed = client.delete(f"/api/projects/{project.id}/")
    assert unconfirmed.status_code == 400
    confirmed = client.delete(f"/api/projects/{project.id}/?confirm=true")
    assert confirmed.status_code == 204


def test_search_stays_inside_the_tenant(auth_client, owner, organization, make_project, make_org, make_user):
    make_project(organization, owner, name="Attendance ledger")
    other = make_org(make_user("z@example.com"), "Zed")
    make_project(other, other.created_by, name="Attendance ledger foreign")
    client = auth_client(owner)
    response = client.get("/api/projects/?search=Attendance")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Attendance ledger"
