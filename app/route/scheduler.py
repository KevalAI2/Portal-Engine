from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.logic import schedule as logic

router = APIRouter()


@router.get("/")
def get_event_logs():
    """Returns all the event logs from the db"""
    return {"message": "Hello World1"}


@router.get("/task")
def get_all_tasks(db: Session = Depends(get_db)):
    """Returns all active scheduled tasks"""
    return logic.get_all_active_task_schedules(db)


@router.post("/task")
def create_task(name: str, task: str, cron: str, args: dict, db: Session = Depends(get_db)):
    """Schedule a report generation task"""
    logic.validate_task_and_cron(task=task, cron=cron)
    return logic.create_task_schedule(db=db, name=name, cron=cron, task=task, args=args)


@router.put("/task/{id}")
def update_task(id: str, task: str, name: str, cron: str, db: Session = Depends(get_db)):
    """Update a scheduled task"""
    logic.validate_task_and_cron(task=task, cron=cron)
    return logic.update_task_schedule(db=db, id=id, cron=cron, name=name, task=task)


@router.delete("/task/{id}")
def delete_task(id: str, db: Session = Depends(get_db)):
    """Delete a scheduled task"""
    return logic.delete_task_schedule(db=db, id=id)


@router.get("/task/{task_id}/history")
def get_task_history(task_id: int, db: Session = Depends(get_db)):
    """Return run history for a scheduled task (by schedule id)"""
    return logic.get_task_run_records_by_schedule_id(db=db, schedule_id=task_id)


@router.get("/celery-task")
def fetch_all_celery_tasks():
    from app.tasks.celery_app import celery_app

    tasks = list(sorted(iter(celery_app.tasks)))
    return [task for task in tasks if not task.startswith("celery")]
