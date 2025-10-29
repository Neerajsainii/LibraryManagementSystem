from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import api

router = DefaultRouter()
router.register(r'books', api.BookViewSet)
router.register(r'categories', api.CategoryViewSet)
router.register(r'loans', api.BookLoanViewSet, basename='loan')

urlpatterns = [
    path('', include(router.urls)),
]