"""
Input validation utilities for the Portal Engine application.

This module provides comprehensive validation functions and decorators
for request data, user input, and API parameters.
"""
import re
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from pydantic import BaseModel, Field, validator, ValidationError
from app.core.exceptions import ValidationError as CustomValidationError
from app.core.logging import get_logger

logger = get_logger("validators")


class BaseValidationModel(BaseModel):
    """Base model with common validation patterns."""
    
    class Config:
        extra = "forbid"  # Reject extra fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values instead of names


def validate_email(email: str) -> str:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise CustomValidationError(
            field_name="email",
            value=email,
            message="Invalid email format"
        )
    return email.lower().strip()


def validate_phone(phone: str) -> str:
    """Validate phone number format."""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise CustomValidationError(
            field_name="phone",
            value=phone,
            message="Phone number must be between 7 and 15 digits"
        )
    
    return digits_only


def validate_user_id(user_id: str) -> str:
    """Validate user ID format."""
    if not user_id or not isinstance(user_id, str):
        raise CustomValidationError(
            field_name="user_id",
            value=user_id,
            message="User ID must be a non-empty string"
        )
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise CustomValidationError(
            field_name="user_id",
            value=user_id,
            message="User ID can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Check length
    if len(user_id) < 3 or len(user_id) > 50:
        raise CustomValidationError(
            field_name="user_id",
            value=user_id,
            message="User ID must be between 3 and 50 characters"
        )
    
    return user_id.strip()


def validate_password_strength(password: str) -> str:
    """Validate password strength."""
    if len(password) < 8:
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must be at least 8 characters long"
        )
    
    if len(password) > 128:
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must be no more than 128 characters long"
        )
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must contain at least one uppercase letter"
        )
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must contain at least one lowercase letter"
        )
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must contain at least one digit"
        )
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise CustomValidationError(
            field_name="password",
            value="[REDACTED]",
            message="Password must contain at least one special character"
        )
    
    return password


def validate_url(url: str) -> str:
    """Validate URL format."""
    url_pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    if not re.match(url_pattern, url):
        raise CustomValidationError(
            field_name="url",
            value=url,
            message="Invalid URL format"
        )
    return url.strip()


def validate_json_data(data: Any, required_fields: List[str]) -> Dict[str, Any]:
    """Validate JSON data structure and required fields."""
    if not isinstance(data, dict):
        raise CustomValidationError(
            field_name="data",
            value=str(data),
            message="Data must be a JSON object"
        )
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise CustomValidationError(
            field_name="required_fields",
            value=missing_fields,
            message=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    return data


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        value = str(value)
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_pagination_params(page: int, page_size: int) -> tuple[int, int]:
    """Validate pagination parameters."""
    if page < 1:
        raise CustomValidationError(
            field_name="page",
            value=page,
            message="Page number must be at least 1"
        )
    
    if page_size < 1 or page_size > 100:
        raise CustomValidationError(
            field_name="page_size",
            value=page_size,
            message="Page size must be between 1 and 100"
        )
    
    return page, page_size


def validate_sort_params(sort_by: str, allowed_fields: List[str]) -> str:
    """Validate sort parameters."""
    if not sort_by:
        return allowed_fields[0] if allowed_fields else "id"
    
    # Remove direction indicator for validation
    field = sort_by.lstrip('-+')
    
    if field not in allowed_fields:
        raise CustomValidationError(
            field_name="sort_by",
            value=sort_by,
            message=f"Sort field must be one of: {', '.join(allowed_fields)}"
        )
    
    return sort_by


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Validate date range parameters."""
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    if start_date and not re.match(date_pattern, start_date):
        raise CustomValidationError(
            field_name="start_date",
            value=start_date,
            message="Start date must be in YYYY-MM-DD format"
        )
    
    if end_date and not re.match(date_pattern, end_date):
        raise CustomValidationError(
            field_name="end_date",
            value=end_date,
            message="End date must be in YYYY-MM-DD format"
        )
    
    if start_date and end_date and start_date > end_date:
        raise CustomValidationError(
            field_name="date_range",
            value=f"{start_date} to {end_date}",
            message="Start date must be before end date"
        )
    
    return start_date, end_date


def validate_request_data(
    data: Dict[str, Any],
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
    field_validators: Optional[Dict[str, Callable]] = None
) -> Dict[str, Any]:
    """
    Comprehensive request data validation.
    
    Args:
        data: Request data to validate
        required_fields: List of required field names
        optional_fields: List of optional field names
        field_validators: Dictionary mapping field names to validation functions
        
    Returns:
        Validated and sanitized data
        
    Raises:
        ValidationError: If validation fails
    """
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise CustomValidationError(
            field_name="required_fields",
            value=missing_fields,
            message=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate field values
    validated_data = {}
    all_fields = required_fields + (optional_fields or [])
    
    for field in all_fields:
        if field in data:
            value = data[field]
            
            # Apply field-specific validator if provided
            if field_validators and field in field_validators:
                try:
                    value = field_validators[field](value)
                except Exception as e:
                    raise CustomValidationError(
                        field_name=field,
                        value=value,
                        message=f"Validation failed for {field}: {str(e)}"
                    )
            
            # Sanitize string values
            if isinstance(value, str):
                value = sanitize_string(value)
            
            validated_data[field] = value
    
    return validated_data


def validate_api_key(api_key: str) -> str:
    """Validate API key format."""
    if not api_key or not isinstance(api_key, str):
        raise CustomValidationError(
            field_name="api_key",
            value=api_key,
            message="API key must be a non-empty string"
        )
    
    # Check for valid characters (alphanumeric and hyphens)
    if not re.match(r'^[a-zA-Z0-9-]+$', api_key):
        raise CustomValidationError(
            field_name="api_key",
            value=api_key,
            message="API key can only contain letters, numbers, and hyphens"
        )
    
    # Check length
    if len(api_key) < 16 or len(api_key) > 64:
        raise CustomValidationError(
            field_name="api_key",
            value=api_key,
            message="API key must be between 16 and 64 characters"
        )
    
    return api_key.strip()


def validate_correlation_id(correlation_id: str) -> str:
    """Validate correlation ID format."""
    if not correlation_id or not isinstance(correlation_id, str):
        raise CustomValidationError(
            field_name="correlation_id",
            value=correlation_id,
            message="Correlation ID must be a non-empty string"
        )
    
    # Check for valid UUID format or custom format
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    custom_pattern = r'^[a-zA-Z0-9_-]{8,32}$'
    
    if not (re.match(uuid_pattern, correlation_id) or re.match(custom_pattern, correlation_id)):
        raise CustomValidationError(
            field_name="correlation_id",
            value=correlation_id,
            message="Correlation ID must be a valid UUID or 8-32 character alphanumeric string"
        )
    
    return correlation_id.strip()


def validate_rate_limit_params(requests_per_minute: int, burst_size: int) -> tuple[int, int]:
    """Validate rate limiting parameters."""
    if requests_per_minute < 1 or requests_per_minute > 10000:
        raise CustomValidationError(
            field_name="requests_per_minute",
            value=requests_per_minute,
            message="Requests per minute must be between 1 and 10000"
        )
    
    if burst_size < 1 or burst_size > 1000:
        raise CustomValidationError(
            field_name="burst_size",
            value=burst_size,
            message="Burst size must be between 1 and 1000"
        )
    
    if burst_size > requests_per_minute:
        raise CustomValidationError(
            field_name="burst_size",
            value=burst_size,
            message="Burst size cannot exceed requests per minute"
        )
    
    return requests_per_minute, burst_size


def validate_file_upload(
    filename: str,
    content_type: str,
    max_size: int = 10 * 1024 * 1024,  # 10MB default
    allowed_types: Optional[List[str]] = None
) -> tuple[str, str]:
    """Validate file upload parameters."""
    if not filename or not isinstance(filename, str):
        raise CustomValidationError(
            field_name="filename",
            value=filename,
            message="Filename must be a non-empty string"
        )
    
    # Check filename length
    if len(filename) > 255:
        raise CustomValidationError(
            field_name="filename",
            value=filename,
            message="Filename must be no more than 255 characters"
        )
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in filename for char in dangerous_chars):
        raise CustomValidationError(
            field_name="filename",
            value=filename,
            message="Filename contains dangerous characters"
        )
    
    # Validate content type
    if not content_type or not isinstance(content_type, str):
        raise CustomValidationError(
            field_name="content_type",
            value=content_type,
            message="Content type must be a non-empty string"
        )
    
    if allowed_types and content_type not in allowed_types:
        raise CustomValidationError(
            field_name="content_type",
            value=content_type,
            message=f"Content type must be one of: {', '.join(allowed_types)}"
        )
    
    return filename.strip(), content_type.strip()


def validate_search_query(query: str, min_length: int = 2, max_length: int = 100) -> str:
    """Validate search query parameters."""
    if not query or not isinstance(query, str):
        raise CustomValidationError(
            field_name="query",
            value=query,
            message="Search query must be a non-empty string"
        )
    
    query = query.strip()
    
    if len(query) < min_length:
        raise CustomValidationError(
            field_name="query",
            value=query,
            message=f"Search query must be at least {min_length} characters"
        )
    
    if len(query) > max_length:
        raise CustomValidationError(
            field_name="query",
            value=query,
            message=f"Search query must be no more than {max_length} characters"
        )
    
    # Check for SQL injection patterns
    sql_patterns = ['union', 'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter']
    if any(pattern in query.lower() for pattern in sql_patterns):
        logger.warning("Potential SQL injection attempt detected", query=query)
    
    return query


def validate_recommendation_params(
    user_id: str,
    limit: int,
    filters: Optional[Dict[str, Any]] = None
) -> tuple[str, int, Optional[Dict[str, Any]]]:
    """Validate recommendation request parameters."""
    user_id = validate_user_id(user_id)
    
    if limit < 1 or limit > 100:
        raise CustomValidationError(
            field_name="limit",
            value=limit,
            message="Limit must be between 1 and 100"
        )
    
    if filters and not isinstance(filters, dict):
        raise CustomValidationError(
            field_name="filters",
            value=filters,
            message="Filters must be a dictionary"
        )
    
    return user_id, limit, filters


def validate_health_check_params(
    service_name: str,
    timeout: int = 30
) -> tuple[str, int]:
    """Validate health check parameters."""
    if not service_name or not isinstance(service_name, str):
        raise CustomValidationError(
            field_name="service_name",
            value=service_name,
            message="Service name must be a non-empty string"
        )
    
    if timeout < 1 or timeout > 300:
        raise CustomValidationError(
            field_name="timeout",
            value=timeout,
            message="Timeout must be between 1 and 300 seconds"
        )
    
    return service_name.strip(), timeout
