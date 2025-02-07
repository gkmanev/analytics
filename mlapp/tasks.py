# weather_data/tasks.py
from celery import shared_task
from mlapp.utils import today_correlation_first_five, today_correlation_five_ten, today_resample_data, pv_forecast
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging


@shared_task
def today_correlation_task():
    today_correlation_first_five()
    logger.info("ML 1-5 device")

@shared_task
def today_correlation_five_to_ten_task():
    today_correlation_five_ten()
    logger.info("ML 5-10 device")


@shared_task
def resample_forecast_task(resample):
    today_resample_data(resample)
    logger.info("Resample data")


@shared_task
def pv_forecast_task():
    pv_forecast()
    logger.info("RUN PV FORECAST")