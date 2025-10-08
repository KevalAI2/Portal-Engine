"""
Error handling utilities for the Portal Engine application.

This module provides utilities for consistent error handling,
logging, and error response formatting across the application.
"""
import traceback
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import PortalEngineException
from app.core.logging import get_logger
from app.models.responses import APIResponse


logger = get_logger("error_handler")


def handle_exception(
    request: Request,
    exc: Exception,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Handle exceptions and return appropriate JSON responses.
    
    Args:
        request: The FastAPI request object
        exc: The exception that occurred
        include_traceback: Whether to include traceback in response
        
    Returns:
        JSONResponse: Formatted error response
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    # Log the exception
    logger.error(
        "Exception occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    # Handle custom Portal Engine exceptions
    if isinstance(exc, PortalEngineException):
        return _handle_portal_engine_exception(exc, correlation_id, include_traceback)
    
    # Handle FastAPI HTTP exceptions
    if isinstance(exc, HTTPException):
        return _handle_http_exception(exc, correlation_id)
    
    # Handle generic exceptions
    return _handle_generic_exception(exc, correlation_id, include_traceback)


def _handle_portal_engine_exception(
    exc: PortalEngineException,
    correlation_id: Optional[str],
    include_traceback: bool
) -> JSONResponse:
    """Handle Portal Engine custom exceptions."""
    error_details = {
        "error_code": exc.error_code,
        "details": exc.details,
        "correlation_id": correlation_id
    }
    
    if include_traceback:
        error_details["traceback"] = traceback.format_exc()
    
    # Map error codes to HTTP status codes
    status_code = _get_status_code_for_error_code(exc.error_code)
    
    response = APIResponse.error_response(
        message=exc.message,
        status_code=status_code,
        error=error_details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )


def _handle_http_exception(
    exc: HTTPException,
    correlation_id: Optional[str]
) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    error_details = {
        "correlation_id": correlation_id
    }
    
    response = APIResponse.error_response(
        message=exc.detail,
        status_code=exc.status_code,
        error=error_details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


def _handle_generic_exception(
    exc: Exception,
    correlation_id: Optional[str],
    include_traceback: bool
) -> JSONResponse:
    """Handle generic exceptions."""
    error_details = {
        "exception_type": type(exc).__name__,
        "correlation_id": correlation_id
    }
    
    if include_traceback:
        error_details["traceback"] = traceback.format_exc()
    
    response = APIResponse.error_response(
        message="An unexpected error occurred",
        status_code=500,
        error=error_details
    )
    
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )


def _get_status_code_for_error_code(error_code: str) -> int:
    """Map error codes to HTTP status codes."""
    error_code_mapping = {
        "SERVICE_UNAVAILABLE": 503,
        "SERVICE_TIMEOUT": 504,
        "VALIDATION_ERROR": 400,
        "CONFIGURATION_ERROR": 500,
        "DATA_PROCESSING_ERROR": 422,
        "CACHE_ERROR": 500,
        "RECOMMENDATION_ERROR": 422,
        "AUTHENTICATION_ERROR": 401,
        "AUTHORIZATION_ERROR": 403,
    }
    
    return error_code_mapping.get(error_code, 500)


def log_service_error(
    service_name: str,
    operation: str,
    error: Exception,
    correlation_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log service errors with consistent formatting.
    
    Args:
        service_name: Name of the service that failed
        operation: Operation that was being performed
        error: The exception that occurred
        correlation_id: Request correlation ID
        additional_context: Additional context to include in logs
    """
    context = {
        "service_name": service_name,
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "correlation_id": correlation_id
    }
    
    if additional_context:
        context.update(additional_context)
    
    logger.error(
        f"Service error in {service_name} during {operation}",
        **context,
        exc_info=True
    )


def create_error_response(
    message: str,
    error_code: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Error code
        status_code: HTTP status code
        details: Additional error details
        correlation_id: Request correlation ID
        
    Returns:
        JSONResponse: Formatted error response
    """
    error_details = {
        "error_code": error_code,
        "correlation_id": correlation_id
    }
    
    if details:
        error_details["details"] = details
    
    response = APIResponse.error_response(
        message=message,
        status_code=status_code,
        error=error_details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: list[str],
    field_type: str = "request"
) -> None:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        field_type: Type of data being validated (for error messages)
        
    Raises:
        ValidationError: If any required fields are missing
    """
    from app.core.exceptions import ValidationError
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            field_name="required_fields",
            value=missing_fields,
            message=f"Missing required fields in {field_type}: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields, "field_type": field_type}
        )


def safe_execute(
    func,
    *args,
    default_return: Any = None,
    error_message: str = "Operation failed",
    log_errors: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return if function fails
        error_message: Error message to log
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(
                error_message,
                function_name=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
        return default_return
