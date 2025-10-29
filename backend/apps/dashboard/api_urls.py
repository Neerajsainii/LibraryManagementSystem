from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'dashboard-api'

router = DefaultRouter()
router.register(r'statistics', api_views.DailyStatsViewSet)
router.register(r'book-activities', api_views.BookActivityViewSet)
router.register(r'popular-books', api_views.PopularBooksViewSet, basename='popular-books')
router.register(r'overdue-loans', api_views.OverdueLoansViewSet, basename='overdue-loans')

urlpatterns = router.urls