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
from app.api.routers import health, users
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
    # Startup
    logger.info("Starting Portal Engine application", version=settings.app_version, environment=settings.environment)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Portal Engine application")


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
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Incoming request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time
        )
        raise


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(
        "Validation error",
        method=request.method,
        url=str(request.url),
        errors=exc.errors()
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
    logger.warning(
        "HTTP exception",
        method=request.method,
        url=str(request.url),
        status_code=exc.status_code,
        detail=exc.detail
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
    logger.warning(
        "Pydantic validation error",
        method=request.method,
        url=str(request.url),
        errors=exc.errors()
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
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
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

@app.get("/")
async def root():
    """Root endpoint"""
    data = {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }
    return APIResponse.success_response(data=data, message="API is running")


@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
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
