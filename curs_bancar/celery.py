from __future__ import absolute_import, unicode_literals
import os
from django.conf import settings
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'curs_bancar.settings')

app = Celery('curs_bancar')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


app.conf.timezone = settings.TIME_ZONE

# Schedule settings: start task every day at 9:30 AM
app.conf.beat_schedule = {
    'daily_parsing': {
        'task': 'parse_all_beat',
        'schedule': crontab(minute=30, hour=8)
    },
}

