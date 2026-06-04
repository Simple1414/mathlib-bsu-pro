from django.contrib import admin
from .models import (
    Article, AuditLog, Author, Book, BookComment, BookRating, BookRequest,
    BookView, Category, DownloadLog, FavoriteBook,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ['full_name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'language', 'is_approved', 'is_active', 'is_deleted', 'views_count', 'downloads_count', 'created_at']
    list_filter = ['is_approved', 'is_active', 'is_deleted', 'language', 'category']
    search_fields = ['title', 'authors__full_name', 'keywords', 'subject']
    filter_horizontal = ['authors']
    readonly_fields = ['views_count', 'downloads_count', 'created_at', 'updated_at', 'deleted_at']


@admin.register(BookView)
class BookViewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'session_key', 'ip_address', 'created_at']
    search_fields = ['book__title', 'user__username', 'session_key']


@admin.register(BookComment)
class BookCommentAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['book__title', 'user__username', 'text']


@admin.register(BookRating)
class BookRatingAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'updated_at']
    list_filter = ['rating']
    search_fields = ['book__title', 'user__username']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors_text', 'language', 'is_approved', 'is_active', 'is_deleted', 'views_count', 'downloads_count', 'created_at']
    list_filter = ['is_approved', 'is_active', 'is_deleted', 'language']
    search_fields = ['title', 'authors_text', 'keywords', 'abstract']
    readonly_fields = ['views_count', 'downloads_count', 'created_at', 'updated_at', 'deleted_at']


@admin.register(FavoriteBook)
class FavoriteBookAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'created_at']
    search_fields = ['user__username', 'book__title']


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'user', 'is_processed', 'created_at']
    list_filter = ['is_processed']
    search_fields = ['title', 'author', 'user__username']


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'ip_address', 'downloaded_at']
    search_fields = ['book__title', 'user__username']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'object_name', 'actor', 'ip_address', 'created_at']
    search_fields = ['action', 'object_name', 'actor__username']
