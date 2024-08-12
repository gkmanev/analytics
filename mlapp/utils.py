from mlapp.helper import performML
import os
import json


def today_correlation():
    file_path = os.path.join('mlapp', 'coords.json')
    with open(file_path, 'r') as file:
        coords = json.load(file)
    
    for dev in coords:
        for k,v in dev.items():
            devId = k 
            lat = v["lat"]
            long = v["long"]
            period = "month"
            url_dev = f"http://85.14.6.37:16455/api/posts/?date_range=month&not_res=true&dev={devId}"
            url_weather = f"http://85.14.6.37:16456/api/weather/?date_range=month&lat={lat}&long={long}"
            # calc_correlations = performML(url_dev, url_weather, period, devId)
            # calc_correlations.corelations()
            make_forecast = performML(url_dev, url_weather, period, devId)
            make_forecast.time_series_forecast()


    













