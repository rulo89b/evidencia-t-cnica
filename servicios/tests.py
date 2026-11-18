
from django.core.exceptions import PermissionDenied
from .services import create_job, reassign_job
from .models import Job, JobPhotoSlot, JobAssignment
from grupos.services import create_group
from grupos.models import GroupMember
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone


from .models import Template, TemplatePhoto

User = get_user_model()


class TemplateTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="test12345",
        )

        self.template = Template.objects.create(
            owner=self.user,
            name="Instalación",
            description="Instalación de equipo de microondas",
        )

    def test_create_template(self):
        self.assertEqual(self.template.name, "Instalación")
        self.assertEqual(self.template.owner, self.user)
        self.assertIsNone(self.template.deleted_at)

    def test_template_owner(self):
        other_user = User.objects.create_user(
            username="otro_tecnico",
            email="otro@example.com",
            password="test12345",
        )

        Template.objects.create(
            owner=other_user,
            name="Desmontaje",
        )

        templates = Template.objects.filter(owner=self.user)

        self.assertEqual(templates.count(), 1)
        self.assertEqual(templates.first(), self.template)

    def test_soft_delete_template(self):
        photo = TemplatePhoto.objects.create(
            template=self.template,
            position=1,
            title="Vista general",
            stage=TemplatePhoto.Stage.BEFORE,
        )

        self.template.deleted_at = timezone.now()
        self.template.save()

        self.assertTrue(
            Template.objects.filter(pk=self.template.pk).exists()
        )

        self.assertFalse(
            Template.objects.filter(
                pk=self.template.pk,
                deleted_at__isnull=True,
            ).exists()
        )

        self.assertTrue(
            TemplatePhoto.objects.filter(pk=photo.pk).exists()
        )


class TemplatePhotoTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="test12345",
        )

        self.template = Template.objects.create(
            owner=self.user,
            name="Instalación",
        )

        self.photo = TemplatePhoto.objects.create(
            template=self.template,
            position=1,
            title="Fachada",
            stage=TemplatePhoto.Stage.BEFORE,
        )

    def test_create_template_photo(self):
        self.assertEqual(self.photo.template, self.template)
        self.assertEqual(self.photo.position, 1)
        self.assertTrue(self.photo.is_required)

    def test_duplicate_position_same_template(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TemplatePhoto.objects.create(
                    template=self.template,
                    position=1,
                    title="Otra fotografía",
                    stage=TemplatePhoto.Stage.AFTER,
                )

    def test_same_position_different_template(self):
        other_template = Template.objects.create(
            owner=self.user,
            name="Desmontaje",
        )

        photo = TemplatePhoto.objects.create(
            template=other_template,
            position=1,
            title="Vista general",
            stage=TemplatePhoto.Stage.BEFORE,
        )

        self.assertEqual(photo.position, 1)

    def test_invalid_position(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TemplatePhoto.objects.create(
                    template=self.template,
                    position=0,
                    title="Fotografía inválida",
                    stage=TemplatePhoto.Stage.BEFORE,
                )

    def test_invalid_stage(self):
        photo = TemplatePhoto(
            template=self.template,
            position=2,
            title="Fotografía inválida",
            stage="invalid",
        )

        with self.assertRaises(ValidationError):
            photo.full_clean()


class JobTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
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

        GroupMember.objects.create(
            group=self.group,
            user=self.member,
        )

        self.template = Template.objects.create(
            owner=self.admin,
            name="Instalación",
        )

        self.photo = TemplatePhoto.objects.create(
            template=self.template,
            position=1,
            title="Fachada",
            stage=TemplatePhoto.Stage.BEFORE,
        )

    def create_individual_job(self):
        return create_job(
            user=self.admin,
            template=self.template,
            site_name="Sitio Norte",
        )

    def create_group_job(self):
        return create_job(
            user=self.admin,
            template=self.template,
            site_name="Sitio Norte",
            group=self.group,
            assigned_to=self.member,
        )

    def test_create_individual_job(self):
        job = self.create_individual_job()

        self.assertEqual(job.created_by, self.admin)
        self.assertEqual(job.assigned_to, self.admin)
        self.assertIsNone(job.group)
        self.assertEqual(job.status, Job.Status.PENDING)

    def test_create_group_job(self):
        job = self.create_group_job()

        self.assertEqual(job.group, self.group)
        self.assertEqual(job.assigned_to, self.member)

    def test_photo_slots_are_created(self):
        job = self.create_individual_job()

        slot = job.photo_slots.get()

        self.assertEqual(slot.title, self.photo.title)
        self.assertEqual(slot.position, self.photo.position)
        self.assertEqual(slot.stage, self.photo.stage)
        self.assertEqual(slot.template_photo, self.photo)
        self.assertFalse(slot.is_captured)

    def test_template_changes_do_not_affect_job(self):
        job = self.create_individual_job()

        self.photo.title = "Nuevo título"
        self.photo.save()

        slot = job.photo_slots.get()

        self.assertEqual(slot.title, "Fachada")

    def test_initial_assignment_is_created(self):
        job = self.create_individual_job()

        assignment = job.assignments.get()

        self.assertEqual(assignment.assigned_to, self.admin)
        self.assertEqual(
            assignment.reason,
            JobAssignment.Reason.INITIAL,
        )
        self.assertIsNone(assignment.ended_at)

    def test_cannot_use_another_users_template(self):
        with self.assertRaises(PermissionDenied):
            create_job(
                user=self.member,
                template=self.template,
                site_name="Sitio Norte",
            )

    def test_cannot_use_deleted_template(self):
        self.template.deleted_at = timezone.now()
        self.template.save()

        with self.assertRaises(ValidationError):
            self.create_individual_job()

    def test_reassign_job(self):
        job = self.create_group_job()

        previous_assignment = job.assignments.get()

        reassign_job(
            job=job,
            user=self.admin,
            new_assignee=self.admin,
        )

        job.refresh_from_db()
        previous_assignment.refresh_from_db()

        self.assertEqual(job.assigned_to, self.admin)
        self.assertIsNotNone(previous_assignment.ended_at)
        self.assertEqual(job.assignments.count(), 2)

        current_assignment = job.assignments.get(
            ended_at__isnull=True,
        )

        self.assertEqual(
            current_assignment.assigned_to,
            self.admin,
        )

        self.assertEqual(
            current_assignment.reason,
            JobAssignment.Reason.ADMIN_REASSIGNMENT,
        )

    def test_cannot_have_two_active_assignments(self):
        job = self.create_individual_job()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JobAssignment.objects.create(
                    job=job,
                    assigned_to=self.member,
                    assigned_by=self.admin,
                    reason=JobAssignment.Reason.INITIAL,
                )

    def test_member_cannot_reassign_job(self):
        job = self.create_group_job()

        with self.assertRaises(PermissionDenied):
            reassign_job(
                job=job,
                user=self.member,
                new_assignee=self.admin,
            )
