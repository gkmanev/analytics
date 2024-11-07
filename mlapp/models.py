import pandas as pd
from django.db import models
from datetime import datetime, timedelta
from pytz import timezone




class ResamplingManager(models.Manager):

    def get_queryset(self):
        today = datetime.now(timezone('Europe/Sofia')).date()
        tomorrow = today + timedelta(1)
        today_start = str(today)+'T'+'00:00:00Z'
        today_end = str(tomorrow)+'T'+'00:00:00Z'
        queryset = super().get_queryset().filter(timestamp__gt = today_start, timestamp__lt = today_end).order_by('timestamp')
        return queryset
    

    
    def resample_data(self, resampling_period, devId):       
       
        dataset = self.get_queryset()
        dataset = dataset.filter(devId=devId)
        data = list(dataset.values())
        df = pd.DataFrame(list(data))        

        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)  # Ensuring it's in UTC
        df.set_index('timestamp', inplace=True)
        # Resample to 15 minutes, summing the values in each interval
        resampled_df = df.resample(resampling_period).mean(numeric_only=True) 
        resampled_df = resampled_df.fillna(method='ffill')
        resampled_df['devId'] = devId        
        
        resampled_data = resampled_df.reset_index().to_dict(orient='records')  
        return resampled_data
             

            




class Forecast(models.Model):
    timestamp = models.DateTimeField(default = datetime.now(timezone('Europe/London')).date())
    power = models.FloatField()
    devId = models.CharField(max_length=50, default="devId")
    resample = ResamplingManager()
    objects = models.Manager()


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