import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drought_warning_system.settings')

app = Celery('drought_warning_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Load beat schedule
from .celery_schedules import CELERY_BEAT_SCHEDULE
app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
app.conf.timezone = 'Africa/Nairobi'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')