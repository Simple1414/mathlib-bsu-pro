"""Smoke tests: every page renders for every role without server errors."""
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from library.models import Article, Author, Book, BookComment, BookRequest, Category

PASSWORD = 'Test-Passw0rd-123'
PDF = b'%PDF-1.4\n%test\n'


def pdf(name='file.pdf'):
    return SimpleUploadedFile(name, PDF, content_type='application/pdf')


class SmokeTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Each test class (and each parallel worker) gets its own media dir.
        cls._media_root = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        cls.users = {
            role: User.objects.create_user(role.lower(), password=PASSWORD, role=role)
            for role in User.Role.values
        }
        cls.category = Category.objects.create(name='Алгебра')
        cls.author = Author.objects.create(full_name='Леонард Эйлер')
        cls.book = Book.objects.create(
            title='Алгебра', category=cls.category, file=pdf(), is_approved=True,
            uploaded_by=cls.users['TEACHER'],
        )
        cls.book.authors.add(cls.author)
        cls.pending_book = Book.objects.create(title='Интизорӣ', file=pdf(), uploaded_by=cls.users['TEACHER'])
        cls.article = Article.objects.create(
            title='Мақола', authors_text='Муаллиф', file=pdf(), is_approved=True,
            uploaded_by=cls.users['TEACHER'],
        )
        BookComment.objects.create(book=cls.book, user=cls.users['STUDENT'], text='Хуб')
        BookRequest.objects.create(user=cls.users['STUDENT'], title='Геометрия')



class AllPagesRenderTests(SmokeTestBase):
    def urls(self):
        b, a, u = self.book.pk, self.article.pk, self.users['STUDENT'].pk
        return [
            reverse('library:home'), reverse('library:about'), reverse('library:contact'),
            reverse('library:book_list'), reverse('library:book_list') + '?q=алгебра&language=TJ',
            reverse('library:book_detail', args=[b]), reverse('library:preview_book', args=[b]),
            reverse('library:download_book', args=[b]), reverse('library:book_create'),
            reverse('library:book_update', args=[b]), reverse('library:book_delete', args=[b]),
            reverse('library:pending_books'), reverse('library:article_list'),
            reverse('library:article_list') + '?q=мақола',
            reverse('library:article_detail', args=[a]), reverse('library:preview_article', args=[a]),
            reverse('library:download_article', args=[a]), reverse('library:article_create'),
            reverse('library:article_update', args=[a]), reverse('library:article_delete', args=[a]),
            reverse('library:favorites'), reverse('library:request_book'), reverse('library:book_requests'),
            reverse('library:set_language', args=['ru']),
            reverse('accounts:login'), reverse('accounts:register'), reverse('accounts:profile'),
            reverse('accounts:user_list'), reverse('accounts:user_list') + '?q=s&role=STUDENT&status=active',
            reverse('accounts:user_role_update', args=[u]),
            reverse('dashboard:home'),
        ]

    def test_every_page_for_every_role(self):
        for who in [None, *User.Role.values]:
            if who:
                self.client.force_login(self.users[who])
            else:
                self.client.logout()
            for url in self.urls():
                with self.subTest(role=who or 'anonymous', url=url):
                    response = self.client.get(url)
                    self.assertIn(response.status_code, (200, 302, 403, 404), response.status_code)

    def test_hidden_book_not_visible_to_student(self):
        self.client.force_login(self.users['STUDENT'])
        for name in ('book_detail', 'preview_book', 'download_book'):
            with self.subTest(view=name):
                url = reverse(f'library:{name}', args=[self.pending_book.pk])
                self.assertEqual(self.client.get(url).status_code, 404)


class WorkflowTests(SmokeTestBase):
    def test_teacher_submits_book_and_librarian_approves(self):
        self.client.force_login(self.users['TEACHER'])
        response = self.client.post(reverse('library:book_create'), {
            'title': 'Алгебра 1/2 ../../x', 'authors': [self.author.pk], 'new_authors': 'Нютон',
            'language': 'TJ', 'file': pdf('my book.pdf'), 'is_download_allowed': 'on', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None) and response.context['form'].errors)
        book = Book.objects.get(title='Алгебра 1/2 ../../x')
        self.assertFalse(book.is_approved)
        self.assertNotIn('..', book.file.name)
        self.assertEqual(book.file.name.count('/'), 1)

        self.client.force_login(self.users['LIBRARIAN'])
        self.client.post(reverse('library:approve_book', args=[book.pk]))
        book.refresh_from_db()
        self.assertTrue(book.is_approved)

        self.client.force_login(self.users['STUDENT'])
        response = self.client.get(reverse('library:download_book', args=[book.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_teacher_edit_of_approved_book_requires_reapproval(self):
        self.client.force_login(self.users['TEACHER'])
        response = self.client.post(reverse('library:book_update', args=[self.book.pk]), {
            'title': 'Алгебра (нав)', 'authors': [self.author.pk], 'language': 'TJ', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, 'Алгебра (нав)')
        self.assertFalse(self.book.is_approved)

    def test_librarian_edit_keeps_approval(self):
        self.client.force_login(self.users['LIBRARIAN'])
        self.client.post(reverse('library:book_update', args=[self.book.pk]), {
            'title': 'Алгебра 2', 'authors': [self.author.pk], 'language': 'TJ', 'is_active': 'on',
        })
        self.book.refresh_from_db()
        self.assertTrue(self.book.is_approved)

    def test_registration_always_creates_student(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser', 'first_name': 'Ном', 'last_name': 'Насаб', 'email': 'n@example.tj',
            'password1': PASSWORD, 'password2': PASSWORD, 'role': 'ADMIN', 'is_staff': 'on',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertFalse(user.is_staff)

    def test_comment_and_rating(self):
        self.client.force_login(self.users['STUDENT'])
        url = reverse('library:book_detail', args=[self.book.pk])
        self.assertEqual(self.client.post(url, {'comment_submit': '1', 'text': 'Аъло'}).status_code, 302)
        self.assertEqual(self.client.post(url, {'rating_submit': '1', 'rating': '5'}).status_code, 302)
        self.assertEqual(self.book.ratings.get().rating, 5)

    def test_logout_via_post(self):
        self.client.force_login(self.users['STUDENT'])
        self.assertEqual(self.client.post(reverse('accounts:logout')).status_code, 302)


class ArticleApprovalTests(SmokeTestBase):
    def test_teacher_article_pending_then_librarian_approves(self):
        self.client.force_login(self.users['TEACHER'])
        self.client.post(reverse('library:article_create'), {
            'title': 'Мақолаи нав', 'authors_text': 'Омӯзгор', 'language': 'TJ',
            'file': pdf(), 'is_active': 'on',
        })
        article = Article.objects.get(title='Мақолаи нав')
        self.assertFalse(article.is_approved)

        self.client.force_login(self.users['LIBRARIAN'])
        page = self.client.get(reverse('library:pending_books')).content.decode()
        self.assertIn('Мақолаи нав', page)
        self.assertEqual(self.client.get(reverse('library:approve_article', args=[article.pk])).status_code, 405)
        self.client.post(reverse('library:approve_article', args=[article.pk]))
        article.refresh_from_db()
        self.assertTrue(article.is_approved)

    def test_student_cannot_approve_article(self):
        article = Article.objects.create(title='X', authors_text='Y', file=pdf())
        self.client.force_login(self.users['STUDENT'])
        self.client.post(reverse('library:approve_article', args=[article.pk]))
        article.refresh_from_db()
        self.assertFalse(article.is_approved)


class UploadValidationTests(SmokeTestBase):
    def test_fake_pdf_is_rejected(self):
        self.client.force_login(self.users['LIBRARIAN'])
        fake = SimpleUploadedFile('virus.pdf', b'MZ\x90\x00 not a pdf', content_type='application/pdf')
        response = self.client.post(reverse('library:book_create'), {
            'title': 'Fake', 'authors': [self.author.pk], 'language': 'TJ', 'file': fake, 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.assertFalse(Book.objects.filter(title='Fake').exists())

    def test_download_uses_readable_filename(self):
        self.client.force_login(self.users['STUDENT'])
        response = self.client.get(reverse('library:download_book', args=[self.book.pk]))
        self.assertIn('.pdf', response['Content-Disposition'])
        self.assertNotIn('/', response['Content-Disposition'])


class MissingFileTests(SmokeTestBase):
    def test_missing_file_returns_404_not_500(self):
        Path(self.book.file.path).unlink()
        self.client.force_login(self.users['STUDENT'])
        with self.assertLogs('library.views', level='ERROR'):
            response = self.client.get(reverse('library:download_book', args=[self.book.pk]))
        self.assertEqual(response.status_code, 404)


class BookAuthorInputTests(SmokeTestBase):
    def post_book(self, **extra):
        self.client.force_login(self.users['LIBRARIAN'])
        data = {'title': 'Китоби нав', 'language': 'TJ', 'file': pdf(), 'is_active': 'on', **extra}
        return self.client.post(reverse('library:book_create'), data)

    def test_only_new_author_typed_is_enough(self):
        response = self.post_book(new_authors='Умари Хайём, Абӯалӣ ибни Сино')
        self.assertEqual(response.status_code, 302)
        book = Book.objects.get(title='Китоби нав')
        self.assertEqual(sorted(a.full_name for a in book.authors.all()), ['Абӯалӣ ибни Сино', 'Умари Хайём'])

    def test_no_author_at_all_is_rejected(self):
        response = self.post_book(new_authors='  ,  ')
        self.assertEqual(response.status_code, 200)
        self.assertIn('authors', response.context['form'].errors)
