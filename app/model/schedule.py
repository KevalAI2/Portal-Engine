import sqlalchemy as sql
from celery import schedules
from sqlalchemy.event import listen
from sqlalchemy.orm import backref, relationship, sessionmaker
from datetime import datetime
from enum import Enum

from app.core.database import Base


# Define missing constants
class TaskRunStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


# Constants
description_length = 1000
name_length = 255


def now():
    return datetime.utcnow()


class TaskSchedules(Base):
    __tablename__ = "task_schedules"

    id = sql.Column(sql.SmallInteger, primary_key=True, default=1, unique=True)
    last_update = sql.Column(sql.DateTime, default=now)

    @classmethod
    def update_changed(cls, session, **kwargs):
        # this is only called by event listener after sql updates. So always open new session and commit
        obj = session.query(cls).filter_by(id=1).first()
        if not obj:
            obj = TaskSchedules(id=1)
        obj.last_update = now()
        session.add(obj)
        session.commit()

    @classmethod
    def last_change(cls, session):
        if obj := session.query(cls).filter_by(id=1).first():
            return obj.last_update


class TaskSchedule(Base):
    __tablename__ = "task_schedule"

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)

    name = sql.Column(sql.String(length=name_length), unique=True, nullable=False)
    # for the name of the task, ex: celery.backend_cleanup
    task = sql.Column(sql.String(length=name_length), nullable=False)

    # schedule time setting
    cron = sql.Column(sql.String(length=name_length), default="* * * * *")
    start_time = sql.Column(sql.DateTime, nullable=True)

    args = sql.Column(sql.JSON, default=[])
    kwargs = sql.Column(sql.JSON, default={})
    options = sql.Column(sql.JSON, default={})

    # Run records
    last_run_at = sql.Column(sql.DateTime, default=now)
    total_run_count = sql.Column(sql.Integer, default=0)

    enabled = sql.Column(sql.Boolean, default=True)
    no_changes = sql.Column(sql.Boolean, default=False)

    task_type = sql.Column(
        sql.String(length=name_length), nullable=False, default="prod"
    )

    def get_cron(self):
        return self.cron.split(" ")

    @property
    def schedule(self):
        minute, hour, day_of_month, month_of_year, day_of_week = self.get_cron()
        return schedules.crontab(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
        )


def task_schedules_updated(mapper, connection, target):
    if not hasattr(target, "no_changes") or not target.no_changes:
        Session = sessionmaker(bind=connection)
        TaskSchedules.update_changed(session=Session())


listen(TaskSchedule, "after_insert", task_schedules_updated)
listen(TaskSchedule, "after_update", task_schedules_updated)
listen(TaskSchedule, "after_delete", task_schedules_updated)


class TaskRunRecord(Base):
    __tablename__ = "task_run_record"

    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(
        sql.String(length=name_length),
        sql.ForeignKey(
            "task_schedule.name",
            ondelete="CASCADE",
            name="task_run_record_task_schedule_fk",
        ),
    )
    results = sql.Column(sql.JSON, default={})
    status = sql.Column(
        sql.Enum(TaskRunStatus), default=TaskRunStatus.RUNNING, nullable=False
    )
    created_at = sql.Column(sql.DateTime, default=now)
    updated_at = sql.Column(sql.DateTime, default=now)
    error_message = sql.Column(sql.String(length=description_length))

    task = relationship(
        "TaskSchedule",
        backref=backref("task_run_record", cascade="all, delete", passive_deletes=True),
        foreign_keys=[name],
    )
