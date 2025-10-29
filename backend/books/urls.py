from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('<int:pk>/', views.book_detail, name='book_detail'),
    path('<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('loans/<int:loan_id>/return/', views.return_book, name='return_book'),
    path('my-loans/', views.my_loans, name='my_loans'),
]