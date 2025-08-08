from const.celery_config import TASK_NAME_CONSTANTS
from logic import schedule as logic
from tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name=TASK_NAME_CONSTANTS.get("tasks.celery_worker.insert_ohlcv"),
)
@logic.with_task_logging()
def test(self, *args, **kwargs) -> str:
    from logic import send_notification as logic

    return "Inserted Successfully"