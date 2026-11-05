"""Create or update the site administrator from environment variables.

Used on hosts without shell access (e.g. Render free plan) where
`createsuperuser` cannot be run interactively. Safe to run on every start.

    ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL (optional)
"""
import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Админро аз тағйирёбандаҳои муҳит (ADMIN_USERNAME, ADMIN_PASSWORD) месозад.'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', '').strip()
        password = os.getenv('ADMIN_PASSWORD', '')
        if not username or not password:
            self.stdout.write('ensure_admin: ADMIN_USERNAME/ADMIN_PASSWORD not set; skipping.')
            return
        if len(password) < 10:
            self.stderr.write('ensure_admin: ADMIN_PASSWORD must be at least 10 characters; skipping.')
            return

        user, created = User.objects.get_or_create(username=username)
        user.email = os.getenv('ADMIN_EMAIL', user.email or '')
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if created or not user.check_password(password):
            user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"ensure_admin: admin '{username}' {'created' if created else 'updated'}."
        ))
