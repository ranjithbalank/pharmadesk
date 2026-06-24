"""Shared base for tests that hit the API, which now requires a login (SEC-1)."""
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthedAPITestCase(APITestCase):
    """Authenticates the test client so protected endpoints are reachable."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('tester', password='secret')
        self.client.force_authenticate(self.user)
