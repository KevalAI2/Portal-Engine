"""Safe serialization utilities to prevent recursion errors."""
import json
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel

def safe_serialize(obj: Any) -> Any:
    """Safely serialize objects to prevent recursion."""
    if isinstance(obj, BaseModel):
        return safe_model_dump(obj)
    elif isinstance(obj, (datetime,)):
        return obj.isoformat()
    elif isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: safe_serialize(value) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):
        return safe_serialize(obj.__dict__)
    else:
        return obj

def safe_model_dump(obj: Any, **kwargs) -> Dict[str, Any]:
    """Safely convert object to dict."""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(**kwargs)
    elif hasattr(obj, 'dict'):
        return obj.dict(**kwargs)
    elif isinstance(obj, dict):
        return obj
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        # For non-iterable objects, return as-is wrapped in a dict
        return {"value": obj}