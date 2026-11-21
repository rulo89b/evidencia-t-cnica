from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Group, GroupMember, GroupInvitation


User = get_user_model()


@transaction.atomic
def create_group(*, user, name, description=""):
    group = Group.objects.create(
        name=name,
        description=description,
        created_by=user,
    )

    GroupMember.objects.create(
        group=group,
        user=user,
        role=GroupMember.Role.ADMIN,
    )

    return group


@transaction.atomic
def invite_user_to_group(*, group, invited_by, email):

    is_admin = GroupMember.objects.filter(
        group=group,
        user=invited_by,
        role=GroupMember.Role.ADMIN,
    ).exists()

    if not is_admin:
        raise PermissionDenied(
            "Solo un administrador puede invitar usuarios."
        )

    email = email.strip().lower()

    try:
        invited_user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        raise ValidationError(
            "No existe un usuario registrado con ese correo."
        )
    except User.MultipleObjectsReturned:
        raise ValidationError(
            "El correo corresponde a más de una cuenta."
        )

    if GroupMember.objects.filter(
        group=group,
        user=invited_user,
    ).exists():
        raise ValidationError(
            "El usuario ya pertenece al grupo."
        )

    now = timezone.now()

    # Marcar como vencidas las invitaciones pendientes antiguas.
    GroupInvitation.objects.filter(
        group=group,
        invited_user=invited_user,
        status=GroupInvitation.Status.PENDING,
        expires_at__lte=now,
    ).update(
        status=GroupInvitation.Status.EXPIRED,
    )

    if GroupInvitation.objects.filter(
        group=group,
        invited_user=invited_user,
        status=GroupInvitation.Status.PENDING,
        expires_at__gt=now,
    ).exists():
        raise ValidationError(
            "Ya existe una invitación pendiente para este usuario."
        )

    invitation = GroupInvitation.objects.create(
        group=group,
        invited_by=invited_by,
        invited_user=invited_user,
        invited_email=invited_user.email,
        expires_at=now + timedelta(days=7),
    )

    return invitation


@transaction.atomic
def accept_group_invitation(*, invitation, user):

    invitation = GroupInvitation.objects.select_for_update().get(
        pk=invitation.pk
    )

    if invitation.invited_user_id != user.pk:
        raise PermissionDenied(
            "Esta invitación no te pertenece."
        )

    if invitation.status != GroupInvitation.Status.PENDING:
        raise ValidationError(
            "La invitación ya no está pendiente."
        )

    if invitation.is_expired:
        invitation.status = GroupInvitation.Status.EXPIRED
        invitation.save(update_fields=["status"])

        raise ValidationError(
            "La invitación ha vencido."
        )

    if GroupMember.objects.filter(
        group=invitation.group,
        user=user,
    ).exists():
        raise ValidationError(
            "Ya perteneces a este grupo."
        )

    membership = GroupMember.objects.create(
        group=invitation.group,
        user=user,
        role=GroupMember.Role.MEMBER,
    )

    invitation.status = GroupInvitation.Status.ACCEPTED
    invitation.responded_at = timezone.now()
    invitation.save(
        update_fields=["status", "responded_at"]
    )

    return membership


@transaction.atomic
def reject_group_invitation(*, invitation, user):

    invitation = GroupInvitation.objects.select_for_update().get(
        pk=invitation.pk
    )

    if invitation.invited_user_id != user.pk:
        raise PermissionDenied(
            "Esta invitación no te pertenece."
        )

    if invitation.status != GroupInvitation.Status.PENDING:
        raise ValidationError(
            "La invitación ya no está pendiente."
        )

    if invitation.is_expired:
        raise ValidationError(
            "La invitación ha vencido."
        )

    invitation.status = GroupInvitation.Status.REJECTED
    invitation.responded_at = timezone.now()

    invitation.save(
        update_fields=["status", "responded_at"]
    )

    return invitation
