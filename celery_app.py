"""
Copyright (c) VKU.OneLove.
This source code is licensed under the Apache-2.0 license found in the
LICENSE file in the root directory of this source tree.
"""

from os import environ

from celery import Celery
from dotenv import load_dotenv

load_dotenv()


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"),
        broker=environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    )
    celery.conf.update(app.config)
    return celery
