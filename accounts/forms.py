from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = [
            'username', 'last_name', 'first_name', 'middle_name', 'email', 'phone',
            'university_name', 'faculty_name', 'specialty_name', 'course', 'group_name',
            'password1', 'password2'
        ]
        labels = {
            'username': 'Логин',
            'last_name': 'Насаб',
            'first_name': 'Ном',
            'middle_name': 'Номи падар',
            'phone': 'Телефон',
            'university_name': 'Номи донишгоҳ',
            'faculty_name': 'Номи факултет',
            'specialty_name': 'Номи ихтисос',
            'course': 'Курс',
            'group_name': 'Гурӯҳ',
        }

    def clean_course(self):
        course = self.cleaned_data.get('course')
        if course and (course < 1 or course > 6):
            raise forms.ValidationError('Курс бояд аз 1 то 6 бошад.')
        return course

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.is_verified = False
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'avatar', 'last_name', 'first_name', 'middle_name', 'email', 'phone',
            'university_name', 'faculty_name', 'specialty_name', 'course', 'group_name'
        ]
        labels = {
            'avatar': 'Расми профил',
            'last_name': 'Насаб',
            'first_name': 'Ном',
            'middle_name': 'Номи падар',
            'phone': 'Телефон',
            'university_name': 'Номи донишгоҳ',
            'faculty_name': 'Номи факултет',
            'specialty_name': 'Номи ихтисос',
            'course': 'Курс',
            'group_name': 'Гурӯҳ',
        }

    def clean_course(self):
        course = self.cleaned_data.get('course')
        if course and (course < 1 or course > 6):
            raise forms.ValidationError('Курс бояд аз 1 то 6 бошад.')
        return course


class UserRoleUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'is_verified', 'is_active', 'is_staff']
        labels = {
            'role': 'Нақш',
            'is_verified': 'Тасдиқ шудааст',
            'is_active': 'Фаъол',
            'is_staff': 'Дастрасӣ ба Django admin',
        }
