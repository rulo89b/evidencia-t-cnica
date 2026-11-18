
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
