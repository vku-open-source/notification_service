from celery import Celery
from os import environ
from dotenv import load_dotenv

load_dotenv()

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    return celery
