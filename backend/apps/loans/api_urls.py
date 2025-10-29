from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'loans-api'

router = DefaultRouter()
router.register(r'loans', api_views.BookLoanViewSet)
router.register(r'reservations', api_views.ReservationViewSet)

urlpatterns = router.urls