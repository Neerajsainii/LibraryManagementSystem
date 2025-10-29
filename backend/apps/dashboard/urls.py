from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('book-activities/', views.book_activities_view, name='book_activities'),
    path('popular-books/', views.popular_books_view, name='popular_books'),
    path('overdue-loans/', views.overdue_loans_view, name='overdue_loans'),
]