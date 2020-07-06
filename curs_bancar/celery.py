import os
from celery import Celery
from celery.schedules import crontab
from celery.schedules import crontab
from kombu import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'curs_bancar.settings')

app = Celery('curs_bancar')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.timezone = 'Europe/Chisinau'

app.conf.beat_schedule = {
    'daily_parsing': {
        'task': 'tasks.parse_beat_banks',
        # 'schedule': crontab(minute=30, hour=9),
        'schedule': crontab(),
        'args': ()
    },
}
