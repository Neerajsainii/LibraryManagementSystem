from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'books-api'

router = DefaultRouter()
router.register(r'books', api_views.BookViewSet)
router.register(r'authors', api_views.AuthorViewSet)
router.register(r'categories', api_views.CategoryViewSet)
router.register(r'copies', api_views.BookCopyViewSet)

urlpatterns = router.urls