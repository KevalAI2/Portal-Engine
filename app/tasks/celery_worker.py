from app.const.celery_config import TASK_NAME_CONSTANTS
from app.logic import schedule as logic
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name=TASK_NAME_CONSTANTS.get("tasks.celery_worker.test"),
)
@logic.with_task_logging()
def test(self, *args, **kwargs) -> str:

    return "Inserted Successfully"