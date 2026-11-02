"""Production behaviour behind an HTTPS reverse proxy."""
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

BASE_DIR = Path(settings.BASE_DIR)


@override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
class ProxySslTests(TestCase):
    def test_https_via_proxy_is_not_redirected(self):
        response = self.client.get(reverse('library:home'), HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)

    def test_plain_http_is_redirected_to_https(self):
        response = self.client.get(reverse('library:home'))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].startswith('https://'))

    def test_healthz_is_exempt_from_redirect(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


class ErrorPageTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_page(self):
        response = self.client.get('/no-such-page/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Саҳифа ёфт нашуд', status_code=404)


class EnvExampleTests(SimpleTestCase):
    def test_env_example_produces_valid_production_settings(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('DB_', 'SECURE_', 'SECRET', 'DEBUG'))}
        for line in (BASE_DIR / '.env.example').read_text().splitlines():
            if line and not line.startswith('#'):
                key, _, value = line.partition('=')
                env[key] = value
        env['SECRET_KEY'] = 'z' * 64
        code = ('import config.settings as s; '
                'assert s.SECURE_PROXY_SSL_HEADER; assert s.SECURE_SSL_REDIRECT; '
                'assert s.SECURE_HSTS_SECONDS == 3600; assert not s.DEBUG; assert not s.SERVE_MEDIA_FILES')
        result = subprocess.run([sys.executable, '-c', code], cwd=BASE_DIR, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
