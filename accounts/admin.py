from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Faculty, Specialty, University, User


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'university']
    search_fields = ['name', 'university__name']


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty', 'code']
    search_fields = ['name', 'code', 'faculty__name']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'role', 'display_university', 'display_specialty', 'is_active', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_active', 'is_verified', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'university_name', 'faculty_name', 'specialty_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Маълумоти иловагӣ', {
            'fields': (
                'role', 'middle_name', 'phone', 'avatar',
                'university', 'faculty', 'specialty',
                'university_name', 'faculty_name', 'specialty_name',
                'course', 'group_name', 'is_verified', 'created_at'
            )
        }),
    )
    readonly_fields = ['created_at']
