"""
Enhanced logging configuration for Portal Engine
"""
import os
import sys
import logging
import structlog
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging() -> None:
    """Configure comprehensive logging for the application"""
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create separate log files for different levels
    info_log_file = logs_dir / "app_info.log"
    error_log_file = logs_dir / "app_error.log"
    debug_log_file = logs_dir / "app_debug.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Info file handler
    info_handler = logging.FileHandler(info_log_file, encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    info_handler.setFormatter(info_formatter)
    info_handler.addFilter(lambda record: record.levelno <= logging.WARNING)
    root_logger.addHandler(info_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s | %(pathname)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Debug file handler (only in debug mode)
    if settings.debug:
        debug_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        debug_handler.setFormatter(debug_formatter)
        root_logger.addHandler(debug_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" 
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Log startup message
    logger = get_logger("logging_setup")
    logger.info("Logging system initialized", 
                info_log=str(info_log_file), 
                error_log=str(error_log_file),
                debug_mode=settings.debug)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


def get_standard_logger(name: str) -> logging.Logger:
    """Get a standard Python logger instance"""
    return logging.getLogger(name)


class LoggingMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)
    
    @property
    def std_logger(self) -> logging.Logger:
        """Get standard logger for this class"""
        return get_standard_logger(self.__class__.__name__)


def log_function_call(func_name: str, **kwargs):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            logger = get_logger("function_calls")
            logger.info(f"Calling {func_name}", 
                       function=func_name, 
                       args_count=len(args),
                       kwargs=func_kwargs)
            try:
                result = func(*args, **func_kwargs)
                logger.info(f"Completed {func_name}", 
                           function=func_name, 
                           success=True)
                return result
            except Exception as e:
                logger.error(f"Failed {func_name}", 
                           function=func_name, 
                           error=str(e), 
                           success=False)
                raise
        return wrapper
    return decorator


def log_api_call(*args, **kwargs):
    """Log API calls. Supports two signatures for backward compatibility:
    1) log_api_call(service_name, endpoint, method="GET", **kwargs) -> initiates call
    2) log_api_call(method, path, status_code, duration_ms, **kwargs) -> completion
    """
    logger = get_logger("api_calls")
    # Completion-style call: (method, path, status_code, duration_ms)
    if len(args) >= 4 and isinstance(args[2], int):
        method, path, status_code, duration_ms = args[:4]
        fields = {
            "method": method,
            "endpoint": path,
            "status_code": status_code,
            "response_time_ms": duration_ms,
        }
        fields.update(kwargs)
        if status_code is not None and int(status_code) < 400:
            logger.info("API call completed", **fields)
        else:
            logger.error("API call failed", **fields)
        return
    
    # Initiation-style call: (service_name, endpoint, method="GET", **kwargs)
    if len(args) >= 2:
        service_name = args[0]
        endpoint = args[1]
        method = args[2] if len(args) >= 3 else kwargs.pop("method", "GET")
        logger.info(
            "External API call initiated",
            service=service_name,
            endpoint=endpoint,
            method=method,
            **kwargs,
        )
        return
    
    # Fallback: insufficient args
    logger.info("API call", **kwargs)


def log_api_response(service_name: str, endpoint: str, success: bool, 
                    status_code: Optional[int] = None, response_time: Optional[float] = None, **kwargs):
    """Log external API responses"""
    logger = get_logger("api_calls")
    if success:
        logger.info("External API call completed",
                   service=service_name,
                   endpoint=endpoint,
                   status_code=status_code,
                   response_time_ms=response_time * 1000 if response_time else None,
                   **kwargs)
    else:
        logger.error("External API call failed",
                    service=service_name,
                    endpoint=endpoint,
                    status_code=status_code,
                    response_time_ms=response_time * 1000 if response_time else None,
                    **kwargs)


def log_database_operation(operation: str, table: str, success: bool, **kwargs):
    """Log database operations"""
    logger = get_logger("database")
    if success:
        logger.info("Database operation completed",
                   operation=operation,
                   table=table,
                   **kwargs)
    else:
        logger.error("Database operation failed",
                    operation=operation,
                    table=table,
                    **kwargs)


def log_background_task(task_name: str, task_id: str, status: str, **kwargs):
    """Log background task operations"""
    logger = get_logger("background_tasks")
    if status == "started":
        logger.info("Background task started",
                   task_name=task_name,
                   task_id=task_id,
                   **kwargs)
    elif status == "completed":
        logger.info("Background task completed",
                   task_name=task_name,
                   task_id=task_id,
                   **kwargs)
    elif status == "failed":
        logger.error("Background task failed",
                    task_name=task_name,
                    task_id=task_id,
                    **kwargs)
    else:
        logger.info("Background task status update",
                   task_name=task_name,
                   task_id=task_id,
                   status=status,
                   **kwargs)


def log_exception(logger_name: str, exception: Exception, context: Dict[str, Any] = None):
    """Log exceptions with context"""
    logger = get_logger(logger_name)
    logger.error("Exception occurred",
                exception_type=type(exception).__name__,
                exception_message=str(exception),
                context=context or {},
                exc_info=True)


def log_performance(operation: str, duration_ms: float, success: bool = True, additional_data: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """Log performance metrics for an operation.
    When success is True -> info; otherwise -> warning.
    """
    logger = get_logger("performance")
    fields: Dict[str, Any] = {
        "operation": operation,
        "duration_ms": duration_ms,
        "success": success,
    }
    if additional_data:
        fields.update(additional_data)
    fields.update(kwargs)
    if success:
        logger.info("Operation performance", **fields)
    else:
        logger.warning("Operation performance", **fields)


def log_security_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """Log security-related events."""
    logger = get_logger("security")
    fields: Dict[str, Any] = {
        "event": event_type,
        "user_id": user_id,
    }
    if details:
        fields.update(details)
    fields.update(kwargs)
    logger.warning("Security event", **fields)


def log_business_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None, **kwargs) -> None:
    """Log business/domain events."""
    logger = get_logger("business")
    fields: Dict[str, Any] = {
        "event": event_type,
        "user_id": user_id,
    }
    if details:
        fields.update(details)
    fields.update(kwargs)
    logger.info("Business event", **fields)


# Initialize logging on module import
setup_logging()