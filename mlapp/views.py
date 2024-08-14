from rest_framework import viewsets
from .models import Forecast, Feature, Correlation
from .serializers import ForecastSerializer, FeatureSerializer, CorrelationSerializer
from .tasks import today_correlation_task
from datetime import datetime
from django.utils import timezone


class ForecastViewSet(viewsets.ModelViewSet):
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer

    def get_queryset(self):
        queryset =  super().get_queryset()
        dev_id = self.request.query_params.get('devId', None)
        date_range = self.request.query_params.get('date_range',None)        
       
        # Optionally, filter queryset based on devId
        if dev_id:
            queryset = queryset.filter(devId=dev_id)

        # Filter by date_range if provided
        if date_range:
            today = timezone.now().date() 
            if date_range == 'today':
                queryset = queryset.filter(timestamp__gte=today)
            elif date_range == 'month':
                first_day_of_month = today.replace(day=1)
                queryset = queryset.filter(timestamp__gte=first_day_of_month, timestamp__lte=today)
            elif date_range == 'year':
                first_day_of_year = today.replace(month=1, day=1)
                queryset = queryset.filter(timestamp__gte=first_day_of_year, timestamp__lte=today)
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
