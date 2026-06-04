from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import User
from library.models import Article, AuditLog, Book, BookRequest, DownloadLog, FavoriteBook


@login_required
def home(request):
    user = request.user
    if user.is_admin_role():
        return admin_dashboard(request)
    if user.is_librarian_role():
        return librarian_dashboard(request)
    if user.is_teacher_role():
        return teacher_dashboard(request)
    return student_dashboard(request)


@login_required
def admin_dashboard(request):
    context = {
        'total_books': Book.objects.not_deleted().count(),
        'approved_books': Book.objects.visible().count(),
        'pending_books': Book.objects.filter(is_approved=False, is_deleted=False).count(),
        'articles_count': Article.objects.visible().count(),
        'pending_articles': Article.objects.filter(is_approved=False, is_deleted=False).count(),
        'users_count': User.objects.count(),
        'active_users_count': User.objects.filter(is_active=True).count(),
        'students_count': User.objects.filter(role=User.Role.STUDENT).count(),
        'teachers_count': User.objects.filter(role=User.Role.TEACHER).count(),
        'requests_count': BookRequest.objects.filter(is_processed=False).count(),
        'recent_logs': AuditLog.objects.select_related('actor')[:10],
        'popular_books': Book.objects.visible().order_by('-downloads_count')[:5],
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def librarian_dashboard(request):
    context = {
        'approved_books': Book.objects.visible().count(),
        'pending_books': Book.objects.filter(is_approved=False, is_deleted=False).count(),
        'articles_count': Article.objects.visible().count(),
        'requests_count': BookRequest.objects.filter(is_processed=False).count(),
        'recent_downloads': DownloadLog.objects.select_related('book', 'user')[:10],
        'popular_books': Book.objects.visible().order_by('-downloads_count')[:5],
    }
    return render(request, 'dashboard/librarian.html', context)


@login_required
def teacher_dashboard(request):
    context = {
        'my_books': Book.objects.filter(uploaded_by=request.user, is_deleted=False).count(),
        'my_pending_books': Book.objects.filter(uploaded_by=request.user, is_approved=False, is_deleted=False).count(),
        'my_articles': Article.objects.filter(uploaded_by=request.user, is_deleted=False).count(),
        'latest_books': Book.objects.visible().select_related('category')[:8],
    }
    return render(request, 'dashboard/teacher.html', context)


@login_required
def student_dashboard(request):
    context = {
        'favorite_count': FavoriteBook.objects.filter(user=request.user, book__is_deleted=False).count(),
        'my_requests': BookRequest.objects.filter(user=request.user).count(),
        'latest_books': Book.objects.visible().select_related('category')[:8],
        'popular_books': Book.objects.visible().order_by('-downloads_count')[:5],
    }
    return render(request, 'dashboard/student.html', context)
