from enum import Enum

TASK_NAME_CONSTANTS = {
    "tasks.celery_worker.test": "test",
}

class PipelineStatus(Enum):
    QUEUED = "Queued"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILURE = "Failure"


CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_BACKEND_URL = "redis://localhost:6379/0"