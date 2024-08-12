from mlapp.models import Forecast
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import pandas as pd

response = requests.get('http://85.14.6.37:16455/api/posts/?date_range=month&not_res=true&dev=sm-0004').json()
df1 = pd.DataFrame(response)
# Convert 'created_date' column to datetime
df1['created_date'] = pd.to_datetime(df1['created_date'])

forecast_data = Forecast.objects.all().values('timestamp', 'power')
df2 = pd.DataFrame(forecast_data)

merged_df = pd.merge(df1, df2, left_on='created_date', right_on='timestamp', how='inner')

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(merged_df['created_date'], merged_df['value'], label='Value from df1')
plt.plot(merged_df['timestamp'], merged_df['power'], label='Power from Forecast')
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Values Over Time')
plt.legend()
plt.grid(True)
plt.show()
