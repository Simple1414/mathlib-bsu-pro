from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Faculty, Specialty, University, User


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'university')
    list_filter = ('university',)
    search_fields = ('name', 'university__name')


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty')
    list_filter = ('faculty',)
    search_fields = ('name', 'code')


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'full_name', 'role', 'faculty', 'specialty', 'course', 'group_name', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'faculty', 'course', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'middle_name', 'email', 'phone')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Маълумоти таълимӣ ва нақш', {
            'fields': ('role', 'middle_name', 'phone', 'university', 'faculty', 'specialty', 'course', 'group_name', 'is_verified')
        }),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Маълумоти иловагӣ', {
            'fields': ('role', 'first_name', 'last_name', 'middle_name', 'email', 'phone', 'university', 'faculty', 'specialty', 'course', 'group_name')
        }),
    )
