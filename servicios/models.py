
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


class Job(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        IN_PROGRESS = "in_progress", "En progreso"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    class CancelledReason(models.TextChoices):
        MEMBER_REMOVED = (
            "member_removed_no_reassignment",
            "Miembro retirado sin reemplazo",
        )
        ADMIN_CANCELLED = (
            "admin_cancelled",
            "Cancelado por administrador",
        )
        OTHER = "other", "Otro"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_jobs",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_jobs",
    )

    group = models.ForeignKey(
        "grupos.Group",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="jobs",
    )

    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        related_name="jobs",
    )

    site_name = models.CharField(max_length=150)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    notes = models.TextField(blank=True)

    due_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cancelled_reason = models.CharField(
        max_length=30,
        choices=CancelledReason.choices,
        blank=True,
    )

    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cancelled_jobs",
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["group", "status"]),
        ]

    def __str__(self):
        return self.site_name


class JobPhotoSlot(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="photo_slots",
    )

    template_photo = models.ForeignKey(
        TemplatePhoto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_slots",
    )

    position = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)

    stage = models.CharField(
        max_length=20,
        choices=TemplatePhoto.Stage.choices,
    )

    is_required = models.BooleanField(default=True)

    photo_path = models.ImageField(
        upload_to="job_photos/%Y/%m/",
        max_length=500,
        blank=True,
    )

    captured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="captured_photo_slots",
    )

    captured_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["position"]

        constraints = [
            models.UniqueConstraint(
                fields=["job", "position"],
                name="unique_job_photo_position",
            ),

            models.CheckConstraint(
                condition=Q(position__gte=1),
                name="job_photo_position_gte_1",
            ),

            models.CheckConstraint(
                condition=(
                    Q(
                        photo_path="",
                        captured_by__isnull=True,
                        captured_at__isnull=True,
                    )
                    |
                    (
                        ~Q(photo_path="")
                        & Q(captured_by__isnull=False)
                        & Q(captured_at__isnull=False)
                    )
                ),
                name="job_photo_capture_consistency",
            ),
        ]

    @property
    def is_captured(self):
        return bool(self.photo_path)

    def __str__(self):
        return f"{self.position}. {self.title}"


class JobAssignment(models.Model):

    class Reason(models.TextChoices):
        INITIAL = "initial", "Asignación inicial"
        ADMIN_REASSIGNMENT = (
            "admin_reassignment",
            "Reasignación por administrador",
        )
        MEMBER_REMOVED = (
            "member_removed",
            "Miembro retirado",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="job_assignment_history",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="made_job_assignments",
    )

    reason = models.CharField(
        max_length=30,
        choices=Reason.choices,
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["assigned_at"]

        indexes = [
            models.Index(fields=["job", "assigned_at"]),
            models.Index(fields=["assigned_to", "ended_at"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["job"],
                condition=Q(ended_at__isnull=True),
                name="unique_active_job_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.job} - {self.assigned_to}"
