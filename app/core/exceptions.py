"""
Custom exceptions for the Portal Engine application.

This module defines custom exception classes for better error handling
and more specific error messages throughout the application.
"""
from typing import Optional, Dict, Any


class PortalEngineException(Exception):
    """Base exception class for all Portal Engine exceptions."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ServiceUnavailableError(PortalEngineException):
    """Raised when an external service is unavailable."""
    
    def __init__(
        self, 
        service_name: str, 
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Service '{service_name}' is currently unavailable"
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service_name": service_name, **(details or {})}
        )
        self.service_name = service_name


class ServiceTimeoutError(PortalEngineException):
    """Raised when a service request times out."""
    
    def __init__(
        self, 
        service_name: str, 
        timeout_seconds: float,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Service '{service_name}' request timed out after {timeout_seconds}s"
        super().__init__(
            message=message,
            error_code="SERVICE_TIMEOUT",
            details={
                "service_name": service_name,
                "timeout_seconds": timeout_seconds,
                **(details or {})
            }
        )
        self.service_name = service_name
        self.timeout_seconds = timeout_seconds


class ValidationError(PortalEngineException):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        field_name: str, 
        value: Any,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Validation failed for field '{field_name}' with value: {value}"
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field_name": field_name,
                "value": str(value),
                **(details or {})
            }
        )
        self.field_name = field_name
        self.value = value


class ConfigurationError(PortalEngineException):
    """Raised when there's a configuration issue."""
    
    def __init__(
        self, 
        config_key: str, 
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Configuration error for key '{config_key}'"
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **(details or {})}
        )
        self.config_key = config_key


class DataProcessingError(PortalEngineException):
    """Raised when data processing fails."""
    
    def __init__(
        self, 
        operation: str, 
        data_type: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Data processing failed for {operation} on {data_type}"
        super().__init__(
            message=message,
            error_code="DATA_PROCESSING_ERROR",
            details={
                "operation": operation,
                "data_type": data_type,
                **(details or {})
            }
        )
        self.operation = operation
        self.data_type = data_type


class CacheError(PortalEngineException):
    """Raised when cache operations fail."""
    
    def __init__(
        self, 
        operation: str, 
        key: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Cache {operation} failed for key '{key}'"
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={
                "operation": operation,
                "key": key,
                **(details or {})
            }
        )
        self.operation = operation
        self.key = key


class RecommendationError(PortalEngineException):
    """Raised when recommendation generation fails."""
    
    def __init__(
        self, 
        user_id: str, 
        reason: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Recommendation generation failed for user '{user_id}': {reason}"
        super().__init__(
            message=message,
            error_code="RECOMMENDATION_ERROR",
            details={
                "user_id": user_id,
                "reason": reason,
                **(details or {})
            }
        )
        self.user_id = user_id
        self.reason = reason


class AuthenticationError(PortalEngineException):
    """Raised when authentication fails."""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details or {}
        )


class AuthorizationError(PortalEngineException):
    """Raised when authorization fails."""
    
    def __init__(
        self, 
        resource: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Access denied to resource '{resource}'"
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details={"resource": resource, **(details or {})}
        )
        self.resource = resource
