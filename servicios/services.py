
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from grupos.models import GroupMember

from .models import (
    Job,
    JobPhotoSlot,
    JobAssignment,
)

from django.db.models import Max
from .models import Template, TemplatePhoto


@transaction.atomic
def create_job(
    *,
    user,
    template,
    site_name,
    group=None,
    assigned_to=None,
    notes="",
    due_date=None,
):
    # Validar la propiedad de la plantilla.
    if template.owner_id != user.pk:
        raise PermissionDenied(
            "Solo puedes utilizar tus propias plantillas."
        )

    if template.deleted_at is not None:
        raise ValidationError(
            "La plantilla ha sido eliminada."
        )

    if group is None:
        # Trabajo individual.
        if assigned_to is not None and assigned_to.pk != user.pk:
            raise ValidationError(
                "Un trabajo individual debe asignarse al creador."
            )

        assigned_to = user

    else:
        # Trabajo grupal.
        is_admin = GroupMember.objects.filter(
            group=group,
            user=user,
            role=GroupMember.Role.ADMIN,
        ).exists()

        if not is_admin:
            raise PermissionDenied(
                "Solo un administrador puede asignar trabajos."
            )

        if assigned_to is None:
            raise ValidationError(
                "Debes seleccionar un responsable."
            )

        is_member = GroupMember.objects.filter(
            group=group,
            user=assigned_to,
        ).exists()

        if not is_member:
            raise ValidationError(
                "El responsable debe pertenecer al grupo."
            )

    # Crear el trabajo.
    job = Job.objects.create(
        created_by=user,
        assigned_to=assigned_to,
        group=group,
        template=template,
        site_name=site_name,
        notes=notes,
        due_date=due_date,
    )

    # Copiar los requisitos fotográficos.
    slots = [
        JobPhotoSlot(
            job=job,
            template_photo=photo,
            position=photo.position,
            title=photo.title,
            instructions=photo.instructions,
            stage=photo.stage,
            is_required=photo.is_required,
        )
        for photo in template.photos.all()
    ]

    JobPhotoSlot.objects.bulk_create(slots)

    # Registrar la asignación inicial.
    JobAssignment.objects.create(
        job=job,
        assigned_to=assigned_to,
        assigned_by=user,
        reason=JobAssignment.Reason.INITIAL,
    )

    return job


@transaction.atomic
def reassign_job(*, job, user, new_assignee):

    job = Job.objects.select_for_update().get(pk=job.pk)

    if job.group_id is None:
        raise ValidationError(
            "Los trabajos individuales no pueden reasignarse."
        )

    if job.status not in (
        Job.Status.PENDING,
        Job.Status.IN_PROGRESS,
    ):
        raise ValidationError(
            "Solo pueden reasignarse trabajos activos."
        )

    is_admin = GroupMember.objects.filter(
        group_id=job.group_id,
        user=user,
        role=GroupMember.Role.ADMIN,
    ).exists()

    if not is_admin:
        raise PermissionDenied(
            "No tienes permiso para reasignar este trabajo."
        )

    is_member = GroupMember.objects.filter(
        group_id=job.group_id,
        user=new_assignee,
    ).exists()

    if not is_member:
        raise ValidationError(
            "El nuevo responsable debe pertenecer al grupo."
        )

    if job.assigned_to_id == new_assignee.pk:
        raise ValidationError(
            "El usuario ya es responsable del trabajo."
        )

    # Cerrar la asignación anterior.
    current_assignment = JobAssignment.objects.get(
        job=job,
        ended_at__isnull=True,
    )

    current_assignment.ended_at = timezone.now()
    current_assignment.save(update_fields=["ended_at"])

    # Crear la nueva asignación.
    JobAssignment.objects.create(
        job=job,
        assigned_to=new_assignee,
        assigned_by=user,
        reason=JobAssignment.Reason.ADMIN_REASSIGNMENT,
    )

    # Actualizar el responsable actual.
    job.assigned_to = new_assignee

    job.save(
        update_fields=["assigned_to", "updated_at"]
    )

    return job


@transaction.atomic
def create_template_photo(
    *,
    template,
    title,
    instructions="",
    stage,
    is_required=True,
):
    template = Template.objects.select_for_update().get(
        pk=template.pk,
        deleted_at__isnull=True,
    )

    last_position = template.photos.aggregate(
        last=Max("position")
    )["last"] or 0

    photo = TemplatePhoto.objects.create(
        template=template,
        position=last_position + 1,
        title=title,
        instructions=instructions,
        stage=stage,
        is_required=is_required,
    )

    return photo


@transaction.atomic
def delete_template_photo(*, photo):

    template = Template.objects.select_for_update().get(
        pk=photo.template_id,
        deleted_at__isnull=True,
    )

    photo = template.photos.get(pk=photo.pk)

    deleted_position = photo.position

    photo.delete()

    remaining_photos = template.photos.filter(
        position__gt=deleted_position
    ).order_by("position")

    for remaining_photo in remaining_photos:
        remaining_photo.position -= 1

        remaining_photo.save(
            update_fields=["position", "updated_at"]
        )


@transaction.atomic
def move_template_photo(*, photo, direction):

    if direction not in ("up", "down"):
        raise ValidationError(
            "Dirección de movimiento inválida."
        )

    template = Template.objects.select_for_update().get(
        pk=photo.template_id,
        deleted_at__isnull=True,
    )

    photo = template.photos.get(pk=photo.pk)

    if direction == "up":
        target = template.photos.filter(
            position__lt=photo.position,
        ).order_by("-position").first()

    else:
        target = template.photos.filter(
            position__gt=photo.position,
        ).order_by("position").first()

    # Ya se encuentra en el extremo correspondiente.
    if target is None:
        return photo

    original_position = photo.position
    target_position = target.position

    temporary_position = template.photos.aggregate(
        last=Max("position")
    )["last"] + 1

    # Mover temporalmente la primera fotografía.
    photo.position = temporary_position
    photo.save(
        update_fields=["position", "updated_at"]
    )

    # Mover la segunda fotografía.
    target.position = original_position
    target.save(
        update_fields=["position", "updated_at"]
    )

    # Colocar la primera en su posición definitiva.
    photo.position = target_position
    photo.save(
        update_fields=["position", "updated_at"]
    )

    return photo
