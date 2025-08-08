from datetime import datetime
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import and_, func

from croniter import croniter
from fastapi import HTTPException

from model.schedule import TaskRunRecord, TaskRunStatus, TaskSchedule
from const.celery_config import TASK_NAME_CONSTANTS


def get_all_task_schedules(db: Session, offset=0, limit=100):
    return db.query(TaskSchedule).offset(offset).limit(limit).all()


def get_all_active_task_schedules(db: Session):
    return db.query(TaskSchedule).filter(TaskSchedule.enabled.is_(True)).all()


def get_task_schedule_by_id(db: Session, id):
    return db.query(TaskSchedule).get(id)


def get_task_schedule_by_name(db: Session, name):
    return db.query(TaskSchedule).filter(TaskSchedule.name == name).first()


def create_task_schedule(
    db: Session,
    name,
    task,
    cron=None,
    start_time=None,
    args=None,
    kwargs=None,
    options=None,
    enabled=None,
    task_type=None,
):
    schedule = TaskSchedule(
        name=name,
        task=task,
        cron=cron,
        start_time=start_time,
        args=args or [],
        kwargs=kwargs or {},
        options=options or {},
        enabled=enabled,
        task_type=task_type,
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def validate_task_and_cron(task: str = None, cron: str = None):
    if task and task not in TASK_NAME_CONSTANTS.values():
        raise HTTPException(detail="Invalid task", status_code=400)
    if cron and not croniter.is_valid(cron):
        raise HTTPException(detail="Invalid cron schedule.", status_code=400)


def update_task_schedule(db: Session, id, **kwargs):
    task_schedule = get_task_schedule_by_id(db, id)

    if not task_schedule:
        raise Exception(f"unable to find any schedules for id {id}")

    for field_name, value in kwargs.items():
        if hasattr(task_schedule, field_name):
            setattr(task_schedule, field_name, value)

    db.commit()
    db.refresh(task_schedule)
    return task_schedule


def delete_task_schedule(db: Session, id):
    task_schedule = get_task_schedule_by_id(db, id)
    if task_schedule:
        db.delete(task_schedule)
        db.commit()


def get_task_run_records(
    db: Session,
    name="",
    limit=20,
    offset=0,
    hide_successful_jobs=False,
    task_type=None,
):
    query = db.query(TaskRunRecord)
    if task_type is not None:
        query = query.join(TaskSchedule).filter(TaskSchedule.task_type == task_type)
    if name:
        query = query.filter(TaskRunRecord.name.like(f"%{name}%"))
    if hide_successful_jobs:
        query = query.filter(TaskRunRecord.status != TaskRunStatus.SUCCESS)

    query = query.order_by(TaskRunRecord.id.desc())
    return query.offset(offset).limit(limit).all()


def get_task_run_record_run_by_name(
    db: Session, name, limit=20, offset=0, hide_successful_jobs=False
):
    query = db.query(TaskRunRecord).filter(TaskRunRecord.name == name)
    query = query.order_by(TaskRunRecord.created_at.desc())

    if hide_successful_jobs:
        query = query.filter(TaskRunRecord.status != TaskRunStatus.SUCCESS)

    tasks = query.offset(offset).limit(limit).all()
    count = query.count()
    return tasks, count


def get_data_doc_schedule_name(id: int):
    return f"run_data_doc_{id}"


def get_task_run_record_run_with_schedule(db: Session, docs_with_schedule):
    all_schedules_names = [
        schedule.name for _, schedule in docs_with_schedule if schedule is not None
    ]

    last_run_record_subquery = (
        db.query(
            TaskRunRecord.name, func.max(TaskRunRecord.created_at).label("max_date")
        )
        .filter(TaskRunRecord.name.in_(all_schedules_names))
        .group_by(TaskRunRecord.name)
        .subquery()
    )
    last_task_run_records = (
        db.query(TaskRunRecord)
        .join(
            last_run_record_subquery,
            and_(
                TaskRunRecord.created_at == last_run_record_subquery.c.max_date,
                last_run_record_subquery.c.name == TaskRunRecord.name,
            ),
        )
        .all()
    )

    docs_with_schedule_and_record = []
    for doc, schedule in docs_with_schedule:
        last_record = None
        if schedule:
            last_record = next(
                filter(
                    lambda record: record.name == schedule.name, last_task_run_records
                ),
                None,
            )
        docs_with_schedule_and_record.append(
            {"last_record": last_record, "schedule": schedule, "doc": doc}
        )
    return docs_with_schedule_and_record


def get_task_run_record(db: Session, id):
    return db.query(TaskRunRecord).get(id)


def create_task_run_record(db: Session, name):
    task_record = TaskRunRecord(name=name)

    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    return task_record


def update_task_run_record(db: Session, id, status=None, error_message=None):
    run = get_task_run_record(db, id)
    if run:
        if status is not None:
            run.status = status

        if error_message is not None:
            run.error_message = error_message

        run.updated_at = datetime.now()
        db.commit()
        db.refresh(run)
        return run


def create_task_run_record_for_celery_task(db: Session, task):
    job_name = task.request.get("shadow", task.name)
    return create_task_run_record(db, job_name).id


def with_task_logging():
    def base_job_decorator(job_func):
        from celery.utils.log import get_task_logger

        logger = get_task_logger(__name__)

        @wraps(job_func)
        def wrapper(self, *args, **kwargs):
            record_id = None
            try:
                # Note: This would need to be updated to pass the session
                # record_id = create_task_run_record_for_celery_task(self)
                result = job_func(self, *args, **kwargs)
                # update_task_run_record(id=record_id, status=TaskRunStatus.SUCCESS)

                return result
            except Exception as e:
                logger.info(e)
                if record_id is not None:
                    # update_task_run_record(
                    #     id=record_id, error_message=str(e), status=TaskRunStatus.FAILURE
                    # )
                    pass
                raise e

        return wrapper

    return base_job_decorator


def run_and_log_scheduled_task(db: Session, scheduled_task_id, wait_to_finish=False):
    schedule = get_task_schedule_by_id(db, scheduled_task_id)
    if schedule:
        from app.tasks.celery_app import celery_app

        result = celery_app.send_task(
            schedule.task,
            args=schedule.args,
            kwargs=schedule.kwargs,
            shadow=schedule.name,
        )
        if wait_to_finish:
            result.get(timeout=60)
        update_task_schedule(
            db,
            schedule.id,
            last_run_at=datetime.now(),
            total_run_count=(schedule.total_run_count + 1),
        )


def get_all_task_schedule(db: Session, enabled=None):
    query = db.query(TaskSchedule)

    if enabled is not None:
        query = query.filter_by(enabled=enabled)

    return query.all()
