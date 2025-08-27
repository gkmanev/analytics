from rest_framework import viewsets
from .models import Forecast, Feature, Correlation, PVForecastModel
from .serializers import ForecastSerializer, FeatureSerializer, CorrelationSerializer, PVForecastModelSerializer
from datetime import datetime
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

class ForecastViewSet(viewsets.ModelViewSet):
    queryset = Forecast.objects.all()[:50]
    serializer_class = ForecastSerializer

    def get_queryset(self):
        queryset =  super().get_queryset().order_by('timestamp')
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
                queryset = queryset.filter(timestamp__gte=first_day_of_month)
            elif date_range == 'year':
                first_day_of_year = today.replace(month=1, day=1)
                queryset = queryset.filter(timestamp__gte=first_day_of_year)
        return queryset
    

    def list(self, request, *args, **kwargs):
        dev_id = self.request.query_params.get('devId', None)
        date_range = self.request.query_params.get('date_range',None)        
        resamling = self.request.query_params.get('resample',None)  
        # Use custom resampling logic if requested
        if date_range == 'today' and resamling and dev_id:
            response = Forecast.resample.resample_data(resamling, dev_id)
            return Response(response, status=status.HTTP_200_OK)

        # Fallback to default list behavior with filtered queryset
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)





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

class PVForecastModelViewSet(viewsets.ModelViewSet):
    queryset = PVForecastModel.objects.all().order_by('timestamp')
    serializer_class = PVForecastModelSerializer
    
    def get_queryset(self):
        farm = self.request.query_params.get('farm', None)
        ppe = self.request.query_params.get('ppe', None)
        queryset = super().get_queryset()
        if farm:
            queryset = queryset.filter(farm=farm)
        if ppe:
            queryset = queryset.filter(ppe=ppe)
        return queryset