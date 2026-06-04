from django.contrib import admin
from .models import AuditLog, Author, Book, BookRequest, Category, DownloadLog, FavoriteBook


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ('full_name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'language', 'publication_year', 'is_approved', 'is_download_allowed', 'downloads_count', 'created_at')
    list_filter = ('is_approved', 'is_download_allowed', 'language', 'category', 'created_at')
    search_fields = ('title', 'description', 'keywords', 'authors__full_name')
    filter_horizontal = ('authors',)
    readonly_fields = ('views_count', 'downloads_count', 'created_at', 'updated_at')


@admin.register(FavoriteBook)
class FavoriteBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'created_at')
    search_fields = ('user__username', 'book__title')


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'user', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('title', 'author', 'user__username')


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'downloaded_at', 'ip_address')
    search_fields = ('book__title', 'user__username')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'object_name', 'actor', 'ip_address', 'created_at')
    search_fields = ('action', 'object_name', 'actor__username')
    readonly_fields = ('actor', 'action', 'object_name', 'ip_address', 'created_at')
