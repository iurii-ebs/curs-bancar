from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


app.conf.timezone = settings.TIME_ZONE

app.conf.beat_schedule = {
    'daily_parsing': {
        'task': 'parse_all_beat',
        'schedule': crontab(minute=30, hour=9, day_of_week='1-5')
    },
}
