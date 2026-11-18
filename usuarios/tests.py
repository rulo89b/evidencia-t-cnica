
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tecnico",
            email="tecnico@example.com",
            password="Test12345!",
        )

    def test_register_page(self):
        response = self.client.get(
            reverse("usuarios:register")
        )

        self.assertEqual(response.status_code, 200)

    def test_user_registration(self):
        response = self.client.post(
            reverse("usuarios:register"),
            {
                "username": "nuevo_tecnico",
                "email": "nuevo@example.com",
                "phone": "",
                "password1": "SecureTest123!",
                "password2": "SecureTest123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("usuarios:login"),
        )

        user = User.objects.get(
            username="nuevo_tecnico"
        )

        self.assertTrue(
            user.check_password("SecureTest123!")
        )

    def test_password_mismatch(self):
        response = self.client.post(
            reverse("usuarios:register"),
            {
                "username": "nuevo_tecnico",
                "email": "nuevo@example.com",
                "phone": "",
                "password1": "SecureTest123!",
                "password2": "DifferentTest123!",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            User.objects.filter(
                username="nuevo_tecnico"
            ).exists()
        )

    def test_login_success(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": "tecnico",
                "password": "Test12345!",
            },
        )

        self.assertRedirects(
            response,
            reverse("usuarios:home"),
        )

        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_invalid_password(self):
        response = self.client.post(
            reverse("usuarios:login"),
            {
                "username": "tecnico",
                "password": "incorrecta",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_home_requires_authentication(self):
        response = self.client.get(
            reverse("usuarios:home")
        )

        self.assertRedirects(
            response,
            reverse("usuarios:login") + "?next=/",
        )

    def test_authenticated_user_can_access_home(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("usuarios:home")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "tecnico")

    def test_logout(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("usuarios:logout")
        )

        self.assertRedirects(
            response,
            reverse("usuarios:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )
