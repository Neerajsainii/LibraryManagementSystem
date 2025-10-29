from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .debug_views import debug_template_dirs

app_name = 'accounts'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'api/users', views.UserViewSet)
router.register(r'api/profiles', views.ProfileViewSet, basename='profile')

# Web URL patterns
web_urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('debug-templates/', debug_template_dirs, name='debug_templates'),
    path('logout/', views.logout_view, name='logout'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]

# Final URL patterns
urlpatterns = web_urlpatterns + [
    path('api/', include(router.urls)),
]