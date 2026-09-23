from django.urls import path

from organizations.views import (
    OrganizationDetailView,
    OrganizationEventListView,
    OrganizationListCreateView,
    OrganizationMemberDetailView,
    OrganizationMemberListCreateView,
)

urlpatterns = [
    path("", OrganizationListCreateView.as_view(), name="organization-list"),
    path("<uuid:organization_id>/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("<uuid:organization_id>/members/", OrganizationMemberListCreateView.as_view(), name="organization-members"),
    path(
        "<uuid:organization_id>/members/<uuid:member_id>/",
        OrganizationMemberDetailView.as_view(),
        name="organization-member-detail",
    ),
    path("<uuid:organization_id>/events/", OrganizationEventListView.as_view(), name="organization-events"),
]
