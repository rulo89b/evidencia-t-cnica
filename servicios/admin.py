
from django.contrib import admin

from .models import Template, TemplatePhoto


class TemplatePhotoInline(admin.TabularInline):
    model = TemplatePhoto
    extra = 0


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "created_at",
        "deleted_at",
    )
    list_filter = ("created_at", "deleted_at")
    search_fields = ("name", "owner__username")
    inlines = [TemplatePhotoInline]


@admin.register(TemplatePhoto)
class TemplatePhotoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "template",
        "position",
        "stage",
        "is_required",
    )
    list_filter = ("stage", "is_required")
    ordering = ("template", "position")
