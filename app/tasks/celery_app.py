import os

from celery import Celery

from app.const.celery_config import CELERY_BROKER_URL, CELERY_BACKEND_URL
celery_app = None

if not bool(os.getenv("DOCKER")):  # if running example without docker
    celery_app = Celery(
        "worker", backend=CELERY_BACKEND_URL, broker=CELERY_BROKER_URL
    )
    # celery_app.conf.task_routes = {
    #     "app.worker.celery_worker.test_celery": "test-queue"}
else:  # running example with docker
    celery_app = Celery(
        "worker", backend=CELERY_BACKEND_URL, broker=CELERY_BROKER_URL
    )
    # celery_app.conf.task_routes = {
    #     "app.tasks.celery_worker.test_celery": "test-queue"}

celery_app.conf.update(task_track_started=True)

# Import tasks to register them
from app.tasks import recommendation_tasks
