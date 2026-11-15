
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Template(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="templates",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class TemplatePhoto(models.Model):
    class Stage(models.TextChoices):
        BEFORE = "before", "Antes"
        DURING = "during", "Durante"
        AFTER = "after", "Después"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name="photos",
    )

    position = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
    )
    is_required = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "position"],
                name="unique_template_photo_position",
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1),
                name="template_photo_position_gte_1",
            ),
        ]

    def __str__(self):
        return f"{self.position}. {self.title}"
