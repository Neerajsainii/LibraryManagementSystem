from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list_view, name='book_list'),
    path('<int:pk>/', views.book_detail_view, name='book_detail'),
    path('categories/', views.category_list_view, name='category_list'),
    path('authors/', views.author_list_view, name='author_list'),
    path('search/', views.book_search_view, name='book_search'),
    # Admin/Staff URLs
    path('manage/', views.manage_books_view, name='manage_books'),
    path('create/', views.book_create_view, name='book_create'),
    path('<int:pk>/edit/', views.book_edit_view, name='book_edit'),
    path('<int:pk>/delete/', views.book_delete_view, name='book_delete'),
]