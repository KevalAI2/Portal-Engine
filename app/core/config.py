"""
Configuration settings for Portal Engine.

This module provides centralized configuration management using Pydantic settings.
It handles environment variable loading, validation, and secure configuration management.

Classes:
    Settings: Main configuration class with validation and security features.

Functions:
    validate_secrets: Validates production security requirements.
    get_secure_redis_url: Returns Redis URL with authentication.
    get_secure_celery_broker_url: Returns Celery broker URL with authentication.
    mask_sensitive_data: Returns configuration with sensitive data masked.

Example:
    >>> from app.core.config import settings
    >>> settings.validate_secrets()
    >>> redis_url = settings.get_secure_redis_url()
"""
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import sys
import re
from urllib.parse import urlparse


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class provides comprehensive configuration management with validation,
    security features, and environment-specific settings.
    
    Attributes:
        app_name (str): Application name.
        app_version (str): Application version.
        environment (str): Environment (development, staging, production, test).
        debug (bool): Debug mode flag.
        api_host (str): API host address.
        api_port (int): API port number (1-65535).
        redis_host (str): Redis host address.
        redis_port (int): Redis port number (1-65535).
        redis_password (Optional[str]): Redis password for authentication.
        rabbitmq_host (str): RabbitMQ host address.
        rabbitmq_port (int): RabbitMQ port number (1-65535).
        rabbitmq_user (str): RabbitMQ username.
        rabbitmq_password (str): RabbitMQ password.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format (str): Logging format (json, text).
        
    Methods:
        validate_secrets(): Validate production security requirements.
        get_secure_redis_url(): Get Redis URL with authentication.
        get_secure_celery_broker_url(): Get Celery broker URL with authentication.
        mask_sensitive_data(): Get configuration with masked sensitive data.
        
    Example:
        >>> settings = Settings()
        >>> settings.validate_secrets()
        >>> redis_url = settings.get_secure_redis_url()
    """
    
    # ✅ Pydantic v2 way (no inner Config class)
    model_config = ConfigDict(env_file=".env", extra="ignore", validate_assignment=True)

    # Application
    app_name: str = Field(default="Portal Engine", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env=["APP_ENV", "ENVIRONMENT"])
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=3031, env="API_PORT", ge=1, le=65535)
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # Redis Settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT", ge=1, le=65535)
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_namespace: str = Field(default="recommendations", env="REDIS_NAMESPACE")
    
    # RabbitMQ Settings
    rabbitmq_host: str = Field(default="localhost", env="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, env="RABBITMQ_PORT", ge=1, le=65535)
    rabbitmq_user: str = Field(default="guest", env="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", env="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field(default="/", env="RABBITMQ_VHOST")
    
    # Celery Settings
    celery_broker_url: str = Field(
        default="amqp://guest:guest@localhost:5672//", 
        env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", 
        env="CELERY_RESULT_BACKEND"
    )
    
    # External Services
    user_profile_service_url: str = Field(
        default="http://localhost:8000", 
        env="USER_PROFILE_SERVICE_URL"
    )
    lie_service_url: str = Field(
        default="http://localhost:8000", 
        env="LIE_SERVICE_URL"
    )
    cis_service_url: str = Field(
        default="http://localhost:8000", 
        env="CIS_SERVICE_URL"
    )
    prefetch_service_url: str = Field(
        default="http://localhost:8000", 
        env="PREFETCH_SERVICE_URL"
    )
    recommendation_api_url: str = Field(
        default="http://localhost:8080",
        env="RECOMMENDATION_API_URL"
    )
    recommendation_api_provider: str = Field(
        default="groq",
        env="RECOMMENDATION_API_PROVIDER"
    )
    
    # Scheduling
    recommendation_refresh_interval_minutes: int = Field(
        default=30, 
        env="RECOMMENDATION_REFRESH_INTERVAL_MINUTES"
    )

    # Task interval
    task_interval_seconds: int = Field(default=10, env="TASK_INTERVAL_SECONDS")
    
    # Celery Worker Configuration
    celery_worker_concurrency: int = Field(default=10, env="CELERY_WORKER_CONCURRENCY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")

    @field_validator('api_port')
    @classmethod
    def validate_api_port(cls, v):
        if not isinstance(v, int) or v < 1 or v > 65535:
            raise ValueError('API port must be between 1 and 65535')
        return v

    @field_validator('redis_port')
    @classmethod
    def validate_redis_port(cls, v):
        if not isinstance(v, int) or v < 1 or v > 65535:
            raise ValueError('Redis port must be between 1 and 65535')
        return v

    @field_validator('rabbitmq_port')
    @classmethod
    def validate_rabbitmq_port(cls, v):
        if not isinstance(v, int) or v < 1 or v > 65535:
            raise ValueError('RabbitMQ port must be between 1 and 65535')
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()

    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        valid_formats = ['json', 'text']
        if v.lower() not in valid_formats:
            raise ValueError(f'Log format must be one of: {", ".join(valid_formats)}')
        return v.lower()

    @field_validator('recommendation_api_url')
    @classmethod
    def validate_api_url(cls, v):
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError('Invalid URL format')
            if parsed.scheme not in ['http', 'https']:
                raise ValueError('URL must use http or https scheme')
        except Exception as e:
            raise ValueError(f'Invalid recommendation API URL: {e}')
        return v

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production', 'test']
        if v.lower() not in valid_envs:
            raise ValueError(f'Environment must be one of: {", ".join(valid_envs)}')
        return v.lower()

    def validate_secrets(self) -> bool:
        """Validate that sensitive configuration is properly set"""
        if self.environment == "production":
            if not self.redis_password:
                raise ValueError("Redis password is required in production")
            if self.rabbitmq_password == "guest":
                raise ValueError("Default RabbitMQ password not allowed in production")
            if self.rabbitmq_user == "guest":
                raise ValueError("Default RabbitMQ user not allowed in production")
            if len(self.redis_password) < 8:
                raise ValueError("Redis password must be at least 8 characters in production")
            if len(self.rabbitmq_password) < 8:
                raise ValueError("RabbitMQ password must be at least 8 characters in production")
        return True

    def get_secure_redis_url(self) -> str:
        """Get secure Redis URL with proper authentication"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_secure_celery_broker_url(self) -> str:
        """Get secure Celery broker URL with proper authentication"""
        if self.rabbitmq_password and self.rabbitmq_user:
            return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"

    def mask_sensitive_data(self) -> Dict[str, Any]:
        """Return configuration with sensitive data masked for logging"""
        config_dict: Dict[str, Any] = self.model_dump()
        sensitive_fields: List[str] = ['redis_password', 'rabbitmq_password']
        for field in sensitive_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = "***MASKED***"
        return config_dict


# Global settings instance
settings = Settings()
if "pytest" in sys.modules:
    settings.environment = "test"