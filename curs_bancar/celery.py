import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'curs_bancar.settings')

app = Celery('curs_bancar')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.timezone = 'Europe/Chisinau'

# Schedule settings: start task every day at 9:30 AM
app.conf.beat_schedule = {
    'daily_parsing': {
        'task': 'bank_parser.tasks.parse_all_beat',
        'schedule': crontab(minute=30, hour=8),
        # 'schedule': 120,
        'args': []
    },
}

