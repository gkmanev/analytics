# weather_data/tasks.py
from celery import shared_task
from mlapp.utils import today_correlation_first_five, today_correlation_five_ten, today_resample_data, pv_forecast_first_five, pv_forecast_five_ten
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging


@shared_task
def today_correlation_task():
    today_correlation_first_five()
    logger.info("ML 1-5 device")

@shared_task(bind=True, max_retries=3, default_retry_delay=120)  # 2 minutes
def today_correlation_task(self):
    try:
        today_correlation_first_five()
    except ValueError as exc:
        raise self.retry(exc=exc)


@shared_task
def resample_forecast_task(resample):
    today_resample_data(resample)
    logger.info("Resample data")


@shared_task
def pv_forecast_first_five_task():
    pv_forecast_first_five()
    logger.info("RUN PV FORECAST_1-5")

@shared_task
def pv_forecast_five_ten_task():
    pv_forecast_five_ten()
    logger.info("RUN PV FORECAST_5-10")
    