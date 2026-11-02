from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from .forms import (
    ArticleForm, ArticleSearchForm, BookCommentForm, BookForm, BookRatingForm,
    BookRequestForm, BookSearchForm,
)
from .models import (
    Article, AuditLog, Book, BookComment, BookRating, BookRequest, BookView,
    Category, DownloadLog, FavoriteBook,
)
from .permissions import can_manage_books, can_submit_books, role_required


SUPPORTED_LANGUAGES = {'tg', 'ru', 'en'}


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


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def record_unique_book_view(request, book):
    try:
        if request.user.is_authenticated:
            _, created = BookView.objects.get_or_create(
                book=book,
                user=request.user,
                defaults={'ip_address': get_client_ip(request), 'session_key': f'user-{request.user.pk}'}
            )
        else:
            session_key = ensure_session_key(request)
            _, created = BookView.objects.get_or_create(
                book=book,
                session_key=session_key,
                defaults={'ip_address': get_client_ip(request)}
            )
        if created:
            Book.objects.filter(pk=book.pk).update(views_count=F('views_count') + 1)
            book.views_count = (book.views_count or 0) + 1
    except IntegrityError:
        # Race condition protection: if two requests hit at once, do not count twice.
        pass


def public_or_manageable_book(request, pk):
    book = get_object_or_404(Book.objects.select_related('category', 'uploaded_by').prefetch_related('authors'), pk=pk, is_deleted=False)
    if not book.is_approved or not book.is_active:
        if not (request.user.is_authenticated and book.can_be_managed_by(request.user)):
            raise Http404('Китоб ёфт нашуд.')
    return book


def public_or_manageable_article(request, pk):
    article = get_object_or_404(Article.objects.select_related('uploaded_by'), pk=pk, is_deleted=False)
    if not article.is_approved or not article.is_active:
        if not (request.user.is_authenticated and article.can_be_managed_by(request.user)):
            raise Http404('Мақола ёфт нашуд.')
    return article


def set_language(request, code):
    if code not in SUPPORTED_LANGUAGES:
        code = 'tg'
    request.session['site_language'] = code
    return redirect(request.META.get('HTTP_REFERER') or 'library:home')


def home(request):
    stats = {
        'books': Book.objects.visible().count(),
        'articles': Article.objects.visible().count(),
        'categories': Category.objects.count(),
        'students': User.objects.filter(role=User.Role.STUDENT).count(),
        'teachers': User.objects.filter(role=User.Role.TEACHER).count(),
    }
    latest_books = Book.objects.visible().select_related('category').prefetch_related('authors')[:6]
    latest_articles = Article.objects.visible()[:3]
    return render(request, 'library/home.html', {
        'stats': stats,
        'latest_books': latest_books,
        'latest_articles': latest_articles,
    })


def about(request):
    return render(request, 'library/about.html')


def contact(request):
    return render(request, 'library/contact.html')


def book_list(request):
    form = BookSearchForm(request.GET or None)
    books = Book.objects.visible().select_related('category').prefetch_related('authors')

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
    book = public_or_manageable_book(request, pk)
    record_unique_book_view(request, book)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Барои гузоштани комментария ё ситора ворид шавед.')
            return redirect('accounts:login')
        if 'comment_submit' in request.POST:
            comment_form = BookCommentForm(request.POST)
            rating_form = BookRatingForm()
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.book = book
                comment.user = request.user
                comment.save()
                messages.success(request, 'Комментарияи шумо илова шуд.')
                return redirect(book.get_absolute_url())
        elif 'rating_submit' in request.POST:
            rating_form = BookRatingForm(request.POST)
            comment_form = BookCommentForm()
            if rating_form.is_valid():
                BookRating.objects.update_or_create(
                    book=book,
                    user=request.user,
                    defaults={'rating': rating_form.cleaned_data['rating']}
                )
                messages.success(request, 'Ситораи шумо сабт шуд.')
                return redirect(book.get_absolute_url())
        else:
            comment_form = BookCommentForm()
            rating_form = BookRatingForm()
    else:
        comment_form = BookCommentForm()
        initial_rating = None
        if request.user.is_authenticated:
            existing = BookRating.objects.filter(book=book, user=request.user).first()
            if existing:
                initial_rating = existing.rating
        rating_form = BookRatingForm(initial={'rating': initial_rating})

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteBook.objects.filter(user=request.user, book=book).exists()
    comments = book.comments.filter(is_approved=True).select_related('user')[:20]
    return render(request, 'library/book_detail.html', {
        'book': book,
        'is_favorite': is_favorite,
        'can_edit': request.user.is_authenticated and book.can_be_managed_by(request.user),
        'comments': comments,
        'comment_form': comment_form,
        'rating_form': rating_form,
    })


def preview_book(request, pk):
    book = public_or_manageable_book(request, pk)
    if not book.file:
        raise Http404('Файл дастрас нест.')
    return FileResponse(book.file.open('rb'), as_attachment=False, filename=book.file.name.split('/')[-1])


@login_required
def download_book(request, pk):
    book = public_or_manageable_book(request, pk)
    if not book.is_download_allowed and not book.can_be_managed_by(request.user):
        messages.error(request, 'Зеркашии ин китоб иҷозат дода нашудааст.')
        return redirect(book.get_absolute_url())

    DownloadLog.objects.create(user=request.user, book=book, ip_address=get_client_ip(request))
    Book.objects.filter(pk=book.pk).update(downloads_count=F('downloads_count') + 1)
    audit(request, 'Зеркашии китоб', book.title)
    return FileResponse(book.file.open('rb'), as_attachment=True, filename=book.file.name.split('/')[-1])


@require_POST
@login_required
def toggle_favorite(request, pk):
    book = get_object_or_404(Book, pk=pk, is_approved=True, is_active=True, is_deleted=False)
    favorite, created = FavoriteBook.objects.get_or_create(user=request.user, book=book)
    if created:
        messages.success(request, 'Китоб ба дӯстдоштаҳо илова шуд.')
    else:
        favorite.delete()
        messages.info(request, 'Китоб аз дӯстдоштаҳо хориҷ шуд.')
    return redirect(book.get_absolute_url())


@login_required
def favorites(request):
    items = FavoriteBook.objects.filter(user=request.user, book__is_deleted=False).select_related('book', 'book__category').prefetch_related('book__authors')
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
    book = get_object_or_404(Book, pk=pk, is_deleted=False)
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


@login_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk, is_deleted=False)
    if not book.can_be_managed_by(request.user):
        messages.error(request, 'Шумо барои нест кардани ин китоб иҷозат надоред.')
        return redirect(book.get_absolute_url())
    if request.method == 'POST':
        book.is_deleted = True
        book.is_active = False
        book.deleted_at = timezone.now()
        book.save(update_fields=['is_deleted', 'is_active', 'deleted_at'])
        audit(request, 'Нест кардани китоб', book.title)
        messages.success(request, 'Китоб аз намоиш хориҷ карда шуд.')
        return redirect('library:book_list')
    return render(request, 'library/book_confirm_delete.html', {'book': book})


@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def pending_books(request):
    books = Book.objects.filter(is_approved=False, is_deleted=False).select_related('uploaded_by', 'category').prefetch_related('authors')
    return render(request, 'library/pending_books.html', {'books': books})


@require_POST
@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def approve_book(request, pk):
    book = get_object_or_404(Book, pk=pk, is_deleted=False)
    book.is_approved = True
    book.is_active = True
    book.save(update_fields=['is_approved', 'is_active'])
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


@require_POST
@role_required(User.Role.ADMIN, User.Role.LIBRARIAN)
def mark_request_processed(request, pk):
    req = get_object_or_404(BookRequest, pk=pk)
    req.is_processed = True
    req.save(update_fields=['is_processed'])
    messages.success(request, 'Дархост ҳамчун баррасишуда қайд шуд.')
    return redirect('library:book_requests')


def article_list(request):
    form = ArticleSearchForm(request.GET or None)
    articles = Article.objects.visible()
    if form.is_valid():
        q = form.cleaned_data.get('q')
        language = form.cleaned_data.get('language')
        if q:
            articles = articles.filter(
                Q(title__icontains=q) |
                Q(authors_text__icontains=q) |
                Q(abstract__icontains=q) |
                Q(content__icontains=q) |
                Q(keywords__icontains=q)
            )
        if language:
            articles = articles.filter(language=language)
    paginator = Paginator(articles, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'library/article_list.html', {'form': form, 'page_obj': page_obj})


def article_detail(request, pk):
    article = public_or_manageable_article(request, pk)
    Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
    can_edit = request.user.is_authenticated and article.can_be_managed_by(request.user)
    return render(request, 'library/article_detail.html', {'article': article, 'can_edit': can_edit})


def preview_article(request, pk):
    article = public_or_manageable_article(request, pk)
    if not article.file:
        raise Http404('Файл дастрас нест.')
    return FileResponse(article.file.open('rb'), as_attachment=False, filename=article.file.name.split('/')[-1])


@login_required
def download_article(request, pk):
    article = public_or_manageable_article(request, pk)
    if not article.file:
        raise Http404('Файл дастрас нест.')
    Article.objects.filter(pk=article.pk).update(downloads_count=F('downloads_count') + 1)
    audit(request, 'Зеркашии мақола', article.title)
    return FileResponse(article.file.open('rb'), as_attachment=True, filename=article.file.name.split('/')[-1])


@login_required
def article_create(request):
    if not can_submit_books(request.user):
        messages.error(request, 'Танҳо омӯзгор, китобдор ё админ метавонад мақола илова кунад.')
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(uploaded_by=request.user, auto_approve=can_manage_books(request.user))
            audit(request, 'Иловаи мақола', article.title)
            messages.success(request, 'Мақола илова шуд.')
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm()
    return render(request, 'library/article_form.html', {'form': form, 'title': 'Иловаи мақола'})


@login_required
def article_update(request, pk):
    article = get_object_or_404(Article, pk=pk, is_deleted=False)
    if not article.can_be_managed_by(request.user):
        messages.error(request, 'Шумо барои таҳрири ин мақола иҷозат надоред.')
        return redirect(article.get_absolute_url())
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            updated = form.save(uploaded_by=article.uploaded_by, auto_approve=article.is_approved)
            audit(request, 'Таҳрири мақола', updated.title)
            messages.success(request, 'Мақола навсозӣ шуд.')
            return redirect(updated.get_absolute_url())
    else:
        form = ArticleForm(instance=article)
    return render(request, 'library/article_form.html', {'form': form, 'title': 'Таҳрири мақола'})


@login_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk, is_deleted=False)
    if not article.can_be_managed_by(request.user):
        messages.error(request, 'Шумо барои нест кардани мақола иҷозат надоред.')
        return redirect(article.get_absolute_url())
    if request.method == 'POST':
        article.is_deleted = True
        article.is_active = False
        article.deleted_at = timezone.now()
        article.save(update_fields=['is_deleted', 'is_active', 'deleted_at'])
        audit(request, 'Нест кардани мақола', article.title)
        messages.success(request, 'Мақола аз намоиш хориҷ карда шуд.')
        return redirect('library:article_list')
    return render(request, 'library/article_confirm_delete.html', {'article': article})
