import os
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse


def validate_file_size(file):
    max_size_mb = 50
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Ҳаҷми файл набояд аз {max_size_mb} MB зиёд бошад.')


def _random_upload_path(folder, filename):
    """Store uploads under a random name so titles never influence the path.

    Using the title allowed '/' and '..' into the path (crash / sub-folders) and
    made protected file URLs guessable.
    """
    ext = os.path.splitext(filename)[1].lower()
    return f'{folder}/{uuid.uuid4().hex}{ext}'


def book_file_path(instance, filename):
    return _random_upload_path('books', filename)


def cover_file_path(instance, filename):
    return _random_upload_path('covers', filename)


def article_file_path(instance, filename):
    return _random_upload_path('articles', filename)


def article_cover_path(instance, filename):
    return _random_upload_path('article_covers', filename)


# Magic bytes for allowed document types: PDF, DOCX (ZIP container), legacy DOC (OLE2).
_DOCUMENT_SIGNATURES = {
    'pdf': (b'%PDF-',),
    'docx': (b'PK\x03\x04',),
    'doc': (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',),
}


def validate_document_content(file):
    """Reject files whose content does not match their extension (e.g. renamed .exe)."""
    if getattr(file, '_committed', False):
        return  # already stored and validated on upload
    ext = os.path.splitext(file.name)[1].lower().lstrip('.')
    signatures = _DOCUMENT_SIGNATURES.get(ext)
    if not signatures:
        return
    position = file.tell() if hasattr(file, 'tell') else 0
    file.seek(0)
    header = file.read(8)
    file.seek(position)
    if not any(header.startswith(sig) for sig in signatures):
        raise ValidationError('Мӯҳтавои файл ба навъи он мувофиқ нест.')


class Category(models.Model):
    name = models.CharField('Ном', max_length=150, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категорияҳо'
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    full_name = models.CharField('Ному насаб', max_length=255)

    class Meta:
        verbose_name = 'Муаллиф'
        verbose_name_plural = 'Муаллифон'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class BookQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(is_approved=True, is_active=True, is_deleted=False)

    def not_deleted(self):
        return self.filter(is_deleted=False)


class Book(models.Model):
    class Language(models.TextChoices):
        TAJIK = 'TJ', 'Тоҷикӣ'
        RUSSIAN = 'RU', 'Русӣ'
        ENGLISH = 'EN', 'Англисӣ'
        OTHER = 'OTHER', 'Дигар'

    title = models.CharField('Номи китоб', max_length=300)
    authors = models.ManyToManyField(Author, verbose_name='Муаллифон', related_name='books')
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField('Шарҳ', blank=True)
    publication_year = models.PositiveIntegerField('Соли нашр', null=True, blank=True)
    language = models.CharField('Забон', max_length=20, choices=Language.choices, default=Language.TAJIK)
    subject = models.CharField('Фан / самт', max_length=255, blank=True)
    keywords = models.CharField('Калидвожаҳо', max_length=500, blank=True)

    cover = models.ImageField(
        'Муқова', upload_to=cover_file_path, blank=True, null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    file = models.FileField(
        'Файли китоб', upload_to=book_file_path,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx']), validate_file_size, validate_document_content]
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Иловакунанда',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_books'
    )
    is_approved = models.BooleanField('Тасдиқ шудааст', default=False)
    is_active = models.BooleanField('Фаъол', default=True)
    is_deleted = models.BooleanField('Нестшуда', default=False)
    is_download_allowed = models.BooleanField('Зеркашӣ иҷозат аст', default=True)
    views_count = models.PositiveIntegerField('Дидан', default=0)
    downloads_count = models.PositiveIntegerField('Зеркашӣ', default=0)
    created_at = models.DateTimeField('Санаи илова', auto_now_add=True)
    updated_at = models.DateTimeField('Санаи навсозӣ', auto_now=True)
    deleted_at = models.DateTimeField('Санаи несткунӣ', null=True, blank=True)

    objects = BookQuerySet.as_manager()

    class Meta:
        verbose_name = 'Китоб'
        verbose_name_plural = 'Китобҳо'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['language']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('library:book_detail', kwargs={'pk': self.pk})

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower().strip('.') if self.file else ''

    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'

    @property
    def average_rating(self):
        value = self.ratings.aggregate(avg=Avg('rating'))['avg']
        return round(value or 0, 1)

    def can_be_managed_by(self, user):
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.is_admin_role() or user.is_librarian_role() or self.uploaded_by_id == user.id


class BookView(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='unique_views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=80, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Дидани китоб'
        verbose_name_plural = 'Дидани китобҳо'
        constraints = [
            models.UniqueConstraint(fields=['book', 'user'], name='unique_book_view_per_user'),
            models.UniqueConstraint(fields=['book', 'session_key'], name='unique_book_view_per_session'),
        ]


class BookComment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_comments')
    text = models.TextField('Шарҳ')
    is_approved = models.BooleanField('Намоён аст', default=True)
    created_at = models.DateTimeField('Санаи шарҳ', auto_now_add=True)

    class Meta:
        verbose_name = 'Шарҳи китоб'
        verbose_name_plural = 'Шарҳҳои китоб'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.book}'


class BookRating(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_ratings')
    rating = models.PositiveSmallIntegerField('Баҳо', validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Баҳои китоб'
        verbose_name_plural = 'Баҳои китобҳо'
        unique_together = ('book', 'user')

    def __str__(self):
        return f'{self.book} — {self.rating}'


class FavoriteBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Китоби дӯстдошта'
        verbose_name_plural = 'Китобҳои дӯстдошта'
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user} → {self.book}'


class BookRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_requests')
    title = models.CharField('Номи китоб', max_length=300)
    author = models.CharField('Муаллиф', max_length=255, blank=True)
    note = models.TextField('Эзоҳ', blank=True)
    is_processed = models.BooleanField('Баррасӣ шуд', default=False)
    created_at = models.DateTimeField('Санаи дархост', auto_now_add=True)

    class Meta:
        verbose_name = 'Дархости китоб'
        verbose_name_plural = 'Дархостҳои китоб'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ArticleQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(is_approved=True, is_active=True, is_deleted=False)

    def not_deleted(self):
        return self.filter(is_deleted=False)


class Article(models.Model):
    class Language(models.TextChoices):
        TAJIK = 'TJ', 'Тоҷикӣ'
        RUSSIAN = 'RU', 'Русӣ'
        ENGLISH = 'EN', 'Англисӣ'
        OTHER = 'OTHER', 'Дигар'

    title = models.CharField('Номи мақола', max_length=350)
    authors_text = models.CharField('Муаллифон', max_length=500)
    abstract = models.TextField('Аннотатсия', blank=True)
    content = models.TextField('Матни мақола', blank=True)
    keywords = models.CharField('Калидвожаҳо', max_length=500, blank=True)
    publication_year = models.PositiveIntegerField('Соли нашр', null=True, blank=True)
    language = models.CharField('Забон', max_length=20, choices=Language.choices, default=Language.TAJIK)
    cover = models.ImageField(
        'Расм/Муқова', upload_to=article_cover_path, blank=True, null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    file = models.FileField(
        'Файли мақола', upload_to=article_file_path, blank=True, null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx']), validate_file_size, validate_document_content]
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Иловакунанда', on_delete=models.SET_NULL,
        null=True, related_name='uploaded_articles'
    )
    is_approved = models.BooleanField('Тасдиқ шудааст', default=False)
    is_active = models.BooleanField('Фаъол', default=True)
    is_deleted = models.BooleanField('Нестшуда', default=False)
    views_count = models.PositiveIntegerField('Дидан', default=0)
    downloads_count = models.PositiveIntegerField('Зеркашӣ', default=0)
    created_at = models.DateTimeField('Санаи илова', auto_now_add=True)
    updated_at = models.DateTimeField('Санаи навсозӣ', auto_now=True)
    deleted_at = models.DateTimeField('Санаи несткунӣ', null=True, blank=True)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = 'Мақола'
        verbose_name_plural = 'Мақолаҳо'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active', 'is_deleted']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('library:article_detail', kwargs={'pk': self.pk})

    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower().strip('.') if self.file else ''

    @property
    def is_pdf(self):
        return self.file_extension == 'pdf'

    def can_be_managed_by(self, user):
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.is_admin_role() or user.is_librarian_role() or self.uploaded_by_id == user.id


class DownloadLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='download_logs')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Сабти зеркашӣ'
        verbose_name_plural = 'Сабтҳои зеркашӣ'
        ordering = ['-downloaded_at']


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    object_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Audit log'
        verbose_name_plural = 'Audit logs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.object_name}'
