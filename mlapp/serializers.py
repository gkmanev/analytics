from rest_framework import serializers
from .models import Forecast, Feature, Correlation


class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forecast
        fields = '__all__'


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name']

class CorrelationSerializer(serializers.ModelSerializer):
    feature1 = FeatureSerializer()
    feature2 = FeatureSerializer()

    class Meta:
        model = Correlation
        fields = ['id', 'feature1', 'feature2', 'correlation_value', 'devId', 'period']