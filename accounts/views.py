from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, UpdateView

from .forms import ProfileUpdateForm, RegistrationForm, UserRoleUpdateForm
from .models import User


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role()


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Бақайдгирӣ анҷом ёфт. Ҳисоб ҳамчун донишҷӯ фаъол шуд.')
            return redirect('dashboard:home')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Маълумоти шахсӣ навсозӣ шуд.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.select_related('university', 'faculty', 'specialty').order_by('-date_joined')
        q = self.request.GET.get('q')
        role = self.request.GET.get('role')
        if q:
            qs = qs.filter(username__icontains=q) | qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q)
        if role:
            qs = qs.filter(role=role)
        return qs


class UserRoleUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserRoleUpdateForm
    template_name = 'accounts/user_role_update.html'
    success_url = '/accounts/users/'

    def form_valid(self, form):
        messages.success(self.request, 'Нақш ва ҳолати корбар навсозӣ шуд.')
        return super().form_valid(form)
