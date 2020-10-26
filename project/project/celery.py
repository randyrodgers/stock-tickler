import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault( 'DJANGO_SETTINGS_MODULE', 'project.settings' )

app = Celery( 'project' )

app.config_from_object( 'django.conf:settings', namespace = 'CELERY' )

app.conf.beat_schedule = {
    'every-15-minutes' : {
        'task' : 'app.tasks.poll_yahoo_and_alert_if_watch_price_met',
        'schedule' : crontab( minute = '*/15' ),
    }
}

app.autodiscover_tasks()
