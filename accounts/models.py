from django.contrib.auth.models import AbstractUser
from django.db import models


class University(models.Model):
    name = models.CharField('Номи донишгоҳ', max_length=255, unique=True)

    class Meta:
        verbose_name = 'Донишгоҳ'
        verbose_name_plural = 'Донишгоҳҳо'
        ordering = ['name']

    def __str__(self):
        return self.name


class Faculty(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='faculties')
    name = models.CharField('Номи факултет', max_length=255)

    class Meta:
        verbose_name = 'Факултет'
        verbose_name_plural = 'Факултетҳо'
        unique_together = ('university', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Specialty(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='specialties')
    name = models.CharField('Номи ихтисос', max_length=255)
    code = models.CharField('Рамз', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Ихтисос'
        verbose_name_plural = 'Ихтисосҳо'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Админ'
        LIBRARIAN = 'LIBRARIAN', 'Китобдор'
        TEACHER = 'TEACHER', 'Омӯзгор'
        STUDENT = 'STUDENT', 'Донишҷӯ'

    role = models.CharField('Нақш', max_length=20, choices=Role.choices, default=Role.STUDENT)
    middle_name = models.CharField('Номи падар', max_length=150, blank=True)
    phone = models.CharField('Телефон', max_length=30, blank=True)

    university = models.ForeignKey(
        University, verbose_name='Донишгоҳ', on_delete=models.SET_NULL, null=True, blank=True
    )
    faculty = models.ForeignKey(
        Faculty, verbose_name='Факултет', on_delete=models.SET_NULL, null=True, blank=True
    )
    specialty = models.ForeignKey(
        Specialty, verbose_name='Ихтисос', on_delete=models.SET_NULL, null=True, blank=True
    )
    course = models.PositiveSmallIntegerField('Курс', null=True, blank=True)
    group_name = models.CharField('Гурӯҳ', max_length=50, blank=True)

    is_verified = models.BooleanField('Тасдиқ шудааст', default=False)
    created_at = models.DateTimeField('Санаи бақайдгирӣ', auto_now_add=True)

    class Meta:
        verbose_name = 'Корбар'
        verbose_name_plural = 'Корбарон'

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join([p for p in parts if p]).strip() or self.username

    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def is_librarian_role(self):
        return self.role == self.Role.LIBRARIAN

    def is_teacher_role(self):
        return self.role == self.Role.TEACHER

    def is_student_role(self):
        return self.role == self.Role.STUDENT
