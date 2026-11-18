
import uuid
import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


def generate_invitation_token():
    return secrets.token_urlsafe(32)


class Group(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_groups",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        MEMBER = "member", "Miembro"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="members",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="group_memberships",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_group_member",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.group.name}"


class GroupInvitation(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        ACCEPTED = "accepted", "Aceptada"
        REJECTED = "rejected", "Rechazada"
        EXPIRED = "expired", "Expirada"
        REVOKED = "revoked", "Revocada"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_group_invitations",
    )

    invited_email = models.EmailField(
        max_length=255,
        blank=True,
    )

    invited_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_group_invitations",
    )

    token = models.CharField(
        max_length=255,
        unique=True,
        default=generate_invitation_token,
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    ~Q(invited_email="")
                    | ~Q(invited_phone="")
                    | Q(invited_user__isnull=False)
                ),
                name="group_invitation_has_recipient",
            ),
        ]

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Invitación a {self.group.name}"
