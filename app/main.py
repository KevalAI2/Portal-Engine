"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import time
import sys
import os
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import get_logger
from app.api.routers import health, users, ui
from app.models.responses import APIResponse
from app.utils.serialization import safe_serialize
import json

class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return safe_serialize(obj)
        except (TypeError, RecursionError):
            return str(obj)

# Configure logging
logger = get_logger("main")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    startup_logger = get_logger("app_startup")
    
    # Startup
    startup_logger.info("Portal Engine application starting", 
                       version=settings.app_version, 
                       environment=settings.environment,
                       debug_mode=settings.debug,
                       api_host=settings.api_host,
                       api_port=settings.api_port)
    
    try:
        # Log configuration details
        startup_logger.info("Application configuration loaded",
                           redis_host=settings.redis_host,
                           redis_port=settings.redis_port,
                           celery_broker=settings.celery_broker_url,
                           log_level=settings.log_level)
        
        # Log service dependencies
        startup_logger.info("Service dependencies configured",
                           user_profile_service=settings.user_profile_service_url,
                           lie_service=settings.lie_service_url,
                           cis_service=settings.cis_service_url,
                           recommendation_api=settings.recommendation_api_url)
        
        startup_logger.info("Portal Engine application started successfully")
        
    except Exception as e:
        startup_logger.error("Failed to start Portal Engine application", 
                           error=str(e), 
                           exc_info=True)
        raise
    
    yield
    
    # Shutdown
    shutdown_logger = get_logger("app_shutdown")
    shutdown_logger.info("Portal Engine application shutting down",
                        version=settings.app_version,
                        environment=settings.environment)
    
    try:
        # Log any cleanup operations here
        shutdown_logger.info("Application shutdown completed successfully")
    except Exception as e:
        shutdown_logger.error("Error during application shutdown", 
                            error=str(e), 
                            exc_info=True)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Portal Engine - A modular recommendation system with FastAPI, Celery, RabbitMQ, and Redis",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    json_encoder=SafeJSONEncoder  # Add custom encoder
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    request_logger = get_logger("request_processing")
    start_time = time.time()
    
    request_logger.info("Processing HTTP request",
                       method=request.method,
                       url=str(request.url),
                       client_ip=request.client.host if request.client else None,
                       user_agent=request.headers.get("user-agent", "Unknown"))
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        request_logger.info("HTTP request completed",
                           method=request.method,
                           url=str(request.url),
                           status_code=response.status_code,
                           process_time_ms=round(process_time * 1000, 2))
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        request_logger.error("HTTP request failed",
                            method=request.method,
                            url=str(request.url),
                            error=str(e),
                            process_time_ms=round(process_time * 1000, 2),
                            exc_info=True)
        raise


# Remove duplicate middleware - already handled above


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    validation_logger = get_logger("validation_errors")
    validation_logger.warning(
        "Request validation failed",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        errors=exc.errors(),
        error_count=len(exc.errors())
    )
    
    response = APIResponse.validation_error_response(
        message="Validation error",
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    http_logger = get_logger("http_exceptions")
    http_logger.warning(
        "HTTP exception occurred",
        method=request.method,
        url=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail,
        client_ip=request.client.host if request.client else None
    )
    
    response = APIResponse.error_response(
        message=exc.detail,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    pydantic_logger = get_logger("pydantic_validation")
    pydantic_logger.warning(
        "Pydantic validation failed",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        errors=exc.errors(),
        error_count=len(exc.errors())
    )
    
    response = APIResponse.validation_error_response(
        message="Data validation error",
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=422,
        content=response.model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    global_logger = get_logger("global_exceptions")
    global_logger.error(
        "Unhandled exception occurred",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "Unknown"),
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        exc_info=True
    )
    
    response = APIResponse.error_response(
        message="Internal server error",
        status_code=500,
        error={"details": str(exc)} if settings.debug else None
    )
    
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )


# Include routers
app.include_router(
    health.router,
    prefix=settings.api_prefix
)

app.include_router(
    users.router,
    prefix=settings.api_prefix
)

# Include UI router (no prefix for direct access)
app.include_router(ui.router)

# Mount static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    root_logger = get_logger("root_endpoint")
    root_logger.info("Root endpoint accessed")
    
    data = {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health/"
    }
    return APIResponse.success_response(data=data, message="API is running")


@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    ping_logger = get_logger("ping_endpoint")
    ping_logger.info("Ping endpoint accessed")
    return APIResponse.success_response(data={"message": "pong"}, message="Pong")


@app.options("/")
async def options_root():
    """Handle OPTIONS request for root endpoint"""
    return Response(status_code=200)


@app.options("/ping")
async def options_ping():
    """Handle OPTIONS request for ping endpoint"""
    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
