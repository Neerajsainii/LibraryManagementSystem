from django.urls import path
from . import views

app_name = 'fines'

urlpatterns = [
    path('', views.fine_list_view, name='fine_list'),
    path('<int:pk>/', views.fine_detail_view, name='fine_detail'),
    path('<int:pk>/pay/', views.process_payment_view, name='process_payment'),
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-cancel/', views.payment_cancel_view, name='payment_cancel'),
]