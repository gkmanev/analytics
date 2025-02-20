from mlapp.helper import performML
from mlapp.models import Forecast
from datetime import datetime, timedelta
from pytz import timezone
import os
import json
import pandas as pd
from mlapp.pv_forecast import PVForecast
from django.conf import settings

def today_correlation_first_five():
    file_path = os.path.join('mlapp', 'coords.json')
    with open(file_path, 'r') as file:
        coords = json.load(file)
    
    for dev in coords[1:6]:
        for k,v in dev.items():
            devId = k 
            lat = v["lat"]
            long = v["long"]
            period = "month"
            url_dev = f"http://85.14.6.37:16455/api/posts/?date_range=year&not_res=true&dev={devId}"
            url_weather = f"http://85.14.6.37:16456/api/weather/?date_range=year&lat={lat}&long={long}"
            calc_correlations = performML(url_dev, url_weather, period, devId)
            calc_correlations.corelations()
            make_forecast = performML(url_dev, url_weather, period, devId)
            make_forecast.time_series_forecast()


# from 5th to 10th

def today_correlation_five_ten():
    file_path = os.path.join('mlapp', 'coords.json')
    with open(file_path, 'r') as file:
        coords = json.load(file)
    
    for dev in coords[6:10]:
        for k,v in dev.items():
            devId = k 
            lat = v["lat"]
            long = v["long"]
            period = "month"
            url_dev = f"http://85.14.6.37:16455/api/posts/?date_range=year&not_res=true&dev={devId}"
            url_weather = f"http://85.14.6.37:16456/api/weather/?date_range=year&lat={lat}&long={long}"
            calc_correlations = performML(url_dev, url_weather, period, devId)
            calc_correlations.corelations()
            make_forecast = performML(url_dev, url_weather, period, devId)
            make_forecast.time_series_forecast()



def create_devs():
    all_devs = list()
    for i in range(30):
        if i < 10:
            all_devs.append(f"sm-000{i}")
        else:
            all_devs.append(f"sm-00{i}")
    return all_devs


def today_resample_data(resolution):
    devs = create_devs()
    today = datetime.now(timezone('Europe/Sofia')).date()
    tomorrow = today + timedelta(1)
    today_start = str(today)+'T'+'00:00:00Z'
    today_end = str(tomorrow)+'T'+'00:00:00Z'
    for dev in devs:
        dataset = Forecast.objects.filter(devId=dev, timestamp__gte=today_start, timestamp_lte=today_end).order_by('timestamp')
        data = list(dataset.values())
        df = pd.DataFrame(list(data))

        if 'created_date' not in df.columns:            
            continue  # Skip this device if no 'created_date' found

        df['created_date'] = pd.to_datetime(df['created_date'], utc=True)  # Ensuring it's in UTC
        df.set_index('created_date', inplace=True)
        # Resample to 15 minutes, summing the values in each interval
        resampled_df = df.resample(resolution).mean(numeric_only=True) 
        resampled_df = resampled_df.fillna(method='ffill')
        resampled_df['devId'] = dev       
        resampled_data = resampled_df.reset_index().to_dict(orient='records') 
        return resampled_data      

       
def pv_ml_forecast():
    project_mapping_path = os.path.join(settings.BASE_DIR, 'projects_mapping.json')
    project_mapping = []
    try:
        if os.path.exists(project_mapping_path):
            with open(project_mapping_path, 'r') as f:
                project_mapping = json.load(f)
        else:
            print(f"Project mapping file not found: {project_mapping_path}")
    except Exception as e:
        print(f"Error loading project mapping file: {e}")

    today = datetime.now().date() - timedelta(days=1)
    end_date = today.strftime('%Y-%m-%d')
    
    for it in project_mapping:
        ppe = it.get("PPE", None)
        farm = it.get("farm", None)
        if ppe is not None: # and ppe == "590310600030911897":                                    
            forecast = PVForecast(end_date, ppe=ppe, farm=farm)
            forecast.train_model()
    



    
    











