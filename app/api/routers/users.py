from fastapi import APIRouter
from app.workers.tasks import get_users

router = APIRouter()

@router.post("/generate-users/")
def generate_users(count: int = 5, delay: int = 2):
    """Trigger dummy user generation"""
    task = get_users.delay(count, delay)
    return {"task_id": task.id, "status": "User generation started"}
