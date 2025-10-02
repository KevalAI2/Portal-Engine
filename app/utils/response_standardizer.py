"""
API Response Standardization Utilities

This module provides standardized response formatting for all API endpoints
to ensure consistency across the application.
"""
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger("response_standardizer")


class StandardResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized success response.
        
        Args:
            data: Response data payload
            message: Success message
            status_code: HTTP status code
            metadata: Additional metadata
            
        Returns:
            Standardized success response dictionary
        """
        response = {
            "success": True,
            "message": message,
            "status_code": status_code,
            "data": data
        }
        
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Specific error code
            details: Additional error details
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            "success": False,
            "message": message,
            "status_code": status_code
        }
        
        if error_code:
            response["error_code"] = error_code
            
        if details is not None:
            response["details"] = details
            
        return response
    
    @staticmethod
    def error_with_details(
        message: str = "An error occurred",
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response that always includes details.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Specific error code
            details: Additional error details (will be included even if None)
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            "success": False,
            "message": message,
            "status_code": status_code,
            "details": details
        }
        
        if error_code:
            response["error_code"] = error_code
            
        return response
    
    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        errors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized validation error response.
        
        Args:
            message: Validation error message
            errors: Validation error details
            
        Returns:
            Standardized validation error response dictionary
        """
        return StandardResponse.error_with_details(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors} if errors else None
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized not found response.
        
        Args:
            message: Not found message
            resource_type: Type of resource not found
            
        Returns:
            Standardized not found response dictionary
        """
        details = {"resource_type": resource_type} if resource_type else None
        return StandardResponse.error_with_details(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Unauthorized access",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized unauthorized response.
        
        Args:
            message: Unauthorized message
            details: Additional details
            
        Returns:
            Standardized unauthorized response dictionary
        """
        return StandardResponse.error_with_details(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details
        )
    
    @staticmethod
    def forbidden(
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized forbidden response.
        
        Args:
            message: Forbidden message
            details: Additional details
            
        Returns:
            Standardized forbidden response dictionary
        """
        return StandardResponse.error_with_details(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details
        )
    
    @staticmethod
    def rate_limited(
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized rate limited response.
        
        Args:
            message: Rate limit message
            retry_after: Seconds to wait before retrying
            
        Returns:
            Standardized rate limited response dictionary
        """
        details = {"retry_after": retry_after} if retry_after else None
        return StandardResponse.error_with_details(
            message=message,
            status_code=429,
            error_code="RATE_LIMITED",
            details=details
        )
    
    @staticmethod
    def server_error(
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized server error response.
        
        Args:
            message: Server error message
            details: Additional details
            
        Returns:
            Standardized server error response dictionary
        """
        return StandardResponse.error_with_details(
            message=message,
            status_code=500,
            error_code="SERVER_ERROR",
            details=details
        )
    
    @staticmethod
    def service_unavailable(
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized service unavailable response.
        
        Args:
            message: Service unavailable message
            retry_after: Seconds to wait before retrying
            
        Returns:
            Standardized service unavailable response dictionary
        """
        details = {"retry_after": retry_after} if retry_after else None
        return StandardResponse.error_with_details(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )


def create_json_response(
    response_data: Dict[str, Any],
    status_code: Optional[int] = None
) -> JSONResponse:
    """
    Create a JSONResponse with standardized data.
    
    Args:
        response_data: Standardized response data
        status_code: HTTP status code (uses response_data status_code if not provided)
        
    Returns:
        JSONResponse object
    """
    status = status_code or response_data.get("status_code", 200)
    return JSONResponse(content=response_data, status_code=status)


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    Handle exceptions and convert to standardized error response.
    
    Args:
        exc: Exception to handle
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(exc, HTTPException):
        return StandardResponse.error(
            message=exc.detail,
            status_code=exc.status_code,
            error_code=f"HTTP_{exc.status_code}"
        )
    
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    return StandardResponse.server_error(
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__}
    )


def standardize_pagination(
    data: list,
    page: int,
    page_size: int,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Standardize paginated response data.
    
    Args:
        data: List of items for current page
        page: Current page number (1-based)
        page_size: Number of items per page
        total_count: Total number of items (optional)
        
    Returns:
        Standardized pagination metadata
    """
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": len(data),
        "has_next": len(data) == page_size and total_count is not None and (page * page_size) < total_count
    }
    
    if total_count is not None:
        pagination["total_count"] = total_count
        pagination["total_pages"] = (total_count + page_size - 1) // page_size
        pagination["has_next"] = page < pagination["total_pages"]
    
    return pagination


def standardize_list_response(
    items: list,
    message: str = "Items retrieved successfully",
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized list response with optional pagination.
    
    Args:
        items: List of items
        message: Success message
        page: Current page number (for pagination)
        page_size: Items per page (for pagination)
        total_count: Total count (for pagination)
        
    Returns:
        Standardized list response dictionary
    """
    response_data = {
        "items": items,
        "count": len(items)
    }
    
    if page is not None and page_size is not None:
        response_data["pagination"] = standardize_pagination(
            items, page, page_size, total_count
        )
    
    return StandardResponse.success(
        data=response_data,
        message=message
    )


def standardize_single_response(
    item: Any,
    message: str = "Item retrieved successfully"
) -> Dict[str, Any]:
    """
    Create a standardized single item response.
    
    Args:
        item: Single item data
        message: Success message
        
    Returns:
        Standardized single item response dictionary
    """
    return StandardResponse.success(
        data=item,
        message=message
    )


def standardize_created_response(
    item: Any,
    message: str = "Item created successfully"
) -> Dict[str, Any]:
    """
    Create a standardized created response.
    
    Args:
        item: Created item data
        message: Success message
        
    Returns:
        Standardized created response dictionary
    """
    return StandardResponse.success(
        data=item,
        message=message,
        status_code=201
    )


def standardize_updated_response(
    item: Any,
    message: str = "Item updated successfully"
) -> Dict[str, Any]:
    """
    Create a standardized updated response.
    
    Args:
        item: Updated item data
        message: Success message
        
    Returns:
        Standardized updated response dictionary
    """
    return StandardResponse.success(
        data=item,
        message=message
    )


def standardize_deleted_response(
    message: str = "Item deleted successfully"
) -> Dict[str, Any]:
    """
    Create a standardized deleted response.
    
    Args:
        message: Success message
        
    Returns:
        Standardized deleted response dictionary
    """
    return StandardResponse.success(
        data=None,
        message=message,
        status_code=204
    )