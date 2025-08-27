import requests
import pandas as pd
import json
import logging

from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
from django.db import transaction
from mlapp.models import Forecast, Correlation, Feature
import seaborn as sns
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)


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
            dfWeather = dfWeather.resample('15min').interpolate(method='linear')           
            dfWeather.reset_index(inplace=True)
            dfWeather['timestamp'] = dfWeather["timestamp"].values.astype('datetime64[m]')
        return dfWeather

    def prepare_power(self):
        """
        Accepts endpoint payloads like any of:
        - { "sm-0002": [[ts, val], ...], "sm-0003": [...] }
        - { "sm-0002": { "timestamps": [...], "values": [...] } }
        - { "sm-0002": { "data": [[ts, val], ...] } }
        - [[ts, val], ...]
        - [{"timestamp": ts, "value": v}, ...]  (or ts/created/created_date, value/power/v)
        """
        try:
            response = requests.get(self.url, timeout=20)
            payload = response.json()
        except Exception as e:
            log.exception("prepare_power: failed to fetch/parse json from %s", getattr(self, "url", "?"))
            return None

        # 1) choose device series (if mapping of devId -> series)
        data = None
        if isinstance(payload, dict):
            if self.devId in payload:
                data = payload[self.devId]
            elif payload:  # fallback to first available series
                # NOTE: next(iter(...)) yields the value (the "series") for the first key
                data = next(iter(payload.values()))
        else:
            data = payload

        # 2) normalize to list[[timestamp, value], ...]
        pairs = self._normalize_pairs(data)
        if not pairs:
            log.warning("prepare_power: no usable data for devId=%s; type(data)=%s sample=%r",
                        getattr(self, "devId", None), type(data).__name__, (data[:1] if isinstance(data, list) else data))
            return None

        # 3) build dataframe
        df1 = pd.DataFrame(pairs, columns=["timestamp", "power"])

        # 4) timestamps -> datetime64[m] (tz-aware OK; coerced then cast to minute precision UTC-naive)
        df1["timestamp"] = pd.to_datetime(df1["timestamp"], errors="coerce")
        df1.dropna(subset=["timestamp"], inplace=True)
        if df1.empty:
            return None

        df1["timestamp"] = df1["timestamp"].values.astype("datetime64[m]")
        df1.sort_values("timestamp", inplace=True)
        df1 = df1[~df1["timestamp"].duplicated(keep="first")]

        # 5) resample per-minute and interpolate
        df1.set_index("timestamp", inplace=True)
        df1 = df1.resample("min").interpolate(method="linear")

        # 6) tidy
        num_cols = df1.select_dtypes(include="number").columns
        if len(num_cols):
            df1[num_cols] = df1[num_cols].round(2)
        df1["devId"] = self.devId
        df1.reset_index(inplace=True)

        return df1
    
    @staticmethod
    def _normalize_pairs(data):
        """Return [[timestamp, value], ...] or [] if not recognizable."""
        if data is None:
            return []

        # Case: mapping with embedded shapes
        if isinstance(data, dict):
            # common wrappers
            if "data" in data:
                return performML._normalize_pairs(data["data"])
            if "timestamps" in data and "values" in data:
                ts = data["timestamps"] or []
                vs = data["values"] or []
                return [[t, v] for t, v in zip(ts, vs)]
            if "ts" in data and "v" in data:
                return [[t, v] for t, v in zip(data["ts"] or [], data["v"] or [])]
            # unexpected dict — not a series
            return []

        # Case: already a list
        if isinstance(data, list):
            if not data:
                return []
            first = data[0]

            # list of [ts, val]
            if isinstance(first, (list, tuple)) and len(first) == 2:
                return data

            # list of dicts: map likely keys
            if isinstance(first, dict):
                ts_key = next((k for k in ("timestamp", "ts", "time", "created", "created_date") if k in first), None)
                v_key  = next((k for k in ("power", "value", "v", "y") if k in first), None)
                if ts_key and v_key:
                    out = []
                    for row in data:
                        try:
                            out.append([row[ts_key], row[v_key]])
                        except Exception:
                            continue
                    return out

        # Anything else: unsupported
        return []

    
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
       
        # if data is not None and not data.empty:

            
        #     columns_to_drop = ['id', 'lat', 'long', 'devId', 'timestamp']
        #     corelation_data = data
        #     corelation_data.drop(columns=columns_to_drop, inplace=True, errors='ignore')     
            
        #     correlation_matrix = corelation_data.corr()
        #     # print("Feature correlations:")
        #     # print(correlation_matrix)        
        #     features = correlation_matrix.columns.tolist()
        #     # Create or get Feature objects
        #     feature_objs = {name: Feature.objects.get_or_create(name=name)[0] for name in features}                               
            
        #     # Iterate through the correlation matrix and save correlations
        #     for feature1 in features:
        #         for feature2 in features:
        #             correlation_value = correlation_matrix.loc[feature1, feature2]
        #             print(f"{feature1}, {feature2}, {correlation_value}")
        #             exist = Correlation.objects.filter(devId=self.devId, period=self.period, feature1=feature_objs[feature1], feature2=feature_objs[feature2])
        #             if not exist:
        #                 Correlation.objects.create(
        #                     feature1=feature_objs[feature1],
        #                     feature2=feature_objs[feature2],
        #                     correlation_value=round(correlation_value, 2),
        #                     devId = self.devId,
        #                     period = self.period
        #                 )


    def time_series_forecast(self):
        
        data = self.process_merge_df()
        
        if data is not None and not data.empty:
            train_data = TimeSeriesDataFrame.from_data_frame(
                data,
                id_column="devId",
                timestamp_column="timestamp"
            )
            predictor = TimeSeriesPredictor(
            prediction_length=96,
            path="/autogluon",  # Adjust path as needed
            target="power",
            eval_metric="MASE",
            freq='15min'  # Specify minute frequency
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
                print(f"time: {timestamp} || prediction: {mean_value}")        
                #Create Predictions object
                
                prediction_obj = Forecast(timestamp=timestamp, power=mean_value, devId = self.devId)
                exist = Forecast.objects.filter(timestamp=timestamp, devId = self.devId)
                if exist.exists():
                    pass
                else:           
                    prediction_obj.save()
