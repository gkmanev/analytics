from django.db import models
from datetime import datetime, timedelta
from pytz import timezone

class Forecast(models.Model):
    timestamp = models.DateTimeField(default = datetime.now(timezone('Europe/London')).date())
    power = models.FloatField()
    devId = models.CharField(max_length=50, default="devId")


class Feature(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Correlation(models.Model):
    feature1 = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='feature1')
    feature2 = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='feature2')
    correlation_value = models.FloatField()
    devId = models.CharField(max_length=50, default="devId")
    period = models.CharField(max_length=50, default='today')

    class Meta:
        #unique_together = ('feature1', 'feature2', 'devId')
        ordering = ['feature1', 'feature2']

    def __str__(self):
        return f'{self.feature1.name} - {self.feature2.name}: {self.correlation_value}'