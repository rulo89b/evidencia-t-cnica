
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from .services import create_job, reassign_job, create_template_photo
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


class TemplateViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="test12345",
        )

        self.other_user = User.objects.create_user(
            username="otro",
            email="otro@example.com",
            password="test12345",
        )

        self.template = Template.objects.create(
            owner=self.user,
            name="Instalación",
        )

        self.other_template = Template.objects.create(
            owner=self.other_user,
            name="Plantilla ajena",
        )

        self.client.force_login(self.user)

    def test_template_list_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("servicios:template_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_list_only_own_active_templates(self):
        Template.objects.create(
            owner=self.user,
            name="Plantilla eliminada",
            deleted_at=timezone.now(),
        )

        response = self.client.get(
            reverse("servicios:template_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Instalación")
        self.assertNotContains(response, "Plantilla ajena")
        self.assertNotContains(response, "Plantilla eliminada")

    def test_create_template(self):
        response = self.client.post(
            reverse("servicios:template_create"),
            {
                "name": "Desmontaje",
                "description": "Retiro de equipos",
            },
        )

        self.assertRedirects(
            response,
            reverse("servicios:template_list"),
        )

        template = Template.objects.get(
            name="Desmontaje"
        )

        self.assertEqual(template.owner, self.user)

    def test_update_own_template(self):
        response = self.client.post(
            reverse(
                "servicios:template_update",
                args=[self.template.pk],
            ),
            {
                "name": "Instalación modificada",
                "description": "Nueva descripción",
            },
        )

        self.assertRedirects(
            response,
            reverse("servicios:template_list"),
        )

        self.template.refresh_from_db()

        self.assertEqual(
            self.template.name,
            "Instalación modificada",
        )

    def test_cannot_update_another_users_template(self):
        response = self.client.post(
            reverse(
                "servicios:template_update",
                args=[self.other_template.pk],
            ),
            {
                "name": "Cambio no autorizado",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.other_template.refresh_from_db()

        self.assertEqual(
            self.other_template.name,
            "Plantilla ajena",
        )

    def test_soft_delete_template(self):
        response = self.client.post(
            reverse(
                "servicios:template_delete",
                args=[self.template.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("servicios:template_list"),
        )

        self.template.refresh_from_db()

        self.assertIsNotNone(self.template.deleted_at)

    def test_cannot_delete_another_users_template(self):
        response = self.client.post(
            reverse(
                "servicios:template_delete",
                args=[self.other_template.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.other_template.refresh_from_db()

        self.assertIsNone(
            self.other_template.deleted_at
        )

    def test_delete_confirmation_does_not_delete(self):
        response = self.client.get(
            reverse(
                "servicios:template_delete",
                args=[self.template.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.template.refresh_from_db()

        self.assertIsNone(self.template.deleted_at)

    def test_cannot_edit_deleted_template(self):
        self.template.deleted_at = timezone.now()
        self.template.save()

        response = self.client.get(
            reverse(
                "servicios:template_update",
                args=[self.template.pk],
            )
        )

        self.assertEqual(response.status_code, 404)


class TemplatePhotoViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="test12345",
        )

        self.other_user = User.objects.create_user(
            username="otro",
            email="otro@example.com",
            password="test12345",
        )

        self.template = Template.objects.create(
            owner=self.user,
            name="Instalación MW",
        )

        self.first_photo = create_template_photo(
            template=self.template,
            title="Fachada",
            stage=TemplatePhoto.Stage.BEFORE,
        )

        self.second_photo = create_template_photo(
            template=self.template,
            title="Antena instalada",
            stage=TemplatePhoto.Stage.AFTER,
        )

        self.third_photo = create_template_photo(
            template=self.template,
            title="Vista final",
            stage=TemplatePhoto.Stage.AFTER,
        )

        self.detail_url = reverse(
            "servicios:template_detail",
            args=[self.template.pk],
        )

        self.client.force_login(self.user)

    def photo_url(self, action, photo):
        return reverse(
            f"servicios:template_photo_{action}",
            args=[self.template.pk, photo.pk],
        )

    def test_template_detail(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fachada")
        self.assertContains(response, "Antena instalada")
        self.assertContains(response, "Vista final")

    def test_create_photo(self):
        response = self.client.post(
            reverse(
                "servicios:template_photo_create",
                args=[self.template.pk],
            ),
            {
                "title": "Gabinete",
                "instructions": "Mostrar conexiones",
                "stage": "during",
                "is_required": "on",
            },
        )

        self.assertRedirects(response, self.detail_url)

        photo = self.template.photos.get(
            title="Gabinete"
        )

        self.assertEqual(photo.position, 4)
        self.assertTrue(photo.is_required)

    def test_update_photo(self):
        response = self.client.post(
            self.photo_url("update", self.first_photo),
            {
                "title": "Fachada modificada",
                "instructions": "Vista completa",
                "stage": "before",
            },
        )

        self.assertRedirects(response, self.detail_url)

        self.first_photo.refresh_from_db()

        self.assertEqual(
            self.first_photo.title,
            "Fachada modificada",
        )

        self.assertFalse(self.first_photo.is_required)
        self.assertEqual(self.first_photo.position, 1)

    def test_delete_photo_reorders_positions(self):
        response = self.client.post(
            self.photo_url("delete", self.second_photo)
        )

        self.assertRedirects(response, self.detail_url)

        self.assertFalse(
            TemplatePhoto.objects.filter(
                pk=self.second_photo.pk
            ).exists()
        )

        self.third_photo.refresh_from_db()

        self.assertEqual(self.third_photo.position, 2)

    def test_move_photo_up(self):
        response = self.client.post(
            self.photo_url("move", self.second_photo),
            {"direction": "up"},
        )

        self.assertRedirects(response, self.detail_url)

        self.first_photo.refresh_from_db()
        self.second_photo.refresh_from_db()

        self.assertEqual(self.first_photo.position, 2)
        self.assertEqual(self.second_photo.position, 1)

    def test_move_photo_down(self):
        response = self.client.post(
            self.photo_url("move", self.first_photo),
            {"direction": "down"},
        )

        self.assertRedirects(response, self.detail_url)

        self.first_photo.refresh_from_db()
        self.second_photo.refresh_from_db()

        self.assertEqual(self.first_photo.position, 2)
        self.assertEqual(self.second_photo.position, 1)

    def test_cannot_move_first_photo_up(self):
        response = self.client.post(
            self.photo_url("move", self.first_photo),
            {"direction": "up"},
        )

        self.assertRedirects(response, self.detail_url)

        self.first_photo.refresh_from_db()

        self.assertEqual(self.first_photo.position, 1)

    def test_cannot_move_last_photo_down(self):
        response = self.client.post(
            self.photo_url("move", self.third_photo),
            {"direction": "down"},
        )

        self.assertRedirects(response, self.detail_url)

        self.third_photo.refresh_from_db()

        self.assertEqual(self.third_photo.position, 3)

    def test_invalid_move_direction(self):
        response = self.client.post(
            self.photo_url("move", self.first_photo),
            {"direction": "invalid"},
        )

        self.assertEqual(response.status_code, 400)

    def test_cannot_access_another_users_template(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 404)

    def test_cannot_modify_another_users_photos(self):
        self.client.force_login(self.other_user)

        for action in ("update", "delete", "move"):
            with self.subTest(action=action):
                response = self.client.post(
                    self.photo_url(
                        action,
                        self.first_photo,
                    ),
                    {"direction": "down"},
                )

                self.assertEqual(
                    response.status_code,
                    404,
                )

        self.first_photo.refresh_from_db()

        self.assertEqual(self.first_photo.position, 1)
        self.assertEqual(self.first_photo.title, "Fachada")

    def test_deleting_photo_preserves_job_slot(self):
        job = create_job(
            user=self.user,
            template=self.template,
            site_name="Sitio Norte",
        )

        slot = job.photo_slots.get(position=1)

        response = self.client.post(
            self.photo_url("delete", self.first_photo)
        )

        self.assertRedirects(response, self.detail_url)

        slot.refresh_from_db()

        self.assertIsNone(slot.template_photo_id)
        self.assertEqual(slot.title, "Fachada")
        self.assertEqual(slot.position, 1)
        self.assertEqual(job.photo_slots.count(), 3)
