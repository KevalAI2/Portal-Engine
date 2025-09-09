"""
Standardized API response models for consistent API responses
"""
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standardized API response wrapper for all endpoints"""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data payload")
    message: str = Field(..., description="Human-readable response message")
    status_code: int = Field(200, description="HTTP status code")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if applicable")
    
    @classmethod
    def success_response(
        cls, 
        data: Any = None, 
        message: str = "Success", 
        status_code: int = 200
    ) -> "APIResponse":
        """Create a successful response"""
        return cls(
            success=True, 
            data=data, 
            message=message, 
            status_code=status_code
        )
    
    @classmethod
    def error_response(
        cls, 
        message: str = "Error", 
        data: Any = None, 
        status_code: int = 400,
        error: Optional[Dict[str, Any]] = None
    ) -> "APIResponse":
        """Create an error response"""
        return cls(
            success=False, 
            data=data, 
            message=message, 
            status_code=status_code,
            error=error
        )
    
    @classmethod
    def validation_error_response(
        cls, 
        message: str = "Validation error", 
        errors: list = None
    ) -> "APIResponse":
        """Create a validation error response"""
        return cls(
            success=False,
            message=message,
            status_code=422,
            error={"validation_errors": errors or []}
        )
    
    @classmethod
    def service_unavailable_response(
        cls, 
        message: str = "Service temporarily unavailable",
        service: str = None
    ) -> "APIResponse":
        """Create a service unavailable response"""
        return cls(
            success=False,
            message=message,
            status_code=503,
            error={"service": service} if service else None
        )


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
