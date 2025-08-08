from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class BackgroundTaskRequest(BaseModel):
    task_type: str
    data: Dict[str, Any]

class LongRunningTaskRequest(BaseModel):
    duration: int = 10

class NotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None

class BatchNotificationRequest(BaseModel):
    notifications: List[NotificationRequest]

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TaskProgressResponse(BaseModel):
    task_id: str
    state: str
    current: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None 