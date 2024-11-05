import requests
import pandas as pd
import json
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
from django.db import transaction
from mlapp.models import Forecast, Correlation, Feature
import seaborn as sns
import matplotlib.pyplot as plt



class performML:
    def __init__(self, url, url_weather, period, devId):
        self.url = url
        self.url_weather = url_weather
        self.period = period
        self.devId = devId
        # self.merge_df()

    def prepare_weather(self):
        response = requests.get(self.url_weather).json()
        dfWeather = None
        if response:
            dfWeather = pd.DataFrame(response)
            # Convert the 'created_date' column to datetime
            dfWeather['timestamp'] = pd.to_datetime(dfWeather['timestamp'], errors='coerce')
            dfWeather = dfWeather[~dfWeather['timestamp'].duplicated(keep='first')]
            dfWeather.dropna(subset=['timestamp'], inplace=True)
            dfWeather.set_index('timestamp', inplace=True)
            dfWeather = dfWeather.resample('min').interpolate(method='linear')
            dfWeather.reset_index(inplace=True)
            dfWeather['timestamp'] = dfWeather["timestamp"].values.astype('datetime64[m]')
        return dfWeather

    def prepare_power(self):
        response = requests.get(self.url).json()
        df1 = None
        date_field_name = "created_date"
        if response:
            df1 = pd.DataFrame(response)
            
            #Convert the 'created_date' column to datetime
            df1['timestamp'] = pd.to_datetime(df1[date_field_name], errors='coerce')
            
            #Ensure that 'timestamp' column is in datetime64 format
            df1['timestamp'] = df1["timestamp"].values.astype('datetime64[m]')
            
            df1 = df1[~df1['timestamp'].duplicated(keep='first')]

            # Drop rows where 'timestamp' could not be converted
            df1.dropna(subset=['timestamp'], inplace=True)

            # 

            # Set the timestamp as the index
            df1.set_index('timestamp', inplace=True)
            
            # Resample to minute frequency, filling any gaps
            
            df1 = df1.resample('min').interpolate(method='linear')
            df1 = df1.round(2)
            df1['devId'] = self.devId
            # Reset index to make timestamp a column again
            df1.reset_index(inplace=True)        

            columns_to_drop = [date_field_name, 'grid', 'actualCorr', 'actualProviding', 'providingAmount']
            df1.drop(columns=columns_to_drop, inplace=True, errors='ignore')     
        return df1
        
    
    def process_merge_df(self):
        weather_processed_df = self.prepare_weather()
        power_processed_df = self.prepare_power()
        merged_df = None

        if weather_processed_df is not None and not weather_processed_df.empty and power_processed_df is not None and not power_processed_df.empty:
            common_start_timestamp = max(power_processed_df['timestamp'].min(), weather_processed_df['timestamp'].min())
            common_end_timestamp = min(power_processed_df['timestamp'].max(), weather_processed_df['timestamp'].max())
            # Trim both DataFrames to start from the common start timestamp and end at the common end timestamp
            power_processed_df_trimmed = power_processed_df[(power_processed_df['timestamp'] >= common_start_timestamp) & (power_processed_df['timestamp'] <= common_end_timestamp)].reset_index(drop=True)
            weather_processed_df_trimmed = weather_processed_df[(weather_processed_df['timestamp'] >= common_start_timestamp) & (weather_processed_df['timestamp'] <= common_end_timestamp)].reset_index(drop=True)

            merged_df = pd.merge(power_processed_df_trimmed, weather_processed_df_trimmed, on='timestamp', how='inner')            
        return merged_df
        

    def corelations(self):
        data = self.process_merge_df()
        if data is not None and not data.empty:

            
            columns_to_drop = ['id', 'lat', 'long', 'devId', 'timestamp']
            corelation_data = data
            corelation_data.drop(columns=columns_to_drop, inplace=True, errors='ignore')     
            
            correlation_matrix = corelation_data.corr()
            # print("Feature correlations:")
            # print(correlation_matrix)        
            features = correlation_matrix.columns.tolist()
            # Create or get Feature objects
            feature_objs = {name: Feature.objects.get_or_create(name=name)[0] for name in features}                               
            
            # Iterate through the correlation matrix and save correlations
            for feature1 in features:
                for feature2 in features:
                    correlation_value = correlation_matrix.loc[feature1, feature2]
                    print(f"{feature1}, {feature2}, {correlation_value}")
                    exist = Correlation.objects.filter(devId=self.devId, period=self.period, feature1=feature_objs[feature1], feature2=feature_objs[feature2])
                    if not exist:
                        Correlation.objects.create(
                            feature1=feature_objs[feature1],
                            feature2=feature_objs[feature2],
                            correlation_value=round(correlation_value, 2),
                            devId = self.devId,
                            period = self.period
                        )


    def time_series_forecast(self):
        
        data = self.process_merge_df()
        
        if data is not None and not data.empty:
            train_data = TimeSeriesDataFrame.from_data_frame(
                data,
                id_column="devId",
                timestamp_column="timestamp"
            )
            predictor = TimeSeriesPredictor(
            prediction_length=1400,
            path="/autogluon",  # Adjust path as needed
            target="value",
            eval_metric="MASE",
            freq='T'  # Specify minute frequency
            )
            predictor.fit(
            train_data,
            presets="medium_quality",
            time_limit=240,
            )
            predictions = predictor.predict(train_data)

            for index, row in predictions.iterrows():            
                timestamp = index[1]                
                mean_value = round(row['mean'], 2)            
                # Create Predictions object
                
                prediction_obj = Forecast(timestamp=timestamp, power=mean_value, devId = self.devId)
                exist = Forecast.objects.filter(timestamp=timestamp, devId = self.devId)
                if exist.exists():
                    pass
                else:           
                    prediction_obj.save()
