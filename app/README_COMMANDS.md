source venv/bin/activate

uvicorn main:app --reload

watchmedo auto-restart -d . -p '*.py' -R -- celery -A tasks.celery_worker worker --loglevel=DEBUG

watchmedo auto-restart -d . -p '*.py' -R -- celery -A tasks.celery_worker beat -S app.scheduler.DatabaseScheduler --loglevel=INFO