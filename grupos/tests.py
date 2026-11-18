
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import Group, GroupMember, GroupInvitation
from .services import create_group

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
