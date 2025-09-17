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
    include=["workers.tasks"]
)

# Celery configuration for maximum parallel processing
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,  # Process one task at a time per worker for independence
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_always_eager=False,  # Set to True for testing
    # Maximum parallel processing settings
    worker_concurrency=settings.celery_worker_concurrency,  # Number of worker processes from env
    worker_disable_rate_limits=True,  # Disable rate limiting for immediate processing
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    # Queue settings for independent processing
    task_default_queue="user_processing",
    task_default_exchange="user_processing",
    task_default_routing_key="user_processing",
    # Advanced settings for maximum throughput
    worker_direct=True,  # Direct routing for faster task distribution
    task_ignore_result=False,  # Store results for status checking
    task_store_errors_even_if_ignored=True,  # Store errors even if results ignored
    worker_send_task_events=True,  # Send task events for monitoring
    task_send_sent_event=True,  # Send sent events for tracking
    # Performance optimizations
    worker_pool_restarts=True,  # Restart worker pool on failures
    worker_cancel_long_running_tasks_on_connection_loss=True,  # Cancel long tasks on connection loss
)

# Configure logging
logger = get_logger("celery")

# @celery_app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     """Setup periodic tasks"""
#     # Import here to avoid circular import
#     from workers.tasks import get_users
#     
#     interval = settings.task_interval_seconds
#     sender.add_periodic_task(
#         interval,  # seconds
#         get_users.s(3, 1),  # pass args here (count=3, delay=1)
#         name=f"generate-users-every-{interval}-seconds"
#     )
