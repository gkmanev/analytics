from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
from mlapp.models import PVForecastModel
import pandas as pd
import requests
import numpy as np
from scipy import stats
import openmeteo_requests
import requests_cache
from datetime import datetime, timedelta
from retry_requests import retry
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import plotly.offline as pyo
import json
import os
from lightning.pytorch.callbacks import EarlyStopping



class PVForecast:
    def __init__(self, end_date, ppe, farm, start_date='2024-12-01'):
        self.start_date = start_date
        self.end_date = end_date
        self.farm = farm
        self.ppe = ppe
        


    def prepare_pv_data(self):

        # start_date = '2024-12-01'
        # today = datetime.now().date() - timedelta(days=1)
        # end_date = today.strftime('%Y-%m-%d')


        url = f'http://209.38.208.230:8000/api/pvmeasurementdata/?start_date={self.start_date}&end_date={self.end_date}&ppe={self.ppe}'

        # Get the data from the API
        response = requests.get(url=url)

        # Create a dataframe from the response

        df_dam = pd.DataFrame(response.json())

        # Clean the DataFrame
        df_dam['production'] = df_dam['production'].replace(['-', 'n/e', 'N/A', 'NaN'], np.nan)
        df_dam['production'] = df_dam['production'].astype(float)
        df_dam['timestamp'] = pd.to_datetime(df_dam['timestamp'], errors='coerce', utc=True)
        df_dam['timestamp'] = df_dam['timestamp'].dt.tz_convert('Europe/Warsaw')
        df_dam['timestamp'] = df_dam['timestamp'].dt.tz_localize(None)  

        # drop all the columns instead of timestamp and production
        df_dam = df_dam[['timestamp', 'production', 'latitude', 'longitude']]
        if df_dam.isnull().values.any():
            print("Warning: NaNs detected in the DataFrame. Please fill or drop them.")
            return None
        return df_dam


    def fetch_weather_data(self, start, end, url_weather = "https://archive-api.open-meteo.com/v1/archive"):

        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        df_dam = self.prepare_pv_data()

        lat = float(df_dam['latitude'].iloc[0])
        long = float(df_dam['longitude'].iloc[0])
        
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
        resampled_df = hourly_dataframe.resample("15T").ffill()

        # Reset index to have 'date' as a column again
        resampled_df.reset_index(inplace=True)

        resampled_df["date"] = resampled_df["date"].dt.tz_localize(None)
        
        return resampled_df
    
    def prepare_merged_df(self):       

        df_dam = self.prepare_pv_data()
        if df_dam is None:
            return None

        resampled_df = self.fetch_weather_data(self.start_date, self.end_date)

        combined_weather_and_df_dam = pd.merge(df_dam, resampled_df, how='inner', left_on='timestamp', right_on='date')

        # Drop the duplicate date column
        combined_weather_and_df_dam.drop(columns='date', inplace=True)

        # Drop Latitude and Longitude columns
        combined_weather_and_df_dam.drop(columns=['latitude', 'longitude'], inplace=True)

        # Drop the rows with missing values
        combined_weather_and_df_dam.dropna(inplace=True)

        combined_weather_and_df_dam = combined_weather_and_df_dam.iloc[:-1]

        return combined_weather_and_df_dam
    
    def prepare_covariates(self):

        start_date_val = self.end_date
        end_date_val = datetime.strptime(self.end_date, '%Y-%m-%d') + timedelta(days=5)
        end_date_val = end_date_val.strftime('%Y-%m-%d') 

        forecast_df = self.fetch_weather_data(start_date_val, end_date_val, url_weather = "https://api.open-meteo.com/v1/forecast")

        # Rename Date to timestamp
        forecast_df.rename(columns={'date': 'timestamp'}, inplace=True)

        forecast_df["item_id"] = "series_1"

        forecast_df = forecast_df.iloc[:480]

        future_covariates = TimeSeriesDataFrame.from_data_frame(
            forecast_df,
            id_column="item_id",
            timestamp_column="timestamp"
        )        
        print(len(future_covariates))

        return future_covariates

    
    def train_model(self):
        # Prepare data for the Autogluon
        combined_weather_and_df_dam = self.prepare_merged_df()
        if combined_weather_and_df_dam is None:
            return None

        future_covariates = self.prepare_covariates()
        print(f"project: {self.ppe}, farm: {self.farm}")
        print(f"-------------------------------------------------------------")
        combined_weather_and_df_dam["item_id"] = "series_1"

        target_column = 'production'  

        known_covariates = ["temperature_2m", "cloud_cover", "cloud_cover_low", "wind_speed_10m", "direct_radiation", "diffuse_radiation", "global_tilted_irradiance"]

        if combined_weather_and_df_dam is None:
            print("Error: The DataFrame is empty. Please check the data.")
            return None
        if len(combined_weather_and_df_dam) > 0:
            if len(future_covariates) == 480:                
                train_data = TimeSeriesDataFrame.from_data_frame(
                    combined_weather_and_df_dam,
                    id_column="item_id",
                    timestamp_column="timestamp"
                )
                # check if there is AutogluonModels folder in project root and lists its folders content
                os.makedirs("/app/ml-models", exist_ok=True)
                print(os.listdir("/app/ml-models"))
                dir = os.listdir("/app/ml-models")
                model_name = 'fast_training_model_2025-03-07_14-34-05'
                model_save_path = f"/app/ml-models/{model_name}"
                if model_name in dir:                    
                    predictor = TimeSeriesPredictor.load(model_save_path)
                    predictions = predictor.predict(data=train_data, known_covariates=future_covariates)

                else:
                    model_save_path = f"/app/ml-models/fast_training_model_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"               
                                
                    #Initialize the predictor
                    predictor = TimeSeriesPredictor(
                        target=target_column,    
                        prediction_length=480,
                        freq='15min',
                        known_covariates_names=known_covariates,
                        path=model_save_path  # Set the path here
                    )

                    #Fit the predictor with cross-validation
                    results = predictor.fit(
                        train_data=train_data,  
                        presets="fast_training",
                        #time_limit=1200,
                        # hyperparameters={
                        #     "DeepAR": {
                        #         # You can specify DeepAR-specific hyperparameters here
                        #         # For example:
                        #         "context_length": 576,
                        #         "num_layers": 3,
                        #         "hidden_size": 480,
                        #         "dropout_rate": 0.2,
                        #         "learning_rate": 1e-3,
                        #         "epochs": 100,  # Added epochs parameter
                        #         "callbacks": [EarlyStopping(monitor="val_loss", patience=20, mode="min")]
                        #     }
                        # },                   
                    )                             
             
                predictions = predictor.predict(data=train_data, known_covariates=future_covariates)
                predictions.reset_index(inplace=True)
                predictions = predictions[['timestamp', '0.9']]
                predictions = predictions.to_dict(orient='records')               

                for predict in predictions:
                    timestamp = predict["timestamp"]
                    
                    prediction = predict["0.9"]    
                    # check if prediction < 5
                    if prediction < 10:
                        prediction = 0  
                    # if timestamp < 08:00 or timestamp > 20:00
                    if timestamp.hour < 8 or timestamp.hour > 20:
                        prediction = 0                                   
                    # Check if the datapoint exists
                    obj, created = PVForecastModel.objects.update_or_create(
                    timestamp=timestamp,
                    ppe=self.ppe,
                    defaults={
                        'farm': self.farm,
                        'production_forecast': prediction
                    }
                    )
                predictor.save()
                # print(f"Model saved: {model_save_path}")

            

