"""
Advanced Serialization Utilities

This module provides robust serialization utilities that handle complex data types,
prevent recursion issues, and ensure safe JSON serialization.
"""
import json
import uuid
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, is_dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from pydantic import BaseModel
from app.core.logging import get_logger

logger = get_logger("serialization")


class SafeJSONEncoder(json.JSONEncoder):
    """
    Safe JSON encoder that handles complex data types and prevents recursion.
    """
    
    def __init__(self, *args, **kwargs):
        # Extract max_depth before passing to parent
        self._max_depth = kwargs.pop('max_depth', 10)
        super().__init__(*args, **kwargs)
        self._serialized_objects: Set[int] = set()
        self._current_depth = 0
    
    def encode(self, obj: Any) -> str:
        """Encode object with depth tracking"""
        self._serialized_objects.clear()
        self._current_depth = 0
        return super().encode(obj)
    
    def default(self, obj: Any) -> Any:
        """Handle various data types safely"""
        # Prevent infinite recursion
        if self._current_depth >= self._max_depth:
            return f"<Max depth {self._max_depth} reached>"
        
        # Check for circular references
        obj_id = id(obj)
        if obj_id in self._serialized_objects:
            return f"<Circular reference to {type(obj).__name__}>"
        
        self._serialized_objects.add(obj_id)
        self._current_depth += 1
        
        try:
            return self._serialize_object(obj)
        finally:
            self._current_depth -= 1
            self._serialized_objects.discard(obj_id)
    
    
    def _serialize_object(self, obj: Any) -> Any:
        """Serialize specific object types"""
        # Handle None
        if obj is None:
            return None
        
        # Handle Pydantic models directly to avoid circular reference issues
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        
        # Handle datetime objects before circular reference check
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle basic types
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        if isinstance(obj, date):
            return {
                "_type": "date",
                "value": obj.isoformat()
            }
        
        if isinstance(obj, time):
            return {
                "_type": "time",
                "value": obj.isoformat()
            }
        
        if isinstance(obj, timedelta):
            return {
                "_type": "timedelta",
                "value": obj.total_seconds()
            }
        
        # Handle Decimal
        if isinstance(obj, Decimal):
            return {
                "_type": "decimal",
                "value": str(obj)
            }
        
        # Handle UUID
        if isinstance(obj, uuid.UUID):
            return {
                "_type": "uuid",
                "value": str(obj)
            }
        
        # Handle Enum
        if isinstance(obj, Enum):
            return {
                "_type": "enum",
                "class": obj.__class__.__name__,
                "value": obj.value
            }
        
        # Handle Path
        if isinstance(obj, Path):
            return {
                "_type": "path",
                "value": str(obj)
            }
        
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            return {
                "_type": "pydantic_model",
                "class": obj.__class__.__name__,
                "data": self._serialize_dict(obj.model_dump())
            }
        
        # Handle dataclasses
        if is_dataclass(obj):
            return {
                "_type": "dataclass",
                "class": obj.__class__.__name__,
                "data": self._serialize_dict(obj.__dict__)
            }
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return {
                "_type": "numpy_array",
                "shape": obj.shape,
                "dtype": str(obj.dtype),
                "data": obj.tolist()
            }
        
        # Handle pandas objects
        if isinstance(obj, pd.DataFrame):
            return {
                "_type": "dataframe",
                "columns": obj.columns.tolist(),
                "index": obj.index.tolist(),
                "data": obj.values.tolist()
            }
        
        if isinstance(obj, pd.Series):
            return {
                "_type": "series",
                "name": obj.name,
                "index": obj.index.tolist(),
                "data": obj.values.tolist()
            }
        
        # Handle dictionaries
        if isinstance(obj, dict):
            return self._serialize_dict(obj)
        
        # Handle lists and tuples
        if isinstance(obj, (list, tuple)):
            return self._serialize_sequence(obj)
        
        # Handle sets
        if isinstance(obj, set):
            return {
                "_type": "set",
                "data": self._serialize_sequence(list(obj))
            }
        
        # Handle custom objects with __dict__
        if hasattr(obj, '__dict__'):
            return {
                "_type": "object",
                "class": obj.__class__.__name__,
                "data": self._serialize_dict(obj.__dict__)
            }
        
        # Handle objects with __slots__
        if hasattr(obj, '__slots__'):
            return {
                "_type": "slots_object",
                "class": obj.__class__.__name__,
                "data": self._serialize_dict({
                    slot: getattr(obj, slot, None)
                    for slot in obj.__slots__
                })
            }
        
        # Fallback for unknown types
        try:
            return str(obj)
        except Exception:
            return f"<Unserializable {type(obj).__name__}>"
    
    def _serialize_dict(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Safely serialize dictionary"""
        result = {}
        for key, value in obj.items():
            try:
                # Convert key to string if needed
                str_key = str(key) if not isinstance(key, str) else key
                result[str_key] = self.default(value)
            except Exception as e:
                logger.warning("Failed to serialize dict key", key=str(key), error=str(e))
                result[str_key] = f"<Serialization error: {str(e)}>"
        return result
    
    def _serialize_sequence(self, obj: Union[List[Any], Tuple[Any]]) -> List[Any]:
        """Safely serialize sequence"""
        result = []
        for item in obj:
            try:
                result.append(self.default(item))
            except Exception as e:
                logger.warning("Failed to serialize sequence item", error=str(e))
                result.append(f"<Serialization error: {str(e)}>")
        return result


class SafeJSONDecoder(json.JSONDecoder):
    """
    Safe JSON decoder that can deserialize complex data types.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deserializers = {
            "datetime": self._deserialize_datetime,
            "date": self._deserialize_date,
            "time": self._deserialize_time,
            "timedelta": self._deserialize_timedelta,
            "decimal": self._deserialize_decimal,
            "uuid": self._deserialize_uuid,
            "enum": self._deserialize_enum,
            "path": self._deserialize_path,
            "pydantic_model": self._deserialize_pydantic_model,
            "dataclass": self._deserialize_dataclass,
            "numpy_array": self._deserialize_numpy_array,
            "dataframe": self._deserialize_dataframe,
            "series": self._deserialize_series,
            "set": self._deserialize_set,
            "object": self._deserialize_object,
            "slots_object": self._deserialize_slots_object
        }
    
    def decode(self, s: str) -> Any:
        """Decode JSON string with type restoration"""
        obj = super().decode(s)
        return self._restore_types(obj)
    
    def _restore_types(self, obj: Any) -> Any:
        """Restore complex types from serialized data"""
        if isinstance(obj, dict) and "_type" in obj:
            type_name = obj["_type"]
            if type_name in self._deserializers:
                try:
                    return self._deserializers[type_name](obj)
                except Exception as e:
                    logger.warning("Failed to deserialize type", type=type_name, error=str(e))
                    return obj
        elif isinstance(obj, dict):
            return {key: self._restore_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._restore_types(item) for item in obj]
        
        return obj
    
    def _deserialize_datetime(self, obj: Dict[str, Any]) -> datetime:
        """Deserialize datetime"""
        dt = datetime.fromisoformat(obj["value"])
        if obj.get("timezone"):
            import pytz
            dt = dt.replace(tzinfo=pytz.timezone(obj["timezone"]))
        return dt
    
    def _deserialize_date(self, obj: Dict[str, Any]) -> date:
        """Deserialize date"""
        return date.fromisoformat(obj["value"])
    
    def _deserialize_time(self, obj: Dict[str, Any]) -> time:
        """Deserialize time"""
        return time.fromisoformat(obj["value"])
    
    def _deserialize_timedelta(self, obj: Dict[str, Any]) -> timedelta:
        """Deserialize timedelta"""
        return timedelta(seconds=obj["value"])
    
    def _deserialize_decimal(self, obj: Dict[str, Any]) -> Decimal:
        """Deserialize decimal"""
        return Decimal(obj["value"])
    
    def _deserialize_uuid(self, obj: Dict[str, Any]) -> uuid.UUID:
        """Deserialize UUID"""
        return uuid.UUID(obj["value"])
    
    def _deserialize_enum(self, obj: Dict[str, Any]) -> Any:
        """Deserialize enum (returns value as fallback)"""
        return obj["value"]
    
    def _deserialize_path(self, obj: Dict[str, Any]) -> Path:
        """Deserialize path"""
        return Path(obj["value"])
    
    def _deserialize_pydantic_model(self, obj: Dict[str, Any]) -> Any:
        """Deserialize Pydantic model (returns dict as fallback)"""
        return obj["data"]
    
    def _deserialize_dataclass(self, obj: Dict[str, Any]) -> Any:
        """Deserialize dataclass (returns dict as fallback)"""
        return obj["data"]
    
    def _deserialize_numpy_array(self, obj: Dict[str, Any]) -> np.ndarray:
        """Deserialize numpy array"""
        return np.array(obj["data"]).reshape(obj["shape"]).astype(obj["dtype"])
    
    def _deserialize_dataframe(self, obj: Dict[str, Any]) -> pd.DataFrame:
        """Deserialize pandas DataFrame"""
        return pd.DataFrame(obj["data"], columns=obj["columns"], index=obj["index"])
    
    def _deserialize_series(self, obj: Dict[str, Any]) -> pd.Series:
        """Deserialize pandas Series"""
        return pd.Series(obj["data"], index=obj["index"], name=obj["name"])
    
    def _deserialize_set(self, obj: Dict[str, Any]) -> set:
        """Deserialize set"""
        return set(obj["data"])
    
    def _deserialize_object(self, obj: Dict[str, Any]) -> Any:
        """Deserialize object (returns dict as fallback)"""
        return obj["data"]
    
    def _deserialize_slots_object(self, obj: Dict[str, Any]) -> Any:
        """Deserialize slots object (returns dict as fallback)"""
        return obj["data"]


def safe_json_dumps(
    obj: Any,
    ensure_ascii: bool = False,
    indent: Optional[int] = None,
    max_depth: int = 10,
    **kwargs
) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        ensure_ascii: Whether to escape non-ASCII characters
        indent: JSON indentation
        max_depth: Maximum serialization depth
        **kwargs: Additional JSON encoder arguments
        
    Returns:
        JSON string
    """
    try:
        # Create encoder class with max_depth
        class EncoderWithMaxDepth(SafeJSONEncoder):
            def __init__(self, **kwargs):
                super().__init__(max_depth=max_depth, **kwargs)
        
        return json.dumps(
            obj,
            cls=EncoderWithMaxDepth,
            ensure_ascii=ensure_ascii,
            indent=indent,
            **kwargs
        )
    except Exception as e:
        logger.error("JSON serialization failed", error=str(e))
        return json.dumps({"error": "Serialization failed", "message": str(e)})


def safe_json_loads(
    s: str,
    **kwargs
) -> Any:
    """
    Safely deserialize JSON string to object.
    
    Args:
        s: JSON string
        **kwargs: Additional JSON decoder arguments
        
    Returns:
        Deserialized object
    """
    try:
        return json.loads(s, cls=SafeJSONDecoder, **kwargs)
    except Exception as e:
        logger.error("JSON deserialization failed", error=str(e))
        return {"error": "Deserialization failed", "message": str(e)}


def safe_serialize(obj: Any) -> Any:
    """
    Safely serialize object for storage or transmission.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serializable representation
    """
    try:
        # Handle datetime objects directly
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle Pydantic models directly
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        
        # Try JSON serialization first
        json_str = safe_json_dumps(obj)
        return safe_json_loads(json_str)
    except Exception as e:
        logger.warning("Safe serialization failed, using fallback", error=str(e))
        return str(obj)


def is_serializable(obj: Any) -> bool:
    """
    Check if object is JSON serializable.
    
    Args:
        obj: Object to check
        
    Returns:
        True if serializable, False otherwise
    """
    try:
        json.dumps(obj, cls=SafeJSONEncoder)
        return True
    except Exception:
        return False


def get_serialization_info(obj: Any) -> Dict[str, Any]:
    """
    Get information about object serialization.
    
    Args:
        obj: Object to analyze
        
    Returns:
        Serialization information dictionary
    """
    info = {
        "type": type(obj).__name__,
        "serializable": is_serializable(obj),
        "size_bytes": 0,
        "complexity": "simple"
    }
    
    try:
        # Calculate size
        json_str = safe_json_dumps(obj)
        info["size_bytes"] = len(json_str.encode('utf-8'))
        
        # Determine complexity
        if isinstance(obj, (dict, list, tuple)):
            info["complexity"] = "complex"
            if isinstance(obj, dict):
                info["key_count"] = len(obj)
            else:
                info["item_count"] = len(obj)
        elif hasattr(obj, '__dict__'):
            info["complexity"] = "object"
            info["attribute_count"] = len(obj.__dict__)
        
    except Exception as e:
        info["error"] = str(e)
    
    return info


def safe_model_dump(
    obj: Any,
    *,
    exclude_none: bool = False,
    by_alias: bool = False,
    exclude: Optional[Union[Set[str], Dict[str, Any]]] = None,
    include: Optional[Union[Set[str], Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Backward-compatible helper to safely dump Pydantic models or mappings to plain dicts.

    - Prefers Pydantic's model_dump when available (v2)
    - Falls back to dict(obj) when obj is a mapping-like
    - As a last resort, uses safe_serialize to avoid recursion issues
    """
    try:
        if isinstance(obj, BaseModel):
            # Build kwargs for model_dump
            dump_kwargs = {
                "exclude_none": exclude_none,
                "by_alias": by_alias
            }
            if exclude is not None:
                dump_kwargs["exclude"] = exclude
            if include is not None:
                dump_kwargs["include"] = include
            return obj.model_dump(**dump_kwargs)  # Pydantic v2
        
        if isinstance(obj, dict):
            # If no filtering is needed, return the same object
            if exclude is None and include is None and not exclude_none:
                return obj
            
            # For dicts, apply exclude/include filters manually
            result = dict(obj)
            if exclude is not None:
                if isinstance(exclude, set):
                    result = {k: v for k, v in result.items() if k not in exclude}
                elif isinstance(exclude, dict):
                    # Handle nested exclusions (simplified)
                    for key in exclude:
                        if key in result:
                            del result[key]
            if include is not None:
                if isinstance(include, set):
                    result = {k: v for k, v in result.items() if k in include}
                elif isinstance(include, dict):
                    # Handle nested inclusions (simplified)
                    result = {k: v for k, v in result.items() if k in include}
            # Optionally filter None values
            if exclude_none:
                result = {k: v for k, v in result.items() if v is not None}
            return result

        # Handle objects with dict() method (legacy Pydantic v1 style)
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
            try:
                result = obj.dict(exclude_none=exclude_none, by_alias=by_alias)
                if exclude is not None:
                    if isinstance(exclude, set):
                        result = {k: v for k, v in result.items() if k not in exclude}
                if include is not None:
                    if isinstance(include, set):
                        result = {k: v for k, v in result.items() if k in include}
                return result
            except Exception:
                # If dict() method fails, fall through to other methods
                pass
        
        # Handle dataclasses
        if is_dataclass(obj):
            raw = {k: getattr(obj, k) for k in obj.__dataclass_fields__.keys()}  # type: ignore[attr-defined]
            result = raw
            if exclude is not None:
                if isinstance(exclude, set):
                    result = {k: v for k, v in result.items() if k not in exclude}
            if include is not None:
                if isinstance(include, set):
                    result = {k: v for k, v in result.items() if k in include}
            if exclude_none:
                result = {k: v for k, v in result.items() if v is not None}
            return result

        # Fallback: serialize and deserialize to ensure safety
        serialized = safe_json_dumps(obj)
        restored = safe_json_loads(serialized)
        if isinstance(restored, dict):
            return restored
        return {"value": restored}
    except Exception as e:
        logger.error("safe_model_dump failed", error=str(e))
        try:
            return dict(obj)  # last-chance attempt for mapping-like objects
        except Exception:
            return {"error": f"unable_to_dump:{type(obj).__name__}", "message": str(e)}