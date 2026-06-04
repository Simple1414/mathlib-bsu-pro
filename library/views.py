from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import User
from .forms import BookForm, BookRequestForm, BookSearchForm
from .models import AuditLog, Book, BookRequest, Category, DownloadLog, FavoriteBook
from .permissions import can_manage_books, can_submit_books, role_required


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def audit(request, action, object_name=''):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        object_name=object_name,
        ip_address=get_client_ip(request)
    )


def home(request):
    stats = {
        'books': Book.objects.filter(is_approved=True).count(),
        'categories': Category.objects.count(),
        'students': User.objects.filter(role=User.Role.STUDENT).count(),
        'teachers': User.objects.filter(role=User.Role.TEACHER).count(),
    }
    latest_books = Book.objects.filter(is_approved=True).select_related('category').prefetch_related('authors')[:6]
    return render(request, 'library/home.html', {'stats': stats, 'latest_books': latest_books})


def book_list(request):
    form = BookSearchForm(request.GET or None)
    books = Book.objects.filter(is_approved=True).select_related('category').prefetch_related('authors')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        language = form.cleaned_data.get('language')
        if q:
            books = books.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(keywords__icontains=q) |
                Q(subject__icontains=q) |
                Q(authors__full_name__icontains=q)
            ).distinct()
        if category:
            books = books.filter(category=category)
        if language:
            books = books.filter(language=language)

    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/book_list.html', {'form': form, 'page_obj': page_obj})


def book_detail(request, pk):
    book = get_object_or_404(Book.objects.select_related('category').prefetch_related('authors'), pk=pk)
    if not book.is_approved and not (request.user.is_authenticated and book.can_be_managed_by(request.user)):
        raise Http404('Китоб ёфт нашуд.')

    Book.objects.filter(pk=book.pk).update(views_count=F('views_count') + 1)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteBook.objects.filter(user=request.user, book=book).exists()
    return render(request, 'library/book_detail.html', {'book': book, 'is_favorite': is_favorite, 'can_edit': request.user.is_authenticated and book.can_be_managed_by(request.user)})


@login_required
def download_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.is_approved and not book.can_be_managed_by(request.user):
        raise Http404('Файл дастрас нест.')
    if not book.is_download_allowed and not book.can_be_managed_by(request.user):
        messages.error(request, 'Зеркашии ин китоб иҷозат дода нашудааст.')
        return redirect(book.get_absolute_url())

    DownloadLog.objects.create(user=request.user, book=book, ip_address=get_client_ip(request))
    Book.objects.filter(pk=book.pk).update(downloads_count=F('downloads_count') + 1)
    audit(request, 'Зеркашии китоб', book.title)
    return FileResponse(book.file.open('rb'), as_attachment=True, filename=book.file.name.split('/')[-1])


@login_required
def toggle_favorite(request, pk):
    book = get_object_or_404(Book, pk=pk, is_approved=True)
    favorite, created = FavoriteBook.objects.get_or_create(user=request.user, book=book)
    if created:
        messages.success(request, 'Китоб ба дӯстдоштаҳо илова шуд.')
    else:
        favorite.delete()
        messages.info(request, 'Китоб аз дӯстдоштаҳо хориҷ шуд.')
    return redirect(book.get_absolute_url())


@login_required
def favorites(request):
    items = FavoriteBook.objects.filter(user=request.user).select_related('book', 'book__category').prefetch_related('book__authors')
    return render(request, 'library/favorites.html', {'items': items})


@login_required
def book_create(request):
    if not can_submit_books(request.user):
        messages.error(request, 'Танҳо китобдор, омӯзгор ё админ метавонад китоб пешниҳод кунад.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            auto_approve = can_manage_books(request.user)
            book = form.save(uploaded_by=request.user, auto_approve=auto_approve)
            audit(request, 'Иловаи китоб', book.title)
            if auto_approve:
                messages.success(request, 'Китоб илова ва тасдиқ шуд.')
            else:
                messages.success(request, 'Китоб пешниҳод шуд. Пас аз тасдиқи китобдор нашр мешавад.')
            return redirect(book.get_absolute_url())
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Иловаи китоб'})


@login_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.can_be_managed_by(request.user):
        messages.error(request, 'Шумо барои таҳрири ин китоб иҷозат надоред.')
        return redirect(book.get_absolute_url())

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            updated = form.save(uploaded_by=book.uploaded_by, auto_approve=book.is_approved)
            audit(request, 'Таҳрири китоб', updated.title)
            messages.success(request, 'Китоб навсозӣ шуд.')
            return redirect(updated.get_absolute_url())
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Таҳрири китоб'})


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def pending_books(request):
    books = Book.objects.filter(is_approved=False).select_related('uploaded_by', 'category').prefetch_related('authors')
    return render(request, 'library/pending_books.html', {'books': books})


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def approve_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.is_approved = True
    book.save(update_fields=['is_approved'])
    audit(request, 'Тасдиқи китоб', book.title)
    messages.success(request, 'Китоб тасдиқ шуд.')
    return redirect('library:pending_books')


@login_required
def request_book(request):
    if request.method == 'POST':
        form = BookRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            audit(request, 'Дархости китоб', req.title)
            messages.success(request, 'Дархости китоб фиристода шуд.')
            return redirect('library:book_list')
    else:
        form = BookRequestForm()
    return render(request, 'library/book_request_form.html', {'form': form})


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def book_requests(request):
    requests_qs = BookRequest.objects.select_related('user').all()
    return render(request, 'library/book_requests.html', {'requests_qs': requests_qs})


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def mark_request_processed(request, pk):
    req = get_object_or_404(BookRequest, pk=pk)
    req.is_processed = True
    req.save(update_fields=['is_processed'])
    messages.success(request, 'Дархост ҳамчун баррасишуда қайд шуд.')
    return redirect('library:book_requests')
