"""
Celery configuration for student knowledge base.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('student_kb')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat schedule - periodic tasks
app.conf.beat_schedule = {
    'sync-schedules-every-3-hours': {
        'task': 'schedule.sync_all_schedules',
        'schedule': crontab(minute=0, hour='*/3'),  # Every 3 hours
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    print(f'Request: {self.request!r}')

