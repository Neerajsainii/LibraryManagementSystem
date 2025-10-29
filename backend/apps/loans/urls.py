from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'loans'

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'api/book-loans', views.BookLoanViewSet)
router.register(r'api/reservations', views.ReservationViewSet)

# URLs for web views
web_urlpatterns = [
    # Loan URLs
    path('', views.loan_list_view, name='loan_list'),
    path('<int:pk>/', views.loan_detail_view, name='loan_detail'),
    path('create/', views.create_loan_view, name='create_loan'),
    path('<int:pk>/return/', views.return_loan_view, name='return_loan'),
    
    # Reservation URLs
    path('reservations/', views.reservation_list_view, name='reservation_list'),
    path('reservations/create/', views.create_reservation_view, name='create_reservation'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
]

# Combine web and API URLs
urlpatterns = web_urlpatterns + router.urls