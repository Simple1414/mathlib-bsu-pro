"""Media exposure, SECRET_KEY enforcement and static storage configuration."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings

BASE_DIR = Path(settings.BASE_DIR)
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PublicMediaTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for rel in ('covers/c.png', 'avatars/a.png', 'books/secret.pdf', 'articles/secret.pdf'):
            path = Path(MEDIA_ROOT, rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'data')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        if not settings.SERVE_MEDIA_FILES:
            self.skipTest('SERVE_MEDIA_FILES is off; media routes are not registered')

    def test_public_folders_are_served(self):
        self.assertEqual(self.client.get('/media/covers/c.png').status_code, 200)
        self.assertEqual(self.client.get('/media/avatars/a.png').status_code, 200)

    def test_protected_folders_are_not_served(self):
        self.assertEqual(self.client.get('/media/books/secret.pdf').status_code, 404)
        self.assertEqual(self.client.get('/media/articles/secret.pdf').status_code, 404)

    def test_path_traversal_into_protected_folder_is_blocked(self):
        self.assertEqual(self.client.get('/media/covers/../books/secret.pdf').status_code, 404)
        self.assertEqual(self.client.get('/media/covers/%2e%2e/books/secret.pdf').status_code, 404)


class SettingsSecurityTests(SimpleTestCase):
    def _load_settings(self, code='import config.settings', **env):
        """Import config.settings in a clean subprocess with the given env."""
        clean = {k: v for k, v in os.environ.items() if k not in ('SECRET_KEY', 'DEBUG')}
        clean.update(env)
        return subprocess.run(
            [sys.executable, '-c', code],
            cwd=BASE_DIR, env=clean, capture_output=True, text=True,
        )

    def test_missing_secret_key_fails_when_not_debug(self):
        result = self._load_settings(DEBUG='False', SECRET_KEY='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ImproperlyConfigured', result.stderr)

    def test_short_or_default_secret_key_fails_when_not_debug(self):
        for key in ('short', 'unsafe-dev-key-change-in-env'):
            with self.subTest(key=key):
                result = self._load_settings(DEBUG='False', SECRET_KEY=key)
                self.assertNotEqual(result.returncode, 0)

    def test_strong_secret_key_accepted_when_not_debug(self):
        result = self._load_settings(DEBUG='False', SECRET_KEY='x' * 60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_dev_fallback_allowed_only_in_debug(self):
        result = self._load_settings(DEBUG='True', SECRET_KEY='')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_production_uses_whitenoise_manifest_storage(self):
        result = self._load_settings(
            code=(
                'import config.settings as s; '
                'print(s.STORAGES["staticfiles"]["BACKEND"]); '
                'print(hasattr(s, "STATICFILES_STORAGE"))'
            ),
            DEBUG='False', SECRET_KEY='x' * 60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        backend, legacy = result.stdout.split()
        self.assertEqual(backend, 'whitenoise.storage.CompressedManifestStaticFilesStorage')
        self.assertEqual(legacy, 'False')
