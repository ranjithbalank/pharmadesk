"""Tests for the single shared login (SEC-1)."""
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('counter', password='pharmadesk')

    def test_login_returns_token(self):
        resp = self.client.post('/api/auth/login/',
                                {'username': 'counter', 'password': 'pharmadesk'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())

    def test_login_rejects_bad_password(self):
        resp = self.client.post('/api/auth/login/',
                                {'username': 'counter', 'password': 'wrong'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_protected_endpoint_blocks_anonymous(self):
        resp = self.client.get('/api/medicines/')
        self.assertEqual(resp.status_code, 401)

    def test_token_grants_access(self):
        token = self.client.post('/api/auth/login/',
                                 {'username': 'counter', 'password': 'pharmadesk'},
                                 format='json').json()['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/medicines/')
        self.assertEqual(resp.status_code, 200)

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/auth/change-password/',
                                {'current_password': 'pharmadesk', 'new_password': 'newpass'},
                                format='json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass'))
