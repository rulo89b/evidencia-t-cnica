
from django.contrib import admin

from .models import Group, GroupMember, GroupInvitation


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name", "created_by__username")


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("group__name", "user__username")


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "invited_email",
        "invited_by",
        "status",
        "expires_at",
    )
    list_filter = ("status",)
    exclude = ("token",)
