"""
Validation decorators for API endpoints.

This module provides decorators for automatic request validation,
data sanitization, and error handling in FastAPI endpoints.
"""
import functools
from typing import Any, Callable, Dict, List, Optional, Type, Union
from fastapi import HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from app.core.exceptions import ValidationError as CustomValidationError
from app.core.validators import validate_request_data, sanitize_string
from app.core.logging import get_logger
from app.models.responses import APIResponse

logger = get_logger("validation_decorators")


def validate_request_body(
    model_class: Type[BaseModel],
    required_fields: Optional[List[str]] = None,
    optional_fields: Optional[List[str]] = None
):
    """
    Decorator to validate request body using Pydantic models.
    
    Args:
        model_class: Pydantic model class for validation
        required_fields: List of required fields (if not using model)
        optional_fields: List of optional fields (if not using model)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request from kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    # Try to get from kwargs
                    request = kwargs.get('request')
                
                if request:
                    # Get request body
                    body = await request.json()
                    
                    # Validate using Pydantic model
                    if model_class:
                        validated_data = model_class(**body)
                        # Add validated data to kwargs
                        kwargs['validated_data'] = validated_data
                    else:
                        # Use custom validation
                        validated_data = validate_request_data(
                            body,
                            required_fields or [],
                            optional_fields or []
                        )
                        kwargs['validated_data'] = validated_data
                
                return await func(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(
                    "Request validation failed",
                    errors=e.errors(),
                    endpoint=func.__name__
                )
                
                response = APIResponse.error_response(
                    message="Request validation failed",
                    status_code=400,
                    error={"validation_errors": e.errors()}
                )
                
                return JSONResponse(
                    status_code=400,
                    content=response.model_dump()
                )
                
            except CustomValidationError as e:
                logger.warning(
                    "Custom validation failed",
                    field=e.field_name,
                    value=e.value,
                    message=e.message,
                    endpoint=func.__name__
                )
                
                response = APIResponse.error_response(
                    message=e.message,
                    status_code=400,
                    error={
                        "field": e.field_name,
                        "value": str(e.value),
                        "error_code": e.error_code
                    }
                )
                
                return JSONResponse(
                    status_code=400,
                    content=response.model_dump()
                )
                
            except Exception as e:
                logger.error(
                    "Unexpected error in validation decorator",
                    error=str(e),
                    endpoint=func.__name__,
                    exc_info=True
                )
                
                response = APIResponse.error_response(
                    message="Internal validation error",
                    status_code=500
                )
                
                return JSONResponse(
                    status_code=500,
                    content=response.model_dump()
                )
        
        return wrapper
    return decorator


def validate_query_params(
    required_params: Optional[List[str]] = None,
    optional_params: Optional[List[str]] = None,
    param_validators: Optional[Dict[str, Callable]] = None
):
    """
    Decorator to validate query parameters.
    
    Args:
        required_params: List of required query parameters
        optional_params: List of optional query parameters
        param_validators: Dictionary mapping param names to validation functions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request from kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    request = kwargs.get('request')
                
                if request:
                    # Get query parameters
                    query_params = dict(request.query_params)
                    
                    # Validate required parameters
                    if required_params:
                        missing_params = [
                            param for param in required_params 
                            if param not in query_params
                        ]
                        if missing_params:
                            response = APIResponse.error_response(
                                message=f"Missing required query parameters: {', '.join(missing_params)}",
                                status_code=400
                            )
                            return JSONResponse(
                                status_code=400,
                                content=response.model_dump()
                            )
                    
                    # Validate parameter values
                    validated_params = {}
                    all_params = (required_params or []) + (optional_params or [])
                    
                    for param in all_params:
                        if param in query_params:
                            value = query_params[param]
                            
                            # Apply custom validator if provided
                            if param_validators and param in param_validators:
                                try:
                                    value = param_validators[param](value)
                                except Exception as e:
                                    response = APIResponse.error_response(
                                        message=f"Invalid value for parameter '{param}': {str(e)}",
                                        status_code=400
                                    )
                                    return JSONResponse(
                                        status_code=400,
                                        content=response.model_dump()
                                    )
                            
                            # Sanitize string values
                            if isinstance(value, str):
                                value = sanitize_string(value)
                            
                            validated_params[param] = value
                    
                    # Add validated parameters to kwargs
                    kwargs['validated_params'] = validated_params
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(
                    "Error in query parameter validation",
                    error=str(e),
                    endpoint=func.__name__,
                    exc_info=True
                )
                
                response = APIResponse.error_response(
                    message="Query parameter validation error",
                    status_code=400
                )
                
                return JSONResponse(
                    status_code=400,
                    content=response.model_dump()
                )
        
        return wrapper
    return decorator


def sanitize_input(func: Callable) -> Callable:
    """
    Decorator to sanitize all string inputs in request data.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if request:
                # Sanitize query parameters
                if hasattr(request, 'query_params'):
                    sanitized_query = {}
                    for key, value in request.query_params.items():
                        if isinstance(value, str):
                            sanitized_query[key] = sanitize_string(value)
                        else:
                            sanitized_query[key] = value
                    request.query_params = sanitized_query
                
                # Sanitize path parameters
                if hasattr(request, 'path_params'):
                    sanitized_path = {}
                    for key, value in request.path_params.items():
                        if isinstance(value, str):
                            sanitized_path[key] = sanitize_string(value)
                        else:
                            sanitized_path[key] = value
                    request.path_params = sanitized_path
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            logger.error(
                "Error in input sanitization",
                error=str(e),
                endpoint=func.__name__,
                exc_info=True
            )
            
            response = APIResponse.error_response(
                message="Input sanitization error",
                status_code=500
            )
            
            return JSONResponse(
                status_code=500,
                content=response.model_dump()
            )
    
    return wrapper


def validate_user_authentication(func: Callable) -> Callable:
    """
    Decorator to validate user authentication.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if request:
                # Check for authorization header
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    response = APIResponse.error_response(
                        message="Authorization header required",
                        status_code=401
                    )
                    return JSONResponse(
                        status_code=401,
                        content=response.model_dump()
                    )
                
                # Basic validation of auth header format
                if not auth_header.startswith(('Bearer ', 'Basic ')):
                    response = APIResponse.error_response(
                        message="Invalid authorization header format",
                        status_code=401
                    )
                    return JSONResponse(
                        status_code=401,
                        content=response.model_dump()
                    )
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            logger.error(
                "Error in authentication validation",
                error=str(e),
                endpoint=func.__name__,
                exc_info=True
            )
            
            response = APIResponse.error_response(
                message="Authentication validation error",
                status_code=500
            )
            
            return JSONResponse(
                status_code=500,
                content=response.model_dump()
            )
    
    return wrapper


def validate_rate_limit(
    requests_per_minute: int = 60,
    burst_size: int = 10
):
    """
    Decorator to validate rate limiting.
    
    Args:
        requests_per_minute: Maximum requests per minute
        burst_size: Maximum burst size
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request from kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    request = kwargs.get('request')
                
                if request:
                    # Get client IP
                    client_ip = request.client.host if request.client else "unknown"
                    
                    # TODO: Implement actual rate limiting logic
                    # This is a placeholder for rate limiting implementation
                    # In a real implementation, you would check against Redis or similar
                    
                    logger.debug(
                        "Rate limit check",
                        client_ip=client_ip,
                        endpoint=func.__name__,
                        requests_per_minute=requests_per_minute
                    )
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(
                    "Error in rate limit validation",
                    error=str(e),
                    endpoint=func.__name__,
                    exc_info=True
                )
                
                response = APIResponse.error_response(
                    message="Rate limit validation error",
                    status_code=500
                )
                
                return JSONResponse(
                    status_code=500,
                    content=response.model_dump()
                )
        
        return wrapper
    return decorator


def validate_cors_origin(func: Callable) -> Callable:
    """
    Decorator to validate CORS origin.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if request:
                origin = request.headers.get('Origin')
                if origin:
                    # Basic origin validation
                    # In a real implementation, you would check against allowed origins
                    logger.debug(
                        "CORS origin check",
                        origin=origin,
                        endpoint=func.__name__
                    )
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            logger.error(
                "Error in CORS origin validation",
                error=str(e),
                endpoint=func.__name__,
                exc_info=True
            )
            
            response = APIResponse.error_response(
                message="CORS validation error",
                status_code=500
            )
            
            return JSONResponse(
                status_code=500,
                content=response.model_dump()
            )
    
    return wrapper


def validate_content_type(
    allowed_types: List[str] = ["application/json"]
):
    """
    Decorator to validate content type.
    
    Args:
        allowed_types: List of allowed content types
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request from kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    request = kwargs.get('request')
                
                if request:
                    content_type = request.headers.get('Content-Type', '')
                    
                    # Check if content type is allowed
                    if not any(allowed_type in content_type for allowed_type in allowed_types):
                        response = APIResponse.error_response(
                            message=f"Content type must be one of: {', '.join(allowed_types)}",
                            status_code=415
                        )
                        return JSONResponse(
                            status_code=415,
                            content=response.model_dump()
                        )
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(
                    "Error in content type validation",
                    error=str(e),
                    endpoint=func.__name__,
                    exc_info=True
                )
                
                response = APIResponse.error_response(
                    message="Content type validation error",
                    status_code=500
                )
                
                return JSONResponse(
                    status_code=500,
                    content=response.model_dump()
                )
        
        return wrapper
    return decorator


def validate_request_size(max_size: int = 1024 * 1024):  # 1MB default
    """
    Decorator to validate request size.
    
    Args:
        max_size: Maximum request size in bytes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract request from kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    request = kwargs.get('request')
                
                if request:
                    content_length = request.headers.get('Content-Length')
                    if content_length:
                        size = int(content_length)
                        if size > max_size:
                            response = APIResponse.error_response(
                                message=f"Request size exceeds maximum allowed size of {max_size} bytes",
                                status_code=413
                            )
                            return JSONResponse(
                                status_code=413,
                                content=response.model_dump()
                            )
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(
                    "Error in request size validation",
                    error=str(e),
                    endpoint=func.__name__,
                    exc_info=True
                )
                
                response = APIResponse.error_response(
                    message="Request size validation error",
                    status_code=500
                )
                
                return JSONResponse(
                    status_code=500,
                    content=response.model_dump()
                )
        
        return wrapper
    return decorator
