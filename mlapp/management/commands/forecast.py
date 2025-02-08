from django.core.management.base import BaseCommand
from mlapp.pv_forecast import PVForecast
from datetime import datetime, timedelta    

class Command(BaseCommand):
    help = 'fetch data from API and store in database'

    def handle(self, *args, **kwargs):
        today = datetime.now().date() - timedelta(days=1)
        end_date = today.strftime('%Y-%m-%d')
        ppe = '590310600030911897'
        forecast = PVForecast(end_date, ppe)
        forecast.train_model()           
        self.stdout.write(self.style.SUCCESS('Fetched and stored data successfully'))