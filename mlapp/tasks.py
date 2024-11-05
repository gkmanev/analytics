# weather_data/tasks.py
from celery import shared_task
from mlapp.utils import today_correlation_first_five
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logging


@shared_task
def today_correlation_task():
    today_correlation_first_five()
    logger.info("Update history data")