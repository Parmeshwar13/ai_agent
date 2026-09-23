from django.contrib import admin

from organizations.models import Organization, OrganizationEvent, OrganizationMember


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 0
    raw_id_fields = ["user"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_by", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [OrganizationMemberInline]


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "role", "created_at"]
    list_filter = ["role"]
    search_fields = ["organization__name", "user__email"]


@admin.register(OrganizationEvent)
class OrganizationEventAdmin(admin.ModelAdmin):
    list_display = ["organization", "event_type", "actor", "created_at"]
    list_filter = ["event_type"]
    readonly_fields = ["id", "created_at", "updated_at", "metadata"]
