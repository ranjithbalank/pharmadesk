"""Ensure the single shared login exists (SEC-1). Creates the default user on
first setup if no users exist. Idempotent — safe to run on every launch.

Credentials default to admin / pharmadesk (override with PHARMADESK_USER /
PHARMADESK_PASSWORD). Change the password after go-live from the app.
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create the default shared login if no users exist.'

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write('Login already configured — no change.')
            return
        username = settings.DEFAULT_LOGIN_USERNAME
        password = settings.DEFAULT_LOGIN_PASSWORD
        User.objects.create_superuser(username=username, password=password, email='')
        self.stdout.write(self.style.SUCCESS(
            f'Created shared login "{username}" (password "{password}"). '
            'Change the password after go-live.'
        ))
