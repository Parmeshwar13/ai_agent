from django.urls import path

from projects.views import (
    LifecycleView,
    ProjectArchiveView,
    ProjectDetailView,
    ProjectEventListView,
    ProjectLifecycleView,
    ProjectListCreateView,
    ProjectMemberDetailView,
    ProjectMemberListCreateView,
    ProjectUnarchiveView,
)

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list"),
    path("lifecycle/", LifecycleView.as_view(), name="project-lifecycle"),
    path("<uuid:project_id>/", ProjectDetailView.as_view(), name="project-detail"),
    path("<uuid:project_id>/lifecycle/", ProjectLifecycleView.as_view(), name="project-lifecycle-detail"),
    path("<uuid:project_id>/archive/", ProjectArchiveView.as_view(), name="project-archive"),
    path("<uuid:project_id>/unarchive/", ProjectUnarchiveView.as_view(), name="project-unarchive"),
    path("<uuid:project_id>/members/", ProjectMemberListCreateView.as_view(), name="project-members"),
    path(
        "<uuid:project_id>/members/<uuid:member_id>/",
        ProjectMemberDetailView.as_view(),
        name="project-member-detail",
    ),
    path("<uuid:project_id>/events/", ProjectEventListView.as_view(), name="project-events"),
]
