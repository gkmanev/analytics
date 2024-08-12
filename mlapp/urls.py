from django.urls import path
from rest_framework import routers
from .views import ForecastViewSet, FeatureViewSet, CorrelationViewSet  # Import the ViewSet directly

router = routers.DefaultRouter()

router.register(r'forecast', ForecastViewSet)  # Register your viewsets here
router.register(r'features', FeatureViewSet)
router.register(r'correlations', CorrelationViewSet)

urlpatterns = router.urls
