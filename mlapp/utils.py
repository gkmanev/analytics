from mlapp.helper import performML
from mlapp.models import Forecast
from datetime import datetime, timedelta
from pytz import timezone
import os
import json
import pandas as pd
from mlapp.pv_forecast import PVForecast
from django.conf import settings
import openmeteo_requests
import requests_cache
from retry_requests import retry


def today_correlation_first_five():
    file_path = os.path.join('mlapp', 'coords.json')
    with open(file_path, 'r') as file:
        coords = json.load(file)
    
    for dev in coords[1:12]:
        for k,v in dev.items():
            devId = k 
            lat = v["lat"]
            long = v["long"]
            start = '2026-01-01'
            end = '2026-01-19'
            url_dev = f"http://85.14.6.37:16455/api/posts/?date_range=month&resample=15min&dev={devId}"
            weather_df = fetch_weather_data(start, end, lat, long)  
                   
            # calc_correlations = performML(url_dev, url_weather, period, devId)
            # calc_correlations.corelations()
            make_forecast = performML(url=url_dev, devId=devId, weather_df=weather_df)           
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
            url_dev = f"http://85.14.6.37:16457/api/posts/?date_range=year&resample=year&dev={devId}"
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

def fetch_weather_data(start, end, lat, long, url_weather = "https://archive-api.open-meteo.com/v1/archive"):

        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)        

        
        
        # start = datetime.strptime(end_date, '%Y-%m-%d')
        params = {
            "latitude": lat,
            "longitude": long,
            "start_date":start,	
            "end_date": end,
            "hourly": ["temperature_2m", "cloud_cover", "cloud_cover_low", "wind_speed_10m", "direct_radiation", "diffuse_radiation", "global_tilted_irradiance"],
            "tilt": 30
        }
        responses = openmeteo.weather_api(url_weather, params=params)
        response_weather = responses[0]


        hourly = response_weather.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_cloud_cover = hourly.Variables(1).ValuesAsNumpy()
        hourly_cloud_cover_low = hourly.Variables(2).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
        hourly_direct_radiation = hourly.Variables(4).ValuesAsNumpy()
        hourly_diffuse_radiation = hourly.Variables(5).ValuesAsNumpy()
        hourly_global_tilted_irradiance = hourly.Variables(6).ValuesAsNumpy()
        

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["cloud_cover"] = hourly_cloud_cover
        hourly_data["cloud_cover_low"] = hourly_cloud_cover_low
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        hourly_data["direct_radiation"] = hourly_direct_radiation
        hourly_data["diffuse_radiation"] = hourly_diffuse_radiation
        hourly_data["global_tilted_irradiance"] = hourly_global_tilted_irradiance
        

        hourly_dataframe = pd.DataFrame(data = hourly_data)

        # Set index to datetime
        hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe["date"])
        hourly_dataframe.set_index("date", inplace=True)

        # Resample to 15-minute intervals using linear interpolation
        resampled_df = hourly_dataframe.resample("60T").ffill()

        # Reset index to have 'date' as a column again
        resampled_df.reset_index(inplace=True)

        resampled_df["date"] = resampled_df["date"].dt.tz_localize(None)
        
       
        return resampled_df


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

def pv_forecast_first_five():    
    first_five_projects = prepare_project_mapping()#[:2] 
    today = datetime.now().date()
    end_date = today - timedelta(days=1)    
    
    for it in first_five_projects:
        ppe = it.get("PPE", None)
        farm = it.get("farm", None)
        if ppe is not None:                                    
            forecast = PVForecast(end_date, ppe=ppe, farm=farm)
            forecast.train_model()

def pv_forecast_five_ten():
    five_ten_projects = prepare_project_mapping()[5:]
    today = datetime.now().date() - timedelta(days=3)
    end_date = today.strftime('%Y-%m-%d')   
    
    for it in five_ten_projects:        
        ppe = it.get("PPE", None)
        farm = it.get("farm", None)
        if ppe is not None:                                    
            forecast = PVForecast(end_date, ppe=ppe, farm=farm)
            forecast.train_model()

def prepare_project_mapping():
    project_mapping_path = os.path.join(settings.BASE_DIR, 'projects_mapping.json')
    project_mapping = []
    try:
        if os.path.exists(project_mapping_path):
            with open(project_mapping_path, 'r') as f:
                project_mapping = json.load(f)
        else:
            print(f"Project mapping file not found: {project_mapping_path}")
            return None
    except Exception as e:
        print(f"Error loading project mapping file: {e}")
        return None
    return project_mapping





    
    



    
    











