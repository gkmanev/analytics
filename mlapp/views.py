from rest_framework import viewsets
from .models import Forecast, Feature, Correlation
from .serializers import ForecastSerializer, FeatureSerializer, CorrelationSerializer
from .tasks import today_correlation_task




class ForecastViewSet(viewsets.ModelViewSet):
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer

    def get_queryset(self):
        queryset =  super().get_queryset()
        dev_id = self.request.query_params.get('devId')

        # Optionally, filter queryset based on devId
        if dev_id:
            queryset = queryset.filter(devId=dev_id)
        return queryset


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

class CorrelationViewSet(viewsets.ModelViewSet):
    queryset = Correlation.objects.all()
    serializer_class = CorrelationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Retrieve devId query parameter from request
        dev_id = self.request.query_params.get('devId')

        # Optionally, filter queryset based on devId
        if dev_id:
            queryset = queryset.filter(devId=dev_id)

        return queryset
