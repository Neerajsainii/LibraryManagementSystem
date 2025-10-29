from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'fines-api'

router = DefaultRouter()
router.register(r'fines', api_views.FineViewSet)
router.register(r'payments', api_views.PaymentViewSet)

urlpatterns = router.urls