"""
Error handling utilities for the Portal Engine application.

This module provides utilities for consistent error handling,
logging, and error response formatting across the application.
"""
import traceback
from typing import Any, Dict, Optional, Union, Callable, TypeVar, Coroutine
import functools
import inspect
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import PortalEngineException
from app.core.logging import get_logger
from app.models.responses import APIResponse


logger = get_logger("error_handler")


async def handle_exception(
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
    # Prefer header if provided, else state
    correlation_id = request.headers.get("X-Correlation-ID") or getattr(request.state, 'correlation_id', None)
    # Ensure JSON-serializable
    if correlation_id is not None and not isinstance(correlation_id, (str, int)):
        correlation_id = str(correlation_id)
    
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
    
    # Handle Pydantic ValidationError (import locally to avoid hard dep at import time)
    try:
        from pydantic import ValidationError  # type: ignore
        if isinstance(exc, ValidationError):
            return _handle_validation_exception(exc, correlation_id, include_traceback)
    except Exception:
        pass
    
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
        "correlation_id": str(correlation_id) if correlation_id is not None else None
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
        "correlation_id": str(correlation_id) if correlation_id is not None else None
    }
    
    if include_traceback:
        error_details["traceback"] = traceback.format_exc()
    
    response = APIResponse.error_response(
        message=str(exc) or "An unexpected error occurred",
        status_code=500,
        error=error_details
    )
    
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )


def _handle_validation_exception(
    exc: Any,
    correlation_id: Optional[str],
    include_traceback: bool
) -> JSONResponse:
    """Handle Pydantic ValidationError consistently."""
    error_details = {
        "exception_type": "ValidationError",
        "correlation_id": str(correlation_id) if correlation_id is not None else None,
        "errors": getattr(exc, 'errors', lambda: [])(),
    }
    if include_traceback:
        error_details["traceback"] = traceback.format_exc()
    response = APIResponse.error_response(
        message=str(exc),
        status_code=422,
        error=error_details
    )
    return JSONResponse(status_code=422, content=response.model_dump())


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
    *,
    status_code: int,
    message: str,
    error_details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    include_traceback: bool = False,
    exc: Optional[Exception] = None,
    error_code: Optional[str] = None,
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
    details_out: Dict[str, Any] = {}
    if error_code:
        details_out["error_code"] = error_code
    if correlation_id is not None:
        details_out["correlation_id"] = str(correlation_id)
    if error_details:
        details_out.update(error_details)
    if include_traceback and exc is not None:
        details_out["traceback"] = traceback.format_exc()
    
    response = APIResponse.error_response(
        message=message,
        status_code=status_code,
        error=details_out
    )
    
    return JSONResponse(status_code=status_code, content=response.model_dump())


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


F = TypeVar("F", bound=Callable[..., Any])


def safe_execute(func: Optional[F] = None, *, default_return: Any = None, error_message: str = "Operation failed", log_errors: bool = True) -> Callable[[F], F] | F:
    """Decorator to execute a function safely with error handling.
    Can be used as `@safe_execute` or `@safe_execute(default_return=..., ...)`.
    Supports both sync and async functions.
    """
    def _decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:  # pragma: no cover - exercised in tests
                    if log_errors:
                        logger.error(
                            error_message,
                            function_name=fn.__name__,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            exc_info=True,
                        )
                    return default_return
            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if log_errors:
                        logger.error(
                            error_message,
                            function_name=fn.__name__,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            exc_info=True,
                        )
                    return default_return
            return sync_wrapper  # type: ignore[return-value]

    if func is not None and callable(func):
        return _decorator(func)  # type: ignore[return-value]
    return _decorator
