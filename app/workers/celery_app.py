"""
Celery application configuration
"""
from celery import Celery
from app.core.config import settings
from app.core.logging import get_logger

# Configure Celery
celery_app = Celery(
    "portal_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_always_eager=False,  # Set to True for testing
)

# Configure logging
logger = get_logger("celery")

from app.workers.tasks import get_users

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    interval = settings.task_interval_seconds
    sender.add_periodic_task(
        interval,  # seconds
        get_users.s(3, 1),  # pass args here (count=3, delay=1)
        name=f"generate-users-every-{interval}-seconds"
    )
    pass
