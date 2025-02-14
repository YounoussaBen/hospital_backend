import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')  # or prod for production

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Optional: Example periodic task registration (requires django-celery-beat)
if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    app.conf.beat_schedule = settings.CELERY_BEAT_SCHEDULE
