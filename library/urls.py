from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_create, name='book_create'),
    path('books/pending/', views.pending_books, name='pending_books'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_update, name='book_update'),
    path('books/<int:pk>/download/', views.download_book, name='download_book'),
    path('books/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('books/<int:pk>/approve/', views.approve_book, name='approve_book'),
    path('favorites/', views.favorites, name='favorites'),
    path('requests/new/', views.request_book, name='request_book'),
    path('requests/', views.book_requests, name='book_requests'),
    path('requests/<int:pk>/processed/', views.mark_request_processed, name='mark_request_processed'),
]
