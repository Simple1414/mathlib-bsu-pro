---
name: django-testing
description: Automated testing and test-driven development for this Django project. Use when adding tests, setting up the test suite or CI test job, writing permission-matrix tests, testing uploads/downloads, measuring coverage, or doing TDD on a feature or bug fix.
---

# Django Testing & TDD

The repo currently has **no tests**. Building the suite is high-priority. For the generic red-green-refactor discipline use `superpowers:test-driven-development`; this skill covers *how* to test this project.

## When to activate
- Any feature or bug fix (write the failing test first).
- Setting up test infrastructure or CI.

## Layout
```
accounts/tests/{__init__,test_registration,test_roles}.py
library/tests/{__init__,factories,test_visibility,test_permissions,test_uploads,test_downloads}.py
dashboard/tests/{__init__,test_dashboards}.py
```
Use Django `TestCase` (transactional, fast). `pytest-django` + `factory_boy` are good upgrades — ask before adding dependencies.

## Test database
- Tests need PostgreSQL (settings hardcode the postgresql engine). Locally: a dev Postgres; in CI: a `postgres:16` service container. The test runner creates `test_<DB_NAME>`; the DB user needs `CREATEDB`.
- Never point tests at a production database.

## Patterns
```python
from django.test import TestCase
from django.urls import reverse
from accounts.models import User

class ApproveBookPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user("s", password="x-Strong-123", role=User.Role.STUDENT)
        cls.librarian = User.objects.create_user("l", password="x-Strong-123", role=User.Role.LIBRARIAN)
        # cls.book = make_book(is_approved=False)

    def test_student_cannot_approve(self):
        self.client.force_login(self.student)
        # resp = self.client.post(reverse("library:approve_book", args=[self.book.pk]))
        # self.book.refresh_from_db(); self.assertFalse(self.book.is_approved)

    def test_get_is_rejected(self):
        self.client.force_login(self.librarian)
        # resp = self.client.get(reverse("library:approve_book", args=[self.book.pk]))
        # self.assertEqual(resp.status_code, 405)
```
- Files: `SimpleUploadedFile("a.pdf", b"%PDF-1.4 ...", content_type="application/pdf")`; use `@override_settings(MEDIA_ROOT=tmpdir)` and clean up.
- Query counts: `with self.assertNumQueries(n):`.
- Use `subTest` for role matrices.

## What must be covered
1. Visibility: anonymous/student never see unapproved, inactive, or soft-deleted items (list, detail, preview, download).
2. Permission matrix for every protected URL.
3. Mutations are POST-only.
4. Registration always yields STUDENT.
5. Upload validation (extension, content, size).
6. Download logging and counter increment.
7. Migrations: `makemigrations --check --dry-run` exits 0.

## Commands
```bash
python manage.py test --parallel           # all
python manage.py test library.tests.test_permissions -v 2
coverage run manage.py test && coverage report -m   # if coverage installed; target ≥ 80% on changed code
```

## Security considerations
- Use obviously fake credentials; no real user data in fixtures.

## Checklist
- [ ] Test written first and seen failing (for bug fixes: reproduces the bug)
- [ ] Positive and negative (denied) cases
- [ ] No reliance on test order or real network
- [ ] Suite passes locally; failures reported verbatim, never hidden or skipped
