
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Group, GroupMember, GroupInvitation
from .services import (
    create_group,
    invite_user_to_group,
    accept_group_invitation,
    reject_group_invitation,
)

User = get_user_model()


class GroupTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="administrador",
            email="admin@example.com",
            password="test12345",
        )

    def test_create_group(self):
        group = Group.objects.create(
            name="Instalaciones Norte",
            description="Grupo de trabajo técnico",
            created_by=self.user,
        )

        self.assertEqual(group.name, "Instalaciones Norte")
        self.assertEqual(group.created_by, self.user)

    def test_creator_becomes_admin(self):
        group = create_group(
            user=self.user,
            name="Instalaciones Norte",
        )

        membership = GroupMember.objects.get(
            group=group,
            user=self.user,
        )

        self.assertEqual(
            membership.role,
            GroupMember.Role.ADMIN,
        )


class GroupMemberTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="administrador",
            email="admin@example.com",
            password="test12345",
        )

        self.member = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="test12345",
        )

        self.group = create_group(
            user=self.admin,
            name="Instalaciones Norte",
        )

    def test_add_member(self):
        membership = GroupMember.objects.create(
            group=self.group,
            user=self.member,
        )

        self.assertEqual(membership.group, self.group)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(
            membership.role,
            GroupMember.Role.MEMBER,
        )

    def test_duplicate_membership(self):
        GroupMember.objects.create(
            group=self.group,
            user=self.member,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GroupMember.objects.create(
                    group=self.group,
                    user=self.member,
                )

    def test_different_roles_in_different_groups(self):
        other_group = create_group(
            user=self.member,
            name="Mantenimiento Sur",
        )

        first_membership = GroupMember.objects.create(
            group=self.group,
            user=self.member,
            role=GroupMember.Role.MEMBER,
        )

        second_membership = GroupMember.objects.get(
            group=other_group,
            user=self.member,
        )

        self.assertEqual(
            first_membership.role,
            GroupMember.Role.MEMBER,
        )

        self.assertEqual(
            second_membership.role,
            GroupMember.Role.ADMIN,
        )

    def test_invalid_role(self):
        membership = GroupMember(
            group=self.group,
            user=self.member,
            role="invalid",
        )

        with self.assertRaises(ValidationError):
            membership.full_clean()


class GroupInvitationTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="administrador",
            email="admin@example.com",
            password="test12345",
        )

        self.group = create_group(
            user=self.admin,
            name="Instalaciones Norte",
        )

    def test_create_invitation(self):
        invitation = GroupInvitation.objects.create(
            group=self.group,
            invited_by=self.admin,
            invited_email="tecnico@example.com",
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.assertEqual(invitation.group, self.group)
        self.assertEqual(invitation.invited_by, self.admin)
        self.assertEqual(
            invitation.status,
            GroupInvitation.Status.PENDING,
        )
        self.assertTrue(invitation.token)
        self.assertIsNone(invitation.responded_at)

    def test_invitation_without_recipient(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GroupInvitation.objects.create(
                    group=self.group,
                    invited_by=self.admin,
                    expires_at=timezone.now() + timedelta(days=7),
                )

    def test_expired_invitation(self):
        invitation = GroupInvitation.objects.create(
            group=self.group,
            invited_by=self.admin,
            invited_email="tecnico@example.com",
            expires_at=timezone.now() - timedelta(days=1),
        )

        self.assertTrue(invitation.is_expired)

    def test_valid_invitation(self):
        invitation = GroupInvitation.objects.create(
            group=self.group,
            invited_by=self.admin,
            invited_email="tecnico@example.com",
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.assertFalse(invitation.is_expired)

    def test_unique_invitation_tokens(self):
        first = GroupInvitation.objects.create(
            group=self.group,
            invited_by=self.admin,
            invited_email="tecnico1@example.com",
            expires_at=timezone.now() + timedelta(days=7),
        )

        second = GroupInvitation.objects.create(
            group=self.group,
            invited_by=self.admin,
            invited_email="tecnico2@example.com",
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.assertNotEqual(first.token, second.token)


class GroupViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin_grupo",
            email="admin_grupo@example.com",
            password="Test12345!",
        )

        self.member = User.objects.create_user(
            username="miembro_grupo",
            email="miembro_grupo@example.com",
            password="Test12345!",
        )

        self.outsider = User.objects.create_user(
            username="externo_grupo",
            email="externo_grupo@example.com",
            password="Test12345!",
        )

        self.group = create_group(
            user=self.user,
            name="Cuadrilla Norte",
            description="Instalaciones MW",
        )

        GroupMember.objects.create(
            group=self.group,
            user=self.member,
            role=GroupMember.Role.MEMBER,
        )

        self.detail_url = reverse(
            "grupos:group_detail",
            args=[self.group.pk],
        )

        self.update_url = reverse(
            "grupos:group_update",
            args=[self.group.pk],
        )

        self.client.force_login(self.user)

    def test_group_list_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("grupos:group_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_group_list_shows_memberships(self):
        response = self.client.get(
            reverse("grupos:group_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuadrilla Norte")

    def test_create_group_page(self):
        response = self.client.get(
            reverse("grupos:group_create")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crear grupo")

    def test_create_group_assigns_admin(self):
        response = self.client.post(
            reverse("grupos:group_create"),
            {
                "name": "Cuadrilla Sur",
                "description": "Mantenimiento",
            },
        )

        group = Group.objects.get(
            name="Cuadrilla Sur"
        )

        self.assertRedirects(
            response,
            reverse(
                "grupos:group_detail",
                args=[group.pk],
            ),
        )

        self.assertEqual(group.created_by, self.user)

        membership = GroupMember.objects.get(
            group=group,
            user=self.user,
        )

        self.assertEqual(
            membership.role,
            GroupMember.Role.ADMIN,
        )

    def test_group_detail_shows_members(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin_grupo")
        self.assertContains(response, "miembro_grupo")

    def test_member_can_view_group(self):
        self.client.force_login(self.member)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuadrilla Norte")

    def test_outsider_cannot_view_group(self):
        self.client.force_login(self.outsider)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 404)

    def test_admin_can_update_group(self):
        response = self.client.post(
            self.update_url,
            {
                "name": "Cuadrilla Actualizada",
                "description": "Nueva descripción",
            },
        )

        self.assertRedirects(
            response,
            self.detail_url,
        )

        self.group.refresh_from_db()

        self.assertEqual(
            self.group.name,
            "Cuadrilla Actualizada",
        )

        self.assertEqual(
            self.group.description,
            "Nueva descripción",
        )

    def test_member_cannot_update_group(self):
        self.client.force_login(self.member)

        response = self.client.post(
            self.update_url,
            {
                "name": "Cambio no autorizado",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.group.refresh_from_db()

        self.assertEqual(
            self.group.name,
            "Cuadrilla Norte",
        )

    def test_outsider_cannot_update_group(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            self.update_url,
            {
                "name": "Cambio externo",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.group.refresh_from_db()

        self.assertEqual(
            self.group.name,
            "Cuadrilla Norte",
        )


class GroupInvitationViewTests(TestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin_invitaciones",
            email="admin_inv@example.com",
            password="Test12345!",
        )

        self.invited_user = User.objects.create_user(
            username="invitado",
            email="invitado@example.com",
            password="Test12345!",
        )

        self.outsider = User.objects.create_user(
            username="externo_inv",
            email="externo_inv@example.com",
            password="Test12345!",
        )

        self.group = create_group(
            user=self.admin_user,
            name="Cuadrilla de pruebas",
        )

        self.invite_url = reverse(
            "grupos:group_invite",
            args=[self.group.pk],
        )

        self.list_url = reverse(
            "grupos:invitation_list",
        )

        self.client.force_login(self.admin_user)

    def make_invitation(self):
        return invite_user_to_group(
            group=self.group,
            invited_by=self.admin_user,
            email=self.invited_user.email,
        )

    def test_invitation_list_requires_login(self):
        self.client.logout()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 302)

    def test_admin_can_open_invitation_form(self):
        response = self.client.get(self.invite_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invitar")

    def test_admin_can_invite_registered_user(self):
        response = self.client.post(
            self.invite_url,
            {"email": self.invited_user.email},
        )

        self.assertRedirects(
            response,
            reverse(
                "grupos:group_detail",
                args=[self.group.pk],
            ),
        )

        invitation = GroupInvitation.objects.get(
            group=self.group,
            invited_user=self.invited_user,
        )

        self.assertEqual(
            invitation.status,
            GroupInvitation.Status.PENDING,
        )

    def test_cannot_invite_unknown_email(self):
        response = self.client.post(
            self.invite_url,
            {"email": "desconocido@example.com"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            GroupInvitation.objects.filter(
                group=self.group,
            ).exists()
        )

    def test_cannot_duplicate_pending_invitation(self):
        self.make_invitation()

        response = self.client.post(
            self.invite_url,
            {"email": self.invited_user.email},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            GroupInvitation.objects.filter(
                group=self.group,
                invited_user=self.invited_user,
            ).count(),
            1,
        )

    def test_member_cannot_invite(self):
        GroupMember.objects.create(
            group=self.group,
            user=self.invited_user,
            role=GroupMember.Role.MEMBER,
        )

        self.client.force_login(self.invited_user)

        response = self.client.post(
            self.invite_url,
            {"email": self.outsider.email},
        )

        self.assertEqual(response.status_code, 404)

    def test_outsider_cannot_invite(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            self.invite_url,
            {"email": self.invited_user.email},
        )

        self.assertEqual(response.status_code, 404)

    def test_invited_user_sees_invitation(self):
        self.make_invitation()

        self.client.force_login(self.invited_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Cuadrilla de pruebas",
        )

    def test_accept_invitation_creates_membership(self):
        invitation = self.make_invitation()

        self.client.force_login(self.invited_user)

        response = self.client.post(
            reverse(
                "grupos:invitation_respond",
                args=[invitation.pk],
            ),
            {"action": "accept"},
        )

        self.assertRedirects(response, self.list_url)

        membership = GroupMember.objects.get(
            group=self.group,
            user=self.invited_user,
        )

        self.assertEqual(
            membership.role,
            GroupMember.Role.MEMBER,
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.status,
            GroupInvitation.Status.ACCEPTED,
        )

    def test_reject_invitation(self):
        invitation = self.make_invitation()

        self.client.force_login(self.invited_user)

        self.client.post(
            reverse(
                "grupos:invitation_respond",
                args=[invitation.pk],
            ),
            {"action": "reject"},
        )

        invitation.refresh_from_db()

        self.assertEqual(
            invitation.status,
            GroupInvitation.Status.REJECTED,
        )

        self.assertFalse(
            GroupMember.objects.filter(
                group=self.group,
                user=self.invited_user,
            ).exists()
        )

    def test_outsider_cannot_accept_invitation(self):
        invitation = self.make_invitation()

        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse(
                "grupos:invitation_respond",
                args=[invitation.pk],
            ),
            {"action": "accept"},
        )

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            GroupMember.objects.filter(
                group=self.group,
                user=self.outsider,
            ).exists()
        )

    def test_expired_invitation_cannot_be_accepted(self):
        invitation = self.make_invitation()

        invitation.expires_at = (
            timezone.now() - timedelta(days=1)
        )
        invitation.save(update_fields=["expires_at"])

        self.client.force_login(self.invited_user)

        response = self.client.post(
            reverse(
                "grupos:invitation_respond",
                args=[invitation.pk],
            ),
            {"action": "accept"},
        )

        self.assertRedirects(response, self.list_url)

        self.assertFalse(
            GroupMember.objects.filter(
                group=self.group,
                user=self.invited_user,
            ).exists()
        )
