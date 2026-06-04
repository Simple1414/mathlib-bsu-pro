from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Шумо барои ин амал иҷозат надоред.')
            return redirect('dashboard:home')
        return _wrapped
    return decorator


def can_manage_books(user):
    return user.is_authenticated and (user.is_superuser or user.is_admin_role() or user.is_librarian_role())


def can_submit_books(user):
    return user.is_authenticated and (user.is_superuser or user.is_admin_role() or user.is_librarian_role() or user.is_teacher_role())
