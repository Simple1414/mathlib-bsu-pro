import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


def validate_file_size(file):
    max_size_mb = 50
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Ҳаҷми файл набояд аз {max_size_mb} MB зиёд бошад.')


def book_file_path(instance, filename):
    base, ext = os.path.splitext(filename)
    safe_title = instance.title[:60].replace(' ', '_')
    return f'books/{safe_title}{ext.lower()}'


def cover_file_path(instance, filename):
    base, ext = os.path.splitext(filename)
    safe_title = instance.title[:60].replace(' ', '_')
    return f'covers/{safe_title}{ext.lower()}'


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
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx']), validate_file_size]
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Иловакунанда',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_books'
    )
    is_approved = models.BooleanField('Тасдиқ шудааст', default=False)
    is_download_allowed = models.BooleanField('Зеркашӣ иҷозат аст', default=True)
    views_count = models.PositiveIntegerField('Дидан', default=0)
    downloads_count = models.PositiveIntegerField('Зеркашӣ', default=0)
    created_at = models.DateTimeField('Санаи илова', auto_now_add=True)
    updated_at = models.DateTimeField('Санаи навсозӣ', auto_now=True)

    class Meta:
        verbose_name = 'Китоб'
        verbose_name_plural = 'Китобҳо'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['language']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('library:book_detail', kwargs={'pk': self.pk})

    def can_be_managed_by(self, user):
        if not user.is_authenticated:
            return False
        return user.is_superuser or user.is_admin_role() or user.is_librarian_role() or self.uploaded_by_id == user.id


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
