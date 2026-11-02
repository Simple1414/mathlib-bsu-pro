"""State-changing library actions must reject GET (CSRF via links/images)."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from library.models import Book, BookRequest, FavoriteBook

MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = 'Test-Passw0rd-123'


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostOnlyActionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user('student', password=PASSWORD, role=User.Role.STUDENT)
        cls.librarian = User.objects.create_user('librarian', password=PASSWORD, role=User.Role.LIBRARIAN)
        cls.pending = Book.objects.create(
            title='Pending', file=SimpleUploadedFile('p.pdf', b'%PDF-1.4 test'), is_approved=False,
        )
        cls.public = Book.objects.create(
            title='Public', file=SimpleUploadedFile('q.pdf', b'%PDF-1.4 test'), is_approved=True,
        )
        cls.book_request = BookRequest.objects.create(user=cls.student, title='Wanted')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    # approve_book
    def test_approve_book_rejects_get(self):
        self.client.force_login(self.librarian)
        response = self.client.get(reverse('library:approve_book', args=[self.pending.pk]))
        self.assertEqual(response.status_code, 405)
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_approved)

    def test_approve_book_post_by_librarian(self):
        self.client.force_login(self.librarian)
        response = self.client.post(reverse('library:approve_book', args=[self.pending.pk]))
        self.assertRedirects(response, reverse('library:pending_books'))
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_approved)

    def test_approve_book_post_by_student_denied(self):
        self.client.force_login(self.student)
        self.client.post(reverse('library:approve_book', args=[self.pending.pk]))
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_approved)

    # toggle_favorite
    def test_toggle_favorite_rejects_get(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('library:toggle_favorite', args=[self.public.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(FavoriteBook.objects.exists())

    def test_toggle_favorite_post_adds_then_removes(self):
        self.client.force_login(self.student)
        url = reverse('library:toggle_favorite', args=[self.public.pk])
        self.client.post(url)
        self.assertTrue(FavoriteBook.objects.filter(user=self.student, book=self.public).exists())
        self.client.post(url)
        self.assertFalse(FavoriteBook.objects.filter(user=self.student, book=self.public).exists())

    # mark_request_processed
    def test_mark_request_processed_rejects_get(self):
        self.client.force_login(self.librarian)
        response = self.client.get(reverse('library:mark_request_processed', args=[self.book_request.pk]))
        self.assertEqual(response.status_code, 405)
        self.book_request.refresh_from_db()
        self.assertFalse(self.book_request.is_processed)

    def test_mark_request_processed_post_by_librarian(self):
        self.client.force_login(self.librarian)
        self.client.post(reverse('library:mark_request_processed', args=[self.book_request.pk]))
        self.book_request.refresh_from_db()
        self.assertTrue(self.book_request.is_processed)

    # templates render POST forms with CSRF tokens
    def test_pending_books_page_uses_post_form(self):
        self.client.force_login(self.librarian)
        html = self.client.get(reverse('library:pending_books')).content.decode()
        self.assertIn(f'action="{reverse("library:approve_book", args=[self.pending.pk])}"', html)
        self.assertIn('csrfmiddlewaretoken', html)
