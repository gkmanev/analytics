from django.core.management.base import BaseCommand
from mlapp.utils import today_correlation_first_five

class Command(BaseCommand):
    def handle(self, *args, **options):
        today_correlation_first_five()  # Call directly
        self.stdout.write(self.style.SUCCESS("Completed without Celery!"))
