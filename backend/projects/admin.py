from django.contrib import admin

from projects.models import Project, ProjectEvent, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    raw_id_fields = ["user"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["key", "name", "organization", "status", "created_by", "created_at"]
    list_filter = ["status", "organization"]
    search_fields = ["name", "key", "slug", "product_description"]
    readonly_fields = ["id", "slug", "key", "status", "created_at", "updated_at", "archived_at"]
    inlines = [ProjectMemberInline]


@admin.register(ProjectEvent)
class ProjectEventAdmin(admin.ModelAdmin):
    list_display = ["project", "event_type", "actor", "created_at"]
    list_filter = ["event_type"]
    readonly_fields = ["id", "created_at", "updated_at", "metadata", "message"]
