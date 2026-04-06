import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cv_screening.settings")

app = Celery("cv_screening")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
