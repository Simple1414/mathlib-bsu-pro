"""Render.com deployment support: DATABASE_URL, hostname, admin bootstrap, blueprint."""
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest import mock

import yaml
from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from accounts.models import User

BASE_DIR = Path(settings.BASE_DIR)


def run_settings(code, **env):
    clean = {k: v for k, v in os.environ.items()
             if not k.startswith(('DB_', 'DATABASE_URL', 'RENDER', 'SECRET', 'DEBUG'))}
    clean.update(env)
    return subprocess.run([sys.executable, '-c', code], cwd=BASE_DIR, env=clean,
                          capture_output=True, text=True)


class RenderSettingsTests(SimpleTestCase):
    def test_database_url_is_parsed(self):
        result = run_settings(
            'import config.settings as s; d = s.DATABASES["default"]; '
            'print(d["NAME"], d["USER"], d["PASSWORD"], d["HOST"], d["PORT"])',
            DEBUG='True', DATABASE_URL='postgresql://mathlib_user:p%40ss@dpg-abc-a/mathlib_bsu',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ['mathlib_bsu', 'mathlib_user', 'p@ss', 'dpg-abc-a', '5432'])

    def test_render_hostname_is_allowed_and_csrf_trusted(self):
        result = run_settings(
            'import config.settings as s; print(s.ALLOWED_HOSTS[-1], s.CSRF_TRUSTED_ORIGINS[-1])',
            DEBUG='False', SECRET_KEY='a' * 44, RENDER_EXTERNAL_HOSTNAME='mathlib-bsu.onrender.com',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ['mathlib-bsu.onrender.com', 'https://mathlib-bsu.onrender.com'])

    def test_render_generated_secret_length_is_accepted(self):
        # Render's generateValue produces a 256-bit base64 value (44 characters).
        result = run_settings('import config.settings', DEBUG='False', SECRET_KEY='Q' * 44)
        self.assertEqual(result.returncode, 0, result.stderr)


class BlueprintTests(SimpleTestCase):
    def test_render_yaml_is_consistent(self):
        blueprint = yaml.safe_load((BASE_DIR / 'render.yaml').read_text())
        web = blueprint['services'][0]
        env = {item['key']: item for item in web['envVars']}
        self.assertEqual(env['DATABASE_URL']['fromDatabase']['name'], blueprint['databases'][0]['name'])
        self.assertTrue(env['SECRET_KEY']['generateValue'])
        self.assertEqual(env['DEBUG']['value'], 'False')
        self.assertEqual(env['BEHIND_PROXY']['value'], 'True')
        for key in ('ADMIN_USERNAME', 'ADMIN_PASSWORD'):
            self.assertFalse(env[key]['sync'], key)  # never stored in the repo
        self.assertIn('collectstatic', web['buildCommand'])
        self.assertIn('migrate', web['startCommand'])
        self.assertIn('$PORT', web['startCommand'])


class EnsureAdminTests(TestCase):
    def run_cmd(self, **env):
        out = StringIO()
        with mock.patch.dict(os.environ, env, clear=False):
            call_command('ensure_admin', stdout=out, stderr=out)
        return out.getvalue()

    def test_creates_admin_who_can_log_in(self):
        self.run_cmd(ADMIN_USERNAME='boss', ADMIN_PASSWORD='Very-Strong-Pass-1', ADMIN_EMAIL='a@b.tj')
        user = User.objects.get(username='boss')
        self.assertTrue(user.is_superuser and user.is_staff and user.is_admin_role())
        self.assertTrue(self.client.login(username='boss', password='Very-Strong-Pass-1'))

    def test_is_idempotent_and_updates_password(self):
        self.run_cmd(ADMIN_USERNAME='boss', ADMIN_PASSWORD='Very-Strong-Pass-1')
        self.run_cmd(ADMIN_USERNAME='boss', ADMIN_PASSWORD='Another-Strong-Pass-2')
        self.assertEqual(User.objects.filter(username='boss').count(), 1)
        self.assertTrue(User.objects.get(username='boss').check_password('Another-Strong-Pass-2'))

    def test_skips_without_env_or_with_weak_password(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ADMIN_USERNAME', None)
            os.environ.pop('ADMIN_PASSWORD', None)
            self.assertIn('skipping', self.run_cmd())
        self.assertIn('skipping', self.run_cmd(ADMIN_USERNAME='boss', ADMIN_PASSWORD='short'))
        self.assertFalse(User.objects.filter(username='boss').exists())
