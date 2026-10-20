from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase


class AdministrationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username="admin-test")
        cls.admin.groups.add(Group.objects.create(name="admin"))
        cls.provider = User.objects.create_user(username="provider-test")
        cls.provider.groups.add(Group.objects.create(name="data_provider"))
        cls.staff = User.objects.create_user(username="staff-test", is_staff=True)
        cls.superuser = User.objects.create_superuser(
            username="superuser-test", password="test-only-password"
        )
        cls.mixed_case_admin = User.objects.create_user(username="mixed-admin")
        cls.mixed_case_admin.groups.add(Group.objects.create(name="Admin"))

    def requests(self):
        for prefix in ("/api/v1/", "/api/v1/auth/"):
            yield "get", f"{prefix}users/", None
            yield "get", f"{prefix}roles/", None
            yield "post", f"{prefix}roles/", {"name": "unauthorized-role"}
        yield (
            "post",
            "/api/v1/auth/register/",
            {
                "username": "unauthorized-admin",
                "password": "test-only-password",
                "role": "admin",
            },
        )

    def test_anonymous_requests_are_rejected(self):
        for method, path, data in self.requests():
            with self.subTest(method=method, path=path):
                response = getattr(self.client, method)(path, data, format="json")
                self.assertEqual(response.status_code, 401)

    def test_non_admins_cannot_list_or_create_resources(self):
        for user in (self.provider, self.staff):
            self.client.force_authenticate(user=user)
            for method, path, data in self.requests():
                with self.subTest(user=user.username, method=method, path=path):
                    response = getattr(self.client, method)(path, data, format="json")
                    self.assertEqual(response.status_code, 403)
        self.assertFalse(
            get_user_model().objects.filter(username="unauthorized-admin").exists()
        )
        self.assertFalse(Group.objects.filter(name="unauthorized-role").exists())

    def test_admins_and_superusers_can_list_users_and_roles(self):
        for user in (self.admin, self.superuser, self.mixed_case_admin):
            self.client.force_authenticate(user=user)
            for path in ("users/", "roles/", "auth/users/", "auth/roles/"):
                with self.subTest(user=user.username, path=path):
                    response = self.client.get(f"/api/v1/{path}")
                    self.assertEqual(response.status_code, 200)
                    self.assertIsInstance(response.data["data"], list)

    def test_admin_can_create_role_and_register_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/roles/", {"name": "analyst"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "new-analyst",
                "password": "test-only-password",
                "role": "analyst",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username="new-analyst")
        self.assertTrue(user.check_password("test-only-password"))
        self.assertTrue(user.groups.filter(name="analyst").exists())
        self.assertNotIn("password", response.data["data"])

    def test_invalid_and_duplicate_resources_are_rejected(self):
        self.client.force_authenticate(user=self.admin)
        for payload in ({"name": "ADMIN"}, {"name": ""}):
            self.assertEqual(
                self.client.post("/api/v1/roles/", payload).status_code, 400
            )
        for payload in (
            {
                "username": "new-user",
                "password": "test-only-password",
                "role": "missing",
            },
            {
                "username": "admin-test",
                "password": "test-only-password",
                "role": "admin",
            },
            {"username": "new-user", "password": "short", "role": "admin"},
        ):
            self.assertEqual(
                self.client.post("/api/v1/auth/register/", payload).status_code, 400
            )

    def test_current_profile_reports_superuser_flag(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_superuser"])
